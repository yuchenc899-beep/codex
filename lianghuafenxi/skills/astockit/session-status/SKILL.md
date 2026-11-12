---
name: session-status
description: "Inspect bundle status, runtime configuration, and recent execution context. Use when user wants the operational audit surface: runtime root, recent runs, current context, and where the workflow left off."
argument-hint: [none]
allowed-tools: Bash(python3 *), Read, Glob
---

# Session Status

Inspect bundle runtime state for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/session-status/run.py`
- Primary purpose: expose the bundle root, config path, output root, and recent command history so the agent can continue the workflow from explicit context instead of guesswork
- Research layer: operational monitoring (Cross-cutting concern for all workflow stages)
- Workflow role: operational control surface spanning artifact reuse, history lookup, and monitoring handoff
- Local executor guarantee: return the current runtime root, config path, last symbol, Feishu mode, and recent history for the chosen execution context

## Use When

- The user asks what the bundle has been doing.
- The user wants to know where runtime output is being written.
- The user wants to confirm the current Feishu mode or the last-used symbol.
- The agent needs to decide whether to rerun, reuse artifacts, or continue a monitoring workflow.
- The user wants to understand current session state and context.
- The user wants to resume work from a previous session.
- The user wants to audit recent activity for troubleshooting.

## Do Not Use When

- The user wants analysis or decision output. Use a market-facing skill.
- The user wants to inspect a specific prior report in detail. Use `reports` or `analysis-history`.
- The user wants a data-freshness diagnosis rather than runtime context. Use `data-sync`.
- The user wants portfolio performance tracking. Use `paper-trading`.

## Inputs

- No required positional arguments.
- Optional `--context` through the local script if the caller needs a non-default execution context.

## Execution

### Step 1: Gather runtime context

Collect comprehensive session state information:

**Runtime configuration:**
- [ ] Bundle root directory path
- [ ] Config file path and contents
- [ ] Output directory path
- [ ] Execution context (default or custom)
- [ ] Environment variables (if relevant)
- [ ] Python version and dependencies

**Session state:**
- [ ] Last symbol used
- [ ] Last skill executed
- [ ] Last execution timestamp
- [ ] Session start time
- [ ] Session duration
- [ ] Active watchlists (if any)

**Integration status:**
- [ ] Feishu mode (enabled/disabled)
- [ ] Notification settings
- [ ] External integrations (if any)
- [ ] API connections (if any)

**Recent activity:**
- [ ] Recent commands (last 10-20)
- [ ] Recent symbols analyzed
- [ ] Recent artifacts created
- [ ] Recent errors or warnings
- [ ] Recent data syncs

### Step 2: Inspect artifact state

Audit available artifacts and their status:

**Artifact inventory:**
- [ ] Analysis reports (count, latest date)
- [ ] Stock data packets (count, latest date)
- [ ] Backtest results (count, latest date)
- [ ] Paper trading records (count, latest date)
- [ ] Screening results (count, latest date)
- [ ] Dashboard snapshots (count, latest date)

**Artifact freshness:**
- [ ] Latest artifact timestamp
- [ ] Stale artifacts (> 7 days old)
- [ ] Orphaned artifacts (no longer referenced)
- [ ] Incomplete artifacts (partial writes)

**Artifact locations:**
- [ ] Output root directory
- [ ] Run directories (dated subdirectories)
- [ ] Cache directories
- [ ] Log directories
- [ ] Export directories

### Step 3: Assess workflow state

Determine where the workflow left off:

**Workflow stage identification:**
- **Stage 1 (Universe Formation):** Last watchlist import or screening
- **Stage 2 (Data Collection):** Last data sync or market-data run
- **Stage 3 (Data Cleaning):** Last normalization or validation
- **Stage 4 (Feature Engineering):** Last market-analyze or technical-scan
- **Stage 5 (Backtesting):** Last backtest-evaluator run
- **Stage 6 (Risk Management):** Last decision-support or strategy-design
- **Stage 7 (Live Trading):** Last paper-trading execution

**Workflow continuity:**
- [ ] Can workflow resume from last state?
- [ ] Are artifacts reusable or stale?
- [ ] Are dependencies satisfied?
- [ ] Are there blocking issues?

**Next logical steps:**
- Based on last activity, what should happen next?
- Which artifacts can be reused?
- Which skills should be invoked?
- What validation is needed before proceeding?

### Step 4: Diagnose operational issues

Identify any operational problems:

**Common issues:**
- **Stale artifacts:** Artifacts too old for current use
- **Missing dependencies:** Required data or artifacts not available
- **Configuration errors:** Invalid or missing config settings
- **Permission issues:** Cannot write to output directories
- **Disk space issues:** Output directory full or near capacity
- **Integration failures:** Feishu or other integrations not working

**For each issue:**
- Issue type and severity
- Impact on workflow
- Recommended resolution
- Workaround (if available)

### Step 5: Generate status report

Organize findings into structured report:

**Part 1: Runtime Configuration**
- Bundle root directory
- Config file path
- Output directory path
- Execution context
- Integration status (Feishu, etc.)

**Part 2: Session State**
- Session start time and duration
- Last symbol used
- Last skill executed
- Last execution timestamp
- Active watchlists

**Part 3: Recent Activity**
- Recent commands (last 10-20 with timestamps)
- Recent symbols analyzed
- Recent artifacts created
- Recent errors or warnings
- Recent data syncs

**Part 4: Artifact Inventory**
- Analysis reports (count, latest)
- Stock data packets (count, latest)
- Backtest results (count, latest)
- Paper trading records (count, latest)
- Screening results (count, latest)
- Dashboard snapshots (count, latest)

**Part 5: Artifact Freshness**
- Latest artifact timestamp
- Stale artifacts (count and list)
- Orphaned artifacts (count and list)
- Incomplete artifacts (count and list)

**Part 6: Workflow State**
- Current workflow stage
- Last completed stage
- Next logical steps
- Artifacts available for reuse
- Dependencies satisfied/missing

**Part 7: Operational Issues**
- Issues detected (count and list)
- Severity distribution
- Impact on workflow
- Recommended resolutions

**Part 8: Recommendations**
- Immediate actions (critical issues)
- Artifact cleanup (stale/orphaned)
- Workflow resumption (next steps)
- Monitoring setup (ongoing)

### Step 6: Run the local executor

```bash
python3 <bundle-root>/session-status/run.py
```

### Step 7: Use result as operational audit

When delivering results, focus on actionable context:

**Operational context interpretation:**
- This is runtime state, not analysis or recommendations
- Artifact inventory is for reuse decisions, not performance assessment
- Recent activity is for continuity, not evaluation
- Workflow state is for resumption, not validation

**Artifact reuse guidance:**
- State which artifacts are fresh enough to reuse
- State which artifacts are stale and should be regenerated
- State which artifacts are missing and need generation
- State dependencies between artifacts

**Workflow resumption guidance:**
- State where workflow left off
- State next logical steps
- State which skills to invoke next
- State validation needed before proceeding

**Issue resolution guidance:**
- State operational issues clearly
- Provide specific resolution steps
- Prioritize by severity and impact
- Offer workarounds when available

## Output Contract

- Minimum local executor output: human-readable text beginning with `A-Stockit runtime status`.
- Core fields: bundle root, config file, output directory, Feishu mode, last symbol, and recent context history.
- Side effects: adds one `session-status` history record for the current execution context.
- Caller-facing delivery standard:
  - **Eight-part structure:** Runtime configuration, session state, recent activity, artifact inventory, artifact freshness, workflow state, operational issues, recommendations
  - **Operational context only:** Present as runtime state, not analysis or recommendations
  - **Artifact reuse guidance:** State which artifacts are fresh/stale/missing and reusable
  - **Workflow resumption guidance:** Identify likely next useful artifact or skill for resuming work
  - **Issue diagnosis:** Specific operational issues with severity and resolution steps
  - **Scope clarity:** This is a context surface, not a semantic summary of every run
  - **Actionable recommendations:** Immediate actions, cleanup, resumption steps, monitoring
  - **No analysis claims:** Runtime state only, no market views or investment recommendations

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Unexpected runtime issues: readable failure text beginning with `执行失败:`.
- Missing config or output directories: report issue and recommend initialization.
- Corrupted history or artifacts: flag for cleanup and regeneration.
- Permission issues: report specific permission errors and resolution steps.

## Key Rules

- **Use this skill for operational context only.**
- **Prefer it before rerunning workflows just to locate prior outputs.**
- **Treat it as the staging surface for artifact reuse, monitoring continuation, and workflow resumption.**
- **Artifact inventory is for reuse decisions, not performance evaluation.**
- **Recent activity is for continuity, not retrospective analysis.**
- **Workflow state is for resumption, not validation.**
- **Issue diagnosis must be specific and actionable.**
- **Recommendations must be prioritized by severity and impact.**
- **No analysis or investment claims.** This is operational monitoring only.

## Composition

- Pairs naturally with `reports`, `analysis-history`, `data-sync`, and `paper-trading`.
- Should be used before artifact-dependent skills to check reusability.
- Can inform `data-sync` about what needs refreshing.
- Can inform `reports` and `analysis-history` about available artifacts.
- Can inform workflow resumption decisions across all skills.
