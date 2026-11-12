# Quantitative Workflow Integration Guide

This document provides detailed guidance on how A-Stockit skills integrate into the complete quantitative finance workflow, from strategy conception through live trading.

## Overview

The A-Stockit skill system now supports the full quantitative workflow lifecycle with 25 skills (24 core + 1 meta-skill):

1. **Strategy Design & Hypothesis Formation** → `analysis`, `strategy-design`
2. **Data Collection & Quality Assurance** → `data-sync`, `market-data`, `stock-data`, `fundamental-context`, `news-intel`
3. **Data Cleaning & Normalization** → `market-data`, `fundamental-context`
4. **Feature Engineering & Signal Construction** → `strategy-design`, `market-analyze`, `technical-scan`
5. **Backtesting & Performance Evaluation** → `backtest-evaluator`, `analysis-history`
6. **Risk Management & Position Sizing** → `decision-support`, `strategy-design`, `decision-dashboard`
7. **Live Trading & Monitoring** → `paper-trading`, `session-status`, `market-recap`, `feishu-notify`

**Cross-Cutting:**
- **Error Recovery:** `fix-everything` (automatic invocation on any failure)
- **Batch Operations:** `watchlist-import`, `watchlist`, `market-screen`, `decision-dashboard`
- **Artifact Management:** `reports`, `strategy-chat`, `session-status`

## Detailed Workflow Integration

### Stage 1: Strategy Design & Hypothesis Formation

**Primary Skills:** `analysis`, `strategy-design`

**Workflow:**
1. User articulates investment hypothesis or asks exploratory questions
2. Agent routes to `analysis` for thesis-level research or `market-brief` for quick synthesis
3. `analysis` enforces mandatory thesis structure:
   - Thesis statement (falsifiable)
   - Key drivers (3-5, ranked, monitorable)
   - Primary catalyst (or explicit statement that none exists)
   - Variant view (intellectually honest alternative)
   - Disconfirming evidence (current, material)
   - Invalidation conditions (specific, observable)
   - Evidence gaps (explicit acknowledgment)

**Quality Gates:**
- [ ] Hypothesis is falsifiable (can be proven wrong)
- [ ] Theoretical basis is articulated (not just data mining)
- [ ] Time horizon matches expected signal decay
- [ ] Universe is tradeable (liquidity, access, costs)
- [ ] Failure conditions are specific and monitorable

**Agent Instructions:**
When user asks about strategy design or investment thesis:
1. Assess evidence sufficiency using `_docs/authoring/evidence-sufficiency.md`
2. Route to `analysis` if user asks "why," "what drives this," "what are the risks," or needs IC-grade memo
3. Route to `market-brief` if user wants fast current positioning without thesis pressure-testing
4. Enforce mandatory thesis structure in `analysis` outputs
5. Do not proceed to execution planning until thesis is accepted

**Error Recovery:**
- All skills integrate with `fix-everything` meta-skill for autonomous error recovery
- Recovery strategies: retry, alternative source, graceful degradation, data reconstruction, workflow rerouting, config auto-fix, dependency auto-install, simplified approach
- Users only see clean results or clear escalation questions
- Technical errors never exposed to non-technical users

**Example User Queries:**
- "What's the investment case for 600519?"
- "Why is this stock moving up?"
- "What are the risks if I buy this?"
- "What would invalidate this trade idea?"

**Example Agent Response Pattern:**
```
I'll use the analysis skill to build a thesis-disciplined research memo for 600519.

[Execute analysis skill]

Based on the analysis:

**Thesis:** [One-sentence falsifiable statement]

**Key Drivers:**
1. [Most important driver]
2. [Second driver]
3. [Third driver]

**Primary Catalyst:** [Specific event or "No identifiable catalyst; thesis depends on..."]

**Variant View:** [Intellectually honest alternative interpretation]

**Disconfirming Evidence:** [Current observations that weaken the thesis]

**Invalidation Conditions:**
- Price-based: [Specific level]
- Non-price: [Specific conditions]

**Evidence Gaps:** [What we don't know]

This is a thesis-level analysis suitable for investment committee review. For execution planning, we can proceed to strategy-design.
```

