
# Deductions Feature — Implementation Plan (2024–25) · UI-Aware v2

*Last updated: 2025-08-16*

This plan adds common individual deductions for **ATO 2024–25** to the tax-assistant without breaking existing functionality or look & feel. It:

* Preserves the **current two-column layout** (Chat left, Form right).
* Introduces a **step-based (wizard) deductions flow** embedded in the existing **right-hand card**.
* Ensures **chat ↔ form bidirectional sync** (existing behavior) for all new deduction fields.
* Only implements deductions with **clear ATO guidance** already captured in rules JSON; anything uncertain is marked **Requirement Unclear** (do not implement).

> Throughout, any rule thresholds/rates must be read **only** from the `deductions_2024_25` section of the rules file to avoid hard-coding.

---

## 0) Scope & Non-Goals

**In scope (implement now):**

* Working from home (fixed-rate)
* Car expenses (choose cents-per-km *or* logbook per car)
* Phone & internet (work use; disabled when WFH fixed-rate used for same period)
* Clothing & laundry (protective/occupation-specific/compulsory; laundry rates & evidence thresholds)
* Tools, equipment & other assets (≤ \$300 immediate; > \$300 flag “depreciation required”, no DV math yet)
* Union & professional fees
* Gifts & donations (DGR; minimum amount; “bucket donations” small-amount rule)
* Cost of managing tax affairs
* Personal super contributions (deductible) with concessional cap **check** (warn only)

**Requirement Unclear (do not implement logic yet):**

* Self-education nuances (advanced eligibility & travel combinations)
* Depreciation schedules/effective life for assets **> \$300**
* Automatic trimming of personal super to fit within the cap (warn-only vs auto-reduce requires product decision)

---

## 1) IA & UX: Fit the Current Two-Column Screen

### 1.1 Entry points (no page routing changes)

* **Right card** gains a **“Add deductions (2024–25)”** button above the Calculate bar.
* **Chat** gains a quick-reply chip (“Add deductions”) that opens the right-card wizard to the first relevant step inferred from the last user message.
* **Post-calculation result** (if present) shows a summary line “Deductions: \$X” with a “Review” link that re-opens the wizard on **Review**.

### 1.2 Deductions wizard placement

* The **wizard renders inside the existing right panel card**, replacing its normal content.
* Keep **header, padding, typography, and spacing tokens** consistent with existing card.
* Provide **Back**, **Next**, and **Exit** (Cancel) at the bottom; **Exit** returns to the original income form without losing any entered deductions.

### 1.3 Step list (linear, skippable)

1. Overview & Year (confirm 2024–25)
2. Working from home (fixed-rate)
3. Car expenses (choose method → reveal fields)
4. Phone & internet (disabled if WFH conflicts)
5. Clothing & laundry
6. Tools & equipment
7. Gifts & donations (DGR)
8. Union & professional fees
9. Cost of managing tax affairs
10. Personal super (deductible)
11. Review & Validate (ledger preview, warnings)
12. Apply to Tax Calc

* Each category step has “**Skip this category**” (marks zero for that step and continues).
* Use **progressive disclosure** within steps (e.g., car method choice reveals appropriate inputs).

### 1.4 Consistency & accessibility

* Color, focus states, keyboard order match the current form.
* Stepper shows current progress (e.g., 4/12) and allows going **back** to edit; non-linear jumping **only backward** to avoid skipping validations.

---

## 2) Shared State & Chat ↔ Form Synchronization

### 2.1 Single source of truth (client)

Introduce a **shared deductions store** on the client (e.g., Zustand/Redux) that both **Chat** and **Wizard** read/write:

