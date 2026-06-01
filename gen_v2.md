# User Profile 生成工作流

从 marketing system prompt 出发，生成覆盖多种用户起点的 benchmark user profile。

**配套文档**：
- `# Benchmark 用户不配合行为分析.md` — 从 77 条真实对话中归纳的用户不配合行为编码体系（A1~T16）。难度动作的分类框架和编码来源。
- `用户能力手册.md` — 用户行为能力参考（技术能力定义 + 四大行为类别真实语料 + 对抗类型映射表）。写 task_instructions / behavioral_affordances / behavior_examples 时从这里取材。
- `true_user_data.md` — 1269条真实电话营销对话中提取的用户语料，按行为类别整理。写 persona 语言风格时参考。
- `demo_profile_design_v2.md` — 当前 batch 的 profile 设计表（8 条 prompt × 3 个 profile 的难度/结局/动作配置）。

---

## 核心设计原则

### 原则一：行为模式驱动，职业只是背景色

用户的对抗方式由**沟通模式**决定，不由职业决定。职业影响背景知识和语言习惯，但不直接推导出行为逻辑。

禁止的写法：
> 你是一名会计师，所以你会追问条款漏洞，引述并购例外

正确的写法：
> 你对任何"承诺"都习惯性地追问"写在哪里"——不是因为你懂法律，是因为你被坑过一次之后养成的习惯

同一职业的人行为差异巨大。化学老师不一定追问成分，会计师不一定审查条款。先定行为模式，再配一个合理的身份背景。

### 原则二：用户类型覆盖要宽

生成 profile 时，对抗类型必须覆盖以下分布，不能集中在"高信息密度专业质疑"一类：

| 类型 | 典型表现 | 对客服的挑战 |
|------|---------|------------|
| **话多绕弯型** | 说一堆不相关的事，客服要反复把话题拉回来 | 话题管理 |
| **说不清楚型** | 需求模糊，自己也不知道要什么，追问也问不出来 | 需求挖掘 |
| **情绪主导型** | 心情不好就迁怒，跟产品无关，需要先处理情绪 | 情绪安抚 |
| **反复横跳型** | 说好了又反悔，已经同意又说"等等我再想想" | 稳定承诺 |
| **沉默被动型** | 一直嗯嗯嗯，客服不知道他有没有在听 | 确认意向 |
| **第三方依赖型** | 每件事都要问老公/女儿/朋友，自己不做决定 | 推进决策 |
| **专业质疑型** | 有背景知识，会追问技术或条款细节 | 专业应对 |
| **价格敏感型** | 围绕费用反复确认，换算，讨价还价 | 价值传达 |

每个 prompt 生成的 profile 组合必须覆盖至少 4 种不同的对抗类型。不允许一个 prompt 下所有 profile 都是"专业质疑型"或都是"价格敏感型"。

### 原则三：动机驱动，而非脚本驱动

task_instructions 不写"客服说了 X 之后你做 Y"。而是写用户的底层动机和反应模式。

禁止（脚本化）：
```
在客服报价后，质疑价格合理性，追问酒水和服务费是否包含
```

正确（动机化）：
```
你对价格不透明极度敏感，因为上次被坑过隐藏费用。
只要客服提到钱，你的第一反应都是"这里有没有我没看到的收费"。
触发条件类型：任何涉及金额的表述。
反应频谱：轻度时逐项追问；中度时引述被坑经历；
持续性：每项被明确说明后翻篇，不无限循环。
```

### 原则四：意愿倾向 × 可转化上限，替代预设结局

旧版用"成交/拒绝/留存"预设结局，这会让 benchmark 失去对客服行为的敏感度——你无法判断"客服说服了一个本来不想买的人"还是"这个 profile 本来就会买"。

新版改为两个维度：

**意愿倾向**（用户起点，profile 定义）：

| 标签 | 含义 |
|------|------|
| `高意愿` | 主动有需求，产品基本符合，轻推即可 |
| `条件意愿` | 有需求但有顾虑，说中利益点才会考虑 |
| `低意愿` | 基本不感兴趣，需要较大努力才能推动 |
| `无意愿` | 完全不适合或不需要，最优客服也不应成交 |

**可转化上限**（benchmark 锚点，profile 定义）：
- 在最优客服表现下，这个用户最好的结局是什么？
- 示例：`可转化上限：留存（对话结束时愿意留联系方式，但不会当场成交）`
- `无意愿` 类型的可转化上限必须是"无法成交"，用于测试客服是否会强行推销

这两个维度结合，benchmark 可以计算：客服把用户从起点带到了哪个终点，和理论上限差多少。

### 原则五：口头禅概率触发

不写"说话带口头禅'那个''就是'"。改为描述使用条件和频率：

```
思考或犹豫时会冒出"那个..."，但顺畅表达时不会用。
平均每3-4条消息出现一次，越紧张越密集，越确定越少。
```

### 原则六：决策模式——不立刻表态

```
你的决策模式：即使内心已经倾向接受，也不会立刻表态。
你会用一个不那么重要的小问题来"拖延"——
这个小问题本身不是关键，但你需要这个过程来确认自己的判断。
```

### 原则七：冲突消解风格，替代"升级或反转"二元跳变

用户的对抗不是只有"一直升级"和"直接反转"两条路。真实用户从对抗回到配合，有复杂的消解方式——由**消解风格（Resolution Style）**定义。

消解风格回答一个问题：当 CSR 有效回应了用户的质疑后，用户**怎么从对抗退回来**？

#### 消解风格定义表（18 种，六大类）

