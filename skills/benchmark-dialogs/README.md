# benchmark-dialogs

`benchmark-dialogs` 是 `benchmark_1_test` 的可复用 benchmark 自动化 skill。
它覆盖从真实对话清洗、池子构建、领域规范生成、profile spec 生成、runtime
profile 生成，到两模型对话模拟的完整链路，同时保留旧的手工 profile 生成、
prompt refinement、function-call quality 检查和 JSONL QC 工作流。

当前新版主链路是：

```text
clean-dialogs
-> build-pools
-> derive-guide
-> generate-spec
-> generate-profiles
-> run-dialogs
```

其中 `generate-profiles -> run-dialogs` 已完成最小 smoke test：
`profile_spec.json` 可以生成 `profiles_native.jsonl` 和
`profiles_runtime.jsonl`，后者可以直接交给 `run_dialogs.py` 跑出 compress
dialog JSONL。

## Install

From the `benchmark_1_test` repository root:

```bash
bash skills/benchmark-dialogs/install.sh
```

This copies the skill to:

```text
~/.codex/skills/benchmark-dialogs/
```

Installed files:

- `SKILL.md`
- `README.md`
- `DESIGN.md`
- `tools/`

Restart Codex or reload skills if the runtime does not pick up newly installed
skills automatically.

## Use

Examples:

- `use benchmark-dialogs to run a TM benchmark`
- `用 benchmark-dialogs 生成 CL profiles`
- `用 benchmark-dialogs 检查 function-call quality`
- `用 benchmark-dialogs 打包一个 GitHub 可复用 skill`

The skill does not store API keys and does not install dependencies.

## Full Pipeline

### 1. clean-dialogs

用途：把原始请求日志、线上 call logs 或混杂 JSONL 清洗成后续工具可消费的
dialog JSONL。

输入：

- 原始 dialogs / call logs JSONL
- domain，例如 `tm`、`cl`、`cx`

输出：

- cleaned dialogs JSONL

成功标准：

- 每行是合法 JSON。
- `dialog` 结构稳定。
- 短对话、坏 schema、明显无效记录被过滤或写入 sidecar failed 文件。

### 2. build-pools

用途：从 cleaned dialogs 里抽取 benchmark 构造所需的真实行为素材。

输入：

- cleaned dialogs JSONL
- domain

输出目录通常包含：

- `stage1_per_conversation.jsonl`
- `noise_pool.jsonl`
- `behavior_pool.jsonl`
- `stage2_typical_personas.jsonl`
- manifest / QC sidecar

关键约束：

- build 阶段不定义 `difficulty`。
- `noise_pool` 和 `behavior_pool` 都是片段级，一条片段一行。
- `behavior_pool` 保留 `context` 和 `why_useful`，方便 profile 生成时追溯。

### 3. derive-guide

用途：根据 prompts、stage2 personas、behavior/noise pools 自动生成当前 domain
的 `gen.md`，也就是 profile 生成规范。

输入：

- Prompts JSONL
- `stage2_typical_personas.jsonl`
- `behavior_pool.jsonl`
- `noise_pool.jsonl`
- domain

输出：

- `gen.md`
- `derive_guide_manifest.json`

注意：`gen.md` 应先人工确认，再进入 `generate-spec` / `generate-profiles`。
这是控制 benchmark 口径的关键文件。

### 4. generate-spec

用途：把 prompts、池子和确认后的 `gen.md` 转成一行一个 profile 设计的
`profile_spec.json`。

输入：

- Prompts JSONL
- `stage2_typical_personas.jsonl`
- `behavior_pool.jsonl`
- `noise_pool.jsonl`
- confirmed `gen.md`

输出：

- `profile_spec.json`
- `profile_spec_failed.json`
- `coverage_matrix.csv`
- `profile_spec_qc.md`
- `generate_spec_manifest.json`

最小 spec contract：

```json
{
  "profile_id": "...",
  "prompt_id": "...",
  "business": "...",
  "difficulty": "L1",
  "user_starting_position": "...",
  "convertibility_ceiling": "...",
  "identity": {},
  "resolution_style": "...",
  "action_design": "..."
}
```

关键约束：

- `profile_spec` 和 profile 一对一。
- 新字段使用 `user_starting_position`，旧 `intent_level` 只作为兼容输入。
- `identity` 必须和 prompt placeholders 对齐。
- `L1` 无主动对抗；`L2` 对抗可自消解；`L3` 对抗不主动消解。

### 5. generate-profiles

用途：把 `profile_spec.json` 扩展成领域原生 native profile，再转换成 runner
可消费的 runtime profile。

输入：

- `profile_spec.json`
- Prompts JSONL
- `stage2_typical_personas.jsonl`
- `behavior_pool.jsonl`
- `noise_pool.jsonl`
- confirmed `gen.md`

输出：

- `profiles_native.jsonl`
- `profiles_runtime.jsonl`
- `failed_profiles.jsonl`
- `repair_manifest.json`

runtime profile 最小 contract：

