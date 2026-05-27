"""
多模型对话 Benchmark 脚本。
读取 user_profiles + marketing_prompts，用不同 LLM 分别扮演 assistant 和 user，
跑多轮对话，输出 JSONL。

支持两种 API 后端：
  - turbo:  原 Turbo API（Bearer 鉴权）
  - chatdemo: 本地 Chat Demo Server（http://localhost:9898，无鉴权）

Usage:
    python benchmark_1_test/run_dialogs.py --num 10
    python benchmark_1_test/run_dialogs.py --backend chatdemo --num 5 --model gpt-4o-mini
    python benchmark_1_test/run_dialogs.py --backend turbo --api-base https://my-api.example.com --api-key sk-xxx
"""

import json
import sys
import os
import re
import time
import uuid
import urllib.request
import urllib.error
import argparse
from datetime import date

# ── 后端预设 ──────────────────────────────────────────────────

BACKEND_PRESETS = {
    "turbo": {
        "api_base": os.environ.get("TURBO_API_BASE", "https://gateway.theturbo.ai"),
        "api_key": os.environ.get("TURBO_API_KEY"),
        "token_field": "max_tokens",
        "extra_body": {},
    },
    "chatdemo": {
        "api_base": "http://192.168.101.15:9898",
        "api_key": None,
        "token_field": "max_completion_tokens",
        "extra_body": {},
    },
}

MAX_TURNS = 20
MAX_RETRIES = 2

# ── 占位符替换 ──────────────────────────────────────────────

PLACEHOLDER_MAP = {
    "[current_date]": date.today().strftime("%Y-%m-%d"),
    "[Date]": date.today().strftime("%Y-%m-%d"),
    "[Tier]": "Silver",
    "[X]": "3",
    "[interest_tag]": "摄影",
    "[Your Name]": "张明",
}


def substitute_placeholders(text: str) -> str:
    for ph, val in PLACEHOLDER_MAP.items():
        text = text.replace(ph, val)
    remaining = set(re.findall(r'\[.*?\]', text))
    unknown = remaining - set(PLACEHOLDER_MAP.keys())
    for u in unknown:
        print(f"  [WARNING] 未处理的占位符: {u}", file=sys.stderr)
    return text


# ── Function Call 解析与模拟 ─────────────────────────────────

