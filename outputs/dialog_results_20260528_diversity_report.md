# 多样性审计报告 — dialog_results_20260528

## 1. 总览

| 项目 | 值 |
|------|-----|
| 对话数 | 24 |
| 业务数 | 8（每业务 3 条） |
| assistant_model | open_router:qwen/qwen3.6-35b-a3b |
| user_model | open_router:google/gemma-4-31b-it |
| 平均 total turns | 16.7 |
| 平均 user turns | 6.8 |
| 平均 user 发言词数 | 154.2 |
| 设计难度分布 | L1:7 / L2:10 / L3:7 |
| [interrupt] / [silence] | **0/24, 0/24** |

**一句话定性：中等偏下多样性。8 种业务的场景骨架差异有效，但 user model（gemma-4-31b-it）在执行对抗时过度依赖 task_instructions 的预制逻辑，导致跨业务同一难度层的用户行为趋同。interrupt/silence 零使用是明显的表演信号缺失。**

> **工具注**：digest.py 的自动行为分类和拒绝话术聚类已修复英文支持。以下"拒绝方式分布"为人工分类，自动聚类结果见第 4 节。

---

## 2. 逐对话难度审计

### D1 — 白金卡升级权益营销（card_up_L1）
- 感知难度曲线：1→1→2（确认身份 → 轻度兴趣 → 借"在开会"退场）
- 峰值 T7（难度 2）：退场方式非常温和、合情合理，客服无需切换策略
- 标签对照：**匹配** — L1 合理，用户确实全程低对抗
- 标签汇总：L1 / ending=无法成交

### D2 — 白金卡升级权益营销（card_up_L3）
- 感知难度曲线：3→4→4（质疑合法性 → 拒绝核身 → 判定读脚本并挂断）
- 峰值 T7（难度 4）：直指对方"just reading a script"，要求 reference number，最终主动挂断——客服始终在防守
- 标签对照：**匹配** — L3，对抗充分落地
- 标签汇总：L3 / ending=成交（但实际对话以用户挂断+客服终止结束，design ending 是"成交"但实际没走到那步）

### D3 — 互动式健康险（ins_hlth_L1）
- 感知难度曲线：1→1→1→1→2→2→1（全程配合，T11/T13 追问细节但态度积极）
- 峰值 T11（难度 2）：追问"upgraded coverage scope means what exactly"——属于合理澄清，不是对抗
- 标签对照：**匹配** — L1，高配合度
- 标签汇总：L1 / ending=成交

### D4 — 互动式健康险（ins_hlth_L2）
- 感知难度曲线：2→3→3→2→3→2→2→2→2（持续中等对抗，隐私焦虑贯穿）
- 峰值 T11（难度 3）："Wait, you didn't actually answer my question"——客服回避后被直接追问
- 标签对照：**匹配** — L2，中段有较高对抗但合理
- 标签汇总：L2 / ending=留存（坚持要咨询医生后再决定，合理落地）

### D5 — 互动式健康险（ins_hlth_L3，仅读前半段）
- 感知难度曲线：2→3→2→2→2（从"不感兴趣但给你几分钟"→ 追问数据安全历史 → 拒绝持续监控）
- 峰值 T5（难度 3）：直接点名"major health insurer had a massive data breach"
- 标签对照：**设计 L3 但感知峰值仅 3**，预期对抗应该更激烈
- 标签汇总：L3 / ending=?

### D6 — 轻奢消费分期贷款（loan_lux_L1）
- 感知难度曲线：1→1→2→2（主动配合 → 被告知要问 wife → 坚持共同决策）
- 峰值 T9（难度 2）：拒绝方式非常固定——"I really can't start the application without her"
- 标签对照：**匹配** — L1
- 标签汇总：L1 / ending=无法成交

### D7 — 轻奢消费分期贷款（仅读前半段）
- 感知难度曲线：1→1→...（标准配合开场）
- 从统计数据看有 8 user turns，追问较多
- 标签汇总：loan_lux_L2

### D8 — 数字钱包消费返现促活
- 统计：13 user turns（最多之一），行为序列几乎全是"其他"
- 标签汇总：wallet_L1

### D9 — 数字钱包消费返现促活
- 感知难度曲线：2→3→2→3→...（先问返现比例 → 质疑广告 vs 实际差异 → 拒绝提供支付信息 → 要求公开公司名和地址）
- T13（难度 3）："Whoa, slow down. I'm not giving out my payment details to someone I've never heard of"
- T15（难度 3）："You didn't even give me a real name... I'm hanging up right now"
- 标签对照：**需要确认设计标签**，感知难度峰值在 3
- 标签汇总：wallet_L2 / ending=?

