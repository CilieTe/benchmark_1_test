# Noise Event Pool Self Audit

Audited file: `demo/cl_pipeline_smoke/noise_event_pool/noise_event_pool_all_types.jsonl`

## Verdict

This pool is useful as a candidate pool, but it is not clean enough to be used as a final benchmark noise pool without second-pass filtering.

Structural validation passed:

- 492 valid JSONL rows.
- 25 noise types.
- No missing required fields.
- No duplicate `event_id`.

Label quality is uneven. Stable surface markers can be used directly. Most semantic/pragmatic labels need LLM or human second judgment before release.

## Use Directly

These types have strong explicit markers and are mostly reliable:

| type | reason |
| --- | --- |
| `silence` | Explicit `[Silence]` user turn. |
| `overlap_interrupt` | Explicit assistant `... [interrupted]` marker. |
| `minimal_feedback` | Mostly short filler tokens, but a few numeric short answers should be filtered. |

## Needs Rule Revision Before Use

These labels have clear false positives in the current pool:

| type | issue |
| --- | --- |
| `asr_garbled` | Current pool was built from the old broad rule. It incorrectly labels normal Spanish containing words like `cinco`, `como`, `banco` as garbled. Should be regenerated with stricter ASR rules. |
| `code_mixing` | Marker-based detection confuses pure Tagalog/Indonesian turns with code-mixing. Needs main-language-aware detection. |
| `truncated_utterance` | Overbroad. It labels `[Silence]`, greetings like `buenas tardes`, and normal short turns as truncated. |
| `conditioned_agreement` | Regex is too loose. It can match substrings such as `if` inside `fifty`, causing numeric utterances to be mislabeled. |
| `authority_deflection` | Overbroad. It treats address terms such as `jefe` or mentions of bank/card as authority deflection. |
| `third_party_boundary_probe` | Overbroad. It catches payment terms near unrelated tokens and does not reliably indicate a third-party privacy probe. |
| `role_confusion` | The phenomenon exists, but the type is too broad. It mixes wrong number, target identity denial, and third-party speaker identity. |

## Needs Second Judgment

These can remain in a candidate pool but should not be final labels without LLM/human review:

| type | reason |
| --- | --- |
| `non_logical_speech` | Current heuristic uses lexical diversity/filler ratio, which catches many normal hesitant utterances. |
| `contradictory_answer` | Affirmation + contrast marker is only a weak signal. |
| `wrong_slot_answer` | Previous-assistant question matching is too broad; many answers are actually relevant. |
| `referent_ambiguity` | Short pronoun/referent heuristic needs context-level validation. |
| `temporal_ambiguity` | Many relative time expressions are valid but still useful; should classify ambiguity severity. |
| `numeric_ambiguity` | Many numeric utterances are valid exact amounts/times, not ambiguous. |
| `indirect_identity_correction` | High-value type, but needs context validation. |
| `implicit_confirmation` | Some rows are just generic `sí`/`bueno`; context decides. |
| `implicit_refusal` | Generally plausible but needs context. |
| `sarcastic_compliance` | Small pool; many `sí claro` cases require tone/context judgment. |
| `hostile_cooperation` | Needs distinguish hostility + valid cooperation from pure abuse/refusal. |
| `privacy_boundary_probe` | Some rows are valid, but privacy/source concern should be verified. |
| `payment_intent_ambiguous` | Requires deciding whether the utterance is truly ambiguous or simply delayed payment. |
| `face_saving_evasion` | Current rule is weak and should be judged semantically. |
| `procedural_pushback` | Often valid, but needs distinguish app/channel issue from actual process pushback. |

## Recommendation

Keep this file as `candidate` data only. Do not use it as final gold noise pool.

Recommended next steps:

1. Regenerate deterministic surface labels with stricter rules for `asr_garbled`, `code_mixing`, and `truncated_utterance`.
2. Split `role_confusion` into more precise identity types:
   - `wrong_number_identity_denial`
   - `target_identity_denial`
   - `third_party_identity_claim`
   - `identity_correction`
3. Run LLM second judgment for all semantic/pragmatic candidates, returning `valid`, `corrected_type`, `confidence`, and `reason`.
4. Human review a stratified sample from the LLM-accepted rows before using it in benchmark generation.

## Practical Status

- Safe for exploration and taxonomy design: yes.
- Safe as profile-generation reference after marking as noisy candidates: maybe.
- Safe as final benchmark noise pool/gold labels: no.