def parse_function_defs(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []

    funcs = []
    raw = raw.strip()

    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            for key, val in data.items():
                if isinstance(val, dict) and "function" in val:
                    inner = val["function"]
                    params_raw = inner.get("parameters", {})
                    if "properties" in params_raw:
                        required_list = params_raw.get("required", [])
                        params = {}
                        for pname, pinfo in params_raw["properties"].items():
                            params[pname] = {
                                "type": pinfo.get("type", "string"),
                                "description": pinfo.get("description", ""),
                                "required": pname in required_list,
                            }
                    else:
                        params = params_raw
                    funcs.append({
                        "name": inner.get("name", key),
                        "description": inner.get("description", ""),
                        "parameters": params,
                    })
            return funcs
        except json.JSONDecodeError:
            pass

    blocks = [b.strip() for b in re.split(r'\n\n+', raw) if b.strip()]
    if len(blocks) == 1:
        blocks = [b.strip() for b in re.split(r'\n(?=\w[\w ]*:\s*\n\s*description)', blocks[0]) if b.strip()]

    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue

        name = lines[0].rstrip(":").strip()
        if name.lower() in ("function", "function:", ""):
            for l in lines[1:]:
                if l.strip() and not l.strip().startswith("description") and not l.strip().startswith("parameter"):
                    name = l.rstrip(":").strip()
                    break

        desc = ""
        params = {}

        param_pattern = re.findall(
            r'(\w+):\s*\n\s*type:\s*(\w+)\s*\n\s*description:\s*([^\n]+)(?:\s*\n\s*required:\s*(\w+))?',
            block
        )
        for pname, ptype, pdesc, preq in param_pattern:
            params[pname] = {
                "type": ptype,
                "description": pdesc.strip(),
                "required": preq.lower() == "true" if preq else False,
            }

        if not params:
            param_pattern2 = re.findall(r'(\w+):\s*\n\s*type:\s*([\w\[\] ,]+)', block)
            desc_pattern2 = re.findall(r'(\w+):\s*\n\s*type:[\s\S]*?description:\s*([^\n]+)', block)
            for (pname, ptype), (_, pdesc) in zip(param_pattern2, desc_pattern2):
                if pname == _:
                    params[pname] = {
                        "type": ptype.strip(),
                        "description": pdesc.strip(),
                        "required": "required: true" in block[block.find(pname):],
                    }

        if name and name.lower() not in ("function",):
            funcs.append({
                "name": name,
                "description": desc,
                "parameters": params,
            })

    return funcs


def format_functions_for_prompt(funcs: list[dict]) -> str:
    if not funcs:
        return ""

    lines = ["## Available Functions", ""]
    for f in funcs:
        lines.append(f"### {f['name']}")
        lines.append(f"Description: {f['description']}")
        if f["parameters"]:
            lines.append("Parameters:")
            for pname, pinfo in f["parameters"].items():
                if isinstance(pinfo, dict):
                    req = "required" if pinfo.get("required") else "optional"
                    lines.append(f"  - {pname} ({pinfo.get('type', 'string')}, {req}): {pinfo.get('description', '')}")
                else:
                    lines.append(f"  - {pname}: {pinfo}")
        lines.append("")

    return "\n".join(lines)


def parse_function_call(text: str):
    m = re.search(r'<function-call>\s*(\w+)\s*\n?\s*(\{[\s\S]*?\})\s*(?:</function-call>)?', text)
    if not m:
        return None
    name = m.group(1)
    try:
        params = json.loads(m.group(2))
    except json.JSONDecodeError:
        raw = m.group(2)
        raw = re.sub(r'(\w+):', r'"\1":', raw)
        try:
            params = json.loads(raw)
        except json.JSONDecodeError:
            params = {"_raw": m.group(2)}
    return name, params


def _build_function_response_data(func_name: str, params: dict) -> dict:
    """构建 function response 的数据部分，返回 dict。"""
    fn = func_name.lower()
    resp = {}

    if "fund_performance" in fn or "get_fund" in fn:
        category = params.get("fund_category", params.get("industry_focus", "混合基金"))
        resp = {
            "fund_name": f"{category}优选组合",
            "1_year_return": "4.2%",
            "3_year_return": "11.8%",
            "5_year_return": "32.5%",
            "max_drawdown_3y": "-8.7%",
            "max_drawdown_5y": "-14.2%",
            "expense_ratio": "0.65%",
            "management_fee": "0.50%",
            "category_average_3y": "7.3%",
            "sharpe_ratio": "1.12",
        }
    elif "risk_assessment" in fn:
        resp = {"status": "recorded", "risk_profile": "balanced", "assessment_id": f"RA-{uuid.uuid4().hex[:6].upper()}"}
        for k, v in params.items():
            if k != "_raw":
                resp[k] = v
    elif "notification" in fn or "activate" in fn:
        channel = params.get("notification_channel", params.get("channel", "SMS"))
        resp = {"status": "activated", "channel": channel, "message": f"通知服务已通过{channel}激活"}
    elif "booking" in fn or ("generate" in fn and "order" in fn):
        resp = {
            "status": "confirmed",
            "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "booking_ref": f"BK-{uuid.uuid4().hex[:6].upper()}",
            "estimated_time": "2-3 business days",
        }
        for k, v in params.items():
            if k != "_raw":
                resp[k] = v
    elif any(kw in fn for kw in ("record", "collect", "verify", "fetch", "retrieve", "check", "query", "get", "book")):
        resp = {"status": "recorded"}
        for k, v in params.items():
            if k != "_raw":
                resp[k] = v
    else:
        resp = {"status": "ok"}
        for k, v in params.items():
            if k != "_raw":
                resp[k] = v

    return resp


def generate_function_response(func_name: str, params: dict, func_defs: list[dict]) -> str:
    """返回 XML 格式的 function response（用于 dialog_log 和 fallback 路径）。"""
    resp = _build_function_response_data(func_name, params)
    call_id = str(uuid.uuid4())[:8]
    return f'<function-response id="call_{call_id}">\n{json.dumps(resp, ensure_ascii=False, indent=2)}\n</function-response>'


def convert_func_defs_to_tools(func_defs: list[dict]) -> dict:
    """将 parse_function_defs 的输出转为 OpenAI function dict 格式。"""
    tools = {}
    for f in func_defs:
        props = {}
        required = []
        for pname, pinfo in f.get("parameters", {}).items():
            props[pname] = {
                "type": pinfo.get("type", "string"),
                "description": pinfo.get("description", ""),
            }
            if pinfo.get("required"):
                required.append(pname)
        tools[f["name"]] = {
            "type": "function",
            "function": {
                "name": f["name"],
                "description": f.get("description", ""),
                "parameters": {
                    "type": "object",
                    "description": None,
                    "properties": props,
                    "required": required,
                },
            },
        }
    if "knowledge_retrieval" not in tools:
        tools["knowledge_retrieval"] = {
            "type": "function",
            "function": {
                "name": "knowledge_retrieval",
                "description": "Search a knowledge base for the required information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_list": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of search queries.",
                        }
                    },
                    "required": ["query_list"],
                },
            },
        }
    return tools


