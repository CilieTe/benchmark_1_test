# Baseline User Model

## Outbound Call Defaults

The baseline user in an outbound collection or payment-assistance context is defined by **low initial trust**, **fragmented attention**, and **defensive brevity**. Unlike telemarketing scenarios where the user is often receptive or curious, the baseline collection user enters the call with a pre-existing negative association (debt, overdue status, or fear of harassment).

*   **Attention Level:** Low and easily distracted. Users are often multitasking (working, driving, caring for family) or mentally disengaged. They do not listen for the full duration of the agent’s opening; they wait for the "ask" (payment amount, deadline, or threat).
*   **Patience:** Low. Users have little tolerance for lengthy introductions, compliance scripts, or repetitive verification. They expect immediate relevance.
*   **Trust/Defensiveness:** High defensiveness. The default state is skepticism regarding the caller’s identity and legitimacy. Users frequently question if the call is a scam, a collection agency, or a legitimate bank representative before engaging with the content.
*   **Listening Quality:** Selective and reactive. Users filter for keywords like "pay," "overdue," "amount," "scam," or "stop." They may miss nuanced explanations or compliance disclaimers.
*   **Language Quality:** Variable. In multilingual contexts (e.g., Philippines, Indonesia, Mexico), users often mix languages (Taglish, Indo-English, Spanglish) or use colloquialisms. In noisy environments, speech may be garbled, fragmented, or interrupted.
*   **Initiative Level:** Low to Passive. Users rarely drive the conversation toward resolution. They react to agent prompts. If the agent is passive, the user may disengage entirely.
*   **Interruption Tendency:** Moderate to High. Users interrupt to clarify identity, assert they are not the debtor, claim they already paid, or express frustration.
*   **Disengagement/Hang-up Tendency:** High. If the user determines the call is unwanted, illegitimate, or if they cannot/will not pay immediately, they may hang up abruptly or go silent.

## Domain-Specific Adaptation

Adapting the baseline to the **Collection (CL)** domain requires shifting from "sales receptivity" to "payment negotiation dynamics."

1.  **From "Interest" to "Liability Awareness":** The user knows they have an obligation. The friction is not *whether* to pay, but *when* and *how much*. The baseline user is aware of the debt but may be in denial about the severity (M0/M1) or overwhelmed by the amount (M3+).
2.  **Identity as a Gatekeeper, Not a Formality:** In CL, identity verification is the primary source of user anxiety. Users will not discuss payment until they are certain they are speaking to the correct entity and that their privacy is respected. Failure to verify quickly leads to immediate disengagement or hostility.
3.  **Payment Intent vs. Payment Ability:** The baseline user distinguishes between "willingness" and "capacity." A user may agree to pay (compliance) but lack the funds (hardship). The model must account for this gap: users often offer vague timelines ("after payday," "tomorrow") rather than concrete commitments.
4.  **Noise as a Defense Mechanism:** In telemarketing, noise might be accidental. In CL, fragmented speech, silence, or "garbled" responses can be intentional stalling tactics or expressions of shame/avoidance. The model treats silence not just as technical error, but as a potential behavioral signal of refusal or distress.
5.  **Compliance as a Boundary, Not a Barrier:** Users in CL are highly sensitive to regulatory boundaries (OJK, BSP, local consumer laws). They will test the agent’s compliance (e.g., asking "Are you reporting to OJK?"). The baseline user expects professional, non-threatening conduct. Aggressive or vague language triggers immediate defensiveness.

## Non-Transferable Assumptions

The following assumptions are valid in telemarketing or general customer service but **must not** be applied to the Collection domain without specific evidence:

1.  **"Users are curious about new products":** In CL, users are not interested in upsells or new features. They are focused on resolving the existing obligation.
2.  **"Users appreciate long explanations of policy":** In CL, lengthy explanations of *why* a fee exists or *how* the system works are often perceived as excuses. Users want to know *what* they owe and *how* to fix it.
3.  **"Silence is always technical":** In CL, silence is often behavioral (avoidance, shame, or refusal). Treating all silence as a technical error (e.g., repeatedly asking "Can you hear me?") can escalate user frustration.
4.  **"Users want to be helped":** While some users want help, many feel judged or attacked. The baseline assumption should be that the user feels *pressured*, not necessarily *helped*.
5.  **"Third parties are helpful":** In CL, third parties (family, friends) are often uncomfortable relaying debt information. They may refuse to engage or provide false information to avoid conflict. Assuming they will pass messages is risky.
6.  **"Immediate compliance is common":** In telemarketing, impulse buys are common. In CL, immediate full payment is rare. The baseline should expect negotiation, deferral, or partial payment.

## Profile Generation Implications

When generating user profiles for the CL domain, adhere to these operational rules:

1.  **Persona Construction:**
    *   Use the provided `Stage2 personas` (e.g., `conditional_deferrer`, `passive_non_responder`) as starting points, but layer them with the **Baseline User Model** traits (defensiveness, low trust).
    *   Ensure the `user_starting_position` reflects the specific debt stage (M0: reminder/annoyance; M3: crisis/avoidance).

2.  **Situation & Task Instructions:**
    *   Define the user’s **financial reality** (e.g., "just paid rent," "waiting for salary," "already paid via different channel"). This drives their behavior.
    *   Specify the **communication constraints** (e.g., "speaking while driving," "poor signal," "multilingual").

3.  **Behavioral Affordances:**
    *   Map `Behavior pool` items to the user’s current state. For example, a `conditional_deferrer` should exhibit `Contextual Justification` and `Vague Commitment`.
    *   Ensure `Noise/friction` is applied realistically. `ASR_garbled` should occur during moments of distraction or poor connection, not randomly. `Code_mixing` should reflect the user’s natural linguistic pattern (e.g., Taglish in Philippines).

4.  **Behavior Examples:**
    *   Include **negative examples** where the user rejects the premise (e.g., "I don't owe this," "This is a scam") to test the agent’s compliance and de-escalation skills.
    *   Ensure examples reflect the **domain-specific adaptation**: users should reference local payment channels (GCash, OXXO, Alfamart) and cultural concepts (gajian, quincena) when relevant.

5.  **Avoid Telemarketing Tropes:**
    *   Do not generate users who are overly enthusiastic, chatty, or interested in unrelated topics unless explicitly defined as `off_topic` behavior.
    *   Do not generate users who immediately agree to pay without any verification or hesitation, unless defined as `immediate_compliant`.
