# Fed & Central Bank Signal Decoder

How to read and report on the policy signals that drive market pricing. The Daily Market Watch report integrates these into Section 0 (Market Overview) and uses them as the "Fed tie-in" rationale throughout Sections A–E.

---

## 1. CME FedWatch Tool

**URL:** https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html

**What it is:** Implied probabilities for the FOMC's target federal funds rate range at upcoming meetings, derived from prices on CME Fed Funds futures.

**How to read it:**

- The tool shows, for each upcoming FOMC meeting, the % probability the market assigns to each possible outcome (e.g. -25 bps, hold, +25 bps) at that meeting.
- Aggregate probabilities by year-end to show the implied path (e.g. "50 bps of cuts priced by Dec").
- Watch for **shifts** week-over-week: a move from 60% to 80% cut probability is more informative than the absolute level.

**How to report:**

> Per CME FedWatch (as of [date]): [X]% probability of [N] bps cut at the [meeting date] FOMC; [Y]% probability of hold. Path: [Z] bps of cumulative cuts priced by Dec.

Always cite the **as-of** date and the meeting being priced. The tool updates in real time — older snapshots become stale within hours.

---

## 2. SOFR Futures

**What it is:** Secured Overnight Financing Rate futures (tickers: SR1, SR3, etc.) trade on CME. They price the **expected average SOFR** over a given three-month period. They are the most liquid expression of expected Fed policy after Fed Funds futures.

**How to read it:**

- The implied rate for a contract month approximates the market's expected SOFR for that quarter.
- Implied rate − current SOFR ≈ market's expected total change in the policy rate during that quarter.
- Subtract the implied rate from the current effective federal funds rate to estimate cumulative bps of easing or tightening priced in.

**Example:** If SOFR for Dec 2025 implies 3.85% and current SOFR is 5.30%, the market is pricing ~145 bps of cuts by year-end.

**How to report:**

> SOFR futures imply [N] bps of cumulative [easing/tightening] by [date], vs [M] bps one week ago.

**Source:** CME Group, https://www.cmegroup.com/markets/interest-rates/stir/sofr.html

---

## 3. Fed Funds Futures (ZQ)

**What it is:** The 30-day federal funds rate futures contract (CME ticker: ZQ) settles to the average effective federal funds rate for the contract month.

**How to read it:**

- Implied rate = 100 − contract price.
- The contract for the month of a known FOMC meeting gives the most direct read on what the market expects post-meeting.
- Stack consecutive contracts to build a forward path.

**How to report:** Use as a sanity check on FedWatch or as the primary read if FedWatch is unavailable.

---

## 4. CFTC COT (Commitments of Traders) Report

**URL:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

**What it is:** Weekly report (released Fridays for the prior Tuesday) showing open interest and positioning by trader category in futures markets.

**Key categories to watch:**

- **Net long / net short** = (long positions) − (short positions) for non-commercial (speculative) accounts.
- Watch for **extremes**: when speculators are net long > 2 standard deviations above the 1-year mean, reversal risk rises.
- Watch for **week-over-week shifts**: a 20% move in net positioning in one week is meaningful.

**Markets to track for the Daily Market Watch:**

- USD Index (DX)
- 10Y Treasury notes (ZN)
- S&P 500 e-mini (ES)
- Gold (GC)
- WTI Crude (CL)
- BTC futures (BRR or CME BTC futures)

**How to report:**

> CFTC COT (week ending [date]): USD net [±K contracts, Δ [K] w/w], 10Y net [±K, Δ [K]], SPX net [±K], Gold net [±K], BTC net [±K].

---

## 5. Treasury Yield Curve

**What to report:**

- 2Y, 5Y, 10Y, 30Y UST yields
- 2s10s spread (10Y − 2Y) — historically a recession indicator when inverted
- 3m10y spread — also a recession signal
- Direction during the window: steepening (long end rising faster) vs flattening
- 1-week change in bps for the 10Y — the single most-watched number

**Source:** US Treasury Daily Yield Curve, https://home.treasury.gov/resource-center/data-chart-center/interest-rates/

**How to interpret:**

- **Bear steepening:** long end rising faster than short end → usually growth/inflation concerns, bearish for bonds, neutral-to-bearish for equities.
- **Bull steepening:** short end falling faster than long end → usually dovish Fed pivot, bullish for risk assets, bullish for bonds.
- **Bear flattening:** short end rising faster → usually hawkish Fed / rate-hike pricing, bearish for bonds, bearish for growth stocks.
- **Bull flattening:** long end falling faster → flight to quality, bearish for risk, bullish for bonds.