# ── 文本清理 ─────────────────────────────────────────────────

def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


# ── API 调用 ─────────────────────────────────────────────────

def api_call(model: str, messages: list[dict], backend_cfg: dict,
             temperature=0.7, max_tokens=512, tools=None, **kwargs):
    """统一的 API 调用入口。返回 (content, tool_calls) 元组，tool_calls 为 None 或列表。"""
    extra_body = backend_cfg.get("extra_body", {}).copy()
    actual_model = model
    if ":" in model and not extra_body.get("provider"):
        provider, actual_model = model.split(":", 1)
        extra_body["provider"] = provider

    body = {
        "model": actual_model,
        "messages": messages,
        "temperature": temperature,
        backend_cfg["token_field"]: max_tokens,
        **extra_body,
        **kwargs,
    }
    if tools:
        body["tools"] = tools

    headers = {"Content-Type": "application/json"}
    api_key = backend_cfg.get("api_key")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{backend_cfg['api_base']}/v1/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
    )
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
                if "error" in data:
                    raise RuntimeError(f"API error: {data['error']}")
                if "content" in data and "choices" not in data:
                    return sanitize_text(data["content"]), None
                elif "choices" in data:
                    msg = data["choices"][0]["message"]
                    content = sanitize_text(msg.get("content") or "")
                    tc_list = msg.get("tool_calls")
                    if tc_list:
                        tool_calls = [
                            {"id": tc["id"], "name": tc["function"]["name"],
                             "arguments": json.loads(tc["function"]["arguments"])}
                            for tc in tc_list
                        ]
                    else:
                        tool_calls = None
                    return content, tool_calls
                else:
                    raise RuntimeError(f"Unexpected response: {list(data.keys())}")
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                raise RuntimeError(f"{model} failed after {MAX_RETRIES} retries: {e}")


def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ── User System Prompt ───────────────────────────────────────

