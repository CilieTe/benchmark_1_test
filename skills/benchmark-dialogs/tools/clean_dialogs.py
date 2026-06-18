#!/usr/bin/env python3
"""Clean request-log or Schema A dialog JSONL for benchmark pool building.

Supported inputs:
- Raw request logs with messages/gen_record fields.
- Schema A records with id/type/dialog/meta fields.

Cleaning:
- Convert raw request logs to Schema A when needed.
- Classify records as conversation / NER / other by system prompt markers.
- For each (call_id, kind), keep the record with the longest dialog.
- Write conversation records with turn_count > min_turns.
- Optionally write NER and other sidecar files.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any


LOG = logging.getLogger("clean_dialogs")

CONV_MARKERS = [
    "ROL Y OBJETIVO",
    "PART 1: CORE DIRECTIVES",
    "Role & Objective",
    "Role and Objective",
    "# Role & Objective",
    "#Role Definition",
    "# Role and Objective",
    "#Role and Objective",
    "SYSTEM ROLE",
    "Instrucciones de Personalidad y Objetivo",
    "Instrucciones del Sistema",
    "BACKGROUND INFORMATION",
    "# ROLE",
    "# Role",
    "ROL Y PERSONALIDAD",
    "System Role (LLM Instruction)",
]

NER_MARKERS = [
    "conversation analysis robot",
    "NER Instruction",
    "As As a conversation analysis robot",
]


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                LOG.warning("skip invalid json line %s: %s", line_no, exc)


def schema_a_turn(role: str, content: str, idx: int) -> dict[str, Any]:
    return {
        "turn_index": idx,
        "role": role,
        "content": content or "",
        "loss": None,
        "tags": [],
        "evaluate": None,
        "analysis": None,
        "metrics": None,
        "extras": None,
        "review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "need_review": None,
            "review": None,
            "status": None,
        },
        "settings": {"segments": None},
        "laep": {"id": "", "remark": None, "created_by": ""},
    }


def raw_to_schema_a(raw: dict[str, Any]) -> dict[str, Any]:
    gen = raw.get("gen_record") or {}
    call_id = (
        gen.get("call_id")
        or gen.get("session_id")
        or raw.get("id")
        or raw.get("call_id")
        or ""
    )
    messages = raw.get("messages") or []
    dialog = [
        schema_a_turn(str(msg.get("role", "")), str(msg.get("content", "")), idx)
        for idx, msg in enumerate(messages)
    ]
    meta = {
        "config": raw.get("config"),
        "gen_record": gen,
        "resource": raw.get("resource"),
    }
    return {
        "id": str(call_id),
        "type": "compress",
        "dialog": dialog,
        "meta": meta,
    }


def normalize_record(obj: dict[str, Any]) -> dict[str, Any]:
    if "dialog" in obj and isinstance(obj.get("dialog"), list):
        return obj
    if "messages" in obj:
        return raw_to_schema_a(obj)
    return {
        "id": str(obj.get("id", "")),
        "type": "compress",
        "dialog": [],
        "meta": {"raw": obj},
    }


def system_content(record: dict[str, Any]) -> str:
    dialog = record.get("dialog") or []
    if not dialog:
        return ""
    return str(dialog[0].get("content") or "")


def classify_record(record: dict[str, Any]) -> str:
    s = system_content(record)[:3000]
    for marker in CONV_MARKERS:
        if marker in s:
            return "conv"
    for marker in NER_MARKERS:
        if marker in s:
            return "ner"
    low = s.lower()
    if s.startswith("system:As As"):
        return "ner"
    if len(s) < 2000 and ("Objective:" in s or "Background:" in s or "Current Time:" in s):
        return "ner"
    if len(s) < 2000 and (
        "dialogue analyzer" in low
        or "extracting and structuring" in low
        or "calculate the number of overdue days" in low
    ):
        return "ner"
    if record.get("dialog"):
        return "conv" if not s else "other"
    return "other"


def clean(input_path: Path, min_turns: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    stats: Counter[str] = Counter()

    for _, obj in iter_jsonl(input_path):
        stats["read"] += 1
        record = normalize_record(obj)
        kind = classify_record(record)
        stats[f"classified_{kind}"] += 1
        cid = str(record.get("id") or "")
        groups.setdefault((cid, kind), []).append(record)

    best_records: list[tuple[str, dict[str, Any]]] = []
    duplicates = 0
    for (cid, kind), records in groups.items():
        best = max(records, key=lambda r: len(r.get("dialog") or []))
        duplicates += len(records) - 1
        best_records.append((kind, best))

    conv_all = [r for kind, r in best_records if kind == "conv"]
    ner = [r for kind, r in best_records if kind == "ner"]
    other = [r for kind, r in best_records if kind == "other"]
    conv = [r for r in conv_all if len(r.get("dialog") or []) > min_turns]

    stats["groups"] = len(groups)
    stats["duplicates_discarded"] = duplicates
    stats["conv_before_turn_filter"] = len(conv_all)
    stats["conv_after_turn_filter"] = len(conv)
    stats["conv_turn_filter_removed"] = len(conv_all) - len(conv)
    stats["ner_output"] = len(ner)
    stats["other_output"] = len(other)
    return conv, ner, other, dict(stats)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean benchmark dialog JSONL")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--min-turns", type=int, default=6)
    parser.add_argument("--ner-output", type=Path)
    parser.add_argument("--other-output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    conv, ner, other, stats = clean(args.input, args.min_turns)
    write_jsonl(args.output, conv)

    if args.ner_output:
        write_jsonl(args.ner_output, ner)
    if args.other_output:
        write_jsonl(args.other_output, other)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    LOG.info("wrote conversations: %d -> %s", len(conv), args.output)
    LOG.info("stats: %s", json.dumps(stats, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
