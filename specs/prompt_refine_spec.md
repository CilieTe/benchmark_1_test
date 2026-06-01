# Marketing Prompt Refine Spec

对 `marketing_prompts.jsonl` 中每条记录的 `prompt` 字段逐条改写。不改 `id` / `category` / `scene` / `function` 字段。

## 语言要求

所有 prompt 正文必须使用英文。若原 prompt 包含中文，翻译为自然流畅的英文。

---

## 一、Rules 修复

在每条 prompt 的 Rules 区域追加以下三条规则。如果已有类似表述则合并而非重复；如果原 prompt 没有 Rules 区域则新建。

1. If the customer indicates they are busy, offer to call back later and end the conversation.
2. For any specific questions from customers, please first refer to the FAQ. If the FAQ does not provide an answer, do not make one up.
3. Only use the benefits listed in the FAQ; do not create extra benefits.

---

## 二、Hints（独立段落，放在整个 prompt 末尾）

删除原 prompt 中所有已有的对话结束标记说明和格式提示（无论什么形式——prose、HINT、规则条款），在 prompt 最后新增独立段落：

```
HINT: Output and append the exact signal <dialog-end> to the end of your response if you want to end the conversation.
HINT: Your user-facing response must always be in the spoken words format.
```

这两条原样保留，不做任何修改。

---

## 三、Main Flow 修复

### 原则
- 第一次客户拒绝时必须挽回：acknowledge concern → offer one alternative or key benefit → ask again
- 客户连续拒绝两次、或明确要求结束通话时，才可以结束
- 客户说忙 → 主动约回拨时间，不继续推销
- 保留原流程业务逻辑和 function-call 位置不变

### 识别需改的分支
逐个检查所有对话结束出口，找到"第一次拒绝就结束"的：

- `politely end the conversation` / `end the conversation politely`
- `end the call` / `hang up`
- `thank the customer and end`

### 改写方式
每个"过早结束"的分支，在结束前插入一个挽回回合：

**改写前**：
> If customer says no → politely end the conversation.

**改写后**：
> If customer says no → acknowledge their concern, briefly mention one key benefit or alternative that addresses their objection, and ask if they'd reconsider. If the customer still declines, politely end the conversation.

### 不改的情况
- 已经是"第二次拒绝后结束"的分支
- Identity verification 失败（安全校验不挽回）
- 客户非目标群体（如"不是家长"、"已销户"）
- 客户主动要求挂断

---

## 四、不可改动

- 所有占位符原样保留：`[X]`、`[Date]`、`[Tier]`、`[home_type]`、`[device_count]`、`[recommended_package]`、`Ms. Zhang`、`张敏`、`4827`、`XX Bank`、`XX Community`、`Mr./Ms. XXX`、`XX万` 等
- Function 名称、参数结构、调用方式
- FAQ 的事实性内容
- Background Information
- `id` / `category` / `scene` / `function` 字段