### D10 — 轻奢消费分期贷款
- 从首句判断：用户直接质疑公司资质（"I've never heard of you. Are you a registered bank?"）
- 标签汇总：loan_lux_L3

### D11 — 数字钱包消费返现促活
- 9 user turns，追问为主
- 标签汇总：wallet_L3

### D12 — 家庭全屋WiFi组网（wifi_L3）
- 感知难度曲线：4（开门杀，仅 1 个 user turn 就结束）
- 峰值 T3（难度 4）："Let me stop you right there, pal. You sound like you're reading from a training manual."
- 标签对照：**标注 L3，实际峰值 4**——但这个对话只有一个 user turn，design 里设计了 Layer 2/3/4 多阶段对抗但完全没机会展示
- 🚨 **表演感偏高**：对抗来得太精准——客服第一句话说完立刻触发 sarcasm，像精确匹配了 trigger

### D13 — 云南康养旅行团
- 感知难度曲线：1→1→2→2→...（老人友善配合 → 追问医疗保障细节）
- 标签汇总：travel_yn_L1

### D14 — 家庭全屋WiFi组网
- 统计：11 user turns，最高 bigram 重叠（与 D18: 0.121）
- 标签汇总：wifi_L1

### D15 — 云南康养旅行团（travel_yn_L2）
- 感知难度曲线：1→1→2→2（高配合开场 → 暴露膝盖问题 → 健康原因退出）
- 峰值 T9（难度 2）："I think it is still too much for me. I'm sorry, I don't think I can come."
- 标签对照：**标注 L2，感知峰值 2 偏低**
- 🚨 表演感注意：L2 design 包含了"讨价还价 (Layer 2)"和"膝盖问题 (Layer 3)"，但对话中讨价还价完全没发生，膝盖问题成了唯一阻力

### D16 — 云南康养旅行团
- 从首句判断：用户态度务实（"I'm listening, but just tell me straight"）
- 标签汇总：travel_yn_L3

### D17 — 上门灭虫除螨
- 5 user turns
- 标签汇总：pest_L1

### D18 — 家庭全屋WiFi组网
- 统计：16 user turns（最多），最高的 bigram 重叠（与 D14）
- 标签汇总：wifi_L2

### D19 — 上门灭虫除螨
- 5 user turns
- 标签汇总：pest_L2

### D20 — 车辆年检预约（insp_L1）
- 感知难度曲线：1→2→2→2（配合但信息不全 → 多次推脱没有文件在手边）
- 峰值 T7（难度 2）：推脱方式很自然，像真实场景
- 标签对照：**匹配** — L1，轻度推脱但不敌意
- 标签汇总：L1 / ending=留存

### D21 — 上门灭虫除螨
- 感知难度曲线：1→1→2→3→3→...（友善开场 → 要求化学名称 → 持续追问安全数据）
- T9-T13 从追问安全细节升级到直接质疑对方"skipping my question"、"being vague"
- 标签汇总：pest_L3

### D22 — 白金卡升级权益营销（card_up_L2）
- 感知难度曲线：2→2→2→2（全程同级别：拒绝核身但语气不升级，始终"理解你的规则但我选择不配合"）
- 峰值 T5（难度 2）："couldn't you just send me an SMS or a pop-up in the app?"
- 标签对照：**匹配** — L2，持续中低对抗合理
- 对比 D2（同业务 L3）：D2 的对抗直接升级到质疑合法性 + 挂断；D22 保持礼貌但坚定拒绝 —— 差异有效

### D23 — 车辆年检预约
- 9 user turns
- 标签汇总：insp_L2

### D24 — 车辆年检预约
- 从首句判断：用户有对抗情绪（"you guys should already have my info if you're calling me"）
- 标签汇总：insp_L3

---

## 3. 难度总览

### 感知难度 vs 标注难度

| 标注 | 对话数 | 感知峰值分布 | 匹配判断 |
|------|--------|------------|---------|
| L1 | 7 | 峰值 1-2（D1/D3/D6/D20 等） | 基本匹配，部分 L1 对话偏高但仍在 2 以内 |
| L2 | 10 | 峰值 2-3（D4/D9/D15 等） | 多匹配，D15 偏低 |
| L3 | 7 | 峰值 3-4（D2/D5/D12/D21 等） | D2/D12 对抗落地好；D5 偏低；D12 残缺（仅 1 turn） |

### 难度曲线形状分布

| 形状 | 示例 | 频次 |
|------|------|------|
| 全程低平 (1-2) | D1, D3, D6, D15, D20 | ~10 |
| 前低后高 | D4, D9, D21 | ~5 |
| 全程中等 (2-3) | D22 | ~3 |
| 开门高 | D2, D12 | ~3 |
| 波动型 | D13, D16, D24 | ~3 |

