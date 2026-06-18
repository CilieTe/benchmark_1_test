# Noise Event Pool Summary

- Source candidates: deleted temporary audit file `demo/noise_type_audit_full/noise_type_candidates.jsonl`
- Output: `demo/cl_pipeline_smoke/noise_event_pool/noise_event_pool_all_types.jsonl`
- Total selected: 492
- Types: 25

| family | type | candidates | selected |
| --- | --- | ---: | ---: |
| surface_noise | `silence` | 1311 | 20 |
| surface_noise | `minimal_feedback` | 1708 | 20 |
| surface_noise | `asr_garbled` | 142 | 20 |
| surface_noise | `code_mixing` | 1303 | 20 |
| surface_noise | `overlap_interrupt` | 1421 | 20 |
| surface_noise | `truncated_utterance` | 2379 | 20 |
| semantic_noise | `non_logical_speech` | 184 | 20 |
| semantic_noise | `contradictory_answer` | 281 | 20 |
| semantic_noise | `wrong_slot_answer` | 1982 | 20 |
| semantic_noise | `referent_ambiguity` | 361 | 20 |
| semantic_noise | `temporal_ambiguity` | 715 | 20 |
| semantic_noise | `numeric_ambiguity` | 674 | 20 |
| semantic_noise | `role_confusion` | 58 | 20 |
| pragmatic_noise | `indirect_identity_correction` | 75 | 20 |
| pragmatic_noise | `implicit_confirmation` | 133 | 20 |
| pragmatic_noise | `implicit_refusal` | 117 | 20 |
| pragmatic_noise | `sarcastic_compliance` | 12 | 12 |
| pragmatic_noise | `hostile_cooperation` | 71 | 20 |
| pragmatic_noise | `third_party_boundary_probe` | 31 | 20 |
| pragmatic_noise | `privacy_boundary_probe` | 52 | 20 |
| pragmatic_noise | `payment_intent_ambiguous` | 238 | 20 |
| pragmatic_noise | `conditioned_agreement` | 258 | 20 |
| pragmatic_noise | `face_saving_evasion` | 40 | 20 |
| pragmatic_noise | `authority_deflection` | 100 | 20 |
| pragmatic_noise | `procedural_pushback` | 45 | 20 |

Notes: heuristic candidates are not gold labels; semantic/pragmatic rows require human review before final benchmark release.