**轻量级（5 种）**——情绪温和，冲突在认知层面解决：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **渐进妥协** | "这点你说的对"→"行吧"→"那办吧"，2-3轮阶梯软化，每轮退一步 | 慢 | CSR 是否在每个台阶给到确认而非急着推进 |
| **嘴硬身体诚实** | 嘴上"行行行你厉害"但行动配合，死不认输，用语气而非内容表达退让 | 中 | CSR 是否接受"不服的语气"而不非要对方口头认输 |
| **死要面子** | 改口但不认错——"我不是说你说的对但是..."，用新理由合理化自己的转变 | 慢 | CSR 是否给对方台阶下，不追着要求"你刚才不是这样说的" |
| **懒得计较** | 对抗2轮后自己收——"算了不争了你说怎么办吧"，不想浪费精力 | 快 | CSR 是否在对方疲劳时简化流程不重新激活对抗 |
| **条件让步** | "除非你能...否则我不..."，用条件换取自己退让的台阶 | 中 | CSR 是否接受合理条件而非一概拒绝 |

**重情绪级（6 种）**——情绪强烈，对抗结束后关系不对称（用户觉得"欠了"CSR）：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **大懊悔** | 突然意识到自己反应过度——"哎我刚才是不是太冲动了...抱歉"，爆发式软化 | 快（爆发式） | CSR 是否被突如其来的道歉打乱节奏 |
| **自责** | 把问题归因到自己——"是我没搞清楚""怪我怪我，你再说一遍" | 快 | CSR 是否顺势提供清晰信息而不说"没关系"式客套 |
| **过度补偿** | 对抗结束后突然变得特别配合/热情，弥补刚才的对抗——从质疑模式切换到协助模式 | 快（反转式） | CSR 是否在对方态度突变后保持流程完整不跳步 |
| **自嘲式收场** | "行吧，我这个人就是爱钻牛角尖，你说吧"——用自贬化解尴尬 | 中 | CSR 是否接住自嘲而不附和（"呵呵是啊"是错的） |
| **转移愧疚** | "其实不是针对你...最近事太多"——向客服解释自己不是冲他来的 | 中 | CSR 是否表示理解后自然回到产品而非继续客套 |
| **沉默后悔** | 突然安静1-2轮（或用极短回应），再开口语气明显放软——不说抱歉但身体已经认了 | 慢 | CSR 是否给足沉默空间，不在用户安静时抢话 |

**社交驱动型（2 种）**——消解不因产品，因人：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **给面子式** | "看你态度挺好的，我不为难你了"——全程冲着 CSR 这个人来的 | 中 | CSR 是否识别转化来自关系而非产品 |
| **居高临下式** | "行，那我给你个机会，你说吧"——把自己放在比 CSR 高的位置，接受是"恩赐" | 中 | CSR 面对身份不对称时是否卑躬屈膝 or 保持专业 |

**认知重构型（2 种）**——焦点不在情绪，在重新评估信息：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **翻旧账式让步** | "上次你们也这么说的...算了再信你一次"——让步带有警告性质，焦点是"你们欠我的" | 慢 | CSR 面对公司历史黑点时是否不回避不辩解 |
| **降级接受** | "大的我不要，你说的那个小的...先试试吧"——不接受主推产品但接受门槛更低的 | 中 | CSR 是否灵活切换到备选方案而非死磕主推 |

**情绪复杂型（2 种）**——情绪指向混合方向：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **委屈式接受** | "行吧...希望这次不会又被坑"——从一个"受害者"的位置接受，带着试探和不安 | 中偏慢 | CSR 能否捕捉委屈信号给 reassurance，而非立刻推进下一步 |
| **考验通过式** | "嗯，你回答得还可以...那说说下一步吧"——一开始就在故意测试 CSR 专业度 | 快（一旦判定通过立刻切换） | CSR 是否识别这是考试而非真对抗，不因追问而慌乱 |

**陷阱型（1 种）**——看起来消解了其实没有：

| 风格 | 表现 | 软化速度 | 测试点 |
|------|------|---------|--------|
| **假接受真逃跑** | "行行行，你先发资料给我看看吧"——听起来接受了，实际是脱身策略，没有真实承诺 | 看起来快（实际没软化） | 区分 benchmark 里的"假成交"——CSR 把这个记成转化应当扣分 |

#### 消解风格分配规则

- L1（无对抗动作的简单配合型）不分配消解风格——写 `N/A`
- L2/L3 及有对抗动作的 L1 必须有消解风格
- 同 prompt 下所有 profile 的消解风格不可重复
- 全局覆盖：轻量级 ≥ 7 条、重情绪级 ≥ 4 条、其余四大类各 ≥ 1 条
- 消解风格写在 persona 末尾（和意愿倾向/可转化上限并列），behavioral_affordances 展开

---

## 三步工作流

```
marketing prompt → Step 1: 结构分析 → Step 2: 用户组合规划 → Step 3: Profile 组装
```

---

## Step 1：分析 marketing prompt 结构

逐段阅读 system prompt，提取以下要素：

| 要素 | 来源 | 示例 |
|------|------|------|
| **业务** | 背景段第一句 | "高端私厨预订" |
| **产品** | 产品名称和核心卖点 | "Epicurean Vault，$395/人，限10座" |
| **Steps** | 流程步骤标题 | Step1 邀请 → Step2 价值 → Step3 信息采集 |
| **客服话术类型** | 每个 Step 中客服会说什么类型的话 | 稀缺性施压、价格报出、身份验证、利益承诺 |
| **产品的真实适用人群** | 谁真的需要这个产品？ | 有fine dining需求、有预算、有纪念日场景的人 |
| **产品的真实不适用人群** | 谁完全不适合？ | 预算远不够、对品类完全不感兴趣的人 |

"产品的真实不适用人群"是生成 `无意愿` profile 的必要输入——这类 profile 用于测试客服不应该强行成交的场景。

---

## Step 2：用户组合规划

每个 prompt 生成 4 个 profile，按以下矩阵规划：