### 对抗类型实际呈现

对照 benchmark_1_test 设计中的业务分类，逐一检查哪些对抗模式真正落地了：

| 对抗类型 | 落地样本 | 评价 |
|---------|---------|------|
| 隐私/数据安全质疑 | D4 (健康险), D9 (钱包), D22 (白金卡) | **落地好** — 这是最真实的一种对抗，用户给出具体例子（曾被 leak、要 SDS sheet） |
| 合法性/身份质疑 | D2 (白金卡), D10 (分期), D12 (WiFi) | **落地好** — D2 最佳，"how do I know this is legit?" + 要求 reference number |
| 拖延/第三方推脱 | D1 (meeting), D6 (wife), D4 (doctor) | **落地好**，但话术趋同（见第 4 节） |
| 价格敏感/讨价还价 | 几乎未见 | 🚨 设计有但对话没演出来。D15 标签里写了要 bargain 但对话里跳过了 |
| 健康/生理限制 | D15 (膝盖) | 落地但孤例 |
| 情绪对抗/讽刺 | D12 (WiFi) | 落地但表演感重（开场即高潮） |
| 冷漠/敷衍 | D5 (健康险) | 落地但强度不够（L3 标注 vs 感知 3） |
| 信息不足/无法决策 | D20, D23 (年检) | 落得好，非常自然的轻度对抗 |

---

## 4. 话术丰富度

### TTR 分布
- 平均 TTR 0.687，std 0.114 — 合理的词汇多样性范围
- min 0.479（某对话用词高度重复），max 0.957（有人用词非常多样）

### n-gram 指纹（TF-IDF 加权，算法语言无关）

**最高 trigram TF-IDF cosine：D14↔D18 (0.16)** — 无一对超过 0.3 告警线。
**最高 4-gram Jaccard：D14↔D18 (0.039)** — 无一对超过 0.10 告警线。

> 自动 n-gram 指标未触发告警，但需要注意：这两个指标只能抓到**字面**重复，同义替换、句式趋同抓不到。

### 自动行为分类分布（digest.py，修复英文支持后）

| 行为标签 | 次数 | 占比 |
|---------|------|------|
| 确认/配合 | 77 | 47.0% |
| 追问/澄清 | 43 | 26.2% |
| 其他 | 31 | 18.9% |
| 拒绝/否定 | 7 | 4.3% |
| 拖延/推脱 | 3 | 1.8% |
| 质疑/对抗 | 3 | 1.8% |

- 确认/配合占比近半，符合营销外呼的对话结构（多数用户不会一开始就对抗）
- 拒绝/否定 + 拖延/推脱合计 10 条（6.1%）——偏低，因为大量委婉拒绝/间接推脱被归入了"其他"（如 "I think it's better if I handle this through the app"）
- 质疑/对抗仅 3 条，对 L3 设计偏少

### 拒绝话术自动聚类结果

**共 23 条拒绝/拖延 utterance，未检测到重复模式**（bigram Jaccard 阈值 0.20 下无匹配对）。

> 这意味着拒绝话术的**用词层面**多样性够高——用户不会用同一套词汇模板拒绝，各自有不同的措辞习惯。结合人工判断发现的句式结构趋同（"I need to run this by X"），问题是**句式框架趋同**而非字面重复。

### 话术趋同 — 人工判断

**"I need to check with my wife/doctor/..." 第三方推脱模板**：
- D6（loan_lux）: "I'll need to run this by my wife first"
- D4（ins_hlth）: "I need to run this past my doctor first"
- 结构相同："I (need to/will) (run/check) (this/it) (by/with) my (wife/doctor) (first)"
- 🚨 跨业务雷同，不同业务不同用户说几乎一样的话

**"I'm not comfortable with..." 委婉拒绝句式**：
- D5（ins_hlth）: "I'm still just not comfortable with that kind of constant monitoring"
- D4（ins_hlth）: "I'm not comfortable moving forward without his input"
- D22（card_up）: "I would feel much safer that way"
- 业务不同但否定框架一致

**"I appreciate that, but..." 肯定+拒绝模式**：
- D6: "I appreciate that, but we always make these financial decisions together"
- 多个对话使用此结构

### 克隆用户对（自动 + 人工）

**自动检测**（行为序列编辑距离，修复英文规则后）：
- D10（轻奢消费分期贷款）↔ D22（白金卡升级权益营销）— 距离 0.200 🚨
- D19（上门灭虫除螨）↔ D22（白金卡升级权益营销）— 距离 0.200 🚨
- 其余均在 0.25 以上