---

### Batch Screening & Decision Workflow

**Primary Skills:** `watchlist-import`, `market-screen`, `decision-dashboard`

**Workflow:**
1. Import universe via `watchlist-import` (with symbol normalization)
2. Screen universe via `market-screen` (comparative ranking)
3. Generate batch decisions via `decision-dashboard` (Buy/Watch/Avoid/Hold/Reduce/Exit)

**Quality Gates:**
- [ ] Symbol resolution rate > 90%
- [ ] Screening completeness (skip accounting documented)
- [ ] Decision logic consistent across symbols
- [ ] Position sizing respects portfolio constraints
- [ ] Comparative metrics are apples-to-apples

**Agent Instructions:**
When user wants to screen multiple stocks or generate batch decisions:

**For `watchlist-import`:**
1. Accept various input formats (CSV, text list, THS export)
2. Normalize symbols to standard format (6-digit with exchange)
3. Report resolution success rate
4. Flag unresolved symbols for user review

**For `market-screen`:**
1. Apply consistent screening criteria across universe
2. Rank stocks by composite score or specific metrics
3. Document skip reasons (data unavailable, suspended, etc.)
4. Provide comparative context (percentile ranks, sector comparison)

**For `decision-dashboard`:**
1. Generate decision for each symbol (Buy/Watch/Avoid/Hold/Reduce/Exit)
2. Provide consistent reasoning across symbols
3. Respect portfolio constraints (concentration limits, sector limits)
4. Include position sizing for actionable decisions
5. Flag high-conviction opportunities

