---
name: strategy-chat
description: "Run a multi-turn strategy Q&A workflow over a stock. Use when user wants iterative discussion anchored to an explicit symbol, artifact, or prior run instead of a one-shot report."
argument-hint: [question-or-stock]
allowed-tools: Read, Glob, Grep, Bash(python3 *)
---

# Strategy Chat

Run a multi-turn strategy Q&A workflow for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: compose `analysis`, `market-brief`, `technical-scan`, `fundamental-context`, and `news-intel`
- Primary purpose: keep a multi-turn strategy discussion coherent with rigorous artifact reuse and provenance discipline
- Research layer: conversational wrapper over descriptive, decision, or execution layers, depending on the turn

## Use When

- The user asks follow-up questions instead of wanting a single report.
- The user wants to explore scenarios, invalidation points, or alternative strategy styles conversationally.
- The caller needs continuity over the same symbol, run artifact, or saved analysis rather than restarting the workflow every turn.
- The user wants to iterate on a thesis or decision frame through dialogue.

## Do Not Use When

- The user wants a one-shot concise report. Use `market-brief`.
- The user wants only a direct action or quantity. Use `decision-support`.
- The user wants exact artifact retrieval or export. Use `reports`.
- The user wants broad historical comparison rather than turn-by-turn discussion. Use `analysis-history`.
- The conversation has no clear anchor (symbol, artifact, or prior analysis). Clarify the anchor first.

## Inputs

- A user question, optionally plus a stock symbol.
- Preferably an explicit prior artifact, run, or earlier analysis result.
- Optional prior context from earlier turns in the same session.
- Optional user assumptions such as capital, position, benchmark, holding horizon, or preferred style.

## Execution

### Step 1: Anchor the symbol, horizon, and evidence explicitly

**Mandatory anchor requirements:**
- Every substantive turn must have a clear anchor: a specific symbol, a saved artifact, or an explicit recent analysis result
- If the anchor is ambiguous (e.g., user says "what about the risks" without specifying which symbol or analysis), ask for clarification before proceeding
- If reusing a prior artifact, state which artifact (path, generation time, command) is being used as the anchor
- If reusing session context from a prior turn, state what context is being reused

**Anchor clarity rules:**
- Do not assume the user wants to continue discussing the same symbol if they haven't mentioned it in the current turn
- Do not assume prior assumptions (capital, holding period, style) still apply if the user's question suggests they may have changed
- When in doubt, ask: "Are you still asking about [symbol] based on [artifact/prior turn]?"

### Step 2: Reuse prior artifacts instead of recomputing blindly

**Artifact reuse discipline:**
- Prefer saved `analysis` or `market-brief` artifacts when answering follow-up questions
- State which artifact is being reused: path, generation time, and command
- Recompute only when:
  - The user explicitly asks for a refresh
  - The old evidence is too stale for the question (state the staleness threshold used)
  - The user has changed key assumptions that invalidate the prior artifact

**Staleness assessment:**
- If the artifact is more than [N] days old and the user is asking about current positioning, recommend a refresh
- If the artifact was generated before a material event (earnings, news, regime change), recommend a refresh
- State the staleness assessment explicitly: "The last analysis was generated [X] days ago; recommend refreshing if current positioning is needed"

### Step 3: Answer in labeled mode with explicit layer identification

**Layer labeling requirements:**
Each substantive reply must make clear which mode it is operating in:
- **Descriptive analysis mode:** interpreting current market state without action or sizing
- **Decision-support mode:** providing conditional action and sizing guidance with explicit assumptions
- **Execution-planning mode:** designing entry/exit zones and checklists for an accepted view
- **Retrospective evaluation mode:** reviewing prior decisions against outcomes

**Mode transition handling:**
- If the user changes mode (e.g., from asking about current state to asking about position sizing), acknowledge the transition explicitly
- State which new assumptions are needed for the new mode
- If prior assumptions no longer apply, ask the user to confirm or update them

