#!/usr/bin/env python3
"""Generate benchmark profile specs from prompts, pools, and a domain guide.

Outputs:
- profile_spec.json
- profile_spec_failed.json
- coverage_matrix.csv
- profile_spec_qc.md
- generate_spec_manifest.json

This is a runnable v1. It keeps validation intentionally thin: the spec layer
only enforces the minimum contract needed by downstream profile generation.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


LOG = logging.getLogger("generate_spec")

DEFAULT_API_BASE = "http://192.168.101.15:9898"
DEFAULT_MODEL = "qwen/qwen3.6-35b-a3b"
VALID_DIFFICULTIES = {"L1", "L2", "L3"}
BEHAVIOR_FIELD = "action_design"
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                LOG.warning("skip invalid json line %s in %s: %s", line_no, path, exc)


def read_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [obj for _, obj in iter_jsonl(path)]
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [obj for obj in data if isinstance(obj, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"unsupported json root in {path}: {type(data).__name__}")


def compact_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = max(1, limit // 2)
    return text[:half] + "\n...[TRUNCATED]...\n" + text[-half:]


def compact_json(data: Any, limit: int) -> str:
    return compact_text(json.dumps(data, ensure_ascii=False, indent=2), limit)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def output_paths(output: Path) -> dict[str, Path]:
    if output.suffix == ".json":
        out_dir = output.parent
        spec_path = output
    else:
        out_dir = output
        spec_path = out_dir / "profile_spec.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    return {
        "dir": out_dir,
        "spec": spec_path,
        "failed": out_dir / "profile_spec_failed.json",
        "coverage": out_dir / "coverage_matrix.csv",
        "qc": out_dir / "profile_spec_qc.md",
        "manifest": out_dir / "generate_spec_manifest.json",
    }


def parse_json_array(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        raw = match.group(1).strip()
    start = raw.find("[")
    end = raw.rfind("]")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("expected JSON array")
    rows = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("expected every array item to be an object")
        rows.append(item)
    return rows


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
        "prompt_excerpt": compact_text(str(item.get("prompt") or ""), 9000),
        "function_excerpt": compact_text(str(item.get("function") or ""), 2500),
    }


def build_generation_prompt(
    domain: str,
    prompt_item: dict[str, Any],
    stage2: list[dict[str, Any]],
    noise_pool: list[dict[str, Any]],
    behavior_pool: list[dict[str, Any]],
    guide: str,
    rows_per_prompt: int,
    profile_prefix: str,
    notes: str,
) -> str:
    pid = prompt_id(prompt_item)
    count_rule = (
        f"Generate exactly {rows_per_prompt} spec rows for this prompt."
        if rows_per_prompt > 0
        else "Choose the smallest useful number of spec rows for this prompt, normally 3-6, enough to cover convertibility_ceiling."
    )
    return f"""You are generating benchmark profile specs for domain `{domain}`.

Generate specs for one assistant prompt only. Return a JSON array only.

User notes:
{notes or "(none)"}

Prompt to cover:
{compact_json(prompt_summary(prompt_item), 22000)}

Confirmed domain guide:
\"\"\"
{compact_text(guide, 50000)}
\"\"\"

Stage2 personas sample:
{compact_json(stage2[:80], 30000)}

Behavior pool sample:
{compact_json(behavior_pool[:160], 35000)}

Noise pool sample:
{compact_json(noise_pool[:120], 26000)}

Spec contract:
- one object generates exactly one profile later.
- every object MUST have:
  - profile_id
  - prompt_id, exactly "{pid}"
  - business
  - difficulty: "L1", "L2", or "L3"
  - user_starting_position
  - convertibility_ceiling
  - identity
  - resolution_style
  - action_design
- You may add extra fields if they are useful; they will be passed through.

Identity rules:
- If the prompt has no identity placeholders, use {{}}.
- If the prompt has placeholders, include exactly those keys.
- Use true when the downstream profile generator should fill a realistic value.
- Use concrete values only when the prompt or user notes require them.

Difficulty rules:
- L1: no proactive adversarial behavior.
- L2: adversarial behavior is self-resolving; even without good handling, the user cools down within one or two turns, and most L2 actions resolve after one turn.
- L3: adversarial behavior does not self-resolve unless the model responds effectively.
- L2 and L3 action_design must include explicit adversarial behavior.

Coverage rules:
- {count_rule}
- convertibility_ceiling must be covered across the rows for this prompt.
- user_starting_position major categories should be covered across the full spec file.
- behavior types should be covered and reasonably balanced; do not put every row into one behavior type.
- Do not write turn-by-turn scripts. action_design describes motives and behavior, not exact replies.
- Ground behavior in the pools, but do not copy long dialog text.

profile_id format:
- Start with "{profile_prefix}{pid}_".
- Make it stable, short, and unique.

