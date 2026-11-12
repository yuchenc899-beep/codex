---
name: daily-market-watch
description: >-
  Generate a "Daily Market Watch" / global finance news report covering the last 7 days for a diversified portfolio — stocks, ETFs, cryptocurrencies, indices, bonds, commodities, Fed signals. Use whenever the user asks for a market overview, daily/weekly market briefing, what is moving markets, global finance news, region-specific market report (e.g. "zoom into China", "US market today", "Japan markets this week"), Fed/rate-cut outlook, value/momentum stock picks, crypto market recap, or anything that sounds like a "morning note" / "market wrap" from a sell-side desk. Triggers on phrases like "daily market watch", "market overview", "weekly market report", "global finance news", "what's happening in markets", "give me a market briefing", "finance report for [region]", "morning market note", "end-of-day report", or any request to summarize market-moving news with sources. Do NOT use for: single-ticker deep dives, trade execution, tax advice, or pure technical chart analysis.
---

# Daily Market Watch

A global-finance, market-moving-news briefing skill. Produces a structured, source-cited Markdown report covering the last 7 days (or a user-specified window) for a diversified portfolio. Default lens is the **whole world**; supports **region zoom-in** (US, China, Japan, EU, UK, India, Singapore, HK, Korea, Australia, etc.) and **asset-class zoom-in** (crypto-only, equities-only, fixed income, commodities).

## When to Use

Run this skill when the user asks any of:

- "Daily market watch" / "morning market briefing" / "end-of-day report"
- "Give me a market overview for this week"
- "What's happening in markets right now"
- "Global finance news" / "market wrap"
- "Zoom into [region / country] markets" — e.g. "give me a China finance report", "US markets this week", "Japan market outlook"
- "[Region] market outlook" / "what's moving [country] stocks"
- "Weekly market report" with a 7-day window
- Any "sell-side note" style request with sources + benchmarks

Do **not** run for: single-ticker technical analysis, trade execution, tax/estate planning, accounting, or pure crypto price predictions.

## Inputs the skill accepts

| Input              | Default                  | How to override                                 |
| ------------------ | ------------------------ | ----------------------------------------------- |
| Region scope       | Global (US + EU + Asia)  | "US only", "China + HK", "Asia ex-Japan"        |
| Asset focus        | All (stocks/ETF/crypto)  | "crypto only", "equities only", "fixed income"  |
| Time window        | Last 7 days              | "from June 1 to June 7", "past 30 days"         |
| Portfolio lens     | Diversified 60/30/10     | "aggressive growth", "income", "capital preserv" |
| Granularity        | Standard 5 sections      | "executive summary only" / "deep dive"          |
| Output format      | Markdown                 | "table only" / "bullet only"                    |

If the user gives a partial brief (e.g. just "China market this week"), fill sensible defaults for the rest and **state assumptions** at the top of the report.

## Workflow

Copy this checklist and track progress:

```
Daily Market Watch Run:
- [ ] 1) Parse scope: regions, assets, time window, lens
- [ ] 2) Pull macro data: indices, yields, commodities, FX, crypto
- [ ] 3) Pull Fed / central-bank signals (CME FedWatch, SOFR, CBs)
- [ ] 4) Pull region-specific news with sources
- [ ] 5) Pull sentiment indicators (VIX, put/call, AAII, Fear&Greed)
- [ ] 6) Identify value + momentum picks (stocks, ETFs, crypto)
- [ ] 7) Synthesize sections A-E per output template
- [ ] 8) Add disclaimer + sources block
- [ ] 9) Deliver markdown report
```

### 1) Parse scope

Before any research, fix:

- **Regions in scope** (default: US, EU, China, Japan; expand to UK, India, Singapore, HK, Korea, LatAm, Middle East, AU on request)
- **Asset classes** (default: stocks + ETFs + crypto + bonds + commodities + FX; trim on request)
- **Time window** (default: trailing 7 days ending today; honor explicit dates)
- **Portfolio lens** (default: balanced 60/30/10 equity/fixed/crypto)
- **Any explicit user filters** (e.g. "tech only", "no crypto", "focus on AI")

State the parsed scope at the top of the report under a `## Scope` heading so the user can correct it.

### 2) Pull macro data

Use `web_search` and `webfetch` to retrieve, for the time window:

