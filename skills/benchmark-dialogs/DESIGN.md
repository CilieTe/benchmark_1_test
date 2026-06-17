# benchmark-dialogs Design

This document defines the target design for turning `benchmark-dialogs` into a
team-usable benchmark generation skill.

The skill remains one package named `benchmark-dialogs`. Do not split profile
generation and dialog running into separate skills.

## Target Pipeline

```text
clean-dialogs
-> build-pools
-> derive-guide
-> generate-spec
-> generate-profiles
-> run-dialogs
```

Two entry modes are supported:

- Fast path: `spec + prompts + gen.md -> profiles -> dialogs`
- Full path: `raw/clean dialogs -> pools -> guide -> spec -> profiles -> dialogs`

First production target: team-internal use with Chatdemo. Public API portability
can be added later.

## Domain Boundary

Pools and generated guides are isolated by domain, such as `tm`, `cl`, and `cx`.
Do not further split pools by country, prompt ID, business, or scene unless a
future task explicitly requires it.

Within one domain, prompts are treated as transferable: user behavior from one
country or business can inform another prompt in the same domain.

## Commands

Planned CLI surface:

```bash
benchmark-dialogs clean-dialogs \
  --input raw.jsonl \
  --output clean/dialogs.jsonl

benchmark-dialogs build-pools \
  --domain cl \
  --dialogs clean/dialogs.jsonl \
  --output profiles/

benchmark-dialogs derive-guide \
  --domain cl \
  --prompts prompts.jsonl \
  --stage2 profiles/stage2_typical_personas.jsonl \
  --noise-pool profiles/noise_pool.jsonl \
  --behavior-pool profiles/behavior_pool.jsonl \
  --output domain_guides/cl/

benchmark-dialogs generate-spec \
  --domain cl \
  --prompts prompts.jsonl \
  --stage2 profiles/stage2_typical_personas.jsonl \
  --noise-pool profiles/noise_pool.jsonl \
  --behavior-pool profiles/behavior_pool.jsonl \
  --guide domain_guides/cl/gen.md \
  --output specs/profile_spec.json

benchmark-dialogs generate-profiles \
  --domain cl \
  --spec specs/profile_spec.json \
  --prompts prompts.jsonl \
  --stage2 profiles/stage2_typical_personas.jsonl \
  --noise-pool profiles/noise_pool.jsonl \
  --behavior-pool profiles/behavior_pool.jsonl \
  --guide domain_guides/cl/gen.md \
  --output profiles/generated/

benchmark-dialogs run-dialogs \
  --profiles profiles/generated/profiles_runtime.jsonl \
  --prompts prompts.jsonl \
  --output dialogs/dialog_results.jsonl
```

These commands are a design contract first. Implement them incrementally.

## clean-dialogs

Purpose: optional preprocessing from raw request logs to cleaned dialogs.

Confirmed cleaning rules:

- Merge records with the same dialog/call ID and keep only the longest record,
  because every call may be logged repeatedly.
- Remove ultra-short dialogs with `turn_count <= 6`.

Inputs:

- Raw request logs JSONL.
- ID field mapping if the file does not use the default dialog ID field.

Output:

- Clean dialogs JSONL.

This step is optional. Users may provide already-cleaned dialogs directly, such
as `request_logs_dialog_schema_a_turn_gt6.jsonl`.

## build-pools

Purpose: use LLM full-dataset reading to construct domain-specific pools from
clean dialogs.

Inputs:

- Clean dialogs JSONL.
- Domain name.

No `gen.md` is required for this step.

Outputs:

```text
stage1_per_conversation.jsonl
noise_pool.jsonl
behavior_pool.jsonl
stage2_typical_personas.jsonl
```

### stage1_per_conversation.jsonl

One line per clean dialog.

Minimum schema:

```json
{
  "source_dialog_id": "...",
  "persona_summary": "...",
  "user_starting_position": "...",
  "communication_style": "...",
  "emotional_pattern": "...",
  "decision_pattern": "...",
  "notable_behaviors": [],
  "representative_quotes": []
}
```

Do not assign `difficulty` in build-pools.

### noise_pool.jsonl

Fragment-level. One noise expression per line.

Minimum schema:

```json
{
  "source_dialog_id": "...",
  "turn_index": 12,
  "noise_type": "...",
  "text": "...",
  "context": "..."
}
```

`context` is required. A noise fragment without context is often impossible to
interpret.

### behavior_pool.jsonl

Fragment-level. One user behavior expression per line.

Minimum schema:

```json
{
  "source_dialog_id": "...",
  "turn_index": 8,
  "behavior_type": "...",
  "text": "...",
  "context": "...",
  "why_useful": "..."
}
```

`behavior_pool` replaces the older `evidence_pool` name. The pool stores real
user behavior language, not evidence labels.

### stage2_typical_personas.jsonl

Typical persona pool derived from stage1. The LLM should ensure coverage of
domain-relevant user starting positions and behavior combinations.

Minimum schema:

```json
{
  "persona_id": "...",
  "user_starting_position": "...",
  "communication_style": "...",
  "decision_pattern": "...",
  "behavior_mix": [],
  "source_dialog_ids": [],
  "coverage_note": "..."
}
```