### Step 4: Track assumption changes and invalidation

**Assumption tracking:**
- If the user changes horizon, position context, or thesis assumptions, state whether the prior conclusion still applies
- If assumptions have changed materially, recommend regenerating the decision or execution frame rather than stretching stale context
- Maintain a running list of active assumptions for the conversation (symbol, horizon, capital, position, style, etc.)

**Invalidation monitoring:**
- If the prior analysis included invalidation conditions, check whether any have been triggered
- If invalidation conditions have been met, state that explicitly and recommend reassessment
- Do not let an old buy, hold, sizing, or execution view survive unexamined after assumptions change or invalidation conditions trigger

### Step 5: Guard against conversational drift and false continuity

**Drift prevention:**
- Continuity is conditional on stable anchor and assumptions, not free-form drift
- If the conversation has drifted away from the original anchor, acknowledge that and establish a new anchor
- Do not blend multiple symbols, timeframes, or thesis frames into a single confused narrative
- If the user asks a question that cannot be answered using the current anchor, say so explicitly

**False continuity prevention:**
- Do not pretend that conversational memory is equivalent to saved artifacts
- Do not carry forward conclusions from prior turns if the evidence basis has changed
- If the user references "what we discussed earlier" but no artifact exists, clarify what is being referenced

## Output Contract

- Expected result: one conversational but analysis-grounded response.
- Caller-facing delivery standard:
  - **Mandatory anchor disclosure:** name the anchor basis for the current answer (fresh run, saved artifact path, or prior turn context)
  - **Artifact provenance:** if reusing a saved artifact, state path, generation time, and command
  - **Layer identification:** state whether the current reply is descriptive analysis, decision support, or execution planning
  - **Assumption tracking:** identify unresolved assumptions or changed assumptions before presenting a confident conclusion
  - **Staleness assessment:** if reusing old evidence, state how old it is and whether refresh is recommended
  - **Invalidation monitoring:** if prior analysis included invalidation conditions, check whether they have been triggered
  - **Prefer artifact reuse over regeneration:** only recompute when explicitly requested or when staleness/assumption changes require it
- Local limitation: no dedicated local chat persistence engine exists. Continuity depends on the host framework and the explicit anchor provided.

## Failure Handling

- If the symbol or prior context is ambiguous, say so and ask the host framework to clarify through normal interaction.
- If supporting data is partial, continue with bounded uncertainty rather than pretending full confidence.
- If the user changes the thesis materially, recommend a refresh through `market-brief` or `analysis` instead of stretching stale context.
- If the anchor is lost (e.g., user switches symbols without stating it), ask for clarification rather than guessing.
- If assumptions have changed but the user hasn't acknowledged it, surface the change and ask whether prior conclusions still apply.

## Key Rules

- **Continuity is conditional, not free-form drift.** Stable anchor and assumptions are required.
- **Prefer persisted artifacts or explicit recent outputs over fuzzy conversational memory.**
- **Do not let an old buy, hold, sizing, or execution view survive unexamined after assumptions change.**
- **Keep the answer strategic rather than collapsing into generic chat.**
- **Anchor clarity is mandatory.** Every turn must have a clear symbol, artifact, or prior analysis basis.
- **Layer identification is mandatory.** State which mode (descriptive, decision, execution) the current turn is operating in.
- **Assumption tracking is mandatory.** Maintain and surface the active assumption set for the conversation.
- **Staleness assessment is required when reusing artifacts.** State how old the evidence is and whether refresh is recommended.
- **Invalidation monitoring is required.** Check whether prior invalidation conditions have been triggered.

## Composition

- Usually builds on `analysis`, `market-brief`, `technical-scan`, `fundamental-context`, and `news-intel`.
- Should hand off to `reports`, `analysis-history`, `decision-support`, or `strategy-design` when the user narrows the task into a cleaner adjacent skill.
- Should route to `backtest-evaluator` when the user wants to evaluate a prior decision against outcomes.
