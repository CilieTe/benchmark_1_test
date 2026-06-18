# Dimension Design

## user_starting_position

This dimension defines the user's initial stance regarding the debt and their willingness to engage in the negotiation process. It is derived directly from the `user_starting_position` field in the Stage 2 personas.

| Label | Definition | Persona Mapping |
| :--- | :--- | :--- |
| **Willing to Pay** | The user is cooperative, acknowledges the debt, and is ready to resolve it immediately or within a short timeframe. | `immediate_compliant` |
| **Conditional Deferral** | The user acknowledges the debt but requires time or specific conditions to be met before payment can be made. | `conditional_deferrer` |
| **Third-party Non-Debtor** | The user is not the account holder but is willing to interact, typically to relay messages or clarify identity. | `third_party_passive` |
| **Third-party Active** | The user is a third party who provides specific information (e.g., prior payment, availability) and actively assists in resolution. | `third_party_active` |
| **Passive Non-Responder** | The user is present but disengaged, offering minimal effort to stall or avoid the conversation without explicit refusal. | `passive_non_responder` |
| **Non-responsive / Incoherent** | The user is mentally distracted, confused, or intentionally obfuscating identity through nonsensical speech. | `incoherent_avoider` |
| **Non-responsive / Unreachable** | The user provides no audio or engagement, leading to procedural termination. | `silent_unreachable` |
| **Unverified / Non-responsive** | A hybrid state where the user provides brief, irrelevant noise before disengaging completely. | `fragmented_disengaged` |
| **Passive/Acknowledging** | The user is technically compliant but lacks attention or detail, agreeing verbally without providing execution data. | `low_effort_compliant` |

## convertibility_ceiling

This dimension defines the maximum achievable positive outcome for a given interaction based on the user's starting position and behavior mix. It categorizes the "success" of the agent's performance.

### Success Outcomes (High Convertibility)
*   **Immediate Payment Scheduled:** User agrees to amount, method, and date immediately (`immediate_compliant`).
*   **Specific Payment Promise:** User provides a concrete date and amount after negotiation (`conditional_deferrer` with successful push).
*   **Dispute Resolved/Verified:** User claims payment made, agent verifies and updates records (`third_party_active` with `Payment Assertion`).
*   **Contact Updated/Message Sent:** Third party agrees to relay message or provides titular's availability (`third_party_passive` / `third_party_active`).

### Intermediate Outcomes (Medium Convertibility)
*   **Vague Commitment Accepted:** User agrees to pay but provides no specific date/amount; agent captures a "soft" promise (`conditional_deferrer` / `low_effort_compliant`).
*   **Partial Information Gathered:** Third party provides some info but refuses to commit to a callback time (`third_party_passive`).
*   **Low-Effort Agreement:** User agrees verbally but requires agent to fill in missing details (`low_effort_compliant`).

### Failure Outcomes (Low/No Convertibility)
*   **Payment Refusal:** User explicitly refuses to repay, denies responsibility for repayment, or states they will not make any payment commitment. This is a failure outcome from the business perspective because collection did not succeed.
*   **Procedural Termination (Silence):** Call ends due to lack of audio (`silent_unreachable`).
*   **Procedural Termination (Incoherence):** Call ends due to inability to understand user (`incoherent_avoider`, `fragmented_disengaged`).
*   **Stall/No Commitment:** User engages minimally but provides no path to resolution (`passive_non_responder`).

## Coverage Rules

The `profile_spec` must ensure comprehensive coverage of the `cl` benchmark by adhering to the following rules:

1.  **Starting Position Distribution:**
    *   Profiles must be distributed across all `user_starting_position` labels.
    *   **High Priority:** `Willing to Pay`, `Conditional Deferral`, and `Third-party` variants must be well-represented as they constitute the majority of real-world calls.
    *   **Edge Cases:** `Non-responsive` and `Incoherent` profiles must be included to test agent robustness and protocol adherence, though they may represent a smaller percentage of the total dataset.

2.  **Behavioral Consistency:**
    *   Each profile must map to a specific `behavior_mix` from the taxonomy.
    *   The `behavior_mix` must align with the `user_starting_position`. For example, `immediate_compliant` cannot exhibit `Contextual Justification` as a primary behavior.
    *   Profiles must include at least one **Primary Behavior** (driving the interaction flow) and one **Secondary Behavior** (adding noise or complexity, e.g., `Echoing` in `low_effort_compliant`).

3.  **Difficulty Assignment:**
    *   Difficulty is assigned at the `profile_spec` stage, not during pool building.
    *   Difficulty must use `L1`, `L2`, and `L3`. Do not use `Low`, `Medium`, or `High` as canonical labels.
    *   Difficulty is independent from `user_starting_position`, `convertibility_ceiling`, and final business outcome. A willing payer can still be difficult if they apply pressure or introduces friction; a refusal can still be L1 if the user simply refuses without proactive adversarial behavior.
    *   **L1:** No proactive adversarial behavior. The profile does not require an adversarial move; normal friction may arise naturally from the user's situation, attention, or constraints.
    *   **L2:** Self-resolving adversarial behavior. After an adversarial move, the user does not keep applying pressure regardless of whether the underlying problem is solved.
    *   **L3:** Persistent adversarial behavior. Unless the assistant handles it effectively, the user continues applying pressure, resistance, interruption, accusation, privacy challenge, or refusal pattern.

4.  **Resolution Pattern Coverage:**
    *   The benchmark must cover all five resolution patterns defined in the taxonomy:
        1.  The "Easy Win" Closure
        2.  The "Stall and Pivot" Negotiation
        3.  The "Third-Party Handoff"
        4.  The "Technical/Procedural Termination"
        5.  The "Conflict Resolution" (Disputed Debt)

## Spec Field Recommendations

The `profile_spec` should include the following fields to ensure accurate simulation and evaluation.

### Required Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `persona_id` | String | The ID from the Stage 2 persona list (e.g., `conditional_deferrer`). |
| `user_starting_position` | Enum | One of the labels defined in the `user_starting_position` section. |
| `behavior_mix` | List[String] | A list of behavior tags from the taxonomy (e.g., `["Contextual Justification", "Vague Commitment"]`). |
| `convertibility_ceiling` | Enum | The expected best-case outcome: `Success`, `Intermediate`, or `Failure`. |
| `difficulty` | Enum | Assigned at spec stage using fixed semantics: `L1`, `L2`, or `L3`. |
| `resolution_pattern` | Enum | The expected resolution pattern: `Easy Win`, `Stall and Pivot`, `Third-Party Handoff`, `Procedural Termination`, or `Conflict Resolution`. |
| `primary_behavior` | String | The single most dominant behavior driving the user's decisions. |
| `communication_style` | String | A brief description of the user's tone, filler usage, and language mix (e.g., "Conversational, informal, Tagalog/English mix"). |

### Optional Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `specific_scenario_details` | String | Additional context for the user's situation (e.g., "User is recovering from surgery," "User is a sibling of the debtor"). |
| `expected_agent_action` | String | A hint for the evaluator on what the agent *should* do (e.g., "Agent should pivot to info gathering," "Agent should push for specific date"). |
| `noise_level` | Enum | Describes the level of incoherence or distraction: `None`, `Low`, `High`. |
| `language_mix` | List[String] | Specific languages or dialects used (e.g., `["Tagalog", "English", "Spanish"]`). |
