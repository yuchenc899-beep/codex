---
name: fundamental-context
description: "Gather fail-open fundamental, capital-flow, and dragon-tiger context for one symbol. Use when user wants a disciplined non-price context workflow with explicit partial-status handling and A-share-specific caveats."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Fundamental Context

Gather fundamental context for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/fundamental-context/run.py`
- Primary purpose: add best-effort growth, earnings, institution, capital-flow, and dragon-tiger context around one symbol without pretending complete coverage
- Research layer: fundamental data collection (Stage 2: Data Collection & Quality Assurance, Stage 3: Data Cleaning & Normalization, Stage 4: Feature Engineering - Fundamental subset)
- Workflow stages: stage 2 `Data Collection & Quality Assurance` and stage 3 `Data Cleaning & Normalization` for non-price data
- Local executor guarantee: query the current adapter set, surface status fields and source chains, and return partial blocks rather than crash on unsupported paths

## Use When

- The user wants deeper non-price context after or alongside market analysis.
- The user wants capital-flow or dragon-tiger hints before forming a view.
- The user wants a compact fundamental block without the full narrative layer.

## Do Not Use When

- The user only wants price or technical interpretation. Use `market-analyze` or `technical-scan`.
- The user wants the full report bundle. Use `market-brief`.
- The user wants a reusable multi-block market snapshot. Use `stock-data`.
- The user expects full point-in-time fundamental warehousing or guaranteed cross-provider completeness. This skill does not guarantee that locally.

## Inputs

- Normal case: one stock symbol.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Capability note:
  - richer results depend on the optional provider stack being available
  - current blocks are adapter-driven and best-effort
  - the agent should say whether the request requires strict as-of correctness that this local path may not fully guarantee

## Execution

### Step 1: Define fundamental data requirements

Before collecting fundamental data, clarify what is needed:

**Fundamental data categories:**
- [ ] Financial statements (income, balance sheet, cash flow)
- [ ] Growth metrics (revenue, earnings, margins)
- [ ] Valuation metrics (P/E, P/B, P/S, EV/EBITDA)
- [ ] Profitability metrics (ROE, ROA, gross margin, net margin)
- [ ] Capital structure (debt/equity, interest coverage)
- [ ] Institutional ownership and changes
- [ ] Capital flow (northbound, margin trading, dragon-tiger)
- [ ] Sector and industry classification

**Data quality requirements:**
- [ ] Point-in-time correctness (no look-ahead bias)
- [ ] Restatement handling (use as-reported or as-restated consistently)
- [ ] Reporting lag (announcement date vs. period end date)
- [ ] Fiscal period alignment (quarterly, annual, TTM)
- [ ] Unit consistency (yuan, millions, billions)

**A-share specific requirements:**
- [ ] CSRC industry classification
- [ ] ST/\*ST status and history
- [ ] Suspension history and reasons
- [ ] Dragon-tiger list appearances (institutional vs. retail)
- [ ] Northbound (Stock Connect) flow
- [ ] Margin trading balance and changes
- [ ] Pledge ratio (share pledging by major shareholders)

### Step 2: Collect fundamental data with status tracking

Run the local executor and track data availability:

```bash
python3 <bundle-root>/fundamental-context/run.py <symbol>
```

**Status model interpretation:**
- **`ok`:** Adapter returned complete and meaningful block
- **`partial`:** Only some expected fields available (specify which)
- **`not_supported`:** Local path does not currently support the block
- **`stale`:** Data available but outdated (specify age)
- **`error`:** Adapter failed (specify error type)

**For each data block, document:**
- Status (ok/partial/not_supported/stale/error)
- Source chain (which provider/adapter)
- Data freshness (as-of date)
- Completeness (% of expected fields present)
- Known limitations (missing fields, stale data, etc.)

### Step 3: Validate and clean fundamental data

Apply systematic validation and cleaning:

#### Financial Statement Validation

**Income statement checks:**
- [ ] Revenue >= 0 (negative revenue is rare, flag for investigation)
- [ ] Gross profit <= Revenue (gross margin <= 100%)
- [ ] Operating profit consistency (revenue - COGS - opex)
- [ ] Net income consistency (operating profit + non-operating - tax)
- [ ] EPS calculation: net income / weighted average shares

**Balance sheet checks:**
- [ ] Assets = Liabilities + Equity (accounting identity)
- [ ] Current assets >= 0, Current liabilities >= 0
- [ ] Total equity can be negative (flag as distressed)
- [ ] Book value per share: total equity / shares outstanding
- [ ] Working capital: current assets - current liabilities

**Cash flow checks:**
- [ ] Operating cash flow vs. net income (quality of earnings)
- [ ] Free cash flow: operating CF - capex
- [ ] Cash flow from financing (debt issuance, equity issuance, dividends)
- [ ] Cash balance change = sum of three cash flow categories

**Cross-statement validation:**
- [ ] Net income (income statement) flows to equity (balance sheet)
- [ ] Depreciation (income statement) flows to accumulated depreciation (balance sheet)
- [ ] Capex (cash flow) flows to PP&E (balance sheet)
- [ ] Dividends (cash flow) reduce retained earnings (balance sheet)

#### Growth Metrics Calculation

**Revenue growth:**
- YoY growth: (revenue_t - revenue_{t-4}) / revenue_{t-4} (quarterly)
- QoQ growth: (revenue_t - revenue_{t-1}) / revenue_{t-1}
- CAGR: (revenue_latest / revenue_earliest)^(1/years) - 1
- Growth consistency: % of quarters with positive YoY growth

**Earnings growth:**
- EPS growth YoY, QoQ, CAGR (same formulas as revenue)
- Earnings surprise: (actual EPS - consensus EPS) / |consensus EPS|
- Earnings quality: operating CF / net income (>1 is good)

**Margin trends:**
- Gross margin: (revenue - COGS) / revenue
- Operating margin: operating profit / revenue
- Net margin: net income / revenue
- Margin expansion/contraction over time

#### Valuation Metrics Calculation

**Price multiples:**
- P/E ratio: price / EPS (use TTM or forward)
- P/B ratio: price / book value per share
- P/S ratio: market cap / revenue
- EV/EBITDA: enterprise value / EBITDA

**Valuation context:**
- Historical percentile (current P/E vs. 5-year range)
- Sector relative (P/E vs. sector median)
- Growth-adjusted (PEG ratio: P/E / earnings growth rate)
- Quality-adjusted (P/E vs. ROE, margin, cash flow quality)

**A-share valuation considerations:**
- A-share vs. H-share premium/discount (if dual-listed)
- Sector rotation effects (growth vs. value cycles)
- Policy sensitivity (regulatory risk premium)
- Liquidity premium (large cap vs. small cap)

#### Profitability and Efficiency Metrics

**Return metrics:**
- ROE: net income / average equity
- ROA: net income / average assets
- ROIC: NOPAT / invested capital
- ROE decomposition (DuPont): net margin × asset turnover × equity multiplier

**Efficiency metrics:**
- Asset turnover: revenue / average assets
- Inventory turnover: COGS / average inventory
- Receivables turnover: revenue / average receivables
- Days sales outstanding (DSO): 365 / receivables turnover

**Capital structure:**
- Debt/Equity ratio
- Interest coverage: EBIT / interest expense
- Net debt: total debt - cash
- Net debt / EBITDA (leverage ratio)

#### Institutional and Capital Flow Analysis

**Institutional ownership:**
- Total institutional ownership %
- Changes in institutional ownership (QoQ)
- Top institutional holders and their changes
- Foreign institutional ownership (QFII, RQFII)

**Northbound (Stock Connect) flow:**
- Cumulative northbound holdings
- Daily/weekly/monthly northbound flow
- Northbound ownership % of float
- Northbound flow vs. price correlation

**Margin trading:**
- Margin trading balance (融资余额)
- Margin trading balance change (daily, weekly)
- Margin trading balance / market cap
- Margin trading sentiment (increasing = bullish, decreasing = bearish)

**Dragon-tiger list (龙虎榜):**
- Appearance frequency (how often on list)
- Net buying by institutions vs. retail
- Hot money (游资) activity patterns
- Institutional seat identification (券商营业部)

**Share pledging:**
- Total shares pledged by major shareholders
- Pledge ratio (pledged shares / total shares)
- Pledge risk (if stock price falls, forced liquidation risk)
- Changes in pledge ratio over time

### Step 4: Synthesize fundamental context

Organize fundamental data into coherent narrative:

**Part 1: Business and Financial Overview**
- Company name, sector, industry (CSRC classification)
- Business description (main products/services)
- Market cap, shares outstanding, float
- Latest financial period (Q1/Q2/Q3/Q4, year)
- Data freshness and completeness status

**Part 2: Growth Profile**
- Revenue growth (YoY, QoQ, CAGR)
- Earnings growth (YoY, QoQ, CAGR)
- Growth consistency and quality
- Growth drivers (organic vs. acquisition, margin expansion, etc.)
- Growth outlook (consensus estimates if available)

**Part 3: Profitability and Efficiency**
- Margin trends (gross, operating, net)
- Return metrics (ROE, ROA, ROIC)
- Efficiency metrics (asset turnover, inventory turnover, DSO)
- Profitability vs. sector peers
- Quality of earnings (cash flow vs. net income)

**Part 4: Valuation Assessment**
- Current valuation multiples (P/E, P/B, P/S, EV/EBITDA)
- Historical valuation context (percentile vs. 5-year range)
- Sector relative valuation (vs. median, vs. peers)
- Growth-adjusted valuation (PEG ratio)
- Valuation interpretation (cheap/fair/expensive, with caveats)

**Part 5: Capital Structure and Financial Health**
- Debt/Equity ratio and trend
- Interest coverage and debt service ability
- Net debt / EBITDA (leverage)
- Working capital and liquidity
- Financial distress signals (negative equity, covenant violations, etc.)

**Part 6: Institutional and Capital Flow**
- Institutional ownership and recent changes
- Northbound flow trends and ownership
- Margin trading balance and sentiment
- Dragon-tiger list activity and patterns
- Share pledging risk assessment

**Part 7: A-Share Specific Context**
- ST/\*ST status and risk
- Suspension history and reasons
- Regulatory environment and policy sensitivity
- Sector rotation and market regime effects
- A-H premium/discount (if applicable)

**Part 8: Data Quality and Limitations**
- Status of each data block (ok/partial/not_supported/stale)
- Source chain and provenance
- Known data gaps and missing fields
- Point-in-time correctness caveats
- Restatement risk and reporting lag

### Step 5: Frame fundamental context honestly

When delivering results, maintain strict discipline:

**Explicit status disclosure:**
- State which blocks are `ok`, `partial`, `not_supported`, or `stale`
- List specific missing fields for partial blocks
- Identify source chain for each data block
- Specify data freshness (as-of date) for each block

**Interpretation boundaries:**
- Separate reported data from derived metrics
- Separate derived metrics from qualitative interpretation
- Label heuristic interpretations explicitly
- Do not convert partial data into strong conclusions

**Fundamental analysis caveats:**
- "Valuation appears cheap based on P/E, but this does not account for [growth, quality, risk factors]"
- "ROE is high, but leverage is also high, increasing financial risk"
- "Revenue growth is strong, but cash flow is weak, suggesting quality concerns"
- "Institutional ownership is increasing, but this is descriptive, not predictive"

**A-share specific caveats:**
- "Dragon-tiger list activity suggests retail speculation, not institutional conviction"
- "Northbound flow is positive, but represents only X% of float"
- "Margin trading balance is high, increasing downside risk if sentiment reverses"
- "Share pledging ratio is elevated, creating forced liquidation risk"

### Step 6: Run the local executor

```bash
python3 <bundle-root>/fundamental-context/run.py <symbol>
```

## Output Contract

- Minimum local executor output: human-readable text beginning with `基本面上下文`.
- Core fields: fundamentals status, capital-flow status, dragon-tiger flag, growth metrics, earnings summary, institution changes, and sector-flow leaders when available.
- Side effects: updates session memory for the current execution context.
- Caller-facing delivery standard:
  - **Eight-part structure:** Business overview, growth profile, profitability, valuation, capital structure, institutional/capital flow, A-share context, data quality
  - **Explicit status disclosure:** State which blocks are ok/partial/not_supported/stale with specific missing fields
  - **Source chain transparency:** Identify data source and provenance for each block
  - **Data freshness:** Specify as-of date for each data block
  - **Interpretation boundaries:** Separate reported data, derived metrics, and qualitative interpretation
  - **Fundamental analysis caveats:** Explicit limitations on valuation, growth, and quality conclusions
  - **A-share specific caveats:** Dragon-tiger interpretation, northbound flow context, margin trading risk, pledge risk
  - **No strong conclusions from partial data:** Acknowledge incompleteness rather than overselling
  - **Point-in-time correctness caveats:** State when data may not be strictly point-in-time correct

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Missing optional providers: fail open into partial or `not_supported` blocks instead of crashing.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- If only one non-price block is available, acknowledge the incompleteness rather than implying a full context sweep.
- Stale data: report age and recommend refresh if critical to decision.
- Restatement detected: flag and explain impact on historical comparisons.
- Missing critical fields: list specific gaps and impact on analysis.

## Key Rules

- **Fundamental blocks are best-effort and fail-open by design.**
- **Partial data is acceptable; hidden incompleteness is not.**
- **Keep the distinction between provider output and analyst interpretation visible.**
- **When point-in-time correctness is central to the decision, recommend a stricter data workflow instead of overselling this block.**
- **Status disclosure is mandatory.** Always state ok/partial/not_supported/stale for each block.
- **Source chain must be identified.** State which provider/adapter supplied each block.
- **Data freshness must be specified.** State as-of date for each block.
- **Valuation conclusions must be qualified.** "Appears cheap" is not the same as "is cheap."
- **Growth metrics must include quality assessment.** Revenue growth without cash flow is a red flag.
- **Capital flow interpretation must be cautious.** Northbound buying is descriptive, not predictive.
- **A-share specific risks must be highlighted.** Dragon-tiger, margin trading, pledging, ST status.
- **Do not convert partial adapter response into strong fundamental verdict.**

## Composition

- Often complements `market-analyze`, `decision-support`, and `market-brief`.
- Can be one component inside broader `analysis` or `stock-data` workflows.
- Should be combined with `technical-scan` for hybrid technical-fundamental analysis.
- Feeds into `decision-support` for position sizing based on fundamental quality.
- Used by `analysis` skill to support thesis with fundamental evidence.
