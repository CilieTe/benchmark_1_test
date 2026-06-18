# Noise and Friction Rules

## Noise Types

Noise is categorized into three primary types based on the source of the disruption. Each type has specific characteristics and constraints regarding when and how it should be applied.

### 1. ASR Garbled / Misrecognized Speech
This category covers instances where the Automatic Speech Recognition (ASR) system fails to transcribe the user's intent correctly, resulting in nonsensical text, numbers, or fragmented phrases.

*   **Characteristics:**
    *   **Numerical Noise:** Single digits (`5`, `6`, `9`, `00`, `33`, `4`, `7`) or short number combinations (`75`, `999`). These often occur when the user is thinking, hesitating, or when background noise interferes with speech.
    *   **Fragmented/Repetitive Text:** Short, unintelligible phrases or repetitions (`cinco`, `a la medio del del banco azteca en la sucursal`, `ah okay mil trescientos setenta y cinco ajá okay`).
    *   **Context:** Usually occurs when the user is not speaking clearly, is interrupted, or is reacting to a complex question with a non-verbal sound that the ASR misinterprets as words.
*   **Heuristic Score:** High (`8-9`). These are high-friction events that require the agent to ask for clarification.

### 2. Code Mixing
This category covers natural speech patterns where users switch between languages (e.g., Tagalog/English, Spanish/English, Indonesian/English) within the same turn or sentence. This is common in multilingual regions.

*   **Characteristics:**
    *   **Polite Particles:** Adding local polite particles to foreign languages (`yes po`, `okay po`, `hello po`, `opo`, `bakit po`).
    *   **Mixed Sentences:** Switching mid-sentence (`ah pues sería hasta como a las cinco de la tarde` - though this is mostly Spanish, the rule applies to mixed code like `yes po` or `hindi po`).
    *   **Context:** Occurs during greetings, confirmations, refusals, or when the user is unsure of the terminology in the primary language.
*   **Heuristic Score:** Low to Medium (`5-6`). These are low-friction events; the agent should understand the intent despite the mixed language.

### 3. Minimal Feedback / Fillers
This category covers short, non-committal responses that provide minimal information but keep the conversation alive.

*   **Characteristics:**
    *   **Affirmations/Negations:** `sí`, `yes`, `hindi`, `no`, `ok`, `ya`.
    *   **Fillers/Hesitations:** `eh`, `ah`, `ajá`, `bueno no`.
    *   **Greetings/Checks:** `hello hello`, `halo iya`.
    *   **Context:** Occurs when the user is listening, thinking, or acknowledging the agent without providing new substantive information.
*   **Heuristic Score:** Low (`6-8`). These are low-friction events. The agent should recognize these as "holding" responses and proceed or rephrase.

### 4. Silence
This category covers periods where no audio is detected from the user.

*   **Characteristics:**
    *   **General Silence:** No sound for a defined duration.
    *   **Identity Verification Silence:** Silence immediately after the agent asks "Am I speaking with [Name]?".
    *   **Payment Request Silence:** Silence immediately after the agent asks for a payment amount or time.
*   **Heuristic Score:** High (`10`). High friction. The agent must handle this by checking connection, asking if the user is still on the line, or repeating the question.

---

## Context Requirements

Noise must be placed in contexts where it is **plausible** for the user to produce such output. Do not insert noise arbitrarily.

1.  **ASR Garbled:**
    *   Place after the agent asks a complex question or reads out a long number/amount.
    *   Place when the user is likely distracted, in a noisy environment, or hesitant.
    *   *Example:* Agent reads a large debt amount -> User says `5` (misrecognized hesitation).
2.  **Code Mixing:**
    *   Place during greetings, confirmations, or when the user is responding to a prompt in a language they are less comfortable with.
    *   *Example:* Agent asks in English -> User responds `yes po` (Tagalog particle).
3.  **Minimal Feedback:**
    *   Place when the agent has just spoken and the user is acknowledging but not yet ready to provide a full answer.
    *   Place when the user is confirming identity or basic details.
    *   *Example:* Agent asks "Can you pay today?" -> User says `eh` or `ah` (thinking).
4.  **Silence:**
    *   Place after the agent asks a direct question requiring a specific answer (Name, Amount, Time).
    *   Place after the agent introduces themselves.
    *   *Example:* Agent asks "Is this John?" -> User says `[Silence]`.

---

## Frequency and Placement

*   **Natural Distribution:** Noise should not appear in every turn. It should occur sporadically, mimicking real-world call center data.
*   **Cluster Avoidance:** Do not stack multiple noise types in consecutive turns unless it represents a severe connection issue (which is rare).
*   **Turn Index:**
    *   **Early Turns (1-5):** High probability of `hello hello`, `halo iya`, `yes po`, `opo`, or `Silence` (identity verification).
    *   **Middle Turns (6-15):** High probability of `ASR Garbled` (during amount/number reading), `Minimal Feedback` (during negotiation), or `Code Mixing`.
    *   **Late Turns (16+):** High probability of `Minimal Feedback` (confirmations) or `Silence` (if the call is ending or failing).
