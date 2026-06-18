# Noise Event Pool Review Notes

This file summarizes `noise_event_pool_candidate.jsonl` output.
Rows are candidate labels, not gold labels.
By default, surface noise is rule-based and semantic/pragmatic noise is mined by Chatdemo.

## Counts

- Total rows: 846
- Family counts: {'surface_noise': 201, 'pragmatic_noise': 391, 'semantic_noise': 254}
- Needs human review: 696
- Usually stable surface rows: 150

## Type Counts

| noise_type | rows | human review |
| --- | ---: | --- |
| `asr_garbled` | 1 | yes |
| `authority_deflection` | 4 | yes |
| `code_mixing` | 50 | yes |
| `conditioned_agreement` | 50 | yes |
| `contradictory_answer` | 37 | yes |
| `face_saving_evasion` | 50 | yes |
| `hostile_cooperation` | 50 | yes |
| `implicit_confirmation` | 50 | yes |
| `implicit_refusal` | 50 | yes |
| `indirect_identity_correction` | 50 | yes |
| `minimal_feedback` | 50 | optional |
| `non_logical_speech` | 50 | yes |
| `numeric_ambiguity` | 50 | yes |
| `overlap_interrupt` | 50 | optional |
| `payment_intent_ambiguous` | 2 | yes |
| `privacy_boundary_probe` | 25 | yes |
| `procedural_pushback` | 7 | yes |
| `referent_ambiguity` | 50 | yes |
| `role_confusion` | 21 | yes |
| `sarcastic_compliance` | 2 | yes |
| `silence` | 50 | optional |
| `temporal_ambiguity` | 4 | yes |
| `third_party_boundary_probe` | 50 | yes |
| `wrong_slot_answer` | 43 | yes |

## Best Human-QC Targets

These types should be reviewed before use in final benchmark generation:

- `asr_garbled`
- `authority_deflection`
- `code_mixing`
- `conditioned_agreement`
- `contradictory_answer`
- `face_saving_evasion`
- `hostile_cooperation`
- `implicit_confirmation`
- `implicit_refusal`
- `indirect_identity_correction`
- `non_logical_speech`
- `numeric_ambiguity`
- `payment_intent_ambiguous`
- `privacy_boundary_probe`
- `procedural_pushback`
- `referent_ambiguity`
- `role_confusion`
- `sarcastic_compliance`
- `temporal_ambiguity`
- `third_party_boundary_probe`
- `wrong_slot_answer`

These types are usually stable but still benefit from spot checks:

- `minimal_feedback`
- `overlap_interrupt`
- `silence`

## Notes

- `semantic_noise` and `pragmatic_noise` are heuristic candidates and should not be treated as gold labels.
- `asr_garbled`, `code_mixing`, and `truncated_utterance` are surface-level but still need review because rule-based language/noise detection can overfire.
- Prefer this event pool for discovery and taxonomy work. Use only reviewed rows for release-quality profile generation.