```ts
type DeductionsState = {
  year: '2024-25';
  wfh?: { hours?: number, useFixedRate: boolean };
  car?: Array<{
    id: string, method: 'cents_per_km'|'logbook',
    kms?: number, workUsePct?: number,
    actuals?: { fuel?: number, servicing?: number, insurance?: number, interestOrLease?: number, depreciation?: number }
  }>;
  phoneInternet?: { workUsePct?: number, incidental?: { claimsIncidental: boolean } };
  clothingLaundry?: { workOnlyLoads?: number, mixedLoads?: number, purchases?: number };
  tools?: Array<{ cost: number, workUsePct: number }>;
  donations?: { dgrAmount?: number, bucketAmount?: number, isDGRConfirmed?: boolean };
  unionFees?: number;
  taxAgentFees?: number;
  personalSuper?: { amount?: number };
  // derived flags (read-only on UI)
  conflicts: string[]; warnings: string[];
};
```

> The store mirrors the **API input** and the **rules JSON** field names to minimize mapping code.

### 2.2 Chat → Form mapping

Implement a **chat intent mapper** that normalizes messages into store updates:

Examples:

* “I worked from home \~400 hours” → `wfh.hours=400`, `wfh.useFixedRate=true`, open wizard at **WFH**.
* “Drove 3,200 km for work” → add car item `{method:'cents_per_km', kms:3200}`; open wizard at **Car**.
* “Donated \$200 to a DGR” → `donations.dgrAmount=200`, `donations.isDGRConfirmed=true`; open **Donations**.
* “Paid \$50 union fees” → `unionFees=50`; open **Union & professional fees**.

**Requirements:**

* Entity extraction should **only** set fields that are unambiguous (numbers, yes/no, simple selections).
* If ambiguity exists (e.g., car method not specified), set a **pending question** for the wizard and open that step.
* Debounce updates (250–400 ms) to avoid race conditions when a single message yields multiple fields.

### 2.3 Form → Chat reflection

Whenever a user **completes a step** (hits Next or Review), post an **assistant summary** in Chat, e.g.:

* “Logged 400 WFH hours (fixed-rate). Phone/internet claims will be disabled for those hours.”
* “Car: cents-per-km selected, 3,200 km.”

This helps users who prefer chat see a running summary and preserves the existing “conversation explains the form” behavior.

### 2.4 Conflict handling in the store

* If `wfh.useFixedRate===true` and `wfh.hours > 0`, set a derived conflict to **disable Phone & Internet** inputs and show a rationale banner.
* If a car step switches from `logbook` to `cents_per_km`, clear actuals and set a warning “running costs will not be added separately.”
* Conflicts/warnings are displayed **both** in form (as banners/field help) **and** echoed to chat summaries.

---

## 3) Backend & API

### 3.1 Rules loader

**Task:** Expose `deductions_2024_25` for year 2024–25; schema check at startup.

**Acceptance:**

* Missing/invalid fields in rules cause a clear startup error (schema path in message).
* No hard-coded thresholds in code; all read from rules.

### 3.2 Deduction calculator

**Function:** `validate_and_calculate_deductions(payload, income, year) → { total_allowed, line_items[], engine_flags }`

**Behavior:**

* Implements only deductions with clear rules (see “In scope”).
* Enforces guardrails (WFH vs phone/internet, car method exclusivity, receipts thresholds, super cap **warning** only).
* Returns a **ledger** (per line claimed: claimed, allowed, reason/adjustment) and **engine\_flags** (conflicts, warnings, caps).

**Acceptance:**

* Deterministic outputs.
* Full parity with rules JSON values.
* ≥ 95% unit test coverage on calculator.

### 3.3 Endpoints (backward-compatible)

* `POST /deductions/preview` → validate + price deductions without computing tax.
* Extend `POST /tax/calc` to accept `deductions[]`; compute:

  * `taxable_income = income – total_allowed`
  * Then run existing tax/Medicare/MLS logic.

**Acceptance:**

* OpenAPI updated; new error taxonomy: `validation_error`, `rule_conflict`, `cap_exceeded`, `unsupported_year`.
* Requests without `deductions[]` behave exactly as today.

---

## 4) Agent Orchestration

