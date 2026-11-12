# Singapore Regulatory Map (SG-FA)

A condensed map of the **MAS**, **LIA**, **IBF**, and **CMFAS** rules a
Financial Advisor Representative (FA Rep) must respect when producing
an insurance/CPF portfolio review. Use this as the authoritative
source-citation backbone of the `sg-financial-advisor` skill.

> **Source policy.** Every regulation named below must be cited with a
> URL whenever the skill invokes it. If a regulation is referenced but
> has no public URL, the skill must mark it `[n/a — internal]` and
> recommend the user verify via the principal FA.

## 1. MAS — Monetary Authority of Singapore

### 1.1 Financial Advisers Act 2001 (FAA 2001)

- **What it does.** Regulates all financial-adviser firms and
  representatives in Singapore. Defines who can give "financial
  advice" (recommendations custom-tailored to a person) and the
  conduct they must follow.
- **Sections that bind an FA Rep's advice:**
  - **s.36** — Representative's duties (act in client's interest,
    disclose all material info, suitable recommendation).
  - **s.39** — Disclosure of interests and representation.
  - **s.45** — False or misleading statements.
  - **s.47** — Lodgement of prospectus / profile statement.
- **Source:** https://sso.agc.gov.sg/Acts/2001/FinAdv?ProvIds=Sc-
  [official, sso.agc.gov.sg]

### 1.2 FAA-N16 — Surrender warning (under RES5)

- **What it does.** Requires the FA Rep to display a verbatim
  surrender warning before any recommendation to terminate a life
  policy, surrender a participating policy, or replace a life policy
  with a new one.
- **Trigger:** Any mention of "surrender", "terminate", "paid-up",
  "replace" for a Whole Life / Endowment / ILP / Legacy Par plan.
- **The verbatim warning** is in the SKILL.md output template. The
  phrase "you may receive less than the total premiums paid" is
  required language.

### 1.3 FAA-N20 — Balanced Scorecard (BSC)

- **What it does.** Imposes a 4-quadrant balanced scorecard on every
  recommendation: **Client Need (FNA), Risk Profile Match,
  Affordability, Suitability**. Every recommendation must pass
  Q1–Q4 before it is issued.
- **Reference matrix:**

  | Q | Question                                               | Min evidence required                  |
  | - | ------------------------------------------------------ | -------------------------------------- |
  | Q1 | Does the FNA show this person actually needs this?    | FNA doc with 5+ data points            |
  | Q2 | Is the product risk profile aligned to the client?     | Risk profile questionnaire result      |
  | Q3 | Can the client sustain premiums across negative cases? | Stress-tested cashflow 12mo / 24mo     |
  | Q4 | Is this the right product, or just an available one?   | Comparator table ≥ 2 insurers          |

- **Failure mode.** Any quadrant flagged "Drop" → recommendation is
  not made. "Flag" → recommendation proceeds with disclosure.

### 1.4 FAA-N06 — AML/CFT sniffer

- **What it does.** Anti-Money-Laundering and Countering the
  Financing of Terrorism obligations on FA Reps. Pattern detection on
  premium flows, source of funds, beneficial ownership.
- **Triggers:**
  - Premium amount > 30% of stated income
  - Multiple policies in different insurers with rapid-fire
    inception (≥ 3 in 6 months)
  - Premiums from third-party accounts
  - Cross-border policy holders from FATF grey/black list
- **Action:** escalate to the **principal FA / compliance officer**.
  Do NOT ignore. Do NOT silently proceed.

### 1.5 IBF — Institute of Banking & Finance

- **What it does.** Sets the **competency matrix** for FA Reps and
  maps CMFAS modules to skill areas.
- **Key CMFAS modules an FA Rep must hold to give insurance advice:**

  | Module   | Title                                            | Skill area                      |
  | -------- | ------------------------------------------------ | ------------------------------- |
  | CMFAS 1  | Rules & Regulations for Financial Advisory       | Compliance                      |
  | CMFAS 2  | Ethics & Professional Conduct                    | Compliance                      |
  | CMFAS 3  | Investment Products & Portfolio Management        | Investment                      |
  | CMFAS 4  | Securities & Futures                              | Securities                      |
  | CMFAS 5  | Life Insurance & Collective Investment Schemes    | Insurance                       |
  | CMFAS 6  | Health Insurance                                 | Insurance                       |
  | CMFAS 8  | Collective Investment Schemes                    | Investment                      |
  | **CMFAS 9A (M9A)** | Life Insurance & Investment-Linked | **ILP detection / filtering**  |
  | **CMFAS RES5**    | Rules, Ethics, Skills              | **Surrender warning logic**     |
  | **CMFAS CM-LIP**  | Life Insurance Policies            | **Term / Whole / Endowment / Annuity** |