Return JSON array only. No markdown. No explanation."""


def normalize_row(row: dict[str, Any], domain: str) -> dict[str, Any]:
    normalized = dict(row)
    if "intent_level" in normalized and "user_starting_position" not in normalized:
        normalized["user_starting_position"] = normalized["intent_level"]
    normalized.setdefault("domain", domain)
    return normalized


def validate_row(
    row: dict[str, Any],
    prompt_ids: set[str],
    placeholders_by_prompt: dict[str, list[str]],
) -> list[str]:
    reasons: list[str] = []
    for field in ("profile_id", "prompt_id", "difficulty", "identity", BEHAVIOR_FIELD):
        if field not in row:
            reasons.append(f"missing {field}")
    pid = str(row.get("prompt_id") or "")
    if pid and pid not in prompt_ids:
        reasons.append(f"unknown prompt_id {pid}")
    difficulty = str(row.get("difficulty") or "")
    if difficulty and difficulty not in VALID_DIFFICULTIES:
        reasons.append(f"invalid difficulty {difficulty}")
    if "identity" in row and not isinstance(row.get("identity"), dict):
        reasons.append("identity must be object")
    if pid in placeholders_by_prompt and isinstance(row.get("identity"), dict):
        required = set(placeholders_by_prompt[pid])
        actual = set(row["identity"].keys())
        if required and actual != required:
            reasons.append(f"identity keys mismatch required={sorted(required)} actual={sorted(actual)}")
        if not required and actual:
            reasons.append(f"identity should be empty for prompt_id {pid}")
    action_design = str(row.get(BEHAVIOR_FIELD) or "").strip()
    if not action_design:
        reasons.append(f"{BEHAVIOR_FIELD} is empty")
    elif difficulty in {"L2", "L3"} and len(action_design) < 20:
        reasons.append(f"{BEHAVIOR_FIELD} too thin for {difficulty}")
    if difficulty == "L1":
        lower = action_design.lower()
        strong_markers = [
            "insult",
            "abusive",
            "threaten",
            "refuse repeatedly",
            "continuous resistance",
            "keeps resisting",
        ]
        if any(marker in lower for marker in strong_markers):
            reasons.append("L1 appears proactively adversarial")
    return reasons


def dedupe_profile_ids(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: Counter[str] = Counter()
    output = []
    for row in rows:
        new_row = dict(row)
        profile_id = str(new_row.get("profile_id") or "").strip()
        seen[profile_id] += 1
        if profile_id and seen[profile_id] > 1:
            new_row["profile_id"] = f"{profile_id}_{seen[profile_id]}"
        output.append(new_row)
    return output


def generate_specs(
    client: ChatClient,
    args: argparse.Namespace,
    prompts: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    noise_pool: list[dict[str, Any]],
    behavior_pool: list[dict[str, Any]],
    guide: str,
    notes: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prompt_ids = {prompt_id(item) for item in prompts}
    placeholders_by_prompt = {prompt_id(item): prompt_placeholders(item) for item in prompts}
    valid: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for idx, item in enumerate(prompts, 1):
        pid = prompt_id(item)
        LOG.info("generating specs for prompt %s (%d/%d)", pid, idx, len(prompts))
        try:
            raw = client.call(
                build_generation_prompt(
                    args.domain,
                    item,
                    stage2,
                    noise_pool,
                    behavior_pool,
                    guide,
                    args.rows_per_prompt,
                    args.profile_prefix,
                    notes,
                )
            )
            rows = parse_json_array(raw)
        except Exception as exc:  # noqa: BLE001
            failed.append({"prompt_id": pid, "reason": f"generation_failed: {exc}"})
            continue

        for row_index, row in enumerate(rows):
            normalized = normalize_row(row, args.domain)
            reasons = validate_row(normalized, prompt_ids, placeholders_by_prompt)
            if reasons:
                failed.append(
                    {
                        "prompt_id": pid,
                        "row_index": row_index,
                        "reason": "; ".join(reasons),
                        "row": normalized,
                    }
                )
            else:
                valid.append(normalized)

    return dedupe_profile_ids(valid), failed


def write_coverage(path: Path, specs: list[dict[str, Any]]) -> None:
    fields = [
        "prompt_id",
        "difficulty",
        "user_starting_position",
        "convertibility_ceiling",
        "behavior_type",
        "count",
    ]
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in specs:
        key = (
            str(row.get("prompt_id") or ""),
            str(row.get("difficulty") or ""),
            str(row.get("user_starting_position") or row.get("intent_level") or ""),
            str(row.get("convertibility_ceiling") or ""),
            str(row.get("behavior_type") or row.get("primary_behavior_type") or ""),
        )
        counts[key] += 1
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key, count in sorted(counts.items()):
            writer.writerow(
                {
                    "prompt_id": key[0],
                    "difficulty": key[1],
                    "user_starting_position": key[2],
                    "convertibility_ceiling": key[3],
                    "behavior_type": key[4],
                    "count": count,
                }
            )


def qc_markdown(specs: list[dict[str, Any]], failed: list[dict[str, Any]], prompts: list[dict[str, Any]]) -> str:
    prompt_ids = [prompt_id(item) for item in prompts]
    by_prompt = Counter(str(row.get("prompt_id") or "") for row in specs)
    by_difficulty = Counter(str(row.get("difficulty") or "") for row in specs)
    by_start = Counter(str(row.get("user_starting_position") or row.get("intent_level") or "") for row in specs)
    by_ceiling = Counter(str(row.get("convertibility_ceiling") or "") for row in specs)
    missing_prompts = [pid for pid in prompt_ids if by_prompt[pid] == 0]

    warnings = []
    if failed:
        warnings.append(f"- {len(failed)} rows failed validation or generation.")
    if missing_prompts:
        warnings.append(f"- Missing generated specs for prompts: {', '.join(missing_prompts)}.")
    if not by_difficulty.get("L1"):
        warnings.append("- No L1 rows.")
    if not by_difficulty.get("L2"):
        warnings.append("- No L2 rows.")
    if not by_difficulty.get("L3"):
        warnings.append("- No L3 rows.")
    if len(by_ceiling) < 2 and specs:
        warnings.append("- convertibility_ceiling coverage looks narrow.")
    if len(by_start) < 2 and specs:
        warnings.append("- user_starting_position coverage looks narrow.")

    def fmt_counter(counter: Counter[str]) -> str:
        if not counter:
            return "- (none)"
        return "\n".join(f"- {key or '(empty)'}: {value}" for key, value in counter.most_common())

    return f"""# Profile Spec QC

