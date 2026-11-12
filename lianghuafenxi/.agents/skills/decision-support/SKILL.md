---
name: decision-support
description: "Produce action guidance with sizing and risk framing. Use when user wants a conditional buy, hold, reduce, avoid, or watch decision tied to explicit account assumptions."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Decision Support

Generate position-aware action guidance for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/decision-support/run.py`
- Primary purpose: convert current market state plus account constraints into an explicit action and sizing frame with systematic risk disclosure
- Research layer: decision support, not execution planning or portfolio instruction
- Workflow stage: stage 6 `Risk Management & Position Sizing`
- Local executor guarantee: produce a baseline action, quantity, stop, take-profit, and risk-budget frame from the current snapshot and account inputs

## Use When

- The user asks whether to buy, watch, hold, reduce, or avoid.
- The user wants quantity sizing under capital and risk constraints.
- The user wants stop-loss and take-profit anchors without the full narrative brief.
- The user needs a conditional decision frame that can be evaluated against explicit account assumptions.

## Do Not Use When

- The user only wants market interpretation. Use `market-analyze`.
- The user wants a full report with data, analysis, and strategy sections. Use `market-brief`.
- The user wants execution style and zone design rather than action sizing. Use `strategy-design`.
- The user wants a deeper thesis memo or explicit variant view discussion. Use `analysis`.
- The user wants executable trading instructions. This skill produces conditional guidance, not orders.

## Inputs

- Normal case: one stock symbol.
- Optional `--csv PATH`: use a local CSV instead of the default market source.
- Optional `--capital`, `--cash`, `--position`, `--risk`, `--max-position`: control sizing and risk limits.
- Optional `--start`, `--end`, `--source`: constrain the data-loading path.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Important assumption boundary: if account inputs are omitted, the local defaults still produce an answer. The caller must mark that answer as conditional on defaults rather than as portfolio-specific advice.

## Execution

### Step 1: Confirm the portfolio context

Use `decision-support` when the user wants a decision on whether and how much to own. If the user mainly wants how to express an already accepted view in the tape, route to `strategy-design`.

### Step 2: Run the local executor

```bash
python3 <bundle-root>/decision-support/run.py <symbol> [--cash N] [--position N] [--capital N] [--risk N]
```

### Step 3: Deliver the result as three-part conditional guidance

Every decision-support output must be structured in three mandatory parts:

**Part 1: Conditional Action Frame**
- Action: buy, watch, hold, reduce, or avoid
- Heuristic conviction score (labeled explicitly as non-probabilistic)
- Target position size
- Quantity (may be zero if action is watch/avoid or if constraints bind)
- Reference price
- Stop loss level
- Take profit level
- Risk budget allocation
- Reasoning bullets (3-5 specific factors)

**Part 2: Explicit Assumptions**
State which inputs were user-supplied vs. defaulted:
- Capital: [user-supplied: X / defaulted: Y]
- Cash available: [user-supplied: X / defaulted: Y]
- Current position: [user-supplied: X / defaulted: Y]
- Risk tolerance: [user-supplied: X / defaulted: Y]
- Max position limit: [user-supplied: X / defaulted: Y]
- Data window: [start date] to [end date]
- Symbol source: [explicit / session reuse]

**Part 3: Non-Modeled Risks**
Systematically disclose material execution and market risks not captured in the decision frame:
- **Liquidity risk:** if average daily volume suggests position size may impact market, state that explicitly
- **Gap risk:** opening gaps can bypass stop levels; state whether symbol has history of gap behavior
- **Limit behavior:** A-share price limits (typically ±10% or ±20%) can prevent stop execution; acknowledge this constraint
- **Stop slippage:** actual stop fills may differ from reference levels, especially in volatile conditions
- **Benchmark/style mismatch:** if the decision frame does not consider benchmark tracking or style constraints, state that explicitly
- **Catalyst uncertainty:** if the action depends on an expected catalyst, acknowledge timing and outcome uncertainty
- **Regime sensitivity:** if the decision is regime-dependent, state what regime change would invalidate the frame

### Step 4: Frame as conditional guidance, never as instruction

The output must be presented as:
- "Conditional decision frame based on [stated assumptions]"
- "This is advisory guidance requiring human judgment, not an executable order"
- "Actual position sizing should incorporate portfolio-level constraints not modeled here"

## Output Contract

- Minimum local executor output: human-readable text beginning with `决策支持`.
- Fields: action, confidence, target position, quantity, reference price, stop loss, take profit, risk budget, and reasoning bullets.
- Side effects: updates session memory for the current execution context.
- Caller-facing delivery standard:
  - **Three-part structure mandatory:** every delivery must include (1) conditional action frame, (2) explicit assumptions, (3) non-modeled risks
  - **Assumption transparency:** distinguish user-provided capital, cash, position, risk, and max-position inputs from local defaults
  - **Confidence labeling:** treat `confidence` as "heuristic conviction score" and label it explicitly as such in every delivery; never present as calibrated probability or expected hit rate
  - **Conditional framing:** label the output as conditional on the current snapshot and stated account assumptions
  - **Risk disclosure:** surface non-modeled risks systematically, not optionally
  - **Zero-quantity handling:** if quantity is zero because the action is `watch`, `hold`, or `avoid`, or because a constraint binds, state the binding constraint explicitly
  - **No order language:** never use language that implies executable instructions, automated trading, or portfolio mandates

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Data-loading or normalization errors: readable failure text beginning with `执行失败:`.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- If material account context is missing, continue with conditional guidance rather than pretending exact portfolio fit.
- If risk disclosure cannot be completed due to missing data (e.g., volume history unavailable), state that gap explicitly.

## Key Rules

- **Respect lot-size and max-position constraints** and state when they bind.
- **Treat the output as a decision frame, not as an automated execution order.**
- **Keep the question of whether to own the name separate from the question of how to execute it.**
- **Route to `strategy-design`** when the user wants execution mechanics after the decision is accepted.
- **Systematic risk disclosure is mandatory, not optional.** Every delivery must include Part 3 (Non-Modeled Risks).
- **Default assumptions must be surfaced explicitly.** Never let defaulted inputs masquerade as user-approved constraints.
- **Confidence scores are heuristic conviction, never probabilities.** This must be stated in every delivery.

## Composition

- Builds on the same upstream data and snapshot logic as `market-data` and `market-analyze`.
- Often pairs with `strategy-design` or appears inside `market-brief` and `analysis`.
- Should feed into `backtest-evaluator` when retrospective evaluation is needed.
