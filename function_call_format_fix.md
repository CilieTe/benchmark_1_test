# function-call 格式修复

## 问题

llmparty `to_segments()` 解析 `<function-call>` 时校验失败，segment type 被标记为 `error_tool_call`，导致数据验证不通过。

## 根因

llmparty `dialog.py:490` 用 `split(":", 1)` 然后 `json.loads()` 解析 function-call 内容，期望格式：

```
function_name: {"param": "value"}
```

但有两处产出了两行格式（换行分隔函数名和 JSON）：

```
function_name
{"param": "value"}
```

此时 `split(":", 1)` 会在 JSON 内部的第一个 `:` 处断开（如 `"fund_category":`），导致：
- `splits[0]` = `function_name\n{"fund_category"`  
- `splits[1]` = ` "混合基金"}` 
- `json.loads()` 失败 → `parse_failed = True` → segment type = `error_tool_call`

两行格式出现在：

| 位置 | 来源 |
|------|------|
| assistant 消息中的实际 function-call | 模型输出（受 system prompt 示例影响） |
| system 消息中的输出格式示例 | `format_functions_for_prompt()` 旧版产出的示例 |

## 修复

### 数据修复（`dialog_results_v10_0527.jsonl`）

正则匹配两行格式，转为单行：

```python
pattern = r'<function-call>\s*\n\s*(\w+)\s*\n\s*(\{[\s\S]*?\})\s*\n\s*</function-call>'
replacement = r'<function-call>\1: \2</function-call>'
```

- 第一轮：修复 assistant 消息中的 47 处
- 第二轮：修复 system 消息示例中的 21 处
- 共计 68 处

### 源头修复（`run_dialogs.py:341`）

`format_functions_for_prompt()` 的示例格式已改为单行：

```python
# 旧（两行）
lines.append('get_fund_info')
lines.append('{"fund_category": "混合基金"}')

# 新（单行）
lines.append('get_fund_info: {"fund_category": "混合基金"}')
```

### 兼容保留

`parse_function_call()`（`run_dialogs.py:347-364`）仍兼容两种格式，以防模型产出两行。

## 验证

```bash
# 检查是否还有两行格式残留
grep -Pzo '<function-call>\s*\n\s*\w+\s*\n' dialog_results_v10_0527.jsonl
# 预期：0 匹配
```
