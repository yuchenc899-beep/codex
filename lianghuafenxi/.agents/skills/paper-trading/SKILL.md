---
name: paper-trading
description: "Run a paper-trading workflow over analyzed symbols. Use when user wants the live-verification stage in simulated form: trade rehearsal, ledger updates, A-share settlement rules, and explicit monitoring of what the local paper book does and does not model."
argument-hint: [symbol-or-order]
allowed-tools: Bash(python3 *), Read, Glob
---

# Paper Trading

Run a simulated trading workflow for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/paper-trading/run.py`
- Primary purpose: maintain a local paper book with order simulation, cost basis tracking, cash updates, and basic A-share settlement constraints
- Workflow stage: stage 7 `Live Trading & Monitoring` in simulated mode
- Local executor guarantee:
  - account inspection when `--side` is omitted
  - JSON-backed paper-book updates when `--side` is provided
  - lot-size normalization, commission and stamp-duty handling, cost-basis updates, and T+1 sell-availability checks
- Non-guarantees:
  - no live trading or brokerage integration
  - no automatic slippage, market-impact, concentration, or alert engine beyond what the local ledger actually stores

## Use When

- The user wants to validate a trade idea with simulated execution before live trading.
- The user wants to track paper positions with a persistent local ledger.
- The user wants to review cash, positions, and trade history in a simulated account.
- The caller wants a controlled rehearsal surface between analysis and real capital.

## Do Not Use When

- The user expects live trading or broker connectivity.
- The user has not yet decided on side, quantity, or thesis and instead needs analysis first.
- The user wants full historical strategy testing. Use `backtest-evaluator`.
- The user wants advanced portfolio analytics that the local paper ledger does not compute automatically.

## Inputs

- One symbol for order mode.
- Optional `--side buy|sell`; if omitted, the skill returns account status instead of placing an order.
- Optional `--quantity`, `--price`, `--account`, `--initial-cash`, `--trade-date`, `--note`.
- Optional market inputs: `--csv`, `--start`, `--end`, `--source` for resolving a default price context.
- Operational note:
  - if `--price` is omitted, the runtime falls back to a current market price context rather than running an execution algorithm
  - the agent should say whether the execution price is user-specified or runtime-defaulted

## Execution

### Step 1: Decide the mode

- Account status mode: no `--side`; inspect the current paper book only.
- Trade execution mode: `--side` is present; attempt a simulated buy or sell and update the paper book.

### Step 2: Perform pre-trade checks around the local ledger

Before executing a simulated trade, the agent should review:

- whether the symbol and thesis source are clear
- whether quantity is lot-compatible for the market
- whether there is enough cash for a buy
- whether enough T+1-available shares exist for a sell
- whether the user is asking for a realistic execution rehearsal or only a bookkeeping update

These checks are partly enforced locally and partly should be stated by the agent when the user expects professional workflow discipline.

### Step 3: Run the local executor

```bash
python3 <bundle-root>/paper-trading/run.py <symbol> --side buy --quantity 100 [--price 18.2]
```

### Step 4: Interpret the result with realism disclosures

The local paper ledger handles cash, cost basis, lots, commission, stamp duty, and T+1 sell constraints. If the user expects richer execution realism, the agent should additionally state:

- whether slippage was explicitly modeled or not
- whether price-limit, suspension, or liquidity risk was checked outside the ledger
- whether concentration or portfolio risk checks were performed manually or remain unmodeled

### Step 5: Link the paper trade back to the research loop

After execution or account review, the agent should identify:

- which thesis or plan the position belongs to
- what invalidation or monitoring conditions should be checked next
- whether `session-status`, `reports`, `analysis-history`, or `backtest-evaluator` should be used for follow-up

## Output Contract

- Account mode: readable text beginning with `# Paper Account <account>`.
- Trade mode: readable text beginning with `# Paper Trade <trade_id>`, followed by account state after the trade.
- Side effects: writes a JSON paper ledger under the runtime area and appends paper-trade history.
- Local executor guarantee:
  - ledger persistence
  - cost-basis and lot tracking
  - commission and stamp-duty modeling
  - T+1 sell-availability enforcement
- Agent-required delivery standard:
  - always state `This is simulated trading only; no real capital is at risk.`
  - identify whether the price was user-specified or runtime-defaulted
  - identify what realism layers were not modeled locally, especially slippage, market impact, ADV capacity, price-limit fillability, suspension risk, and portfolio-level concentration
  - if presenting performance or risk interpretation beyond cash and positions, label the assumptions and calculation basis explicitly

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Invalid lot-normalized quantity: readable `执行失败:` text with the lot-size requirement.
- Insufficient cash: readable `执行失败:` text.
- Insufficient available shares for sell: readable `执行失败:` text with the available T+1-adjusted quantity.
- The skill never places live orders; all changes stay local to the paper ledger.

## Key Rules

- Treat every result as simulated only.
- Be honest about what the local ledger models versus what the agent is layering on top.
- Respect A-share constraints such as lot sizes, T+1 sell availability, and sell-side stamp duty.
- Use this skill to validate process discipline before real execution, not to mimic a broker.

## Composition

- Commonly follows `analysis`, `decision-support`, or `strategy-design`.
- Pairs with `session-status` for runtime context and with `reports` or `analysis-history` for artifact-linked review.
- Serves as the simulated live-verification layer before any real-capital workflow outside the bundle.