def build_user_system(profile: dict, lang: str = "zh") -> str:
    tasks_text = ""
    for i, t in enumerate(profile.get("task_instructions", []), 1):
        tasks_text += f"{t}\n\n"

    situation = profile.get("situation", "")

    examples = profile.get("behavior_examples", {})
    examples_text = ""
    if examples:
        lines = []
        for trait, phrases in examples.items():
            lines.append(f"- {trait}: {' | '.join(phrases)}")
        examples_text = "\n".join(lines)

    if lang == "en":
        return f"""You are roleplaying a customer who just received a cold call. You must strictly stay in character.

## Character Profile
{profile['persona']}

## Your Current Situation
{situation}

## Your Motivational Layers (hierarchical — these are your underlying reaction patterns, not a script to follow)
{tasks_text}
## Your Confrontation Style (how you usually express dissatisfaction or concern, your behavioral boundaries)
{profile.get('behavioral_affordances', '')}

## Expected Outcome
{profile.get('ending') or profile.get('convertibility_ceiling', 'natural conclusion')}

## Speech Style Reference (language habits that show up in conversation; each line is something you might actually say)
{examples_text}

## Format Requirements
- Use English, conversational, like a real phone call.
- Keep replies short (1-3 sentences). No long paragraphs.
- Never break character to explain what you're doing.
- No emoji or markdown formatting — just talk naturally.
- [Hesitation Signal Rules]
  ① Only use hesitation markers when genuinely stuck/nervous/unsure. Don't insert them into smooth speech.
  ② Frequency: skip at least one turn between hesitations. Never use them in two consecutive turns.
  ③ Vary the form: sometimes a sentence-starting "Um...", sometimes a mid-sentence pivot, sometimes an inherently hesitant phrasing ("I guess... maybe not"), sometimes just a trailing "I mean" or "y'know".
  ④ Don't add "..." to every sentence — say definite things without dots.
- The agent speaks first.
- When you decide to end the call or the conversation has substantively concluded (you've confirmed purchase / clearly declined and said your piece / have nothing left to say), end with a short natural spoken closing. Don't robotically say just "Goodbye."

## Random Deviation (low probability, roughly every 20 turns)
Occasionally (about 5% chance), you will give a response that slightly deviates from the current conversation flow —
for example: zoning out and saying something slightly off-topic, suddenly questioning something you previously confirmed,
or saying something logically disjointed and then catching yourself.
This is not a bug; it's normal human behavior on a phone call.
When triggered, don't try to correct it — just continue the conversation naturally.
The form of deviation should match your character profile (distracted type → mishears; guarded type → suddenly re-questions; impatient type → suddenly says "you know what, forget it" and then continues)."""
    else:
        return f"""你正在扮演一个接到推销电话的客户。必须严格保持角色。

## 角色设定
{profile['persona']}

## 你的处境
{situation}

## 你的动机层（按层级递进，这些是你的底层反应模式，不是逐条执行的脚本）
{tasks_text}
## 你的对抗风格（你习惯用什么方式表达不满或顾虑，你的行为边界在哪里）
{profile.get('behavioral_affordances', '')}

## 预期结局
{profile.get('ending') or profile.get('convertibility_ceiling', '自然结束')}

## 说话风格素材（体现在对话中的语言习惯，每条都是你可能会说的原话）
{examples_text}

## 格式要求
- 使用中文，口语化，就像真实打电话。
- 回复简短（1-3句话），不要长篇大论。
- 绝对不能跳出角色解释你在做什么。
- 不要用 emoji 或 markdown 格式——就是直接说话。
- 【犹豫信号使用规范】
  ① 只在真正卡壳/紧张/不确定时用，顺畅表达时不要塞
  ② 出现频率：最多隔一轮发一次，绝对不能连续两轮都用
  ③ 表现形式多样：不要固定某一个词。有时是句首的"嗯..."，有时是句中停顿换说法，有时是句子本身的犹豫感（"好像...也不是"），有时只是一个拖长的"吧""嘛"
  ④ "..."不是每句话都要加——确定的话直接说，不需要点
- 客服会先开口。
- 当你决定挂断或对话已实质性结束时（你已确认购买/已明确拒绝并说完再见/已无话可说），用简短的口语结束最后一句话，不要僵硬地说"再见"两个字的格式。

## 随机偏差（低概率，约每20轮触发一次）
你偶尔（约5%概率）会给出略偏离当前对话流的回应——
比如走神后说了一句不太相关的话、突然质疑一个之前已确认过的事、
或说出一句逻辑跳跃的话然后自己收回来。
这不是bug，是真实人类在电话中的正常现象。
触发后不需要刻意修正，自然地继续对话即可。
偏差的表现形式应与你的角色设定一致（走神型→听岔、防备型→突然重新质疑、急性子→突然说"算了不说了"但又继续）。"""


# ── 用户回复结构化解析 ──────────────────────────────────

