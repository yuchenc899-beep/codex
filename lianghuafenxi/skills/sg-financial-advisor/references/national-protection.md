# National Protection Integration

The Singapore **national protection stack** is the floor of every
portfolio review. This file is the reference for the
`sg-financial-advisor` skill's Section 3 (National Protection
Integration).

> **Position.** National protection is the **floor**, not the
> ceiling. MediShield Life + CareShield Life + HPS are baseline.
> Anything else is layered on top.

## 1. The four layers

```
+--------------------------------------+
|  Layer 4: Private supplements        |
|  (Private hospital rider, LTC rider) |
+--------------------------------------+
|  Layer 3: Integrated Shield (IP)     |
|  (Plan 1 / 2 / 3 + rider)            |
+--------------------------------------+
|  Layer 2: MediShield Life (auto)     |
|  (Catastrophic, CPF-MA deducted)     |
+--------------------------------------+
|  Layer 1: CareShield Life (auto)     |
|  (Long-term care, opt-out at 30)     |
+--------------------------------------+
```

Layer 1 and the lower half of Layer 2 are **auto-enrolled for
Singaporeans and PRs**. The skill must verify these are active and
premiums are being deducted from CPF-MA.

## 2. Layer 1 — MediShield Life

- **What.** Universal catastrophic hospital insurance for all
  Singaporeans and PRs. Auto-enrolled.
- **Coverage.** Large hospital bills at restructured hospitals
  (Class B2/C wards). Annual claim limit S$150,000. Lifetime
  unlimited.
- **Premium.** Age-banded; deducted from CPF-MA. The full premium
  can be paid by Medisave.
- **Source:** https://www.moh.gov.sg/medishield-life [official,
  moh.gov.sg]

### 2.1 What MediShield Life does NOT cover

- Private hospital stays
- Class A / B1 ward stays (only partial)
- Pre-existing conditions waiting period: 12 months for the
  condition-specific exclusion
- Private specialist outpatient care

## 3. Layer 2 — Integrated Shield Plan (IP)

- **What.** Optional private insurance that **tops up** MediShield
  Life to cover Class A/B1 wards, private hospitals, and private
  specialists.
- **Insurers.** AIA, Aviva (now HSBC Life), Great Eastern, NTUC
  Income, Prudential, Raffles Health, Singlife.
- **Plans (3 tiers).**

  | Plan | Ward | Approx premium (35yo) | Co-payment |
  | ---- | ---- | --------------------- | ---------- |
  | IP Plan 1 | Class B1 (public)         | S$300–500/yr  | 10% co-pay  |
  | IP Plan 2 | Class A (public)          | S$700–1,200/yr| 10% co-pay  |
  | IP Plan 3 | Private hospital          | S$1,500–2,500/yr | 10% co-pay |
  | (Plan 4 if offered) | Private + international | S$3,000+/yr | varies |

### 3.1 Co-payment rule (post-2018)

- **From 8 March 2018 onwards**, all new IP plans must include a
  **5% co-payment** (capped at S$3,000 per policy year) for
  treatment by **non-panel** doctors.
- This was MAS's response to over-charging by private specialists.
  Plans written before 2018 grandfather the old no-co-pay terms.
- **Source:** https://www.moh.gov.sg/news-highlights/details/ [official,
  moh.gov.sg press release, March 2018]

### 3.2 Stay-on-MediShield vs upgrade-to-IP — decision matrix

| Profile                                | Recommendation          |
| -------------------------------------- | ----------------------- |
| Single, public hospital comfortable    | Stay on MediShield Life |
| Married, may want private specialist   | IP Plan 2 with 5% co-pay|
| Family, want private hospital + delivery| IP Plan 3 with 5% co-pay|
| Comfortable with public Class A only   | IP Plan 1 with 5% co-pay|

The skill should always show the **co-payment math** before any
upgrade decision: e.g. "S$50,000 private hospital bill − MediShield
Life payout ~S$10,000 = S$40,000 net, of which 5% (S$2,000) is your
out-of-pocket co-pay."

## 4. Layer 1 (long-term care) — CareShield Life

- **What.** Long-term-care insurance for severe disability. Pays a
  monthly cash payout for as long as the insured is disabled.
- **Auto-enrolled.** All Singaporeans / PRs born 1980 or later
  are auto-enrolled. Opt-out is possible (one-time declaration at
  age 30) but is **irreversible**.
