---
name: data-sync
description: "Run or inspect data synchronization workflows. Use when user wants the stage-2 data-acquisition control surface: freshness checks, provider health, source comparison, stale-artifact diagnosis, and explicit next actions."
argument-hint: [symbol-or-source]
allowed-tools: Read, Glob, Grep, Bash(python3 *)
---

# Data Sync

Run or inspect data synchronization workflows for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: use runtime artifacts, manifests, bundle diagnostics, and host-provided sync steps
- Primary purpose: define the data-refresh, source-health, and freshness-audit workflow without overstating local orchestration support
- Research layer: data infrastructure (Stage 2: Data Collection & Quality Assurance - Data refresh and validation)
- Workflow stage: stage 2 `Data Collection & Quality Assurance`

## Use When

- The user wants to refresh source data.
- The user wants to compare provider behavior or diagnose stale records.
- The caller needs an explicit audit of whether current artifacts are fresh enough for research, screening, or backtesting.
- The user wants to know what must happen before a clean rerun.
- The user wants to verify data freshness before critical decisions.
- The user wants to diagnose data quality issues or provider failures.

## Do Not Use When

- The user wants immediate one-symbol analysis and the existing data is already sufficient.
- The user only wants runtime context locations. Use `session-status`.
- The user wants normalization or feature enrichment of an already available dataset. Use `market-data`.
- The user wants to analyze data quality after collection. Use `market-data` for quality assessment.

## Inputs

- A symbol, a provider name, a date window, or a sync scope.
- Optional host-side parameters such as freshness threshold, source priority, or required artifact types.
- Optional user requirement such as:
  - current-day screening freshness
  - backtest-grade historical coverage
  - point-in-time fundamental correctness
  - explicit provider comparison

## Execution

### Step 1: Classify the sync request

Determine which type of sync operation is needed:

**Sync request types:**
- **Freshness audit:** Check if existing data is recent enough for intended use
- **Provider comparison:** Compare data from multiple sources for consistency
- **Missing history diagnosis:** Identify gaps in historical data coverage
- **Symbol-level refresh:** Update data for specific symbols
- **Artifact lineage check:** Verify data provenance and transformation chain
- **Pre-backtest readiness check:** Validate data quality for backtesting
- **Bulk refresh:** Update entire universe or watchlist
- **Incremental update:** Add only new data since last sync

**Use case classification:**
- **Descriptive analysis:** Lower freshness requirement (1-2 days stale acceptable)
- **Screening:** Medium freshness requirement (same-day data preferred)
- **Decision support:** High freshness requirement (intraday data needed)
- **Backtesting:** Historical completeness required (no gaps, point-in-time correct)
- **Live trading:** Real-time or near-real-time data required

### Step 2: Inspect existing data state

Audit current data availability and quality:

**Data inventory:**
- [ ] Which symbols have data available
- [ ] Date range for each symbol (start date, end date)
- [ ] Data freshness (latest date, days since last update)
- [ ] Data source (provider, file, cache)
- [ ] Data completeness (% of expected dates present)
- [ ] Data quality score (from market-data if available)

**Artifact inspection:**
- [ ] Runtime artifacts (state.json, report.md, metadata.json)
- [ ] Manifests (data source declarations, version info)
- [ ] Bundle diagnostics (error logs, sync logs)
- [ ] File timestamps (when files were last modified)
- [ ] Cache status (what is cached, cache age)

**Provider status:**
- [ ] Which providers are configured (akshare, tushare, etc.)
- [ ] Provider health (last successful fetch, error rate)
- [ ] Provider rate limits (requests remaining, reset time)
- [ ] Provider coverage (which symbols, which fields)
- [ ] Provider latency (typical fetch time)

### Step 3: Evaluate data readiness

Assess whether existing data meets requirements:

**Freshness evaluation:**
- **Fresh (< 1 day old):** Suitable for all use cases
- **Recent (1-3 days old):** Suitable for descriptive analysis, screening
- **Stale (3-7 days old):** Suitable for historical analysis only
- **Very stale (> 7 days old):** Requires refresh before any use
- **Missing:** No data available, must fetch

**Completeness evaluation:**
- **Complete (100%):** All expected dates present
- **Mostly complete (90-99%):** Minor gaps, acceptable for most uses
- **Incomplete (70-89%):** Significant gaps, use with caution
- **Sparse (< 70%):** Major gaps, unsuitable for analysis

**Quality evaluation:**
- **High quality (score 90-100):** Suitable for all uses including backtesting
- **Good quality (score 70-89):** Suitable for descriptive analysis, screening
- **Fair quality (score 50-69):** Use with caution, validate results
- **Poor quality (score < 50):** Requires refresh or alternative source

