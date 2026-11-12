---
name: stock-data
description: "Assemble a reusable one-symbol research snapshot across quote, levels, indicators, and fail-open fundamentals. Use when user wants a structured stage-2 to stage-4 research packet without a final thesis memo or action recommendation."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Stock Data

Assemble a reusable research snapshot for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/stock-data/run.py`
- Primary purpose: build a structured one-symbol research packet with market features and non-price context, without collapsing into a full thesis memo or order frame
- Workflow stages: stage 2 `Data Collection & Quality Assurance`, stage 3 `Data Cleaning & Normalization`, and stage 4 `Feature Engineering & Signal Construction`
- Local executor guarantee: build a persisted packet containing quote context, levels, indicators, fail-open fundamentals, and raw blocks for downstream reuse

## Use When

- The user wants a reusable structured snapshot rather than a prose-heavy report.
- The caller needs a canonical artifact that other skills can inspect, compare, or extend.
- The user wants market features plus best-effort fundamental context without the fuller memo discipline of `analysis`.

## Do Not Use When

- The user wants only normalized market data. Use `market-data`.
- The user wants the default concise report. Use `market-brief`.
- The user wants a deeper research memo with thesis framing, disconfirming evidence, or invalidation logic. Use `analysis`.
- The user wants a direct action, quantity, or execution plan. Use `decision-support` or `strategy-design`.

## Inputs

- Normal case: one stock symbol.
- Optional market inputs: `--csv`, `--start`, `--end`, `--source`.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Downstream assumption note:
  - the packet is only as current as the market and fundamental inputs used to build it
  - the agent should say whether the snapshot is fresh, stale, or explicitly historical

## Execution

### Step 1: Define research snapshot requirements

Before assembling the snapshot, clarify the scope:

**Research snapshot components:**
- [ ] Market data (OHLCV, normalized and validated)
- [ ] Technical features (MAs, momentum, volatility, support/resistance)
- [ ] Market state assessment (trend, regime, bias, score)
- [ ] Fundamental context (growth, profitability, valuation, capital structure)
- [ ] Capital flow context (institutional, northbound, margin, dragon-tiger)
- [ ] Data quality metadata (completeness, freshness, status)

**Snapshot purpose:**
- [ ] Reusable artifact for downstream analysis
- [ ] Comparison baseline for historical tracking
- [ ] Input to decision support or strategy design
- [ ] Audit trail for retrospective evaluation

**Freshness requirements:**
- [ ] Real-time (latest available data)
- [ ] Historical (specific date or period)
- [ ] Reuse existing snapshot (if recent enough)

### Step 2: Assemble market data foundation

Build the market data layer with quality validation:

**Market data collection:**
- Run `market-data` skill or equivalent to get normalized OHLCV
- Validate data quality (completeness, consistency, outliers)
- Document data source, date range, and quality score
- Flag any data quality issues that affect downstream analysis

**Technical feature engineering:**
- Calculate trend indicators (MAs, ADX, trend classification)
- Calculate momentum indicators (RSI, MACD, Stochastic, ROC)
- Calculate volatility indicators (ATR, Bollinger Bands, historical vol)
- Calculate volume indicators (volume ratio, OBV, accumulation/distribution)
- Identify support and resistance levels
- Calculate price position metrics (distance to MAs, support, resistance)

**Market state assessment:**
- Run `market-analyze` skill or equivalent to get composite score
- Document trend direction, strength, and classification
- Document regime (bull/bear/range/volatile/breakout/exhaustion)
- Document bias (bullish/bearish/neutral/uncertain)
- Document key support and resistance levels
- Document risk flags (overbought, oversold, divergence, etc.)

### Step 3: Assemble fundamental context (fail-open)

Add fundamental data with explicit status tracking:

**Fundamental data collection:**
- Run `fundamental-context` skill to get best-effort fundamental data
- Track status for each block (ok/partial/not_supported/stale/error)
- Document source chain and data freshness for each block
- List specific missing fields for partial blocks

**Fundamental metrics synthesis:**
- Growth profile (revenue, earnings, margins, consistency)
- Profitability metrics (ROE, ROA, ROIC, margins)
- Valuation metrics (P/E, P/B, P/S, EV/EBITDA, historical context)
- Capital structure (debt/equity, interest coverage, leverage)
- Financial health (working capital, liquidity, distress signals)

**Capital flow context:**
- Institutional ownership and changes
- Northbound (Stock Connect) flow and ownership
- Margin trading balance and sentiment
- Dragon-tiger list activity and patterns
- Share pledging ratio and risk

**A-share specific context:**
- ST/\*ST status and history
- Suspension history and reasons
- Regulatory environment and policy sensitivity
- Sector rotation and market regime effects
- A-H premium/discount (if dual-listed)

### Step 4: Build structured research packet

Organize all components into canonical artifact:

**Packet structure:**

**Section 1: Snapshot Metadata**
- Symbol, name, board, sector, industry
- Snapshot generation timestamp
- Data sources (market, fundamental, capital flow)
- Data freshness (as-of dates for each component)
- Snapshot purpose (analysis, comparison, decision support, etc.)
- Quality summary (overall data quality score)

**Section 2: Market Data Summary**
- Latest price, volume, turnover
- Date range and trading days
- Data quality score and issues
- Corporate action events in period
- Price limit days and suspension days

**Section 3: Technical Features (Data Perspective)**
- **Trend analysis:**
  - Current trend (direction, strength, classification)
  - Moving average alignment and distances
  - ADX and directional indicators
  - Trend duration and consistency
- **Momentum analysis:**
  - RSI, MACD, Stochastic readings
  - Momentum strength and direction
  - Overbought/oversold conditions
  - Divergences (bullish/bearish)
- **Volatility analysis:**
  - Historical volatility (20-day, 60-day)
  - Volatility percentile and regime
  - ATR and Bollinger Band width
  - Volatility trend (rising/falling/stable)
- **Volume analysis:**
  - Volume trend and patterns
  - Volume confirmation/divergence
  - OBV and accumulation/distribution
  - Volume percentile and regime
- **Support and resistance:**
  - Key support levels (with distances)
  - Key resistance levels (with distances)
  - Level strength assessment
  - Current price position

**Section 4: Market State Assessment**
- Composite score (0-100) with interpretation
- Regime classification (bull/bear/range/volatile/breakout/exhaustion)
- Bias (bullish/bearish/neutral/uncertain)
- Risk flags (technical, A-share, volatility)
- Confidence level in assessment

**Section 5: Fundamental Context (Intelligence)**
- **Status disclosure:** State which blocks are ok/partial/not_supported/stale
- **Growth profile:** Revenue, earnings, margin trends, consistency
- **Profitability:** ROE, ROA, ROIC, margins, efficiency
- **Valuation:** P/E, P/B, P/S, historical context, sector relative
- **Capital structure:** Debt/equity, interest coverage, leverage, financial health
- **Data quality:** Source chain, freshness, missing fields, limitations

**Section 6: Capital Flow Context**
- **Status disclosure:** State which blocks are ok/partial/not_supported/stale
- **Institutional:** Ownership %, changes, top holders
- **Northbound:** Flow trends, ownership %, sentiment
- **Margin trading:** Balance, changes, sentiment
- **Dragon-tiger:** Appearance frequency, institutional vs. retail, patterns
- **Share pledging:** Pledge ratio, risk assessment

**Section 7: A-Share Specific Context**
- ST/\*ST status and risk
- Suspension history and liquidity risk
- Price limit frequency and impact
- Regulatory environment and policy sensitivity
- Sector rotation and market regime effects

**Section 8: Data Quality and Limitations**
- Overall quality score (0-100)
- Completeness assessment (% of expected data present)
- Freshness assessment (days since latest data)
- Known gaps and missing fields
- Point-in-time correctness caveats
- Recommended actions (refresh, validate, supplement)

**Section 9: Raw Blocks (Provenance Layer)**
- Market data raw output
- Market-analyze raw output
- Fundamental-context raw output
- Source chains for each block
- Timestamps for each block
- Status codes for each block

### Step 5: Persist research packet as artifact

Write structured artifact to run directory:

**Artifact files:**
- `state.json`: Machine-readable snapshot state
  - All metrics, indicators, and status codes
  - Timestamps and source chains
  - Quality scores and completeness flags
- `report.md`: Human-readable snapshot report
  - All sections formatted for readability
  - Tables for metrics and indicators
  - Status badges for data blocks
- `metadata.json`: Snapshot metadata
  - Generation timestamp
  - Symbol and data sources
  - Quality summary
  - Downstream usage tracking

**Artifact validation:**
- [ ] All files written successfully
- [ ] JSON files are valid and parseable
- [ ] Markdown file is well-formatted
- [ ] Run directory is properly dated and named
- [ ] Artifact is reusable by downstream skills

### Step 6: Run the local executor

```bash
python3 <bundle-root>/stock-data/run.py <symbol> [--csv PATH]
```

### Step 7: Review packet as structured artifact

After generation, validate the packet:

**Completeness check:**
- [ ] All expected sections present
- [ ] Market data section complete
- [ ] Technical features section complete
- [ ] Market state section complete
- [ ] Fundamental context section present (even if partial)
- [ ] Capital flow section present (even if partial)
- [ ] Data quality section complete

**Quality check:**
- [ ] Status codes accurate for each block
- [ ] Source chains documented
- [ ] Freshness timestamps present
- [ ] Missing fields explicitly listed
- [ ] Quality score reflects actual data state

**Provenance check:**
- [ ] Raw blocks preserved for audit
- [ ] Generation timestamp recorded
- [ ] Data sources documented
- [ ] Reuse vs. fresh computation noted

### Step 8: Hand off with provenance

When passing packet to downstream skills:

**Provenance disclosure:**
- Run directory path
- Generation timestamp
- Symbol and data sources
- Which blocks are fully populated vs. partial
- Data freshness (how old is the snapshot)
- Quality score and known limitations

**Reuse discipline:**
- If snapshot is recent (< 1 day old), consider reusing
- If snapshot is stale (> 3 days old), regenerate
- If user requests fresh data, regenerate regardless of age
- If downstream skill needs specific data not in packet, supplement

**Integration with downstream skills:**
- `analysis`: Use packet as evidence base for thesis
- `decision-support`: Use packet for position sizing inputs
- `strategy-design`: Use packet for execution planning
- `backtest-evaluator`: Use packet for retrospective comparison
- `analysis-history`: Use packet for historical tracking
- `reports`: Use packet for report generation

## Output Contract

- Minimum local executor output: human-readable text beginning with `# <symbol> Analysis`.
- Minimum packet emphasis: `Data Perspective` and `Intelligence` rather than a complete battle plan.
- Artifact side effects: writes one dated run directory with `state.json`, `report.md`, and `metadata.json`.
- Caller-facing delivery standard:
  - **Nine-section structure:** Metadata, market data summary, technical features, market state, fundamental context, capital flow, A-share context, data quality, raw blocks
  - **Structured artifact emphasis:** Make clear this is a reusable research object, not a final thesis memo
  - **Status transparency:** Identify which blocks are ok/partial/not_supported/stale with specific missing fields
  - **Provenance documentation:** State generation time, symbol, source basis, data freshness
  - **Quality assessment:** Overall quality score and completeness percentage
  - **Reuse discipline:** State whether snapshot is fresh, recent, or stale; recommend regeneration if needed
  - **Integration guidance:** Explain how packet feeds downstream skills (analysis, decision-support, etc.)
  - **No thesis or action claims:** Keep strictly descriptive; do not add investment views or trade recommendations
  - **Fail-open transparency:** Acknowledge when fundamental or capital flow blocks are partial or missing

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Market-data failures: readable failure text beginning with `执行失败:`.
- Fundamental enrichment degrades fail-open rather than aborting the snapshot.
- If the market layer is adequate but non-price context is thin, return the packet with explicit partial-status language.
- Missing run directory: create directory structure and retry write.
- JSON serialization errors: log error and write partial artifact with error metadata.
- Stale data detected: flag in metadata and recommend refresh.

