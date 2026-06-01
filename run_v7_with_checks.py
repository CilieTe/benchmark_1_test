"""逐条运行 v7 profiles，每跑一条检查 function call 质量，有问题停下。"""
import json, sys, os

# Import run_dialogs internals
sys.path.insert(0, os.path.dirname(__file__))
from run_dialogs import (
    load_jsonl, parse_function_defs, run_dialog, build_backend_cfg,
)

PROFILES_PATH = "benchmark_1_test/data/all_profiles_v9_0527.jsonl"
PROMPTS_PATH = "benchmark_1_test/marketing_prompts.jsonl"
OUTPUT_PATH = "benchmark_1_test/data/dialog_results_v9_0527.jsonl"
ASSISTANT_MODEL = "open_router:qwen/qwen3.6-35b-a3b"
USER_MODEL = "open_router:google/gemma-4-31b-it"
BACKEND = "chatdemo"
LANG = "en"


def check_function_quality(result: dict, func_defs: list[dict]) -> list[str]:
    """返回问题列表，空列表 = 没问题。"""
    issues = []
    dialog = result["dialog"]
    profile_id = result["id"]
    expected_funcs = {f["name"] for f in func_defs}

    # 检查 1：function-response 是否都有对应的 function-call
    fc_turns = []
    fr_turns = []
    for t in dialog:
        tags = t.get("tags", [])
        if "function_call" in tags:
            fc_turns.append(t)
        if "function_response" in tags:
            fr_turns.append(t)

    if fr_turns and not fc_turns:
        issues.append("有 function_response 但没有 function_call")

    # 检查 2：function-call 格式是否被正确解析
    for t in fc_turns:
        content = t.get("content", "")
        if not content.strip():
            issues.append(f"turn {t['turn_index']}: function_call content 为空")
        elif "<function-call>" not in content:
            issues.append(f"turn {t['turn_index']}: function_call 缺少 XML 标签")

    # 检查 3：function-response 内容是否有效
    for t in fr_turns:
        content = t.get("content", "")
        if "function-response" not in content:
            issues.append(f"turn {t['turn_index']}: function_response 缺少 XML 标签")
        if '"status": "recorded"' not in content and '"status"' not in content:
            issues.append(f"turn {t['turn_index']}: function_response 可能缺少 status 字段")

    # 检查 4：function_response 的内容是否可解析为 JSON
    for t in fr_turns:
        content = t.get("content", "")
        # 尝试提取 JSON 部分
        try:
            import re
            m = re.search(r'\{[\s\S]*\}', content)
            if m:
                json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            issues.append(f"turn {t['turn_index']}: function_response JSON 解析失败")

    return issues


def main():
    profiles = load_jsonl(PROFILES_PATH)
    prompts = load_jsonl(PROMPTS_PATH)
    prompt_by_id = {p["id"]: p for p in prompts}

    # 选择 backend
    class Args: pass
    args = Args()
    args.backend = BACKEND
    args.api_base = None
    args.api_key = None
    backend_cfg = build_backend_cfg(args)

    print(f"后端: {backend_cfg['api_base']}")
    print(f"Assistant: {ASSISTANT_MODEL} | User: {USER_MODEL}")
    print(f"共 {len(profiles)} 条 profiles\n")

    results = []
    for i, profile in enumerate(profiles):
        pid = profile.get("prompt_id") or profile.get("id")
        prompt_record = prompt_by_id.get(pid)
        if not prompt_record:
            print(f"[{i+1}/{len(profiles)}] {profile['profile_id']} — 找不到 prompt {pid}，跳过")
            continue

        sys_prompt = prompt_record["prompt"]
        func_defs = parse_function_defs(prompt_record.get("function", ""))
        biz = profile.get("business", "unknown")
        diff = profile.get("difficulty", "")

        print(f"[{i+1}/{len(profiles)}] {profile['profile_id']} ({biz}, {diff})", flush=True)
        if func_defs:
            print(f"  functions: {[f['name'] for f in func_defs]}", flush=True)

        result = run_dialog(profile, sys_prompt, ASSISTANT_MODEL, USER_MODEL, func_defs, backend_cfg, lang=LANG)
        fc_count = sum(1 for t in result["dialog"] if "function_response" in t.get("tags", []))

        # 质检
        issues = check_function_quality(result, func_defs)
        if issues:
            print(f"  -> {len(result['dialog'])-1} turns, {fc_count} FC, {result['meta']['elapsed_s']}s")
            print(f"  ⚠️ 质量问题：", flush=True)
            for issue in issues:
                print(f"     - {issue}", flush=True)
            # 写入已跑结果
            results.append(result)
            with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
                for r in results:
                    out.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"\n已保存 {len(results)} 条到 {OUTPUT_PATH}")
            print("发现质量问题，停止。请检查后重新运行。")
            sys.exit(1)

        print(f"  -> {len(result['dialog'])-1} turns, {fc_count} FC, {result['meta']['elapsed_s']}s ✓", flush=True)
        results.append(result)

        # 逐条写入
        with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
            for r in results:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n全部 {len(results)} 条完成，无质量问题")
    print(f"保存到 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
