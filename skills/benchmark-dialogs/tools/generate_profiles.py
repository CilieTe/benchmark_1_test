#!/usr/bin/env python3
"""Generate benchmark profiles from profile specs.

Pipeline:
- profile_spec.json -> profiles_native.jsonl
- profiles_native.jsonl -> profiles_runtime.jsonl
- failed_profiles.jsonl and repair_manifest.json for rows that cannot pass the
  local contract after generation/repair.

This tool implements the v1 generate-profiles contract from DESIGN.md. Native
profiles may contain domain-specific fields, but runtime profiles are normalized
for run_dialogs.py.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


LOG = logging.getLogger("generate_profiles")

DEFAULT_API_BASE = "http://192.168.101.15:9898"
DEFAULT_MODEL = "qwen/qwen3.6-35b-a3b"
VALID_DIFFICULTIES = {"L1", "L2", "L3"}
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
SCRIPTED_RE = re.compile(
    r"\bwhen (the )?(agent|assistant|csr|rep|caller) (says|asks|mentions)\b"
    r"|客服(说|问|提到).*(你就|就)",
    re.IGNORECASE,
)


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def read_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [obj for _, obj in iter_jsonl(path)]
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [obj for obj in data if isinstance(obj, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"unsupported json root in {path}: {type(data).__name__}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compact_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = max(1, limit // 2)
    return text[:half] + "\n...[TRUNCATED]...\n" + text[-half:]


def compact_json(data: Any, limit: int) -> str:
    return compact_text(json.dumps(data, ensure_ascii=False, indent=2), limit)


def parse_json_object(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        raw = match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


class ChatClient:
    def __init__(
        self,
        api_base: str,
        model: str,
        provider: str,
        temperature: float,
        max_tokens: int,
        retries: int,
        timeout: int,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retries = retries
        self.timeout = timeout

    def call(self, prompt: str) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_completion_tokens": self.max_tokens,
        }
        if self.provider:
            body["provider"] = self.provider
        req = urllib.request.Request(
            f"{self.api_base}/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read())
                if "choices" in data:
                    return (data["choices"][0]["message"].get("content") or "").strip()
                if "content" in data:
                    return str(data["content"]).strip()
                raise RuntimeError(f"unexpected response keys: {list(data.keys())}")
            except urllib.error.HTTPError as exc:
                body_text = exc.read().decode(errors="replace")
                last_error = RuntimeError(f"HTTP {exc.code}: {body_text[:300]}")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            if attempt < self.retries:
                time.sleep(2)
        raise RuntimeError(f"chat failed after {self.retries + 1} attempts: {last_error}")


def output_paths(output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    return {
        "dir": output,
        "native": output / "profiles_native.jsonl",
        "runtime": output / "profiles_runtime.jsonl",
        "failed": output / "failed_profiles.jsonl",
        "manifest": output / "repair_manifest.json",
    }


def prompt_id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("prompt_id") or "").strip()


def prompt_placeholders(item: dict[str, Any]) -> list[str]:
    text = str(item.get("prompt") or "")
    return sorted(set(PLACEHOLDER_RE.findall(text)))


def prompt_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": prompt_id(item),
        "category": item.get("category"),
        "scene": item.get("scene") or item.get("business"),
        "lang": item.get("lang"),
        "identity_placeholders": prompt_placeholders(item),
        "prompt_excerpt": compact_text(str(item.get("prompt") or ""), 10000),
        "function_excerpt": compact_text(str(item.get("function") or ""), 2500),
    }


def normalize_spec(row: dict[str, Any], domain: str) -> dict[str, Any]:
    spec = dict(row)
    if "intent_level" in spec and "user_starting_position" not in spec:
        spec["user_starting_position"] = spec["intent_level"]
    spec.setdefault("domain", domain)
    spec.setdefault("identity", {})
    return spec


def selected_slice(rows: list[dict[str, Any]], start: int, count: int | None) -> list[dict[str, Any]]:
    if count is None:
        return rows[start:]
    return rows[start : start + count]


def nearest_rows(rows: list[dict[str, Any]], spec: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    difficulty = str(spec.get("difficulty") or "")
    start = str(spec.get("user_starting_position") or "")
    scored = []
    for row in rows:
        score = 0
        row_text = json.dumps(row, ensure_ascii=False).lower()
        if difficulty and difficulty.lower() in row_text:
            score += 2
        if start and start.lower() in row_text:
            score += 2
        for key in ("behavior_type", "primary_behavior_type", "resolution_style"):
            value = str(spec.get(key) or "")
            if value and value.lower() in row_text:
                score += 1
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for score, row in scored[:limit] if score > 0] or rows[:limit]


def build_generation_prompt(
    domain: str,
    spec: dict[str, Any],
    prompt_item: dict[str, Any],
    guide: str,
    stage2_rows: list[dict[str, Any]],
    behavior_rows: list[dict[str, Any]],
    noise_rows: list[dict[str, Any]],
    lang: str,
) -> str:
    return f"""You are generating one native user profile for a benchmark dialog runner.

