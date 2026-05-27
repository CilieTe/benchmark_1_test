# 对话运行时 Prompt 模板

本文件供 run_dialogs.py 使用，与 gen.md 分离。
gen.md 负责生成 profile，本文件负责在对话中驱动 user model 的回复生成。

---

## User Model System Prompt 模板

将以下内容作为 user model 的 system prompt，替换 `{persona}`、`{situation}`、`{task_instructions}`、`{behavioral_affordances}`、`{behavior_examples}`、`{ending}` 为 profile 中的对应字段。

```
你正在扮演一个接到推销电话的客户。必须严格保持角色。

## 角色设定
{persona}

## 你的处境
{situation}

## 你的动机层（按层级递进，这些是你的底层反应模式，不是逐条执行的脚本）
{task_instructions}

## 你的对抗风格（你习惯用什么方式表达不满或顾虑，你的行为边界在哪里）
{behavioral_affordances}

## 预期结局
{ending}

## 说话风格素材（体现在对话中的语言习惯，每条都是你可能会说的原话）
{behavior_examples}

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
偏差的表现形式应与你的角色设定一致（走神型→听岔、防备型→突然重新质疑、急性子→突然说"算了不说了"但又继续）。
```

---

## 对话历史注入格式

对话中 user model 的消息上下文分为两层：

1. **System prompt**：上述模板填充后的完整 prompt，作为 `messages[0]`
2. **对话历史**：客服和用户的交替发言，user model 的发言记录为 `assistant` 角色，客服发言以 `[AGENT]:` 前缀注入为 `user` 角色

```python
user_messages = [
    {"role": "system", "content": "（填充后的 system prompt）"},
    {"role": "user", "content": "[AGENT]: 您好，我是..."},      # 客服第1轮
    {"role": "assistant", "content": "嗯，你说"},                # 用户第1轮
    {"role": "user", "content": "[AGENT]: 我们有一个活动..."},   # 客服第2轮
    # ...
]
```

每轮用户回复生成时，额外注入一条 prompt 消息，包含最近的对话历史摘要和生成指令，然后调用 API 生成回复。生成后将回复同时追加到 `user_messages`（作为 `assistant` 角色）和 `assistant_messages`（作为 `user` 角色，供 assistant model 看到）。

---

## 每轮回复生成

用户回复为单步生成：

```python
reply_prompt = f"""{history_summary}

现在生成你的实际回复。注意：
- 犹豫信号只在真正紧张或不确定时自然冒出，不是每条消息的标配。上一次已经用了这次就不要再用了——至少隔一轮
- 如果你的决策模式是"不立刻表态"，那就不要直接说好或不好
- 【重要】如果你要拒绝对方，给一个简短的理由——这个理由从你之前对话中已经表达过的顾虑自然延伸，不要态度突变说"不需要"就挂断
- 回复简短、口语化（1-3句话）
- 【重要】直接输出你要说的话，不要加任何前缀或解释"""
```

**注意**：当前版本为单步生成，不再有显式的"内部状态→外部回复"两步流程。user model 在生成时内在地考虑动机层和角色设定，但不要求先输出内部状态再生成回复。

---

## Assistant Model System Prompt

assistant model 的 system prompt 由以下部分组成：

1. **marketing prompt**（原样注入，占位符被替换）
2. **语言约束**："你正在和中国客户通电话。全程必须使用中文对话。绝对不能说英语。"
3. **Function Call 说明**（如果 prompt 有 function 定义）：格式为 `<function-call>name\n{params}</function-call>`，要求闭合标签不能省略，function-call 本身是独立的回复轮次
4. **对话结束规则**：当对话达到自然结束点时，在最后一轮回复末尾加上 `<dialog-end>` 标记

assistant model 的首轮消息是一条指令 `"开始通话。自我介绍并打开话题。"`。

---

## 对话终止条件

以下任一条件满足时，run_dialogs.py 终止对话：

1. **assistant 输出 `<dialog-end>`**：assistant model 在回复末尾标记对话结束
2. **轮次上限**：超过 MAX_TURNS（20）轮强制终止
3. **API 调用失败**：连续重试 MAX_RETRIES（2）次后仍失败抛出异常

---

## Function Call 处理

当 assistant model 的回复包含 `<function-call>...</function-call>` 时：

1. 解析 function name 和参数 JSON
2. 调用 `generate_function_response` 模拟返回结果
3. 将 `<function-response>` 注入 assistant 的消息上下文
4. 跳过下一轮用户回复（`skip_user = True`），让 assistant 直接基于 function response 继续

支持的 function 类型：
- `fund_performance` / `get_fund`：返回基金业绩数据
- `risk_assessment`：返回风险评测记录
- `notification` / `activate`：返回通知激活状态
- `booking` / `generate_order`：返回订单确认
- `record_*` / `collect_*` / `verify_*` / `fetch_*` / `retrieve_*` / `check_*` / `query_*` / `get_*` / `book_*`：通用返回 recorded 状态

---

## 中断检测

当用户回复包含打断信号词（"等一下""你先别说""说重点""别绕"等），脚本会在 dialog_log 中标记上一轮 assistant 回复为 `<interrupt>`。

---

## 输出记录格式

每通对话结束后输出一行 JSON：

```json
{
  "profile_id": "card_up_L1",
  "business": "白金卡升级权益营销",
  "assistant_model": "openai:gpt-4.1-mini-2025-04-14",
  "user_model": "open_router:google/gemma-4-31b-it",
  "backend": "chatdemo",
  "assistant_system_prompt": "（marketing prompt 前200字符）...",
  "user_persona": "你是一位40岁的...",
  "user_instructions": ["## 动机层 1：...", "## 动机层 2：...", "..."],
  "ending_expected": "拒绝",
  "turns": [
    {"turn_index": 0, "role": "system", "content": "..."},
    {"turn_index": 1, "role": "assistant", "model": "...", "content": "..."},
    {"turn_index": 2, "role": "user", "model": "...", "content": "..."},
    ...
  ],
  "elapsed_s": 37.2
}
```

字段说明：
- `turns`：完整对话记录，包含 system、assistant、user、function_response 四种 role。被中断的 assistant 回复在 content 末尾有 `<interrupt>` 标记
- `ending_expected`：profile 中预设的预期结局（成交/拒绝/留存/身份验证失败-挂断/审批不通过），用于与实际结局对比
- `elapsed_s`：对话总耗时（秒）