def parse_user_reply(raw_text: str) -> tuple[str, dict]:
    """从模型输出中提取 [回复] 和行为标注。未按格式时 fallback 整段作为回复。"""
    annotations = {}
    clean_reply = raw_text.strip()

    layer_m = re.search(r'\[行为层\]\s*(.+?)(?:\n|$)', raw_text)
    trigger_m = re.search(r'\[触发\]\s*(.+?)(?:\n|$)', raw_text)
    transition_m = re.search(r'\[衔接\]\s*(.+?)(?:\n|$)', raw_text)
    reply_m = re.search(r'\[回复\]\s*(.+)', raw_text, re.DOTALL)

    if layer_m:
        annotations["behavior_layer"] = layer_m.group(1).strip()
    if trigger_m:
        annotations["trigger"] = trigger_m.group(1).strip()
    if transition_m:
        annotations["transition"] = transition_m.group(1).strip()
    if reply_m:
        clean_reply = reply_m.group(1).strip()

    return clean_reply, annotations


# ── 用户回复生成 ──────────────────────────────────────────

def generate_user_reply(user_model, user_messages, history_summary, backend_cfg):
    reply_prompt = f"""{history_summary}

在生成回复前，先记录你本轮的行为决策（内部标注，不是你要说的话）：

[行为层] 动机层X：<当前激活的动机名称>
[触发] <本轮客服说了什么/做了什么触发了这个行为>
[衔接] <这一轮和上一轮内容的关联>
[回复] <你的实际回复>

规则：
- [回复] 部分只放你要说的话，1-3句口语，不要有任何标记
- 如果当前是纯 baseline 状态（没有特殊动机被触发），[行为层] 填"动机层1：日常节奏"
- 犹豫信号只在真正紧张或不确定时冒出，至少隔一轮
- 拒绝时给的理由从之前已表达的顾虑自然延伸。硬边界被踩到时可以直接说不并挂断"""

    user_messages.append({"role": "user", "content": reply_prompt})
    raw_output, _ = api_call(user_model, user_messages, backend_cfg, temperature=0.8, max_tokens=384)
    raw_output = raw_output.strip()

    clean_reply, annotations = parse_user_reply(raw_output)

    # assistant user_model 的上下文里只放干净回复，不放标注
    user_messages.append({"role": "assistant", "content": clean_reply})
    return clean_reply, annotations


# ── 对话主循环 ───────────────────────────────────────────────

