---
name: watchlist
description: "Manage watchlist workflows after import. Use when user wants the stage-1 universe-management workflow: grouping, coverage intent, review cadence, artifact reuse, and repeated tracking after ingestion."
argument-hint: [watchlist-operation]
allowed-tools: Read, Glob, Bash(python3 *)
---

# Watchlist

Manage watchlist workflows for: $ARGUMENTS

## Overview

- Implementation status: workflow-only
- Current backing path: use `watchlist-import` plus host-side or file-based watchlist handling
- Primary purpose: define the post-import watchlist lifecycle without pretending a durable local watchlist service already exists
- Research layer: universe management (Stage 1: Strategy Design & Hypothesis Formation - Universe definition and maintenance)
- Workflow stage: stage 1 `Strategy Design & Universe Formation`, with handoff into screening and monitoring

## Use When

- The user wants to continue after a raw watchlist import.
- The user wants grouping, enrichment, review cadence, or repeated tracking of selected symbols.
- The caller wants a stable universe-management concept even before a dedicated storage layer exists locally.
- The user wants to organize symbols by strategy, sector, priority, or other criteria.
- The user wants to define monitoring cadence (daily, weekly, event-driven).
- The user wants to track watchlist changes over time.

## Do Not Use When

- The user is still providing a raw list of symbols. Use `watchlist-import`.
- The user wants immediate ranking rather than watchlist management. Use `market-screen` or `decision-dashboard`.
- The user wants a specific saved artifact or run comparison. Use `reports` or `analysis-history`.
- The user wants portfolio tracking with positions and P&L. Use `paper-trading`.

## Inputs

- A watchlist operation or intent.
- Optional imported watchlist items from `watchlist-import`.
- Optional symbol subsets to group, tag, review, or monitor.
- Optional host-side rules such as:
  - coverage tiers
  - review cadence
  - strategy buckets
  - event-driven monitoring lists

## Execution

### Step 1: Normalize raw input first

If the user starts from raw text or files, run `watchlist-import` before attempting watchlist management.

**Import validation:**
- [ ] Symbols are resolved (not unresolved items)
- [ ] Import quality is sufficient (>70% resolution rate)
- [ ] Confidence scores are acceptable (mostly high/medium)
- [ ] No major format or existence issues

If import quality is low, route back to `watchlist-import` for cleanup before proceeding.

### Step 2: Define watchlist management objectives

Identify what the user wants to accomplish:

**Management operations:**
- **Create:** Build new watchlist from imported symbols
- **Update:** Add/remove symbols from existing watchlist
- **Group:** Organize symbols by strategy, sector, priority, etc.
- **Tag:** Add metadata tags (research, screen, execute, monitor, etc.)
- **Review:** Assess watchlist for stale symbols, performance, coverage
- **Monitor:** Set up recurring screening or dashboard generation
- **Archive:** Save watchlist state for future reference
- **Compare:** Compare current watchlist to previous versions

**Grouping criteria:**
- **By strategy:** Momentum, mean-reversion, value, growth, etc.
- **By sector:** Technology, finance, consumer, healthcare, etc.
- **By priority:** High priority (immediate action), medium (watch), low (monitor)
- **By stage:** Research (thesis development), screen (ranking), execute (ready to trade), monitor (existing positions)
- **By risk:** Low risk, medium risk, high risk
- **By liquidity:** High liquidity, medium liquidity, low liquidity

**Review cadence:**
- **Daily:** High priority symbols, active positions
- **Weekly:** Medium priority symbols, watchlist maintenance
- **Monthly:** Low priority symbols, portfolio rebalancing
- **Event-driven:** Earnings, news, technical breakouts

### Step 3: Organize watchlist structure

Define explicit watchlist structure:

**Watchlist metadata:**
- Watchlist name (e.g., "Momentum Strategy", "Tech Sector", "High Priority")
- Creation date and last update date
- Total symbols count
- Grouping scheme (strategy, sector, priority, stage, etc.)
- Review cadence (daily, weekly, monthly, event-driven)
- Intended downstream skills (market-screen, decision-dashboard, analysis, etc.)

**Symbol-level metadata:**
- Symbol and company name
- Group assignment (which group within watchlist)
- Tags (research, screen, execute, monitor, etc.)
- Priority level (high, medium, low)
- Date added to watchlist
- Last review date
- Notes (reason for inclusion, thesis summary, etc.)

**Watchlist groups:**
For each group within watchlist:
- Group name and description
- Symbol count
- Group-specific review cadence
- Group-specific downstream skills
- Group-specific risk parameters

