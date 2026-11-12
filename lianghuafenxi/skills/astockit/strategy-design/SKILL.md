---
name: strategy-design
description: "Design an execution plan for one A-share symbol. Use when user wants the execution-planning stage of the workflow: strategy family selection, entry and exit structure, hold horizon, monitoring rules, and execution-realism notes after the investment view is already accepted."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Strategy Design

Design an execution plan for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/strategy-design/run.py`
- Primary purpose: turn an accepted market view into a conditional execution style, actionable zones, and a monitoring checklist
- Workflow stages: stage 4 `Feature Engineering & Signal Construction`, stage 6 `Risk Management & Position Sizing`, and stage 7 `Live Trading & Monitoring`
- Local executor guarantee: produce a baseline strategy plan from the current snapshot and optional strategy preset
- Agent-required overlay: verify that the plan is appropriate for liquidity, price-limit behavior, cost assumptions, holding horizon, and monitoring discipline

## Use When

- The user wants execution style rather than only a trade action.
- The user asks for entry, stop, target, and holding-horizon structure.
- The user wants a practical execution and monitoring checklist around the current market state.

## Do Not Use When

- The user only wants a trading action and quantity. Use `decision-support`.
- The user wants a full report bundle. Use `market-brief` or `analysis`.
- The user wants to know whether the name belongs in the portfolio at all. Use `decision-support` or `analysis` first.
- The user expects a live-execution algorithm or broker integration. This skill does not provide that.

## Inputs

- Normal case: one stock symbol.
- Optional `--csv PATH`: use a local CSV instead of the default market source.
- Optional `--strategy STRATEGY_ID`: force a migrated strategy preset.
- Optional `--style auto|breakout|trend_pullback|range_trade|defensive`.
- Optional `--hold-days N`, `--capital N`, `--risk N`.
- Optional `--start`, `--end`, `--source`.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Assumption note:
  - style, hold-days, capital, and risk defaults materially affect the plan
  - the agent should say which were explicit and which were defaulted

## Execution

### Step 1: Confirm the planning boundary

Use `strategy-design` only after the investment judgment is accepted or at least conditionally accepted. If the user is still asking whether to own the name, route back to `decision-support` or `analysis`.

### Step 2: Run the local executor

```bash
python3 <bundle-root>/strategy-design/run.py <symbol> [--strategy STRATEGY_ID] [--style STYLE] [--hold-days N]
```

### Step 3: Validate execution realism around the baseline plan

The agent should explicitly review:

- regime and style fit
- price-limit risk for A-share execution
- gap and stop-slippage risk
- whether the expected position size appears too large relative to likely liquidity
- whether the holding period makes sense given signal decay and event risk
- whether the plan depends on a deterministic preset or an advisory-style framework

### Step 4: Deliver a complete execution plan

When the user needs more than the raw local output, the skill should structure the answer into:

- strategy family and rationale
- entry conditions and entry zone
- stop logic and invalidation triggers
- target or profit-taking logic
- holding horizon and review cadence
- execution-realism notes and known non-modeled risks

### Step 5: Define monitoring and handoff rules

The plan should identify what to watch next and which downstream skill should handle the next stage:

- `paper-trading` for simulated execution
- `backtest-evaluator` for historical validation of similar rules
- `analysis-history` or `reports` for prior comparable runs

## Output Contract

- Minimum local executor output: human-readable text beginning with `策略设计`.
- Core fields: strategy id or display name when applicable, holding days, entry zone, stop zone, take-profit zone, position percentage, checklist items, and risk notes.
- Side effects: updates session memory for the current execution context.
- Local executor guarantee:
  - baseline plan generation from the current snapshot and preset logic
  - conditional style selection when `auto` is used
- Agent-required delivery standard:
  - disclose style, preset, hold-period, capital, and risk assumptions
  - state whether the plan comes from deterministic preset logic or higher-level manual framing
  - treat zones as planning anchors rather than guaranteed fills
  - surface non-modeled risks when relevant, especially opening gaps, limit-up or limit-down behavior, liquidity, stop slippage, and event timing
  - keep execution mechanics separate from the question of whether the position should exist at all

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Data-loading or normalization errors: readable failure text beginning with `执行失败:`.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- If execution realism cannot be assessed from the available evidence, the plan should still return with explicit caveats rather than false precision.

## Key Rules

- Treat the result as a conditional execution plan, not as an automatic order.
- Keep the style aligned with the observed market regime unless the user explicitly overrides it.
- Avoid false precision: the plan should acknowledge level slippage, price-limit behavior, and tape risk when they matter.
- If the user wants portfolio approval, route back to `decision-support` or `analysis`.

## Composition

- Often follows `market-analyze`, `decision-support`, or `analysis`.
- Frequently appears as the planning section inside `market-brief`.
- Natural upstream companion to `paper-trading`.
