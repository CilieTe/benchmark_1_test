---
name: benchmark-dialogs
description: Marketing cold-call benchmark — generate profiles (Agent-driven, no external API), run two-model dialog simulations, manage profiles/prompts, check function-call quality. Trigger on: run_dialogs, benchmark dialog, all_profiles, generate profiles, v9 profiles, function-call quality, intent_level, convertibility_ceiling.
---

# benchmark-dialogs

营销外呼 / 催收 benchmark 构建与运行。覆盖 profile 生成、对话模拟、prompt 精修、FC 互换检查四类任务。支持 TM（Telemarketing 营销）和 CL（Collection 催收）两个领域。

## 路由（必须最先执行）

根据用户输入判断**领域**和**任务类型**：

### 领域判断

| 关键词 | 领域 |
|--------|------|
| 催收、collection、M1、M3、debt、loan overdue、逾期 | **CL**（催收） |
| 营销、marketing、外呼、cold-call、TM、保险、信用卡、贷款营销 | **TM**（营销） |
| 未明确 | 用 AskUserQuestion 询问 |

### 任务判断

| 关键词 | 功能 |
|--------|------|
| 生成 profile、generate profiles、写画像、重新生成 | → [[#profile-生成]] |
| run_dialogs、run benchmark、simulate dialog、跑对话 | → [[#对话模拟]] |
| refine prompt、改写 prompt、更新话术 | → [[#prompt-精修]] |
| function-call quality、互换成功率、FC format、衔接词 | → [[#fc-互换检查]] |
| clean-dialogs、清洗对话、去短对话、合并 call logs | → [[#自动生成路线图]] |
| build-pools、构建人设池、噪声池、行为池 | → [[#自动生成路线图]] |
| derive-guide、生成 gen.md、生成领域规范 | → [[#自动生成路线图]] |
| generate-spec、生成 spec、profile_spec | → [[#自动生成路线图]] |
| generate-profiles、生成 runtime profiles、profiles_runtime | → [[#自动生成路线图]] |

如果用户输入**没有匹配到上述任何关键词**（例如只输入 `/benchmark-dialogs` 或 "benchmark"），必须先用 AskUserQuestion 问清楚要执行哪个功能：

- 问题：「你要执行哪个功能？」选项：Profile 生成 / 对话模拟 / Prompt 精修 / FC 互换检查

确定领域和功能后，跳转到对应模块，进入参数确认阶段。

## 自动生成路线图

本 skill 的长期目标是把 benchmark 构造升级为可复用自动流水线。当前仓库版以 `DESIGN.md` 为准，分阶段落地：

```text
clean-dialogs
-> build-pools
-> derive-guide
-> generate-spec
-> generate-profiles
-> run-dialogs
```

### 已确认的设计约束

- 使用一个 skill：`benchmark-dialogs`，不要拆成多个 benchmark skill。
- 目标用户优先是团队同事；第一版可以依赖 Chatdemo。
- 池子按 domain 隔离，例如 TM、CL、CX；同一 domain 内不按国家、prompt、business 继续拆分。
- `build-pools` 输入是 cleaned dialogs JSONL + domain；`clean-dialogs` 是可选前置工具。
- `build-pools` 输出四类文件：
  - `stage1_per_conversation.jsonl`
  - `noise_pool.jsonl`
  - `behavior_pool.jsonl`
  - `stage2_typical_personas.jsonl`
- `noise_pool` 和 `behavior_pool` 都是片段级，一条片段一行，必须保留 `context`。
- `behavior_pool` 额外保留 `why_useful`。
- build 阶段不定义 `difficulty`；`difficulty` 到 spec/profile 阶段再决定。
- 固定 difficulty 语义：
  - `L1`：无主动对抗。
  - `L2`：对抗可以消解；即使模型没有良好应对，也会在 1-2 轮内快速消气，其中约 70% 一轮内消解，直到下一个对抗动作。
  - `L3`：对抗不主动消解；除非模型有效应对，否则持续对抗。
- `generate-spec` 使用 `user_starting_position`，不再用旧字段 `intent_level` 作为新标准。
- `profile_spec` 最小字段契约：`profile_id`、`prompt_id`、`difficulty`、`identity`、`action_design`；其他字段原样透传。
- spec 和 profile 一对一。
- profile 先生成领域原生 native profile，再由 adapter 转 runtime profile。
- `gen.md` 必须自动生成，但需要 human confirm 后再用于 profile generation。

详细 schema、产物目录和后续 CLI 设计见 `skills/benchmark-dialogs/DESIGN.md`。

## 共享参考（只读）

### 关键文件 — TM（营销）

| 文件 | 路径 | 用途 |
|------|------|------|
| 精修后 prompts | `benchmark_1_test/marketing_prompts_v2.jsonl` | 37 条营销 prompt |
| Profile 生成规范 | `benchmark_1_test/gen_v2.md` | Step 3 组装规则 + 质量检查清单 |
| Profile 设计表 A | `benchmark_1_test/demo_profile_design_1.md` | 当前 batch（24 条，8 prompt × 3 profile） |
| Profile 设计表 B | `benchmark_1_test/demo_profile_design_2.md` | 备用新版设计 |
| 行为能力参考 | `benchmark_1_test/用户能力手册.md` | — |
| 真实用户语料 | `benchmark_1_test/true_user_data.md` | — |
| 对抗行为编码 | `benchmark_1_test/# Benchmark 用户不配合行为分析.md` | — |
| Prompt 精修规格 | `benchmark_1_test/specs/prompt_refine_spec.md` | — |

### 关键文件 — CL（催收）

| 文件 | 路径 | 用途 |
|------|------|------|
| Prompts | `benchmark_1_test/cl/m1_m3_prompts.jsonl` | 2 条催收 prompt（M1 墨西哥 + M3 印尼） |
| 实例化 Prompts（只读） | `benchmark_1_test/cl/m1_m3_instantiated_prompts_compress_format_v2.jsonl` | 含完整 system prompt + tools |
| Profile 生成规范 | `benchmark_1_test/cl/gen_v2_collection.md` | 催收版 profile 组装规则 |
| Profile 设计文档 | `benchmark_1_test/cl/m1_m3_profile_design.md` | 6 条 profile 设计（M1/M3 各 3 条） |
| 噪音语料池 | `dataset/debt_analysis/profiles/noise_pool.jsonl` | 285 条：pragmatic_noise / code_mixing / minimal_feedback / silence / asr_garbled |
| 证据语料池 | `dataset/debt_analysis/profiles/evidence_pool.jsonl` | 3280 条：text / difficulty / intent_level / resolution_style |
| Stage2 Personas | `benchmark_1_test/cl/stage2_typical_personas.jsonl` | 45 条真实催收对话画像 |

### 通用工具

| 文件 | 路径 | 用途 |
|------|------|------|
| Profile 生成脚本 | `workspace/scripts/generate_profiles_v2.py` | TM + CL 双领域通用 |
| 对话运行脚本 | `benchmark_1_test/run_dialogs.py` | 领域无关，读 profiles + prompts JSONL |
| FC 工具链 | `dataset/fc-continuer/` | parse → prep → apply |

### identity 占位符映射表 — TM

| prompt_id | 占位符变量 | identity 字段数 | 备注 |
|-----------|-----------|:---:|------|
| mp_01 | `{{user_id}}` | 1 | 字符串如 `"U88291"` |
| mp_02 | `{{customer_name}}` `{{last_four_digits}}` | 2 | `customer_name` 含称呼如 `"Ms. Zhang"` |
| mp_20 | `{{miles_balance}}` `{{miles_expiry_date}}` `{{membership_tier}}` `{{upgrade_seats_available}}` | 4 | — |
| mp_21 | `{{miles_balance}}` `{{miles_expiry_date}}` | 2 | — |
| mp_29 | `{{customer_name}}` `{{vehicle_model}}` `{{vehicle_short_name}}` `{{vehicle_age}}` `{{license_plate}}` `{{mileage}}` `{{registration_date}}` `{{inspection_deadline}}` `{{inspection_deadline_display}}` `{{contact_last_four}}` `{{slot_date_1}}` `{{slot_date_2}}` | 12 | — |
| mp_32 | `{{customer_name}}` `{{session_rate}}` | 2 | `session_rate` 不带 `$` |
| mp_36 | `{{current_date}}` | 1 | 如 `"2025-06-02"` |
| 其余 30 条 | 无 | 0 | `{}` |

mp_10、mp_14、mp_27 在旧版有占位符，v2 已 mock 掉，无需 identity。

### identity 占位符映射表 — CL

| prompt_id | 占位符变量 | identity 字段数 | 备注 |
|-----------|-----------|:---:|------|
| mx_loan_m1 | 无 | 0 | `{}`，身份已 mock 在 prompt 中（Carlos Hernández López） |
| id_loan_m3 | 无 | 0 | `{}`，身份已 mock 在 prompt 中（Budi Santoso） |

---

## profile 生成

**触发词**：生成 profile、generate profiles、写画像、重新生成 profiles

**工具**：`workspace/scripts/generate_profiles_v2.py`

**默认模型**：`openai:gpt-4.1-mini-2025-04-14`（chatdemo 后端，脚本内置常量 `CHATDEMO_MODEL`）

**耗时参考**：每条 profile ~2 分钟，8 并发 6 条约 3-5 分钟，24 条约 6-10 分钟。

### 参数确认（必须逐组 AskUserQuestion，不问完不执行）

根据当前领域（TM / CL）设置默认值。

**第一组（必问）：**

1. **设计文档**：用哪个设计表？
   - TM：`demo_profile_design_1`（24 条）/ `demo_profile_design_2`（备用）/ 自定义
   - CL：`benchmark_1_test/cl/m1_m3_profile_design.md`（6 条）/ 自定义

2. **Prompts 文件**：
   - TM 默认：`benchmark_1_test/marketing_prompts_v2.jsonl`
   - CL 默认：`benchmark_1_test/cl/m1_m3_prompts.jsonl`

3. **输出路径**：写入哪个文件？

4. **运行模式**：试跑还是全量？
   - 试跑 `--count 1 --workers 1`
   - 全量 `--workers N`

**第二组（第一组回答后继续，仅在全量时问）：**

5. **全量数量**：一共生成多少条？

6. **并发数**：`--workers` 多少？

7. **是否续跑**：从第几条开始？不续跑则从 0 开始。

### 执行

参数确认完毕后：

1. 如果脚本内置 `PROFILES` 列表与设计文档不一致，将设计文档中的 spec 导出为 JSON 数组（`--spec` 传入）。
2. 用确认后的参数拼接命令并执行。**不使用任何示例值或默认路径**。

```
python3 workspace/scripts/generate_profiles_v2.py \
    --domain {tm|cl} \
    --prompts {prompts路径} \
    --spec {spec路径} \
    --count {数量} --workers {并发数} \
    --start {起始条数} \
    -o {输出路径}
```

`--domain` 必传，决定加载哪套参考文件和 system prompt 模板。

---

## 对话模拟

**触发词**：run_dialogs、run benchmark、simulate dialog、跑对话

**链路**：`run_dialogs.py` 直接读取 profiles JSONL + prompts JSONL，两模型多轮对话。无需 pre-build 步骤。

### 参数确认（必须逐组 AskUserQuestion，不问完不执行）

根据当前领域（TM / CL）设置默认值。

**第一组（必问）：**

1. **Profile 文件**：用哪个 profile JSONL？
   - TM 默认：`benchmark_1_test/outputs/profiles_v2.jsonl`
   - CL 默认：`benchmark_1_test/cl/m1_m3_profiles.jsonl`

2. **Prompts 文件**：用哪个 prompts JSONL？
   - TM 默认：`benchmark_1_test/marketing_prompts_v2.jsonl`
   - CL 默认：`benchmark_1_test/cl/m1_m3_prompts.jsonl`

3. **语言**：
   - TM 默认：`en`；可选：`zh` / `en-SG`
   - CL 默认：`id`（M3 印尼语）或 `es-MX`（M1 西语），取决于 profile；可选：`en`

4. **对话数量**：要跑多少条？部分（指定数量）还是全部？

**第二组（第一组回答后继续）：**

5. **Assistant 模型**：哪个模型扮演外呼 AI？
   - 默认：`openai:gpt-4.1-mini-2025-04-14`

6. **User 模型**：哪个模型扮演用户？
   - 默认：`open_router:google/gemma-4-31b-it`

7. **Backend**：
   - 默认：`chatdemo`

每个参数都要用 AskUserQuestion 确认，选项里把默认值放在第一位并标注 "(Recommended)"。用户可以直接回车确认默认值。

### 执行

直接运行，无需 build 步骤：

```
python benchmark_1_test/run_dialogs.py \
    --backend {backend} --num {数量} --lang {语言} \
    --model {assistant模型} \
    --user-model {user模型}
```

---

## prompt 精修

**触发词**：refine prompt、改写 prompt、更新营销话术

**工具**：无脚本，Agent 直接按规格改写 JSONL。

**规格文档**：`benchmark_1_test/specs/prompt_refine_spec.md`

**改写规则**：rules 追加 3 条（busy→callback、FAQ-first no fabrication、FAQ-listed benefits only）、hints 统一为两条 HINT 格式置于末尾、main flow 所有首次拒绝分支插入一次挽回再结束。占位符和 function 定义不动。

### 参数确认（必须逐组 AskUserQuestion，不问完不执行）

1. **输入文件**：要精修哪个 prompts JSONL？

2. **输出文件**：精修后写到哪个路径？

3. **精修规格**：用哪个规格文档？（通常为 `benchmark_1_test/specs/prompt_refine_spec.md`）

4. **精修范围**：全量还是指定 prompt_id 子集？

参数确认后，读取输入 → 按规格逐条改写 → 写入输出文件。

---

## FC 互换检查

**触发词**：check function-call quality、互换成功率、FC format、衔接词

**工具链**：`dataset/fc-continuer/` 下的 `parse_fc_compare.py` → `prep_eval_sheet.py` → `apply_prefix_scores.py`

### 参数确认（必须逐组 AskUserQuestion，不问完不执行）

**第一组（必问）：**

1. **输入 JSONL**：要检查哪个对话结果文件？

2. **需要筛选 run_keys 吗？**
   - 不筛选（全部跑）
   - 指定 run_keys（列出）

3. **输出 CSV 路径**：对比表 CSV 写到哪？

4. **只看 content 还是保留 metrics？**
   - `--content-only`（纯输出，简洁）
   - 保留 metrics（完整）

**第二组（仅当需要写入人工评分时问）：**

5. **是否需要 apply scores 回写 JSONL？**如果需要，人工评分文件路径是什么？

### 执行

参数确认后按链路执行：

```
# Step 1: parse（JSONL → CSV 对比表）
python dataset/fc-continuer/parse_fc_compare.py \
    {输入JSONL} {--run-keys筛选} {--content-only} \
    -o {CSV路径}

# Step 2: prep（对比 CSV → 评估表，自动标 -1）
python dataset/fc-continuer/prep_eval_sheet.py \
    {CSV路径} \
    -o {评估表路径}

# Step 3: apply（仅当需要，将评分写入 JSONL）
python dataset/fc-continuer/apply_prefix_scores.py \
    {输入JSONL} \
    --scores {评分CSV}
```

### 评分标准

| 分数 | 含义 |
|:---:|------|
| -1 | 无 function-call / 无衔接词 / FC 格式错误（自动标出） |
| 0 | FC 参数提取错误 |
| 1 | FC 正确，衔接词存在但表现不佳 |
| 2 | FC 正确，衔接词表现良好 |

---

## 仓库化复用与发布

当用户要求“把 benchmark skill 放到 GitHub / push 一个可复用 skill / 发布自动化 skill”时，沿用本 skill 名称 `benchmark-dialogs`，不要另起其他 benchmark skill 名字。

### 仓库内目录

标准目录：

```text
skills/benchmark-dialogs/
  SKILL.md
  README.md
  install.sh
```

`SKILL.md` 是 agent 读取的主文件；`README.md` 面向人类说明安装与使用；`install.sh` 只做本地复制，不安装依赖、不写密钥、不修改系统配置。

### 安装约定

从 `benchmark_1_test` 仓库根目录执行：

```bash
bash skills/benchmark-dialogs/install.sh
```

安装脚本将文件复制到：

```text
~/.codex/skills/benchmark-dialogs/
```

如果还要同步到 Claude Code skills，由用户单独确认目标目录后再做，不默认写入。

### 发布前检查

发布到 GitHub 前：

1. 只 stage `skills/benchmark-dialogs/`，除非用户明确要求把 benchmark 数据也一起发布。
2. 检查 frontmatter 至少包含 `name: benchmark-dialogs` 和 `description:`。
3. 运行 `bash -n skills/benchmark-dialogs/install.sh`。
4. 运行一次安装脚本，确认 `~/.codex/skills/benchmark-dialogs/SKILL.md` 存在。
5. 查看 `git diff --cached --name-status`，确认没有混入数据产物、密钥、`.env`、缓存或 unrelated worktree 变化。
6. `git push` 前必须单独请求用户确认。

### JSONL 最小校验

对任何生成、精修、修复后的 JSONL，至少做结构校验：

```bash
python3 - <<'PY' path/to/file.jsonl
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if line.strip():
            json.loads(line)
print("valid jsonl")
PY
```

compress 数据还要抽查：

- `dialog` 是 list。
- `turn_index` 从 0 连续递增。
- `turn 0` 是 `system`。
- `id` 存在且唯一。
- `meta.chat_lang` 与目标语言一致。
- function-call 标签闭合，必要时有 function-response。
- 不在未获授权时清空 `review`、`metrics`、`evaluate`、`laep.remark`。

### 报告与交付

当用户要求产出 digest、matrix、card、release note 或 GitHub 说明时，报告至少包含：

- 文件范围与 record count。
- 领域、语言、prompt/business 覆盖。
- 难度、结局、对抗/摩擦类型覆盖。
- QC 状态、已修复记录、残留风险。
- 可复现命令。

报告更新优先局部处理，不无脑重写整篇。
