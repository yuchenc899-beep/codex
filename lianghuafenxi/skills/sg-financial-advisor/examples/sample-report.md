# Singapore Insurance & CPF Portfolio Review — 2026-06-30

**Scope:** Client 29yo non-smoker employed Singaporean | Income S$60,000/yr (S$5,000/mo) | Annual premiums S$5,747 | Single, no kids, no mortgage | Risk profile: Balanced
**Time-stamp:** 2026-06-30
**Assumptions:**
- Annual income: S$60,000 gross = S$5,000/mo take-home after CPF + tax
- CPF balances: OA S$45,000 / SA S$28,000 / MA S$8,000 [user-stated]
- Liquid cash savings: S$12,000
- Outstanding debts: none
- Risk profile: Balanced (default for FNA when not specified)
- Existing medical shields: MediShield Life auto-deducted; no IP upgrade; no CareShield opt-out
- All policy numbers and account values are [illustrative] — verify with insurer benefit illustration

---

## 0. Portfolio Ingest (categorized & de-duplicated)

| Bucket              | Policy                                       | Sum Assured / Account Value | Annual Premium |
| ------------------- | -------------------------------------------- | --------------------------- | -------------- |
| Hospitalisation     | MediShield Life (CPF-MA auto)               | Catastrophic, S$150k/yr     | ~S$430 [illustrative]|
| Death / TPD         | Group Term Life (employer, 24× salary)      | S$120,000                   | employer-paid  |
| CI                  | Group Early CI rider (employer)              | S$24,000                    | employer-paid  |
| PA                  | —                                            | 0                           | 0              |
| Investment-Legacy   | GE WholeLife Premier (1997, parent-owned)    | SA S$50,000 / Cash Value S$18,000 | S$1,800 (user-paid since 2018) |
| Investment-Legacy   | GE GreatLink Supreme (2001)                  | SA S$100,000 / Acc. Value S$42,000 | S$1,440 |
| Investment-Legacy   | **GE GreatLink FlexiPlan (2014)** ⚠ ILP flag | SA S$200,000 / Acc. Value S$31,000 | S$2,077 |
| **Total**           | **7 policies**                              | Aggregated Death S$270,000  | **S$5,747**    |

**ILP conflict flag (M9A):** The **GE GreatLink FlexiPlan (2014)** triggers the M9A filter on three independent keywords — "Great**Link**" (Link), "**Flexi**Plan" (Flexi), and the product disclosure references "**Sub-Funds**" and "**Premium Allocation**". Treat as an ILP conflict. Account value of S$31,000 is held across 4 sub-funds; bid-offer spread on every premium allocation, M&E charges deducted monthly, plus 0.85–1.50% p.a. fund management fee on the sub-funds.

**Net premiums situation:** Of the S$5,747/yr in user-paid premiums, S$5,317 (~92%) goes to three Investment-Legacy plans, S$430 goes to MediShield Life (national floor), and the user relies on the employer for Term and CI. This is the **Premium Overhead Inefficiency** that defines the case.

---

## 1. Surrender Warning (FAA-N16 / RES5)

> **Surrender warning (FAA-N16 / RES5).** Terminating a Whole Life, Endowment, or ILP policy means you will lose the insurance protection it provides, **and you may receive less than the total premiums paid** (the cash surrender value is net of distribution costs, mortality charges, and expense loadings). This decision is **permanent and irreversible** for the policy term. Do not surrender under time pressure, family influence, or because an agent offered to "replace" it with a new policy.

**Sunk-cost vs cash-value per legacy policy:**

| Policy                       | Year started | Premiums paid (cumulative) | Current cash value | Unrecoverable cost |
| ---------------------------- | ------------ | -------------------------- | ------------------ | ------------------ |
| GE WholeLife Premier (1997)  | 1997         | S$52,200 (29yr × S$1,800)  | S$18,000           | **S$34,200 unrecovered** |
| GE GreatLink Supreme (2001)  | 2001         | S$36,000 (25yr × S$1,440)  | S$42,000           | **S$(6,000) net gain** |
| GE GreatLink FlexiPlan (2014)| 2014         | S$24,924 (12yr × S$2,077)  | S$31,000           | **S$(6,076) net gain**, but inside ILP drag |

**Reading the table.** The 1997 WholeLife is still underwater by S$34,200 (cash value has not yet recovered the 29 years of distribution cost + mortality charges). The 2001 and 2014 plans are nominally in the money, but the FlexiPlan's "gain" is inside an ILP account value subject to sub-fund market risk — it is not a guaranteed cash value.

