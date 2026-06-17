#!/usr/bin/env python3
"""Build benchmark pools from cleaned dialogs.

Minimal v1 pipeline:
- stage1_per_conversation.jsonl: LLM summary per dialog, no difficulty.
- behavior_pool.jsonl: fragment-like behavior rows derived from stage1.
- noise_pool.jsonl: rule-based user-turn noise extraction with context.
- stage2_typical_personas.jsonl: LLM summary over stage1 groups.

This tool is intentionally parameterized and writes only to --output.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


LOG = logging.getLogger("build_pools")

DEFAULT_API_BASE = "http://192.168.101.15:9898"
DEFAULT_MODEL = "qwen/qwen3.6-35b-a3b"

FILLER_WORDS = {
    "ajá", "aja", "ah", "mmm", "bueno", "sí", "si", "ok", "ya", "no",
    "oh", "eh", "este", "pues", "halo", "iya", "ahh", "mm", "ehh", "oke",
    "hmm", "hello", "hi", "yes", "yeah", "nah", "huh", "uh", "um",
}

CODE_MIX_MARKERS = {
    "tagalog": {"po", "wala", "hindi", "ako", "mo", "ba", "ang", "ko", "sa", "ng", "mga"},
    "indonesian": {"nya", "ini", "itu", "sih", "kak", "pak", "bu", "saya", "nanti", "belum", "sudah"},
}


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                LOG.warning("skip invalid json line %s: %s", line_no, exc)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_json_object(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        raw = match.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    return json.loads(raw)


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


def dialog_to_text(dialog: list[dict[str, Any]], max_chars: int) -> str:
    lines = []
    for turn in dialog:
        role = turn.get("role", "?")
        if role == "system":
            label = "SYSTEM"
        elif role == "assistant":
            label = "AGENT"
        else:
            label = "USER"
        content = str(turn.get("content") or "").strip()
        lines.append(f"[{label}] {content}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        head = text[: max_chars // 2]
        tail = text[-max_chars // 2 :]
        return head + "\n...[TRUNCATED]...\n" + tail
    return text


def build_stage1_prompt(record: dict[str, Any], domain: str, max_chars: int) -> str:
    call_id = record.get("id", "")
    meta = record.get("meta") or {}
    metadata = ((meta.get("config") or {}).get("metadata") or {})
    dialog_text = dialog_to_text(record.get("dialog") or [], max_chars)
    company = metadata.get("company_name", "")
    bot_id = metadata.get("bot_id", "")

    return f"""You are analyzing real {domain} phone-call dialogs to build benchmark user pools.

Analyze one complete dialog. Extract user behavior and persona signals. Do not assign benchmark difficulty here.

Context:
- source_dialog_id: {call_id}
- company: {company}
- bot_id: {bot_id}

Dialog:
\"\"\"
{dialog_text}
\"\"\"

Return one JSON object only:
{{
  "source_dialog_id": "{call_id}",
  "persona_summary": "2-4 sentences describing who the user is in this call and what drives their behavior.",
  "user_starting_position": "A domain-specific label for the user's starting position, named from the data.",
  "communication_style": "How the user speaks: concise/fragmented/emotional/avoidant/etc.",
  "emotional_pattern": "How emotion changes over the call.",
  "decision_pattern": "How the user decides, delays, refuses, compromises, or ends the call.",
  "notable_behaviors": [
    {{"behavior_type": "short label", "description": "specific behavior pattern"}}
  ],
  "representative_quotes": [
    "short original user quote 1",
    "short original user quote 2"
  ]
}}

