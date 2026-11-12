---
name: market-brief
description: "Generate the default one-symbol A-share brief. Use when user wants a fast, single-pass synthesis combining current market state, conditional decision framing, and conditional execution planning in one persisted run."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob
---

# Market Brief

Generate the default one-symbol A-share brief for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/market-brief/run.py`
- Primary purpose: deliver the default first-pass one-symbol synthesis by combining current market state, conditional action framing, and conditional execution planning into one persisted run
- Research layer: composed skill spanning descriptive analysis, decision support, and execution planning
- Workflow stages: stage 4 `State Interpretation`, stage 6 `Decision Support`, and stage 7 `Execution Planning` in one fast bundled pass
- Design intent: speed and completeness over depth; single-pass synthesis without thesis pressure-testing
- Local executor guarantee: generate the persisted composed brief and artifact set from the current snapshot plus the shared decision and strategy helpers

## Use When

- The user wants the default one-symbol entry point.
- The user wants one bounded output covering current state, what the system would do, and how it would structure the trade.
- The user wants persisted artifacts that downstream skills can inspect or evaluate later.
- The user prioritizes speed over depth and does not need thesis pressure-testing, variant views, or invalidation logic.
- The user wants a complete picture quickly without asking follow-up questions.

## Do Not Use When

- The user only wants raw normalized data. Use `market-data`.
- The user only wants descriptive state reading without action or execution layers. Use `market-analyze`.
- **The user asks "why," "what drives this," "what are the risks," or "what would change your view."** Use `analysis`.
- **The user needs a research memo suitable for investment committee review or retrospective evaluation.** Use `analysis`.
- **The user wants thesis framing, catalyst analysis, variant views, disconfirming evidence, or invalidation conditions.** Use `analysis`.
- The user wants stored artifact retrieval or comparison rather than fresh computation. Use `reports` or `analysis-history`.
- The user wants batch ranking or watchlist triage. Use `market-screen` or `decision-dashboard`.

## Routing Boundary: market-brief vs. analysis

This is the most important routing decision in the bundle. Use this operational rule:

**Use `market-brief` when:**
- User wants current positioning quickly
- User accepts single-pass synthesis without pressure-testing
- User does not ask about drivers, risks, or what could go wrong
- Speed matters more than depth

**Use `analysis` when:**
- User asks "why," "what drives this," "what are the risks," "what would change your view"
- User needs a research memo for IC review or formal evaluation
- User wants saved artifacts for later retrospective evaluation with `backtest-evaluator`
- User explicitly requests depth, thesis framing, or risk pressure-testing
- The decision has material portfolio impact and requires documented thesis discipline

**When in doubt:** If the user's question implies they need to understand causation, risks, or invalidation conditions, route to `analysis`. If they just want to know current state and what to do about it, use `market-brief`.

## Inputs

- Normal case: one stock symbol.
- Optional `--csv PATH`: use a local CSV instead of the default market source.
- Optional `--start`, `--end`, `--source`: constrain the data-loading path.
- Optional `--capital`, `--cash`, `--position`, `--risk`, `--max-position`: shape the decision-support block.
- Optional `--style`, `--hold-days`: shape the execution-planning block.
- Optional `--notify`: attempt outbound Feishu delivery after report creation.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Important assumption boundary: if cash, position, risk, style, or hold-days are omitted, local defaults drive the decision and strategy sections. The caller should surface those defaults as assumptions rather than treating them as user-approved constraints.

## Execution

### Step 1: Confirm this is the right layer mix

Use `market-brief` only when the user actually wants descriptive analysis, decision support, and execution planning in one pass. If the user wants only one layer or wants deeper research pressure-testing, route accordingly.

**Critical routing check:** Does the user's question imply they need thesis-level rigor? If yes, route to `analysis` instead.

### Step 2: Run the local executor

```bash
python3 <bundle-root>/market-brief/run.py <symbol> [--csv PATH] [--capital N] [--position N] [--notify]
```

### Step 3: Deliver the result with labeled layers

Keep `数据处理`, `市场分析`, `决策支持`, and `策略设计` distinct in the caller-facing answer. Make clear that the last two are conditional heuristics, not executable orders.

**Layer separation requirements:**
- **Data layer:** state the data source, date window, and whether symbol was reused from session
- **Analysis layer:** present as descriptive current-state interpretation, not as thesis validation
- **Decision layer:** frame as conditional guidance with explicit assumptions (see `decision-support` contract for three-part structure)
- **Execution layer:** frame as conditional planning anchors, not as guaranteed fill levels

### Step 4: Acknowledge what market-brief does not provide

When delivering the output, explicitly state:
- "This is a single-pass synthesis without thesis pressure-testing"
- "For deeper analysis including variant views, disconfirming evidence, and invalidation conditions, use the analysis skill"
- If the user later asks "why" or "what are the risks," recommend escalating to `analysis`

### Step 5: Reuse the run artifacts downstream

If the next step is export, comparison, or retrospective evaluation, pass the generated run directory to `reports`, `analysis-history`, or `backtest-evaluator` instead of recomputing blindly.

## Output Contract

- Minimum local executor output: human-readable text beginning with `# <symbol> A 股简报` plus four labeled blocks: `数据处理`, `市场分析`, `决策支持`, and `策略设计`.
- Artifact side effects: writes one dated run directory with `state.json`, `report.md`, and `metadata.json`.
- Caller-facing delivery standard:
  - **Layer visibility:** keep descriptive analysis separate from action sizing and execution planning
  - **Data provenance:** identify the market-data source, date window, and whether the symbol was supplied explicitly or reused from session context
  - **Assumption transparency:** state any defaulted capital, cash, position, risk, style, or hold-period assumptions that materially shaped the answer
  - **Confidence framing:** treat `score` and `confidence` as heuristic decision aids, not forecast probabilities
  - **Risk disclosure:** surface non-modeled risks when relevant, especially catalyst gaps, liquidity constraints, opening gap risk, price-limit behavior, and stop slippage
  - **Conditional framing:** present action and plan blocks as advisory frames, not as executable orders
  - **Scope acknowledgment:** explicitly state that this is a single-pass synthesis without thesis pressure-testing
  - **Escalation path:** if the user asks follow-up questions about drivers, risks, or invalidation, recommend `analysis`
- Optional side effect: if `--notify` is used, the skill attempts Feishu notification without blocking the report.

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Runtime data errors: readable failure text beginning with `执行失败:`.
- Missing symbol with no reusable session symbol: readable guidance instead of a traceback.
- Notification delivery problems: fail open; the report still returns.
- If optional context is absent, do not imply the brief is fully informed on fundamentals, catalysts, or news.

## Key Rules

- **Prefer this skill as the default one-symbol entry point, but do not let default status turn it into a catch-all.**
- **Treat this as a first-pass synthesis, not as an IC-grade deep dive by itself.**
- **If the user asks what would change the view, recommend escalating to `analysis` for proper invalidation logic.**
- **Treat all action and plan blocks as advisory framing rather than executable trading instructions.**
- **The value of `market-brief` is speed and completeness, not depth.** When depth is needed, route to `analysis`.
- **Layer separation is mandatory.** Do not let the composed output blur into a single undifferentiated recommendation.

## Composition

- Builds on the same shared loaders and scoring logic used by `market-data`, `market-analyze`, `decision-support`, and `strategy-design`.
- Produces artifacts that should be reused by `reports`, `analysis-history`, and `backtest-evaluator`.
- **`analysis` is the escalation path** when the caller needs stronger thesis discipline than the default brief provides.
- Should not be used when the user's question implies they need thesis-level rigor, variant views, or invalidation logic.
