---
name: market-analyze
description: "Assess trend, regime, and risk state for one A-share symbol. Use when user wants current market interpretation from the normalized snapshot without action sizing, execution planning, or thesis narration."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Market Analyze

Assess scored market state for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/market-analyze/run.py`
- Primary purpose: turn normalized market data into a readable current-state interpretation
- Research layer: descriptive analysis only
- Workflow stage: stage 4 `Signal and State Interpretation`
- Local executor guarantee: compute and return the current market snapshot summary, including score, bias, trend, regime, key levels, notes, and risk flags

## Use When

- The user wants current trend, regime, support, resistance, and risk-state interpretation.
- The user wants descriptive market-state context before moving into `decision-support`, `strategy-design`, or `technical-scan`.
- The user needs a bounded summary of the current snapshot rather than a thesis memo or full report.

## Do Not Use When

- The user wants a full report with decision and strategy sections. Use `market-brief`.
- The user wants a direct trading action or quantity. Use `decision-support`.
- The user wants technical-only pattern language or broader chart commentary beyond the runtime snapshot summary. Use `technical-scan`.
- The user wants raw normalized data only. Use `market-data`.
- The user wants broader catalyst, thesis, or variant-view analysis. Use `analysis`.

## Inputs

- Normal case: one stock symbol.
- Optional `--csv PATH`: use a local CSV instead of the default market source.
- Optional `--start`, `--end`, `--source`: constrain the data-loading path.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Data note:
  - the local runtime derives its state from the normalized daily-bar frame
  - the user should not assume an intraday, benchmark-relative, or multi-factor attribution engine exists here

## Execution

### Step 1: Confirm the descriptive boundary

Use `market-analyze` for current-state interpretation only. It describes what the normalized snapshot currently looks like; it does not approve a position, design an execution plan, or validate a thesis.

### Step 2: Run the local executor

```bash
python3 <bundle-root>/market-analyze/run.py <symbol> [--csv PATH]
```

### Step 3: Deliver the snapshot honestly

The local output should be interpreted as a bounded state summary built from the enriched market frame. The agent should state:

- the data source and date window
- whether the symbol was explicit or reused from session context
- that `score` and `bias` summarize current state heuristically
- that the skill does not imply portfolio action, catalyst interpretation, or execution readiness

## Output Contract

- Minimum local executor output: human-readable text beginning with `市场分析`.
- Core fields: symbol, board, score, bias, trend, regime, support, resistance, notes, and risk flags.
- Side effects: updates session memory for the current execution context.
- Caller-facing delivery standard:
  - identify the data source and date window
  - treat score and bias as descriptive state summaries, not expected-return claims
  - keep the answer interpretive and current-state oriented
  - say explicitly when the result does not incorporate fundamentals, catalysts, portfolio constraints, or execution assumptions

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Data-loading or normalization errors: readable failure text beginning with `执行失败:`.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- If the available data window is too thin for robust interpretation, say so directly rather than pretending high confidence.

## Key Rules

- Keep this skill interpretive rather than prescriptive.
- Use it as the clean descriptive anchor for `technical-scan`, `decision-support`, and `strategy-design`.
- Do not let a scored snapshot summary masquerade as a trading instruction.
- Do not imply indicators or controls that the current runtime does not actually expose in this skill’s local output.

## Composition

- Usually follows `market-data` or shares the same upstream loaders.
- Often feeds `technical-scan`, `decision-support`, `strategy-design`, and `market-brief`.