Rules:
- Use labels that fit this domain; do not force fixed intent categories.
- Keep original user quotes short and verbatim.
- Do not include markdown fences.
- Do not include difficulty.
"""


def extract_stage1_one(
    client: ChatClient,
    record: dict[str, Any],
    domain: str,
    max_chars: int,
) -> dict[str, Any]:
    prompt = build_stage1_prompt(record, domain, max_chars)
    raw = client.call(prompt)
    data = parse_json_object(raw)
    data.setdefault("source_dialog_id", record.get("id", ""))
    data["_raw"] = raw
    return data


def load_dialogs(path: Path, limit: int) -> list[dict[str, Any]]:
    rows = [obj for _, obj in iter_jsonl(path)]
    if limit > 0:
        return rows[:limit]
    return rows


def context_for_turn(dialog: list[dict[str, Any]], idx: int, window: int = 1) -> str:
    chunks = []
    for turn in dialog:
        t_idx = turn.get("turn_index")
        if not isinstance(t_idx, int):
            continue
        if idx - window <= t_idx <= idx + window:
            role = turn.get("role")
            text = str(turn.get("content") or "").strip()
            chunks.append(f"{role}: {text}")
    return "\n".join(chunks)


def classify_noise(text: str) -> tuple[int, str | None]:
    c = text.strip()
    if not c:
        return 0, None
    if "[silence]" in c.lower():
        return 10, "silence"
    if re.match(r"^[\d\s.,;:!?¿¡\-_]+$", c):
        return 9, "asr_garbled"

    words = c.split()
    lower_words = [w.lower().strip(".,;:!?¿¡") for w in words]
    lower_set = set(lower_words)
    if len(c) <= 3:
        return 6, "minimal_feedback"
    if lower_set and lower_set.issubset(FILLER_WORDS):
        return 8, "minimal_feedback"

    score = 0
    ntype: str | None = None
    if len(c) <= 8:
        score += 3
        ntype = "minimal_feedback"
    if re.search(r"(.)\1{4,}", c):
        score += 4
        ntype = "asr_garbled"
    if re.search(r"\b[a-z]{1,3}co\b", c.lower()):
        score += 5
        ntype = "asr_garbled"
    if words:
        filler_count = sum(1 for w in lower_words if w in FILLER_WORDS)
        if filler_count / max(len(words), 1) > 0.5:
            score += 3
            ntype = ntype or "pragmatic_noise"
    for label, markers in CODE_MIX_MARKERS.items():
        if any(w in markers for w in lower_words):
            score += 2
            ntype = "code_mixing"
            break
    return score, ntype


def build_noise_pool(dialogs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for record in dialogs:
        dialog = record.get("dialog") or []
        source_id = str(record.get("id") or "")
        for turn in dialog:
            if turn.get("role") != "user":
                continue
            text = str(turn.get("content") or "").strip()
            if text in {"[Conversation Begins]", "[conversation begins]"}:
                continue
            score, ntype = classify_noise(text)
            if score < 5 or not ntype:
                continue
            idx = turn.get("turn_index")
            key = (source_id, int(idx) if isinstance(idx, int) else -1, text)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source_dialog_id": source_id,
                    "turn_index": idx,
                    "noise_type": ntype,
                    "text": text,
                    "context": context_for_turn(dialog, idx if isinstance(idx, int) else -1),
                    "heuristic_score": score,
                }
            )
    return rows


def build_behavior_pool(stage1_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in stage1_rows:
        source_id = str(item.get("source_dialog_id") or "")
        behaviors = item.get("notable_behaviors") or []
        quotes = [str(q).strip() for q in (item.get("representative_quotes") or []) if str(q).strip()]
        if not behaviors and quotes:
            behaviors = [{"behavior_type": "representative_user_expression", "description": q} for q in quotes]
        for i, behavior in enumerate(behaviors):
            if isinstance(behavior, dict):
                btype = str(behavior.get("behavior_type") or behavior.get("type") or "behavior")
                desc = str(behavior.get("description") or behavior.get("text") or "").strip()
            else:
                btype = "behavior"
                desc = str(behavior).strip()
            if not desc:
                continue
            quote = quotes[i] if i < len(quotes) else ""
            text = quote or desc
            key = (source_id, btype, text)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source_dialog_id": source_id,
                    "turn_index": None,
                    "behavior_type": btype,
                    "text": text,
                    "context": desc,
                    "why_useful": f"Shows {btype} for user simulation in this domain.",
                }
            )
    return rows


def choose_num_personas(stage1_count: int, requested: int) -> int:
    if requested > 0:
        return requested
    if stage1_count <= 0:
        return 0
    return max(6, min(60, int(math.sqrt(stage1_count) * 2)))


def build_stage2_prompt(stage1_rows: list[dict[str, Any]], domain: str, num_personas: int) -> str:
    samples = []
    for item in stage1_rows:
        behaviors = item.get("notable_behaviors") or []
        samples.append(
            {
                "source_dialog_id": item.get("source_dialog_id"),
                "user_starting_position": item.get("user_starting_position"),
                "communication_style": item.get("communication_style"),
                "emotional_pattern": item.get("emotional_pattern"),
                "decision_pattern": item.get("decision_pattern"),
                "notable_behaviors": behaviors[:3] if isinstance(behaviors, list) else behaviors,
                "quotes": (item.get("representative_quotes") or [])[:2],
            }
        )

    block = json.dumps(samples, ensure_ascii=False)
    if len(block) > 70000:
        block = block[:70000] + "\n...TRUNCATED..."

    return f"""You are deriving typical personas for a {domain} benchmark from per-conversation summaries.

