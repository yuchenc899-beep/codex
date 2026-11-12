# LIA Gap Formulas

The LIA-published "rule of thumb" formulas for insurance adequacy, the
M9A ILP detection rule, and the FNA matrix used in the
`sg-financial-advisor` skill. This file is the math backbone of the
output.

## 1. LIA standard gap formulas

These are the **starting-point multiples** an FA Rep should default to
when a client has no specific dependency, mortgage, or income trajectory
that would override them. Always personalise.

### 1.1 Coverage → target multiple

| Coverage                | Formula              | Rationale                                       |
| ----------------------- | -------------------- | ----------------------------------------------- |
| **Death / TPD**         | Annual income × 10   | 10 years of income replacement for the family   |
| **CI (Critical Illness)** | Annual income × 4  | 4 years of recovery income (multi-pay can stack)|
| **ECI (Early CI)**      | Annual income × 1    | Lump-sum for early-stage diagnosis              |
| **Personal Accident**   | Annual income × 4    | Accidental death + permanent disablement        |
| **Hospitalisation**     | IP Plan 2 ceiling    | S$1.5M typical ceiling                          |

### 1.2 Worked example (29yo non-smoker, S$60k income)

| Coverage | Target formula              | Target (S$)    |
| -------- | --------------------------- | -------------- |
| Death    | 60,000 × 10                 | 600,000        |
| CI       | 60,000 × 4                  | 240,000        |
| ECI      | 60,000 × 1                  | 60,000         |
| PA       | 60,000 × 4                  | 240,000        |

If the user has a **mortgage** of S$300,000 outstanding, the Death
target becomes S$900,000 (income replacement + debt clearance). If
the user has **2 children** and a non-working spouse, Death target
becomes S$1.2M+ (10 years × dual-income replacement).

### 1.3 Adjustment matrix

| Life situation                         | Adjustment                |
| -------------------------------------- | ------------------------- |
| Single, no kids, no mortgage           | × 0.5 on Death            |
| Single, mortgage S$X                   | + outstanding loan         |
| Married, no kids                       | × 1.0 on Death, +0.5 on CI |
| Married, 1–2 kids                      | × 1.0 on Death, × 1.0 on CI|
| Single parent, kids                    | × 1.2 on Death, × 1.0 on CI|
| Self-employed / commission-based        | × 1.2 on Death            |
| Smoker / pre-existing condition        | Premium load +0.5× to 2×  |

The FA Rep's job is to make these adjustments transparent to the
client and walk through them line by line.

## 2. Net gap math

For every coverage line:

```
Net gap = Target (formula × life-situation adjustment)
        − Aggregated sum assured across all policies covering that risk
        + Outstanding debts / liabilities that the coverage must clear
```

| Result    | Interpretation                                            |
| --------- | --------------------------------------------------------- |
| Net > 0   | Under-covered. The client should buy more.                |
| Net = 0   | Right-sized. Hold; review annually.                      |
| Net < 0   | Over-covered. May be over-paying. Investigate.            |

> **Important.** A **negative** gap on Death is fine if the
> policies are Term (cheap protection). A **negative** gap on Death
> caused by an ILP's account value is **not** fine — the account
> value is not payable on death in the same way as a sum assured.

## 3. M9A — ILP detection rule

The M9A module classifies an **Investment-Linked Policy (ILP)** by
keyword. Flag a plan as an ILP conflict if its name, brochure, or
product summary contains any of the following:

| Keyword                  | Example                                 |
| ------------------------ | --------------------------------------- |
| "Link"                   | GreatLink, ManuLink, PRUlink            |
| "Flexi"                  | FlexiPlan, FlexiLife, FlexiAdvantage    |
| "Managed Investment"     | "Managed Investment Account"            |
| "Investment-linked"      | Explicit phrase                         |
| "Sub-Funds"              | "Choice of Sub-Funds"                   |
| "Premium Allocation"     | "100% Premium Allocation"               |
| "Bid-Offer Spread"       | "Bid-Offer Spread: 5%"                  |
| "Account Value"          | "Current Account Value"                 |
| "NAV"                    | "Net Asset Value of the Sub-Fund"       |

