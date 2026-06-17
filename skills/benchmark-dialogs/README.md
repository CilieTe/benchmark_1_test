# benchmark-dialogs

Reusable Codex skill for the `benchmark_1_test` benchmark workflow.

It keeps the existing `benchmark-dialogs` behavior and makes it publishable from
this repository:

- automated benchmark generation design
- clean dialogs, build pools, derive guide, generate spec
- profile generation
- two-model dialog simulation with `run_dialogs.py`
- prompt refinement
- function-call quality checks
- JSONL QC and release packaging

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

## Runnable Tools

The automatic pipeline is being implemented incrementally under
`skills/benchmark-dialogs/tools/`:

- `clean_dialogs.py`: raw request logs to cleaned dialogs.
- `build_pools.py`: cleaned dialogs to stage1, noise, behavior, and stage2 pools.
- `derive_guide.py`: prompts and pools to a domain `gen.md`.
- `generate_spec.py`: prompts, pools, and guide to `profile_spec.json`.

Each tool can be run directly with `python3` and supports `--help`.

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