### Step 4: Define watchlist operations

Specify available operations:

**Create watchlist:**
- Input: Imported symbols from `watchlist-import`
- Process: Organize into groups, assign tags, set review cadence
- Output: Structured watchlist with metadata
- Persistence: File-based (JSON, CSV) or host-framework storage

**Update watchlist:**
- Add symbols: Validate format, check for duplicates, assign to group
- Remove symbols: Remove from all groups, archive if needed
- Modify metadata: Update tags, priority, notes
- Regroup: Move symbols between groups

**Review watchlist:**
- Check for stale symbols (no recent review, no recent data)
- Check for delisted symbols (remove or archive)
- Check for suspended symbols (flag for monitoring)
- Check for duplicate symbols (different formats of same symbol)
- Check for performance (if tracking positions)

**Monitor watchlist:**
- Run `market-screen` on watchlist (daily, weekly, etc.)
- Run `decision-dashboard` on watchlist (daily, weekly, etc.)
- Generate alerts for significant changes (price moves, news, technical breakouts)
- Track watchlist composition changes over time

**Archive watchlist:**
- Save current state with timestamp
- Preserve grouping, tags, metadata
- Enable future comparison and retrospective analysis
- Link to analysis artifacts for provenance

### Step 5: Represent watchlist state explicitly

Even without durable local database, maintain clear state:

**Current watchlist state:**
- Which symbols are currently in scope
- How they are grouped (strategy, sector, priority, stage)
- What tags are assigned (research, screen, execute, monitor)
- What the review cadence is (daily, weekly, monthly, event-driven)
- Which downstream skills should consume each group
- When watchlist was last updated
- What changes were made since last version

**State representation options:**
- **Conversational memory:** Session-only, lost when session ends
- **File-based:** JSON or CSV file in project directory
- **Host-framework:** Persistent storage in host system
- **Hybrid:** File-based with host-framework sync

**State transparency:**
- Always state which persistence method is being used
- State whether state is durable or session-only
- State what happens to watchlist when session ends
- State how to restore watchlist in future session

### Step 6: Define downstream workflow

Connect watchlist to downstream skills:

**For research group:**
- Run `market-brief` on each symbol for quick overview
- Run `analysis` on selected symbols for full thesis development
- Run `stock-data` to build research packets
- Run `news-intel` to gather catalyst and risk context

**For screen group:**
- Run `market-screen` to rank symbols by technical strength
- Run `technical-scan` for pattern recognition
- Run `market-analyze` for detailed market state

**For execute group:**
- Run `decision-support` for position sizing
- Run `strategy-design` for execution planning
- Run `paper-trading` for simulated execution

**For monitor group:**
- Run `decision-dashboard` for daily monitoring
- Run `market-screen` for weekly ranking updates
- Run `backtest-evaluator` for retrospective performance review

### Step 7: Handle watchlist persistence

Manage persistence based on available infrastructure:

**If file-based persistence:**
- Save watchlist to JSON or CSV file
- Include all metadata (groups, tags, review cadence, etc.)
- Include timestamp and version number
- Store in project directory or user-specified location
- Provide file path for future loading

**If host-framework persistence:**
- Delegate to host-framework storage API
- Confirm successful save
- Provide watchlist ID or name for future retrieval
- State host-framework-specific limitations

**If no persistence available:**
- State that watchlist is session-only
- Recommend file-based export for durability
- Provide watchlist structure for manual recreation
- Warn that state will be lost when session ends

### Step 8: Generate watchlist management report

Organize findings into structured report:

**Part 1: Watchlist Summary**
- Watchlist name and description
- Creation date and last update date
- Total symbols count
- Grouping scheme and group counts
- Review cadence
- Persistence method (file, host, session-only)

**Part 2: Watchlist Groups**
For each group:
- Group name and description
- Symbol count
- Group-specific review cadence
- Group-specific downstream skills
- Group-specific risk parameters

**Part 3: Symbol Details**
For each symbol (or top N if large watchlist):
- Symbol, company name, board
- Group assignment
- Tags (research, screen, execute, monitor)
- Priority level (high, medium, low)
- Date added and last review date
- Notes (if any)

**Part 4: Watchlist Health**
- Stale symbols (no recent review)
- Delisted symbols (need removal)
- Suspended symbols (need monitoring)
- Duplicate symbols (need cleanup)
- Unresolved symbols (need import cleanup)

**Part 5: Review Schedule**
- Daily review symbols (high priority, active positions)
- Weekly review symbols (medium priority, watchlist maintenance)
- Monthly review symbols (low priority, portfolio rebalancing)
- Event-driven symbols (earnings, news, technical breakouts)