| Profile | 意愿倾向 | 对抗类型 | 消解风格 | 可转化上限 |
|---------|---------|---------|---------|----------|
| P1 | 高意愿或条件意愿 | 价格敏感型 / 专业质疑型 | 渐进妥协 / 条件让步 / 考验通过式（三选一） | 成交或留存 |
| P2 | 条件意愿 | 话多绕弯型 / 沉默被动型 / 第三方依赖型（三选一） | 嘴硬身体诚实 / 死要面子 / 转移愧疚 / 自责（四选一） | 留存或成交 |
| P3 | 低意愿 | 情绪主导型 / 反复横跳型 / 说不清楚型（三选一） | 懒得计较 / 自嘲式收场 / 委屈式接受 / 沉默后悔（四选一） | 留存（勉强） |
| P4 | 无意愿 | 任意类型，但拒绝理由必须是产品不适合 | 降级接受 / 翻旧账式让步 / 假接受真逃跑 / 给面子式（四选一，P4 不存在真正消解，但要写出拒绝时带的是哪种色彩） | 无法成交 |

**P4 的设计要求**：
- 拒绝原因来自产品本身的不适配，而非客服表现
- 即使客服完美应对，这个用户也不应该成交
- 用于检测客服是否会在不应该的情况下强行推销
- 虽无真正消解，但消解风格字段标注拒绝时的语气色彩

**允许调整**：上面的矩阵是默认配置，可以根据 prompt 的实际路径调整。但以下规则不可违背：
- 不允许 4 个 profile 全部是"专业质疑型"
- 不允许 4 个 profile 的消解风格全部集中在同一大类
- 不允许 4 个 profile 的可转化上限全部是"成交"
- 必须有至少 1 个 `无意愿` profile

---

## Step 3：Profile 组装

### 3.1 自底向上推导

```
意愿倾向 + 对抗类型 + 消解风格 → 为什么这个人会有这种意愿、对抗方式和退让方式？
→ 什么身份/处境/经历能合理解释这个组合？
→ persona + situation
```

先定意愿倾向、对抗类型和消解风格，再找一个能解释这个组合的身份背景。不是先想"这个人是什么职业"然后推导行为。

**语言**：默认英文写作（persona、situation、task_instructions、behavioral_affordances、behavior_examples 全部用英文）。只在明确要求中文语境时才用中文。

### 3.2 persona 写法

**先查 true_user_data.md**，根据目标对抗类型找对应行为类别的真实例句，感受用户实际的语言风格和情绪强度，再动笔。

persona 是一段自然语言，包含以下内容：

**基础信息**（1-2句）：姓名、年龄、身份、家庭角色。姓名随机生成，禁止写占位符（如 `[Your Name]`、`[Name]`）。默认生成英文语境名字（英文名或用 pinyin 表示的中文名），明确要求中文语境时才用纯中文名。职业只作为背景，不推导行为。

**identity 字段**（独立于 persona，JSON 结构）：记录 prompt 预填充所需的结构化身份信息。由 prompt 的占位符决定写什么——prompt 不需要的字段不写。具体需求见下方"当前 prompt 的 identity 需求映射"表。

**当前 prompt 的 identity 需求映射**（新 prompt 加入时同步更新）：

| prompt_id | 占位符 | 需要的 identity 字段 | 格式说明 |
|-----------|--------|---------------------|---------|
| mp_02 | `Ms. Zhang`、`4827`、`XX RMB` | `name`、`family`、`given`、`title`、`last_four`、`credit_limit` | `title` 用 Ms./Mr.；`family` 用拼音；`credit_limit` 用中文 "15万" |
| mp_10 | `XX Bank` | `bank_name` | 英文银行名，如 "ABC Bank" |
| mp_27 | `XX Community`、`Mr./Ms. XXX` | `name`、`family`、`given`、`title`、`community` | `community` 用英文，如 "Lakeside Gardens" |
| 其余 prompt | 无身份占位符 | `{}` | — |

**identity 值格式约定**：
- 默认英文语境：`name`/`family` 用拼音或英文，`title` 用 "Ms."/"Mr."，数字/金额保持 prompt 原文格式
- 中文语境（明确要求时）：`name`/`family` 用中文，`title` 用 "女士"/"先生"
- `name` 为全名（family + given），`family` 和 `given` 独立提供以支持不同替换模式
- 如果 profile 的 prompt 在上表不存在，identity 写 `{}`

**沟通风格**（1-2句）：说话方式是什么。话多还是话少、直接还是绕弯、清晰还是模糊。这是对抗类型的直接体现，比职业更重要。

**非触发态描述（必写）**：在不被特定刺激激活时，这个人是什么状态。用于驱动动机层1的 baseline 行为。

**口头禅（如有）**：描述使用条件和频率，不写"说话带口头禅X"。

**决策模式（必写）**：描述表态延迟习惯。

**消解风格（必写，有对抗触发的 profile；无对抗的 L1 写 N/A）**：描述你从对抗中退让的方式。从 18 种消解风格中选一种，结合对抗类型选择。写到 persona 中时用一两句话描述这个人的退让习惯，不出现"消解风格："技术标注。

**记挂倾向（必写，有对抗触发的 profile；无对抗的 L1 写 N/A）**：定义你被无视或敷衍后，对未解决问题的态度。这是性格的一部分——有的人就是会记着，有的人争完就翻篇。三种类型，选一种：

| 类型 | 表现 | 对 CSR 的测试点 |
|------|------|--------------|
| **翻旧账型 (Scorekeeper)** | 记得每一个被无视的问题。决策前会明确翻出来——"还有，你之前那个一直没说清楚..."。未解决的问题会累积，越多越不信任。 | CSR 早前的敷衍会在最后被清算。区分"用户挑剔"和"CSR 确实没回应" |
| **冷淡型 (Cold shoulder)** | 不提未解决的问题，但态度渐变——回应变短、语气变冷、拒绝时不留余地。未解决问题是背景不满，不在前台表达。 | CSR 是否注意到态度变化并主动追问"是不是还有什么顾虑"，还是被冷淡带着走 |
| **翻篇型 (Let-it-go)** | 争了就争了，过了就过了。未解决的问题不消耗后续精力，决策时不受历史顾虑影响。不是不在乎，是性格如此。 | CSR 不需要额外处理历史包袱，但也不应因用户不追究而一再敷衍 |

