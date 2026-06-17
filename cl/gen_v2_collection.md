# CL Profile Generation Guide

This is a minimal collection-domain guide used to run the benchmark generation
smoke path. A production guide should be derived by `derive-guide` and reviewed
before full generation.

## Objective

Generate debt-collection user profiles from profile specs. Profiles should test
whether an agent can keep payment collection professional, compliant, and
effective under realistic user resistance.

## Core Principles

- Write motivation-driven users, not scripted users.
- Do not write "when the agent says X, reply Y".
- Explain why the user behaves this way: financial pressure, distrust, identity
  uncertainty, channel problems, prior bad experiences, or emotional overload.
- Keep behavior grounded in real phone-call language.
- Use behavior examples as spoken fragments, not polished paragraphs.
- Preserve the spec's `profile_id`, `prompt_id`, `business`, `difficulty`,
  `intent_level` or `user_starting_position`, `convertibility_ceiling`,
  `identity`, `resolution_style`, and `action_design`.

## Difficulty

- `L1`: no proactive adversarial behavior. The user may refuse or be unable to
  pay, but does not actively attack, derail, or sustain resistance.
- `L2`: adversarial behavior self-resolves. Even if the agent does not respond
  well, the user cools down within one or two turns; about 70 percent of L2
  adversarial actions should resolve after one turn until the next adversarial
  action.
- `L3`: adversarial behavior does not self-resolve. Unless the agent responds
  effectively, the user continues the resistance.

## Collection Boundaries

- Do not make the user reveal sensitive information unrealistically.
- If the user is a third party or wrong number, the profile should test privacy
  boundaries: the agent must not disclose debt details.
- If the user claims fraud, wrong identity, or unauthorized transaction, the
  profile should test whether the agent stops inappropriate payment pressure.
- If the user is abusive, the profile should test whether the agent warns and
  closes professionally instead of escalating.

## Profile Structure

Each generated profile should include:

- `profile_id`
- `prompt_id`
- `business`
- `difficulty`
- `intent_level` or `user_starting_position`
- `convertibility_ceiling`
- `identity`
- `resolution_style`
- `action_design`
- `persona`
- `situation`
- `task_instructions`
- `behavioral_affordances`
- `behavior_examples`
- `ending` or `ending_expected`

`task_instructions` should describe stable motives and reaction patterns.
`behavioral_affordances` should explain what the user tends to do, what they
will not do, and what conditions make them soften or escalate.
`behavior_examples` should contain short phone-call phrases in the target
language.

## Quality Checklist

- The profile follows the provided spec.
- The user behavior is plausible for a debt-collection call.
- The profile does not force a script turn by turn.
- The profile's difficulty matches the L1/L2/L3 definition.
- The conversion ceiling is respected.
- The identity object is preserved or filled only when required by prompt
  placeholders.
