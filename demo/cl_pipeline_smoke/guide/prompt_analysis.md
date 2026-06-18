# Prompt Structure Analysis

## Domain Objective
The primary objective is to generate benchmark prompts for **Collections (CL)** and **Pre-Due Reminders** across diverse financial products (BNPL, Credit Cards, Cash Loans, Telecom, Platform Wallets) in specific regions (Indonesia, Mexico, Philippines).

The core goal is to simulate realistic outbound interactions that test an AI agent's ability to:
1.  **Verify Identity** securely before disclosing any account data.
2.  **Navigate Payment Barriers** (channel confusion, app issues, lack of funds) without violating compliance.
3.  **Secure a Payment Commitment** (PTP - Promise to Pay) or resolve a dispute/fraud claim.
4.  **Maintain Strict Compliance** by avoiding illegal collection tactics (harassment, legal threats, third-party disclosure) while remaining firm on the debt obligation.

## Common Assistant Goals
*   **Identity Confirmation:** The agent must confirm they are speaking with the specific account holder before mentioning any debt, amount, or product details.
*   **Payment Resolution:** The ultimate goal is to secure a same-day payment or a concrete future payment plan.
    *   *Pre-Due (M0):* Deliver reminder; note intent.
    *   *Early Overdue (M1):* Secure full or minimum payment.
    *   *Mid/Late Overdue (M2/M3):* Negotiate settlements, minimum reservations, or partial payments based on severity.
*   **Barrier Resolution:** If the customer cannot pay due to technical issues (app down, wrong channel) or financial hardship (payday delay), the agent must document the issue and attempt to reschedule or provide official support channels.
*   **Fraud/Dispute Handling:** Immediately stop collection efforts if fraud, identity theft, or billing disputes are raised, and route to official support.

## Required Flow Patterns
All prompts follow a rigid, state-machine-like structure to ensure consistency in benchmarking:

1.  **Pre-Identity Phase:**
    *   Greet and ask for the customer's name.
    *   *Constraint:* Do NOT mention loan, overdue, amount, or product type until identity is confirmed.
    *   *Third-Party Handling:* If a third party answers, leave a neutral message and close. Do not disclose debt details.

2.  **Identity Confirmation:**
    *   Confirm the customer is the named account holder.
    *   If they deny or refuse, close politely without disclosing details.

3.  **Core Interaction (Post-Identity):**
    *   **State the Purpose:** Briefly state the reason for the call (e.g., "calling about your upcoming installment" or "overdue balance").
    *   **Present Amounts:** State the total due, minimum due, or settlement offer.
    *   **Offer Channels:** List official payment channels (App, Bank Transfer, Cash Stores like OXXO/Alfamart/7-Eleven).

4.  **Branching Logic (Priority Rules):**
    *   *Fraud/Identity Misuse:* Stop immediately. Create fraud case. Close.
    *   *Already Paid:* Record claim. Do not ask for payment again. Close.
    *   *Dispute/Billing Issue:* Note dispute. Route to official support. Ask if they still want to pay the undisputed portion (if applicable).
    *   *Hardship/Payday Delay:* Record hardship. Schedule callback or accept a later date.
    *   *Channel Issues:* Guide to official support or alternative channel.

5.  **Commitment Capture (PTP):**
    *   If the customer agrees to pay, capture: **Amount**, **Date/Time**, **Channel**.
    *   Call `record_ptp` (or equivalent) with these details.
    *   Recap the commitment to the user.

6.  **Closure:**
    *   **Positive:** Thank the user, remind them to keep receipts/comprobantes, and close.
    *   **Negative:** If no agreement is reached, state that no arrangement was completed, provide official support contact, and close.
    *   **Hard Close:** If abuse or repeated silence occurs, use exact termination scripts.

## Tools and Function-Call Requirements
The prompts require specific function calls to track state and outcomes. These are consistent across most scenarios:

*   **`count_event(event_type)`**:
    *   Used for `silence` and `off_topic`.
    *   Increments a counter.
    *   *Logic:* Count 1 = Clarify/Redirect. Count 2 = Repeat/Re-assert. Count >= 3 = Close call.