**Point-in-time correctness (for backtesting):**
- [ ] Corporate actions properly adjusted (splits, dividends)
- [ ] No look-ahead bias (data as-of historical dates)
- [ ] Survivorship bias addressed (delisted symbols included)
- [ ] Restatements handled (as-reported vs. as-restated)
- [ ] Suspension periods identified

### Step 4: Diagnose data issues

Identify specific problems requiring attention:

**Common data issues:**
- **Stale data:** Latest date is too old for intended use
- **Missing symbols:** Symbols in watchlist have no data
- **Incomplete history:** Gaps in date coverage
- **Provider failures:** Recent fetch attempts failed
- **Quality degradation:** Data quality score declining over time
- **Inconsistent sources:** Different providers show different values
- **Corporate action errors:** Splits/dividends not properly adjusted
- **Suspension gaps:** Suspension periods not identified
- **Delisting issues:** Delisted symbols missing from historical data

**For each issue:**
- Issue type and severity (critical, high, medium, low)
- Affected symbols (count and list)
- Impact on downstream workflows (which skills affected)
- Recommended action (refresh, validate, alternative source)
- Automation status (can be fixed automatically or requires manual intervention)

### Step 5: Generate sync plan

Create actionable plan to address issues:

**Sync plan components:**

**Part 1: Immediate actions (critical issues):**
- Symbols requiring immediate refresh (stale data blocking decisions)
- Provider health checks (if recent failures detected)
- Cache invalidation (if corrupted data suspected)
- Manual interventions (if automation unavailable)

**Part 2: Scheduled actions (high priority):**
- Bulk refresh for watchlist (if many symbols stale)
- Historical backfill (if gaps detected)
- Provider comparison (if inconsistencies suspected)
- Quality validation (if quality scores declining)

**Part 3: Maintenance actions (medium priority):**
- Routine refresh schedule (daily, weekly)
- Cache cleanup (remove old artifacts)
- Provider rotation (switch to backup if primary failing)
- Monitoring setup (alerts for future staleness)

**Part 4: Validation actions (before critical use):**
- Pre-backtest validation (point-in-time correctness)
- Pre-decision validation (freshness and quality)
- Cross-provider validation (consistency check)
- Manual spot checks (sample verification)

### Step 6: Execute or delegate sync operations

Perform sync based on automation availability:

**If local automation available:**
- Execute refresh commands directly
- Monitor progress and handle errors
- Validate results after sync
- Update artifacts and manifests

**If host-framework automation available:**
- Delegate to host-framework sync API
- Provide sync parameters (symbols, date range, providers)
- Monitor sync status
- Validate results after sync

**If manual intervention required:**
- Provide explicit instructions for manual refresh
- List specific commands to run
- Specify validation steps after manual sync
- Document what was done for audit trail

**Sync execution priorities:**
1. Critical symbols (blocking immediate decisions)
2. High-priority watchlist (screening, monitoring)
3. Historical backfill (backtesting preparation)
4. Routine maintenance (scheduled updates)

### Step 7: Validate sync results

After sync, verify data quality:

**Post-sync validation:**
- [ ] Freshness improved (latest date is now recent)
- [ ] Completeness improved (gaps filled)
- [ ] Quality maintained or improved (quality score)
- [ ] No new issues introduced (consistency checks)
- [ ] Artifacts updated (manifests, metadata)

**Validation checks:**
- Compare before/after freshness
- Compare before/after completeness
- Compare before/after quality scores
- Check for new gaps or inconsistencies
- Verify corporate action adjustments

**If validation fails:**
- Identify specific failures
- Recommend retry with different provider
- Recommend manual intervention
- Document issue for future investigation

### Step 8: Generate sync report

Organize findings into structured report:

**Part 1: Sync Summary**
- Sync scope (symbols, date range, providers)
- Sync timestamp
- Sync status (success, partial, failed)
- Symbols refreshed (count and list)
- Issues resolved (count and list)

**Part 2: Data Inventory**
- Total symbols with data
- Freshness distribution (fresh, recent, stale, very stale, missing)
- Completeness distribution (complete, mostly complete, incomplete, sparse)
- Quality distribution (high, good, fair, poor)
- Provider distribution (which providers used)

**Part 3: Issues Diagnosed**
For each issue:
- Issue type and severity
- Affected symbols
- Impact on workflows
- Recommended action
- Automation status

**Part 4: Sync Plan**
- Immediate actions (critical)
- Scheduled actions (high priority)
- Maintenance actions (medium priority)
- Validation actions (before critical use)