Return one valid JSON object only. No markdown, no explanation.

Domain: {domain}
Target profile spec:
{compact_json(spec, 12000)}

Assistant prompt being tested:
{compact_json(prompt_summary(prompt_item), 18000)}

Confirmed domain guide:
\"\"\"
{compact_text(guide, 38000)}
\"\"\"

Relevant stage2 persona references:
{compact_json(stage2_rows, 16000)}

Relevant behavior references:
{compact_json(behavior_rows, 18000)}

Relevant noise/language references:
{compact_json(noise_rows, 12000)}

Required JSON keys:
- profile_id
- prompt_id
- business
- difficulty
- user_starting_position
- convertibility_ceiling
- identity
- persona
- situation
- task_instructions
- behavioral_affordances
- behavior_examples
- ending_expected
- native_notes

Identity rules:
- The prompt placeholders are: {json.dumps(prompt_placeholders(prompt_item), ensure_ascii=False)}.
- The spec identity object is: {json.dumps(spec.get("identity") or {}, ensure_ascii=False)}.
- If a spec identity value is true, replace it with a realistic fake concrete value.
- If a spec identity value is concrete, preserve it exactly.
- If the prompt has no placeholders, identity must be {{}}.

Profile quality rules:
- Write all user-facing profile text in language `{lang}` unless the spec explicitly requires another language.
- The profile is motive-driven, not a turn-by-turn script.
- Do not write instructions like "when the agent says X, say Y".
- L1 must have no proactive adversarial behavior.
- L2 must include adversarial behavior that cools down by itself within one or two turns.
- L3 must include adversarial behavior that persists unless the assistant responds effectively.
- task_instructions should be a list of 4-6 concise but operational strings.
- behavioral_affordances should be a list of concrete behavior tendencies and hard boundaries.
- behavior_examples should be a list of short spoken fragments, not polished scripts.
- ending_expected should align with convertibility_ceiling.

Return JSON object only."""


def build_repair_prompt(
    original_prompt: str,
    native: dict[str, Any] | None,
    reasons: list[str],
) -> str:
    return f"""{original_prompt}

The previous output failed local validation.

Validation failures:
{json.dumps(reasons, ensure_ascii=False, indent=2)}

Previous JSON output:
{compact_json(native or {}, 18000)}