*   **Occurrence Count:** Use the `occurrence_count` from the sample as a guide for relative frequency. `yes po` (20) is more common than `a la medio del del banco azteca en la sucursal` (1).

---

## How Noise Should Affect the Agent

The agent's response must be **context-aware** and **empathetic**. The agent should not ignore the noise, nor should it become aggressive.

1.  **ASR Garbled:**
    *   **Action:** Ask for clarification politely.
    *   **Agent Response:** "Mohon maaf, saya kurang mengerti. Bisa diulangi?" (Sorry, I didn't understand. Could you repeat?) or "Could you please repeat that?"
    *   **Constraint:** Do not assume the meaning. Do not guess the number.
2.  **Code Mixing:**
    *   **Action:** Acknowledge and continue in the primary language or match the user's language if appropriate.
    *   **Agent Response:** Continue the flow. "Okay, noted. So you will pay at 5 PM?"
    *   **Constraint:** Do not correct the user's grammar or language choice.
3.  **Minimal Feedback:**
    *   **Action:** Acknowledge the feedback and proceed to the next step or rephrase the question if stuck.
    *   **Agent Response:** "Baik, kapan kira-kira Kakak bisa melakukan pembayaran?" (Okay, when can you make the payment?) or "Got it. Which payment method would you like to use?"
    *   **Constraint:** Do not repeat the exact same question immediately unless the user is clearly stuck.
4.  **Silence:**
    *   **Action:** Check connection, ask if the user is still there, or repeat the question.
    *   **Agent Response:** "Maaf, suaranya tidak terdengar. Apakah Kakak masih di sana?" (Sorry, I can't hear you. Are you still there?) or "Hello? Can you hear me?"
    *   **Constraint:** Do not assume the call has dropped immediately. Give the user a chance to respond.

---

## What Not to Do

1.  **Do Not Add Noise for Difficulty:** Noise must be realistic. Do not add `ASR Garbled` just to make the dialog harder. It must be a plausible misrecognition of speech.
2.  **Do Not Ignore Noise:** The agent must acknowledge the noise. Ignoring it leads to a disjointed conversation.
3.  **Do Not Overuse Noise:** Too much noise makes the simulation unrealistic and frustrating for the user.
4.  **Do Not Misinterpret Minimal Feedback:** Do not treat `eh` or `ah` as a refusal or agreement. Treat them as fillers.
5.  **Do Not Break Character:** The agent should remain professional and polite, even when dealing with garbled speech or silence.
6.  **Do Not Assume Intent from Garbled Text:** If the user says `5`, do not assume they mean "5 PM" or "5000". Ask for clarification.

---

## Examples

### Example 1: ASR Garbled (Numerical)
**Context:** Agent reads out a debt amount.
**Agent:** "Total tunggakan Anda saat ini adalah lima puluh empat ribu tiga ratus satu Rupiah."
**User:** `5`
**Agent:** "Mohon maaf Kak, apakah maksud Kakak tanggal lima bulan ini untuk melakukan pembayaran? Jika iya, tanggal tersebut sudah lewat. Bisa diinformasikan tanggal pembayaran yang baru dan akan datang?"

### Example 2: Code Mixing
**Context:** User confirms identity.
**Agent:** "Hi luv, this is Virtual Assistant from Tonik Digital Bank. Pwede ko po bang makausap si NILDA PALERMO PATAIAG?"
**User:** `yes po`
**Agent:** "Bago po tayo mag-proceed, ipinaaalam ko lang na ang call na ito ay recorded for quality and training purposes..."

### Example 3: Minimal Feedback (Filler)
**Context:** Agent asks for payment amount.
**Agent:** "Berapa yang bisa Kakak bayar hari ini?"
**User:** `eh`
**Agent:** "Baik, Kakak sedang menghitung ya? Silakan, saya tunggu."

### Example 4: Silence (Identity Verification)
**Context:** Agent asks if user is the account holder.
**Agent:** "Halo, apakah saya sedang berbicara dengan Widodo?"
**User:** `[Silence]`
**Agent:** "Halo..?"

### Example 5: ASR Garbled (Fragmented)
**Context:** User is trying to explain payment method.
**Agent:** "Dengan cara apa Kakak akan melakukan pembayaran?"
**User:** `a la medio del del banco azteca en la sucursal`
**Agent:** "Mohon maaf, saya kurang mengerti. Apakah Kakak ingin membayar di kantor cabang Bank Azteca?"