**Hard rule for this case.** Do NOT touch the 1997 WholeLife until the user has Term + CI cover in force (Step 1–2 of the action checklist). The risk of holding a S$50,000 sum-assured policy with no replacement cover, while debating surrender, is precisely the kind of bad outcome the FAA-N16 warning exists to prevent.

---

## 2. LIA Gap Analysis

| Coverage       | Target (formula)                       | Aggregated sum assured | Net gap      | Status        |
| -------------- | -------------------------------------- | ---------------------- | ------------ | ------------- |
| **Death / TPD**| Income S$60,000 x 10 = S$600,000 (LIA standard) | S$270,000 (group + 3 legacy) | **−S$330,000** | **Under by S$330k** |
| **CI**         | Income S$60,000 x 4 = S$240,000 (LIA standard)  | S$24,000 (group only)  | **−S$216,000** | **Under by S$216k** |
| **ECI**        | Income S$60,000 x 1 = S$60,000 (LIA standard)   | 0                      | **−S$60,000**  | **Zero cover**|
| **PA**         | Income S$60,000 x 4 = S$240,000 (LIA standard)  | 0                      | **−S$240,000** | **Zero cover**|
| **Hospitalisation** | IP Plan 2 ceiling ≈ S$1,500,000   | MediShield Life only   | n/a          | Floor; upgrade optional |

