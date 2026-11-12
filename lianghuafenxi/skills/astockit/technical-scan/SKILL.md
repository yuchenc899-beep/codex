---
name: technical-scan
description: "Run a technical-only scan over one symbol. Use when user explicitly wants trend, levels, volume, volatility, or chart-pattern context without broader thesis, sizing, or execution claims."
argument-hint: [symbol]
allowed-tools: Read, Glob, Grep, Bash(python3 *)
---

# Technical Scan

Run a technical-only scan for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: compose `market-analyze` plus any needed direct data or saved-artifact inspection
- Primary purpose: isolate the technical lens from broader narrative, portfolio, or execution layers
- Research layer: descriptive technical commentary only
- Local limitation: no dedicated standalone pattern engine or persisted technical-scan artifact exists yet

## Use When

- The user explicitly wants technical context rather than a full report.
- The caller wants to discuss trend structure, moving-average alignment, support and resistance, volume behavior, or chart language separately.
- The user wants a technical checkpoint before moving to decision or strategy layers.
- The user wants technical invalidation or monitoring conditions without broader thesis framing.

## Do Not Use When

- The user wants a full one-symbol report. Use `market-brief`.
- The user wants a direct action, quantity, or position recommendation. Use `decision-support`.
- The user wants structured execution zones and checklist output. Use `strategy-design`.
- The user wants broader thesis, catalysts, or disconfirming evidence beyond technicals. Use `analysis`.
- The user wants only the bounded scored state summary. Use `market-analyze`.

## Inputs

- One stock symbol.
- Optional local market-data source when the host framework chooses to supply it.
- Optional neighboring context from `market-analyze`, `market-data`, or a persisted artifact.
- Optional timeframe or horizon if the host framework supports it. If absent, do not pretend a separate timeframe analysis exists.

## Execution

### Step 1: Anchor the symbol and technical basis

Prefer an explicit symbol plus either:

- a fresh `market-analyze` result
- a named market-data or stock-data artifact
- a directly inspected local dataset

If the symbol or evidence basis is reused from session context, say so.

### Step 2: Reuse the descriptive foundation honestly

Use `market-analyze` for the core state summary:

- score and bias
- trend and regime
- support and resistance
- notes and risk flags
- snapshot-level volume and ATR context

Do not claim that `market-analyze` directly provides a full chart-pattern engine or every oscillator under the sun. If extra technical color comes from direct data inspection rather than the state summary, label that boundary explicitly.

### Step 3: Add technical interpretation only where evidence supports it

If the available data or artifact supports it, the agent may extend the scan with:

- pattern language such as consolidation, breakout attempt, pullback, rejection, or exhaustion
- moving-average alignment commentary
- volatility compression or expansion commentary
- volume-confirmation or volume-divergence commentary
- exact technical invalidation or monitoring levels

These are agent-composed interpretations, not guaranteed local signal-engine outputs.

### Step 4: Deliver a bounded technical note

Keep the answer technical-only and separate:

- what the snapshot explicitly reports
- what direct data inspection adds
- what is heuristic chart interpretation

## Output Contract

- Expected result: a readable technical-only scan rather than a persisted standalone artifact.
- Caller-facing delivery standard:
  - state the technical basis used, for example fresh `market-analyze`, direct data inspection, or a saved artifact path
  - keep the answer technical-only and avoid widening into fundamentals, portfolio action, or execution planning unless the user explicitly changes the request
  - include technical invalidation or monitoring conditions when the evidence supports them
  - label pattern language such as breakout, base, exhaustion, pullback, or rejection as heuristic unless the evidence is explicit
- Local non-guarantees:
  - no dedicated standalone pattern-engine contract
  - no persisted technical-scan artifact by default
  - no promise that every technical claim is directly computed by a local runner

## Failure Handling

- If the symbol cannot be resolved, return readable guidance instead of guessing.
- If the technical basis is stale, partial, or insufficient, say what is missing rather than fabricating pattern claims.
- If the user’s request drifts into action or execution planning, route to `decision-support` or `strategy-design` instead of silently widening scope.

## Key Rules

- Keep the scope narrow and technical.
- Do not silently drift into broader narrative analysis.
- Use `market-analyze` as the descriptive anchor unless the caller already provides a better technical basis.
- Be explicit when a conclusion is chart language rather than a directly computed local signal.
- Technical risk/reward commentary may describe the setup, but should not become a trading instruction.

## Composition

- Usually follows `market-data` or `market-analyze`.
- Often precedes `decision-support`, `strategy-design`, or `analysis`.
