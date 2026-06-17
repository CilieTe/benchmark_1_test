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

`run-dialogs` is not just a thin process wrapper. It owns the simulation
protocol, output contract, and the first layer of automatic evaluation. The
existing `run_dialogs.py` is the first implementation target because it already
contains most of the runner mechanics: two isolated model contexts, function
calling, mock function responses, interruption marking, dialog-end handling, and
compress-style output.

Domain-specific native profile schemas should not be passed directly to the
runner. Always pass `profiles_runtime.jsonl`.

### Inputs

Minimum inputs:

- `profiles_runtime.jsonl`
- prompts JSONL
- assistant model
- user model
- backend
- language
- output path

Optional inputs:

- run ID / experiment ID
- judge model
- evaluator rubric
- max turns
- worker count
- resume offset
- random seed, if the backend supports deterministic settings

### Runtime Profile Contract

The runner consumes the runtime profile contract from `generate-profiles`:

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

Adapters may pass through extra fields, but the runner should not rely on
domain-native fields that are absent from this contract.

### Two-Model Simulation Protocol

The simulation uses two independent message histories:

- Assistant context: system prompt from the benchmark prompt, with identity
  placeholders filled from `profile.identity`, plus tool/function instructions.
- User context: user simulator system prompt built from the runtime profile.

The user model never sees the assistant system prompt or hidden tool definitions
except through the assistant's spoken messages. The assistant model never sees
the full user profile except through the user's spoken replies.

The assistant speaks first. The opening user input should be a minimal start
signal such as "start the call" rather than a scripted user utterance.

Each user turn should be generated with two layers:

1. Internal annotation for audit, such as active motivation, trigger, and
   transition from previous turn.
2. Spoken reply only, used as the actual dialog content.

Only the spoken reply is fed back into the assistant context. Internal
annotations are stored in `laep.remark` or a sidecar trace field for auditing.

### Turn Loop

Recommended loop:

1. Build assistant system prompt from prompt + identity + tools.
2. Build user simulator system prompt from runtime profile.
3. Ask assistant to open the call.
4. Alternate user and assistant turns.
5. If assistant emits a tool/function call, inject a mock function response and
   skip the next user turn so the assistant can continue from the tool result.
6. Stop on `<dialog-end>`, max turns, or unrecoverable API failure.

The output must preserve every actual turn with continuous `turn_index`.
Function responses should appear as system-generated turns tagged with
`function_response`.

### Function-Call Handling

The runner should support:

- prompt-defined function/tool schemas
- assistant native tool calls when the backend supports them
- text fallback format such as `<function-call>...</function-call>`
- mock function response generation
- function-call and function-response tags in the dialog log

Function-call evaluation is separate from simulation and should not block dialog
generation unless a malformed tool call prevents continuation.

Minimum function-call metadata:

```json
{
  "function_name": "...",
  "arguments": {},
  "parse_status": "ok",
  "response_status": "ok"
}
```

### Output Contract

Primary output is JSONL, one dialog per line.

Minimum record shape:

```json
{
  "id": "profile_id",
  "type": "compress",
  "dialog": [],
  "tools": {},
  "meta": {
    "domain": "...",
    "chat_lang": "en",
    "prompt_id": "...",
    "business": "...",
    "assistant_model": "...",
    "user_model": "...",
    "backend": "chatdemo",
    "difficulty": "...",
    "user_starting_position": "...",
    "convertibility_ceiling": "...",
    "ending_expected": "...",
    "elapsed_s": 0.0,
    "run_id": "..."
  },
  "run": {
    "status": "ok",
    "max_turns_hit": false,
    "api_errors": [],
    "function_call_count": 0
  },
  "evaluation": null
}
```

The existing `run_dialogs.py` already writes compress-like records. The wrapper
should gradually add missing `meta`, `run`, and `evaluation` fields without
breaking existing downstream consumers.

### Evaluation Layers

Evaluation must be separated into layers so teams can run cheap checks first and
LLM judges only when needed.

#### Layer 0: Structural Validation

No LLM required.

Checks:

- JSONL parses.
- `dialog` is non-empty.
- `turn_index` is continuous.
- `turn 0` is system.
- Required `meta` fields exist.
- `profile_id` and `prompt_id` are present.
- Function-call tags and function-response tags are paired where required.
- No unclosed `<function-call>`, `<function-response>`, or `<dialog-end>` tags.
- Conversation ended by `<dialog-end>` or has an explicit max-turn stop reason.

Output:

```text
dialog_validate_report.md
dialog_validate_failed.jsonl
```

#### Layer 1: Deterministic Behavior Checks

