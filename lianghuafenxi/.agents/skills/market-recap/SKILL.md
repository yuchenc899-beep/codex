---
name: market-recap
description: "Render region-aware market recap blueprints. Use when user wants the stage-7 review and communication frame for CN or US markets: recap structure, next-session posture template, and checklist-driven market review rather than live data retrieval."
argument-hint: [region]
allowed-tools: Bash(python3 *), Read, Glob
---

# Market Recap

Render a market recap blueprint for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/market-recap/run.py`
- Primary purpose: provide reusable market-review and next-session posture blueprints rather than live market payloads
- Workflow stage: stage 7 `Monitoring, Review, and Communication`
- Local executor guarantee: render a CN or US recap template in `markdown` or `prompt` form

## Use When

- The user wants a reusable CN or US recap framework.
- The user wants prompt-ready or markdown-ready posture guidance for daily review.
- The user wants a structured recap template for operator review, post-close process, or next-session planning.

## Do Not Use When

- The user wants actual live market data, index values, or fresh symbol analytics.
- The user wants one-symbol analysis. Use a market-facing symbol skill instead.
- The user expects the recap blueprint itself to contain populated market facts without another workflow supplying them.

## Inputs

- Optional `--region cn|us`; defaults to `cn`.
- Optional `--format markdown|prompt`; defaults to `markdown`.
- Usage note:
  - `markdown` is for human-readable operator review artifacts
  - `prompt` is for feeding another agent or workflow that will fill in the recap with actual observations

## Execution

### Step 1: Clarify recap purpose and scope

Determine what type of recap is needed:

**Recap purpose types:**
- **Operator review:** Daily post-close review for human operators
- **Agent recap generation:** Template for another agent to populate with fresh data
- **Communication artifact:** Structured message for stakeholder distribution
- **Workflow checkpoint:** Status summary at workflow stage completion
- **Session handoff:** Context transfer between sessions or operators

**Region-specific considerations:**

**CN market recap:**
- Trading hours: 9:30-11:30, 13:00-15:00 (CST)
- Key indices: SSE Composite, SZSE Component, ChiNext, STAR 50
- Market mechanics: Price limits (±10%/±20%), T+1 settlement, suspensions
- Key flows: Northbound capital, margin trading, dragon-tiger list
- Regulatory events: CSRC announcements, policy changes
- Sector rotation: Industry themes, concept stocks

**US market recap:**
- Trading hours: 9:30-16:00 (EST)
- Key indices: S&P 500, Nasdaq, Dow Jones, Russell 2000
- Market mechanics: Circuit breakers, after-hours trading
- Key flows: Institutional flows, options activity, futures positioning
- Economic events: Fed announcements, economic data releases
- Sector rotation: Growth vs. value, cyclical vs. defensive

### Step 2: Define recap structure

Establish comprehensive recap framework:

**Part 1: Market Overview**
- Session date and trading hours
- Major index performance (open, high, low, close, change %)
- Market breadth (advancers vs. decliners, new highs vs. new lows)
- Volume comparison (vs. average, vs. previous session)
- Market regime assessment (trending, ranging, volatile, quiet)

**Part 2: Sector Performance**
- Sector winners and losers (top 3 each)
- Sector rotation patterns (capital flows between sectors)
- Relative strength changes (which sectors outperformed/underperformed)
- Sector-specific catalysts (news, events, policy)

**Part 3: Notable Movers**
- Top gainers (symbols, % change, volume, catalysts)
- Top losers (symbols, % change, volume, catalysts)
- High volume stocks (unusual activity, reasons)
- Limit-up/limit-down stocks (CN market specific)
- Dragon-tiger list highlights (CN market specific)

**Part 4: Market Internals**
- Breadth indicators (advance/decline ratio, up/down volume)
- Volatility measures (VIX or equivalent, intraday range)
- Liquidity conditions (bid-ask spreads, market depth)
- Market sentiment (put/call ratio, fear/greed indicators)

**Part 5: Key Flows (CN market)**
- Northbound capital (net inflow/outflow, sector allocation)
- Margin trading (balance change, buy vs. sell)
- Share pledging (new pledges, releases, warnings)
- Block trades (large transactions, institutional activity)

**Part 6: Key Flows (US market)**
- Institutional flows (mutual funds, ETFs, hedge funds)
- Options activity (unusual options volume, put/call ratio)
- Futures positioning (index futures, sector futures)
- Foreign flows (international capital movements)

**Part 7: News and Events**
- Major news headlines (market-moving events)
- Economic data releases (GDP, inflation, employment, etc.)
- Corporate earnings (beats, misses, guidance changes)
- Regulatory announcements (policy changes, investigations)
- Geopolitical events (trade, politics, conflicts)

**Part 8: Technical Levels**
- Key support and resistance levels for major indices
- Trend status (uptrend, downtrend, sideways)
- Moving average positions (50-day, 200-day)
- Chart patterns (breakouts, breakdowns, consolidations)
- Volume profile (accumulation, distribution, neutral)

**Part 9: Next Session Outlook**
- Overnight developments (futures, international markets)
- Scheduled events (economic data, earnings, Fed speakers)
- Technical setup (key levels to watch, potential scenarios)
- Sector focus (which sectors to monitor)
- Risk factors (potential catalysts for volatility)

**Part 10: Watchlist Updates**
- Symbols added to watchlist (reasons)
- Symbols removed from watchlist (reasons)
- Position changes (entries, exits, size adjustments)
- Alert triggers (price levels, technical signals)

### Step 3: Specify template format

Choose appropriate format for intended use:

**Markdown format (for human operators):**
- Structured sections with headers
- Tables for numerical data (indices, sectors, movers)
- Bullet points for qualitative observations
- Links to detailed reports or charts
- Emphasis on readability and quick scanning

**Prompt format (for agent population):**
- Structured placeholders for data insertion
- Clear instructions for each section
- Data source specifications (where to get each piece of data)
- Validation checkpoints (what to verify before populating)
- Output format specifications (how to format populated data)

### Step 4: Add quality gates

Define validation requirements for populated recaps:

**Data freshness:**
- [ ] All market data is from the correct session date
- [ ] No stale data from previous sessions
- [ ] Overnight developments are current (not outdated)
- [ ] Economic calendar is up-to-date

**Data completeness:**
- [ ] All major indices have OHLC data
- [ ] Sector performance data is complete
- [ ] Notable movers list is populated
- [ ] Key flows data is available (if applicable)
- [ ] News and events section is populated

**Data consistency:**
- [ ] Index changes match breadth indicators
- [ ] Sector performance aligns with individual stock movers
- [ ] Volume data is consistent across sources
- [ ] Flow data reconciles with price action

**Interpretation quality:**
- [ ] Market regime assessment is evidence-based
- [ ] Sector rotation analysis is supported by data
- [ ] Notable mover catalysts are identified
- [ ] Next session outlook is grounded in current setup

**Communication clarity:**
- [ ] Technical jargon is explained or avoided
- [ ] Key takeaways are highlighted
- [ ] Action items are specific and actionable
- [ ] Risk factors are clearly stated

### Step 5: Run the local executor

```bash
python3 <bundle-root>/market-recap/run.py [--region cn|us] [--format markdown|prompt]
```

### Step 6: Deliver as review template

When delivering results, maintain proper framing:

**Template interpretation:**
- This is a recap structure, not a populated market report
- Placeholders indicate where fresh data should be inserted
- Quality gates define validation requirements for populated recaps
- Format choice determines intended downstream use

**Population guidance:**
- State which data sources should populate each section
- State freshness requirements for each data type
- State validation steps before finalizing populated recap
- State distribution channels for completed recap

**Scope clarity:**
- This is a communication template, not market analysis
- Populated recaps require fresh data from market-facing skills
- Template provides structure, not investment recommendations
- Operator judgment required for interpretation and action

**Limitation disclosure:**
- Template cannot guarantee data availability
- Template cannot validate data quality automatically
- Template cannot generate investment recommendations
- Template requires human oversight for critical decisions

## Output Contract

- Success format: reusable recap blueprint text beginning with `# Market Recap Template (<region>)`.
- `markdown` mode: a markdown block with structured sections, tables, and bullet points for human operators.
- `prompt` mode: a prompt-oriented blueprint with placeholders, instructions, and validation checkpoints for agent population.
- Caller-facing delivery standard:
  - **Ten-part structure:** Market overview, sector performance, notable movers, market internals, key flows, news and events, technical levels, next session outlook, watchlist updates, quality gates
  - **Template framing:** State clearly this is a review template, not a populated market report
  - **Region specificity:** CN market includes northbound capital, margin trading, dragon-tiger list; US market includes institutional flows, options activity, futures positioning
  - **Format clarity:** Identify intended downstream use (operator review, agent population, communication artifact)
  - **Population guidance:** State which data sources should populate each section and freshness requirements
  - **Quality gates:** Define validation requirements for populated recaps (freshness, completeness, consistency, interpretation, communication)
  - **Scope separation:** Keep template structure separate from current market observations
  - **No market views:** Template provides structure only, not investment recommendations or market analysis

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Unexpected runtime issues: readable failure text beginning with `执行失败:`.

## Key Rules

- **This skill provides the recap frame, not the live market payload.**
- **Keep the region explicit when the user’s market scope is ambiguous.**
- **Treat this as a process-support skill for monitoring and communication, not as an analysis substitute.**
- **Template structure must be comprehensive.** Cover all major recap dimensions (overview, sectors, movers, internals, flows, news, technicals, outlook, watchlist).
- **Region specificity is mandatory.** CN and US markets have different mechanics, flows, and regulatory environments.
- **Format choice determines use case.** Markdown for human operators, prompt for agent population.
- **Quality gates must be explicit.** Define validation requirements for freshness, completeness, consistency, interpretation, communication.
- **Population guidance is required.** State which data sources populate each section and freshness requirements.
- **No market analysis in template.** Template provides structure only, not investment recommendations.
- **Scope separation is critical.** Keep template structure separate from current market observations.

## Composition

- Can be embedded into broader reporting or monitoring workflows.
- Pairs naturally with `session-status`, market-facing analysis skills, and `feishu-notify` for recap delivery.
