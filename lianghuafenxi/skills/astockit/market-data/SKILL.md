---
name: market-data
description: "Normalize and summarize one A-share dataset. Use when user wants the stage-2 and stage-3 data pipeline for one symbol: source selection, schema normalization, feature-base preparation, export, and data-quality review without interpretation."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Market Data

Normalize and summarize market data for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/market-data/run.py`
- Primary purpose: expose the canonical one-symbol market-data pipeline without adding decision, thesis, or execution claims
- Workflow stages: stage 2 `Data Collection & Quality Assurance` plus stage 3 `Data Cleaning & Normalization`, with stage-4 feature-base preparation
- Local executor guarantee: schema normalization, required-column validation, date sorting, duplicate-date collapse, numeric coercion, indicator enrichment, and optional export

## Use When

- The user wants to inspect whether a symbol’s raw price data is usable for research or backtesting.
- The user wants an enriched export that downstream skills or external workflows can reuse.
- The user wants to verify date coverage, source, row count, and the basic feature base before analysis.
- The caller needs a disciplined preprocessing step before `market-analyze`, `stock-data`, `market-screen`, or `backtest-evaluator`.

## Do Not Use When

- The user wants scored market interpretation. Use `market-analyze`.
- The user wants a reusable multi-block research snapshot. Use `stock-data`.
- The user wants action guidance or execution planning. Use `decision-support` or `strategy-design`.
- The user wants provider refresh orchestration or stale-record diagnosis across the broader runtime. Use `data-sync`.

## Inputs

- Normal case: one stock symbol.
- Optional `--csv PATH`: load from a local CSV or JSON file rather than the default data provider.
- Optional `--export PATH`: write the enriched dataset to a target path.
- Optional `--start`, `--end`, `--source`: constrain the data-loading path.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Local file contract:
  - minimum normalized columns required after alias resolution: `date`, `open`, `high`, `low`, `close`, `volume`
  - optional supported columns include `amount`, `pct_change`, `turnover`, and `name`
  - the agent should state whether the file is externally supplied, bundle-generated, or host-generated
- Adjustment note:
  - the runtime uses the configured adjustment mode when pulling provider data
  - the agent should say whether the dataset is provider-fetched or external-file-backed when the adjustment basis matters

## Execution

### Step 1: Define the acquisition scope

Before running the local executor, identify:

- the symbol or explicit local file being normalized
- the intended date window
- the expected downstream use: inspection, export, research snapshot, screening, or backtest preparation
- whether point-in-time correctness matters for the next stage

### Step 2: Run the local executor

```bash
python3 <bundle-root>/market-data/run.py <symbol> [--csv PATH] [--export PATH]
```

### Step 3: Review the normalized dataset as a research input, not just a table

The agent should check and report:

- source provenance: `akshare` or local file
- date coverage and row count
- duplicate-date handling and obvious missing-window issues
- whether required columns were present directly or inferred through alias normalization
- whether turnover or amount are absent, because that weakens later liquidity commentary
- whether the requested date window is too short for downstream indicators or backtests

### Step 4: Confirm the feature base and known limits

The local enrichment path adds moving averages, MACD, RSI, Bollinger bands, ATR, volume ratio, support, resistance, drawdown, and breakout proximity. The agent should state:

- that these are convenience features for downstream skills, not validated alpha factors by themselves
- that the pipeline is daily-bar oriented rather than intraday
- that local normalization does not by itself solve point-in-time corporate-action, suspension, or survivorship questions for backtesting

## Output Contract

- Minimum local executor output: human-readable text beginning with `数据处理`.
- Core fields: symbol, source, date range, row count, last close, last volume, turnover, optional export path.
- Local executor side effects:
  - updates session history for the current execution context
  - writes an enriched dataset only when `--export` is present
- Caller-facing delivery standard:
  - explicitly label the dataset source and whether the symbol or file was reused from session context
  - say whether the dataset is being used for inspection, export, screening, or backtest preparation
  - if a local file was supplied, treat its provenance and adjustment basis as user-supplied assumptions
  - identify any material quality issues that affect downstream use, especially short history, missing turnover, suspicious gaps, unsupported columns, stale files, or external-file ambiguity
- Non-guarantees:
  - no persisted run directory is created by this skill
  - no claim is made about strategy validity, signal strength, or execution readiness

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Unsupported or malformed market data: readable failure text beginning with `执行失败:`.
- Missing required columns in a local file: readable failure text rather than a traceback.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- If the dataset is technically readable but analytically weak, the skill should still return with explicit quality warnings rather than pretending the input is backtest-ready.

## Key Rules

- Use this skill for data inspection and preprocessing, not recommendation.
- Distinguish local executor guarantees from broader research hygiene that the agent must still review.
- Do not treat enriched indicators as a substitute for point-in-time feature engineering discipline.
- For backtests or retrospective evaluation, explicitly state whether the dataset appears clean enough for the intended holding horizon and realism assumptions.

## Composition

- This skill is the data foundation for `market-analyze`, `stock-data`, `market-screen`, `decision-dashboard`, `decision-support`, `strategy-design`, and `backtest-evaluator`.
- `data-sync` is the upstream orchestration surface when freshness or provider health is the real task.