**Reading the gaps.** The user is **systemically under-protected**. The aggregate Death cover is S$270,000 vs a target of S$600,000; the gap is S$330,000. The CI cover is even worse — S$24,000 (employer group, ends on job change) vs S$240,000 target. There is **zero ECI and zero PA cover**. The user is paying S$5,747/yr into legacy plans whose combined death cover (S$350,000 nominal, of which S$200,000 is inside an ILP's "account value" and not a true sum-assured) is still below the LIA × 10 target.

**The trap.** Of the S$5,747/yr in premiums, **92% goes to Investment-Legacy plans that do not close the gap.** A S$500,000 Term Life (level to age 65) costs ~S$600–800/yr for a 29yo non-smoker. A S$200,000 Multi-pay CI rider costs ~S$500–700/yr. The user could close the entire Death + CI gap for ~S$1,200/yr, releasing ~S$4,500/yr for CPF / savings / investment.

---

## 3. National Protection Integration

| Layer                | Status                              | Action                                          |
| -------------------- | ----------------------------------- | ----------------------------------------------- |
| **MediShield Life**  | Active (CPF-MA auto-deducted)       | Verify annual premium on CPF statement; no change |
| **Integrated Shield**| None — MediShield Life only         | Optional upgrade to IP Plan 2 (Class A, 5% co-pay) only if private specialist is a need; recommend staying on MediShield for now given the cashflow priority |
| **CareShield Life**  | Auto-enrolled, no opt-out           | Stay on; default payout >S$600/mo in 2025+; opt-out is irreversible, do not recommend |
| **HPS**              | n/a — no HDB loan                   | n/a                                            |

**Reading the national stack.** The user is on the floor for all 4 layers. No upgrade is urgent. CareShield Life is a floor that should not be opted out of; MediShield Life + Catastrophic cover is enough for a 29yo single, especially with the cashflow priority. **Do not touch the national stack while fixing the legacy plan mess.**

---

## 4. FAA-N20 Balanced Scorecard (BSC)

The skill ran the BSC on each candidate recommendation. Verdict matrix:

| Quadrant                | Term Life S$500k  | CI Rider S$200k | ECI Rider S$60k | PA S$240k | Surrender 1997 WL | Surrender 2014 FlexiPlan |
| ----------------------- | ----------------- | --------------- | ---------------- | --------- | ----------------- | ------------------------ |
| **Q1: Client Need (FNA)** | ✅ gap S$330k     | ✅ gap S$216k   | ✅ gap S$60k     | ✅ gap S$240k | ⚠ covered partially by S$50k SA | ✅ FNA shows Premium Overhead |
| **Q2: Risk Profile Match** | ✅ Term, no sub-fund | ✅ Multi-pay CI | ✅ Multi-pay ECI | ✅ PA     | n/a (not a purchase) | n/a (not a purchase) |
| **Q3: Affordability**   | ✅ ~S$700/yr      | ✅ ~S$600/yr    | ⚠ marginal       | ✅ ~S$300/yr | ✅ unlocks S$18k cash value | ✅ unlocks S$31k Acc. Value |
| **Q4: Suitability**     | ✅ 2 insurers compared | ✅ 2 insurers compared | ✅ 2 insurers | ✅ 2 insurers | ❌ Drop — premature without replacement cover | ✅ Pass — keep S$200k Term in force, surrender only the ILP shell |
| **Verdict**             | **Pass**          | **Pass**         | **Pass w/ note** | **Pass**  | **Drop**           | **Pass w/ note** (after Step 1–2 in force) |

**Reading the BSC.** All four purchase recommendations pass. The 1997 WholeLife surrender is **Drop** because Q4 fails (no replacement cover in force). The 2014 FlexiPlan surrender **passes with note**: do not surrender until the new Term + CI are in force, and the FA Rep must walk the client through the bid-offer spread, M&E charges, and sub-fund market risk first.

---

## 5. CPF & Cashflow Optimisation

| Lever                  | Current state           | Recommendation                                  |
| ---------------------- | ----------------------- | ----------------------------------------------- |
| **OA vs SA balance**   | OA S$45,000 / SA S$28,000 | OA healthy. SA below FRS — eligible for S$8,000/yr cash top-up with 4% p.a. (FRS) + S$8,000 tax relief (c.f. IRAS) |
| **Cash vs CPF-OA**     | Cash S$12,000 / OA idle S$20k | Cash S$12,000 is < 3 mo take-home; do NOT sweep to OA until emergency fund is restocked to S$15,000 |
| **Cashflow Surplus**   | S$5,000 take-home − S$2,500 fixed − S$479 premiums (after Step 1–2 in force) = **S$2,021/mo (40%)** | Strong surplus once legacy premiums are reduced. Direct S$1,000/mo to emergency fund top-up; S$1,000/mo to SA top-up / low-cost index fund |
| **Emergency Fund**     | S$12,000 (≈ 2.4 mo)     | Build to S$15,000 (3 mo) in next 3 months; then S$30,000 (6 mo) in 18 months |

**Reading the cashflow picture.** Once the legacy plans are cleaned up, the user has a **40% cashflow surplus** — one of the most powerful positions a 29yo Singaporean can be in. The trap is to over-deploy the surplus into ILPs or new Whole Life plans. The right play is: restock the emergency fund → top up SA → invest the rest in a low-cost global index fund via a brokerage or CPFIS-OA.

---

## 6. Premium Overhead Inefficiency Diagnosis

The user is paying **S$5,747/yr in insurance premiums** for **S$270,000 of nominal death cover** and **S$24,000 of CI cover** (the rest is group cover that ends on job change). Of the S$5,747:

- **S$1,800 (31%)** → 1997 GE WholeLife Premier. Cash value S$18,000 vs S$52,200 paid. **Unrecovered: S$34,200**. SA: S$50,000.
- **S$1,440 (25%)** → 2001 GE GreatLink Supreme. Cash value S$42,000 vs S$36,000 paid. **In the money by S$6,000**, but cash value is held inside participating-fund rules.
- **S$2,077 (36%)** → 2014 GE GreatLink FlexiPlan. Account value S$31,000 vs S$24,924 paid. **In the money by S$6,076**, but **inside an ILP** with 3–5% p.a. all-in drag (bid-offer + M&E + fund fees).
- **S$430 (8%)** → MediShield Life. The right amount for a 29yo floor.

**Diagnosis: Premium Overhead Inefficiency.** ~92% of the user's premium dollars are going to Investment-Legacy products that close < 40% of the LIA Death gap and zero of the CI / ECI / PA gap. The user is paying S$5,317/yr for an effective death cover of S$270k that they could replace with S$700/yr of Term + S$1,200/yr of Multi-pay CI + S$300/yr of PA. The annual saving is **S$3,800+** — enough to retire the emergency fund in 8 months and start an SA top-up programme.

---

## 7. Prioritized Action Checklist (Sequence)

1. **[Risk] Close the Death / TPD gap (S$330k under).** Action: Get a S$500,000 Term Life quote, level premium to age 65, from ≥ 2 insurers (AIA, PRU, GE, NTUC Income). 29yo non-smoker expected ~S$600–800/yr. Verify medical underwriting. [target: 30 days]
2. **[Risk] Close the CI / ECI gap (S$216k under / S$60k zero).** Action: Multi-pay CI rider S$200k base + 4× ECI early payout, attached to the new Term Life, from the same insurer. ~S$600–700/yr for a 29yo non-smoker. [target: 30 days]
3. **[Risk] Add a Personal Accident policy (S$240k zero).** Action: S$240k PA cover, ~S$300/yr. 2 insurers. [target: 30 days]
4. **[National] Verify MediShield Life + CareShield Life on CPF statement.** Action: pull the latest CPF statement, confirm MA deduction for MediShield (~S$430/yr at 29), confirm CareShield Life premium is being deducted (~S$200/yr at 29). [target: 14 days]
5. **[Cashflow] Restock emergency fund to 3 months.** Action: park S$1,000/mo in a high-yield savings account (MariBank 2.5%, GXS 2.0%, UOB One 1.5%) until S$15,000. [target: 3 months]
6. **[Cleanup] Do NOT surrender the 1997 WholeLife yet.** Action: do nothing on the 1997 plan until Step 1–3 are in force. S$50,000 sum-assured is the only guaranteed-death-cover the user has. [target: blocked on Step 1–3]
7. **[Cleanup] Re-evaluate the 1997 WholeLife once Step 1–3 in force.** Action: obtain surrender illustration from GE; run the sunk-cost math; compare "surrender + invest the difference" vs "paid-up + hold for estate". Decision rule: if cash value < premiums paid AND no estate need, surrender; if cash value > premiums paid OR estate need, hold. [target: 60 days, after Step 1–3]
8. **[Cleanup] Surrender the 2014 GreatLink FlexiPlan ONLY after walking the M9A disclosure.** Action: obtain surrender illustration (S$31k Account Value minus surrender charge); obtain bid-offer spread history; obtain 5-year M&E + fund-fee drag summary. After the FAA-N20 BSC re-confirms the recommendation, surrender and reinvest the S$30k+ into a low-cost global index fund (e.g. VWRA, CSPX via IBKR / Syfe / Endowus). [target: 90 days, after Step 1–3]
9. **[Cleanup] Hold the 2001 GreatLink Supreme as paid-up.** Action: convert to paid-up at the next policy anniversary. The S$42,000 cash value is in the money; the cost of the SA (S$100k) is already paid for. [target: next anniversary]
10. **[CPF] SA top-up S$8,000 (cash).** Action: claim tax relief up to S$8,000/yr (c.f. IRAS); verify FRS still below. [target: 31 Dec 2026]
11. **[CPF] CPFIS-OA idle-cash sweep.** Action: if OA > S$20,000 idle after emergency fund is built, consider low-cost index fund (e.g. ABF SG Bond Index) via the CPF Investment Scheme. [target: next CPFIS window]
12. **[Review] Annual rebalance.** Action: re-run this skill every 12 months, or after a major life event (marriage, child, home purchase). Re-evaluate HPS once an HDB loan is taken.

---

## Sources

**MAS / regulatory:**
- MAS FAA 2001 — https://sso.agc.gov.sg/Acts/2001/FinAdv [official, sso.agc.gov.sg]
- FAA-N16 (RES5 surrender warning) — https://www.mas.gov.sg/ [official, mas.gov.sg]
- FAA-N20 (Balanced Scorecard) — https://www.mas.gov.sg/ [official, mas.gov.sg]
- FAA-N06 (AML/CFT) — https://www.mas.gov.sg/ [official, mas.gov.sg]
- IBF competency matrix — https://www.ibf.org.sg/ [official, ibf.org.sg]

**LIA / industry:**
- LIA Consumer Guide — https://www.lia.org.sg/ [official, lia.org.sg]
- LIA gap formulas (×10 Death, ×4 CI, ×1 ECI, ×4 PA) — see `references/lia-gap-formulas.md`

**CPF / national:**
- CPF Board — https://www.cpf.gov.sg/ [official, cpf.gov.sg]
- MediShield Life — https://www.moh.gov.sg/medishield-life [official, moh.gov.sg]
- CareShield Life — https://www.careshieldlife.gov.sg/ [official, careshieldlife.gov.sg]
- HPS — https://www.cpf.gov.sg/Members/Schemes/schemes/housing/hps [official, cpf.gov.sg]
- IRAS SA top-up tax relief — https://www.iras.gov.sg/ [official, iras.gov.sg]

**Insurer-specific (per policy cited):**
- Great Eastern WholeLife Premier fact sheet — [verify with GE benefit illustration, illustrative]
- Great Eastern GreatLink Supreme — [verify with GE benefit illustration, illustrative]
- Great Eastern GreatLink FlexiPlan — [verify with GE benefit illustration, illustrative]
- AIA, PRU, NTUC Income Term Life fact sheets — [verify with each insurer, illustrative]

**Companion skill (this repo):**
- `references/sg-regulatory-map.md` — MAS FAA, LIA, IBF, CMFAS modules
- `references/lia-gap-formulas.md` — LIA standard math, ILP detection, FNA matrix
- `references/national-protection.md` — MediShield, Integrated Shield, CareShield, HPS, CPF
- `references/compliance-engine.md` — RES5 surrender warning, FAA-N20 BSC, FAA-N06 AML

---

**This is a structural review of your insurance and CPF position based on the information you provided. It is not personalised financial advice. Please consult a licensed Financial Advisor Representative and refer to the LIA Consumer Guide and your CPF statement before acting on any of the points above. Surrendering a life policy is an irreversible decision.**