- **Indices**: S&P 500, Nasdaq Composite, Dow Jones, Russell 2000, STOXX Europe 600, FTSE 100, DAX, Nikkei 225, TOPIX, Hang Seng, Shanghai Composite, CSI 300, KOSPI, S&P/ASX 200, Nifty 50, Sensex
- **Bonds**: US 10Y / 2Y / 30Y Treasury yields, German Bund, JGB 10Y, China CGB
- **Commodities**: WTI/Brent crude, gold, silver, copper, iron ore, natural gas, wheat
- **Forex**: DXY (USD index), EUR/USD, USD/JPY, USD/CNY, GBP/USD, AUD/USD
- **Crypto**: BTC, ETH, total market cap, BTC dominance, total DeFi TVL

For each, capture **last close**, **% change over the window**, and **a 1-line catalyst** (e.g. "rose on softer CPI print").

### 3) Pull Fed / central-bank signals

Required for the Market Overview:

- **CME FedWatch Tool** implied probabilities for the next FOMC meeting (cut / hold / hike) — current snapshot
- **Fed funds futures / SOFR futures** — front-month implied rate, change since window start
- **CFTC COT positioning** — net long/short on USD, 10Y notes, S&P, gold, oil, BTC (if available)
- **Yield curve** — 2s10s, 3m10y spreads, direction during window
- **Other central banks** for region-zoom: ECB (deposit rate + next meeting), BoJ (policy rate + JGB purchases), PBoC (LPR + reserve req), BoE (Bank Rate), RBI (repo rate)

If a data point is not retrievable, write `n/a (source unavailable)` rather than fabricating. Source every number.

### 4) Pull region-specific news with sources

**This is the core of the skill.** For each region in scope, search the last 7 days for **market-moving** news. Market-moving = anything that moves the underlying index, FX, bonds, or sector ETFs by ≥ 0.5% intraday, OR is a policy/regulatory/geopolitical event the desk would flag.

Use the curated source map in `references/regional-sources.md` for each region. Priorities:

| Region | Primary sources                                                          |
| ------ | ------------------------------------------------------------------------ |
| US     | Reuters, Bloomberg, WSJ, CNBC, Fed speeches, Treasury statements, SEC    |
| China  | Reuters, Bloomberg, SCMP, Caixin, PBoC, NBS, CSRC, MoF                    |
| Japan  | Reuters, Nikkei Asia, BoJ, METI, Ministry of Finance                     |
| EU     | Reuters, FT, ECB, Eurostat, Bundesbank, ECB speakers                     |
| UK     | FT, Reuters, BoE, ONS                                                    |
| India  | Reuters, RBI, SEBI, MoF, Moneycontrol, Economic Times                     |
| HK     | SCMP, HKEX, HKMA, SFC                                                   |
| Korea  | Reuters, BOK, KRX, Korea Times                                          |
| AU     | Reuters, RBA, ASIC, AFR                                                 |
| Crypto | CoinDesk, The Block, Decrypt, Glassnode, Coinglass, project blogs        |

For **each** news item, capture: date, headline, 1-sentence impact, source URL.

### 5) Pull sentiment indicators

- **VIX** (level + % change), **VVIX** (vol of vol)
- **Put/Call ratio** (equity + index options)
- **AAII bull-bear survey** (% bulls, % bears, neutral)
- **Crypto Fear & Greed Index**
- **CNN Business Fear & Greed Index** (US equities)
- **CNN Business greed indicators** (momentum, junk-bond demand, market breadth)
- **Skew index** if available

### 6) Identify value + momentum picks

For each of the 6 pick lists (Section A: stocks/ETFs/crypto value; Section B: stocks/ETFs/crypto momentum), identify 5 candidates. Pull live data:

**Stocks** — use Yahoo Finance / Bloomberg / Reuters. Filter by Market Cap > $5B. For value: P/E vs sector, P/B, debt/equity, FCF yield, % from 52-wk low. For momentum: 30-day % change, 30-day avg volume vs 90-day avg, RS rating.

**ETFs** — AUM > $1B, expense ratio < 0.5%, % from 52-wk low (value) or 30-day % change (momentum).

**Crypto** — Top 50 by market cap, on-chain dev activity (GitHub commits last 30d) for value, 7-day % change + volume for momentum.

**Guardrail**: if a real-time price cannot be verified, write `n/a` in the price column and cite a source that was retrieved. Never invent a number.

### 7) Synthesize Sections A-E

Follow the **Output Template** below verbatim. Do not skip sections unless the user explicitly opts out. For each pick, justify the Fed tie-in (e.g. "long duration benefits from cut >70%").

### 8) Add disclaimer + sources block

- **Mandatory disclaimer** at end of every report (see template).
- **Sources block** at the end — bulleted list of every URL cited in the report. If a section has no sourceable data, state "no verifiable data retrieved for this section" rather than fabricating.

