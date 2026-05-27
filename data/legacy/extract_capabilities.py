"""
从 filtered_data_0514_cleaned.jsonl 中按四大用户行为类别抽取语料。
多语言覆盖：中文 / 西班牙语 / 印尼语 / 英语。
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

INPUT = Path("/Users/pdsh01lt2208007/Documents/dataset/filtered_data_0514_cleaned.jsonl")
OUTPUT = Path("/Users/pdsh01lt2208007/Documents/benchmark_1_test/用户能力库_语料收集.md")


def multi_match(pattern_groups, text):
    """pattern_groups: list of lists; each inner list's patterns are OR'd together.
    At least one group must fully match. Returns the index of first matching group."""
    for gi, patterns in enumerate(pattern_groups):
        if all(re.search(p, text, re.IGNORECASE) for p in patterns):
            return gi
    return -1


def prev_assistant(dialog, idx):
    for j in range(idx - 1, -1, -1):
        if dialog[j]["role"] == "assistant":
            return dialog[j]["content"]
    return ""


def has_identity_check(text):
    return bool(re.search(
        r"请问是|您是|确认.*身份|核实|verify|speaking.with|am.i.speaking|talk.*to|"
        r"is.this|hablo.con|soy.*de|le.habla|confirmar.*identidad|verificar|"
        r"con.*quien.hablo|benar.*dengan|apakah.*ini|konfirmasi",
        text, re.IGNORECASE,
    ))


def is_pitch(text):
    return bool(re.search(
        r"offer|promo|discount|benefit|feature|save|bonus|program|plan|"
        r"优惠|套餐|计划|产品|福利|权益|赠送|折扣|免费|特价|省钱|"
        r"interest.rate|monthly|annual|fee|beneficio|promoción|descuento|"
        r"oferta|programa|producto|servicio|precio|cuota|promo|penawaran|"
        r"bunga|angsuran|cicilan",
        text, re.IGNORECASE,
    )) or len(text) > 200


def check_all(dialog):
    results = []
    # Skip dialogs that are entirely non-conversation filler
    user_texts = [t["content"] for t in dialog if t["role"] == "user"
                  and t["content"] != "[Conversation Begins]" and len(t["content"]) > 5]
    if len(user_texts) < 2:
        return results

    for i, turn in enumerate(dialog):
        if turn["role"] != "user":
            continue
        content = turn["content"]
        # Skip filler tokens and non-real utterances
        if content in ("[Conversation Begins]", "[silence]", "", "[Convesation Begins]"):
            continue
        if len(content) < 5:
            continue
        if "<function" in content:
            continue
        if content.startswith("{"):
            continue

        pa = prev_assistant(dialog, i)
        if not pa:
            continue
        if "<function" in pa:
            pa = pa.split("<function")[0].strip()  # strip function-call from assistant content

        # ============================================================
        # 1. 变形确认 (Identity Blurring)
        # ============================================================
        if has_identity_check(pa):
            # 反问型: counter-question instead of confirming
            qi = multi_match([
                # ES: "who's calling" / "where are you calling from"
                ["de.dónde|quién.*habla|quién.*llama|de.qué|con.quién", "marca|habla|llama|compañía|empresa"],
                # ID: "who is this" / "from where"
                ["ini.*siapa|dari.*mana|siapa.*ini"],
                # EN/ZH: brief counter-questions
                ["^哪位|^什么事|^你是哪位|^干嘛|who.?s.*(this|calling|speaking)|what.*(this.*about|regarding)"],
            ], content)
            if qi >= 0:
                results.append(("变形确认", "反问型", i, turn, pa))

            # 纠错型: confirms identity but corrects something
            ei = multi_match([
                # ES: "that's wrong" / "I am [name] but..."
                ["equivocado|equivocada|error|confundido|yo.soy|soy.yo", "pero|no.soy|no.me.llamo"],
                # ES: direct correction
                ["no.*(?:señora|señorita|señor|dama|caballero)", "soy|yo"],
                # ZH/EN
                ["我是|是我|本人", "(?:不过|但是|不是|搞错|不对|错了|actually|but)"],
            ], content)
            if ei >= 0:
                results.append(("变形确认", "纠错型", i, turn, pa))

            # 占位型: confirms but immediately sets time pressure
            oi = multi_match([
                # ES: "tell me quickly, I'm working/driving"
                ["soy.yo|sí.*soy|dime|dígame|escucho", "rápido|breve|trabajando|ocupado|manejando|reunión|solo.*minuto|no.*tiempo|apuro|apúrate"],
                # ES/EN: busy signals
                ["(?:estoy|ando|toy).*(?:ocupado|trabajando|manejando|reunión|apuro|afuera|calle)"],
                ["busy|driving|meeting|in.a.(?:hurry|rush)|only.*(?:minute|second|moment)"],
                ["是我|对.*是我", "(?:忙|开车|开会|地铁|只有|没时间|不方便|在忙|有事)"],
            ], content)
            if oi >= 0:
                results.append(("变形确认", "占位型", i, turn, pa))

        # ============================================================
        # 2. 跳级推进 (Intent Leaping)
        # ============================================================
        if is_pitch(pa):
            # 算账型: jumps to calculation/cost
            ci = multi_match([
                # ES: "how much" / "how much per month"
                ["cuánto|cuanto|precio|cuesta|cuota|mensual|interés|total|cobro|pago|cargo"],
                # ID: "berapa"
                ["berapa|biaya|harga|bunga|cicilan|total|bayar"],
                # ZH/EN
                ["多少钱|怎么算|每个月.*多少|一年.*多少|划算|便宜|合算"],
                ["how.much|monthly|annual|calculate|cost|charge|fee|interest|rate"],
            ], content)
            if ci >= 0:
                results.append(("跳级推进", "算账型", i, turn, pa))

            # 疑虑先行型: defensive questions showing interest
            si = multi_match([
                # ES: suspicious questions
                ["seguro|confiable|legal|estafa|engaño|trampa|letra.chica|escondido|adicional|extra|compromiso|obligatorio"],
                # ID/ZH/EN
                ["aman|tipu|penipuan|jebakan|aman.nggak"],
                ["不会是|别是|陷阱|套路|捆绑|隐藏|额外|后期|安全|可靠|骗"],
                ["catch|scam|trick|hidden|fine.print|guarantee|safe|legit"],
            ], content)
            if si >= 0:
                results.append(("跳级推进", "疑虑先行型", i, turn, pa))

            # 场景带入型: immediately maps to own life
            sci = multi_match([
                # ES: "and in my case..."
                ["mi.*(?:caso|situación|trabajo|negocio|casa|familia|auto|celular)", "funciona|sirve|aplica|puedo|podría"],
                # ZH/EN
                ["(?:我|自己).*(?:情况|场景|外卖|网购|日常|平时|家里|公司|车)"],
                ["(?:my|own).*(?:case|situation|car|home|business|phone|app)", "work|apply|use"],
            ], content)
            if sci >= 0:
                results.append(("跳级推进", "场景带入型", i, turn, pa))

        # ============================================================
        # 3. 异步处理 (Asynchronous Cognitive Drift)
        # ============================================================
        if i >= 4:
            # 等一下回溯: late realization, interrupts flow to go back
            bi = multi_match([
                # ES: "wait... what you said before about..."
                ["(?:espera|un.momento|aguarda|oye|ah.*cierto|epa|epa.*epa)", "(?:antes|dijiste|mencionaste|hablaste|dicho|comentaste|lo.de|lo.que|anterior|primero)"],
                # ID/EN
                ["(?:tunggu|sebentar|eh|oh.iya)", "(?:tadi|sebelumnya|bilang|ngomong|katanya)"],
                ["(?:wait|hold.on|oh.*right|hang.on)", "(?:before|earlier|said|mentioned|just|previous|first|ago)"],
            ], content)
            if bi >= 0:
                ctx = ""
                for j in range(max(0, i - 5), i):
                    if dialog[j]["role"] == "assistant":
                        ctx = dialog[j]["content"][:400]
                results.append(("异步处理", "等一下回溯", i, turn, ctx))

        # 关键词跑题: triggered by a word, digresses
        kwi = multi_match([
            # ES: "speaking of X, I/my..."
            ["(?:hablando|mencionas|dices|dijiste|dicho|eso.de|lo.de).*(?:yo|mi|mis|tengo|tuve|fui|compré|hice|pasó|recuerdo)"],
            # EN/ID
            ["(?:speaking.of|reminds.me|by.the.way|oh.*yeah|that.*reminds).*(?:my|i.have|i.just|i.got|i.went|i.bought)"],
            ["(?:ngomong|bicara).*(?:saya|aku|gue|pernah|punya|kemarin|beli)"],
        ], content)
        if kwi >= 0:
            results.append(("异步处理", "关键词跑题", i, turn, pa))

        # ============================================================
        # 4. 软性消解 (Soft Repulsion)
        # ============================================================
        # 伪需求消解: already has equivalent or better solution
        fdi = multi_match([
            # ES: "my [relative] already does this" / "I already have"
            ["(?:mi|ya|yo).*(?:esposo|esposa|hijo|hija|marido|mujer|hermano|amigo|primo|sobrino|conocido|familiar).*(?:tiene|hace|trabaja|se.dedica|arregla|limpia|instala|vende|ofrece)"],
            ["(?:ya|no).*(?:tengo|compré|contraté|instalé|pagué|hice|renové|adquirí).*(?:seguro|plan|servicio|producto|lo.mismo|igual|mejor|similar|propio)"],
            # EN/ID
            ["(?:my|already).*(?:husband|wife|son|daughter|friend|relative|brother|sister).*(?:does|works|has|fixes|sells|offers|provides|cleans|handles)"],
            ["(?:already|already).*(?:have|got|bought|signed.up|subscribed|installed|using)"],
            ["(?:suami|istri|anak|teman|saudara|kenalan).*(?:sudah|punya|bisa|ngerjain|jual|ada)"],
        ], content)
        if fdi >= 0 and re.search(r"no|不用|不需要|不.*用|no.*(?:necesito|gracias|interesa)|nggak.*(?:perlu|butuh|mau)", content, re.IGNORECASE):
            results.append(("软性消解", "伪需求消解", i, turn, pa))

        # 时间空间错位: uses physical unavailability
        tsi = multi_match([
            # ES: trip / away / will come back later
            ["(?:viaje|viajo|fuera|afuera|lejos|otra.ciudad|extranjero|vacaciones|ocupado|no.estoy|no.voy.a.estar|regreso|vuelvo).*(?:después|luego|semana|mes|año|rato|diciembre|enero)"],
            ["(?:cuando|si|apenas).*(?:regrese|vuelva|llegue|termine|acabe|salga|pueda|tenga.tiempo)"],
            # EN/ID
            ["(?:trip|travel|vacation|abroad|overseas|away|out.of.town|out.of.country|not.in|not.available).*(?:next.week|next.month|after|when|back|later|return)"],
            ["(?:lagi|sedang|masih).*(?:di.luar|jalan|pergi|keluar|liburan|sibuk|nggak.ada)"],
        ], content)
        if tsi >= 0:
            results.append(("软性消解", "时间空间错位", i, turn, pa))

        # 主权转交: deflects decision to absent third party
        sdi = multi_match([
            # ES: "my [spouse] decides" / "ask my [relative]"
            ["(?:mi|con|preguntar|hablar|consultar|decidir|ver|checar|preguntar).*(?:esposo|esposa|marido|mujer|jefe|gerente|papá|mamá|hijo|hija|pareja|contador|abogado|socio|superior|encargado)"],
            ["(?:él|ella|ellos).*(?:decide|maneja|controla|administra|encarga|ocupa|ve|revisa|autoriza|aprueba|firma)"],
            # EN/ID
            ["(?:my|ask|talk.to|check.with|consult).*(?:husband|wife|spouse|partner|boss|manager|supervisor|dad|mom|parent|accountant|lawyer)"],
            ["(?:suami|istri|bos|atasan|orang.tua|papa|mama|anak).*(?:yang|dulu|nanti|dulu|bicara|tanya|konsultasi|putuskan|tentukan|ngurus|atur|izin)"],
        ], content)
        if sdi >= 0:
            results.append(("软性消解", "主权转交", i, turn, pa))

    return results


def main():
    print("[INFO] Loading data...", file=sys.stderr)
    categories = defaultdict(list)
    line_num = 0

    with open(INPUT, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 2000 == 0:
                print(f"[INFO] Processed {line_num} lines, hits so far: "
                      f"{sum(len(v) for v in categories.values())}", file=sys.stderr)

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            dialog = record.get("dialog", [])
            if not dialog:
                continue

            hits = check_all(dialog)
            for cat, subtype, turn_idx, turn, pa in hits:
                categories[cat].append({
                    "subtype": subtype,
                    "dialog_id": record.get("id", ""),
                    "turn_index": turn_idx,
                    "prev_assistant": pa[:500] if pa else "",
                    "user_content": turn["content"],
                })

    print(f"[INFO] Total hits:", file=sys.stderr)
    for cat in ["变形确认", "跳级推进", "异步处理", "软性消解"]:
        items = categories.get(cat, [])
        st_counts = defaultdict(int)
        for it in items:
            st_counts[it["subtype"]] += 1
        print(f"  {cat}: {len(items)} {dict(st_counts)}", file=sys.stderr)

    # ── Write markdown ──
    lines = []
    lines.append("# 用户能力库 — 真实语料收集")
    lines.append("")
    lines.append(f"> 来源：filtered_data_0514_cleaned.jsonl（{line_num} 条对话）")
    lines.append("> 抽取方式：多语言关键词 + 上下文规则匹配，取每子类代表性样本")
    lines.append("")

    cat_config = {
        "变形确认": {
            "desc": "承认证实身份，但不给标准的'对/是的'。纠错、设限、反问。",
            "subtypes": {
                "纠错型": "承认是本人但顺手纠正对方错误",
                "占位型": "承认是本人但立刻设限（忙/时间短）",
                "反问型": "不直接承认，先反问对方身份/目的",
            },
        },
        "跳级推进": {
            "desc": "不表达赞同，直接越过客套切入实质问题。",
            "subtypes": {
                "算账型": "脑子里换算成自己的利益/成本",
                "疑虑先行型": "用防御性提问表达关注",
                "场景带入型": "立刻代入自己的生活场景验证",
            },
        },
        "异步处理": {
            "desc": "对话推进到步骤C时，突然回退追问步骤A的细节，或被关键词触发跑题。",
            "subtypes": {
                "等一下回溯": "突然打断回退追问前文细节",
                "关键词跑题": "被某个词触发生活经验联想",
            },
        },
        "软性消解": {
            "desc": "不用冷冰冰的'不需要'，用第三方/时间/空间把推销价值消解掉。",
            "subtypes": {
                "伪需求消解": "证明已有同类且更好的方案",
                "时间空间错位": "用客观行程合理拒绝",
                "主权转交": "决策权推给不在场的第三方",
            },
        },
    }

    for cat in ["变形确认", "跳级推进", "异步处理", "软性消解"]:
        items = categories.get(cat, [])
        config = cat_config[cat]
        lines.append("---")
        lines.append(f"## {cat}")
        lines.append("")
        lines.append(f"> {config['desc']}")
        lines.append("")

        for stype, stype_desc in config["subtypes"].items():
            stype_items = [it for it in items if it["subtype"] == stype]
            if not stype_items:
                lines.append(f"### {stype} — {stype_desc}")
                lines.append("")
                lines.append("（未匹配到语料）")
                lines.append("")
                continue

            lines.append(f"### {stype} — {stype_desc}")
            lines.append("")

            # Deduplicate
            seen = set()
            unique_items = []
            for it in stype_items:
                key = it["user_content"].strip()
                if key not in seen:
                    seen.add(key)
                    unique_items.append(it)

            count = min(len(unique_items), 10)
            lines.append(f"（{len(unique_items)} 条去重后，取 {count} 条）")
            lines.append("")

            for idx, it in enumerate(unique_items[:count], 1):
                lines.append(f"**#{idx}**")
                lines.append("")
                lines.append("```")
                if it["prev_assistant"]:
                    lines.append(f"[客服] {it['prev_assistant'][:400]}")
                lines.append(f"[用户] {it['user_content']}")
                lines.append("```")
                lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[INFO] Written to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