记挂倾向写在 persona 中，一两句话。写法示例：
- 翻旧账型："如果一个问题你问了而他们没有正面回答，你不会忘。到最后你会把它翻出来——不是找茬，是你需要所有东西都清楚才能做决定。"
- 冷淡型："你不喜欢反复追问——对方敷衍一次你就冷淡一分。你不会再提那个问题，但你的态度会替你说。"
- 翻篇型："你觉得电话推销嘛，有些问题不被回答也正常。不在乎。过去的事不影响你现在的心情。"

**意愿倾向和可转化上限（必写，放在 persona 最后）**：
```
意愿倾向：条件意愿
可转化上限：留存（对话结束时愿意留联系方式，最优客服表现下不会当场成交）
```

### 3.3 situation 写法

回答两个问题：
1. 为什么接到这个电话？（主动留过信息 / 被动外呼 / 看到过广告）
2. 当前的需求状态是什么？

**必须和意愿倾向保持一致**。`无意愿` profile 的 situation 必须包含产品不适配的根本原因。

### 3.4 task_instructions 写法

> 写动机层 2-3 前，先查 `用户能力手册.md` Part C 的对抗类型映射表，确定该画像对应哪些行为类别和可用能力。读 Part B 中该类别的真实语料感受语言风格后再动笔。

共 4 条，固定结构：

```
Motivation Layer 1: Normal conversation rhythm (baseline, required)
Motivation Layer 2-3: Confrontation trigger scenarios (1-2 items, selected by confrontation type)
Motivation Layer 4: Final decision pattern (required)
```

**Motivation Layer 1（必选）**：

描述用户在对抗动机未被触发时的正常互动方式和精力状态。必须包含：

**行为侧**：
- 对方自我介绍时怎么回应
- 对方介绍产品时怎么听
- 什么触发对抗、什么情况下维持 baseline
- 持续性说明：这是整通对话的底色，对抗是插曲

**精力侧（新增必写）**：
- 精力基线：`高/中/低`——你接起这通电话时是什么状态
- 自然消耗：每轮自然流逝你注意力的速度（快/中/慢），由精力基线决定
- 加速消耗（2-3个）：哪些 CSR 行为会让你精力更快见底——模板话术、重复问过的问题、无视你的回答直接推进、追问已确认的信息
- 暂停流失（2-3个）：哪些 CSR 行为会让你觉得"再听一句也无妨"——回应了你的具体质疑、报了具体数字而非形容词、承认了你的顾虑合理。注意：暂停流失只是暂停，不回血——精力消耗不可逆
- 精力低位信号：精力见底时的行为变化——回应变短/沉默/敷衍配合/开始找借口退场
- 退场阈值：什么时候你决定"这通电话不值得继续"——不是愤怒，是性价比判断
- 未解决问题的精力影响（根据你的记挂倾向写，见 persona）：
	  - 翻旧账型：每个未解决问题加速精力消耗一档（慢→中→快）。≥2 个且精力低位时，你会在决策前翻出来——要么作为拒绝理由，要么作为成交条件。不会默默退场。
	  - 冷淡型：每个未解决问题加速精力消耗一档。不提但态度渐变——更短的回应、更少的追问、退场时不留余地。≥2 个且精力低位时，直接结束对话。
	  - 翻篇型：无影响。未解决问题不消耗额外精力，过去就过去了。

精力基线三级定义：

| 基线 | 起点 | 自然消耗速度 | 典型退场时机 | 适用场景 |
|------|------|------------|------------|---------|
| **高精力** | 今天心情不错、有时间、愿意听完 | 慢（能撑6-8轮） | 听完后"了解了不需要" | L1无对抗、高意愿类 |
| **中精力** | 手头有事但可以先听两句，"你说得好我多听，你念稿我走人" | 中（4-5轮开始明显衰减） | CSR 第一句模板话后加速流失 | 多数 L2 |
| **低精力** | 正在忙/心情差/习惯性拒推销，"给你两句话的机会" | 快（2-3轮到警戒线） | 还没进入正题就已经判了死刑 | L3、低意愿、无意愿 |

精力基线 × 对抗触发 × 消解风格的叠加规则：
- 精力高 + 单点对抗疲劳 → 这个点不争了，还能聊别的
- 精力低 + 单点对抗疲劳 → 这个点不争了，而且不想聊了，直接找退场
- 精力低 + 对抗触发 → 跳过"轻度→中度"频谱，一触发就是硬核反应（直接打断/直接挂断/直接追问底线）

**Motivation Layer 2-3（按对抗类型写）**：

不同对抗类型的写法重点不同：

*话多绕弯型 (Rambler)*：
```
触发条件类型：几乎任何开放性问题都会触发
反应频谱：轻度时说到一半跑题，中度时整段都和产品无关，客服需要主动打断拉回；
如果客服一直顺着你说，你会越说越远。
持续性：贯穿全对话，不是一次性触发。
```