**Why this matters.** ILPs have:
- **Bid-offer spread** on every premium allocation (1–5% drag)
- **Mortality & expense (M&E) charges** deducted monthly from the
  account value
- **Fund management fees** of 0.5–1.5% p.a. on the sub-fund
- **Sub-fund market risk** that the policyholder bears fully
- **No guaranteed cash value** — the policy can lapse to zero

The "Total Expense Ratio" of an ILP can run **3–5% p.a. effective**
when bid-offer + M&E + fund fees are combined. This is the
"Premium Overhead Inefficiency" the skill is designed to detect.

## 4. FNA matrix (Financial Needs Analysis)

The FAA-N20 FNA is the structured input to every recommendation. The
**minimum** FNA data points the FA Rep must capture:

| # | Field                              | Notes                                       |
| - | ---------------------------------- | ------------------------------------------- |
| 1 | Age                                | Drives term-life pricing, age-bands         |
| 2 | Gender                             | Mortality table selection                   |
| 3 | Smoker status                      | Non / Occasional / Smoker                   |
| 4 | Annual income (gross)              | Drives the ×10 / ×4 / ×1 formulas           |
| 5 | Annual income (after tax)          | Drives the cashflow analysis                |
| 6 | Marital status                     | Drives Death/CI adjustments                 |
| 7 | Number of dependents               | Kids, parents, spouse                       |
| 8 | Outstanding mortgage               | Drives Death target adjustment              |
| 9 | Other debts                        | Car loans, study loans, credit cards        |
| 10| Existing policies + sum assured    | Drives the gap analysis                     |
| 11| Existing annual premium total      | Drives the affordability check              |
| 12| CPF balances (OA / SA / MA)        | Drives the CPF optimisation step            |
| 13| Liquid savings / emergency fund    | Drives the cashflow step                    |
| 14| Investment assets (outside CPF)    | Drives the "Step 9 — growth" lane           |
| 15| Risk profile result                | Conservative / Balanced / Aggressive        |
| 16| Time horizon for major goals       | Retirement age, kids' education, etc.       |

If **any of 1–11 is missing**, the skill must **state the assumption**
at the top of the report and proceed. Items 12–16 are best-effort.

## 5. CM-LIP product taxonomy (M9A-aware)

The four core life-insurance product types (CM-LIP), with the M9A
classification:

| Type        | Cash value? | Premium pattern       | M9A class | Typical use                       |
| ----------- | ----------- | --------------------- | --------- | --------------------------------- |
| **Term Life** | No          | Level or increasing   | Pure protection | Cover Death/TPD gap cheaply    |
| **Whole Life**| Yes (guaranteed) | Level for life  | Legacy / savings | Lifetime cover + estate planning |
| **Endowment** | Yes (projected) | Level for term  | Legacy / savings | Forced savings with protection  |
| **Annuity**   | Reverse — pays out | n/a           | Decumulation | Retirement income                |

A Whole Life or Endowment in the **Investment-Legacy** bucket is a
candidate for the **surrender warning (FAA-N16 / RES5)** if the
client asks "should I surrender this?"

## 6. Risk profile mapping

The risk profile result (Conservative / Balanced / Aggressive) drives
which products are suitable per the FAA-N20 BSC:

| Profile       | Term | Whole Life | Endowment | ILP    | Comment                              |
| ------------- | ---- | ---------- | --------- | ------ | ------------------------------------ |
| Conservative  | ✅    | ✅          | ✅         | ❌      | ILP sub-fund risk fails Q2           |
| Balanced      | ✅    | ✅          | ✅         | ⚠ only | ILP allowed only with 100% capital-protected sub-fund |
| Aggressive    | ✅    | ⚠          | ❌         | ✅      | Endowment inefficient; prefer ILP + Term, or pure Term + invest the difference |

The "invest the difference" rule: if a young client can buy S$500k
Term Life for S$50/mo, vs the same cover inside a Whole Life for
S$500/mo, the S$450/mo difference can be invested in a low-cost
index fund. Over 30 years at 5% real return, the difference
compounds to S$350k+ — usually dwarfing the cash value of the
Whole Life.