Repair it and return one complete valid JSON object only. No markdown."""


def text_blob(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False).lower()


def has_adversarial_signal(profile: dict[str, Any]) -> bool:
    blob = text_blob(
        {
            "task_instructions": profile.get("task_instructions"),
            "behavioral_affordances": profile.get("behavioral_affordances"),
            "action_design": profile.get("action_design"),
        }
    )
    markers = [
        "challenge",
        "push back",
        "resist",
        "object",
        "skeptical",
        "privacy",
        "complain",
        "interrupt",
        "bargain",
        "hostile",
        "质疑",
        "对抗",
        "拒绝",
        "打断",
        "讨价还价",
        "隐私",
        "不满",
    ]
    return any(marker in blob for marker in markers)


def has_strong_l1_conflict(profile: dict[str, Any]) -> bool:
    blob = text_blob(
        {
            "task_instructions": profile.get("task_instructions"),
            "behavioral_affordances": profile.get("behavioral_affordances"),
        }
    )
    markers = [
        "hostile",
        "insult",
        "abusive",
        "threaten",
        "keeps resisting",
        "continuous resistance",
        "持续对抗",
        "辱骂",
        "威胁",
        "连续打断",
    ]
    return any(marker in blob for marker in markers)


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items()]
    return [str(value)]


def coerce_behavior_examples(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, dict):
        examples = []
        for key, item in value.items():
            if isinstance(item, list):
                joined = " | ".join(str(x) for x in item if str(x).strip())
            else:
                joined = str(item)
            if joined.strip():
                examples.append(f"{key}: {joined}")
        return examples
    return [str(value)]


def adapt_runtime(native: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    runtime = dict(native)
    profile_id = str(native.get("profile_id") or spec.get("profile_id") or "")
    prompt_id_value = str(native.get("prompt_id") or spec.get("prompt_id") or "")
    identity = native.get("identity") if isinstance(native.get("identity"), dict) else spec.get("identity") or {}
    runtime.update(
        {
            "profile_id": profile_id,
            "prompt_id": prompt_id_value,
            "identity": identity,
            "persona": str(native.get("persona") or ""),
            "situation": str(native.get("situation") or ""),
            "task_instructions": [str(item) for item in normalize_list(native.get("task_instructions"))],
            "behavioral_affordances": [
                str(item) for item in normalize_list(native.get("behavioral_affordances"))
            ],
            "behavior_examples": coerce_behavior_examples(native.get("behavior_examples")),
            "ending_expected": str(
                native.get("ending_expected")
                or native.get("ending")
                or spec.get("convertibility_ceiling")
                or ""
            ),
            "business": native.get("business") or spec.get("business"),
            "difficulty": native.get("difficulty") or spec.get("difficulty"),
            "user_starting_position": native.get("user_starting_position")
            or spec.get("user_starting_position")
            or spec.get("intent_level"),
            "convertibility_ceiling": native.get("convertibility_ceiling")
            or spec.get("convertibility_ceiling"),
            "resolution_style": native.get("resolution_style") or spec.get("resolution_style"),
        }
    )
    runtime["meta"] = {
        **(runtime.get("meta") if isinstance(runtime.get("meta"), dict) else {}),
        "domain": native.get("domain") or spec.get("domain"),
        "difficulty": runtime.get("difficulty"),
        "user_starting_position": runtime.get("user_starting_position"),
        "convertibility_ceiling": runtime.get("convertibility_ceiling"),
        "resolution_style": runtime.get("resolution_style"),
    }
    return runtime


def validate_runtime(
    runtime: dict[str, Any],
    spec: dict[str, Any],
    placeholders: list[str],
) -> list[str]:
    reasons: list[str] = []
    for field in (
        "profile_id",
        "prompt_id",
        "identity",
        "persona",
        "situation",
        "task_instructions",
        "behavioral_affordances",
        "behavior_examples",
        "ending_expected",
        "meta",
    ):
        if field not in runtime:
            reasons.append(f"missing {field}")
    if runtime.get("profile_id") != spec.get("profile_id"):
        reasons.append("profile_id does not match spec")
    if runtime.get("prompt_id") != spec.get("prompt_id"):
        reasons.append("prompt_id does not match spec")
    difficulty = str(runtime.get("difficulty") or (runtime.get("meta") or {}).get("difficulty") or "")
    if difficulty not in VALID_DIFFICULTIES:
        reasons.append(f"invalid difficulty {difficulty}")
    identity = runtime.get("identity")
    if not isinstance(identity, dict):
        reasons.append("identity must be object")
    else:
        required = set(placeholders)
        actual = set(identity.keys())
        if required != actual:
            reasons.append(f"identity keys mismatch required={sorted(required)} actual={sorted(actual)}")
        spec_identity = spec.get("identity") if isinstance(spec.get("identity"), dict) else {}
        for key, value in spec_identity.items():
            if value is True and (not identity.get(key) or identity.get(key) is True):
                reasons.append(f"identity {key} was not concretely filled")
            elif value is not True and identity.get(key) != value:
                reasons.append(f"identity {key} does not preserve concrete spec value")
    for field in ("persona", "situation", "ending_expected"):
        if not str(runtime.get(field) or "").strip():
            reasons.append(f"{field} is empty")
    for field in ("task_instructions", "behavioral_affordances", "behavior_examples"):
        if not isinstance(runtime.get(field), list) or not runtime.get(field):
            reasons.append(f"{field} must be non-empty list")
    if difficulty in {"L2", "L3"} and not has_adversarial_signal({**runtime, **spec}):
        reasons.append(f"{difficulty} has no adversarial behavior signal")
    if difficulty == "L1" and has_strong_l1_conflict(runtime):
        reasons.append("L1 appears proactively adversarial")
    if SCRIPTED_RE.search(text_blob(runtime)):
        reasons.append("profile appears scripted")
    action_design = str(spec.get("action_design") or "")
    if action_design and action_design[:80].lower() not in text_blob(runtime):
        native_notes = text_blob(runtime.get("native_notes") or "")
        if action_design[:40].lower() not in text_blob(runtime) and action_design[:40].lower() not in native_notes:
            reasons.append("profile may not reflect action_design")
    return reasons


def generate_one(
    client: ChatClient,
    args: argparse.Namespace,
    spec: dict[str, Any],
    prompt_by_id: dict[str, dict[str, Any]],
    guide: str,
    stage2: list[dict[str, Any]],
    behavior_pool: list[dict[str, Any]],
    noise_pool: list[dict[str, Any]],
) -> dict[str, Any]:
    pid = str(spec.get("prompt_id") or "")
    prompt_item = prompt_by_id.get(pid)
    if not prompt_item:
        return {
            "ok": False,
            "profile_id": spec.get("profile_id"),
            "spec": spec,
            "reasons": [f"unknown prompt_id {pid}"],
        }

    generation_prompt = build_generation_prompt(
        args.domain,
        spec,
        prompt_item,
        guide,
        nearest_rows(stage2, spec, args.stage2_sample),
        nearest_rows(behavior_pool, spec, args.behavior_sample),
        nearest_rows(noise_pool, spec, args.noise_sample),
        args.lang,
    )
    raw = ""
    native: dict[str, Any] | None = None
    reasons: list[str] = []
    for repair_round in range(args.repair_rounds + 1):
        try:
            raw = client.call(
                generation_prompt
                if repair_round == 0
                else build_repair_prompt(generation_prompt, native, reasons)
            )
            native = parse_json_object(raw)
        except Exception as exc:  # noqa: BLE001
            reasons = [f"generation_or_parse_failed: {exc}"]
            continue
        native = {**spec, **native}
        runtime = adapt_runtime(native, spec)
        reasons = validate_runtime(runtime, spec, prompt_placeholders(prompt_item))
        if not reasons:
            return {
                "ok": True,
                "profile_id": spec.get("profile_id"),
                "native": native,
                "runtime": runtime,
                "repair_round": repair_round,
            }

    return {
        "ok": False,
        "profile_id": spec.get("profile_id"),
        "spec": spec,
        "native": native,
        "raw": raw,
        "reasons": reasons,
    }


def validate_specs(specs: list[dict[str, Any]], prompt_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures = []
    seen: set[str] = set()
    for spec in specs:
        reasons = []
        for field in ("profile_id", "prompt_id", "difficulty", "identity", "action_design"):
            if field not in spec:
                reasons.append(f"missing {field}")
        if spec.get("profile_id") in seen:
            reasons.append("duplicate profile_id")
        seen.add(str(spec.get("profile_id") or ""))
        if spec.get("difficulty") not in VALID_DIFFICULTIES:
            reasons.append(f"invalid difficulty {spec.get('difficulty')}")
        prompt_item = prompt_by_id.get(str(spec.get("prompt_id") or ""))
        if not prompt_item:
            reasons.append(f"unknown prompt_id {spec.get('prompt_id')}")
        elif isinstance(spec.get("identity"), dict):
            required = set(prompt_placeholders(prompt_item))
            actual = set(spec["identity"].keys())
            if required != actual:
                reasons.append(f"identity keys mismatch required={sorted(required)} actual={sorted(actual)}")
        else:
            reasons.append("identity must be object")
        if reasons:
            failures.append({"profile_id": spec.get("profile_id"), "spec": spec, "reasons": reasons})
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate benchmark profiles from profile_spec.json")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--prompts", required=True, type=Path)
    parser.add_argument("--stage2", required=True, type=Path)
    parser.add_argument("--noise-pool", required=True, type=Path)
    parser.add_argument("--behavior-pool", required=True, type=Path)
    parser.add_argument("--guide", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--stage2-sample", type=int, default=8)
    parser.add_argument("--behavior-sample", type=int, default=12)
    parser.add_argument("--noise-sample", type=int, default=10)
    parser.add_argument("--repair-rounds", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default="open_router")
    parser.add_argument("--temperature", type=float, default=0.55)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    paths = output_paths(args.output)
    specs = [normalize_spec(row, args.domain) for row in read_json_or_jsonl(args.spec)]
    prompts = read_json_or_jsonl(args.prompts)
    prompt_by_id = {prompt_id(item): item for item in prompts if prompt_id(item)}
    selected_specs = selected_slice(specs, args.start, args.count)
    spec_failures = validate_specs(selected_specs, prompt_by_id)
    if spec_failures:
        write_jsonl(paths["failed"], spec_failures)
        write_json(
            paths["manifest"],
            {
                "status": "spec_validation_failed",
                "valid_profiles": 0,
                "failed_profiles": len(spec_failures),
                "outputs": {"failed_profiles": str(paths["failed"])},
            },
        )
        LOG.error("spec validation failed for %d selected rows", len(spec_failures))
        return 2
    if args.validate_only:
        write_jsonl(paths["failed"], [])
        write_json(
            paths["manifest"],
            {
                "status": "validated",
                "selected_specs": len(selected_specs),
                "outputs": {"failed_profiles": str(paths["failed"])},
            },
        )
        LOG.info("validated %d specs", len(selected_specs))
        return 0

    stage2 = read_json_or_jsonl(args.stage2)
    noise_pool = read_json_or_jsonl(args.noise_pool)
    behavior_pool = read_json_or_jsonl(args.behavior_pool)
    guide = args.guide.read_text(encoding="utf-8")
    client = ChatClient(
        api_base=args.api_base,
        model=args.model,
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        retries=args.retries,
        timeout=args.timeout,
    )

    LOG.info("generating %d profiles with workers=%d", len(selected_specs), args.workers)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_map = {
            pool.submit(
                generate_one,
                client,
                args,
                spec,
                prompt_by_id,
                guide,
                stage2,
                behavior_pool,
                noise_pool,
            ): spec
            for spec in selected_specs
        }
        for future in as_completed(future_map):
            spec = future_map[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {
                    "ok": False,
                    "profile_id": spec.get("profile_id"),
                    "spec": spec,
                    "reasons": [f"uncaught_error: {exc}"],
                }
            results.append(result)
            LOG.info(
                "%s [%s] %d/%d",
                result.get("profile_id"),
                "OK" if result.get("ok") else "FAIL",
                len(results),
                len(selected_specs),
            )

    order = {str(spec.get("profile_id")): idx for idx, spec in enumerate(selected_specs)}
    results.sort(key=lambda row: order.get(str(row.get("profile_id")), 10**9))
    native_rows = [row["native"] for row in results if row.get("ok")]
    runtime_rows = [row["runtime"] for row in results if row.get("ok")]
    failed_rows = [
        {key: value for key, value in row.items() if key not in {"ok", "runtime"}}
        for row in results
        if not row.get("ok")
    ]
    write_jsonl(paths["native"], native_rows)
    write_jsonl(paths["runtime"], runtime_rows)
    write_jsonl(paths["failed"], failed_rows)
    write_json(
        paths["manifest"],
        {
            "status": "complete" if not failed_rows else "complete_with_failures",
            "domain": args.domain,
            "lang": args.lang,
            "spec": str(args.spec),
            "prompts": str(args.prompts),
            "stage2": str(args.stage2),
            "noise_pool": str(args.noise_pool),
            "behavior_pool": str(args.behavior_pool),
            "guide": str(args.guide),
            "model": args.model,
            "provider": args.provider,
            "selected_specs": len(selected_specs),
            "valid_profiles": len(runtime_rows),
            "failed_profiles": len(failed_rows),
            "repair_rounds": args.repair_rounds,
            "outputs": {
                "profiles_native": str(paths["native"]),
                "profiles_runtime": str(paths["runtime"]),
                "failed_profiles": str(paths["failed"]),
                "repair_manifest": str(paths["manifest"]),
            },
        },
    )
    LOG.info("wrote valid=%d failed=%d to %s", len(runtime_rows), len(failed_rows), paths["dir"])
    return 0 if not failed_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