### 4.1 Tool

Expose `validate_and_price_deductions(deductions[], income, year)` for the agent.

### 4.2 Prompts

* “If user mentions deductions or asks for totals including deductions, first call `validate_and_price_deductions` with the current client state.”
* “Explain reductions/blocks using reasons from the ledger; never invent rules.”
* “When the user gives new facts (e.g., ‘3,200 km’), propose the appropriate step and update the client state.”

**Acceptance:**

* In e2e tests, any deduction-related chat triggers a tool call before totals.
* Responses contain ledger reasons verbatim (paraphrased, not reinterpreted).

---

## 5) Frontend (Right-Card Wizard inside Existing Layout)

### 5.1 Shell & Navigation

**Tasks:**

* Add a **Deductions** button to the existing form card header.
* Mount the wizard **inside the card**; preserve current card styling.
* Controls: **Back**, **Next**, **Exit** (Exit returns to main form, preserving state).

**Acceptance:**

* Keyboard/ARIA compliant; focus traps only when wizard is open.
* Wizard state persists on back navigation and page refresh (session storage).

### 5.2 Step Components (2–10)

Per step:

* Short guidance at top; inputs below; progressive disclosure for sub-choices.
* “Skip this category” link sets zero values and advances.
* Inline rule hints sourced from rules JSON (no hard-coding of figures).

**Examples of inputs (labels, not code):**

* **WFH:** “Hours worked from home (2024–25)”
* **Car:** Method radios (“Cents per km” / “Logbook”), then kms or work-use% + actuals
* **Phone & Internet:** “Work use percentage” or “Incidental claim” (disabled with WFH conflict)
* **Clothing & Laundry:** “Work-only loads”, “Mixed loads”, “Protective/Uniform purchases (optional)”
* **Tools:** Repeatable rows “Cost” + “Work use %”
* **Donations:** “Amount to DGR”, “Bucket donations (optional)”, “Confirm DGR” checkbox
* **Union & Pro Fees:** “Total paid”
* **Tax Agent Fees:** “Total paid”
* **Personal Super:** “Personal (after-tax) contribution”

**Acceptance:**

* Conditional fields appear without layout jump; screenreader announces changes.

### 5.3 Client-side guardrails

* WFH chosen → **disable** Phone/Internet inputs and show rationale.
* Car cents/km → **hide/ignore** running costs, show note “included in rate.”
* Laundry → show “receipts not required ≤ threshold” helper; show overall > \$300 work-related evidence reminder at Review.
* Super → show cap **warning**; no auto-trim.

**Acceptance:**

* Guardrails match backend decisions (see parity tests).

### 5.4 Review & Validate (Step 11)

* Call `/deductions/preview` and render the **ledger** (claimed vs allowed, reasons).
* Show **warnings/conflicts** returned by engine.
* “Edit” links jump back to relevant steps; returning to Review re-calls preview.

### 5.5 Apply to Tax Calc (Step 12)

* Post to `/tax/calc` with current deductions; show updated results in the same right card results view you already use.
* Chat posts an assistant summary (“Applied \$X deductions; taxable reduced to \$Y”).

---

## 6) Chat Enhancements (Sync)

### 6.1 Intent extraction (client)

* Parse plain language for amounts, durations, percents, and categories.
* For ambiguous intents (e.g., car method unknown), set a **pending field** and open the wizard step to resolve.

### 6.2 Echo & audit

* After each step completion, post a succinct assistant line in Chat summarizing what changed.
* When conflicts occur (e.g., WFH + Phone), post a clarifying assistant message that mirrors the on-form banner.

**Acceptance:**

* No “hidden state”: changes in either surface are visible in the other.

---

## 7) Testing

### 7.1 Unit (calculator)

* WFH only; Car cents/km cap; Car logbook with % + actuals; WFH+Phone conflict; Laundry ≤ threshold and total work-related > threshold; Tools ≤ \$300 immediate; Donations DGR + bucket; Personal super cap warning.
* ≥ 95% coverage on deduction math/guards.