- **Payout.** >S$600/mo in 2025+; the payout is age-banded and
  increases over time per scheme rules.
- **Premium.** Deductible from CPF-MA (MediSave).
- **Source:** https://www.careshieldlife.gov.sg/ [official]

### 4.1 CareShield vs Eldershield vs Private LTC

| Scheme              | Status         | Payout          | Verdict              |
| ------------------- | -------------- | --------------- | -------------------- |
| CareShield Life     | Active, default| >S$600/mo 2025+ | **Stay on** — the floor |
| Eldershield (older)| Closed to new | S$300–400/mo    | Hold if you have it   |
| Private LTC rider   | Optional       | S$2,000+/mo     | Only if you can show 5%+ RoP math |

The skill should treat CareShield as the **floor of long-term-care
coverage** and only recommend a private LTC rider if the client
shows a clear willingness to fund the gap.

## 5. HPS — Home Protection Scheme

- **What.** Decreasing-term life insurance that covers the
  outstanding HDB loan balance. **Mandatory** for HDB loans.
- **Coverage.** Reduces as the HDB loan amortises.
- **Premium.** Deductible from CPF-OA (or cash).
- **Source:** https://www.cpf.gov.sg/Members/Schemes/schemes/housing/hps
  [official, cpf.gov.sg]

### 5.1 HPS verification checklist

- [ ] Is the HPS policy in force? (CPF statement → HPS deduction)
- [ ] Is the cover still ≥ outstanding HDB loan balance?
- [ ] Is the premium being deducted from CPF-OA? (Cash is fine but
      loses the 2.5% OA arbitrage)
- [ ] Will the HPS cover expire before the loan amortises? (A
      mismatch in term is a flag)

## 6. CPF — the integrated layer

CPF is not insurance but is part of the protection picture because:

| Account | Earns       | Used for                                    | Notes                              |
| ------- | ----------- | ------------------------------------------- | ---------------------------------- |
| **OA**  | 2.5%        | Housing, insurance, education, CPFIS        | Most flexible                      |
| **SA**  | 4.0% (FRS)  | Retirement, CPF-Life annuity                 | Higher yield, less flexible        |
| **MA**  | 4.0%        | MediShield, CareShield, IP premiums, medical | Insurance + medical                |
| **RA**  | 4.0% (FRS)  | Retirement                                  | Created at age 55 from OA + SA     |

- **SA top-up.** Voluntary cash top-up to SA earns 4% p.a. (FRS) or
  4% p.a. (EHS) and **qualifies for tax relief up to S$8,000/yr**
  (capped). Source: https://www.iras.gov.sg/ [official, iras.gov.sg]
- **CPFIS-OA.** OA above S$20k idle can be invested via the
  **CPF Investment Scheme** in approved unit trusts, REITs, or
  Singapore Government Securities (SGS) bonds. Returns are
  tax-free but the principal is not guaranteed.
- **CPF Life.** At age 65, the RA starts paying out a monthly
  annuity for life. The payout is **bequest-adjusted** — leaving
  less to heirs in exchange for a higher monthly payout.

## 7. The integration in a portfolio review

The skill's Section 3 (National Protection Integration) is a 4-row
checklist. The skill must:

1. **Verify** each layer is active (CPF statement + insurer fact
   sheet).
2. **Quantify** the cover vs need (e.g. HPS cover vs outstanding
   HDB loan).
3. **Recommend** stay / upgrade / supplement with the co-payment
   math shown.
4. **Never** advise cancelling MediShield or CareShield. The skill
   diagnoses the optional **upgrade** (IP) and the **opt-out**
   decision (CareShield, age-30 declaration) — both of which are
   irreversible.

## 8. Common client questions

| Question                                                | Skill's posture |
| ------------------------------------------------------- | --------------- |
| "Should I upgrade from MediShield to IP?"              | Show the 5% co-pay math; recommend IP only if private hospital is a clear need |
| "Should I opt out of CareShield?"                       | **Default: stay on.** Opt-out is irreversible; payout grows with the scheme |
| "Can I pay IP premium from MediSave?"                   | Yes, but only the MediShield-Life-equivalent portion. The rest is cash. |
| "Is HPS enough or do I need a separate Mortgage Term?"  | HPS is enough if you only have an HDB loan. If you have a private bank loan, HPS does not cover it. |
| "What if I'm a foreigner / not a PR?"                   | National layers do not apply; the skill falls back to a private-market plan review. State the assumption. |
