"""
将 marketing prompt + user profile 组装为最终的 assistant system prompt。

Usage:
    # 批量：读 profile JSONL + prompt JSONL，输出一一对应的最终 prompt
    python benchmark_1_test/build_prompt.py \
        -p benchmark_1_test/data/user_profiles_20260525.jsonl \
        -m benchmark_1_test/marketing_prompts.jsonl \
        -o outputs/final_prompts.jsonl

    # 单条：指定 --profile-id 和 --prompt-id
    python benchmark_1_test/build_prompt.py \
        -p benchmark_1_test/data/user_profiles_20260525.jsonl \
        -m benchmark_1_test/marketing_prompts.jsonl \
        --profile-id profile_01 --prompt-id mp_02
"""

import json
import sys
import re
import hashlib
import random
import argparse
from datetime import date


# ── 姓名提取 & identity 解析 ──────────────────────────────────

def extract_name_from_persona(persona: str) -> dict:
    import re as _re
    result = {"family": "", "given": "", "full": "", "title_en": "", "gender": ""}

    m = _re.search(r'你叫([一-鿿]{2,4})(?:[，。,\s]|$)', persona)
    if m:
        full = m.group(1)
        result["full"] = full
        result["family"] = full[0] if len(full) <= 3 else full[:2]
        result["given"] = full[1:] if len(full) <= 3 else full[2:]
        if "先生" in persona or "他" in persona or "丈夫" in persona or "父亲" in persona or "男" in persona:
            result["gender"] = "male"
            result["title_en"] = "Mr."
        elif "女士" in persona or "她" in persona or "妻子" in persona or "母亲" in persona or "女" in persona:
            result["gender"] = "female"
            result["title_en"] = "Ms."
        else:
            result["title_en"] = "Mr./Ms."
        return result

    m = _re.search(r'(?:Your name is|you are|you\'re)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', persona)
    if m:
        full = m.group(1)
        parts = full.split()
        result["full"] = full
        result["given"] = parts[0]
        result["family"] = parts[-1] if len(parts) > 1 else ""
        if any(w in persona.lower() for w in [" he ", " his ", " him ", " husband", " father", " mr.", " man "]):
            result["gender"] = "male"
            result["title_en"] = "Mr."
        elif any(w in persona.lower() for w in [" she ", " her ", " wife", " mother", " ms.", " mrs.", " woman "]):
            result["gender"] = "female"
            result["title_en"] = "Ms."
        else:
            female_names = ["sarah", "margaret", "mary", "emma", "lisa", "jennifer", "jessica", "amanda", "elizabeth", "susan", "linda", "barbara", "nancy", "karen", "michelle", "patricia", "sandra", "laura", "helen", "anna", "emily", "sophia", "olivia"]
            male_names = ["james", "john", "robert", "michael", "william", "david", "richard", "joseph", "thomas", "charles", "christopher", "daniel", "matthew", "anthony", "mark", "donald", "steven", "paul", "andrew", "joshua", "kenneth", "kevin", "brian", "george", "edward", "ronald"]
            if parts[0].lower() in female_names:
                result["gender"] = "female"
                result["title_en"] = "Ms."
            elif parts[0].lower() in male_names:
                result["gender"] = "male"
                result["title_en"] = "Mr."
            else:
                result["title_en"] = "Mr./Ms."
        return result

    return result


def _derive_name_parts(name: str) -> dict:
    if not name:
        return {}
    if re.match(r'[一-鿿]', name):
        full = name
        family = full[0] if len(full) <= 3 else full[:2]
        given = full[len(family):]
        return {"full": full, "family": family, "given": given}
    parts = name.split()
    if len(parts) == 2 and re.match(r'[一-鿿]', parts[1]):
        return {"full": name, "family": parts[0], "given": parts[1]}
    return {"full": name, "given": parts[0], "family": parts[-1] if len(parts) > 1 else ""}