Mostly rule-based, with optional lightweight classifiers.

Checks:

- Language matches `meta.chat_lang`.
- User simulator did not leak internal annotations in spoken content.
- Assistant did not output tool responses as if speaking to the user.
- Assistant did not keep talking after a clear terminal state.
- User difficulty behavior is plausible:
  - `L1` has no proactive adversarial behavior.
  - `L2` adversarial behavior resolves within one to two turns unless another
    adversarial action starts.
  - `L3` does not self-resolve unless the assistant responds effectively.
- Runtime profile constraints are visible in the dialog.
- `convertibility_ceiling` is not exceeded. For example, a profile with an
  impossible conversion ceiling should not become a clean success.

Output:

```text
dialog_rule_qc.md
dialog_rule_failed.jsonl
```

#### Layer 2: LLM Judge

Use an evaluator model to judge semantic outcomes and policy/process compliance.
This should be optional because it is slower and more expensive.

Judge inputs:

- prompt/system instructions used by assistant
- runtime profile
- full dialog
- tools/function definitions
- domain guide `gen.md`
- target `convertibility_ceiling`

Judge outputs:

```json
{
  "outcome_actual": "...",
  "outcome_matches_ceiling": true,
  "agent_goal_score": 0,
  "process_compliance_score": 0,
  "user_simulation_score": 0,
  "function_call_score": null,
  "safety_compliance_score": 0,
  "overall_score": 0,
  "hard_failures": [],
  "remarks": "..."
}
```

Scores should use a simple 0-2 scale by default:

- `0`: failed or materially wrong
- `1`: partially correct, usable but flawed
- `2`: correct / acceptable

`overall_score` should not hide hard failures. A hard safety or tool-use
failure should keep the record reviewable even if other scores are high.

#### Layer 3: Human Review Handoff

Human review should consume the same output fields rather than a separate ad hoc
format. Failed or uncertain records should be written to:

```text
dialog_review_todo.jsonl
```

Each row should preserve the original record and add:

```json
{
  "qc": {
    "reason": "...",
    "suggested_action": "accept|repair|discard|manual_review"
  }
}
```

### Outcome and Scoring Semantics

The benchmark should distinguish user ceiling from assistant performance.

- `convertibility_ceiling`: best realistic outcome for this user under a strong
  assistant.
- `ending_expected`: optional legacy alias or natural-language target ending.
- `outcome_actual`: what actually happened in the dialog.

A dialog is not automatically bad because it failed to convert. It is bad when
the assistant performs worse than the user's ceiling, violates the process, or
forces an outcome beyond the ceiling.

Recommended top-level score dimensions:

| Score | Meaning |
| --- | --- |
| `agent_goal_score` | Did the assistant reach the best feasible outcome or an acceptable fallback? |
| `process_compliance_score` | Did it follow the prompt's required flow and domain policy? |
| `user_simulation_score` | Did the user model follow the runtime profile and difficulty semantics? |
| `function_call_score` | Were tool calls necessary, well-formed, and followed by appropriate continuation? |
| `safety_compliance_score` | Did the assistant avoid privacy, security, coercion, fabrication, or other hard violations? |
| `conversation_quality_score` | Was the dialog natural, coherent, and not repetitive? |

### Run Artifacts

A complete run should write:

```text
dialog_results.jsonl
dialog_validate_report.md
dialog_validate_failed.jsonl
dialog_rule_qc.md
dialog_rule_failed.jsonl
dialog_judge_scores.jsonl
dialog_review_todo.jsonl
run_manifest.json
```

`run_manifest.json` should include:

- input file paths and hashes when practical
- models
- backend
- worker count
- language
- start/end timestamps
- command arguments
- git commit
- failure counts

### Failure and Resume Behavior

The runner should never silently lose failed dialogs.

Rules:

- API failures write `run_failed.jsonl` with profile ID, prompt ID, error, and
  retry count.
- Resume should support `--offset`, explicit profile IDs, or failed-file replay.
- Concurrent workers must write output with a lock or per-worker temp files.
- A partially completed output file should remain valid JSONL.

### Implementation Notes for Existing run_dialogs.py

Current script capabilities to preserve:

- assistant and user model separation
- user internal annotations stored in remarks
- function-call parsing and mock function responses
- function-response turns tagged as system-generated user turns
- interruption detection by appending `<interrupt>`
- `<dialog-end>` stop condition
- compress-like output

Gaps to add in wrappers or future revisions:

- richer `meta` fields from runtime profile
- run manifest
- failed-run JSONL
- structural validator
- rule QC
- optional LLM judge
- review todo output
- explicit outcome extraction and 0-2 scoring

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
