---
name: backtest-evaluator
description: "Evaluate a saved analysis run against later market data. Use when user wants retrospective review grounded in a saved state or a deterministic strategy simulation with explicit assumptions."
argument-hint: [symbol-or-state]
allowed-tools: Bash(python3 *), Read, Glob
---

# Backtest Evaluator

Evaluate a saved analysis run for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/backtest-evaluator/run.py`
- Primary purpose: compare a saved run's action and price framing with later market behavior, or run a deterministic strategy simulation over local data, with explicit evaluation assumptions and realism limits
- Research layer: retrospective evaluation for process improvement, not forward-looking approval or predictive proof
- Workflow stage: stage 5 `Backtesting & Retrospective Evaluation`
- Local executor guarantee: evaluate a saved state against later price data or run the configured deterministic strategy simulation and persist backtest artifacts

## Use When

- The user wants retrospective signal review tied to a saved `analysis` or `market-brief` artifact.
- The caller has a saved `state.json` and wants to see how that view behaved over the next holding window.
- The user wants a deterministic strategy simulation over local CSV or fetched data with saved backtest artifacts.
- The user wants to improve research process discipline through systematic review of prior decisions.

## Do Not Use When

- There is no prior saved run or no later price window to evaluate.
- The user wants forward-looking analysis rather than retrospective evaluation.
- The user wants proof of predictive edge. This skill provides process scorecards, not validation of forecasting skill.
- The user wants to claim that a "validated" outcome proves the original thesis was correct. Retrospective alignment does not prove causation or skill.

## Inputs

- One symbol, or omit `symbol` when `--state PATH` already identifies the run.
- Optional `--state PATH`: explicit saved state file.
- Optional `--from-command`: default lookup command when resolving the latest saved run.
- Optional `--holding-days N`.
- Optional `--strategy STRATEGY_ID` (repeatable): run one or more full strategy backtests instead of single-run evaluation.
- Optional `--initial-cash`, `--slippage-bps`, `--max-position-pct`.
- Optional market inputs: `--csv`, `--start`, `--end`, `--source`.
- Important reproducibility boundary: prefer explicit `--state` when the evaluation must be repeatable. Otherwise the skill may resolve the latest matching saved run.

## Execution

### Step 1: Resolve the evaluation mode and artifact

Decide whether the request is for saved-run evaluation mode or strategy-simulation mode. In saved-run mode, resolve `state.json` from `--state` or the latest matching run. In strategy mode, resolve the market frame plus one or more strategy ids.

### Step 2: Run the local evaluator or simulator

```bash
python3 <bundle-root>/backtest-evaluator/run.py <symbol> [--state PATH] [--holding-days N]
python3 <bundle-root>/backtest-evaluator/run.py <symbol> --strategy bull_trend --csv ./data.csv
```

### Step 3: Structure the evaluation with mandatory discipline

Every retrospective evaluation must include these elements:

**Outcome Summary (mandatory):**
- Action from saved state
- Holding window used
- Entry and exit prices (actual or modeled)
- Price change percentage
- Maximum favorable excursion (best case during window)
- Maximum adverse excursion (worst case during window)
- Stop and take-profit flags (whether levels were touched)
- Outcome classification (see below)

**Outcome Classification (mandatory, use honest language):**
Replace verdict labels like "validated" or "invalidated" with more accurate language:
- **"Outcome aligned with thesis"**: price moved in the expected direction and magnitude
- **"Outcome diverged from thesis"**: price moved contrary to expectations
- **"Outcome mixed"**: some thesis elements confirmed, others disconfirmed
- **"Outcome inconclusive"**: insufficient price movement or time to evaluate

Never use language that implies proof, validation, or predictive skill confirmation.

**What Was Not Knowable Then (mandatory):**
Explicitly state information that is now visible but was not available at the time of the original decision:
- Subsequent news or events that affected price
- Regime changes that occurred after the decision
- Information that would have changed the original thesis if known
- Alternative scenarios that were plausible but did not occur

This section guards against hindsight bias by acknowledging that the evaluation has perfect information about what actually happened, but the original decision did not.

**Evaluation Assumptions (mandatory):**
State the mechanical assumptions used in the evaluation:
- **Entry mechanics:** "Entry assumed at saved `entry_ref` price [X], or last close [Y] if `entry_ref` unavailable"
- **Exit mechanics:** "Exit assumed at window close price [Z] on day [N]"
- **Stop handling:** "Stop flag set if intraday low touched stop level; actual fill price not modeled"
- **Take-profit handling:** "Take-profit flag set if intraday high touched target level; actual fill price not modeled"
- **Holding window:** "Evaluation window: [N] days from entry, ending [date]"

**Realism Limits (mandatory):**
Systematically disclose what is not modeled in the evaluation:

For saved-run evaluation mode:
- **No liquidity modeling:** evaluation assumes fills at reference prices regardless of position size or market depth
- **No auction behavior:** opening and closing auction dynamics not modeled
- **No gap handling:** stop losses assumed executable at exact levels; gap risk not modeled
- **No limit behavior:** A-share price limits (±10% or ±20%) not modeled; stops may be unexecutable in limit scenarios
- **No slippage beyond configured assumptions:** actual execution costs may differ
- **No benchmark comparison:** evaluation does not assess performance relative to benchmark or opportunity cost
- **No regime normalization:** evaluation does not adjust for whether market regime remained stable during window
- **No partial fills or scaling:** evaluation assumes single entry and exit, not realistic position building

For strategy-simulation mode:
- State which frictions are modeled (e.g., configured slippage) and which are not
- Acknowledge that deterministic simulation cannot capture regime changes, liquidity shocks, or behavioral factors
- State that simulation results are conditional on the specific data window and strategy parameters used

**Process Insights (mandatory):**
State what the evaluation reveals about research process, not about predictive skill:
- Did the original thesis identify the right drivers, even if timing was off?
- Were invalidation conditions appropriate and monitorable?
- Did the risk framing capture the actual risks that materialized?
- What would improve the next similar analysis?

### Step 4: Preserve artifact provenance

Reference the evaluated saved state path, generation time, and generating command. In strategy mode, reference the backtest artifact directory.

## Output Contract

- Saved-run mode returns human-readable text beginning with `# <symbol> Backtest Evaluation`.
- Saved-run fields: action, holding window, entry and exit, change percentage, max upside, max drawdown, stop and take flags, outcome classification, and evaluated state path.
- Strategy mode returns a strategy summary table and writes `config.json`, `state.json`, `metrics.json`, `report.md`, `trades.csv`, `equity_curve.csv`, and `metadata.json` under the backtest artifact tree.
- Caller-facing delivery standard:
  - **Honest outcome language:** use "outcome aligned/diverged/mixed/inconclusive" rather than "validated/invalidated"
  - **Mandatory hindsight guard:** every evaluation must include "What Was Not Knowable Then" section
  - **Explicit evaluation assumptions:** state entry/exit mechanics, stop handling, and holding window assumptions
  - **Systematic realism limits:** disclose all non-modeled factors (liquidity, gaps, limits, benchmark, regime)
  - **Process focus:** frame insights as process improvements, not as proof of predictive edge
  - **Artifact provenance:** reference the evaluated state path, generation time, and command
  - **No proof claims:** never present retrospective alignment as validation of forecasting skill or as evidence that the original thesis was "correct"

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Missing saved state: readable `执行失败:` text explaining that no evaluable state file was found.
- Market-data failures in the future window: readable `执行失败:` text.
- If the resolved latest run is ambiguous or unsuitable for the requested review, prefer an explicit `--state` path.
- If "What Was Not Knowable Then" section cannot be completed due to missing context, state that limitation explicitly.

## Key Rules

- **This skill evaluates prior output; it does not generate new analysis.**
- **Use it to improve process discipline, not to claim predictive proof.**
- **Outcome alignment does not prove the original thesis was correct.** Many theses can produce the same price outcome for different reasons.
- **Hindsight bias is the primary risk.** The "What Was Not Knowable Then" section is mandatory to guard against it.
- **Realism limits must be disclosed systematically, not optionally.** Users must understand what the evaluation does and does not model.
- **In strategy mode, treat it as a simulation engine rather than a single-run scorecard.**
- **Pair it with `analysis-history` or `reports`** when the user needs the evaluated artifact lineage.
- **Never use "validated" or "invalidated" language.** These terms imply stronger conclusions than retrospective evaluation can support.

## Composition

- Usually consumes artifacts created by `analysis` or `market-brief`.
- Pairs naturally with `analysis-history` and `reports`.
- Should feed back into research process improvement, not into claims of predictive skill.
