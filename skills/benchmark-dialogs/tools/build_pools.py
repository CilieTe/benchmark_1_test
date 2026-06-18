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

LANG_MARKERS = {
    "spanish": {
        "que", "no", "si", "sí", "pero", "para", "con", "usted", "pago",
        "cuenta", "hoy", "mañana", "pesos", "señor", "señora", "bueno",
        "este", "por", "favor", "soy", "yo", "de", "la", "el",
    },
    "indonesian": {
        "saya", "ini", "itu", "belum", "sudah", "nanti", "kak", "pak",
        "bu", "iya", "tidak", "bayar", "berapa", "hari", "mau", "bisa",
        "nya", "sih",
    },
    "tagalog": {
        "po", "hindi", "ako", "kayo", "si", "ng", "sa", "ang", "wala",
        "bayad", "anak", "trabaho", "sige", "opo", "nasa", "tumawag",
    },
    "english": {
        "yes", "no", "ok", "hello", "hi", "payment", "pay", "today",
        "tomorrow", "account", "loan", "bank", "call", "number",
    },
}

EVENT_REVIEW_REQUIRED = {
    "asr_garbled",
    "code_mixing",
    "truncated_utterance",
    "non_logical_speech",
    "contradictory_answer",
    "wrong_slot_answer",
    "referent_ambiguity",
    "temporal_ambiguity",
    "numeric_ambiguity",
    "role_confusion",
    "indirect_identity_correction",
    "implicit_confirmation",
    "implicit_refusal",
    "sarcastic_compliance",
    "hostile_cooperation",
    "third_party_boundary_probe",
    "privacy_boundary_probe",
    "payment_intent_ambiguous",
    "conditioned_agreement",
    "face_saving_evasion",
    "authority_deflection",
    "procedural_pushback",
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
    data["source_dialog_id"] = record.get("id", "")
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


def tokens(text: str) -> list[str]:
    return [w.lower().strip(".,;:!?¿¡()[]\"'") for w in text.split() if w.strip()]


def dominant_language_from_system(system_text: str) -> str:
    low = system_text.lower()
    if "filipino" in low or "tagalog" in low or "tonik" in low:
        return "tagalog"
    if "indones" in low or "bahasa" in low:
        return "indonesian"
    if "español" in low or "spanish" in low or "mexic" in low or "banco azteca" in low:
        return "spanish"
    return "unknown"


def language_hits(text: str) -> dict[str, int]:
    word_set = set(tokens(text))
    return {lang: len(word_set & markers) for lang, markers in LANG_MARKERS.items()}


def is_code_mixing(text: str, dominant_language: str) -> bool:
    hits = language_hits(text)
    active = [lang for lang, count in hits.items() if count >= 2]
    off_domain = [
        lang for lang, count in hits.items()
        if lang != dominant_language and count >= 2
    ]
    return len(active) >= 2 or bool(off_domain)


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
    if words:
        filler_count = sum(1 for w in lower_words if w in FILLER_WORDS)
        if filler_count / max(len(words), 1) > 0.5:
            score += 3
            ntype = ntype or "minimal_feedback"
    if any(w in markers for markers in CODE_MIX_MARKERS.values() for w in lower_words):
        if len(lower_words) <= 3:
            score += 2
            ntype = "code_mixing"
    return score, ntype


def normalize_noise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def build_noise_pool(dialogs: list[dict[str, Any]], max_per_text: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    text_counts: Counter[str] = Counter()
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
            text_key = normalize_noise_text(text)
            if max_per_text > 0 and text_counts[text_key] >= max_per_text:
                continue
            idx = turn.get("turn_index")
            key = (source_id, int(idx) if isinstance(idx, int) else -1, text)
            if key in seen:
                continue
            seen.add(key)
            text_counts[text_key] += 1
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


def build_typical_noise_pool(
    noise_rows: list[dict[str, Any]],
    max_per_type: int,
    max_contexts: int = 3,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in noise_rows:
        ntype = str(row.get("noise_type") or "unknown")
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        key = (ntype, normalize_noise_text(text))
        item = grouped.get(key)
        if item is None:
            item = {
                "noise_type": ntype,
                "text": text,
                "occurrence_count": 0,
                "source_examples": [],
                "contexts": [],
                "heuristic_score_max": row.get("heuristic_score"),
            }
            grouped[key] = item
        item["occurrence_count"] += 1
        if len(item["source_examples"]) < max_contexts:
            item["source_examples"].append(
                {
                    "source_dialog_id": row.get("source_dialog_id"),
                    "turn_index": row.get("turn_index"),
                }
            )
        context = str(row.get("context") or "").strip()
        if context and len(item["contexts"]) < max_contexts:
            item["contexts"].append(context)
        score = row.get("heuristic_score")
        if isinstance(score, (int, float)):
            current = item.get("heuristic_score_max")
            if not isinstance(current, (int, float)) or score > current:
                item["heuristic_score_max"] = score

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in grouped.values():
        by_type[str(item.get("noise_type") or "unknown")].append(item)

    rows: list[dict[str, Any]] = []
    for ntype in sorted(by_type):
        candidates = sorted(
            by_type[ntype],
            key=lambda x: (-int(x.get("occurrence_count") or 0), str(x.get("text") or "")),
        )
        rows.extend(candidates[:max_per_type] if max_per_type > 0 else candidates)
    return rows


def previous_turn(dialog: list[dict[str, Any]], idx: int, role: str | None = None) -> dict[str, Any] | None:
    prev = None
    for turn in dialog:
        t_idx = turn.get("turn_index")
        if isinstance(t_idx, int) and t_idx < idx and (role is None or turn.get("role") == role):
            prev = turn
    return prev


def add_noise_event(
    rows: list[dict[str, Any]],
    record: dict[str, Any],
    turn: dict[str, Any],
    noise_family: str,
    noise_type: str,
    reason: str,
) -> None:
    dialog = record.get("dialog") or []
    idx = turn.get("turn_index")
    text = str(turn.get("content") or "").strip()
    rows.append(
        {
            "noise_family": noise_family,
            "noise_type": noise_type,
            "source_dialog_id": record.get("id"),
            "turn_index": idx,
            "role": turn.get("role"),
            "text": text,
            "context": context_for_turn(dialog, idx if isinstance(idx, int) else -1),
            "heuristic_reason": reason,
            "candidate_source": "build_pools_rule_based_scan",
            "needs_human_review": noise_type in EVENT_REVIEW_REQUIRED,
        }
    )


def build_noise_event_candidates_rule_based(dialogs: list[dict[str, Any]], max_per_type: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    identity_q = re.compile(r"(eres|es usted|hablo con|tengo el gusto con|speaking with|berbicara dengan|apakah saya.*dengan|kayo.*ba si|usted es|you are|are you|¿.*es)", re.I)
    payment_q = re.compile(r"(pago|pagar|cubrir|payment|pay|bayar|monto|amount|cu[aá]nto|cuando|cu[aá]ndo|today|hoy|hari ini|ngayon)", re.I)
    time_words = re.compile(r"\b(later|today|tomorrow|yesterday|tonight|mañana|manana|ahorita|luego|hoy|ayer|nanti|besok|kemarin|ngayon|mamaya|bukas)\b|月底|明天|今天|昨天|晚点|稍后", re.I)
    numberish = re.compile(r"(\d|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|cien|mil|pesos|rupiah|ribu|hundred|thousand|百|千|万)", re.I)
    referents = re.compile(r"\b(he|she|him|her|they|that|this|it|él|ella|ese|esa|eso|aquel|aquella|dia|itu|ini|siya|nya)\b|他|她|那个|这个|那边|这边|上次", re.I)
    third_party = re.compile(r"(wife|husband|spouse|mother|father|brother|sister|son|daughter|老婆|老公|妈妈|爸爸|儿子|女儿|esposa|esposo|madre|padre|hermano|hermana|anak|istri|suami|ibu|bapak|kakak|adik)", re.I)
    privacy = re.compile(r"(privacy|privacidad|datos|data|informaci[oó]n|information|autoriz|consent|where.*number|d[oó]nde.*n[uú]mero|de d[oó]nde|怎么知道|隐私|授权|personal)", re.I)
    refusal = re.compile(r"(stop calling|don.?t call|no llame|no me llames|dejen de llamar|not interested|no quiero|no puedo|不方便|别打|不要再|huwag|jangan|tidak mau)", re.I)
    condition = re.compile(r"(\bif\b|cuando|si me|si ustedes|despu[eé]s de|after|first|primero|send|env[ií]a|sms|message|whatsapp|短信|先|再|kalau|jika)", re.I)
    authority = re.compile(r"(boss|manager|wife|husband|spouse|company|bank|approval|approve|老婆|老公|老板|经理|公司|银行|批准|esposa|esposo|jefe|banco|istri|suami|atasan)", re.I)
    procedure = re.compile(r"(send.*sms|send.*message|whatsapp|email|branch|office|app|link|text me|no.*phone|not.*call|短信|邮件|app|线下|门店|发给我|mande.*mensaje|env[ií]e.*mensaje)", re.I)
    sarcasm = re.compile(r"(yeah right|sure sure|whatever|as you say|lo que digas|sí claro|ajá claro|对对对|你说什么都对|terserah|iya deh)", re.I)
    hostile = re.compile(r"(idiot|stupid|fuck|shit|c[aá]llate|pendejo|idiota|est[uú]pido|ching|puta|bobo|gago|tanga|闭嘴|傻|滚|bodoh|anjing)", re.I)
    comply = re.compile(r"(ok|yes|sí|si|ya|vale|bueno|pago|pagar|pay|bayar|will|puedo|puede|好|可以|行|iya|sige)", re.I)

    for record in dialogs:
        dialog = record.get("dialog") or []
        system_text = str(dialog[0].get("content") if dialog else "")
        dominant_language = dominant_language_from_system(system_text)
        for turn in dialog:
            role = turn.get("role")
            text = str(turn.get("content") or "").strip()
            low = text.lower()
            idx = turn.get("turn_index")
            if role == "assistant" and "... [interrupted]" in low:
                add_noise_event(rows, record, turn, "surface_noise", "overlap_interrupt", "assistant turn contains interrupted marker")
                continue
            if role != "user" or low in {"[conversation begins]", "[conversation begins]"}:
                continue

            word_list = tokens(text)
            word_set = set(word_list)
            if "[silence]" in low:
                add_noise_event(rows, record, turn, "surface_noise", "silence", "user turn contains [Silence]")
            if word_list and word_set.issubset(FILLER_WORDS):
                add_noise_event(rows, record, turn, "surface_noise", "minimal_feedback", "all tokens are filler/minimal feedback")
            elif 0 < len(text) <= 8:
                add_noise_event(rows, record, turn, "surface_noise", "minimal_feedback", "short user text <= 8 chars")
            malformed = sum(1 for w in word_list if len(w) >= 8 and not re.search(r"[aeiouáéíóú]", w))
            if re.match(r"^[\d\s.,;:!?¿¡\-_]+$", text) or re.search(r"(.)\1{4,}", text) or (len(word_list) >= 8 and malformed >= 2):
                add_noise_event(rows, record, turn, "surface_noise", "asr_garbled", "numeric/punctuation only, repeated chars, or malformed-token pattern")
            if is_code_mixing(text, dominant_language):
                add_noise_event(rows, record, turn, "surface_noise", "code_mixing", "language markers indicate mixed or off-domain language")
            if re.search(r"(\.\.\.|…)$", text) or re.search(r"\[interrupted\]", low):
                add_noise_event(rows, record, turn, "surface_noise", "truncated_utterance", "ellipsis or interruption marker in user turn")

            if len(word_list) >= 6:
                unique_ratio = len(set(word_list)) / max(len(word_list), 1)
                filler_ratio = sum(1 for w in word_list if w in FILLER_WORDS) / max(len(word_list), 1)
                if unique_ratio < 0.45 or filler_ratio > 0.45:
                    add_noise_event(rows, record, turn, "semantic_noise", "non_logical_speech", "low lexical diversity or high filler ratio in longer text")
            if re.search(r"\b(yes|sí|si|iya|ok|no|not|hindi|tidak)\b", low) and re.search(r"\b(but|pero|sin embargo|但是|不过|tapi)\b", low):
                add_noise_event(rows, record, turn, "semantic_noise", "contradictory_answer", "affirm/deny plus contrast marker")
            prev = previous_turn(dialog, idx if isinstance(idx, int) else -1, "assistant")
            prev_text = str(prev.get("content") or "") if prev else ""
            if prev and payment_q.search(prev_text) and not payment_q.search(text) and 0 < len(text) < 80:
                add_noise_event(rows, record, turn, "semantic_noise", "wrong_slot_answer", "previous assistant asks payment/amount/time but user answer lacks payment/time cue")
            if referents.search(text) and len(word_list) <= 12:
                add_noise_event(rows, record, turn, "semantic_noise", "referent_ambiguity", "short answer with ambiguous referent")
            if time_words.search(text):
                add_noise_event(rows, record, turn, "semantic_noise", "temporal_ambiguity", "contains vague/relative time expression")
            if numberish.search(text):
                add_noise_event(rows, record, turn, "semantic_noise", "numeric_ambiguity", "contains number-like expression needing confirmation")
            if re.search(r"(soy su esposo|soy su esposa|saya anaknya|anak po ako|no soy|wrong number|n[uú]mero equivocado|nomor .*bapak saya|not .*person)", low):
                add_noise_event(rows, record, turn, "semantic_noise", "role_confusion", "identity denial or third-party speaker marker")

            if prev and identity_q.search(prev_text) and re.search(r"\b(i am|soy|me llamo|this is|ako si|saya|我是)\b", low) and not re.search(r"\b(yes|sí|si|correct|correcto|iya|是的)\b", low):
                add_noise_event(rows, record, turn, "pragmatic_noise", "indirect_identity_correction", "identity question followed by self-identification without direct yes/no")
            if prev and re.search(r"(puedes atender|can you talk|tienes.*momento|listen|escuch|o[ií]r|hablar)", prev_text, re.I) and re.search(r"\b(ok|sí|si|ya|bueno|go ahead|dime|tell me|adelante|iya|sige)\b", low):
                add_noise_event(rows, record, turn, "pragmatic_noise", "implicit_confirmation", "availability question answered with proceed/listening cue")
            if refusal.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "implicit_refusal", "refusal/stop-call phrase")
            if sarcasm.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "sarcastic_compliance", "sarcasm-like compliance phrase")
            if hostile.search(text) and comply.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "hostile_cooperation", "hostile words plus compliance/payment cue")
            if third_party.search(text) and re.search(r"(debt|loan|account|cuenta|deuda|pago|utang|pinjaman|payment|信息|账户)", text, re.I):
                add_noise_event(rows, record, turn, "pragmatic_noise", "third_party_boundary_probe", "third-party/family marker near debt/account/payment terms")
            if privacy.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "privacy_boundary_probe", "privacy/data/source/authorization phrase")
            if re.search(r"(maybe|maybe later|see|try|if i can|cuando pueda|a ver|vemos|quiz[aá]s|tal vez|有钱|看看|nanti|mungkin|usahakan)", low):
                add_noise_event(rows, record, turn, "pragmatic_noise", "payment_intent_ambiguous", "ambiguous payment-intent phrase")
            if condition.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "conditioned_agreement", "conditional/procedural condition marker")
            if re.search(r"(not.*money|no.*dinero|no es.*dinero|not broke|不是没钱|hindi.*pera|bukan.*uang)", low):
                add_noise_event(rows, record, turn, "pragmatic_noise", "face_saving_evasion", "face-saving money denial marker")
            if authority.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "authority_deflection", "decision/payment authority shifted to person/org")
            if procedure.search(text):
                add_noise_event(rows, record, turn, "pragmatic_noise", "procedural_pushback", "asks to change channel/process")

    seen: set[tuple[str, str, Any, str | None]] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = (row["noise_type"], str(row.get("source_dialog_id")), row.get("turn_index"), row.get("role"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in deduped:
        by_type[str(row["noise_type"])].append(row)

    selected: list[dict[str, Any]] = []
    for noise_type in sorted(by_type):
        chosen: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        candidates = sorted(
            by_type[noise_type],
            key=lambda r: (str(r.get("source_dialog_id") or ""), -len(str(r.get("context") or ""))),
        )
        for row in candidates:
            source_id = str(row.get("source_dialog_id") or "")
            if source_id in seen_sources:
                continue
            chosen.append(row)
            seen_sources.add(source_id)
            if max_per_type > 0 and len(chosen) >= max_per_type:
                break
        if max_per_type <= 0 or len(chosen) < max_per_type:
            keys = {(r.get("source_dialog_id"), r.get("turn_index"), r.get("role")) for r in chosen}
            for row in candidates:
                key = (row.get("source_dialog_id"), row.get("turn_index"), row.get("role"))
                if key in keys:
                    continue
                chosen.append(row)
                keys.add(key)
                if max_per_type > 0 and len(chosen) >= max_per_type:
                    break
        for i, row in enumerate(chosen, 1):
            row = dict(row)
            row["event_id"] = f"{noise_type}_{i:03d}"
            selected.append(row)
    return selected


def build_noise_event_llm_prompt(record: dict[str, Any], domain: str, max_chars: int) -> str:
    dialog = dialog_to_text(record.get("dialog") or [], max_chars)
    return f"""You are mining real `{domain}` phone-call dialogs for semantic and pragmatic noise candidates.

Return only events that are clearly supported by the dialog. Do not include surface artifacts such as silence, filler-only feedback, code mixing, ASR garbling, truncation, or assistant interruption; those are handled by deterministic rules.

Allowed semantic_noise types:
- non_logical_speech
- contradictory_answer
- wrong_slot_answer
- referent_ambiguity
- temporal_ambiguity
- numeric_ambiguity
- role_confusion

Allowed pragmatic_noise types:
- indirect_identity_correction
- implicit_confirmation
- implicit_refusal
- sarcastic_compliance
- hostile_cooperation
- third_party_boundary_probe
- privacy_boundary_probe
- payment_intent_ambiguous
- conditioned_agreement
- face_saving_evasion
- authority_deflection
- procedural_pushback

Dialog:
\"\"\"
{dialog}
\"\"\"

Return a JSON array only. Each object must have:
{{
  "noise_family": "semantic_noise or pragmatic_noise",
  "noise_type": "one allowed type",
  "turn_index": 5,
  "text": "verbatim user text from that turn",
  "heuristic_reason": "short evidence-based reason"
}}

Rules:
- Only user turns are eligible.
- Use exact turn_index values from the dialog.
- Do not invent or paraphrase text.
- The `heuristic_reason` must cite only evidence visible in the included dialog context.
- Do not mention facts, actions, or future intentions that are not explicitly present in the selected turn or its nearby context.
- If no strong candidates exist, return [].
- Prefer precision over recall.
"""


def extract_noise_events_one(
    client: ChatClient,
    record: dict[str, Any],
    domain: str,
    max_chars: int,
) -> list[dict[str, Any]]:
    raw = client.call(build_noise_event_llm_prompt(record, domain, max_chars))
    data = parse_json_array(raw)
    dialog = record.get("dialog") or []
    turn_by_index = {
        turn.get("turn_index"): turn
        for turn in dialog
        if isinstance(turn.get("turn_index"), int)
    }
    rows: list[dict[str, Any]] = []
    allowed_families = {"semantic_noise", "pragmatic_noise"}
    for item in data:
        if not isinstance(item, dict):
            continue
        family = str(item.get("noise_family") or "")
        noise_type = str(item.get("noise_type") or "")
        idx = item.get("turn_index")
        if family not in allowed_families or not isinstance(idx, int):
            continue
        turn = turn_by_index.get(idx)
        if not turn or turn.get("role") != "user":
            continue
        text = str(turn.get("content") or "").strip()
        if not text:
            continue
        rows.append(
            {
                "noise_family": family,
                "noise_type": noise_type,
                "source_dialog_id": record.get("id"),
                "turn_index": idx,
                "role": "user",
                "text": text,
                "context": context_for_turn(dialog, idx),
                "heuristic_reason": str(item.get("heuristic_reason") or "chatdemo candidate"),
                "candidate_source": "chatdemo_noise_event_mining",
                "needs_human_review": True,
            }
        )
    return rows


def cap_noise_events_by_type(rows: list[dict[str, Any]], max_per_type: int) -> list[dict[str, Any]]:
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, Any, str | None]] = set()
    for row in rows:
        key = (
            str(row.get("noise_type") or ""),
            str(row.get("source_dialog_id") or ""),
            row.get("turn_index"),
            row.get("role"),
        )
        if key in seen or not key[0]:
            continue
        seen.add(key)
        by_type[key[0]].append(row)

    selected: list[dict[str, Any]] = []
    for noise_type in sorted(by_type):
        chosen: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        candidates = sorted(
            by_type[noise_type],
            key=lambda r: (str(r.get("source_dialog_id") or ""), -len(str(r.get("context") or ""))),
        )
        for row in candidates:
            source_id = str(row.get("source_dialog_id") or "")
            if source_id in seen_sources:
                continue
            chosen.append(row)
            seen_sources.add(source_id)
            if max_per_type > 0 and len(chosen) >= max_per_type:
                break
        if max_per_type <= 0 or len(chosen) < max_per_type:
            keys = {(r.get("source_dialog_id"), r.get("turn_index"), r.get("role")) for r in chosen}
            for row in candidates:
                key = (row.get("source_dialog_id"), row.get("turn_index"), row.get("role"))
                if key in keys:
                    continue
                chosen.append(row)
                keys.add(key)
                if max_per_type > 0 and len(chosen) >= max_per_type:
                    break
        for i, row in enumerate(chosen, 1):
            item = dict(row)
            item["event_id"] = f"{noise_type}_{i:03d}"
            selected.append(item)
    return selected


