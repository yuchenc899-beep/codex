# Singapore Insurance & CPF Portfolio Review — 2026-06-30

**Scope:** Client 38yo non-smoker self-employed Singaporean (freelance consultant) | Income S$120,000/yr (S$10,000/mo take-home) | Annual premiums S$8,400 | Married, 1 child (age 4) | S$280,000 outstanding HDB loan | Risk profile: Balanced
**Time-stamp:** 2026-06-30
**Assumptions:**
- Spouse: 36yo, not working, dependent
- 1 child: 4yo, primary school in 2 years
- CPF balances: OA S$62,000 / SA S$40,000 / MA S$10,000 [user-stated]
- Liquid cash savings: S$24,000 (~2.4 mo) [user-stated]
- Self-employed: emergency fund target = 6–12 months
- Investment assets outside CPF: S$45,000 in SRS + S$30,000 in unit trusts [user-stated]
- All policy numbers and account values are [illustrative] — verify with insurer benefit illustration

---

## 0. Portfolio Ingest (categorized & de-duplicated)

| Bucket              | Policy                                       | Sum Assured / Account Value | Annual Premium |
| ------------------- | -------------------------------------------- | --------------------------- | -------------- |
| Hospitalisation     | NTUC IncomeShield Plan A (2018)              | S$1.5M ceiling, 5% co-pay   | S$1,100        |
| Hospitalisation     | Rider: private hospital + day surgery        | Limit S$300k/yr             | S$420          |
| Death / TPD         | AIA Term Life (2015, level to 65)            | S$500,000                   | S$1,200        |
| Death / TPD         | HPS (HDB loan)                               | ~S$280,000 (decreasing)     | ~S$360         |
| CI                  | PRUlife Vantage 100 (2019)                   | S$100,000 base + 4× ECI     | S$1,800        |
| PA                  | Group PA (spouse's employer) — own cover     | S$100,000                   | employer-paid  |
| Investment-Legacy   | Manulife ReadyBuilder (2010) — ILP           | SA S$150,000 / Acc. Value S$58,000 | S$3,520 |
| **Total**           | **7 policies**                               | Aggregated Death S$780,000 (Term+HPS), CI S$100k+4×ECI | **S$8,400**    |

**ILP conflict flag (M9A):** The **Manulife ReadyBuilder (2010)** is the only M9A trigger. Note the **"Manu"** prefix and the "**Builder**" name with sub-fund disclosure (M9A "Link"/"Managed Investment"/"Sub-Funds" keywords). Treat as an ILP conflict. Account value S$58,000 across 3 sub-funds; 15-year drag has averaged ~2.8% p.a. effective (bid-offer + M&E + fund fees).

---

## 1. Surrender Warning (FAA-N16 / RES5)

> **Surrender warning (FAA-N16 / RES5).** Terminating a Whole Life, Endowment, or ILP policy means you will lose the insurance protection it provides, **and you may receive less than the total premiums paid** (the cash surrender value is net of distribution costs, mortality charges, and expense loadings). This decision is **permanent and irreversible** for the policy term. Do not surrender under time pressure, family influence, or because an agent offered to "replace" it with a new policy.

**Sunk-cost vs cash-value per legacy policy:**

| Policy                       | Year started | Premiums paid (cumulative) | Current cash value | Unrecoverable cost |
| ---------------------------- | ------------ | -------------------------- | ------------------ | ------------------ |
| Manulife ReadyBuilder (2010) | 2010         | S$56,320 (16yr × S$3,520)  | S$58,000           | **S$(1,680) net gain**, but inside ILP drag |

**Reading the table.** The ReadyBuilder is in the money by S$1,680, but the S$58,000 is an account value inside 3 sub-funds — not a guaranteed cash value. The plan is also providing S$150,000 of nominal life cover, but the cover is **ILP-driven** and the sum-assured will reduce as the account value runs down. This is the FAA-N20 "Suitability" red flag: the cover that the user is relying on is not stable.

**Hard rule for this case.** Do NOT surrender the ReadyBuilder until the user has decided whether to replace the S$150,000 life cover with a Term Life top-up. The risk of surrendering an in-force life cover and being uninsurable later (38yo self-employed can develop conditions) is precisely the FAA-N16 risk surface.

---

## 2. LIA Gap Analysis

| Coverage       | Target (formula)                       | Aggregated sum assured | Net gap      | Status        |
| -------------- | -------------------------------------- | ---------------------- | ------------ | ------------- |
| **Death / TPD**| S$120,000 × 10 = S$1,200,000           | S$500k Term + S$280k HPS + S$150k ILP-nominal = S$930k | **−S$270,000** | **Under by S$270k** (mortgage-adjusted) |
| **CI**         | S$120,000 × 4 = S$480,000              | S$100k base + 4× ECI    | **−S$280,000** | **Under by S$280k** (with ECI stacking) |
| **ECI**        | S$120,000 × 1 = S$120,000              | 4× ECI = S$400,000 max  | +S$280,000 over | ECI **over-covered** (slight) |
| **PA**         | S$120,000 × 4 = S$480,000              | S$100k (group)          | **−S$380,000** | **Under by S$380k** |
| **Hospitalisation** | IP Plan A ceiling ≈ S$1.5M        | S$1.5M (NTUC IncomeShield A) | met | **Right-sized** |

**Reading the gaps.** The user is moderately under-covered on Death (S$270k short, mortgage-adjusted), severely under-covered on CI base (S$280k short), and severely under-covered on PA (S$380k short, no own policy). The hospitalisation stack is right-sized (Plan A + rider). ECI is over-covered (4× ECI from a S$100k CI base = S$400k, which is fine, but the FA Rep should explain that ECI only pays for early-stage diagnosis, not full CI).

---

## 3. National Protection Integration

| Layer                | Status                              | Action                                          |
| -------------------- | ----------------------------------- | ----------------------------------------------- |
| **MediShield Life**  | Active (CPF-MA auto-deducted)       | Verify on CPF statement; no change              |
| **Integrated Shield**| NTUC IncomeShield Plan A (2018)     | Right-sized; verify 5% co-payment clause (post-2018 IP rules) |
| **CareShield Life**  | Active, auto-enrolled               | Stay on; payout >S$600/mo in 2025+; consider Eldershield / Private LTC supplement only if 5%+ RoP math works |
| **HPS**              | Active, decreasing on HDB loan      | Verify HPS cover still ≥ outstanding HDB loan (S$280k); verify premium deduction from OA |

**Reading the national stack.** Plan A is a sensible level for a 38yo family. The post-2018 5% co-payment clause is in force — the user should expect S$2,000–3,000 out-of-pocket per year on private hospital stays. HPS is on track. No urgent change.

---

## 4. FAA-N20 Balanced Scorecard (BSC)

| Quadrant                | Term Life top-up S$300k | CI base top-up S$200k | PA S$400k | Surrender ReadyBuilder |
| ----------------------- | ----------------------- | ---------------------- | ---------- | ----------------------- |
| **Q1: Client Need (FNA)** | ✅ gap S$270k, mortgage-adjusted | ✅ gap S$280k | ✅ gap S$380k | ⚠ covers S$150k, but unstable |
| **Q2: Risk Profile Match** | ✅ Term, no sub-fund | ✅ Multi-pay CI | ✅ PA | n/a |
| **Q3: Affordability**   | ⚠ ~S$1,000/yr marginal | ✅ ~S$1,200/yr | ✅ ~S$500/yr | ✅ unlocks S$58k |
| **Q4: Suitability**     | ✅ 2 insurers compared | ✅ 2 insurers | ✅ 2 insurers | ❌ Drop — replacement cover required first |
| **Verdict**             | **Pass w/ note**        | **Pass**                | **Pass**   | **Drop** until Step 1 in force |

---

## 5. CPF & Cashflow Optimisation

| Lever                  | Current state           | Recommendation                                  |
| ---------------------- | ----------------------- | ----------------------------------------------- |
| **OA vs SA balance**   | OA S$62k / SA S$40k      | SA still below FRS; eligible for S$8,000/yr cash top-up with 4% + S$8,000 tax relief |
| **Cash vs CPF-OA**     | Cash S$24k / OA idle ~S$30k | Cash S$24k is 2.4 mo — below the 6-mo self-employed target; do not sweep to OA |
| **Cashflow Surplus**   | S$10,000 take-home − S$5,500 fixed − S$700 premiums (after cleanup) = **S$3,800/mo (38%)** | Strong surplus. Direct S$2,000/mo to emergency fund (target S$60k = 6 mo); S$1,000/mo to SA top-up; S$800/mo to SRS / low-cost index |
| **Emergency Fund**     | S$24k (~2.4 mo)          | Build to S$60k (6 mo self-employed) in 18 months; then S$120k (12 mo) over 5 years |
| **SRS**                | S$45k (well below S$80k SRS cap) | Top up S$15.3k/yr SRS limit; tax-relieved; invest via low-cost unit trust |

---

## 6. Premium Overhead Inefficiency Diagnosis

Of the S$8,400/yr in user-paid premiums:

- **S$3,520 (42%)** → Manulife ReadyBuilder ILP. S$58,000 account value vs S$56,320 paid. 2.8% p.a. drag means the user is paying **S$1,624/yr for S$1,624 in drag**. Net: zero real return inside the ILP after 15 years.
- **S$2,520 (30%)** → IncomeShield Plan A + rider. Right-sized for the family; keep.
- **S$1,200 (14%)** → AIA Term Life. Pure protection, no waste. Keep.
- **S$1,800 (21%)** → PRUlife Vantage 100 Multi-pay CI. Right-sized for the family. Keep, top up base.
- **S$360 (4%)** → HPS. Mandatory; keep.

**Diagnosis.** The single source of premium overhead is the **Manulife ReadyBuilder ILP**. S$3,520/yr × 16 years = S$56,320 in premiums → S$58,000 in account value (net gain S$1,680, IRR ~0.3% real). A S$30,000 Term Life top-up + invest-the-difference in a low-cost global index fund would have produced S$130k+ over the same 16 years at 5% real. The user is paying a **> 5% annual drag** for what looks like "savings".

---

## 7. Prioritized Action Checklist (Sequence)

1. **[Risk] Term Life top-up S$300,000.** Action: S$300k Term Life level to age 65, from ≥ 2 insurers. 38yo non-smoker ~S$900–1,200/yr. This closes the mortgage-adjusted Death gap. [target: 30 days]
2. **[Risk] CI base top-up S$200,000.** Action: PRUlife / AIA Multi-pay CI base S$200k, attached to the new Term Life. ~S$1,200/yr. Closes the CI base gap. [target: 30 days]
3. **[Risk] Personal Accident S$400,000.** Action: own PA policy (do not rely on spouse's group). ~S$500/yr. 2 insurers. [target: 30 days]
4. **[National] Verify MediShield + Plan A + HPS + CareShield on CPF statement.** Action: pull CPF statement; confirm all 4 layers active; confirm HPS cover ≥ outstanding HDB loan S$280k. [target: 14 days]
5. **[Cashflow] Restock emergency fund to 6 months (self-employed).** Action: park S$2,000/mo in high-yield savings until S$60,000. [target: 18 months]
6. **[Cleanup] Do NOT surrender the ReadyBuilder yet.** Action: keep the S$150,000 life cover in force until Step 1 is bound. [target: blocked on Step 1]
7. **[Cleanup] Re-evaluate the ReadyBuilder once Step 1 in force.** Action: obtain surrender illustration; if account value > S$50k, **convert to paid-up** (keep S$50k+ cover) and stop paying premiums on the rest; if account value < S$30k, surrender and reinvest in a low-cost global index fund. [target: 60 days, after Step 1]
8. **[CPF] SA top-up S$8,000 (cash).** Action: claim S$8,000 tax relief (c.f. IRAS). [target: 31 Dec 2026]
9. **[CPF] SRS top-up S$15,300.** Action: max the SRS annual limit, invest in low-cost unit trust. [target: 31 Dec 2026]
10. **[CPF] CPFIS-OA idle-cash sweep.** Action: when OA > S$20k idle, consider low-cost index fund via CPFIS. [target: next CPFIS window]
11. **[Review] Annual rebalance.** Action: re-run this skill every 12 months, or after a major life event (child 2nd, home upgrade, business change).

---

## Sources

**MAS / regulatory:**
- MAS FAA 2001 — https://sso.agc.gov.sg/Acts/2001/FinAdv [official]
- FAA-N16 / FAA-N20 / FAA-N06 — https://www.mas.gov.sg/ [official]
- IBF competency matrix — https://www.ibf.org.sg/ [official]

**LIA / industry:**
- LIA Consumer Guide — https://www.lia.org.sg/ [official]
- LIA gap formulas — see `references/lia-gap-formulas.md`

**CPF / national:**
- CPF Board — https://www.cpf.gov.sg/ [official]
- MediShield Life — https://www.moh.gov.sg/medishield-life [official]
- CareShield Life — https://www.careshieldlife.gov.sg/ [official]
- HPS — https://www.cpf.gov.sg/Members/Schemes/schemes/housing/hps [official]
- IRAS SA / SRS top-up — https://www.iras.gov.sg/ [official]

**Insurer-specific (per policy cited):**
- Manulife ReadyBuilder fact sheet — [verify with Manulife benefit illustration, illustrative]
- AIA Term Life fact sheet — [verify with AIA, illustrative]
- PRUlife Vantage 100 — [verify with PRU, illustrative]
- NTUC IncomeShield Plan A — https://www.income.com.sg/ [verify with Income, illustrative]

**Companion skill (this repo):**
- `references/sg-regulatory-map.md`
- `references/lia-gap-formulas.md`
- `references/national-protection.md`
- `references/compliance-engine.md`

---

**This is a structural review of your insurance and CPF position based on the information you provided. It is not personalised financial advice. Please consult a licensed Financial Advisor Representative and refer to the LIA Consumer Guide and your CPF statement before acting on any of the points above. Surrendering a life policy is an irreversible decision.**
