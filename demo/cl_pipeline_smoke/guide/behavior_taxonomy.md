# Behavior Taxonomy for `cl` Benchmark User Simulation

This taxonomy is derived from Stage 2 personas and the associated behavior pool. It is designed to guide the generation of realistic user profiles for debt collection simulations, focusing on domain-specific interactions (identity verification, payment negotiation, third-party routing) rather than generic conversational traits.

## Major Behavior Types

The following behaviors are categorized by their functional role in the debt collection workflow. Each type includes the definition, triggers, spoken signals (based on the provided pool), and specific agent test points.

### 1. Identity & Verification Behaviors
*Critical for the initial phase of the call. Failure here terminates or derails the interaction.*

#### **Identity Clarification**
*   **Definition:** The user explicitly states they are not the account holder (titular) but is a third party (family, friend, colleague). This shifts the agent’s goal from negotiation to information gathering or message relay.
*   **Triggers:** Agent asks "Is this [Name]?" or "Am I speaking to the account holder?"
*   **Spoken Signals:**
    *   "es dona carmenntaz" (It's Dona Carmen Taz)
    *   "anak anak po ako ni manuel antaran" (I am the child of Manuel Antaran)
    *   "yo le indico que vaya" (I will tell him to go)
*   **Agent Test Point:** Can the agent pivot from negotiation to asking for the titular’s availability or contact info without being rude? Does the agent respect the third party’s boundary?

#### **Failure to Identify**
*   **Definition:** The user refuses or fails to confirm/deny identity, often due to incoherence, evasion, or intentional obfuscation.
*   **Triggers:** Agent asks for identity confirmation.
*   **Spoken Signals:**
    *   Random statements unrelated to the name.
    *   "User does not confirm or deny being Oscar Garcia, instead responding with random statements."
*   **Agent Test Point:** Does the agent persist politely? Does the agent recognize the stalling tactic and attempt to re-verify or terminate based on protocol?

### 2. Payment Negotiation Behaviors
*Core behaviors determining the financial outcome of the interaction.*

#### **Immediate Compliance**
*   **Definition:** The user agrees to the proposed payment terms (amount, method, timeline) immediately upon hearing them, with no negotiation.
*   **Triggers:** Agent states the total amount due and payment options.
*   **Spoken Signals:**
    *   "ya ajá sí" (Yes, okay, yes)
    *   "sí ok"
*   **Agent Test Point:** Can the agent efficiently close the deal? Does the agent confirm the details clearly to ensure execution?

#### **Vague Commitment**
*   **Definition:** The user expresses willingness to pay but provides non-specific timelines or amounts, requiring the agent to probe for concrete details.
*   **Triggers:** Agent asks "When can you pay?" or "How much can you pay?"
*   **Spoken Signals:**
    *   "belum tapi entar dua dua tiga hari lagi" (Not yet, but in two or three days)
    *   "desconozco" (I don't know)
    *   "mmm así es" (Mmm, yes)
*   **Agent Test Point:** Does the agent push for a specific date/amount? Does the agent accept vague answers or enforce commitment?

#### **Contextual Justification**
*   **Definition:** The user provides specific personal reasons (illness, job loss, repairs) for the delay or inability to pay, often linking their livelihood to the delay.
*   **Triggers:** Agent demands payment or asks why payment hasn't been made.
*   **Spoken Signals:**
    *   "iya iya iya ini saya baru sembuh sih kak motor juga baru jadi ini jadi baru mau narik" (Yes, yes, I just recovered, my motorcycle just got fixed, so I just want to drive again)
*   **Agent Test Point:** Does the agent show empathy while maintaining firmness? Does the agent use the justification to offer a modified plan or stick to the original demand?

#### **Payment Assertion**
*   **Definition:** The user claims the debt has already been settled, contradicting the agent’s records.
*   **Triggers:** Agent states the outstanding balance.
*   **Spoken Signals:**
    *   "bayad na kami kanina" (We already paid earlier)
*   **Agent Test Point:** Does the agent verify the claim? Does the agent ask for proof/reference numbers? Does the agent handle conflicting information calmly?

### 3. Engagement & Communication Styles
*Describes the user’s level of participation and cognitive load.*

#### **Minimal Verbal Engagement / Minimal Engagement**
*   **Definition:** The user responds with short, fragmented, or single-word utterances, indicating low attention, multitasking, or passive resistance.
*   **Triggers:** Any agent prompt requiring a response.
*   **Spoken Signals:**
    *   "sí ok"
    *   "tener todo el limpio sí bueno" (Having everything clean, yes, well)
    *   "mmm así es"
*   **Agent Test Point:** Can the agent maintain control of the conversation with low-effort responses? Does the agent repeat questions clearly?

#### **Echoing**
*   **Definition:** The user repeats the agent’s last phrase or part of it without adding new information, often as a stalling tactic or due to lack of attention.
*   **Triggers:** Agent asks a direct question.
*   **Spoken Signals:**
    *   "sí esa cantidad" (Yes, that amount) - repeating the agent's previous statement.
*   **Agent Test Point:** Does the agent recognize the echo and rephrase the question? Does the agent avoid getting stuck in a loop?

#### **Passive Acknowledgment**
*   **Definition:** The user uses filler words or vague acknowledgments without committing to any action or confirming facts.
*   **Triggers:** Agent asks for confirmation or action.
*   **Spoken Signals:**
    *   "bueno" (Well/Okay)
    *   "The user uses 'bueno' as a filler or acknowledgment without confirming identity..."
*   **Agent Test Point:** Does the agent distinguish between acknowledgment and agreement? Does the agent seek explicit confirmation?

### 4. Disengagement & Termination Behaviors
*Behaviors that lead to call termination or procedural closure.*

#### **Complete Silence / Protocol Trigger**
*   **Definition:** The user provides no audio response, triggering the agent’s silence protocol.
*   **Triggers:** Agent speaks; user does not respond.
*   **Spoken Signals:**
    *   "[Silence]"
*   **Agent Test Point:** Does the agent follow the strict silence protocol (e.g., 3 prompts, then terminate)? Does the agent handle technical issues vs. intentional avoidance?

#### **Complete Disengagement**
*   **Definition:** The user provides brief, incoherent noise followed by silence, effectively ending the interaction.
*   **Triggers:** Agent attempts to engage.
*   **Spoken Signals:**
    *   "remo co"
    *   "necesito" (I need) - followed by silence.
*   **Agent Test Point:** Does the agent recognize the disengagement and terminate appropriately?

#### **Incoherent Speech / Topic Drift**
*   **Definition:** The user speaks in disjointed, nonsensical phrases or introduces unrelated topics, making logical negotiation impossible.
*   **Triggers:** Agent asks logical questions.
*   **Spoken Signals:**
    *   "le dice la maestra a pepito..." (The teacher tells Pepito...)
    *   "llegó una señora con farmacéutico..." (A lady arrived with a pharmacist...)
*   **Agent Test Point:** Can the agent maintain professionalism despite high-noise input? Does the agent attempt to steer back to the topic or terminate due to incoherence?

#### **Passive Cooperation (Third-Party)**
*   **Definition:** The third party agrees to pass the message but offers no financial commitment or detailed information.
*   **Triggers:** Agent asks for the titular’s contact or availability.
*   **Spoken Signals:**
    *   "yo le indico que vaya por favor" (I will indicate to him to go, please)
*   **Agent Test Point:** Does the agent thank the third party and confirm the message was received? Does the agent avoid pressuring the third party for payment?

## Behavior Combinations

These combinations define the core personas in the `cl` benchmark. When generating profiles, combine these behaviors to create consistent user archetypes.

| Persona ID | Primary Behavior Mix | Interaction Flow |
| :--- | :--- | :--- |
| **incoherent_avoider** | `Incoherent Speech` + `Topic Drift` + `Failure to Identify` | User speaks nonsense -> Agent tries to verify -> User drifts -> Agent terminates. |
| **immediate_compliant** | `Immediate Compliance` + `Minimal Verbal Engagement` | Agent states amount -> User says "Yes" -> Agent confirms -> Call ends. |
| **conditional_deferrer** | `Contextual Justification` + `Vague Commitment` | Agent demands payment -> User explains illness -> User says "2-3 days" -> Agent pushes for date. |
| **third_party_passive** | `Identity Clarification` + `Passive Cooperation` | Agent asks for titular -> User says "Not me" -> User says "I'll tell him" -> Call ends. |
| **passive_non_responder** | `Minimal Verbal Engagement` + `Ambiguous Initial Statement` + `Passive Acknowledgment` | Agent speaks -> User says "Bueno" -> Agent asks question -> User says "Bueno" -> Stalling. |
| **silent_unreachable** | `Complete Silence` + `Protocol Trigger` | Agent speaks -> Silence -> Agent prompts -> Silence -> Termination. |
| **fragmented_disengaged** | `Incoherent Response` + `Complete Disengagement` | Agent speaks -> User says "Remo co" -> Silence -> Termination. |
| **low_effort_compliant** | `Minimal Engagement` + `Echoing` + `Vague Commitment` | Agent asks details -> User echoes -> User says "I don't know" -> User accepts summary. |
| **third_party_active** | `Identity Clarification` + `Payment Assertion` + `Availability Provision` | Agent asks for titular -> User says "Child" -> User says "Paid already" -> User gives callback time. |

## Resolution / De-escalation Patterns

1.  **The "Easy Win" Closure:**
    *   *Trigger:* `Immediate Compliance`
    *   *Pattern:* Agent confirms amount -> User agrees -> Agent confirms method -> User agrees -> **Resolution: Payment Scheduled.**
    *   *Risk:* Low. Ensure agent captures all necessary details (card number, date) despite user’s brevity.

2.  **The "Stall and Pivot" Negotiation:**
    *   *Trigger:* `Vague Commitment` + `Contextual Justification`
    *   *Pattern:* User gives reason -> Agent empathizes but pushes for date -> User gives vague date -> Agent negotiates to specific date -> **Resolution: Conditional Promise.**
    *   *Risk:* Medium. Agent must not accept "maybe" as a commitment.

3.  **The "Third-Party Handoff":**
    *   *Trigger:* `Identity Clarification` + (`Passive Cooperation` OR `Availability Provision`)
    *   *Pattern:* User identifies as third party -> Agent pivots to info gathering -> User provides info or agrees to relay -> **Resolution: Contact Updated / Message Sent.**
    *   *Risk:* Low. Ensure agent does not violate privacy by discussing debt details with unauthorized third parties.

4.  **The "Technical/Procedural Termination":**
    *   *Trigger:* `Complete Silence` OR `Incoherent Speech` (persistent)
    *   *Pattern:* Agent attempts engagement -> User fails to respond logically -> Agent follows silence protocol -> **Resolution: Call Terminated / Status: Unreachable.**
    *   *Risk:* Low. Strict adherence to protocol is required.

5.  **The "Conflict Resolution" (Disputed Debt):**
    *   *Trigger:* `Payment Assertion`
    *   *Pattern:* User claims paid -> Agent verifies -> Agent acknowledges discrepancy -> **Resolution: Escalation / Note Added.**
    *   *Risk:* High. Agent must not argue but must document the dispute.

## Behaviors to Avoid or Not Overuse

1.  **Overusing `Incoherent Speech`:**
    *   *Reason:* While necessary for the `incoherent_avoider` persona, overusing this in other personas breaks immersion and makes the agent look incompetent if it’s not the designated behavior. Use sparingly and only for specific edge cases.
2.  **Ambiguous `Passive Acknowledgment` without Follow-up:**
    *   *Reason:* If a user says "Bueno" repeatedly, the agent must not assume agreement. Avoid generating profiles where the user is *only* passive without any eventual resolution or clear termination signal, as this creates infinite loops.
3.  **Aggressive `Immediate Compliance` in Non-Compliant Personas:**
    *   *Reason:* Do not force `Immediate Compliance` onto personas like `conditional_deferrer` or `passive_non_responder`. This breaks the persona consistency.
4.  **Ignoring `Identity Clarification`:**
    *   *Reason:* Agents should not continue negotiating payment with a third party who has clarified they are not the debtor. Avoid generating scenarios where the agent ignores `Identity Clarification`.

## How to Use `behavior_pool` in Profile Generation

1.  **Select Persona:** Start with a `persona_id` from the Stage 2 list (e.g., `conditional_deferrer`).
2.  **Map Behaviors:** Retrieve the `behavior_mix` for that persona (e.g., `["Contextual Justification", "Vague Commitment"]`).
3.  **Retrieve Examples:** Use the `behavior_pool` to find specific `text` and `context` examples for each behavior in the mix.
    *   *Example:* For `Contextual Justification`, use: "iya iya iya ini saya baru sembuh sih..."
    *   *Example:* For `Vague Commitment`, use: "belum tapi entar dua dua tiga hari lagi"
4.  **Construct Dialogue:**
    *   Generate the user’s response by adapting the `text` from the pool to fit the current conversation state.
    *   Ensure the `context` aligns with the agent’s previous turn.
5.  **Validate Consistency:**
    *   Check if the generated behavior matches the `decision_pattern` of the persona.
    *   *Check:* Does the user’s `Vague Commitment` align with their `Conditional Deferral` starting position? Yes.
6.  **Add Noise/Style:**
    *   Apply the `communication_style` from the persona (e.g., "Conversational and informal, using filler words") to the generated text.
    *   *Example:* Add "kak", "iya", "bueno" as fillers where appropriate.

This approach ensures that generated profiles are not just random collections of behaviors but coherent, persona-driven interactions that test specific agent capabilities.
