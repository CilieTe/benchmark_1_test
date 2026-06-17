# Marketing Benchmark 测试集设计思路

## 核心目标

构造以 **user input 为自变量** 的营销场景 benchmark，测试 Agent 在用户施加对抗/干扰时的应对能力。

## 三维正交架构

| 维度     | 定义                       | 覆盖                      |
| ------ | ------------------------ | ----------------------- |
| **业务** | 推销标的（理财、车险、电信、私厨…）       | 22 条呼出-推销 prompt        |
| **结局** | 对话退出分支（成交/拒绝/留存/中断）      | 每条 prompt 覆盖 3-4 种结局    |
| **动作** | 用户对抗行为（讨价还价/改口/质疑隐私/沉默…） | 从 user profile 人格模型自然浮现 |

三者全组合约 1000+ 种，实际策略：先保证 **业务×结局** 全覆盖（约 75 条），再叠加难度动作，质检后确保难度正态分布。

## User Profile 设计（见 gen.md）

- **动机驱动，非脚本驱动**：写用户的底层顾虑和反应模式，不写"客服说了 X 你做 Y"
- **4 层 task_instructions**：baseline 日常节奏 → 对抗触发 1~2 层（含反应频谱+持续时间上限） → 最终决策模式
- **behavioral_affordances**：行为风格声明（倾向做什么/不会做什么/硬边界）
- **behavior_examples**：碎片化口语短句，提供语言素材防表演腔
- **内部状态驱动回复**：每轮先生成内心状态（情绪/顾虑/冲动），再生成实际话语

## 难度来源

难度不从 task_instructions 预设动作，而是从 user profile 的人格深度中自然浮现——一个足够丰富的人格会在合适时机自己选出合适的对抗动作。

## Prompt 约束

- Prompt 不过度 refine，只确保无硬伤
- 仅保留呼出-推销（outbound sales），排除呼入服务和客诉
- 所有 benchmark 首版必须全量人工质检

## 数据来源

1. 日常数据构建表（主要）→ 22 条已筛选
2. 历史测试集 Task 926/1008（次要参考）
3. Botlab 线上 TM 数据（补充盲区）

## 当前交付文件

TM 分支已整理出 finished 版本，路径位于 `tm/finished/`：

| 文件 | 说明 |
| --- | --- |
| `benchmark_telemarketing_en.jsonl` | 英文版，48 条 |
| `benchmark_telemarketing_es-MX.jsonl` | 西语墨西哥版，24 条 |
| `benchmark_telemarketing_id.jsonl` | 印尼语版，24 条 |

英文版 metadata 已按 `tm/data/outputs/profiles_1.jsonl` 和
`tm/data/outputs/profiles_2.jsonl` 对齐：

- `id` 去掉语言后缀后匹配 `profile_id`。
- `prompt_id`、`business`、`ending_expected` 以 profile 文件为准。
- `prompt_category`、`prompt_scene` 按业务统一归一化。

finished 文件中的 `laep.remark` 已清空，保留 `laep.id`、`created_by` 和其他结构字段。
英文版还修复了 `edu_save_L1_en` 的 function-response JSON 尾逗号，以及
`ins_hlth_L2_en` 的代办授权闭环。