def run_dialog(profile: dict, sys_prompt: str, assistant_model: str,
               user_model: str, func_defs: list[dict], backend_cfg: dict,
               lang: str = "zh") -> dict:
    sys_prompt = substitute_placeholders(sys_prompt)

    lang_pack = {
        "zh": {
            "instruction": "你必须全程使用中文对话。绝对不能说其他语言。用自然、口语化的中文。",
            "tool": "【工具使用规则】当对话流程要求调用工具时，请严格按上述格式输出：1. 必须以 <function-call> 标签开头，以 </function-call> 标签结尾 2. 不要在 function-call 前后添加多余的口语内容——function-call 本身就是一个独立的回复轮次 3. 你会在下一轮收到 function-response，然后基于其中的数据继续对话",
            "end": "【对话结束规则】当对话达到自然结束点时——客户确认购买/预订、客户明确拒绝并说再见、你已完成所有步骤并致谢告别——请在你最后一轮回复的末尾加上 <dialog-end> 标记。不要在对话还在进行中时使用此标记。",
        },
        "en": {
            "instruction": "You must conduct the entire conversation in English. Use natural, conversational English. Do not use any other language.",
            "tool": "[Tool Usage Rules] When the conversation flow requires calling a tool, strictly follow the format above: 1. Must start with the <function-call> opening tag and end with the <function-call> closing tag 2. Do not add conversational text before or after the function-call — it is a standalone turn 3. You will receive a function-response in the next turn, then continue the conversation based on the data.",
            "end": "[Conversation End Rule] When the conversation reaches a natural ending — customer confirms purchase/booking, customer explicitly declines and says goodbye, or you have completed all steps and thanked the customer — add the <dialog-end> tag at the end of your final reply. Do not use this tag while the conversation is still in progress.",
        },
    }
    lp = lang_pack.get(lang, lang_pack["zh"])

    # Build OpenAI tools list from func_defs (native tool calling, not in system prompt)
    openai_tools = None
    if func_defs:
        openai_tools = []
        for f in func_defs:
            props = {}
            required = []
            for pname, pinfo in f.get("parameters", {}).items():
                props[pname] = {"type": pinfo.get("type", "string"), "description": pinfo.get("description", "")}
                if pinfo.get("required"):
                    required.append(pname)
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": f["name"],
                    "description": f.get("description", ""),
                    "parameters": {"type": "object", "properties": props, "required": required},
                },
            })

    system_parts = [sys_prompt, lp["instruction"]]

    if func_defs:
        func_prompt = format_functions_for_prompt(func_defs)
        system_parts.append(func_prompt)

    system_parts.append(lp["end"])
    full_sys_prompt = "\n\n".join(system_parts)
    assistant_messages = [{"role": "system", "content": full_sys_prompt}]

    user_messages = [{"role": "system", "content": build_user_system(profile, lang=lang)}]

    dialog_log = []
    business = profile.get("business", "unknown")

    dialog_log.append({
        "turn_index": 0, "role": "system", "content": full_sys_prompt,
        "tags": [], "evaluate": {}, "review": {},
        "settings": {"segments": None},
        "laep": {"id": "", "remark": None, "created_by": ""},
    })

    # turn 1: 对话开始标记
    turn1_remark_parts = []
    for field in ["intent_level", "convertibility_ceiling", "persona", "situation"]:
        val = profile.get(field)
        if val:
            turn1_remark_parts.append(f"[{field}] {val}")
    turn1_remark = "\n".join(turn1_remark_parts) if turn1_remark_parts else None
    dialog_log.append({
        "turn_index": 1, "role": "user", "content": "[conversation begins]",
        "tags": ["model:system"], "evaluate": {}, "review": {},
        "settings": {"segments": None},
        "laep": {"id": "", "remark": turn1_remark, "created_by": ""},
    })

    # Assistant 开场
    t_start = time.time()
    assistant_messages.append({"role": "user", "content": "开始通话。自我介绍并打开话题。"})
    assistant_reply, tool_calls = api_call(assistant_model, assistant_messages, backend_cfg, max_tokens=256, tools=openai_tools)
    assistant_messages.append({"role": "assistant", "content": assistant_reply})
    user_messages.append({"role": "user", "content": f"[AGENT]: {assistant_reply}"})
    dialog_log.append({
        "turn_index": 2, "role": "assistant", "content": assistant_reply,
        "tags": [f"model:{assistant_model}"], "evaluate": {}, "review": {},
        "settings": {"segments": None},
        "laep": {"id": "", "remark": None, "created_by": ""},
    })

    skip_user = False

    for turn_idx in range(3, MAX_TURNS * 2 + 1):
        if turn_idx % 2 == 1:
            if skip_user:
                skip_user = False
                continue
            recent_turns = []
            for m in user_messages:
                if m["role"] == "user" and m["content"].startswith("[AGENT]:"):
                    recent_turns.append(f"客服: {m['content'][8:].strip()}")
                elif m["role"] == "assistant" and not m["content"].startswith("[内部状态]"):
                    recent_turns.append(f"你: {m['content']}")
            history_summary = "对话历史：\n" + "\n".join(recent_turns[-6:])

            user_reply, annotations = generate_user_reply(user_model, user_messages, history_summary, backend_cfg)
            assistant_messages.append({"role": "user", "content": user_reply})
            remark_parts = []
            if annotations.get("behavior_layer"):
                remark_parts.append(f"[行为层] {annotations['behavior_layer']}")
            if annotations.get("trigger"):
                remark_parts.append(f"[触发] {annotations['trigger']}")
            if annotations.get("transition"):
                remark_parts.append(f"[衔接] {annotations['transition']}")
            remark = "\n".join(remark_parts) if remark_parts else None
            dialog_log.append({
                "turn_index": turn_idx, "role": "user", "content": user_reply,
                "tags": [f"model:{user_model}"], "evaluate": {}, "review": {},
                "settings": {"segments": None},
                "laep": {"id": "", "remark": remark, "created_by": ""},
            })

            interrupt_patterns = [
                "等一下", "你先别说", "你还没回答", "我问你", "别绕", "说重点",
                "打断", "你等一下", "停一下", "先不说这个", "回到刚才",
                "你刚才说", "你还没说", "不要扯开", "回答我", "先回答",
            ]
            if any(p in user_reply for p in interrupt_patterns):
                for prev in reversed(dialog_log):
                    if prev.get("role") == "assistant":
                        prev["content"] = prev["content"].rstrip() + "<interrupt>"
                        break
        else:
            assistant_reply, tool_calls = api_call(assistant_model, assistant_messages, backend_cfg, max_tokens=512, tools=openai_tools)

            if tool_calls:
                # Native tool_calls from API — record assistant turn + generate function responses
                assistant_messages.append({
                    "role": "assistant", "content": assistant_reply or "",
                    "tool_calls": [
                        {"id": tc["id"], "type": "function",
                         "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"], ensure_ascii=False)}}
                        for tc in tool_calls
                    ],
                })
                dialog_log.append({
                    "turn_index": turn_idx, "role": "assistant", "content": assistant_reply or "",
                    "tags": [f"model:{assistant_model}", "function_call",
                             *[f"function:{tc['name']}" for tc in tool_calls]],
                    "evaluate": {}, "review": {},
                    "settings": {"segments": None},
                    "laep": {"id": "", "remark": None, "created_by": ""},
                })

                for tc in tool_calls:
                    func_name = tc["name"]
                    params = tc["arguments"]
                    resp_data = _build_function_response_data(func_name, params)
                    fc_display = generate_function_response(func_name, params, func_defs)
                    assistant_messages.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "content": json.dumps(resp_data, ensure_ascii=False),
                    })
                    dialog_log.append({
                        "turn_index": turn_idx + 1, "role": "user", "content": fc_display,
                        "tags": ["model:system", "function_response", f"function:{func_name}"],
                        "evaluate": {}, "review": {},
                        "settings": {"segments": None},
                        "laep": {"id": "", "remark": None, "created_by": ""},
                    })
                    turn_idx += 1
                skip_user = True
                continue
            else:
                assistant_messages.append({"role": "assistant", "content": assistant_reply})
                user_messages.append({"role": "user", "content": f"[AGENT]: {assistant_reply}"})
                dialog_log.append({
                    "turn_index": turn_idx, "role": "assistant", "content": assistant_reply,
                    "tags": [f"model:{assistant_model}"], "evaluate": {}, "review": {},
                    "settings": {"segments": None},
                    "laep": {"id": "", "remark": None, "created_by": ""},
                })

                # Fallback: XML-format function call parsing (for models without native tool support)
                fc = parse_function_call(assistant_reply)
                if fc:
                    func_name, params = fc
                    fc_response = generate_function_response(func_name, params, func_defs)
                    assistant_messages.append({"role": "user", "content": fc_response})
                    dialog_log.append({
                        "turn_index": turn_idx + 1, "role": "user", "content": fc_response,
                        "tags": ["model:system", "function_response", f"function:{func_name}"],
                        "evaluate": {}, "review": {},
                        "settings": {"segments": None},
                        "laep": {"id": "", "remark": None, "created_by": ""},
                    })
                    skip_user = True
                    continue

            if "<dialog-end>" in (assistant_reply or ""):
                break

    elapsed = time.time() - t_start
    return {
        "id": profile["profile_id"],
        "type": "compress",
        "dialog": dialog_log,
        "tools": convert_func_defs_to_tools(func_defs),
        "meta": {
            "chat_lang": lang,
            "description": f"{business} - {profile['profile_id']}",
            "business": business,
            "assistant_model": assistant_model,
            "user_model": user_model,
            "backend": backend_cfg.get("_name", "unknown"),
            "user_persona": profile["persona"],
            "user_instructions": profile.get("task_instructions", []),
            "ending_expected": profile.get("ending") or profile.get("convertibility_ceiling", ""),
            "elapsed_s": round(elapsed, 1),
        },
    }


