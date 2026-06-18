> Note: This QC was generated before `gen.md` was converted into a routing entry document. Treat it as QC for the underlying guide content, not as an audit of the current thin `gen.md` structure.

> Note: This QC was generated before the `Engagement State Transitions` section was removed from the baseline user model requirement. References to that section are stale and should be ignored.

# Guide QC

## Strengths
*   **Strict Compliance Boundaries:** The guide explicitly defines "hard stops" for fraud, identity theft, and illegal threats. This is critical for financial collection benchmarks to prevent generating harmful or non-compliant agent behaviors.
*   **Structured State Machine:** The "Required Flow Patterns" (Pre-Identity -> Identity -> Core -> Branching -> Commitment -> Closure) provide a clear, logical skeleton for the AI to follow, ensuring consistency across diverse scenarios.
*   **Domain-Specific Nuance:** The "Baseline User Model" section effectively distinguishes Collection (CL) from Telemarketing, highlighting key differences like "Liability Awareness" vs. "Interest" and "Silence as Defense" vs. "Silence as Technical Error."
*   **Comprehensive Behavior Taxonomy:** The taxonomy is well-categorized (Identity, Negotiation, Engagement, Disengagement) with specific "Spoken Signals" and "Agent Test Points," which helps in generating realistic user responses and evaluating agent performance.
*   **Noise & Friction Rules:** The inclusion of specific noise types (ASR Garbled, Code Mixing, Minimal Feedback) with heuristic scores and placement rules adds necessary realism to the simulation, preventing overly clean and unrealistic dialogues.
*   **Clear Difficulty Semantics:** The L1/L2/L3 definitions are precise and actionable, providing a clear metric for profile complexity.

## Blocking Issues
*   **Contradiction in Third-Party Handling (Section 1 vs. Section 5):**
    *   *Section 1 (Required Flow Patterns)* states: *"If a third party answers, leave a neutral message and close. Do not disclose debt details."*
    *   *Section 5 (Behavior Taxonomy)* defines `third_party_active` and `third_party_passive` as valid personas with specific interaction flows (e.g., "User provides info or agrees to relay").
    *   *Conflict:* The rigid flow in Section 1 suggests *immediate closure* upon third-party identification, while the taxonomy and persona definitions in Section 5 imply a *negotiation/information-gathering phase* with third parties. This creates ambiguity for the generator: should it generate a call that ends immediately, or one where the agent gathers info?
    *   *Resolution Needed:* Clarify if "Third-Party" profiles are strictly for *message relay* (no negotiation) or if they allow for *availability scheduling* (as implied by `third_party_active`). The current guide allows both, which may lead to inconsistent benchmark data.
*   **Ambiguity in "Convertibility Ceiling" vs. "Resolution Pattern":**
    *   Section 2 defines `convertibility_ceiling` as an outcome (Success/Intermediate/Failure).
    *   Section 5 defines `resolution_pattern` (Easy Win, Stall and Pivot, etc.).
    *   *Conflict:* The mapping between specific `resolution_pattern`s and `convertibility_ceiling` is not explicitly defined in a lookup table. For example, is "Stall and Pivot" always "Intermediate" or can it be "Success" if a PTP is secured? The guide implies a mapping but doesn't enforce it, risking profiles where the user's behavior makes a "Success" ceiling impossible, or vice versa.
*   **Lack of Specific Regional Constraints in "Spoken Signals":**
    *   The guide mentions Indonesia, Mexico, and Philippines. However, the "Spoken Signals" examples are mixed (Tagalog, Spanish, Indonesian) without clear mapping to specific regions or personas.
    *   *Risk:* A generator might assign a Tagalog spoken signal to a Mexican user profile if the `language_mix` field is not strictly enforced. The guide needs a stricter rule: *"Spoken signals must match the `language_mix` defined in the profile spec."*

## Ambiguities
*   **"Pre-Due (M0)" vs. "Overdue (M1+)" Handling:**
    *   The guide mentions M0, M1, M2, M3 in "Common Assistant Goals" but does not define how the *user's behavior* changes based on the delinquency stage.
    *   *Ambiguity:* Does a "Conditional Deferrer" behave differently in M0 (reminder) vs. M3 (late)? The guide implies it does ("severity"), but doesn't provide specific behavioral modifiers for each stage. This could lead to M0 users acting like M3 users (highly defensive) or M3 users acting too compliant.