---

## 6. VIX & Vol Complex

- **VIX** (Cboe): 30-day implied vol on SPX. Levels: <15 calm, 15-25 normal, 25-35 elevated, 35+ stressed.
- **VVIX** (Cboe): vol of VIX. Rises into known events.
- **Skew** (Cboe SKEW): tail-risk pricing. >150 = elevated tail demand.
- **MOVE** (ICE BofA): Treasury vol analog. Spikes with Fed/spending news.
- **Implied vs realized:** when implied >> realized, options are rich → sell premium; when implied << realized, options are cheap → buy protection.

**How to report:** Cite level + 1W Δ. Tie to options strategy selection in Section D (e.g. "VIX at 12 supports short premium; VIX at 28 supports long protection").

---

## 7. Other Central Banks (for region-zoom)

| CB | Policy rate | URL | Cadence |
| --- | --- | --- | --- |
| ECB | Deposit rate | https://www.ecb.europa.eu/ | 6 weeks |
| BoE | Bank Rate | https://www.bankofengland.co.uk/ | 6 weeks |
| BoJ | Policy rate (uncollateralized overnight call rate) | https://www.boj.or.jp/en/ | 1-2 months |
| PBoC | 1Y LPR / 5Y LPR / 7-day reverse repo | http://www.pbc.gov.cn/ | LPR monthly |
| RBA | Cash rate | https://www.rba.gov.au/ | Monthly |
| BoC | Overnight rate | https://www.bankofcanada.ca/ | 6 weeks |
| SNB | Policy rate | https://www.snb.ch/ | Quarterly (review) |
| MAS | SGD NEER slope (no rate) | https://www.mas.gov.sg/ | Semi-annual (Apr, Oct) |
| RBI | Repo rate | https://www.rbi.org.in/ | Bi-monthly |

**MAS special case:** Singapore does not use an interest rate to manage monetary policy — it manages the **slope, level, and curvature of the S$ nominal effective exchange rate (S$NEER)**. When reporting on Singapore, frame it as "MAS [steepened / flattened / appreciated / depreciated] the S$NEER policy band" rather than as a rate change.

**BoJ special case:** BoJ exited NIRP and YCC in 2024. Watch the policy rate (currently 0.50%), JGB purchases (tapering), and JPY intervention signals from the MoF.

**PBoC special case:** PBoC uses multiple tools — 7-day reverse repo, MLF, LPR, RRR. Track all of them. LPR fixing on the 20th of each month is the headline number.

---

## 8. How to Tie Policy to Markets (the "Fed tie-in")

Use the following framework when writing the rationale for each pick in Sections A–E:

| Policy signal | Typical market impact |
| --- | --- |
| Rate cuts priced > 70% | Long duration bonds, long growth/tech equities, long gold, long BTC, short USD |
| Rate hikes priced > 30% | Short long-duration bonds, long cash/short-duration, short high-beta growth, long USD |
| Bull steepening curve | Long banks, long cyclicals, short bond proxies |
| Bear flattening curve | Long quality/defensives, long duration, short cyclicals |
| Net long USD specs at 1Y high | Risk of dollar squeeze → long gold/EM as hedge |
| Net short gold specs at 1Y low | Contrarian bullish gold |
| Net long SPX specs at 1Y high | Crowded trade → risk of sharp unwind |
| VIX > 25 with low realized | Long protective puts (cheap) |
| VIX < 14 with rising realized | Sell premium (covered calls, CSPs) |

---

## 9. Quick Phrasing Templates

Use these to keep the report's voice consistent:

- "CME FedWatch implies [N] bps of cuts by [date], up from [M] bps one week ago."
- "SOFR futures price [X.XX]% for [month], implying [N] bps of easing."
- "The 2s10s spread widened by [N] bps to [-X] bps, signaling [bull steepening / continued inversion]."
- "CFTC specs added [N]K contracts to their [long/short] position in [asset], the largest weekly build since [date]."
- "VIX closed the week at [X], [up/down N]%, suggesting the market is [pricing in / dismissing] tail risk."
- "PBoC set the 1Y LPR at [X.XX]%, [unchanged / -10 bps], with the 5Y LPR [flat / -15 bps]."
- "BoJ kept the policy rate at [X.XX]% but signaled [further hikes / pause], pushing the yen [N]% on the week."
- "ECB's [X]-month deposit rate sits at [X.XX]%; OIS prices [N] bps of cuts by [date]."