*   **`parse_payment_time(expression)`**:
    *   Converts vague expressions ("after work", "besok", "mamaya", "sa sweldo") into concrete dates/times for recording.
*   **`record_ptp(...)`** (or `record_payment_intent`, `record_settlement_commitment`):
    *   Records the final agreement.
    *   *Parameters:* `payment_date`, `payment_channel`, `commitment_type` (e.g., `full_payment`, `minimum_payment`, `partial_recharge`, `discounted_settlement`).
*   **`record_payment_claim(...)`**:
    *   Records when a user claims they already paid.
    *   *Parameters:* `channel`, `approximate_payment_time`, `reference` (optional).
*   **`create_fraud_case(claim_summary)`**:
    *   Triggered by fraud/identity misuse claims. Stops all payment requests.
*   **`record_hardship(summary)`** / **`record_dispute(summary)`**:
    *   Documents reasons for non-payment (financial hardship or billing disputes).
*   **`schedule_callback(callback_date)`**:
    *   Used when a customer cannot pay today but has a specific future date (e.g., payday).

## Compliance / Safety Boundaries
Strict boundaries are enforced to prevent illegal or unethical collection practices:

*   **Privacy First:** No account details (balance, product type, overdue status) can be shared with third parties or before identity confirmation.
*   **No Illegal Threats:** Agents must NEVER mention:
    *   Legal action, police, arrest, or jail.
    *   Blacklisting, credit bureau reporting (unless explicitly allowed by local policy, but generally avoided in these prompts).
    *   Home visits, employer contact, or family contact.
    *   Public exposure or shaming.
*   **Data Security:** Agents must NEVER ask for:
    *   PINs, OTPs, passwords, or full card numbers.
    *   Full KTP/ID numbers or screenshots of documents.
*   **Tone:** Firm but calm. No harassment. "Barrier before pressure" – resolve technical issues before pushing payment.
*   **Fraud Halt:** Any claim of fraud or identity misuse immediately terminates the collection flow.

## User Decision Points
The benchmark tests the agent's handling of these specific user states:

1.  **Willing to Pay:**
    *   *Full Payment:* Secure full amount.
    *   *Minimum Payment:* Secure minimum if full is not possible.
    *   *Partial Payment:* Accept partial only if policy allows (e.g., M3 settlement reservation or platform wallet recharge).
2.  **Unable to Pay (Financial):**
    *   *Payday Delay:* Note the date, schedule callback, or accept a later date.
    *   *Hardship:* Document the reason, close politely, route to support.
3.  **Unable to Pay (Technical/Channel):**
    *   *App/Channel Issue:* Guide to official support or alternative channel. Re-attempt payment if resolved.
    *   *Wrong Channel:* Clarify official channels.
4.  **Disputes:**
    *   *Billing Dispute:* Note the dispute, route to support. Ask if they will pay the undisputed portion.
    *   *Fraud/Identity Theft:* Stop immediately, create case, close.
5.  **Already Paid:**
    *   Record the claim. Do not demand payment. Close.
6.  **Hostile/Non-Compliant:**
    *   *Abuse:* Warn once, then close.
    *   *Silence/Off-Topic:* Clarify twice, then close.
    *   *Stop Contact:* Acknowledge, provide support info, close.

## Identity Placeholder Rules
*   **Pre-Confirmation:** The agent must treat the user as an unknown entity. Use generic greetings ("Hello, may I speak with [Name]?").
*   **Confirmation Trigger:** The agent must explicitly ask, "Am I speaking with [Customer Name]?"
*   **Post-Confirmation:** Only after the user confirms (or provides a neutral affirmative like "Yes, this is him/her") can the agent proceed to discuss the account.
*   **Third-Party Handling:** If the user is not the account holder (e.g., "This is his wife," "Wrong number"), the agent must:
    1.  Stop discussing the account.
    2.  Leave a neutral message (e.g., "Please ask [Name] to check their app").
    3.  Close the call immediately.
*   **Refusal to Confirm:** If the user denies being the account holder or refuses to confirm after one retry, the agent must close politely without disclosing any information.