### 9) Deliver

- Output as a single Markdown file (default filename: `daily-market-watch-YYYY-MM-DD.md`) if the agent has a write target.
- If delivering inline, still use the full template; allow truncation only when the user asks for a "summary" or "bullet only".
- Lead with a 3-5 line **TL;DR** above the Market Overview so the user can decide whether to read the full report.

## Output Template (canonical — follow exactly)

```markdown
# Daily Market Watch — [Date Range, e.g. 23 Jul 2025 → 30 Jul 2025]

**Scope:** [regions] | [asset focus] | Lens: [portfolio type] | As of: [ISO date]
**TL;DR:** [3-5 bullets; the single most important takeaway first]

---

## 0. Market Overview

- **Indices (1W %):** SPX [price, %], NDX [price, %], DJI [price, %], STOXX [price, %], NKY [price, %], HSI [price, %], SHCOMP [price, %]
- **Bonds:** UST 10Y [yield, bps Δ 1W], 2Y [yield, bps Δ], 2s10s [bps]; Bund 10Y [yield]; JGB 10Y [yield]
- **Commodities:** WTI [$/bbl, %], Brent [$/bbl, %], Gold [$/oz, %], Copper [$/lb, %]
- **Forex:** DXY [level, %], EUR/USD, USD/JPY [level, %], USD/CNY [level, %]
- **Crypto:** BTC [$/coin, %], ETH [$/coin, %], Total mcap [$T, %], BTC dominance [%]
- **Sentiment:** VIX [level, %], Put/Call [ratio], AAII [% bull / % bear], Crypto Fear&Greed [0-100]
- **Data prints this week:** CPI [actual vs est], NFP [actual vs est], PPI, PCE, GDP-now [level]
- **Fed signals (CME FedWatch):** Next FOMC: [X bps cut % / hold % / hike %]; [Y bps] by year-end [%]
- **Other CBs:** ECB [next decision / implied path], BoJ [next decision / implied path], PBoC [LPR / OMO]
- **Positioning (CFTC COT):** USD net [K contracts, Δ], 10Y net [K, Δ], SPX net, Gold net, BTC net
- **Curve & vol:** 2s10s [bps, Δ], MOVE [level], skew [level]
- **Macro read:** [2-3 sentences tying the above to risk-on/risk-off regime]

---

## A. Top 5 Value Opportunities

**Stocks (Mkt Cap > $5B, near 52-wk low, strong fundamentals):**
| Ticker | Price | % from 52W Low | Key Fundamental |
| --- | --- | --- | --- |
| [TICK] | [price] | [%] | [1-liner + Fed tie-in] |
| ... (5 rows) |

**ETFs (AUM > $1B, expense <0.5%, near 52-wk low):**
| Ticker | Price | % from 52W Low | Key Fundamental |
| --- | --- | --- | --- |
| ... (5 rows) |

**Crypto (Top-50 mcap, >50% off recent peak, active dev):**
| Symbol | Price | % from Recent High | Key Use Case |
| --- | --- | --- | --- |
| ... (5 rows) |

---

## B. Top 5 Momentum Picks

**Stocks (Mkt Cap > $5B, >15% 30D, rising volume):**
| Ticker | Price | % Δ 30D | Catalyst |
| --- | --- | --- | --- |
| ... (5 rows) |

**ETFs (AUM > $1B, >10% 30D, rising AUM):**
| Ticker | Price | % Δ 30D | Catalyst |
| --- | --- | --- | --- |
| ... (5 rows) |

**Crypto (Top-50 mcap, >20% 7D, rising volume):**
| Symbol | Price | % Δ 7D | Catalyst |
| --- | --- | --- | --- |
| ... (5 rows) |

---

## C. Portfolio Allocation Insights

**Sample allocation (lens: [portfolio type]):**
- Equities: [X%]
- Fixed income: [X%]
- Crypto: [X%]
- Cash/commodities: [X%]

**Rebalancing actions (2-3):**
1. [action 1 + reason]
2. [action 2 + reason]
3. [action 3 + reason]

**Long/short by asset class:**
- **Equities (Stocks/ETFs):** Long [2-3 tickers]; Short/hedge [1-2 tickers]
- **Fixed income:** Long [1-2 examples]; Short/hedge [1 example]
- **Crypto:** Long [2 examples]; Short/hedge [1 example]
- **Cash/Commodities:** Long [1 example]; Short/hedge [1 example]

**Overall sentiment:** [Bullish / Neutral / Bearish] → suggested cash buffer [X%]

---

## D. Options Strategies for Income & Hedging

| Strategy | Target | Key Parameters | Rationale (incl. Fed tie-in) |
| --- | --- | --- | --- |
| [e.g. Wheel] | [TICK] | [strike, expiry] | [1-2 lines] |
| [e.g. Covered Call] | [TICK] | [strike, expiry] | [1-2 lines] |
| [e.g. Protective Put] | [TICK] | [strike, expiry] | [1-2 lines] |
| [e.g. Iron Condor] | [INDEX] | [strikes, expiry] | [1-2 lines] |
| [e.g. Collar] | [TICK] | [put strike, call strike, expiry] | [1-2 lines] |

(3-5 strategies total)

---

## E. Key Market Trends & Risks to Watch

**Trends this week (3-5):**
1. [trend + Fed tie-in]
2. ...
3. ...

**Risks (2-3):**
1. [risk + mitigation]
2. ...
3. ...

**Upcoming events (next 1-4 weeks, 3-5):**
| Date / Event | Key Details | Portfolio Impact | Pro Tip |
| --- | --- | --- | --- |
| [date — FOMC / CPI / NFP / earnings / etc.] | [1 line] | [vol / sector / rate-sensitivity] | [what to watch: OI, vol surface, positioning] |
| ... (3-5 rows) |

---

## Sources

- [URL 1 — title]
- [URL 2 — title]
- [URL 3 — title]
- (every claim in the report should trace back to a URL here; if a section has no sourceable data, say so explicitly)

---

**Disclaimer:** This analysis is for informational purposes only and does not constitute financial advice. Consult a qualified advisor before making investment decisions. Past performance is not indicative of future results.
```

