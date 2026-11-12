---
name: analysis
description: "Run a deeper one-symbol A-share research workflow. Use when user wants a research memo that goes beyond the default brief and pressure-tests thesis, catalysts, risks, and invalidation using persisted artifacts."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob, Grep
---

# Analysis

Run a deeper one-symbol analysis workflow for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/analysis/run.py`
- Primary purpose: build a research memo that enforces institutional thesis discipline through mandatory structural elements: explicit thesis statement, identified key drivers, articulated variant views, disconfirming evidence, and invalidation conditions
- Research layer: deeper memo that may compose descriptive, decision, and execution layers, but must pressure-test them rather than simply restate them
- Workflow stages: stage 1 `Strategy Framing`, stage 4 `Signal and State Interpretation`, and stage 6 `Decision Context` at memo depth
- Local executor guarantee: generate a persisted research packet and artifact set that the agent can elevate into a thesis-disciplined memo

## Use When

- The user asks "why," "what drives this," "what are the risks," or "what would change your view."
- The user wants a research memo suitable for investment committee review or retrospective evaluation.
- The user needs saved artifacts that will later feed `analysis-history`, `reports`, or `backtest-evaluator`.
- The user explicitly requests depth, thesis framing, catalyst analysis, or risk pressure-testing.
- The user wants to understand not just current state but what could go wrong or what would invalidate the current view.

## Do Not Use When

- The user wants the default concise full-stock brief. Use `market-brief`.
- The user only wants direct action, quantity, or stop and take-profit anchors. Use `decision-support`.
- The user only wants execution zones and checklist output. Use `strategy-design`.
- The user wants artifact retrieval or comparison rather than fresh computation. Use `reports` or `analysis-history`.
- The user wants batch triage rather than one-symbol depth. Use `market-screen` or `decision-dashboard`.
- The available evidence is too thin to support thesis-level claims. In this case, either narrow to `market-brief` or acknowledge evidence gaps explicitly.

## Inputs

- Normal case: one stock symbol.
- Optional market inputs: `--csv`, `--start`, `--end`, `--source`.
- Optional account inputs: `--capital`, `--cash`, `--position`, `--risk`, `--max-position`.
- Optional planning inputs: `--style`, `--hold-days`, `--depth compact|standard|deep`, `--strategy STRATEGY_ID` (repeatable).
- Optional news inputs: `--headline`, `--headline-file`, `--company-name`, `--alias`, `--max-items`.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Important assumption boundary: any benchmark, scenario, or portfolio assumption that comes from the user prompt rather than the local executor must be labeled as a user-supplied assumption in the final memo.

## Execution

### Step 1: Confirm evidence sufficiency for thesis-level analysis

Before proceeding, assess whether the available evidence supports thesis-level claims. Thesis-level analysis requires:
- Sufficient price history to identify trend structure and regime
- Observable technical or fundamental drivers that can be articulated specifically
- Enough context to frame at least one plausible alternative interpretation

If evidence is insufficient, either:
- Route to `market-brief` for a descriptive synthesis without thesis claims, or
- Proceed with `analysis` but explicitly narrow the thesis section to acknowledge evidence gaps

### Step 2: Run the local executor

```bash
python3 <bundle-root>/analysis/run.py <symbol> [--headline-file PATH] [--depth standard] [--strategy STRATEGY_ID]
```

### Step 3: Structure the memo with mandatory thesis discipline

The analysis memo must include these structural elements when evidence permits:

**Thesis Statement (mandatory):**
- One clear sentence stating the investment view
- Must be falsifiable: a thesis that cannot be wrong is not a thesis
- Example: "600519 is positioned for a trend continuation based on institutional accumulation and sector rotation tailwinds"

**Key Drivers (mandatory, 3-5 maximum):**
- Specific, observable factors supporting the thesis
- Ranked by importance
- Each driver must be concrete enough to monitor
- Example: "1) Net institutional inflow over 10 consecutive sessions, 2) Sector relative strength vs. benchmark, 3) Technical breakout above 200-day resistance"

**Primary Catalyst (mandatory when identifiable):**
- The single most important near-term event or condition that would validate or accelerate the thesis
- Must have observable timing or trigger conditions
- If no clear catalyst exists, state that explicitly: "No identifiable near-term catalyst; thesis depends on continuation of current technical structure"

**Variant View (mandatory):**
- At least one alternative interpretation of the same evidence
- Must be intellectually honest, not a strawman
- Should articulate why a reasonable investor might reach a different conclusion
- Example: "Alternative view: current strength reflects late-cycle momentum exhaustion rather than institutional accumulation; volume profile suggests retail participation rather than smart money"

**Disconfirming Evidence (mandatory):**
- Specific observations that weaken or contradict the thesis
- Must be current and material, not hypothetical
- If no material disconfirming evidence exists, state that explicitly but acknowledge this is unusual
- Example: "Disconfirming: sector breadth is narrowing, with only 30% of sector constituents above their 50-day MA despite index strength"

**Invalidation Conditions (mandatory):**
- Specific, observable conditions that would falsify the thesis
- Must include both price-based and non-price-based conditions
- Should be monitorable in real-time or near-real-time
- Example: "Thesis invalidated if: 1) price closes below 180 support on volume, 2) sector relative strength turns negative for 3+ sessions, 3) institutional flow reverses to net selling"

**Evidence Gaps (mandatory when material):**
- Explicit acknowledgment of what is not known or not observable
- Should state what additional information would strengthen or weaken the thesis
- Example: "Evidence gaps: no visibility into institutional mandate changes, limited fundamental disclosure on Q4 margins, unclear regulatory timeline for sector policy"

### Step 4: Separate layers explicitly

When the memo includes decision support or execution planning layers, keep them visibly distinct:
- Use clear section headers or transitions
- Restate the account or style assumptions that drive those layers
- Do not let action or execution framing masquerade as thesis validation

### Step 5: Preserve the artifact trail

Reference the generated run directory when handing off to `reports`, `analysis-history`, or `backtest-evaluator`. The artifact should be complete enough to support retrospective evaluation without requiring conversational context.

## Output Contract

- Minimum local executor output: human-readable text beginning with `# <symbol> Analysis`.
- Minimum local sections: `Data Perspective`, `Intelligence`, `Battle Plan`, and `Workflow Blueprint` when available.
- Artifact side effects: writes one dated run directory with `state.json`, `report.md`, and `metadata.json`.
- Caller-facing delivery standard:
  - **Mandatory thesis structure:** every analysis memo must include thesis statement, key drivers, primary catalyst (or explicit statement that none exists), variant view, disconfirming evidence, and invalidation conditions
  - **Evidence sufficiency:** if any mandatory element cannot be supported by available evidence, state that gap explicitly rather than fabricating content
  - **Provenance separation:** distinguish computed facts from heuristic interpretation, optional enrichments from core analysis, and user-supplied assumptions from local defaults
  - **Manual context handling:** if manual headlines are used, label them as user-supplied or file-backed context and explicitly state they are not independently verified
  - **Confidence framing:** treat numeric `confidence` fields as heuristic conviction scores, never as statistical hit-rate estimates or calibrated probabilities
  - **Layer visibility:** keep the distinction between descriptive analysis, decision support, and execution planning visible; do not collapse the memo into a disguised order ticket
  - **Non-modeled risks:** when decision or execution layers are included, surface material non-modeled risks including catalyst uncertainty, liquidity constraints, gap risk, limit behavior, and stop slippage

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Market-data failures: readable failure text beginning with `执行失败:`.
- Optional fundamentals degrade fail-open through the shared helper.
- If `--headline-file` is unreadable or malformed, the command returns readable `执行失败:` text.
- **Evidence-thin scenarios:** if the available evidence cannot support thesis-level claims, either:
  - Route to `market-brief` for descriptive synthesis without thesis structure, or
  - Proceed with `analysis` but explicitly acknowledge evidence gaps in each mandatory section
  - Never pad evidence-thin sections with generic narrative or fabricated conviction

## Key Rules

- **Depth means better pressure-testing, not just more words.** The value of `analysis` over `market-brief` is structural thesis discipline, not length.
- **Thesis structure is mandatory, not optional.** If evidence cannot support a thesis element, acknowledge the gap explicitly.
- **Variant views must be intellectually honest.** Do not create strawman alternatives just to fill the section.
- **Invalidation conditions must be specific and monitorable.** Vague conditions like "if the market changes" are not acceptable.
- **Preserve explicit provenance** for any news, fundamental, or user-supplied context.
- **Do not present heuristic confidence or battle-plan outputs as order instructions.**
- **Route to `decision-support` or `strategy-design`** when the user wants the narrower action or execution layer rather than the full memo.

## Composition

- Builds on `market-data`, `market-analyze`, `decision-support`, `strategy-design`, and optional `news-intel` logic.
- Produces artifacts that can feed `reports`, `analysis-history`, and `backtest-evaluator`.
- Often serves as the deepest one-symbol artifact before retrospective evaluation.
- Should be the default choice when the user's question implies they need thesis-level rigor rather than just current-state description.