**Part 6: Downstream Workflow**
- Which groups feed into which skills
- Recommended next steps for each group
- Monitoring and alerting setup
- Periodic review and rebalancing plan

**Part 7: Persistence Status**
- Persistence method (file, host, session-only)
- File path or host ID (if applicable)
- Durability (durable, session-only)
- Restoration instructions (how to reload in future session)

### Step 9: Return watchlist management answer

When delivering results, maintain proper framing:

**Watchlist interpretation:**
- This is universe organization and management, not investment recommendation
- Grouping and tagging are organizational tools, not performance predictors
- Review cadence is a workflow tool, not a timing signal
- Watchlist inclusion does not imply buy recommendation

**State transparency:**
- State which symbols are in scope
- State how they are grouped and tagged
- State what the review cadence is
- State which downstream skills will consume each group
- State persistence method and durability

**Limitations disclosure:**
- **No durable local database:** State if persistence depends on file or host
- **No automatic monitoring:** State if monitoring requires manual skill invocation
- **No performance tracking:** State if P&L tracking requires `paper-trading`
- **No alerting:** State if alerts require external integration

**Workflow guidance:**
- Recommend next steps for each group
- Recommend review schedule
- Recommend downstream skills for each group
- Recommend periodic watchlist maintenance

## Output Contract

- Expected result: watchlist grouping, state summary, review plan, or explicit next-step guidance.
- Caller-facing delivery standard:
  - **Seven-part structure:** Watchlist summary, watchlist groups, symbol details, watchlist health, review schedule, downstream workflow, persistence status
  - **Symbol set identification:** Identify which symbols are being managed
  - **Grouping and tagging transparency:** State how watchlist is partitioned (research, screen, execute, monitor)
  - **Review cadence specification:** State daily/weekly/monthly/event-driven review schedule
  - **Persistence transparency:** State whether state is durable locally, host-persisted, or conversational only
  - **Downstream workflow mapping:** Identify which downstream skills each group should feed
  - **Watchlist health assessment:** Flag stale, delisted, suspended, duplicate symbols
  - **State representation:** Provide explicit current state even without durable database
  - **Limitations disclosure:** State what is NOT provided (automatic monitoring, performance tracking, alerting)
  - **No investment claims:** Watchlist organization is workflow tool, not investment recommendation
- Local limitation:
  - No guaranteed local persistent watchlist database yet
  - Grouping and tagging semantics may depend on host-framework support
  - No automatic monitoring or alerting without external integration
  - No performance tracking without `paper-trading` integration

## Failure Handling

- If there is no imported or explicit symbol set to operate on, say so directly.
- If the requested management action cannot be persisted locally yet, state that limitation instead of implying success.
- If the watchlist still contains too many unresolved or ambiguous names, route back to `watchlist-import` or manual cleanup.
- If persistence method is unavailable, offer file-based export as fallback.
- If watchlist is too large for effective management, recommend splitting into multiple watchlists.

## Key Rules

- **Keep the difference between import and management explicit.**
- **Do not imply durable watchlist storage unless it truly exists in the local execution path.**
- **Use watchlists as an explicit universe-control surface rather than a vague conversational memory shortcut.**
- **Tie the watchlist to the next research, screening, or monitoring stage intentionally.**
- **State transparency is mandatory.** Always represent current watchlist state explicitly.
- **Persistence transparency is mandatory.** State whether durable, file-based, host-persisted, or session-only.
- **Grouping must be explicit.** State grouping scheme and group assignments.
- **Review cadence must be specified.** State daily/weekly/monthly/event-driven schedule.
- **Downstream workflow must be mapped.** State which skills consume which groups.
- **Watchlist health must be assessed.** Flag stale, delisted, suspended, duplicate symbols.
- **No fake storage success.** If persistence unavailable, state limitation clearly.
- **No automatic monitoring claims.** State if monitoring requires manual skill invocation.

## Composition

- Follows `watchlist-import`.
- Often feeds `market-screen`, `decision-dashboard`, and repeated one-symbol analysis workflows.
- Research group feeds `market-brief`, `analysis`, `stock-data`, `news-intel`.
- Screen group feeds `market-screen`, `technical-scan`, `market-analyze`.
- Execute group feeds `decision-support`, `strategy-design`, `paper-trading`.
- Monitor group feeds `decision-dashboard`, periodic `market-screen`, `backtest-evaluator`.
- Should be reviewed and updated periodically to maintain watchlist health.
- Can be archived and compared over time for retrospective analysis.
