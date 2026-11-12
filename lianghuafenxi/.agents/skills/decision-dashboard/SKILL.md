---
name: decision-dashboard
description: "Build a batch decision dashboard for multiple symbols. Use when user wants the stage-6 watchlist action surface: action distribution, focus list, and portfolio-assumption-aware triage before deeper single-name review."
argument-hint: [symbol-or-list]
allowed-tools: Bash(python3 *), Read, Glob
---

# Decision Dashboard

Build a batch decision dashboard for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/decision-dashboard/run.py`
- Primary purpose: summarize conditional actions, scores, and regimes across a symbol set instead of returning one-symbol reports
- Research layer: batch decision support (Stage 6: Risk Management & Position Sizing - Portfolio-level view)
- Workflow stages: stage 1 `Universe Review` and stage 6 `Risk Management & Position Sizing` in batch form
- Local executor guarantee: compute per-symbol decision summaries under shared account assumptions, aggregate action counts, and return a ranked focus list

## Use When

- The user wants a batch decision board rather than raw ranking.
- The user wants action distribution across a watchlist.
- The user wants to shortlist names before moving into one-symbol detail.
- The user wants portfolio-level view of potential actions.
- The user wants to understand aggregate exposure and risk across watchlist.
- The user wants daily monitoring dashboard for existing positions and watchlist.

## Do Not Use When

- The user wants a complete report for one symbol. Use `market-brief` or `analysis`.
- The user only wants ranked screening output. Use `market-screen`.
- The user wants only watchlist ingestion. Use `watchlist-import`.
- The user expects this to produce a portfolio optimizer, cross-name correlation control, or live order book. It does not.
- The user wants actual portfolio construction with correlation and diversification. This skill does not model cross-name correlations.

## Inputs

- Direct positional symbols.
- Optional `--file PATH`: plain text file containing one symbol per line.
- Optional `--dir PATH`: directory of per-symbol CSV files.
- Optional `--capital`, `--cash`, `--risk`, `--max-position`: influence dashboard decision framing.
- Optional `--top N`, `--start`, `--end`, `--source`.
- Important boundary: `--file` is a symbol-list file, not a market-data CSV.
- Assumption note:
  - the same account assumptions are applied across the batch
  - the agent should identify when those assumptions are user-supplied versus defaulted

## Execution

### Step 1: Define dashboard scope and portfolio context

Before building dashboard, clarify objectives and constraints:

**Dashboard objectives:**
- [ ] Daily monitoring (track existing positions and watchlist)
- [ ] Idea triage (identify new opportunities from watchlist)
- [ ] Position review (assess current holdings for hold/reduce/exit)
- [ ] Risk review (identify concentration, exposure, risk flags)
- [ ] Action planning (prioritize symbols for deeper analysis)

**Portfolio context:**
- [ ] Total capital available
- [ ] Current cash balance
- [ ] Existing positions (symbols, quantities, cost basis)
- [ ] Risk tolerance (max position size, max portfolio risk)
- [ ] Concentration limits (max % per position, per sector)

**Shared assumptions:**
- **Capital:** Total portfolio value (default: user-supplied or session default)
- **Cash:** Available cash for new positions (default: 100% of capital if no positions)
- **Risk per position:** Max % of capital per position (default: 5-10%)
- **Max position count:** Max number of positions (default: 10-20)
- **Rebalancing threshold:** When to adjust positions (default: ±20% from target)

**A-share specific constraints:**
- T+1 settlement (cannot sell same-day purchases)
- Lot size (100 shares minimum)
- Price limits (±10% or ±20%)
- Suspension risk
- Margin requirements (if using margin)

### Step 2: Validate universe and collect data

Process watchlist with quality validation:

**Universe validation:**
- [ ] All symbols are valid A-share tickers
- [ ] Symbols are currently tradeable (not delisted)
- [ ] Symbols are not suspended (or suspension flagged)
- [ ] Symbols have sufficient data history (minimum 60 days)
- [ ] Symbols meet minimum liquidity requirements

**For each symbol, collect:**
- Market data (OHLCV, normalized and validated)
- Technical features (trend, momentum, volatility, volume)
- Market state (score, regime, bias, risk flags)
- Current position (if held: quantity, cost basis, P&L)
- Liquidity metrics (volume, turnover, bid-ask spread)

**Partial failure handling:**
- Skip invalid symbols and record reason
- Skip suspended symbols and flag for monitoring
- Skip insufficient data symbols and record reason
- Continue processing remaining symbols

### Step 3: Generate per-symbol decision summaries

For each valid symbol, generate conditional action:

**Decision logic (consistent with decision-support):**

**For symbols NOT currently held:**
- **Buy (score 70-100, bullish bias, no major risk flags):**
  - Suggested position size (% of capital)
  - Entry price range
  - Initial stop-loss level
  - Confidence level
- **Watch (score 50-69, neutral/uncertain bias, or minor risk flags):**
  - Reason for watching (waiting for confirmation, better entry, etc.)
  - Trigger conditions (what would change this to Buy)
- **Avoid (score 0-49, bearish bias, or major risk flags):**
  - Reason for avoiding (downtrend, overbought, high risk, etc.)

**For symbols currently held:**
- **Hold (score 60-100, position within target range, no major risk flags):**
  - Current position size vs. target
  - Unrealized P&L
  - Stop-loss level
  - Monitoring conditions
- **Reduce (score 40-59, position above target, or moderate risk flags):**
  - Suggested reduction amount (shares or %)
  - Reason for reduction (risk management, rebalancing, etc.)
  - Target position size after reduction
- **Exit (score 0-39, major risk flags, or stop-loss triggered):**
  - Reason for exit (stop-loss, invalidation, risk, etc.)
  - Expected exit price
  - Realized P&L (if exited)

**Position sizing (for Buy actions):**
- **Fixed sizing:** Equal weight across all positions (e.g., 5% each for 20-position portfolio)
- **Score-based sizing:** Higher score = larger position (within limits)
- **Risk-based sizing:** Size based on volatility (higher vol = smaller position)
- **Liquidity-constrained:** Limit position to % of ADV (e.g., max 5% of 20-day ADV)

**Risk checks:**
- [ ] Position size within limits (max % per position)
- [ ] Total exposure within limits (max % invested)
- [ ] Concentration within limits (max % per sector, if tracked)
- [ ] Cash sufficiency (enough cash for suggested buys)
- [ ] Liquidity sufficiency (can execute without excessive impact)

### Step 4: Aggregate action distribution

Summarize actions across entire watchlist:

**Action counts:**
- **Buy:** Count of symbols with Buy recommendation
- **Watch:** Count of symbols with Watch recommendation
- **Avoid:** Count of symbols with Avoid recommendation
- **Hold:** Count of currently held symbols with Hold recommendation
- **Reduce:** Count of currently held symbols with Reduce recommendation
- **Exit:** Count of currently held symbols with Exit recommendation

**Action distribution analysis:**
- % of watchlist in each action category
- Trend over time (if historical dashboards available)
- Comparison to previous dashboard (if available)

**Aggregate exposure:**
- Total suggested new capital deployment (sum of Buy position sizes)
- Total suggested capital reduction (sum of Reduce/Exit position values)
- Net capital change (deployment - reduction)
- Resulting cash balance after all actions
- Resulting total exposure (% of capital invested)

**Aggregate risk:**
- Total portfolio risk (sum of position risks, if calculable)
- Concentration risk (largest position %, largest sector %)
- Liquidity risk (% of positions with low liquidity)
- A-share specific risks (% with price limit risk, suspension risk, etc.)

### Step 5: Generate ranked focus list

Prioritize symbols for deeper review:

**Focus list criteria:**
- **High priority (immediate action):**
  - Buy recommendations with score > 80
  - Exit recommendations (stop-loss triggered, major risk flags)
  - Reduce recommendations with significant risk flags
- **Medium priority (review soon):**
  - Buy recommendations with score 70-79
  - Watch recommendations near Buy threshold
  - Hold recommendations with moderate risk flags
- **Low priority (monitor):**
  - Watch recommendations not near threshold
  - Hold recommendations with no risk flags
  - Avoid recommendations (no action needed)

**Focus list ranking:**
- Sort by priority (high > medium > low)
- Within priority, sort by score (descending)
- Within same score, sort by momentum strength
- Break further ties by volume confirmation

**Focus list output:**
For each symbol in focus list (top 10-20):
- Symbol, name, board
- Current action (Buy/Watch/Avoid/Hold/Reduce/Exit)
- Score, trend, regime, bias
- Priority level (high/medium/low)
- Key reason (why this action, why this priority)
- Suggested next step (run market-brief, decision-support, etc.)

### Step 6: Generate dashboard report

Organize findings into structured dashboard:

**Part 1: Dashboard Summary**
- Universe source and size
- Dashboard timestamp
- Valid symbols processed
- Symbols skipped (by category)
- Portfolio context (capital, cash, positions)

**Part 2: Action Distribution**
- Action counts (Buy/Watch/Avoid/Hold/Reduce/Exit)
- Action percentages
- Trend vs. previous dashboard (if available)
- Aggregate capital deployment/reduction
- Resulting cash and exposure

**Part 3: Aggregate Risk Summary**
- Total portfolio exposure (% of capital)
- Largest position (symbol, %)
- Concentration risk (sector, if tracked)
- Liquidity risk (% low liquidity positions)
- A-share specific risks (price limits, suspensions, etc.)

**Part 4: Focus List**
For each high/medium priority symbol:
- Symbol, action, score, regime
- Priority level and reason
- Suggested next step
- Key risk flags (if any)

**Part 5: Position Review (if positions held)**
For each current position:
- Symbol, quantity, cost basis
- Current price, market value
- Unrealized P&L ($ and %)
- Action (Hold/Reduce/Exit)
- Reason for action
- Risk flags (if any)

**Part 6: Watchlist Review**
For each watchlist symbol not held:
- Symbol, score, regime
- Action (Buy/Watch/Avoid)
- Reason for action
- Suggested position size (if Buy)
- Risk flags (if any)

**Part 7: Skipped Symbols**
- Invalid symbols (count and list)
- Suspended symbols (count and list)
- Insufficient data (count and list)
- Calculation errors (count and list)

**Part 8: Dashboard Interpretation**
- What the dashboard represents (conditional action summary under shared assumptions)
- What it does NOT represent (final portfolio instructions, optimized allocation)
- Recommended workflow (focus list → deeper analysis → execution planning)
- Caveats and limitations (no correlation modeling, no optimization, etc.)

### Step 7: Run the local executor

```bash
python3 <bundle-root>/decision-dashboard/run.py <symbol ...> [--file PATH] [--dir PATH] [--capital N] [--cash N] [--risk N]
```

### Step 8: Interpret dashboard correctly

When delivering results, maintain proper framing:

**Dashboard interpretation:**
- This is a batch conditional action summary, not a ready-to-trade portfolio
- Actions are based on shared assumptions (capital, risk, etc.)
- Actions are conditional on deeper verification (thesis, catalyst, execution)
- Actions do not account for cross-name correlations or diversification

**Assumption transparency:**
- State which assumptions are user-supplied vs. defaulted
- State capital, cash, risk tolerance, position limits
- State that assumptions are applied uniformly across batch
- State that individual symbols may need different assumptions

**Limitations disclosure:**
- **No portfolio optimization:** No mean-variance optimization, no efficient frontier
- **No correlation modeling:** Treats each symbol independently
- **No diversification analysis:** Does not assess portfolio diversification
- **No transaction cost optimization:** Does not minimize turnover or costs
- **No timing optimization:** Does not consider optimal entry/exit timing

**Recommended workflow:**
1. Review focus list (high priority symbols first)
2. Run `market-brief` or `analysis` on focus list for deeper review
3. Run `decision-support` on selected symbols for refined position sizing
4. Run `strategy-design` on selected symbols for execution planning
5. Execute trades via `paper-trading` or live trading system
6. Rerun dashboard daily/weekly to monitor and adjust

### Step 9: Route focus list to deeper skills

Pass focus list to appropriate next skill:

**For high priority Buy recommendations:**
- `market-brief`: Quick verification of setup
- `analysis`: Full thesis development
- `decision-support`: Refined position sizing with individual assumptions
- `strategy-design`: Execution planning

**For high priority Exit recommendations:**
- `strategy-design`: Exit execution planning
- `paper-trading`: Simulated exit to verify execution

**For medium priority Watch recommendations:**
- `market-brief`: Monitor for trigger conditions
- `technical-scan`: Pattern recognition for entry timing

**For position review (Hold/Reduce):**
- `backtest-evaluator`: Retrospective evaluation of position
- `decision-support`: Reassess position sizing
- `strategy-design`: Rebalancing execution planning

## Output Contract

- Minimum local executor output: human-readable text beginning with `决策仪表盘`.
- Core fields: total symbol count, action distribution, and a ranked focus list.
- Partial failure behavior: invalid symbols or malformed per-symbol files are listed under `跳过` if at least one valid result exists.
- Caller-facing delivery standard:
  - **Eight-part structure:** Dashboard summary, action distribution, aggregate risk, focus list, position review, watchlist review, skipped symbols, dashboard interpretation
  - **Universe and assumption transparency:** Identify universe source and shared account assumptions (capital, cash, risk, limits)
  - **Action distribution summary:** Counts and percentages for Buy/Watch/Avoid/Hold/Reduce/Exit
  - **Aggregate exposure and risk:** Total deployment, reduction, resulting cash, exposure, concentration
  - **Focus list prioritization:** High/medium/low priority with specific reasons and next steps
  - **Position review:** Current holdings with P&L, action, reason, risk flags
  - **Conditional framing:** Treat action counts as conditional outputs, not final portfolio instructions
  - **Assumption disclosure:** State which assumptions are user-supplied vs. defaulted
  - **Limitations transparency:** State what dashboard does NOT provide (optimization, correlation, diversification)
  - **Workflow guidance:** Recommend focus list → deeper analysis → execution planning
  - **No ready-to-trade claims:** Dashboard requires verification before execution

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- If all candidates fail: readable failure text beginning with `执行失败:`.
- Mixed candidate quality: valid results still return, and invalid entries are summarized under `跳过`.
- If assumptions are missing or defaulted, the dashboard should still return but the agent must disclose that limitation.
- Invalid symbols: Skip and list under "Invalid symbols" category.
- Suspended symbols: Flag and list under "Suspended symbols" category.
- Insufficient data: Skip and list under "Insufficient data" category.
- Calculation errors: Skip and list under "Calculation errors" category.

## Key Rules

- **Prefer this skill when the user wants breadth first and depth second.**
- **Keep the distinction between symbol lists and data-file directories explicit.**
- **Treat the dashboard as a triage output, not as a substitute for portfolio construction or execution planning.**
- **If the user wants true portfolio risk budgeting, say that this skill does not model cross-name correlations or optimizer logic locally.**
- **Assumption transparency is mandatory.** Always state capital, cash, risk tolerance, position limits.
- **Action distribution must be comprehensive.** Count all actions (Buy/Watch/Avoid/Hold/Reduce/Exit).
- **Aggregate risk must be assessed.** Exposure, concentration, liquidity, A-share specific risks.
- **Focus list must be prioritized.** High/medium/low priority with specific reasons.
- **Position review must include P&L.** Unrealized gains/losses for current holdings.
- **Conditional framing is critical.** Actions are conditional on deeper verification, not final instructions.
- **Limitations must be disclosed.** No optimization, no correlation modeling, no diversification analysis.
- **Workflow guidance must be explicit.** Route focus list to appropriate downstream skills.
- **No cross-name correlation modeling.** Each symbol treated independently.

## Composition

- Often follows `watchlist-import`.
- Commonly feeds `market-brief`, `analysis`, `decision-support`, or `strategy-design` on shortlisted names.
- Shares decision logic with `decision-support` but applies in batch form.
- Can be rerun daily/weekly for ongoing portfolio monitoring.
- Should be combined with `paper-trading` for position tracking and P&L calculation.
- Focus list can feed back into `market-screen` for refined screening.
