#!/usr/bin/env python3
"""将精修后的 prompt 文本写入 JSONL，保留原始 id/category/scene/function 字段。"""
import json, sys

orig = {}
with open(sys.argv[1], encoding='utf-8') as f:
    for line in f:
        r = json.loads(line.strip())
        orig[r['id']] = r

refined = {}
with open(sys.argv[2], encoding='utf-8') as f:
    for line in f:
        r = json.loads(line.strip())
        refined[r['id']] = r['prompt']

with open(sys.argv[3], 'w', encoding='utf-8') as out:
    for pid, r in orig.items():
        if pid in refined:
            r = dict(r)
            r['prompt'] = refined[pid]
        out.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f"Wrote {len(orig)} records -> {sys.argv[3]}, {len(refined)} refined")