Persona count is selected from data scale, but must be no smaller than the
minimum needed for coverage. Users may override with `--num-personas`.

## derive-guide

Purpose: automatically derive a domain `gen.md` from prompts and pools. The
guide must be human-confirmed before profile generation.

Inputs:

- Domain name.
- Prompts JSONL.
- `stage2_typical_personas.jsonl`.
- `noise_pool.jsonl`.
- `behavior_pool.jsonl`.
- Optional user notes about business goals or hard red lines.

Do not generate `gen.md` in one step. Derive and save intermediate analyses:

```text
domain_guides/{domain}/
  prompt_analysis.md
  behavior_taxonomy.md
  noise_rules.md
  dimension_design.md
  gen.md
  guide_qc.md
```

`gen.md` should use this stable structure:

```text
# Domain Guide: {domain}

## 1. Benchmark Objective
## 2. Prompt Structure
## 3. User Starting Position
## 4. Convertibility Ceiling
## 5. Difficulty Semantics
## 6. Behavior Taxonomy
## 7. Noise and Friction Rules
## 8. Profile Assembly Rules
## 9. Identity Handling
## 10. Output Profile Requirements
## 11. Quality Checklist
## 12. Common Failure Modes
```

Difficulty semantics are fixed and must be copied into every guide:

- `L1`: no proactive adversarial behavior.
- `L2`: adversarial behavior is self-resolving. Even without good model
  handling, the user cools down within one or two turns; about 70 percent of L2
  adversarial actions should resolve after one turn until the next adversarial
  action.
- `L3`: adversarial behavior does not self-resolve. Unless the model responds
  effectively, the user continues adversarial behavior.

## generate-spec

Purpose: generate profile specs from prompts, stage2 personas, pools, and a
confirmed guide.

Inputs:

- Prompts JSONL.
- `stage2_typical_personas.jsonl`.
- `behavior_pool.jsonl`.
- `noise_pool.jsonl`.
- Domain name.
- Confirmed `gen.md`.
- Optional user-specified `user_starting_position` definitions.
- Optional target count or prompt scope.

Output:

```text
profile_spec.json
profile_spec_qc.md
profile_spec_failed.json
coverage_matrix.csv
```

Spec is one-to-one with profile generation: one spec row produces one profile.

Minimum spec contract:

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

Required fields:

- `profile_id`
- `prompt_id`
- `difficulty`
- `identity`
- behavior design field, default `action_design`

Other fields are passed through unchanged. Do not force one universal spec
schema beyond the minimum contract.

New specs should use `user_starting_position`; old `intent_level` files may be
accepted by adapters for backward compatibility.

Default coverage rules:

- `convertibility_ceiling` must be fully covered.
- `user_starting_position` major categories should be covered.
- `behavior_type` should be covered and reasonably balanced.
- `difficulty` need not be fully covered for every prompt, but the whole file
  should have reasonable distribution.
- `L1` rows do not proactively adversarially challenge the agent.
- `L2` and `L3` rows must contain explicit adversarial behavior.
- Per-prompt row count may be user-specified; otherwise derive from coverage.

## generate-profiles

Purpose: expand specs into profiles, then adapt them to a runtime schema.

Inputs:

- `profile_spec.json`.
- Prompts JSONL.
- `stage2_typical_personas.jsonl`.
- `behavior_pool.jsonl`.
- `noise_pool.jsonl`.
- Confirmed `gen.md`.

Outputs:

```text
profiles_native.jsonl
profiles_runtime.jsonl
failed_profiles.jsonl
repair_manifest.json
```

Native profile schema may differ by domain. The adapter must produce a runtime
profile with this minimum shape:

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

`identity` handling:

- `{}` means the prompt has no variables or the prompt already mocks identity.
- `{ "field": true }` means the generator should fill a realistic value.
- Concrete values should be preserved.
- Placeholder mismatch is a validation failure.

Auto repair should run two to three rounds and produce failed files rather than
silently dropping records.

Failure checks:

- JSON parse failure.
- Missing minimum fields.
- Identity placeholder missing or extra.
- `L1` contains proactive adversarial behavior.
- `L2` or `L3` has no adversarial behavior.
- `L2` or `L3` violates the difficulty semantics.
- Profile contradicts `action_design`.
- Language does not match the target language.
- Profile is scripted, such as "when the agent says X, say Y".

## run-dialogs

Purpose: run two-model simulations from runtime profiles and prompts.

First implementation may wrap the existing `run_dialogs.py`. Domain-specific
profile schemas should not be passed directly to the runner; use
`profiles_runtime.jsonl`.

## Implementation Order

Recommended implementation order:

1. `DESIGN.md`
2. `validate_spec.py`
3. `validate_runtime_profiles.py`
4. `clean_dialogs.py`
5. `derive_guide.py` framework with intermediate output files
6. LLM calls and auto-repair loops
7. `generate_spec.py`
8. `generate_profiles.py`
9. runner wrapper

Each step should be usable independently and should write explicit output files.