# ── CLI ──────────────────────────────────────────────────────

def build_backend_cfg(args) -> dict:
    """根据 CLI 参数构建后端配置。"""
    preset = BACKEND_PRESETS[args.backend].copy()
    preset["extra_body"] = preset.get("extra_body", {}).copy()

    if args.api_base:
        preset["api_base"] = args.api_base
    if args.api_key is not None:
        preset["api_key"] = args.api_key
    preset["_name"] = args.backend

    return preset


def parse_args():
    p = argparse.ArgumentParser(
        description="多模型对话 Benchmark 脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_dialogs.py --num 10
  python run_dialogs.py --backend chatdemo --num 5 --model gpt-4o-mini
  python run_dialogs.py --backend turbo --api-base https://my-api.example.com --api-key sk-xxx
  python run_dialogs.py --backend chatdemo --api-base http://192.168.1.100:9898
        """,
    )
    p.add_argument("--num", "-n", type=int, default=10, help="处理的 profile 数量（默认 10）")
    p.add_argument("--backend", "-b", choices=["turbo", "chatdemo"], default="turbo",
                   help="API 后端: turbo（默认）或 chatdemo")
    p.add_argument("--api-base", default=None,
                   help="覆盖 API base URL（如 https://my-api.example.com）")
    p.add_argument("--api-key", default=None,
                   help="覆盖 API key（chatdemo 默认无鉴权）")
    p.add_argument("--lang", choices=["zh", "en"], default="zh",
                   help="对话语言: zh（中文）或 en（英文），默认 zh")
    p.add_argument("--model", "-m", default="open_router:qwen/qwen3.6-35b-a3b",
                   help="Assistant 模型（默认 open_router:qwen/qwen3.6-35b-a3b）")
    p.add_argument("--user-model", "-u", default="open_router:google/gemma-4-31b-it",
                   help="User 模型（默认 open_router:google/gemma-4-31b-it）")
    p.add_argument("--output", "-o", default="benchmark_1_test/data/dialog_results_20260525.jsonl",
                   help="输出 JSONL 路径")
    p.add_argument("--profiles", default="benchmark_1_test/data/user_profiles_20260525.jsonl",
                   help="用户画像 JSONL 路径")
    p.add_argument("--prompts", default="benchmark_1_test/marketing_prompts.jsonl",
                   help="Marketing prompts JSONL 路径")
    return p.parse_args()


def main():
    args = parse_args()
    backend_cfg = build_backend_cfg(args)

    print(f"后端: {args.backend} -> {backend_cfg['api_base']}", flush=True)
    if backend_cfg.get("api_key"):
        print(f"鉴权: Bearer {backend_cfg['api_key'][:8]}...", flush=True)
    else:
        print(f"鉴权: 无", flush=True)

    profiles = load_jsonl(args.profiles)
    prompts = load_jsonl(args.prompts)

    # 按 id 字段建索引，同时保留按行号索引作为 fallback
    prompt_by_id = {}
    prompt_by_idx = prompts  # 兼容旧的 prompt_idx 整数下标
    for p in prompts:
        pid = p.get("id")
        if pid:
            prompt_by_id[pid] = p

    selected = profiles[:args.num]

    print(f"Assistant: {args.model} | User: {args.user_model}", flush=True)
    print(f"处理 {len(selected)} 条对话 -> {args.output}", flush=True)

    with open(args.output, "w", encoding="utf-8") as out:
        for i, profile in enumerate(selected):
            # 优先用 prompt_id / id 字段查找，fallback 到旧的 prompt_idx
            pid = profile.get("prompt_id") or profile.get("id")
            if pid and pid in prompt_by_id:
                prompt_record = prompt_by_id[pid]
                idx_label = pid
            else:
                idx = profile.get("prompt_idx", 2)
                prompt_record = prompt_by_idx[idx] if idx < len(prompt_by_idx) else prompt_by_idx[0]
                idx_label = f"prompt_idx={idx}"

            sys_prompt = prompt_record["prompt"]
            func_defs = parse_function_defs(prompt_record.get("function", ""))
            biz = profile.get("business", "unknown")

            print(f"[{i+1}/{len(selected)}] {profile['profile_id']} ({biz}, {idx_label}) "
                  f"| bot={args.model} | user={args.user_model}", flush=True)
            if func_defs:
                print(f"  functions: {[f['name'] for f in func_defs]}", flush=True)

            result = run_dialog(profile, sys_prompt, args.model, args.user_model, func_defs, backend_cfg, lang=args.lang)
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()

            fc_count = sum(1 for t in result["dialog"] if "function_response" in t.get("tags", []))
            print(f"  -> {len(result['dialog'])-1} turns, {fc_count} function calls, {result['meta']['elapsed_s']}s", flush=True)

    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
