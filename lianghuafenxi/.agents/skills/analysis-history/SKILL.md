---
name: analysis-history
description: "Inspect prior analysis records and artifacts. Use when user wants to browse, compare, or track how saved views changed over time rather than just reading one stored file."
argument-hint: [symbol-or-run]
allowed-tools: Read, Glob, Bash(python3 *)
---

# Analysis History

Inspect prior analysis history for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: inspect session history, run manifests, and persisted artifacts under the runtime tree
- Primary purpose: retrieve and compare existing saved results with rigorous provenance instead of re-running analysis blindly
- Research layer: historical chronology and comparison, not fresh analysis

## Use When

- The user wants to revisit prior analysis results for the same symbol.
- The user wants to compare historical runs, actions, or conclusions over time.
- The caller needs to locate old `state.json`, `report.md`, or `metadata.json` artifacts and summarize how they differ.
- The user asks "how has the view changed" or "what did we think last time."

## Do Not Use When

- The user wants one exact stored file rather than a historical view. Use `reports`.
- The user wants fresh analysis on current data. Use an analysis-facing skill instead.
- The user wants only runtime locations and recent command context. Use `session-status`.

## Inputs

- One symbol, a run path, or an implied recent run.
- Optional date or time filtering handled by the host framework if available.
- Optional comparison target such as another run, date, or command.

## Execution

### Step 1: Build the candidate artifact set with provenance

Use `session-status`, manifests, and the dated runtime `runs/` tree to identify matching saved runs.

**Provenance requirements for each candidate:**
- Artifact path (run directory)
- Generation timestamp
- Generating command
- Symbol and key parameters
- Available artifact files (state.json, report.md, metadata.json)

### Step 2: Establish chronology and provenance

For each run, capture the command, generation time, run directory, and available artifacts before making any comparison claim.

**Mandatory chronology disclosure:**
When presenting historical results, state:
- How many matching runs were found
- The time range covered
- Which runs are being compared (if comparison is requested)
- What fields are available for comparison across runs

### Step 3: Return a saved-history view with comparison discipline

Return the requested historical content, timeline, or comparison summary grounded in saved artifacts.

**Comparison discipline rules:**
- **Name both artifacts explicitly:** when comparing runs, state both run directories, generation times, and commands
- **Identify field changes:** state which fields changed, which were stable, and which were unavailable in one or both runs
- **Avoid hindsight bias:** describe what was saved at the time, not what now seems obvious in hindsight
- **Acknowledge thin comparison base:** if only one artifact exists, state that explicitly rather than inventing a trend
- **Separate observation from interpretation:** distinguish "field X changed from Y to Z" (observation) from "the view strengthened" (interpretation)

### Step 4: Guard against artifact confusion and hindsight bias

**Artifact confusion prevention:**
- If multiple runs exist for the same symbol, list them chronologically with generation times
- If the user's request is ambiguous, ask for clarification rather than guessing which runs to compare
- If runs used different parameters (e.g., different holding periods), state that explicitly

**Hindsight bias prevention:**
- Do not reinterpret old artifacts using current knowledge
- Do not judge old decisions based on outcomes that were not knowable at the time
- If comparing a decision to its outcome, recommend using `backtest-evaluator` for proper retrospective evaluation with realism limits

## Output Contract

- Output should reference concrete stored artifacts and their timestamps.
- Caller-facing delivery standard:
  - **Mandatory provenance for each run:** state artifact path, generation time, and command
  - **Explicit comparison boundaries:** when comparing runs, name both artifacts and state which fields are being compared
  - **Field-level change tracking:** identify which fields changed, which were stable, and which were unavailable
  - **Chronological clarity:** present runs in time order with clear timestamps
  - **Hindsight bias guard:** describe what was saved at the time, not what seems obvious now
  - **Thin-base acknowledgment:** if comparison base is thin (only 1-2 runs), state that explicitly
  - **Grounded in artifacts:** keep the narrative grounded in saved artifacts rather than reconstructed conversational memory
- Local limitation: the skill cannot recover history that was never persisted.

## Failure Handling

- If no matching artifact is found, return a clear not-found explanation with the search criteria used.
- If a file exists but cannot be parsed, report that explicitly instead of hiding the failure.
- If the requested comparison depends on missing runs, state the gap instead of smoothing over it.
- If provenance metadata is incomplete for some runs, state what is missing.

## Key Rules

- **Prefer persisted history over regeneration** unless the user explicitly wants a rerun.
- **Provenance is mandatory for every run referenced.** State path, time, and command.
- **Comparison discipline is required.** Name both artifacts, identify field changes, avoid hindsight bias.
- **Avoid hindsight bias** by describing what was saved at the time, not what now seems obvious in hindsight.
- **If only one artifact exists, say that explicitly** rather than inventing a trend.
- **Separate observation from interpretation** when describing how views changed over time.
- **For outcome-based evaluation, route to `backtest-evaluator`** for proper retrospective evaluation with realism limits.

## Composition

- Commonly paired with `reports`, `backtest-evaluator`, and `session-status`.
- Often serves as the historical control surface before running retrospective evaluation.
- Should feed into process improvement discussions about how research quality has evolved.