def _resolve_identity(profile: dict) -> dict:
    persona = profile.get("persona", "")
    name_info = extract_name_from_persona(persona)
    explicit = profile.get("identity", {})

    name_from_id = _derive_name_parts(explicit.get("name", ""))
    full = explicit.get("full") or name_from_id.get("full") or name_info.get("full", "")
    family = explicit.get("family") or name_from_id.get("family") or name_info.get("family", "")
    given = explicit.get("given") or name_from_id.get("given") or name_info.get("given", "")
    title_en = explicit.get("title_en") or explicit.get("title") or name_info.get("title_en", "")

    return {
        "family": family,
        "given": given,
        "full": full,
        "title_en": title_en,
        "gender": name_info.get("gender", ""),
        "last_four": explicit.get("last_four", ""),
        "credit_limit": explicit.get("credit_limit", ""),
        "bank_name": explicit.get("bank_name", ""),
        "community": explicit.get("community", ""),
        "home_type": explicit.get("home_type", ""),
        "device_count": explicit.get("device_count", ""),
        "recommended_package": explicit.get("recommended_package", ""),
    }


# ── 占位符替换 ──────────────────────────────────────────────

def fill_placeholders(prompt: str, profile: dict) -> str:
    """根据 profile 替换 prompt 中的占位符。"""
    pid = profile.get("profile_id", "unknown")
    seed = int(hashlib.md5(pid.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    id_data = _resolve_identity(profile)
    text = prompt
    prompt_id = profile.get("prompt_id", "")

    # mp_02: 信用卡升级 — Ms. Zhang / 张敏 / 4827 / XX万
    if prompt_id == "mp_02":
        if id_data["title_en"] and id_data["family"]:
            text = re.sub(r'Ms\.\s*\w+|Mr\.\s*\w+', f'{id_data["title_en"]} {id_data["family"]}', text)
        if id_data["full"]:
            text = text.replace("张敏", id_data["full"])
        if id_data["family"]:
            text = text.replace("张女士", f'{id_data["family"]}女士')
        last_four = id_data["last_four"] or f"{rng.randint(1000,9999):04d}"
        text = text.replace("4827", last_four)
        credit = id_data["credit_limit"] or f"{rng.choice([10,15,20,30,50])}万"
        text = re.sub(r'XX\s*(?:万|万元|RMB)?', credit, text)

    # mp_10: 轻奢消费分期 — XX Bank
    if prompt_id == "mp_10":
        bank = id_data["bank_name"]
        if not bank:
            business = profile.get("business", "")
            bank = business if "银行" in business else "ABC Bank"
        text = text.replace("XX Bank", bank)

    # mp_27: 健身 — XX Community / Mr./Ms. XXX
    if prompt_id == "mp_27":
        community = id_data["community"] or "your community"
        text = re.sub(r'XX\s*Community', community, text)
        if id_data["title_en"] and (id_data["family"] or id_data["full"]):
            label = id_data["family"] or id_data["full"]
            text = re.sub(r'Mr\./Ms\.\s*XXX', f'{id_data["title_en"]} {label}', text)
        text = re.sub(r'X\s+sessions\s+for\s+only\s+XXX',
                      f'{rng.randint(4,12)} sessions for only ¥{rng.randint(200,600)}', text)
        text = re.sub(r'X\s+hours\s+for\s+XXX',
                      f'{rng.randint(10,40)} hours for ¥{rng.randint(500,1500)}', text)
        text = re.sub(r'X\s+points', f'{rng.randint(50,200)} points', text)

    # mp_14: WiFi — 占位符从 identity 取值
    if prompt_id == "mp_14":
        home_type = id_data.get("home_type") or "your home type"
        device_count = id_data.get("device_count") or "your device count"
        rec_pkg = id_data.get("recommended_package") or "our recommended package"
        text = text.replace("[home_type]", home_type)
        text = text.replace("[device_count]", device_count)
        text = text.replace("[recommended_package]", rec_pkg)

    # mp_20: 航司里程升级 — [X] / [Date] / [Tier]
    if prompt_id == "mp_20":
        text = re.sub(r'\[X\]', str(rng.randint(3, 15)), text)
        text = text.replace("[Date]", date.today().strftime("%Y-%m-%d"))
        text = text.replace("[Tier]", "Silver")

    # mp_36: 水疗按摩 — [current_date]
    if prompt_id == "mp_36":
        text = text.replace("[current_date]", date.today().strftime("%Y-%m-%d"))

    return text


# ── 尾部拼接 ────────────────────────────────────────────────

LANG_PACK = {
    "zh": {
        "instruction": "你必须全程使用中文对话。绝对不能说其他语言。用自然、口语化的中文。",
    },
    "en": {
        "instruction": "You must conduct the entire conversation in English. Use natural, conversational English. Do not use any other language.",
    },
    "en-SG": {
        "instruction": "You must conduct the entire conversation in Singapore English. Use natural, conversational English suitable for Singapore. Do not switch to another language unless the user does.",
    },
    "es-MX": {
        "instruction": "Debes mantener toda la conversación en español de México. Usa lenguaje natural y conversacional. No uses otro idioma.",
    },
    "id": {
        "instruction": "Anda harus melakukan seluruh percakapan dalam bahasa Indonesia. Gunakan bahasa Indonesia yang alami dan percakapan. Jangan gunakan bahasa lain.",
    },
}


def build_system_prompt(prompt: str, profile: dict, lang: str = "en") -> str:
    """完整流程：占位符替换 + 语言指令 + 结束规则拼接。返回最终 assistant system prompt。"""
    text = fill_placeholders(prompt, profile)
    lp = LANG_PACK.get(lang, LANG_PACK["en"])
    return "\n\n".join([text, lp["instruction"]])


# ── CLI ─────────────────────────────────────────────────────

def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def parse_args():
    p = argparse.ArgumentParser(description="组装 marketing prompt + user profile → 最终 system prompt")
    p.add_argument("--profiles", "-p", default="benchmark_1_test/data/user_profiles_20260525.jsonl",
                   help="用户画像 JSONL 路径")
    p.add_argument("--prompts", "-m", default="benchmark_1_test/marketing_prompts.jsonl",
                   help="Marketing prompts JSONL 路径")
    p.add_argument("--lang", choices=["zh", "en", "en-SG", "es-MX", "id"], default="en",
                   help="对话语言（默认 en）")
    p.add_argument("--output", "-o", default=None, help="输出 JSONL 路径（默认 stdout）")
    p.add_argument("--profile-id", default=None, help="只处理指定 profile_id")
    p.add_argument("--prompt-id", default=None, help="只处理指定 prompt_id（需配合 --profile-id）")
    return p.parse_args()


def main():
    args = parse_args()

    profiles = load_jsonl(args.profiles)
    prompts = load_jsonl(args.prompts)

    prompt_by_id = {p["id"]: p for p in prompts if "id" in p}

    if args.profile_id:
        profiles = [p for p in profiles if p.get("profile_id") == args.profile_id]
        if not profiles:
            print(f"未找到 profile_id={args.profile_id}", file=sys.stderr)
            sys.exit(1)

    if args.output is None:
        stem = args.profiles.rsplit(".", 1)[0]
        args.output = f"{stem}_refine.jsonl"

    results = []
    for profile in profiles:
        pid = args.prompt_id or profile.get("prompt_id") or profile.get("id")
        if pid not in prompt_by_id:
            print(f"  [SKIP] {profile.get('profile_id', '?')}: prompt_id={pid} 不在 prompts 中", file=sys.stderr)
            continue
        prompt_text = prompt_by_id[pid]["prompt"]
        profile["system_prompt"] = build_system_prompt(prompt_text, profile, lang=args.lang)
        results.append(profile)

    with open(args.output, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"写入 {len(results)} 条 -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
