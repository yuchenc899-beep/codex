# Compliance Engine

The three compliance modules the `sg-financial-advisor` skill
implements inline: **RES5 / FAA-N16 surrender warning**, **FAA-N20
balanced scorecard**, and **FAA-N06 AML sniffer**. This file is the
implementation reference for Sections 1, 4, and 9 of the output
template.

## 1. RES5 / FAA-N16 — Surrender warning engine

### 1.1 Trigger conditions

The surrender warning must be displayed verbatim if **any** of the
following applies:

- The output recommends **terminating**, **surrendering**, or
  **paid-up**-ing any policy in the **Investment-Legacy** bucket
  (Whole Life, Endowment, ILP, Legacy Par).
- The output recommends **replacing** any existing life policy
  with a new one.
- The output discusses "buying term and investing the difference"
  against an existing Whole Life / Endowment / ILP.

### 1.2 The verbatim warning

Display exactly:

> **Surrender warning (FAA-N16 / RES5).** Terminating a Whole Life,
> Endowment, or ILP policy means you will lose the insurance
> protection it provides, **and you may receive less than the total
> premiums paid** (the cash surrender value is net of distribution
> costs, mortality charges, and expense loadings). This decision is
> **permanent and irreversible** for the policy term. Do not
> surrender under time pressure, family influence, or because an
> agent offered to "replace" it with a new policy.

The phrase "you may receive less than the total premiums paid" is
required language. Do not paraphrase. Do not soften.

### 1.3 Sunk-cost vs cash-value table

For each Investment-Legacy policy flagged, the skill must show:

| Field                | Source                                         |
| -------------------- | ---------------------------------------------- |
| Policy name + insurer| User input                                     |
| Year started         | User input (or estimate from policy number)    |
| Annual premium       | User input                                     |
| Premiums paid (cumulative) | annual premium × years paid             |
| Current cash value   | Insurer benefit illustration (cite URL)        |
| Unrecoverable cost   | premiums paid − current cash value             |

A **negative** unrecoverable cost means the policy is "in the
money" (cash value > premiums paid). A **positive** unrecoverable
cost means the client has not yet recovered the distribution
costs; surrendering now crystallises that loss.

### 1.4 Decision rule

| Profile + situation                                | Recommendation          |
| -------------------------------------------------- | ----------------------- |
| Large unrecoverable cost + client has better Term | Do NOT surrender yet; wait until cash value > premiums paid, OR do not surrender at all |
| Small unrecoverable cost + better Term available   | Consider surrender; show the math |
| Cash value > premiums paid + client can self-insure | Surrender makes sense; show the math |
| ILP with 3–5% p.a. all-in drag + better Term + cheaper index fund | Strongly consider surrender + replace; show the math |

**Never** recommend surrender if the client is replacing the
protection with another high-cost Whole Life / Endowment. The
warning is also about **replacement cost**, not just surrender.

## 2. FAA-N20 — Balanced Scorecard engine

### 2.1 The 4 quadrants

Every recommendation must pass all four:

| Quadrant | Question                                                   | Pass condition                                       |
| -------- | ---------------------------------------------------------- | ---------------------------------------------------- |
| **Q1: Client Need (FNA)** | Does the FNA show this person actually needs this cover? | FNA evidence present; recommendation addresses a documented gap |
| **Q2: Risk Profile Match** | Is the product's risk profile aligned to the client's? | Risk profile result matches product risk band (Conservative/Balanced/Aggressive) |
| **Q3: Affordability** | Can the client sustain premiums across negative scenarios? | Premium ≤ 10% of take-home pay; cashflow surplus ≥ 10% after premium |
| **Q4: Suitability** | Is this the right product, or just an available one? | Comparator table shows ≥ 2 insurers; cheapest suitable option is recommended |

### 2.2 Verdict matrix