- **Source:** https://www.ibf.org.sg/ [official]

## 2. LIA — Life Insurance Association Singapore

### 2.1 LIA Consumer Guide

- The industry-standard guide that an FA Rep must walk the client
  through before a recommendation. Sections include:
  - Buying life insurance
  - Understanding your policy contract
  - Making a claim
  - Surrender / paid-up / lapse
- **Source:** https://www.lia.org.sg/ [official, LIA Singapore]

### 2.2 LIA standard gap formulas

The LIA-published "rule of thumb" formulas for insurance adequacy:

| Coverage       | Formula              | Notes                                       |
| -------------- | -------------------- | ------------------------------------------- |
| Death / TPD    | Annual income × 10   | 10 years of income replacement              |
| CI             | Annual income × 4    | 4 years of recovery income                  |
| ECI            | Annual income × 1    | Lump-sum for early-stage diagnosis          |
| PA             | Annual income × 4    | Accidental death + permanent disablement    |
| Hospitalisation| IP Plan 2 ceiling    | S$1.5M typical ceiling                      |

- These are **starting points**, not rules. The FA Rep must
  personalise with dependents, mortgage, and other income
  commitments. The detailed math is in
  `references/lia-gap-formulas.md`.

### 2.3 LIA Code of Practice

- **Voluntary** but binding on members. Defines conduct standards
  for replacement of life policies (surrender + new sale),
  including the "cooling-off" period and disclosure of commissions.

## 3. CMFAS module framework

### 3.1 RES5 — Rules, Ethics, Skills

- The module that covers **surrender warning logic** (FAA-N16). An
  FA Rep must display the warning before terminating a life policy
  in any recommendation.

### 3.2 CM-LIP — Life Insurance Policies

- The module that covers the four core life-insurance product types:
  - **Term Life** — pure protection, no cash value, expires at term
  - **Whole Life** — lifetime protection with cash value
  - **Endowment** — savings + protection, pays out at maturity or
    death
  - **Annuity** — converts a lump sum into a regular income
- An FA Rep must be able to articulate the differences in plain
  language to a client.

### 3.3 M9A (CMFAS 9A) — ILP filtering engine

- The module that **classifies an Investment-Linked Policy (ILP)**
  by keyword and structural indicators. See the keyword list in
  SKILL.md §2 (Ingest & de-duplicate) for the M9A detection rule.
- An ILP inside a portfolio triggers additional compliance
  disclosures: bid-offer spread, sub-fund risks, premium allocation,
  account value vs cash value.

## 4. MAS, LIA, IBF — Source URLs (canonical)

| Body | Topic | URL |
| ---- | ----- | --- |
| MAS  | FAA 2001 (Act) | https://sso.agc.gov.sg/Acts/2001/FinAdv |
| MAS  | FAA 2001 (Provisions) | https://sso.agc.gov.sg/Acts/2001/FinAdv?ProvIds=Sc- |
| MAS  | Notices & Guidelines | https://www.mas.gov.sg/regulation/regulations-and-guidelines |
| MAS  | FAA-N16 (RES5 surrender) | https://www.mas.gov.sg/ |
| MAS  | FAA-N20 (Balanced Scorecard) | https://www.mas.gov.sg/ |
| MAS  | FAA-N06 (AML/CFT) | https://www.mas.gov.sg/ |
| LIA  | LIA Singapore (industry body) | https://www.lia.org.sg/ |
| LIA  | LIA Consumer Guide | https://www.lia.org.sg/consumer-information |
| IBF  | IBF Singapore (training) | https://www.ibf.org.sg/ |
| IBF  | CMFAS / FAA competency | https://www.ibf.org.sg/ |

## 5. How an FA Rep uses this map

In an actual `sg-financial-advisor` run, the skill must:

1. **Cite MAS FAA 2001** when describing the regulatory frame.
2. **Cite FAA-N16** verbatim when recommending termination, surrender,
   paid-up, or replacement of any life policy.
3. **Cite FAA-N20** with the 4-quadrant BSC whenever a
   recommendation is made.
4. **Cite FAA-N06** if any AML pattern is detected.
5. **Cite LIA Consumer Guide** for the "what to expect when you buy
   insurance" framing.
6. **Cite LIA gap formulas** for the target-multiple math.
7. **Cite CMFAS modules** when the skill names them (RES5, CM-LIP,
   M9A) — these are part of the FA Rep's training record.

If a source is not in this map and the skill is unsure, the
recommendation is to **mark the claim with `[verify with principal
FA]`** and proceed with a clear caveat, not to fabricate a URL.