## Summary

- valid_specs: {len(specs)}
- failed_rows: {len(failed)}
- prompt_count: {len(prompt_ids)}

## Prompt Coverage

{fmt_counter(by_prompt)}

## Difficulty Distribution

{fmt_counter(by_difficulty)}

## User Starting Position Distribution

{fmt_counter(by_start)}

## Convertibility Ceiling Distribution

{fmt_counter(by_ceiling)}

## Warnings

{chr(10).join(warnings) if warnings else "- No blocking warnings from local contract checks."}

## Scope

This is local contract QC only. It does not replace human review of benchmark
intent, business realism, or downstream profile quality.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate benchmark profile specs")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--prompts", required=True, type=Path)
    parser.add_argument("--stage2", required=True, type=Path)
    parser.add_argument("--noise-pool", required=True, type=Path)
    parser.add_argument("--behavior-pool", required=True, type=Path)
    parser.add_argument("--guide", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prompt-limit", type=int, default=0)
    parser.add_argument("--prompt-ids", default="", help="comma-separated prompt ids to generate")
    parser.add_argument("--rows-per-prompt", type=int, default=0)
    parser.add_argument("--profile-prefix", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--notes-file", type=Path)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default="open_router")
    parser.add_argument("--temperature", type=float, default=0.4)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    notes = args.notes
    if args.notes_file:
        notes = args.notes_file.read_text(encoding="utf-8")
    if not args.profile_prefix:
        args.profile_prefix = f"{args.domain}_"

    paths = output_paths(args.output)
    prompts = read_json_or_jsonl(args.prompts)
    if args.prompt_ids.strip():
        wanted = {item.strip() for item in args.prompt_ids.split(",") if item.strip()}
        prompts = [item for item in prompts if prompt_id(item) in wanted]
    if args.prompt_limit > 0:
        prompts = prompts[: args.prompt_limit]
    if not prompts:
        raise ValueError("no prompts selected")

    stage2 = read_json_or_jsonl(args.stage2)
    noise_pool = read_json_or_jsonl(args.noise_pool)
    behavior_pool = read_json_or_jsonl(args.behavior_pool)
    guide = args.guide.read_text(encoding="utf-8")
    LOG.info(
        "loaded prompts=%d stage2=%d noise=%d behavior=%d",
        len(prompts),
        len(stage2),
        len(noise_pool),
        len(behavior_pool),
    )

    client = ChatClient(
        api_base=args.api_base,
        model=args.model,
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        retries=args.retries,
        timeout=args.timeout,
    )

    specs, failed = generate_specs(client, args, prompts, stage2, noise_pool, behavior_pool, guide, notes)
    write_json(paths["spec"], specs)
    write_json(paths["failed"], failed)
    write_coverage(paths["coverage"], specs)
    paths["qc"].write_text(qc_markdown(specs, failed, prompts), encoding="utf-8")
    write_json(
        paths["manifest"],
        {
            "domain": args.domain,
            "prompts": str(args.prompts),
            "stage2": str(args.stage2),
            "noise_pool": str(args.noise_pool),
            "behavior_pool": str(args.behavior_pool),
            "guide": str(args.guide),
            "model": args.model,
            "provider": args.provider,
            "rows_per_prompt": args.rows_per_prompt,
            "valid_specs": len(specs),
            "failed_rows": len(failed),
            "outputs": {
                "profile_spec": str(paths["spec"]),
                "profile_spec_failed": str(paths["failed"]),
                "coverage_matrix": str(paths["coverage"]),
                "profile_spec_qc": str(paths["qc"]),
            },
        },
    )
    LOG.info("wrote valid_specs=%d failed_rows=%d to %s", len(specs), len(failed), paths["dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