| Q1 | Q2 | Q3 | Q4 | Verdict     | Action                                       |
| -- | -- | -- | -- | ----------- | -------------------------------------------- |
| ✅  | ✅  | ✅  | ✅  | **Pass**    | Recommend                                    |
| ✅  | ✅  | ✅  | ⚠  | Pass w/ note| Recommend, disclose the Q4 caveat            |
| ✅  | ✅  | ⚠  | ✅  | Flag        | Recommend only with affordability improvement plan |
| ✅  | ❌  | ✅  | ✅  | Drop        | Do not recommend; mismatch with risk profile|
| ❌  | ✅  | ✅  | ✅  | Drop        | Do not recommend; FNA does not support it    |
| ✅  | ✅  | ❌  | ✅  | Drop        | Do not recommend; cannot afford             |
| ❌  | ❌  | ❌  | ❌  | **Drop**    | No business here; revisit client profile     |

The skill must display the quadrant matrix and verdict in the
output. Any **Drop** quadrant means the recommendation is removed
from the action checklist.

### 2.3 Workings to show

For each quadrant, the skill must cite the **evidence**:

- **Q1:** "FNA shows client has 2 dependents and 10× Death gap; this
  Term Life fills the gap."
- **Q2:** "Client risk profile = Balanced; product is Term Life with
  no sub-fund risk, fits Balanced."
- **Q3:** "Annual premium S$X = Y% of take-home pay; cashflow surplus
  after premium = Z% (above the 10% threshold)."
- **Q4:** "Compared 3 insurers: [insurer A] S$X, [insurer B] S$Y,
  [insurer C] S$Z. Selected [cheapest] because coverage identical."

## 3. FAA-N06 — AML sniffer

### 3.1 Pattern detection

Flag for **escalation to principal FA / compliance officer** if any
of the following is detected:

| Pattern                                         | Trigger                                       |
| ----------------------------------------------- | --------------------------------------------- |
| Premium > 30% of stated income                  | Premium / income > 0.30                       |
| Rapid-fire policy inception                     | ≥ 3 policies in 6 months, ≥ 2 different insurers |
| Third-party premium payer                       | Account name ≠ policyholder name              |
| Cross-border policyholder from FATF grey/black list | Country of residence on the FATF list       |
| Unusually large lump-sum top-up                 | Lump sum > S$200k in a single transaction     |
| Cash payments above reporting threshold         | Cash > S$20k in a single payment              |
| Refund-then-resubmit pattern                    | Refund within 30 days of new policy inception |

### 3.2 Action

If any pattern is detected, the skill must:

1. **NOT** silently proceed with the recommendation.
2. **NOT** ignore the flag.
3. Add an explicit **Step [N]: AML flag** in the action checklist
   recommending escalation to the **principal FA / compliance
   officer**.
4. Cite **FAA-N06** as the regulatory anchor.
5. Mark the rest of the action checklist as **pending the AML
   resolution**.

### 3.3 What the skill must NOT do

- Diagnose the client as a money launderer (only a principal /
  compliance officer can make that call).
- Refuse to do the rest of the review (the AML flag is one
  finding among many; the other findings remain valid).
- Disclose the flag to any third party (AML escalations are
  confidential within the FA firm).

## 4. Putting it together

The compliance engine is invoked in this order during a
`sg-financial-advisor` run:

```
1. Ingest & de-duplicate  →  identify Investment-Legacy bucket
2. RES5 / FAA-N16 surrender scan  →  display warning + sunk-cost table
3. LIA gap analysis  →  identify under-covered areas
4. National protection check  →  verify floor layers
5. FAA-N20 BSC  →  pass/fail/drop per recommendation
6. CPF / cashflow  →  affordability
7. FAA-N06 AML  →  pattern detection
8. Sequence-style action checklist  →  risk-first, growth-last
9. Sources + SG-FA disclaimer
```

If any compliance step fails, the output must reflect it. A
**Drop** verdict on a recommendation means that line item is removed
from the action checklist, not that the whole review is abandoned.

## 5. Audit trail

Every output must be reproducible. The skill should ideally log:

- Date of run
- Inputs (income, premiums, policies, CPF balances)
- Assumptions made
- Verdict per quadrant
- Sources cited (with URLs)

The SG-FA disclaimer at the end is not a substitute for a proper
audit trail. The principal FA is responsible for the audit trail
on their end; the skill is responsible for the **content** of the
audit.
