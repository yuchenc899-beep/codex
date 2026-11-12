# Singapore Insurance Portfolio Review (Lite) — 2026-06-30

**Scope:** Client 45yo non-smoker employed Singaporean | Income S$90,000/yr | Annual premiums S$3,200 | Married, 2 kids, HDB loan fully paid | Risk profile: Conservative
**Time-stamp:** 2026-06-30
**Granularity:** Lite (Sections 0, 2, 3, 7, 8 only — omit BSC, CPF, AML for a quick verdict)

**Assumptions:** CPF balances: OA S$90k / SA S$55k / MA S$12k. Liquid cash: S$30,000 (~4 mo). No outstanding mortgage. No Investment-Legacy products. [All values illustrative]

---

## 0. Portfolio Ingest

| Bucket              | Policy                                       | Sum Assured | Annual Premium |
| ------------------- | -------------------------------------------- | ----------- | -------------- |
| Hospitalisation     | AIA HealthShield Gold Max A (2015)            | S$1.5M     | S$1,800        |
| Death / TPD         | NTUC Income Term Life (2010, level to 65)    | S$500,000   | S$900          |
| CI                  | AIA Multipay Critical Illness (2018)         | S$200,000 base + 3× ECI | S$1,200 |
| PA                  | —                                            | 0           | 0              |
| Investment-Legacy   | —                                            | —           | —              |
| **Total**           | **3 policies**                              |             | **S$2,900** (+ S$300 rider = S$3,200) |

**ILP conflict flag (M9A):** None. No Whole Life, Endowment, or ILP in the portfolio. No surrender warning required.

---

## 1. Surrender Warning (FAA-N16 / RES5)

> Not applicable — no Investment-Legacy policies in the portfolio. The RES5 surrender warning is not triggered.

---

## 2. LIA Gap Analysis

| Coverage       | Target (formula)                       | Aggregated | Net gap      | Status        |
| -------------- | -------------------------------------- | ---------- | ------------ | ------------- |
| **Death / TPD**| S$90,000 × 10 = S$900,000              | S$500,000 (Term only — HPS not needed) | **−S$400,000** | **Under by S$400k** (kids-dependent) |
| **CI**         | S$90,000 × 4 = S$360,000               | S$200,000 base | **−S$160,000** | **Under by S$160k** |
| **ECI**        | S$90,000 × 1 = S$90,000                | 3× ECI = S$600,000 max | +S$510,000 over | ECI well-covered |
| **PA**         | S$90,000 × 4 = S$360,000               | 0          | **−S$360,000** | **Zero cover** |
| **Hospitalisation** | IP Plan A ceiling ≈ S$1.5M        | S$1.5M (AIA Gold A) | met | **Right-sized** |

**Reading the gaps.** Two coverage gaps to close: **Death (S$400k under)** and **PA (S$360k under)**. CI base is also S$160k short, but ECI over-compensates for early-stage diagnosis. Hospitalisation is right-sized.

---

## 3. National Protection Integration

| Layer                | Status                              | Action                                          |
| -------------------- | ----------------------------------- | ----------------------------------------------- |
| **MediShield Life**  | Active                              | Verify on CPF statement                         |
| **Integrated Shield**| AIA HealthShield Gold Max A (2015)  | Right-sized for family; verify 5% co-payment clause (post-2018 IP rules); pre-2018 grandfathering may still apply — check the policy contract |
| **CareShield Life**  | Active                              | Stay on; default payout >S$600/mo in 2025+      |
| **HPS**              | n/a — HDB loan fully paid           | n/a                                            |

**Reading the national stack.** All layers right-sized for a 45yo family with no mortgage. No urgent national-layer change.

---

## 4. FAA-N20 BSC

*Omitted (lite variant).*

---

## 5. CPF & Cashflow

*Omitted (lite variant).*

---

## 6. Premium Overhead Inefficiency

**No ILP / Investment-Legacy drag.** All three policies are pure protection (Term + Multi-pay CI + IP). The user is paying S$3,200/yr for S$500k Term + S$200k CI + S$1.5M IP. This is **right-priced** for the cover delivered — no Premium Overhead Inefficiency detected.

---

## 7. Prioritized Action Checklist (Sequence)

1. **[Risk] Term Life top-up S$400,000.** Action: S$400k Term Life level to age 65, from ≥ 2 insurers. 45yo non-smoker ~S$1,400/yr. [target: 30 days]
2. **[Risk] Personal Accident S$400,000.** Action: own PA policy. ~S$500/yr. [target: 30 days]
3. **[Risk] CI base top-up S$200,000 (optional).** Action: S$200k CI base to bring it to S$400k. ~S$900/yr. Consider after Step 1–2. [target: 60 days]
4. **[National] Verify 5% co-payment clause on AIA HealthShield Gold Max A.** Action: pull the policy contract; if the policy is pre-March 2018 and grandfathered, no co-pay. If post-2018 rider, expect 5% co-pay on private specialists. [target: 14 days]
5. **[Review] Annual rebalance.** Action: re-run this skill every 12 months.

---

## Sources

**MAS / regulatory:** https://www.mas.gov.sg/ [official]
**LIA / industry:** https://www.lia.org.sg/ [official]
**CPF / national:** https://www.cpf.gov.sg/, https://www.careshieldlife.gov.sg/ [official]
**Insurer-specific:**
- AIA HealthShield Gold Max A — https://www.aia.com.sg/ [verify with AIA, illustrative]
- NTUC Income Term Life — https://www.income.com.sg/ [verify with Income, illustrative]
- AIA Multipay CI — https://www.aia.com.sg/ [verify with AIA, illustrative]

**Companion skill (this repo):** see `SKILL.md` references

---

**This is a structural review of your insurance and CPF position based on the information you provided. It is not personalised financial advice. Please consult a licensed Financial Advisor Representative and refer to the LIA Consumer Guide and your CPF statement before acting on any of the points above. Surrendering a life policy is an irreversible decision.**