Create about {num_personas} typical personas. Cover the major user starting positions, communication styles, decision patterns, and behavior mixes. Do not assign difficulty.

Stage1 samples:
{block}

Return a JSON array only. Each object must have:
{{
  "persona_id": "short stable id",
  "user_starting_position": "domain-specific starting-position label",
  "communication_style": "summary",
  "decision_pattern": "summary",
  "behavior_mix": ["behavior label 1", "behavior label 2"],
  "source_dialog_ids": ["..."],
  "coverage_note": "what coverage this persona provides"
}}

Rules:
- Use the data's own categories; do not force fixed intent labels.
- Keep personas distinct and useful for benchmark generation.
- Do not include markdown fences.
"""


def extract_stage2(client: ChatClient, stage1_rows: list[dict[str, Any]], domain: str, num_personas: int) -> list[dict[str, Any]]:
    if not stage1_rows:
        return []
    raw = client.call(build_stage2_prompt(stage1_rows, domain, num_personas))
    rows = parse_json_array(raw)
    for row in rows:
        row.setdefault("_raw_source", "stage2_llm")
    return rows


def read_existing_stage1(path: Path) -> list[dict[str, Any]]:
    rows = []
    for _, obj in iter_jsonl(path):
        rows.append(obj)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build benchmark pools from clean dialogs")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--dialogs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default="open_router")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-dialog-chars", type=int, default=18000)
    parser.add_argument("--num-personas", type=int, default=0)
    parser.add_argument("--skip-stage1", action="store_true", help="Reuse existing stage1 file in output dir")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    stage1_path = args.output / "stage1_per_conversation.jsonl"
    behavior_path = args.output / "behavior_pool.jsonl"
    noise_path = args.output / "noise_pool.jsonl"
    stage2_path = args.output / "stage2_typical_personas.jsonl"
    failed_path = args.output / "stage1_failed.jsonl"
    report_path = args.output / "build_pools_report.json"

    dialogs = load_dialogs(args.dialogs, args.limit)
    LOG.info("loaded dialogs: %d", len(dialogs))

    client = ChatClient(
        api_base=args.api_base,
        model=args.model,
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        retries=args.retries,
        timeout=args.timeout,
    )

    if args.skip_stage1:
        stage1_rows = read_existing_stage1(stage1_path)
        failed_rows: list[dict[str, Any]] = []
        LOG.info("reused stage1 rows: %d", len(stage1_rows))
    else:
        stage1_rows = []
        failed_rows = []
        with stage1_path.open("w", encoding="utf-8") as out, failed_path.open("w", encoding="utf-8") as ferr:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {
                    executor.submit(extract_stage1_one, client, record, args.domain, args.max_dialog_chars): record
                    for record in dialogs
                }
                for i, fut in enumerate(as_completed(futures), 1):
                    record = futures[fut]
                    source_id = record.get("id", "")
                    try:
                        item = fut.result()
                        stage1_rows.append(item)
                        out.write(json.dumps(item, ensure_ascii=False) + "\n")
                        out.flush()
                        LOG.info("[%d/%d] stage1 ok: %s", i, len(futures), str(source_id)[:16])
                    except Exception as exc:  # noqa: BLE001
                        failed = {"source_dialog_id": source_id, "error": str(exc)}
                        failed_rows.append(failed)
                        ferr.write(json.dumps(failed, ensure_ascii=False) + "\n")
                        ferr.flush()
                        LOG.warning("[%d/%d] stage1 failed: %s %s", i, len(futures), source_id, exc)

    noise_rows = build_noise_pool(dialogs)
    write_jsonl(noise_path, noise_rows)
    LOG.info("noise rows: %d", len(noise_rows))

    behavior_rows = build_behavior_pool(stage1_rows)
    write_jsonl(behavior_path, behavior_rows)
    LOG.info("behavior rows: %d", len(behavior_rows))

    num_personas = choose_num_personas(len(stage1_rows), args.num_personas)
    try:
        stage2_rows = extract_stage2(client, stage1_rows, args.domain, num_personas)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("stage2 failed: %s", exc)
        stage2_rows = []
    write_jsonl(stage2_path, stage2_rows)
    LOG.info("stage2 rows: %d", len(stage2_rows))

    report = {
        "domain": args.domain,
        "dialogs": len(dialogs),
        "stage1": len(stage1_rows),
        "stage1_failed": len(failed_rows),
        "noise_pool": len(noise_rows),
        "behavior_pool": len(behavior_rows),
        "stage2_typical_personas": len(stage2_rows),
        "user_starting_position_counts": Counter(
            str(r.get("user_starting_position", "")) for r in stage1_rows
        ),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOG.info("wrote report: %s", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
