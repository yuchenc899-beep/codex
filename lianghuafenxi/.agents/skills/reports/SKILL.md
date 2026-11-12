---
name: reports
description: "Inspect and export generated analysis artifacts. Use when user wants exact stored markdown, JSON state, or run metadata instead of rerunning analysis."
argument-hint: [run-or-report]
allowed-tools: Read, Glob, Bash(python3 *)
---

# Reports

Inspect or export stored report artifacts for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: use persisted `report.md`, `state.json`, and `metadata.json` artifacts from prior runs
- Primary purpose: surface exact stored outputs with rigorous provenance rather than recomputing them unnecessarily
- Research layer: artifact retrieval and faithful restatement only

## Use When

- The user wants a stored report, saved state file, or run metadata.
- The caller wants to inspect a prior `analysis`, `stock-data`, or `market-brief` result without rerunning it.
- The user wants export-oriented access to already generated outputs.
- The user asks to "show me the last report" or "what did the analysis say."

## Do Not Use When

- There is no prior artifact and the user actually wants fresh analysis.
- The user wants broad historical comparison or change-over-time analysis. Use `analysis-history`.
- The user only needs recent context locations. Use `session-status`.

## Inputs

- A run directory, report path, state path, metadata path, or an implied recent run.
- Optional symbol or date scope chosen by the host framework.
- Prefer explicit run or file references when reproducibility matters.

## Execution

### Step 1: Locate the exact artifact with explicit provenance

Prefer an explicit run directory or file path. Otherwise use session history, manifests, and the runtime `runs/` tree to resolve the most likely target.

**Provenance requirements:**
- Identify the artifact path (full path to run directory or file)
- Identify the generating command (from `metadata.json` if available)
- Identify the generation timestamp (from `metadata.json` or file system)
- Identify the symbol and any key parameters (from `state.json` or `metadata.json`)

### Step 2: Read the artifact together with provenance

Use `metadata.json` first when available, then `report.md` for human-readable output and `state.json` for structured inspection.

**Mandatory provenance disclosure:**
Every artifact retrieval must state:
- **Artifact path:** full path to the run directory or file
- **Generation time:** when the artifact was created
- **Generating command:** the command that produced it (if available)
- **Content type:** whether returning verbatim content, extracted fields, or summary

### Step 3: Return the stored content faithfully

Return the requested artifact content, path, or extracted fields without rerunning the analytical workflow. Preserve the stored wording unless the user explicitly asks for a summary.

**Faithful restatement rules:**
- Do not paraphrase artifact content into new narrative unless explicitly requested
- Do not blend artifact content with fresh interpretation without labeling the boundary
- Do not update or "improve" the stored language to reflect current knowledge
- If the stored content contains errors or outdated information, surface it as-is and note that it reflects the state at generation time

### Step 4: Guard against artifact confusion

When multiple artifacts exist or when the resolved artifact may not be what the user intended:
- State which fallback rule was used to select the artifact
- Offer to retrieve a different artifact if the user specifies one
- If the user asks about "the analysis" but multiple analyses exist, list the candidates and ask for clarification

## Output Contract

- Output should reference real stored artifact paths whenever possible.
- Caller-facing delivery standard:
  - **Mandatory provenance disclosure:** every response must include artifact path, generation time, and generating command (when available)
  - **Content type labeling:** state whether the response is verbatim artifact content, extracted fields, or a short summary
  - **Faithful restatement:** preserve the provenance of the stored result instead of paraphrasing it into an untraceable new narrative
  - **Temporal clarity:** make clear that the artifact reflects the state at generation time, not current state
  - **No silent updates:** do not "fix" or "improve" stored content to reflect current knowledge without explicit user request
  - **Artifact confusion prevention:** when multiple candidates exist, state which was selected and why
- Local limitation: no dedicated alternate export renderer is guaranteed beyond the stored files.

## Failure Handling

- If the target report is not found, return a direct not-found explanation with the search path used.
- If the artifact exists but is malformed, surface that parsing issue explicitly and return whatever content is recoverable.
- If multiple candidate runs match, prefer the most explicit path or state which fallback rule was used (e.g., "latest run for symbol X from command Y").
- If provenance metadata is incomplete, state what is missing (e.g., "generation command not available in metadata").

## Key Rules

- **Prefer reading stored artifacts over rerunning analysis.**
- **Provenance disclosure is mandatory, not optional.** Every artifact retrieval must state path, generation time, and command.
- **Faithful restatement is required.** Do not paraphrase stored content into new narrative without labeling the boundary.
- **Temporal clarity matters.** Make clear that artifacts reflect the state at generation time, not current state.
- **If the user asks to compare, browse, or narrate change over time, route to `analysis-history`.**
- **Guard against artifact confusion** by stating which artifact was selected when multiple candidates exist.

## Composition

- Often follows `analysis`, `stock-data`, or `market-brief`.
- Pairs with `analysis-history` and `session-status`.
- Should feed into `backtest-evaluator` when retrospective evaluation is needed.