*   **"Hardship" vs. "Dispute" Distinction:**
    *   The guide lists both `record_hardship` and `record_dispute`.
    *   *Ambiguity:* What is the exact boundary? If a user says "I can't pay because I lost my job," is that hardship? If they say "I can't pay because the amount is wrong," is that a dispute? The guide mentions "Billing Dispute" but doesn't provide clear examples of what constitutes a *valid* dispute vs. a *false* dispute in the context of the benchmark. This affects the agent's decision to route to support vs. continue negotiation.
*   **"Third-Party Active" Definition:**
    *   The definition says: *"The user is a third party who provides specific information (e.g., prior payment, availability) and actively assists in resolution."*
    *   *Ambiguity:* If a third party claims "prior payment," this triggers a `Payment Assertion` (which is usually a debtor behavior). How does the agent handle a third party claiming payment? Do they verify it immediately? The guide doesn't specify the agent's protocol for *third-party* payment claims, which is a critical edge case.

## Missing Inputs
*   **Regional Policy Variations:**
    *   The guide mentions regions (ID, MX, PH) but does not specify if there are *different* compliance rules or payment channels per region that should be reflected in the profile. For example, OXXO is specific to Mexico, Alfamart to Indonesia. The guide mentions them but doesn't enforce that the `payment_channels` in the profile must match the region.
*   **Specific "Stop Contact" Protocol:**
    *   Section 1 mentions "Stop Contact" under User Decision Points, but Section 5 doesn't have a specific behavior for "Request to Stop Contact."
    *   *Missing:* A clear behavior tag for `request_to_stop_contact` and the exact agent response required (e.g., "Acknowledge, provide support info, close"). Without this, agents might continue to nag users who have explicitly asked to be stopped.
*   **Fraud Verification Steps:**
    *   The guide says "Stop immediately" for fraud claims.
    *   *Missing:* What constitutes a "fraud claim"? Is it just "I didn't make this purchase"? Or does it require specific keywords? The guide needs a list of *trigger phrases* for fraud to ensure the agent recognizes it consistently.

## Baseline User Model Checks
*   **Outbound-Call Defaults:** ✅ Included. (Section 4: "Outbound Call Defaults" covers attention, patience, trust, etc.)
*   **Domain-Specific Adaptation:** ✅ Included. (Section 4: "Domain-Specific Adaptation" covers liability awareness, identity as gatekeeper, etc.)
*   **Engagement State Transitions:** ✅ Included. (Section 4: "Engagement State Transitions" covers Skepticism, Assessment, Negotiation, Closure.)
*   **Non-Transferable Assumptions:** ✅ Included. (Section 4: "Non-Transferable Assumptions" lists 6 key assumptions to avoid.)
*   **Practical Profile-Generation Implications:** ✅ Included. (Section 4: "Profile Generation Implications" provides 5 operational rules.)

## Recommended Human Review Checklist

1.  **Resolve Third-Party Flow Conflict:** Decide if third-party interactions are *strictly* message relay (close immediately) or if they allow for *availability scheduling* (continue interaction). Update Section 1 and Section 5 to be consistent.
2.  **Define M0-M3 Behavioral Modifiers:** Add a section or table that specifies how user defensiveness, willingness to pay, and noise levels change based on the delinquency stage (M0 vs. M3).
3.  **Clarify Dispute vs. Hardship:** Provide clear examples and decision trees for agents to distinguish between financial hardship and billing disputes, and the corresponding agent actions.
4.  **Enforce Regional Language/Channel Mapping:** Add a rule that `language_mix` and `payment_channels` in the profile spec *must* match the region specified in the prompt.
5.  **Add "Stop Contact" Behavior:** Add a specific behavior tag for `request_to_stop_contact` and define the agent's mandatory response protocol.
6.  **Define Fraud Triggers:** List specific keywords or phrases that constitute a "fraud claim" to ensure consistent agent recognition.
7.  **Map Resolution Patterns to Convertibility:** Create a clear mapping table between `resolution_pattern` and `convertibility_ceiling` to prevent inconsistent profile generation.

**Verdict:** **Not Safe for Full Generation.** The guide has significant structural contradictions (especially regarding third-party handling) and missing operational details (regional enforcement, dispute/hardship distinction) that will lead to inconsistent and potentially non-compliant benchmark data. It requires human review and revision to resolve these blocking issues before being used for full-scale profile generation. It is safe for *smoke testing* of the generation pipeline's basic mechanics, but not for validating agent performance.