## Key Rules

- **Use this skill for canonical structured context assembly.**
- **Preserve the difference between a reusable research object and a final investment view.**
- **Prefer reusing this artifact in later skills when the user asks for history, comparison, or memo escalation.**
- **Do not pretend that the packet implies a tested signal or a portfolio instruction.**
- **Status disclosure is mandatory for all blocks.** Always state ok/partial/not_supported/stale.
- **Provenance must be documented.** Generation time, sources, freshness, quality.
- **Fail-open is acceptable for non-price blocks.** Partial fundamental data is better than no packet.
- **Quality score must be honest.** Reflect actual data completeness and freshness.
- **Reuse discipline must be enforced.** Don't regenerate unnecessarily, but don't use stale data.
- **Integration with downstream skills must be explicit.** State how packet will be used.
- **Raw blocks must be preserved.** Audit trail for retrospective evaluation.
- **Artifact structure must be consistent.** Downstream skills depend on predictable format.

## Composition

- Builds on `market-data` and fail-open `fundamental-context`.
- Often feeds `analysis`, `reports`, `analysis-history`, and custom host-framework workflows.
- Integrates with `market-analyze` for market state assessment.
- Integrates with `technical-scan` for pattern recognition (if needed).
- Provides evidence base for `decision-support` position sizing.
- Provides execution context for `strategy-design` planning.
- Provides comparison baseline for `backtest-evaluator` retrospective analysis.
- Should be reused across multiple workflow stages to avoid redundant computation.