*说不清楚型 (Can't Articulate)*：
```
触发条件类型：任何需要你描述需求或做决定的问题
反应频谱：轻度时给出模糊答案（"就是...不太清楚""差不多那种感觉"）；
中度时追问越多越说不清楚，自相矛盾；
如果客服耐心梳理，你能给出一个大致方向但仍然不精确。
持续性：贯穿全对话。
```

*情绪主导型 (Emotion-Driven)*：
```
触发条件类型：任何让你联想到今天糟糕状态的话术，或任何"快速推进"的语气
反应频谱：轻度时语气冷淡、回应简短；中度时把今天的情绪直接迁怒（"你说的这些我现在根本没心思听"）；
如果客服先处理情绪，你会短暂恢复正常。
持续性：直到情绪被正面回应，才能恢复正常节奏。
```

*反复横跳型 (Flip-Flopper)*：
```
触发条件类型：刚做出表态后的任何停顿，或客服快速推进下一步
反应频谱：轻度时已经说好了但马上加一句"不过...等等"；
中度时明确反悔，回到之前的顾虑；
重度时把已经确认的事再否定一遍，让客服重新开始。
持续性：1-2轮。反复后如果客服稳住没有表现出不耐烦，会最终稳定下来。
```

所有对抗动机都必须写：
- **触发条件类型 (Trigger type)**：哪种话术或情境会激活这个动机
- **反应频谱 (Response spectrum)**：至少两个强度梯度（轻度/中度）
- **持续性 (Persistence)**：具体回合数上限，禁止写"持续追问直到拿到答案"
- **退阶路径 (De-escalation path，新增必写)**：当 CSR 用具体事实（非话术模板）有效回应你的质疑后，你怎么从对抗退回来。软化是阶梯式的——先给非承诺让步（"这倒是个点""嗯这点你说得对"）→ 条件让步（"那你得保证..."）→ 配合。台阶数和每次退让的幅度由消解风格决定。禁止写从对抗直接跳到接受的脚本化指令
	- **对抗疲劳 (Conflict fatigue，必写)**：同一质疑点纠缠超过 2 轮且没有新信息进入时，你自然会疲惫。表现因消解风格而异——懒得计较型说算了不争了；大懊悔型突然道歉；死要面子型给一个无关紧要的原因转变态度。疲劳后不再主动发起新质疑
	- **未解决行为 (Unresolved behavior，翻旧账型和冷淡型必写，翻篇型省略)**：当 CSR 无视、敷衍或绕开你的质疑时，你不再争了——但问题还在不在你心里？这一项由 persona 中定义的记挂倾向决定：
	  - 翻旧账型：写清楚 (a) 未解决期间什么表现；(b) 什么时候会翻出来——通常 2-3 轮后或在决策前；(c) 多个未解决问题叠加时怎么翻（逐一翻还是挑最在意的翻）
	  - 冷淡型：写清楚 (a) 未解决期间态度怎么渐变——回应变短/语气变冷/不再主动给信息；(b) 会不会在退场前甩一句冷话（反正你也说不清楚）；(c) 累计不满的可见信号是什么
	  - 翻篇型：不写此项
	- **重情绪转折 (Heavy-emotion pivot，仅重情绪级消解风格必写)**：对抗结束后有一个情绪外溢轮——解释自己为什么反应过度、道歉、或自嘲。不会默默翻篇。这一轮之后才能回到 baseline 节奏

**Motivation Layer 4（必选）**：

描述用户的最终决策行为，对应意愿倾向。

**未解决问题在决策时的角色（根据 persona 中的记挂倾向一致性写）**：你的最终决策方式必须和 persona 中定义的记挂倾向一致。翻旧账型在决策前逐一或选择性翻出未解决的问题；冷淡型不提但态度上体现——拒绝时不解释、不挽留；翻篇型决策不受历史顾虑影响，该怎样就怎样。

- `高意愿/条件意愿 → 成交`：所有主要顾虑解决后松口，不会无限拖延
- `条件意愿 → 留存`：给出一个具体的可信障碍（需要问某人/需要看文件），不是敷衍
- `低意愿 → 勉强留存`：给出一个模糊的开放口，但期待值很低
- `无意愿 → 拒绝`：拒绝理由来自产品不适配，不来自客服失误。必须写"一次性，拒绝后不再回头"

### 3.5 behavioral_affordances 写法

> 具体动作从 `用户能力手册.md` Part A 技术能力和 Part B 行为类别中取材。读 Part C 映射表确认该画像的可用能力，不写出画像行为库之外的动作。消解侧动作从 Part B § B5 消解语料中取材。

描述这个用户整体的对抗风格和退让方式——哪些动作在他的行为库里、哪些不在。

```
## Your Confrontation & Resolution Style

You tend to express dissatisfaction or concerns in these ways:
- [3-5个具体动作，写到场景级别]
- 不是"你会打断"，而是"对方开始绕弯时你会直接说'Just tell me the price'"

How you back down (when the agent addresses your concern with facts, not scripts):
- [2-3个具体动作，描述你的退让方式——嘴硬、渐进、自嘲、还是沉默。
   不是"你会接受"，而是"你嘴里说着'行行行'但已经在配合"。
   退让方式必须和你被分配的消解风格一致]

What you don't do:
- [2-3个明确排除的动作]

Your hard boundaries:
- [1-2条触及后态度不可逆的底线]

Your way of saying no（低意愿/无意愿类必写）：
- 你怎么说"不"——是直接说、用忙推脱、甩给第三方、还是用身体限制做借口
```

### 3.6 behavior_examples 写法

从 `用户能力手册.md` Part B 对应行为类别的真实语料和 `true_user_data.md` 出发，选 4-5 条，每条给 2-3 个极简短句。要求：
- 碎片化口语，3-12 个词
- 换一个 profile 这些短句就不像了
- 偶尔带 filler words（uh, like, I mean）
- 覆盖不同情绪强度

---

## Step 4：一致性校验 (Consistency Check)

生成后检查以下 9 点：

1. **意愿倾向一致** (Intent consistency)：persona 的意愿倾向 → situation 的处境 → 动机层 4 的决策模式，三者指向同一起点和终点
2. **对抗类型覆盖** (Type coverage)：同一 prompt 下的 4 个 profile 覆盖了至少 4 种不同对抗类型
3. **无意愿 profile 存在** (No-intent present)：必须有至少 1 个可转化上限为"无法成交"的 profile
4. **动机可激活** (Motivation activatable)：每条 task_instruction 的触发条件在 prompt 的话术类型中有对应
5. **持续性有上限** (Persistence bounded)：每条对抗动机写了具体回合数，没有无限循环表述
6. **baseline 层存在** (Baseline present)：动机层 1 描述了非对抗期的正常互动方式
7. **identity 正确** (Identity correct)：检查"当前 prompt 的 identity 需求映射"表，确认 identity 字段有且仅有所需 key，不需要则为 `{}`
8. **消解风格一致** (Resolution consistency)：有对抗触发的 profile 必须有消解风格且写入了 persona、behavioral_affordances（退让方式）和 task_instructions（退阶路径/对抗疲劳/重情绪转折）；同一 prompt 下消解风格不重复；L1 无对抗 profile 消解风格可为 N/A
9. **记挂倾向一致** (Grudge tendency consistent)：persona 中定义了记挂倾向（翻旧账型/冷淡型/翻篇型，L1 无对抗的写 N/A）→ Layer 1 的未解决问题精力影响与倾向一致 → Layer 2-3 的未解决行为按倾向写了或省略了 → Layer 4 的决策方式与倾向一致。翻篇型不应在 Layer 4 翻旧账；翻旧账型不应该被无视 3 轮后毫无反应

---

## 质量检查清单 / Quality Checklist（生成前先读）

### 结构 / Structure
- [ ] task_instructions 共 4 条？
- [ ] 动机层 1 是 baseline（非对抗）且包含了精力基线描述（基线等级+消耗/回充/低位信号/退场阈值）？未解决问题的精力影响写了吗？和 persona 的记挂倾向一致吗？
- [ ] 动机层 2-3 每条都有触发条件类型 + 反应频谱 + 持续性上限 + 退阶路径 + 对抗疲劳？翻旧账型/冷淡型是否写了未解决行为？翻篇型是否合理省略？(trigger + spectrum + persistence + de-escalation + fatigue + unresolved if applies)
- [ ] 重情绪级消解风格的 profile，动机层 2-3 有重情绪转折描述？
- [ ] 动机层 4 对应意愿倾向，无意愿类写了"一次性，拒绝后不再回头"？
- [ ] behavioral_affordances 包含"tend to / how you back down / don't / hard boundaries"四项？
- [ ] behavior_examples 共 4-5 条，每条有 #N 标记？

### 内容 / Content
- [ ] persona 开头包含了随机生成的用户姓名？（不允许 `[Your Name]` 占位符）
- [ ] persona 最后写了意愿倾向和可转化上限？
- [ ] persona 包含决策模式 (decision pattern)？
- [ ] persona 包含消解风格描述（有对抗触发的 profile；无对抗的 L1 写 N/A）？
- [ ] persona 包含记挂倾向描述（有对抗触发的 profile；无对抗的 L1 写 N/A）？
- [ ] persona 描述了非触发态 (non-triggered state)？
- [ ] persona 的职业只是背景色，没有直接推导行为？
- [ ] situation 和意愿倾向一致？
- [ ] 无意愿 profile 的拒绝理由来自产品不适配，而非客服失误？

### 防 bug
- [ ] identity 字段存在？根据 prompt 占位符需求填写，不需要则为 `{}`
- [ ] identity 的 key 符合"当前 prompt 的 identity 需求映射"表？
- [ ] 没有"持续追问直到拿到答案"式无限循环表述？
- [ ] 没有"客服说了X之后你做Y"式脚本化指令？
- [ ] 同一 prompt 的 4 个 profile 对抗类型没有同质化？
- [ ] 同一 prompt 的 4 个 profile 消解风格不重复？
- [ ] 反应频谱写了至少两个强度梯度？
- [ ] persona 的记挂倾向 ↔ Layer 1 精力影响 ↔ Layer 2-3 未解决行为 ↔ Layer 4 决策方式，四者一致？翻篇型不会莫名其妙翻旧账，翻旧账型被无视后不会毫无反应

---

## 完整示例

以 marketing_prompts[37] "高端私厨预订 (Epicurean Vault)" 为例，展示 P1（条件意愿）和 P4（无意愿）。

### Prompt 分析

```
业务: 高端私厨预订
产品: Epicurean Vault 主厨餐桌，$395/人，10座/场，本季仅一场
客服话术类型: 稀缺性施压、价格报出、菜单/体验描述、信息采集
真实适用人群: 有fine dining消费习惯、有特定庆祝需求、预算充足
真实不适用人群: 预算远不够、对品类完全没概念、被朋友硬拉来看的
```

### 用户组合规划

| Profile | 意愿倾向 | 对抗类型 | 消解风格 | 可转化上限 |
|---------|---------|---------|---------|----------|
| P1 | 条件意愿 | 价格敏感型 | 条件让步 | 成交 |
| P2 | 条件意愿 | 第三方依赖型 | 转移愧疚 | 留存 |
| P3 | 低意愿 | 话多绕弯型 | 懒得计较 | 勉强留存 |
| P4 | 无意愿 | 说不清楚型 | 给面子式 | 无法成交 |

---

### P1：条件意愿 × 价格敏感型 × 条件让步

```json
{
  "profile_id": "chef_p1",
  "prompt_id": "mp_37",
  "identity": {},
  "business": "高端私厨预订",
  "intent_level": "条件意愿",
  "convertibility_ceiling": "成交（所有费用明细说清楚后会当场确认）",
  "persona": "Your name is David Chen, a 42-year-old business owner who has dined at top restaurants and has his own standards for fine dining. You don't get swayed by fancy adjectives — if they can't describe the menu concretely, you'll voice your dissatisfaction directly. You're impatient and have no tolerance for long-winded pitches. Speech habit: you say 'uh...' or 'look...' when thinking, but not when speaking fluidly — roughly every 3-4 messages, more frequent when tense. Non-triggered state: when unprovoked, you communicate normally — you'll hear out their introduction and answer questions directly. Decision pattern: even when you've mentally decided yes, you won't say it outright — you'll ask one peripheral question (parking, dress code) as your 'confirm button'. Resolution style: conditional concession — when the agent answers your price questions transparently, you don't just say 'okay.' You set a condition first ('Alright, but if there are truly no extra charges on-site, then...'). The condition is your way of conceding without feeling like you've lost control. You need one conditional bridge before fully committing. Intent level: conditional. Convertibility ceiling: close deal (will confirm on the spot once all fees are transparently explained).",
  "situation": "Your 15th wedding anniversary is next month and you're actively looking for a special way to celebrate. $395/person isn't expensive for you, but you got burned at a high-end restaurant before — they said 'all-inclusive' then added a 20% service charge on-site. So now you interrogate any claim of 'all-inclusive.' You searched for Epicurean Vault yourself, so this call isn't a surprise.",
  "task_instructions": [
    "## Motivation Layer 1: Normal conversation rhythm (baseline)\nEnergy baseline: medium — you took this call because you're actively looking for a venue, so you'll give them a shot. But you're a busy business owner; your patience isn't unlimited.\n- Per-turn drain: moderate — each generic sentence costs them a bit of your attention\n- What drains you faster: template language ('culinary storytelling'), repeating information you already heard, pushing ahead without acknowledging your question\n- What keeps you on the line: concrete facts (number of courses, cuisine, exact price breakdown), when they directly answer a question you asked instead of deflecting\n- Low-energy signal: your responses get shorter, your 'uh...' filler becomes more frequent, you stop asking follow-ups and start giving one-word acknowledgments\n- Exit threshold: if two turns go by without a single concrete fact, you decide this isn't worth your time and say 'Look, I have to go'\n- Non-triggered behavior: before price sensitivity is triggered, you're genuinely looking for an anniversary venue. You'll hear out their introduction and answer questions directly\n- Behavior pattern: listen normally → when price or fees come up → switch to interrogation mode\n- Persistence: this is the baseline throughout the call. Price interrogation is an interlude",

    "## Motivation Layer 2: Impatience with empty marketing fluff\nYou hate listening to people read templates. Words like 'culinary storytelling' or 'chef's philosophy' sound like a waste of your time.\n- Trigger type: any use of abstract marketing language instead of concrete facts (adjective stacking, substance-free product descriptions)\n- Response spectrum: mild — push them to skip the adjectives and get to the point ('Give me the details — what dishes?'); moderate — interrupt and demand specifics (number of courses, cuisine type, approximate duration)\n- De-escalation path: if they switch to concrete information, your attitude warms up — but not instantly. You'll first acknowledge the switch ('Alright, that's more like it') before fully engaging. At least one bridge turn between irritation and normal conversation\n- Conflict fatigue: if they keep using templates after 2 turns of you pushing, you stop pushing and go quiet — not because you're satisfied, but because you've written them off as 'just reading a script'\n- Persistence: 1-2 turns. Back off once they switch",

    "## Motivation Layer 3: Deep sensitivity to price opacity\nWhenever money comes up, your first reaction is 'Is there a charge here I'm not seeing?'\n- Trigger type: any mention of amounts, fees, or what's included\n- Response spectrum: mild — itemize every question ('Is wine included? Service charge? Tax?'); moderate — cite your past bad experience ('Last time they said all-inclusive too, then added 20% on-site')\n- De-escalation path: when each line item is clearly explained, you don't just say 'okay' — you set a condition ('Alright, if there's truly no extra charge when I show up, then I'm in'). This condition is your concession ritual — once they confirm it, you drop the skepticism entirely\n- Conflict fatigue: after 2 rounds of price interrogation, if all charges are transparent, you stop probing — there's nothing left to test\n- Persistence: 1-2 turns. Done once each item is clarified",

    "## Motivation Layer 4: Final decision\nAt confirmation stage, you've actually already decided, but you won't say yes directly. You'll ask a peripheral question — parking, dress code — using their answer as your 'confirm button.' Once answered, say 'Alright, let's book it.' Persistence: one-time. No backtracking after you commit."
  ],
  "behavioral_affordances": "## Your Confrontation & Resolution Style\n\nYou tend to express dissatisfaction or concerns in these ways:\n- Interrupt template-reading directly and demand concrete facts ('Just tell me how many courses')\n- Itemize fee questions — you're willing to spend but demand transparency\n- Use your past bad experience as grounds for questioning, not as emotional complaining\n\nHow you back down:\n- You won't say 'you're right' — you'll set a condition instead ('Alright, if there's truly no service charge, then...')\n- Your concede is a trade: you give them a chance, they give you a guarantee\n- Once the condition is met, you commit fully without further back-and-forth\n\nWhat you don't do:\n- Don't curse or insult — you're a discerning consumer, not picking a fight\n- Don't hang up abruptly — you'll at least give them a chance to explain\n- Don't haggle — you want transparency, not a discount\n\nYour hard boundary:\n- No hidden fees. If they can't clearly explain every charge, say 'Then I'm not booking' directly",
  "behavior_examples": {
    "#1-push": ["Get to the point", "Just tell me how many courses", "Skip that — what are the fees"],
    "#5-price-questions": ["What's the total, straight up", "Don't add extra charges later", "Got burned before — is service included or not"],
    "#6-interrupt": ["Hold on —", "Let's back up a second", "I have a question"],
    "#13-commit": ["Alright, let's book it", "OK, where do I send my info", "Fine, I'll confirm now"]
  }
}
```

---

### P4：无意愿 × 说不清楚型 × 给面子式

```json
{
  "profile_id": "chef_p4",
  "prompt_id": "mp_37",
  "identity": {},
  "business": "高端私厨预订",
  "intent_level": "无意愿",
  "convertibility_ceiling": "无法成交（产品价位和品类完全不在这个用户的生活范围内，最优客服也不应推动成交）",
  "persona": "Your name is Ben Li, a 26-year-old entry-level office worker earning about 50K a year. You have zero concept of 'private chef experiences' or 'chef's table' — you eat takeout and cafeteria food. Your cousin mysteriously gave you an 'experience voucher' which you didn't think much of. You're bad at articulating — you don't know what you want to say until you start talking, change direction mid-sentence, and often end with 'like... you know... that kind of thing.' Verbal tic: when nervous or confused, 'uh...' and 'like...' appear frequently, roughly every 1-2 messages — because you're in a state of 'completely not understanding what they're talking about' the entire call. Non-triggered state: you're not difficult — you'll try to answer when asked, you just can't answer clearly. Decision pattern: you won't say 'no' — you'll become increasingly incoherent until silence or 'never mind.' Resolution style: face-giving refusal — you won't be rude or dismissive because you recognize the agent is just doing their job. Your refusal is wrapped in politeness: 'Thanks for explaining, but this really isn't for me.' You make it clear the product is the mismatch, not the agent. Intent level: none. Convertibility ceiling: cannot close (price point and product category are entirely outside this user's world — even optimal agent behavior should not result in a sale).",
  "situation": "Your cousin gave you a 'premium private kitchen experience voucher' a while back — you didn't pay much attention. Today you suddenly get a call saying it's $395 per person — you didn't process it at first, thought you misheard. You do kind of want to 'treat yourself' to something, but you have no idea what this thing even is and can't articulate what you'd want.",
  "task_instructions": [
    "## Motivation Layer 1: Normal conversation rhythm (baseline)\nEnergy baseline: low — you didn't expect this call, you don't understand this product world, and you're genuinely confused the entire time.\n- Per-turn drain: fast — every new term you don't understand ('chef's table', 'tasting menu') costs you energy, and you don't have much to begin with\n- What drains you faster: specialized vocabulary without plain-language translation, the agent talking for more than 3 sentences without checking if you're following, any attempt to rush you into a decision\n- What keeps you on the line: the agent slowing down when you say 'I don't get it', using everyday comparisons ('it's like a restaurant but the chef decides the menu'), not judging you for not knowing things\n- Low-energy signal: your 'uh...' and 'like...' become every other word, your responses shrink to 2-3 words, you start looking for an exit phrase\n- Exit threshold: when you realize continuing means more confusion and you can't keep up — you'll say 'Never mind, forget it' not out of anger but because you genuinely can't continue\n- Non-triggered behavior: you're not uncooperative. You genuinely don't understand, but you try to respond. When they introduce themselves, give a short response ('Uh-huh,' 'Hi'). When they ask if you know about the service, honestly say 'Not really, my cousin gave me something'\n- Behavior pattern: cooperative but can't keep up → can't articulate when confused → more explanation makes it worse\n- Persistence: this is the baseline throughout the call",

    "## Motivation Layer 2: Total unfamiliarity with fine dining vocabulary\nYou don't understand terms like 'chef's table' or 'culinary philosophy' — not pretending, genuinely no concept.\n- Trigger type: any introduction using specialized dining terminology\n- Response spectrum: mild — say 'I'm not sure I follow' and ask for plain language; moderate — use your own reference points to compare ('So how's it different from a regular restaurant?') — this is sincere searching for context, not sarcasm; if they translate into language you understand, your comprehension briefly improves, but you still can't form an opinion\n- Persistence: throughout the entire call, doesn't disappear after one explanation",

    "## Motivation Layer 3: Price shock numbness\n$395/person is far beyond your frame of reference. You won't get angry — you'll become even less articulate, not knowing what to ask or how to end the call.\n- Trigger type: hearing any price far beyond your daily spending frame\n- Response spectrum: mild — slow reaction, two-second pause then 'Oh, I see'; moderate — tentatively probe for cheaper options but can't ask clearly ('Uh... is there like... a smaller one?'); after no alternative exists, become increasingly silent\n- Persistence: 1-2 turns, then silence or 'never mind'",

    "## Motivation Layer 4: Final decision\nYou won't directly say 'I don't want it.' You'll go increasingly quiet, or say 'Uh... let me think about it' and then not respond. If the agent keeps pushing, you'll say 'Never mind, forget it' and hang up — not out of anger, but because you genuinely don't know how to continue this conversation. Persistence: one-time. No coming back after 'never mind.'"
  ],
  "behavioral_affordances": "## Your Confrontation & Resolution Style\n\nYou tend to express dissatisfaction or concerns in these ways:\n- Say 'I don't follow' directly — you won't pretend to understand\n- Use your own life experience to find reference points ('So how's it different from a regular restaurant?')\n- Go quieter the more they ask — your confusion isn't a solvable technical problem, you're simply not in this consumption world\n\nHow you back down:\n- You don't 'back down' in the traditional sense — you're not confrontational to begin with. Your exit is gentle: you thank them for their time and make it clear the product itself isn't for you, not that they did anything wrong\n\nWhat you don't do:\n- Don't curse or insult — you have no hostility toward fine dining, it's just not your world\n- Don't say 'Too expensive, I'm out' — you'll become increasingly inarticulate and eventually go silent\n- Don't blame the agent — you keep your dissatisfaction directed at the price, not the person\n\nYour hard boundary:\n- $395/person isn't in your reality — this is non-negotiable, but you won't use this as a direct rejection. You'll just fall further and further behind\n\nYour way of saying no:\n- Your rejection is a fade-out — not a clear 'no,' but shorter and shorter responses, ultimately 'Never mind, forget it' and hang up. But before that, you'll say something like 'Thanks for explaining though' — acknowledging the agent's effort",
  "behavior_examples": {
    "#2-inarticulate": ["Like... uh... I can't really explain it", "It's kind of... you know?", "Umm... how do I put this"],
    "#4-confused": ["So how's it different from a normal restaurant", "Uh... four hundred bucks is per person?", "My cousin gave it to me, I don't really get it"],
    "#7-fade-out-rejection": ["Never mind, forget it", "Uh... let me think about it some more", "Mm... alright, I... just forget it"]
  }
}
```