## Guardrails

- **No fabricated numbers.** If a price, yield, or % change cannot be verified, write `n/a` and explain. Better to leave a gap than to guess.
- **No trade execution.** This skill produces research only. Never say "buy" or "sell" without framing as a "thesis" or "watchlist idea", and never cite target prices as guarantees.
- **Source every claim.** Every non-trivial number, every named pick, every Fed/CB signal must trace to a URL in the Sources block.
- **No financial-advice framing.** Always end with the disclaimer. Never say "you should" or "I recommend" — use "thesis", "watchlist idea", "if you're considering".
- **Time-stamp everything.** Every report must include an `As of:` ISO date and the date range covered.
- **Respect scope.** If the user asks for "China only", do not pad with US/EU sections; keep it focused and state scope explicitly.
- **Region-zoom = source-zoom.** For "China only", use Chinese-language or China-focused sources (Caixin, SCMP, PBoC). For "Japan only", use Nikkei, BoJ, METI. Do not extrapolate from US/English-language coverage of a non-US market.
- **When web tools fail**, fall back to cached/known data and clearly label it `[last known]`. Do not silently invent.
- **Crypto picks** require on-chain dev activity (GitHub commits in last 30d) for value list, and rising spot volume + a verifiable catalyst for momentum. No pure-meme picks.

## Data Source Map (summary)

Full per-region source list lives in `references/regional-sources.md`. Quick reference:

| Region | Primary feeds                                                          |
| ------ | ---------------------------------------------------------------------- |
| US     | fed.gov, treasury.gov, sec.gov, wsj.com, reuters.com, cnbc.com         |
| China  | pbc.gov.cn, stats.gov.cn, csrc.gov.cn, scmp.com, caixin.com            |
| Japan  | boj.or.jp, meti.go.jp, mof.go.jp, nikkei.com, reuters.com              |
| EU     | ecb.europa.eu, bundesbank.de, reuters.com, ft.com                      |
| UK     | bankofengland.co.uk, ons.gov.uk, ft.com, reuters.com                   |
| India  | rbi.org.in, sebi.gov.in, moneycontrol.com, economictimes.com           |
| HK     | hkex.com.hk, hkma.gov.hk, scmp.com                                     |
| Korea  | bok.or.kr, krx.co.kr, koreatimes.co.kr                                 |
| Crypto | coingecko.com, coinmarketcap.com, coindesk.com, glassnode.com          |

## Companion Skills

- `smart-money-tracker` (same repo) — for institutional + congressional trade flows to corroborate Section C.
- Any charting / portfolio tracker the user maintains.

## References

- `references/regional-sources.md` — per-region source URLs + search queries
- `references/fed-signals.md` — CME FedWatch, SOFR futures, COT positioning, how to read each

## Example

A full template-conforming report lives at `examples/sample-report.md`. All numbers/tickers in the example are tagged `[last known]` or `[illustrative]` to signal it is a structural reference, not live data. Use the example as a golden output when iterating on this skill.