### 7.2 Integration (API)

* `/deductions/preview` deterministic ledger snapshots.
* `/tax/calc` reduces taxable income by preview total; no regressions to existing tax/Medicare/MLS outputs when deductions empty.

### 7.3 UI (wizard)

* Step navigation, state persistence, conditional reveals, field disabling for conflicts, Review parity with preview.
* Accessibility: focus order, ARIA attributes for stepper and dynamic content.

### 7.4 Chat sync

* Chat message updates form state (store values change).
* Form step completion posts assistant summary lines.
* Conflicts produce both banners and chat notes.

---

## 8) Deployment & Backward Compatibility

* Feature-flag the Deductions button and API handling.
* If flag off, right card stays as today; endpoints ignore `deductions[]`.
* Analytics (names only): `deduction_claimed`, `deduction_blocked`, `cap_warning_shown`, `receipts_warning_shown`, `chat_to_form_sync`, `form_to_chat_sync`.

**Acceptance:**

* Old “income-only” flow identical when no deductions are provided or feature flag is off.

---

## 9) Data Contracts (No Code, Schemas Only)

### 9.1 `/deductions/preview` request (example shape)

```json
{
  "year": "2024-25",
  "income": 120000,
  "deductions": {
    "wfh": { "hours": 400, "useFixedRate": true },
    "car": [{ "id": "car-1", "method": "cents_per_km", "kms": 3200 }],
    "phoneInternet": { "workUsePct": 30 },
    "clothingLaundry": { "workOnlyLoads": 40, "mixedLoads": 50 },
    "tools": [{ "cost": 250, "workUsePct": 80 }],
    "donations": { "dgrAmount": 200, "bucketAmount": 5, "isDGRConfirmed": true },
    "unionFees": 120,
    "taxAgentFees": 180,
    "personalSuper": { "amount": 5000 }
  }
}
```

### 9.2 `/deductions/preview` response (example shape)

```json
{
  "total_allowed": 1234.56,
  "line_items": [
    { "id": "ded_wfh_fixed_rate", "claimed": 280.00, "allowed": 280.00 },
    { "id": "ded_car_expenses", "claimed": 2816.00, "allowed": 2816.00, "note": "cents-per-km method chosen" },
    { "id": "ded_phone_internet", "claimed": 360.00, "allowed": 0.00, "reason": "Excluded due to WFH fixed-rate for same hours" }
  ],
  "engine_flags": {
    "conflicts": ["phone_internet_blocked_by_wfh"],
    "warnings": ["personal_super_may_exceed_concessional_cap"]
  }
}
```

> Exact keys must match the rules file identifiers to keep the UI, agent, and backend aligned.

---

## 10) Definition of Done

* ✅ Rules loader surfaces `deductions_2024_25`; no hard-coded rule values in code.
* ✅ Deterministic calculator with guardrails & ledger output; ≥ 95% unit coverage.
* ✅ `/deductions/preview` + extended `/tax/calc` implemented and documented.
* ✅ Right-card wizard integrated; two-column layout preserved; feature-flagged.
* ✅ Chat ↔ form sync both directions with conflict messaging.
* ✅ Review step matches preview output; Apply step updates tax breakdown.
* ✅ Accessibility and responsiveness preserved.
* ✅ “Requirement Unclear” areas **not implemented**.

---

## 11) Open Questions (to resolve before extending scope)

* **Self-education**: confirm detailed eligibility & travel logic sources and examples for 2024–25.
* **Depreciation for >\$300 assets**: decide whether to add a basic DV module or defer to a later phase.
* **Personal super over cap**: confirm whether to warn only or offer auto-adjust with explicit user consent.

---

If you want, I can now convert this into **Jira/Linear tickets** with dependencies, story points, and acceptance criteria copied verbatim from each section.