**Error Recovery:**
- Symbol resolution failures trigger alternative lookup strategies
- Data gaps handled with graceful degradation (partial results)
- Screening errors isolated per symbol (don't fail entire batch)
- Decision generation continues with available data

**Example User Queries:**
- "Screen these 50 stocks for me"
- "Import my watchlist and tell me what to buy"
- "Generate decisions for my portfolio"
- "Which stocks in this list are worth buying?"

**Example Agent Response Pattern:**
```
I'll process your watchlist through the batch screening workflow.

[Execute watchlist-import]

**Import Results:**
- Total symbols: 50
- Successfully resolved: 47 (94%)
- Failed resolution: 3 (symbols: [list])

[Execute market-screen on resolved symbols]

**Screening Results:**
- Screened: 45 stocks
- Skipped: 2 (suspended, data unavailable)
- Top 10 by composite score: [list with scores]

[Execute decision-dashboard]

**Batch Decisions:**

**Buy (5 stocks):**
1. 600519 - Strong momentum + fundamental support (conviction: 8/10)
2. 000858 - Breakout with volume confirmation (conviction: 7/10)
[...]

**Watch (12 stocks):**
1. 600036 - Approaching entry zone, wait for confirmation
[...]

**Hold (15 stocks):**
1. 601318 - Maintain position, no new action
[...]

**Avoid (13 stocks):**
1. 600000 - Weak technicals, downtrend intact
[...]

**Portfolio Impact:**
- New capital required: ¥[X] for Buy recommendations
- Portfolio concentration: [Y%] in top 5 positions
- Sector exposure: [breakdown]

**Quality Notes:**
- All decisions based on data through [date]
- 2 stocks skipped due to data gaps (documented in report)
- Position sizing respects 5% single-stock limit
```

---

### Workflow Continuity & Session Management

**Primary Skills:** `session-status`, `reports`, `analysis-history`, `strategy-chat`

**Workflow:**
1. Use `session-status` to check current workflow state
2. Use `reports` to retrieve prior artifacts
3. Use `analysis-history` to review historical analyses
4. Use `strategy-chat` for multi-turn workflow continuation

**Quality Gates:**
- [ ] Session context is current and relevant
- [ ] Artifacts are properly versioned and timestamped
- [ ] Historical analyses include provenance metadata
- [ ] Multi-turn conversations maintain workflow discipline

**Agent Instructions:**
When resuming or continuing workflow:

**For `session-status`:**
1. Check current workflow state before starting new analysis
2. Identify available artifacts and their freshness
3. Surface relevant prior work to avoid duplication
4. Flag stale data that needs refresh

**For `reports`:**
1. Retrieve exact stored artifacts (don't regenerate)
2. Surface artifact metadata (generation time, command, version)
3. Distinguish artifact content from fresh interpretation
4. Recommend regeneration if artifact is stale

**For `analysis-history`:**
1. Compare how views changed over time
2. Identify thesis evolution or pivot points
3. Maintain rigorous provenance (what was known when)
4. Guard against hindsight bias in comparisons

**For `strategy-chat`:**
1. Maintain workflow context across turns
2. Reference prior decisions and reasoning
3. Update views when new information arrives
4. Keep conversation focused on actionable workflow steps

**Error Recovery:**
- Session state corruption triggers automatic recovery
- Missing artifacts prompt regeneration with user confirmation
- Stale data flagged with refresh recommendations
- Context loss handled with graceful degradation

**Example User Queries:**
- "What was I working on?"
- "Show me my previous analysis of 600519"
- "Has anything changed since last week?"
- "Continue our discussion about that strategy"

**Example Agent Response Pattern:**
```
Let me check your current session state.

[Execute session-status]

**Current Session:**
- Active analyses: 3
- Recent artifacts: 5 (last 7 days)
- Data freshness: Current through [date]
- Pending actions: 2

**Recent Work:**
1. Analysis of 600519 (3 days ago) - Thesis: trend continuation
2. Decision support for 000858 (2 days ago) - Action: Buy
3. Paper trade execution for 600519 (1 day ago) - Status: Open position

**Available Artifacts:**
- 600519_analysis_[timestamp].md
- 000858_decision_[timestamp].md
- paper_portfolio_[timestamp].json

**Recommendations:**
- 600519 analysis is 3 days old; consider refresh if market conditions changed
- Paper position in 600519 should be monitored against invalidation conditions
- No stale data detected

Would you like to continue with any of these workflows?
```

---

### Stage 2-4: Data Collection, Cleaning, and Feature Engineering

**Primary Skills:** `data-sync`, `market-data`, `stock-data`, `fundamental-context`

**Workflow:**
1. Data collection happens automatically through `data-sync` or on-demand through `market-data`
2. Data cleaning and normalization are handled by `market-data` and `fundamental-context`
3. Feature engineering is implicit in `market-analyze` and `technical-scan`

**Quality Gates:**
- [ ] Data coverage is complete for analysis period
- [ ] Point-in-time correctness verified (no look-ahead bias)
- [ ] Survivorship bias addressed (delistings included)
- [ ] Corporate actions properly adjusted
- [ ] A-share specific mechanics captured

**Agent Instructions:**
These stages are largely automated, but agent should:
1. Verify data freshness before analysis
2. Flag data quality issues if detected
3. Acknowledge data limitations in analysis outputs
4. Use `session-status` to check data sync status

**Error Recovery:**
- Data sync failures trigger alternative source attempts
- Missing data handled with graceful degradation
- Stale data flagged with refresh recommendations
- Data quality issues surfaced transparently

**Example User Queries:**
- "Do we have current data for 600519?"
- "When was the data last updated?"
- "Is the fundamental data current?"

**Example Agent Response Pattern:**
```
Let me check data status using session-status.

[Execute session-status]

Data status for 600519:
- Price data: Current through [date]
- Fundamental data: Last updated [date] (Q[X] [YEAR])
- Data quality: [Any issues flagged]

Data is [sufficient/insufficient] for current analysis. [If insufficient, recommend data-sync]
```

---

### Stage 5: Backtesting & Performance Evaluation

**Primary Skills:** `backtest-evaluator`, `analysis-history`, `reports`

**Workflow:**
1. After strategy is designed, use `backtest-evaluator` for retrospective evaluation
2. Use `analysis-history` to compare how views changed over time
3. Use `reports` to retrieve exact stored artifacts

**Quality Gates:**
- [ ] Backtest has no look-ahead bias
- [ ] Transaction costs are realistic
- [ ] Execution constraints are modeled
- [ ] Performance metrics are comprehensive
- [ ] Robustness checks are performed

**Agent Instructions:**
When user wants retrospective evaluation:
1. Use `backtest-evaluator` with explicit `--state` path for reproducibility
2. Enforce mandatory evaluation structure:
   - Outcome summary (aligned/diverged/mixed/inconclusive)
   - What was not knowable then (hindsight bias guard)
   - Evaluation assumptions (entry/exit mechanics)
   - Realism limits (what's not modeled)
   - Process insights (not predictive proof)
3. Never use "validated/invalidated" language
4. Frame as process improvement, not proof of skill

**Error Recovery:**
- Missing artifacts trigger user prompt for correct path
- Incomplete evaluation data handled with partial results
- Calculation errors isolated and reported clearly
- Stale reference data flagged with warnings

**Example User Queries:**
- "How did that 600519 analysis from last month perform?"
- "Was the thesis correct?"
- "Should I trust this signal?"

**Example Agent Response Pattern:**
```
I'll evaluate the prior 600519 analysis using backtest-evaluator.

[Execute backtest-evaluator with --state path]

**Retrospective Evaluation:**

**Outcome:** Price moved [X%] over [N] days. Outcome [aligned with/diverged from] thesis.

**What Was Not Knowable Then:**
- [Event 1 that occurred after decision]
- [Event 2 that occurred after decision]
- [Information that would have changed the thesis]

**Evaluation Assumptions:**
- Entry: [Price and timing]
- Exit: [Price and timing]
- Stop handling: [How modeled]
- Realism limits: No liquidity modeling, no gap handling, no limit behavior

**Process Insights:**
- [What the evaluation reveals about research process]
- [What would improve next similar analysis]

Important: This evaluation shows outcome alignment, not predictive proof. The original thesis may have been right for wrong reasons, or wrong despite reasonable logic.
```

---

### Stage 6: Risk Management & Position Sizing

**Primary Skills:** `decision-support`, `strategy-design`

**Workflow:**
1. After thesis is accepted, use `decision-support` for action and sizing
2. Use `strategy-design` for execution planning
3. Both skills enforce rigorous risk disclosure

**Quality Gates:**
- [ ] Position sizing method is appropriate for strategy
- [ ] Risk limits are clearly defined and monitorable
- [ ] Stop-loss rules account for A-share constraints
- [ ] Rebalancing frequency balances alpha capture and costs
- [ ] Portfolio construction is robust to estimation error

**Agent Instructions:**
When user wants position sizing or execution planning:

**For `decision-support`:**
1. Enforce mandatory three-part structure:
   - Part 1: Conditional action frame
   - Part 2: Explicit assumptions (user-supplied vs. defaulted)
   - Part 3: Non-modeled risks (systematic disclosure)
2. Label confidence as "heuristic conviction score" (never probability)
3. Surface A-share specific risks: liquidity, gaps, limits, suspensions, T+1

**For `strategy-design`:**
1. Validate execution context (market state, regime, liquidity)
2. Select appropriate style (breakout/trend/range/defensive)
3. Construct technically rigorous zones (entry, stop, target)
4. Model execution realism (slippage, costs, multi-day if needed)
5. Provide actionable monitoring checklist

**Error Recovery:**
- Market data failures trigger alternative sources or cached data
- Calculation errors isolated and reported clearly
- Missing context handled with explicit assumptions
- Invalid parameters rejected with clear guidance

**Example User Queries:**
- "Should I buy 600519?"
- "How much should I buy?"
- "Where should I set my stop?"
- "How should I execute this trade?"

**Example Agent Response Pattern for decision-support:**
```
I'll use decision-support to generate conditional action and sizing guidance for 600519.

[Execute decision-support with account parameters]

**Part 1: Conditional Action Frame**
- Action: [Buy/Hold/Reduce/Avoid/Watch]
- Heuristic conviction score: [X/10] (not a probability)
- Target position: [X shares or X% of portfolio]
- Quantity: [X shares]
- Reference price: [¥X]
- Stop loss: [¥X] ([Y%] below entry)
- Take profit: [¥X] ([Z%] above entry)
- Risk budget: [¥X or X% of portfolio]

**Reasoning:**
1. [Factor 1]
2. [Factor 2]
3. [Factor 3]

**Part 2: Explicit Assumptions**
- Capital: [User-supplied: ¥X / Defaulted: ¥Y]
- Cash available: [User-supplied: ¥X / Defaulted: ¥Y]
- Current position: [User-supplied: X shares / Defaulted: 0]
- Risk tolerance: [User-supplied: X% / Defaulted: Y%]
- Data window: [Start] to [End]

**Part 3: Non-Modeled Risks**
- Liquidity risk: [Position size vs. ADV analysis]
- Gap risk: [Historical gap behavior]
- Limit behavior: [A-share ±10% limits may prevent stop execution]
- Stop slippage: [Actual fills may differ from reference levels]
- Catalyst uncertainty: [Timing and outcome uncertainty]
- Regime sensitivity: [What regime change would invalidate]

**Important:** This is conditional guidance requiring human judgment, not an executable order.
```

**Example Agent Response Pattern for strategy-design:**
```
I'll use strategy-design to create an execution plan for 600519.

[Execute strategy-design with style and holding period]

**Part 1: Execution Style & Rationale**
- Selected style: [Breakout/Trend/Range/Defensive]
- Rationale: [Why this style matches current market state]
- Key assumptions: [Regime, volatility, liquidity]

**Part 2: Entry Plan**
- Primary entry zone: ¥[X] to ¥[Y]
- Entry confirmation: [Specific signals]
- Order type: [Market/Limit/VWAP]
- Timing: [Opening auction/Intraday/Closing auction]
- Multi-day plan: [If position size > 5% ADV]

**Part 3: Risk Management**
- Initial stop: ¥[X] ([Y%] below entry)
- Trailing stop: [Activation level and trailing distance]
- Position size: [X% of portfolio]
- Maximum loss: ¥[X] or [Y%]
- A-share risks: [Limits, gaps, suspensions, T+1]

**Part 4: Profit Targets**
- Primary target (50%): ¥[X] ([Y%] gain, [Z]:1 R:R)
- Secondary target (30%): ¥[X] ([Y%] gain, [Z]:1 R:R)
- Final target (20%): Trail with stop or ¥[X]

**Part 5: Holding Period & Rebalancing**
- Expected holding: [N] days
- Maximum holding: [M] days
- Time-based exit: [Conditions]
- Rebalancing triggers: [Signal decay, regime shift, etc.]

**Part 6: Monitoring Checklist**
Daily: [Items]
Weekly: [Items]
Events: [Items]
Invalidation: [Conditions]

**Part 7: Execution Cost Estimate**
- Commission: ¥[X] (0.03%)
- Stamp duty: ¥[Y] (0.1% on sell)
- Slippage: ¥[Z] ([W%])
- Total cost: ¥[Total]
- Net expected return: [X%] after costs

**Important:** This is a conditional execution plan, not a guaranteed fill.
```

---

### Stage 7: Live Trading & Monitoring

**Primary Skills:** `paper-trading`, `session-status`

**Workflow:**
1. Before live trading, validate strategy with `paper-trading`
2. Execute simulated trades with realistic constraints
3. Monitor paper portfolio performance
4. Use `session-status` for runtime monitoring

**Quality Gates:**
- [ ] Pre-trade checks are comprehensive and automated
- [ ] Execution algorithms are appropriate for strategy
- [ ] Real-time monitoring covers all critical metrics
- [ ] Post-trade analysis is systematic and actionable
- [ ] Incident response procedures are documented

**Agent Instructions:**
When user wants to execute or monitor trades:

**For `paper-trading`:**
1. Perform comprehensive pre-trade validation
2. Model execution realistically (slippage, costs, constraints)
3. Track position-level detail (cost basis, T+1 availability)
4. Monitor risk continuously (position limits, concentration)
5. Provide comprehensive performance metrics
6. Always include simulation disclaimer

**For monitoring:**
1. Use `session-status` for runtime context
2. Check for risk alerts (drawdown, concentration, etc.)
3. Monitor invalidation conditions from original analysis
4. Recommend rebalancing or exit if conditions change

**Error Recovery:**
- Portfolio state corruption triggers automatic recovery
- Missing position data handled with partial results
- Calculation errors isolated per position
- Alert system failures escalate to user notification

**Example User Queries:**
- "Execute a paper trade for 600519"
- "Show my paper portfolio"
- "How is my paper portfolio performing?"
- "Should I exit this position?"

**Example Agent Response Pattern for paper trade execution:**
```
I'll execute a simulated trade for 600519 using paper-trading.

[Execute paper-trading with side, quantity, price]

**Trade Confirmation:**
- Trade ID: [ID]
- Symbol: 600519
- Side: Buy
- Quantity: 1,000 shares (10 lots)
- Price: ¥18.50
- Execution time: [Timestamp]

**Transaction Costs:**
- Commission: ¥5.55 (0.03%)
- Stamp duty: ¥0 (buy side)
- Slippage: ¥18.50 (0.1% assumed)
- Total cost: ¥18,524.05

**Updated Position:**
- Shares held: 0 → 1,000
- Average cost: ¥18.524
- Market value: ¥18,500 (at execution price)
- Unrealized P&L: -¥24.05 (transaction costs)
- Position weight: [X%] of portfolio
- T+1 status: Cannot sell until [next trading day]

**Updated Account:**
- Cash: ¥[Before] → ¥[After]
- Portfolio value: ¥[Before] → ¥[After]
- Total return: [X%]

**Risk Alerts:**
[Any triggered alerts]

**Important:** This is simulated trading only; no real capital at risk.
```

**Example Agent Response Pattern for portfolio monitoring:**
```
I'll check your paper portfolio status.

[Execute paper-trading without --side]

**Portfolio Summary:**
- Portfolio value: ¥[X]
- Cash balance: ¥[Y] ([Z%] of portfolio)
- Invested capital: ¥[A]
- Total return: ¥[B] ([C%])
- Realized P&L: ¥[D]
- Unrealized P&L: ¥[E]

**Positions:** [N positions]
[Table of positions with symbol, shares, cost, price, value, P&L, weight, days held]

**Performance Metrics:**
- Win rate: [X%] ([Y] wins / [Z] total trades)
- Average win: ¥[X]
- Average loss: ¥[Y]
- Profit factor: [X]
- Transaction costs: ¥[Y] ([Z%] of P&L)

**Risk Metrics:**
- Largest position: [X%]
- Top 5 concentration: [Y%]
- Gross exposure: [Z%]
- Current drawdown: [W%] from peak

**Alerts:**
[Any triggered risk alerts or positions requiring attention]

**Monitoring Recommendations:**
[Based on original analysis invalidation conditions]
```

---

## Workflow Decision Tree

```
User Query
    ↓
Is this about strategy/thesis?
    Yes → Evidence sufficient for thesis?
        Yes → Use `analysis` (mandatory thesis structure)
        No → Use `market-brief` (descriptive synthesis)
    No ↓
Is this about position sizing/action?
    Yes → Use `decision-support` (three-part structure)
    No ↓
Is this about execution planning?
    Yes → Use `strategy-design` (seven-part structure)
    No ↓
Is this about retrospective evaluation?
    Yes → Use `backtest-evaluator` (honest outcome language)
    No ↓
Is this about historical comparison?
    Yes → Use `analysis-history` (rigorous provenance)
    No ↓
Is this about artifact retrieval?
    Yes → Use `reports` (faithful restatement)
    No ↓
Is this about simulated trading?
    Yes → Use `paper-trading` (realistic modeling)
    No ↓
Is this about multi-turn discussion?
    Yes → Use `strategy-chat` (disciplined continuity)
    No ↓
Route to appropriate skill based on intent
```

---

## Quality Assurance Checklist

Before delivering any workflow output, verify:

### For Strategy Design (`analysis`):
- [ ] Thesis statement is falsifiable
- [ ] Key drivers are specific and monitorable (3-5 maximum)
- [ ] Variant view is intellectually honest (not strawman)
- [ ] Disconfirming evidence is current and material
- [ ] Invalidation conditions are specific and observable
- [ ] Evidence gaps are acknowledged explicitly

### For Position Sizing (`decision-support`):
- [ ] Three-part structure is complete (action, assumptions, risks)
- [ ] Confidence is labeled as "heuristic conviction score"
- [ ] User-supplied vs. defaulted inputs are distinguished
- [ ] Non-modeled risks are disclosed systematically
- [ ] A-share constraints are addressed (limits, gaps, T+1)
- [ ] Output is framed as conditional guidance, not orders

### For Execution Planning (`strategy-design`):
- [ ] Seven-part structure is complete
- [ ] Style selection matches current market regime
- [ ] Entry/stop/target zones are technically rigorous
- [ ] Transaction costs are estimated realistically
- [ ] Multi-day execution planned if position size > 5% ADV
- [ ] Monitoring checklist is actionable
- [ ] A-share constraints are modeled (limits, T+1, suspensions)

### For Retrospective Evaluation (`backtest-evaluator`):
- [ ] Honest outcome language (aligned/diverged, not validated/invalidated)
- [ ] "What Was Not Knowable Then" section included
- [ ] Evaluation assumptions stated explicitly
- [ ] Realism limits disclosed systematically
- [ ] Framed as process improvement, not predictive proof

### For Paper Trading (`paper-trading`):
- [ ] Pre-trade validation performed
- [ ] Execution modeled realistically (slippage, costs)
- [ ] A-share constraints enforced (lot size, T+1, limits)
- [ ] Position tracking includes cost basis and T+1 status
- [ ] Performance metrics are comprehensive
- [ ] Simulation disclaimer included

---

## Common Agent Mistakes to Avoid

1. **Routing to `market-brief` when user asks "why" or "what are the risks"**
   - Correct: Route to `analysis` for thesis-level rigor

2. **Not enforcing mandatory thesis structure in `analysis`**
   - Correct: Require all seven elements (thesis, drivers, catalyst, variant, disconfirming, invalidation, gaps)

3. **Presenting `decision-support` output as executable orders**
   - Correct: Frame as "conditional guidance requiring human judgment"

4. **Using "validated/invalidated" language in `backtest-evaluator`**
   - Correct: Use "outcome aligned/diverged/mixed/inconclusive"

5. **Not disclosing which inputs were defaulted vs. user-supplied**
   - Correct: Always distinguish in Part 2 of `decision-support` output

6. **Ignoring A-share specific constraints**
   - Correct: Address lot sizes, T+1, price limits, stamp duty in every relevant output

7. **Not including "What Was Not Knowable Then" in retrospective evaluation**
   - Correct: Mandatory hindsight bias guard in every `backtest-evaluator` output

8. **Treating paper trading as equivalent to live trading**
   - Correct: Always include simulation disclaimer and acknowledge limitations

9. **Not checking invalidation conditions during monitoring**
   - Correct: Reference original analysis invalidation conditions when monitoring positions

10. **Blending artifact content with fresh interpretation without labeling**
    - Correct: Distinguish what came from saved artifacts vs. current computation

---

## Integration with Existing Skills

This quantitative workflow framework integrates with and extends the institutional research quality improvements:

- **Thesis discipline** from `analysis` improvements now includes quantitative workflow context
- **Risk disclosure** from `decision-support` improvements now includes execution modeling
- **Retrospective honesty** from `backtest-evaluator` improvements now includes process focus
- **Provenance integrity** from history skills now supports workflow audit trails

The complete system now supports both:
1. **Institutional research quality** (thesis rigor, risk disclosure, retrospective honesty)
2. **Quantitative workflow completeness** (strategy design through live trading)

This makes A-Stockit suitable for professional quantitative investment workflows while maintaining the research discipline expected from institutional-grade analysis.