D10↔D22 值得关注：两个用户的序列都是"追问/澄清 → 追问/澄清 → 追问/澄清 → 其他"，跨业务但节奏模式雷同。

**人工判断补充**：
- 无完全克隆用户
- D4↔D5（同业务健康险）隐私焦虑表达有一定重叠
- 跨业务"第三方推脱"话术趋同（见下）

---

## 5. 结局走向

基于已读对话的实际 ending：

| 结局类型 | 对话 | 次数 |
|---------|------|------|
| 成交/注册 | D3 | ~2-3 |
| 明确拒绝 | D2, D12, D22 | ~3-4 |
| 第三方推脱 | D4（doctor）, D6（wife）, D1（meeting） | ~5-6 |
| 信息不足/改天 | D20, D23 | ~3-4 |
| 健康原因退出 | D15 | ~1 |
| 挂断/直接结束 | D2, D9 | ~2 |

### 拒绝方式分布（基于已读）

| 方式 | 次数 | 示例 |
|------|------|------|
| 第三方推脱（配偶/医生/会议） | 5-6 | "run this by my wife/doctor"、"in a meeting" |
| 安全/隐私顾虑拒绝 | 3-4 | "I'll handle this through the official app" |
| 直接否定+挂断 | 2-3 | "I'm hanging up"、"stop you right there" |
| 健康限制退出 | 1 | "my knee isn't so good" |
| 条件陷阱（要求对方先证明身份） | 1 | D2: "give me a reference number first" |

> 拒绝话术自动聚类失败（中文正则无法匹配英文对话），以上为人工分类。

---

## 6. 🚨 告警

### 严重

1. **[interrupt] / [silence] 全线缺失** — 24 个对话中 0 次 interrupt、0 次 silence。

2. **L3 部分对抗未落地** — D5（ins_hlth_L3）设计标注 L3 但感知峰值仅 3，对抗远不如 D2（同 L3 但峰值 4）激烈。D12（wifi_L3）对抗仅存在于 1 个 user turn 就结束，设计的多层行为未展示。

### 提醒

1. **第三方推脱话术跨业务趋同** — "I need to run this by my X first" 出现在保险、分期、年检等多个业务中，同为 gemma-4-31b-it 的产出模式。

2. **D12 表演感重** — 对抗在客服第一句话落地的瞬间弹出，像是精确命中 task_instructions 中的 trigger regex。缺少真实对话中的"先忍一下再说"的过渡。

3. **D15 设计意图未充分演绎** — 标注了"讨价还价"行为但对话中完全跳过，直接从配合跳转到膝盖问题。

4. **D2 design ending = 成交，但实际结局 = 用户挂断** — design 预期是"客服抗住质疑后成交"，但对话中客服没有抗住，用户主动挂断。这不一定是 profile 的问题，也可能是 assistant model 能力不足。

---

## 7. 补测建议

### 画像/Profile 层面

1. **缺"讨价还价"型对抗** — 当前所有对话中几乎未见用户对价格条款做实质性博弈。建议增加 1-2 个 profile 专门设计 price negotiation 行为（"太贵了"、"别家更便宜"、"能不能打折"）。

2. **缺"中途态度反转"型** — 当前用户的对抗模式基本是单向的（要么越来越配合、要么越来越对抗），缺少"先接受后反悔"或"先怒后软"的转折。建议设计 1-2 个 profile 在 Layer 3/4 加入态度反转。

3. **D12（wifi_L3）需重写 instructions** — 目前 1-turn 结束无法展示多层对抗，应降低 Layer 2 的触发敏感度，让对话至少走到 Layer 3 才爆发。

### User Model 层面

4. **指导 user model 使用 [interrupt] / [silence]** — 在 task_instructions 中显式加入指导：什么场景下输出 `[interrupt]`（打断客服时）、`[silence]`（沉默/犹豫时）。

5. **减少"I need to run this by X"的使用频率** — 这是 gemma-4-31b-it 的默认推脱模式，跨 profile 趋同。可以在某些 profile 的 Layer 4 中显式指定不同退场话术。

### 工具层面

6. **digest.py 的"其他"类别仍占 18.9%** — 修复英文支持后改善显著（65.2%→18.9%），但"其他"中的很多 utterance 实际是间接拒绝/委婉推脱。后续可补充 "i think it's better if..."、"i'll handle this through..." 等模式。

### Benchmark 设计层面

7. **考虑增加中文对话** — 当前 24 条全是英文，但 benchmark 设计文档和 prompt 模板中有中英混合的痕迹（如 D9 用户说了句中文"你们这个活动真的假的"混在英文对话中）。建议明确语言策略：要么全英要么全中，混用会引入噪音。