**Part 5: Sync Execution Results**
- Actions taken (refresh, backfill, validation)
- Success rate (% of actions successful)
- Failures (count and reasons)
- Manual interventions required

**Part 6: Post-Sync Validation**
- Freshness improvement (before/after)
- Completeness improvement (before/after)
- Quality improvement (before/after)
- Remaining issues (if any)

**Part 7: Readiness Assessment**
- Ready for descriptive analysis? (Yes/No/Conditional)
- Ready for screening? (Yes/No/Conditional)
- Ready for decision support? (Yes/No/Conditional)
- Ready for backtesting? (Yes/No/Conditional)
- Conditions or caveats (if conditional)

**Part 8: Next Steps**
- Downstream workflows ready to proceed
- Workflows blocked pending further sync
- Monitoring and alerting recommendations
- Scheduled maintenance recommendations

### Step 9: Return explicit sync diagnosis

When delivering results, maintain proper framing:

**Sync interpretation:**
- This is data infrastructure status, not investment recommendation
- Freshness and quality assessments are technical, not fundamental
- Readiness evaluation is for workflow purposes, not market timing
- Sync recommendations are operational, not strategic

**Automation transparency:**
- State which sync operations are locally automated
- State which operations require host-framework support
- State which operations require manual intervention
- State limitations of current automation

**Readiness framing:**
- Separate readiness for different use cases (analysis, screening, backtesting)
- State specific conditions or caveats for conditional readiness
- Recommend validation steps before critical use
- Tie readiness to next workflow stage

**Limitation disclosure:**
- State what sync can and cannot guarantee
- State point-in-time correctness limitations
- State survivorship bias limitations
- State provider coverage limitations

## Output Contract

- Expected result: sync status, stale-data diagnosis, provider comparison, or an explicit next-action plan.
- Caller-facing delivery standard:
  - **Eight-part structure:** Sync summary, data inventory, issues diagnosed, sync plan, execution results, post-sync validation, readiness assessment, next steps
  - **Scope identification:** State what is being audited (symbols, date range, providers)
  - **Evidence basis:** Identify evidence used (manifests, timestamps, runtime status, file inspection)
  - **Automation transparency:** State whether locally automated, partially automated, or host-dependent
  - **Readiness assessment:** Tie sync recommendation to next workflow stage (screening, analysis, backtesting, trading)
  - **Issue diagnosis:** Specific issues with severity, affected symbols, impact, recommended actions
  - **Sync plan:** Immediate, scheduled, maintenance, and validation actions
  - **Validation results:** Before/after comparison of freshness, completeness, quality
  - **Limitation disclosure:** State what sync can and cannot guarantee (point-in-time, survivorship, etc.)
- Local limitation:
  - The skill does not currently guarantee a full local provider-orchestration layer
  - The workflow may depend on external scheduling or host-side refresh behavior
  - Some sync operations may require manual intervention

## Failure Handling

- If the requested sync scope is not supported locally, state that explicitly.
- If available evidence is insufficient to diagnose freshness, say what is missing.
- If the user asks for backtest-grade readiness and the skill cannot verify survivorship, corporate-action, or point-in-time integrity, say so directly.
- If provider is unavailable or failing, recommend alternative sources or manual intervention.
- If sync execution fails, provide specific error details and retry recommendations.

## Key Rules

- **Do not imply a full provider-orchestration layer where none exists locally.**
- **Separate source-health diagnostics from market-analysis claims.**
- **Prefer explicit freshness and readiness language over vague advice to “rerun.”**
- **Treat descriptive-analysis readiness as a lower bar than backtest or live-verification readiness.**
- **Automation transparency is mandatory.** State what is automated vs. manual.
- **Readiness must be use-case specific.** Different standards for analysis, screening, backtesting, trading.
- **Issue diagnosis must be specific.** Type, severity, affected symbols, impact, actions.
- **Sync plan must be actionable.** Specific commands, parameters, validation steps.
- **Validation must be quantitative.** Before/after metrics, not just “looks better.”
- **Limitation disclosure is mandatory.** State what sync cannot guarantee.

## Composition

- Often paired with `session-status`, `market-data`, `stock-data`, and `backtest-evaluator`.
- Serves as the stage-2 control surface before broader research or validation workflows.
- Should be run before `market-screen` or `decision-dashboard` if data freshness is uncertain.
- Should be run before `backtest-evaluator` to ensure historical data quality.
- Can be triggered by `market-data` if quality issues detected.
- Results feed into readiness decisions for all downstream skills.