```json
{
  "profile_id": "...",
  "prompt_id": "...",
  "identity": {},
  "persona": "...",
  "situation": "...",
  "task_instructions": [],
  "behavioral_affordances": [],
  "behavior_examples": [],
  "ending_expected": "...",
  "meta": {
    "domain": "...",
    "difficulty": "...",
    "user_starting_position": "...",
    "convertibility_ceiling": "...",
    "resolution_style": "..."
  }
}
```

本地校验会检查：

- JSON parse failure
- minimum fields
- prompt identity placeholder mismatch
- L1/L2/L3 difficulty 语义
- scripted profile，例如 `when the agent says X, say Y`
- `action_design` 是否被 profile 吸收

示例：

```bash
python3 skills/benchmark-dialogs/tools/generate_profiles.py \
  --domain cl \
  --spec demo/m1_m3_profile_spec_24.json \
  --prompts demo/m1_m3_prompts_from_md_no_prompt_card.jsonl \
  --stage2 ../dataset/debt_analysis/profiles/stage2_typical_personas.jsonl \
  --noise-pool ../dataset/debt_analysis/profiles/noise_pool.jsonl \
  --behavior-pool ../dataset/debt_analysis/profiles/noise_pool.jsonl \
  --guide cl/gen_v2_collection.md \
  --output /tmp/generated_profiles \
  --count 1 \
  --workers 1 \
  --lang es-MX
```

先做 contract 检查、不调用模型：

```bash
python3 skills/benchmark-dialogs/tools/generate_profiles.py \
  --domain cl \
  --spec demo/m1_m3_profile_spec_24.json \
  --prompts demo/m1_m3_prompts_from_md_no_prompt_card.jsonl \
  --stage2 ../dataset/debt_analysis/profiles/stage2_typical_personas.jsonl \
  --noise-pool ../dataset/debt_analysis/profiles/noise_pool.jsonl \
  --behavior-pool ../dataset/debt_analysis/profiles/noise_pool.jsonl \
  --guide cl/gen_v2_collection.md \
  --output /tmp/generated_profiles_validate \
  --count 1 \
  --validate-only
```

### 6. run-dialogs

用途：使用 assistant model 和 user model 基于 `profiles_runtime.jsonl` 跑多轮
dialog simulation，输出 compress JSONL。

输入：

- `profiles_runtime.jsonl`
- Prompts JSONL
- assistant model
- user model
- backend
- language

输出：

- dialog results JSONL

示例：

```bash
python3 run_dialogs.py \
  --backend chatdemo \
  --profiles /tmp/generated_profiles/profiles_runtime.jsonl \
  --prompts demo/m1_m3_prompts_from_md_no_prompt_card.jsonl \
  --num 1 \
  --workers 1 \
  --lang es-MX \
  --output /tmp/dialog_results.jsonl \
  --model openai:gpt-4.1-mini-2025-04-14 \
  --user-model open_router:qwen/qwen3.6-35b-a3b
```

`run_dialogs.py` 当前支持：

- `zh`
- `en`
- `en-SG`
- `es-MX`
- `id`

注意：如果 prompt 本身写死了语言，例如 system prompt 内部要求
`Speak English only`，后追加的 `--lang es-MX` 语言指令可能无法完全覆盖原
prompt。正式多语言数据应使用对应语言的 prompt 文件。

## Runnable Tools

The automatic pipeline is being implemented incrementally under
`skills/benchmark-dialogs/tools/`:

- `clean_dialogs.py`: raw request logs to cleaned dialogs.
- `build_pools.py`: cleaned dialogs to stage1, noise, behavior, and stage2 pools.
- `derive_guide.py`: prompts and pools to a domain `gen.md`.
- `generate_spec.py`: prompts, pools, and guide to `profile_spec.json`.
- `generate_profiles.py`: `profile_spec.json` to `profiles_native.jsonl` and
  `profiles_runtime.jsonl`.

Each tool can be run directly with `python3` and supports `--help`.

## Current Status

已跑通的最小闭环：

```text
demo/m1_m3_profile_spec_24.json
-> generate_profiles.py --count 1
-> profiles_native.jsonl
-> profiles_runtime.jsonl
-> run_dialogs.py --num 1
-> dialog_results.jsonl
```

验证结果：

- `generate_profiles.py --validate-only --count 1` 通过。
- `generate_profiles.py --count 1` 通过，`valid_profiles=1`、
  `failed_profiles=0`。
- `run_dialogs.py --num 1` 通过，输出 1 条 compress dialog，4 turns，0 FC。

尚未声明为完成的部分：

- 从原始大数据全量自动跑到最终 dialogs 的大规模批处理。
- `gen.md` 的人工确认流程仍需保留。
- prompt 语言和 `--lang` 必须一致，否则可能出现系统 prompt 与 runtime
  语言指令冲突。

## Design

The next-generation workflow is documented in `DESIGN.md`:

```text
clean-dialogs
-> build-pools
-> derive-guide
-> generate-spec
-> generate-profiles
-> run-dialogs
```

The current implementation keeps existing manual workflows usable while the
automatic generation CLI is added incrementally.
