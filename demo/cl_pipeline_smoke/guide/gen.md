# Domain Guide: cl

This is the routing entry point for CL profile generation. Detailed analyses are kept in the companion Markdown files in this directory; this file preserves only the canonical decisions and generation contract needed by `generate-spec` and `generate-profiles`.

Human review is required before full profile generation.

## 1. Source Map

| Need | Read | Purpose |
| --- | --- | --- |
| Prompt/business objective, assistant flow, compliance boundaries, tools | `prompt_analysis.md` | Understand what the assistant is trying to do and what it must not violate. |
| `user_starting_position`, `convertibility_ceiling`, coverage rules, spec field recommendations | `dimension_design.md` | Define benchmark dimensions and business-outcome labels. |
| Default real-user state for outbound CL calls | `baseline_user_model.md` | Prevent overly cooperative, overly clear, test-like users. |
| User behavior categories and combinations | `behavior_taxonomy.md` | Select realistic behavior patterns for profile design. |
| Noise and friction usage | `noise_rules.md` | Add contextual noise without making noise artificial or overused. |
| Safety/readiness audit | `guide_qc.md` | Review blocking issues and human-review checklist. |

## 2. Canonical Decisions

### Business Objective

The CL benchmark tests whether an assistant can verify identity, preserve privacy boundaries, handle collection/payment barriers, and capture a valid payment commitment or appropriate non-payment outcome without illegal or unsafe collection behavior.

### Convertibility Ceiling

`convertibility_ceiling` is judged from the business outcome perspective.

For CL, user refusal to repay belongs under Failure / Low-No Convertibility because collection did not succeed. This is independent from difficulty: a simple refusal can still be `L1` if the user does not proactively apply adversarial pressure.

Use `dimension_design.md` as the detailed source of truth for outcome categories.

### Difficulty Semantics

Difficulty is assigned at the `profile_spec` / profile stage, not during pool building.

- `L1`: no proactive adversarial behavior. The profile does not require an adversarial move; normal friction may arise naturally from the user's situation, attention, or constraints.
- `L2`: self-resolving adversarial behavior. After an adversarial move, the user does not keep applying pressure regardless of whether the underlying problem is solved.
- `L3`: persistent adversarial behavior. Unless the assistant handles it effectively, the user continues applying pressure, resistance, interruption, accusation, privacy challenge, or refusal pattern.

Do not map difficulty directly from `user_starting_position`, `convertibility_ceiling`, persona, or final business outcome.

### Baseline User Model

Apply `baseline_user_model.md` to every generated profile unless the spec explicitly overrides it. CL users should generally have partial attention, limited patience, defensive trust posture, natural spoken language, and realistic interruption or disengagement tendencies.

Do not add a fixed engagement-state-transition path. Different starting positions and behaviors should remain profile-specific.

### Noise and Friction

Use noise sparingly and only with context. Noise should be plausible for the user's situation and phone-call conditions; it should not be added only to make the task harder.

Prefer typicalized or reviewed noise pools when available. Treat rule-based semantic/pragmatic noise candidates as candidates, not gold labels, unless they have been second-judged.

## 3. Profile Assembly Rules

- Generate motivation-driven profiles, not turn-by-turn scripts.
- Preserve the profile spec fields exactly: `profile_id`, `prompt_id`, `business`, `difficulty`, `user_starting_position` or legacy `intent_level`, `convertibility_ceiling`, `identity`, `resolution_style`, and `action_design`.
- Use `stage2_typical_personas.jsonl` as stable user archetype evidence.
- Use `behavior_pool.jsonl` for realistic user actions and spoken phrasing.
- Use noise pools only with enough context.
- Apply the baseline user model to every profile unless the spec explicitly overrides it.
- `task_instructions` should describe motives, triggers, reaction spectrum, and persistence, not exact replies.
- `behavioral_affordances` should state what the user tends to do, what they do not do, hard boundaries, and how they soften or escalate.
- `behavior_examples` should be short spoken fragments in the target language.

## 4. Identity Handling

- `identity: {}` means no prompt variables need filling or the prompt already mocks identity.
- `identity: {"field": true}` means the generator should create a realistic value for that placeholder.
- Concrete identity values must be preserved.
- Do not add extra identity fields that are not required by the prompt.
- Before identity confirmation, the assistant must not disclose debt/account/product details.
- Third-party or wrong-number cases must preserve privacy boundaries and should not be forced into payment collection.

## 5. Output Profile Requirements

Native profiles may vary by domain, but they must be adaptable to runtime profiles with:

- `profile_id`
- `prompt_id`
- `identity`
- `persona`
- `situation`
- `task_instructions`
- `behavioral_affordances`
- `behavior_examples`
- `ending_expected`
- `meta`

## 6. Quality Checklist

- The profile follows the spec and does not contradict `action_design`.
- The profile is plausible for the CL domain.
- The profile reflects the baseline user model: partial attention, limited patience, natural spoken language, and defensiveness unless explicitly contradicted by the spec.
- The profile is not scripted as "when the agent says X, say Y".
- Difficulty follows the fixed `L1` / `L2` / `L3` semantics.
- `convertibility_ceiling` is respected and is judged from the business outcome perspective.
- User language and behavior are grounded in the pools.
- Noise is contextual and not overused.
- Identity placeholders are handled correctly.
- CL privacy and compliance boundaries are preserved.

## 7. Common Failure Modes

- Making users too attentive, patient, articulate, or test-like.
- Overfitting to one prompt or business line.
- Turning behavior examples into scripts.
- Mapping difficulty directly to conversion outcome, persona, or starting position.
- Treating refusal to repay as anything other than business failure in CL.
- Making all difficult users angry instead of varying behavior types.
- Letting L2 users sustain resistance like L3.
- Letting L3 users soften without effective assistant handling.
- Exceeding `convertibility_ceiling`.
- Adding facts, product benefits, threats, or policy claims not present in prompts.

## 8. User Notes

Generate a CL domain guide. Include realistic outbound-call baseline user states and avoid transferring telemarketing-only assumptions directly into collection.
