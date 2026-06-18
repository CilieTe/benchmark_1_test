# CL Pipeline Smoke

This directory groups the CL smoke pipeline artifacts.

## Layout

- `inputs/`: source CL prompt/spec/dialog inputs.
- `pools/`: build-pools outputs from the 10-dialog smoke run plus full rule-based noise extraction.
- `noise_event_pool/`: rule-based all-type noise event candidate pool and self-audit.
- `guide/`: derive-guide outputs, including the routing `gen.md`.
- `dialogs/`: dialog runner smoke outputs.

## Notes

- `pools/stage1_per_conversation.jsonl` has 10 successful rows and `stage1_failed.jsonl` has 0 rows.
- `pools/noise_pool_typical.jsonl` is balanced to 20 rows per surface noise type.
- `noise_event_pool/noise_event_pool_all_types.jsonl` is candidate-only; see `noise_event_pool_self_audit.md` before using it as benchmark evidence.
- `guide/gen.md` is a thin routing entry point. Detailed guide content lives in the companion Markdown files in `guide/`.