def build_noise_event_candidates_chatdemo(
    client: ChatClient,
    dialogs: list[dict[str, Any]],
    domain: str,
    max_per_type: int,
    workers: int,
    max_chars: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surface_rows = [
        row for row in build_noise_event_candidates_rule_based(dialogs, 0)
        if row.get("noise_family") == "surface_noise"
    ]
    llm_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(extract_noise_events_one, client, record, domain, max_chars): record
            for record in dialogs
        }
        for i, fut in enumerate(as_completed(futures), 1):
            record = futures[fut]
            source_id = record.get("id", "")
            try:
                rows = fut.result()
                llm_rows.extend(rows)
                LOG.info("[%d/%d] noise events ok: %s rows=%d", i, len(futures), str(source_id)[:16], len(rows))
            except Exception as exc:  # noqa: BLE001
                failed_rows.append({"source_dialog_id": source_id, "error": str(exc)})
                LOG.warning("[%d/%d] noise events failed: %s %s", i, len(futures), source_id, exc)
    return cap_noise_events_by_type(surface_rows + llm_rows, max_per_type), failed_rows


def write_noise_event_review(path: Path, rows: list[dict[str, Any]]) -> None:
    by_type = Counter(str(r.get("noise_type", "")) for r in rows)
    by_family = Counter(str(r.get("noise_family", "")) for r in rows)
    review_counts = Counter(bool(r.get("needs_human_review")) for r in rows)
    needs_review = sorted(t for t in by_type if t in EVENT_REVIEW_REQUIRED)
    stable = sorted(t for t in by_type if t not in EVENT_REVIEW_REQUIRED)
    lines = [
        "# Noise Event Pool Review Notes",
        "",
        "This file summarizes `noise_event_pool_candidate.jsonl` output.",
        "Rows are candidate labels, not gold labels.",
        "By default, surface noise is rule-based and semantic/pragmatic noise is mined by Chatdemo.",
        "",
        "## Counts",
        "",
        f"- Total rows: {len(rows)}",
        f"- Family counts: {dict(by_family)}",
        f"- Needs human review: {review_counts.get(True, 0)}",
        f"- Usually stable surface rows: {review_counts.get(False, 0)}",
        "",
        "## Type Counts",
        "",
        "| noise_type | rows | human review |",
        "| --- | ---: | --- |",
    ]
    for noise_type, count in sorted(by_type.items()):
        flag = "yes" if noise_type in EVENT_REVIEW_REQUIRED else "optional"
        lines.append(f"| `{noise_type}` | {count} | {flag} |")
    lines.extend(
        [
            "",
            "## Best Human-QC Targets",
            "",
            "These types should be reviewed before use in final benchmark generation:",
            "",
        ]
    )
    lines.extend(f"- `{t}`" for t in needs_review)
    lines.extend(
        [
            "",
            "These types are usually stable but still benefit from spot checks:",
            "",
        ]
    )
    lines.extend(f"- `{t}`" for t in stable)
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `semantic_noise` and `pragmatic_noise` are heuristic candidates and should not be treated as gold labels.",
            "- `asr_garbled`, `code_mixing`, and `truncated_utterance` are surface-level but still need review because rule-based language/noise detection can overfire.",
            "- Prefer this event pool for discovery and taxonomy work. Use only reviewed rows for release-quality profile generation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    parser.add_argument("--max-noise-per-text", type=int, default=10)
    parser.add_argument("--max-typical-noise-per-type", type=int, default=20)
    parser.add_argument("--max-noise-events-per-type", type=int, default=20)
    parser.add_argument(
        "--noise-event-mode",
        choices=["chatdemo", "rules", "off"],
        default="chatdemo",
        help="Build noise_event_pool_candidate with Chatdemo semantic/pragmatic mining, local rules only, or disable it.",
    )
    parser.add_argument("--skip-stage1", action="store_true", help="Reuse existing stage1 file in output dir")
    parser.add_argument("--only-stage2", action="store_true", help="Repair only stage2_typical_personas from existing stage1")
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
    typical_noise_path = args.output / "noise_pool_typical.jsonl"
    noise_event_path = args.output / "noise_event_pool_candidate.jsonl"
    noise_event_review_path = args.output / "noise_event_pool_review.md"
    noise_event_failed_path = args.output / "noise_event_failed.jsonl"
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

    if args.only_stage2:
        stage1_rows = read_existing_stage1(stage1_path)
        LOG.info("reused stage1 rows: %d", len(stage1_rows))
        num_personas = choose_num_personas(len(stage1_rows), args.num_personas)
        stage2_rows = extract_stage2(client, stage1_rows, args.domain, num_personas)
        write_jsonl(stage2_path, stage2_rows)
        LOG.info("stage2 rows: %d", len(stage2_rows))
        report = {}
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        report["stage2_typical_personas"] = len(stage2_rows)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LOG.info("updated report: %s", report_path)
        return 0

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

    noise_rows = build_noise_pool(dialogs, args.max_noise_per_text)
    write_jsonl(noise_path, noise_rows)
    LOG.info("noise rows: %d", len(noise_rows))

    typical_noise_rows = build_typical_noise_pool(noise_rows, args.max_typical_noise_per_type)
    write_jsonl(typical_noise_path, typical_noise_rows)
    LOG.info("typical noise rows: %d", len(typical_noise_rows))

    noise_event_failed_rows: list[dict[str, Any]] = []
    if args.noise_event_mode == "off":
        noise_event_rows = []
        noise_event_failed_path.write_text("", encoding="utf-8")
    elif args.noise_event_mode == "rules":
        noise_event_rows = build_noise_event_candidates_rule_based(dialogs, args.max_noise_events_per_type)
        noise_event_failed_path.write_text("", encoding="utf-8")
    else:
        noise_event_rows, noise_event_failed_rows = build_noise_event_candidates_chatdemo(
            client,
            dialogs,
            args.domain,
            args.max_noise_events_per_type,
            args.workers,
            args.max_dialog_chars,
        )
        write_jsonl(noise_event_failed_path, noise_event_failed_rows)
    write_jsonl(noise_event_path, noise_event_rows)
    write_noise_event_review(noise_event_review_path, noise_event_rows)
    LOG.info("noise event candidate rows: %d", len(noise_event_rows))

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
        "noise_pool_typical": len(typical_noise_rows),
        "noise_type_counts": Counter(str(r.get("noise_type", "")) for r in noise_rows),
        "typical_noise_type_counts": Counter(str(r.get("noise_type", "")) for r in typical_noise_rows),
        "noise_event_pool_candidate": len(noise_event_rows),
        "noise_event_mode": args.noise_event_mode,
        "noise_event_failed": len(noise_event_failed_rows),
        "noise_event_family_counts": Counter(str(r.get("noise_family", "")) for r in noise_event_rows),
        "noise_event_type_counts": Counter(str(r.get("noise_type", "")) for r in noise_event_rows),
        "noise_event_review_required": sum(1 for r in noise_event_rows if r.get("needs_human_review")),
        "max_noise_per_text": args.max_noise_per_text,
        "max_typical_noise_per_type": args.max_typical_noise_per_type,
        "max_noise_events_per_type": args.max_noise_events_per_type,
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
