---
name: fix-everything
description: "Autonomous error recovery and workflow continuation. Use when any skill fails, data is missing, or workflow is blocked. Agent analyzes root cause, attempts fixes, and continues workflow without user intervention. Designed for non-technical users who should not see internal errors."
argument-hint: [error-context]
allowed-tools: Bash(python3 *), Read, Glob, Grep, Edit, Write
---

# Fix Everything

Autonomous error recovery and workflow continuation for: $ARGUMENTS

## Overview

- Implementation status: workflow-orchestration
- Primary purpose: enable autonomous error recovery so non-technical users never see internal failures
- Workflow role: cross-cutting error handling and recovery across all workflow stages
- Design philosophy: closed-loop problem solving - analyze, fix, verify, continue
- User experience goal: seamless workflow execution without technical interruptions

## Use When

- Any skill execution fails with an error
- Data is missing, stale, or corrupted
- Configuration is invalid or incomplete
- Dependencies are not met
- Network or provider failures occur
- Workflow is blocked or stuck
- User should not be exposed to technical details
- Autonomous recovery is possible without user input

## Do Not Use When

- User explicitly requests to see errors for debugging
- Error requires user decision (e.g., which data source to use)
- Security or authentication issues require user credentials
- Data ambiguity requires user clarification (e.g., which symbol they meant)
- Destructive operations need user confirmation
- Error is truly unrecoverable and user must be informed

## Core Principles

### 1. Closed-Loop Recovery
- Detect error → Analyze root cause → Attempt fix → Verify success → Continue workflow
- Never stop at first failure - try multiple recovery strategies
- Log all recovery attempts for audit trail
- Only escalate to user when all recovery strategies exhausted

### 2. Graceful Degradation
- If optimal path fails, try alternative approaches
- If data source fails, try backup sources
- If full data unavailable, proceed with partial data (with status tracking)
- If skill fails, try equivalent skill or simplified approach

### 3. Transparent Logging
- Log all errors and recovery attempts internally
- Present clean, successful results to user
- Maintain audit trail for retrospective analysis
- Surface only actionable information to user

### 4. Progressive Recovery
- Start with simple fixes (retry, refresh)
- Escalate to moderate fixes (alternative sources, workarounds)
- Escalate to complex fixes (data reconstruction, workflow rerouting)
- Only fail if all strategies exhausted

## Execution

### Step 1: Error Detection and Classification

When any error occurs, immediately classify it:

**Error Categories:**

**Data Errors:**
- Missing data (symbol not found, no historical data)
- Stale data (data too old for intended use)
- Corrupted data (invalid format, parsing errors)
- Incomplete data (gaps in time series, missing fields)
- Quality issues (outliers, inconsistencies)

**Configuration Errors:**
- Missing configuration (webhook, API keys, paths)
- Invalid configuration (malformed values, wrong types)
- Conflicting configuration (incompatible settings)

**Dependency Errors:**
- Missing dependencies (Python packages, system tools)
- Version conflicts (incompatible versions)
- Path errors (files or directories not found)

**Provider Errors:**
- Network failures (timeout, connection refused)
- API failures (rate limit, authentication, service down)
- Data provider unavailable (maintenance, deprecated)

**Execution Errors:**
- Parse errors (invalid arguments, malformed input)
- Runtime errors (exceptions, crashes)
- Resource errors (out of memory, disk full)

**Workflow Errors:**
- Blocked workflow (missing prerequisites)
- Circular dependencies (skill A needs B needs A)
- State inconsistency (session state corrupted)

### Step 2: Root Cause Analysis

For each error, analyze the root cause:

**Analysis Questions:**
1. What exactly failed? (specific operation, line, component)
2. Why did it fail? (immediate cause)
3. What was the system trying to do? (intended operation)
4. What are the dependencies? (what does this depend on)
5. What are the alternatives? (other ways to achieve same goal)
6. Is this transient or persistent? (retry-able or needs fix)
7. What's the blast radius? (what else is affected)
8. Can we proceed without this? (is it critical or optional)

**Root Cause Categories:**
- **Transient:** Network glitch, temporary provider issue → Retry
- **Configuration:** Missing or invalid config → Fix config
- **Data availability:** Source doesn't have data → Try alternative source
- **Data quality:** Data exists but poor quality → Clean or filter
- **Dependency:** Missing prerequisite → Install or workaround
- **Logic:** Bug in code or workflow → Workaround or fix
- **Resource:** System resource exhausted → Clean up or optimize

### Step 3: Recovery Strategy Selection

Based on root cause, select recovery strategy:

**Strategy 1: Retry with Backoff**
- **Use for:** Transient network errors, temporary provider issues
- **Approach:** Retry 3 times with exponential backoff (1s, 2s, 4s)
- **Success criteria:** Operation succeeds on retry
- **Fallback:** If all retries fail, escalate to Strategy 2

**Strategy 2: Alternative Source**
- **Use for:** Provider unavailable, data source failure
- **Approach:** Try alternative data providers in priority order
- **Example:** akshare fails → try tushare → try local cache
- **Success criteria:** Alternative source provides data
- **Fallback:** If all sources fail, escalate to Strategy 3

**Strategy 3: Graceful Degradation**
- **Use for:** Optional data unavailable, partial failures
- **Approach:** Proceed with partial data, mark status as "partial"
- **Example:** Fundamentals unavailable → proceed with technicals only
- **Success criteria:** Workflow continues with reduced scope
- **Fallback:** If critical data missing, escalate to Strategy 4

**Strategy 4: Data Reconstruction**
- **Use for:** Missing or corrupted data that can be derived
- **Approach:** Reconstruct from other available data
- **Example:** Missing volume → estimate from price moves and liquidity
- **Success criteria:** Reconstructed data passes quality checks
- **Fallback:** If reconstruction fails, escalate to Strategy 5

**Strategy 5: Workflow Rerouting**
- **Use for:** Blocked workflow, missing prerequisites
- **Approach:** Find alternative workflow path to achieve goal
- **Example:** market-brief fails → try market-analyze + decision-support separately
- **Success criteria:** Alternative workflow produces equivalent result
- **Fallback:** If no alternative path, escalate to Strategy 6

**Strategy 6: Configuration Auto-Fix**
- **Use for:** Missing or invalid configuration
- **Approach:** Detect and fix configuration issues automatically
- **Example:** Missing webhook → disable notifications, continue workflow
- **Success criteria:** Configuration fixed, workflow continues
- **Fallback:** If config cannot be auto-fixed, escalate to Strategy 7

**Strategy 7: Dependency Auto-Install**
- **Use for:** Missing dependencies that can be installed
- **Approach:** Automatically install missing dependencies
- **Example:** Missing Python package → pip install
- **Success criteria:** Dependency installed, operation succeeds
- **Fallback:** If installation fails, escalate to Strategy 8

**Strategy 8: Simplified Approach**
- **Use for:** Complex operation fails, simpler alternative exists
- **Approach:** Use simpler method that's more likely to succeed
- **Example:** Complex pattern recognition fails → use simple trend classification
- **Success criteria:** Simplified approach produces usable result
- **Fallback:** If simplified approach fails, escalate to user

### Step 4: Execute Recovery

Execute selected recovery strategy:

**Execution Protocol:**
1. Log recovery attempt (strategy, parameters, timestamp)
2. Execute recovery operation
3. Capture result (success/failure, output, errors)
4. Verify recovery success (does it solve the problem?)
5. If successful, continue workflow
6. If failed, try next strategy
7. If all strategies exhausted, prepare user escalation

**Recovery Execution Examples:**

**Example 1: Data Provider Failure**
```
Error: akshare API timeout for symbol 600519
Root Cause: Transient network issue or provider overload
Strategy: Retry with backoff → Alternative source

Recovery Steps:
1. Retry akshare with 2s delay → Still fails
2. Try tushare as alternative → Success
3. Validate data quality → OK
4. Continue workflow with tushare data
5. Log: "Data source switched from akshare to tushare due to timeout"
```

**Example 2: Missing Fundamental Data**
```
Error: Fundamental data not available for symbol 688001
Root Cause: New STAR market stock, limited fundamental history
Strategy: Graceful degradation

Recovery Steps:
1. Mark fundamental block status as "not_supported"
2. Continue with technical analysis only
3. Add note: "Fundamental analysis limited for STAR market IPO"
4. Proceed to decision support with technical data only
5. Log: "Fundamental data unavailable, proceeded with technical-only analysis"
```

**Example 3: Configuration Missing**
```
Error: Feishu webhook URL not configured
Root Cause: User hasn't set up notifications
Strategy: Configuration auto-fix

Recovery Steps:
1. Detect missing webhook configuration
2. Disable Feishu notifications (fail-open)
3. Continue workflow without notifications
4. Log: "Feishu notifications disabled due to missing webhook"
5. Do not interrupt user workflow
```

**Example 4: Stale Data**
```
Error: Market data is 3 days old, too stale for decision support
Root Cause: Data sync hasn't run recently
Strategy: Data refresh

Recovery Steps:
1. Detect stale data (last update 3 days ago)
2. Trigger data-sync skill automatically
3. Wait for sync completion
4. Verify data freshness (now < 1 day old)
5. Continue with fresh data
6. Log: "Auto-refreshed stale data before analysis"
```

**Example 5: Workflow Blocked**
```
Error: decision-dashboard requires watchlist, but no watchlist exists
Root Cause: User hasn't created watchlist yet
Strategy: Workflow rerouting

Recovery Steps:
1. Detect missing prerequisite (watchlist)
2. Offer alternative: "Would you like to analyze a specific symbol instead?"
3. If user provides symbol, route to market-brief
4. If user wants dashboard, guide through watchlist-import first
5. Log: "Rerouted from decision-dashboard to market-brief due to missing watchlist"
```

### Step 5: Verify Recovery Success

After executing recovery, verify it actually solved the problem:

**Verification Checks:**
- [ ] Original operation now succeeds
- [ ] Data quality is acceptable (not just present but usable)
- [ ] Workflow can continue to next step
- [ ] No new errors introduced by recovery
- [ ] Result is equivalent to what would have succeeded originally

**Verification Failures:**
- If verification fails, recovery didn't actually solve the problem
- Try next recovery strategy
- If all strategies exhausted, escalate to user

### Step 6: Continue Workflow Seamlessly

Once recovery succeeds, continue workflow as if nothing happened:

**Continuation Protocol:**
1. Resume workflow at the point of failure
2. Pass recovered data/state to next step
3. Maintain workflow context and history
4. Present clean results to user
5. Log recovery details internally (not shown to user)

**User Experience:**
- User sees: "Analysis complete for 600519"
- User does NOT see: "akshare failed, retried with tushare, data quality check passed, analysis complete"
- Internal log records all recovery details for audit

### Step 7: Audit Trail and Learning

Maintain detailed audit trail for all recoveries:

**Audit Log Contents:**
- Timestamp of error and recovery
- Error type and root cause
- Recovery strategies attempted
- Recovery strategy that succeeded
- Time taken for recovery
- Impact on workflow (delay, degradation)
- Data quality after recovery

**Learning from Recoveries:**
- Track which errors occur most frequently
- Track which recovery strategies work best
- Identify patterns in failures
- Recommend proactive fixes (e.g., "akshare fails often, consider switching default to tushare")
- Update recovery strategies based on success rates

### Step 8: User Escalation (Last Resort)

Only escalate to user when all recovery strategies exhausted:

**Escalation Criteria:**
- All recovery strategies failed
- Error requires user decision or input
- Security/authentication issue needs user credentials
- Ambiguity requires user clarification
- Destructive operation needs user confirmation

**Escalation Message Format:**
```
I encountered an issue that needs your input:

[Clear description of what we're trying to do]

[What went wrong in simple terms]

[What I've already tried]

[What I need from you]

[Options you can choose from]
```

**Example Escalation:**
```
I'm trying to analyze symbol "平安银行" but I found two possible matches:

1. 000001.SZ - Ping An Bank (Shenzhen)
2. 601318.SH - Ping An Insurance (Shanghai)

Which one would you like to analyze?
```

**NOT this:**
```
Error: AmbiguousSymbolException in watchlist-import/run.py line 247
Multiple symbols matched fuzzy search query
Traceback: [stack trace]
```

## Output Contract

- **Success case:** Workflow continues seamlessly, user sees clean results
- **Partial success:** Workflow continues with degraded functionality, user sees note about limitations
- **Escalation case:** User sees clear, actionable message asking for specific input
- **Audit trail:** All recovery attempts logged internally for retrospective analysis
- **Caller-facing delivery standard:**
  - Present clean, successful results whenever possible
  - Hide internal errors and recovery details from non-technical users
  - Surface only actionable information when user input needed
  - Frame escalations as questions, not errors
  - Maintain professional tone even when things go wrong

## Failure Handling

- **Never crash or show stack traces to users**
- **Never stop workflow at first error - always try recovery**
- **Never expose technical jargon to non-technical users**
- **Always maintain audit trail even if recovery fails**
- **Always provide clear escalation message if all recovery fails**

## Key Rules

- **Closed-loop recovery is mandatory.** Never stop at first error.
- **User experience is paramount.** Non-technical users should never see internal errors.
- **Try multiple strategies.** Don't give up after first recovery attempt fails.
- **Graceful degradation is acceptable.** Partial results are better than no results.
- **Audit everything.** Log all errors and recoveries for learning.
- **Escalate clearly.** When escalation needed, ask clear questions, not show errors.
- **Maintain workflow context.** Recovery should not lose user's place in workflow.
- **Verify recovery success.** Don't assume recovery worked - verify it.
- **Learn from failures.** Track patterns and improve recovery strategies.
- **Fail-open when possible.** Optional features should not block critical workflow.

## Composition

- **Used by:** All skills when errors occur
- **Calls:** Any skill needed for recovery (data-sync, market-data, etc.)
- **Integrates with:** session-status (for state recovery), data-sync (for data refresh)
- **Logs to:** Internal audit trail (not shown to user)
- **Escalates to:** User only when all recovery strategies exhausted

## Recovery Strategy Priority Matrix

| Error Type | Strategy 1 | Strategy 2 | Strategy 3 | Escalate If |
|------------|-----------|-----------|-----------|-------------|
| Network timeout | Retry | Alt source | Cache | All sources fail |
| Missing data | Alt source | Reconstruct | Degrade | Critical data missing |
| Stale data | Refresh | Cache | Degrade | Refresh fails |
| Config missing | Auto-fix | Disable feature | Default | Security config |
| Parse error | Retry | Simplify | Skip | Invalid user input |
| Dependency missing | Install | Workaround | Degrade | Install fails |
| Provider down | Alt provider | Cache | Degrade | All providers down |
| Ambiguous input | Fuzzy match | Ask user | - | Multiple matches |

## Examples

### Example 1: Complete Autonomous Recovery

**User Request:** "Analyze 600519"

**Internal Execution:**
1. market-brief skill called
2. akshare data fetch fails (timeout)
3. fix-everything detects error
4. Retries akshare → still fails
5. Tries tushare → success
6. Validates data quality → OK
7. Continues market-brief with tushare data
8. Analysis completes successfully

**User Sees:** "Analysis complete for 600519 [clean results]"

**User Does NOT See:** Any mention of akshare failure or tushare fallback

---

### Example 2: Graceful Degradation

**User Request:** "Full analysis for 688001"

**Internal Execution:**
1. analysis skill called
2. Fundamental data fetch fails (STAR market IPO, limited history)
3. fix-everything detects error
4. Tries alternative fundamental sources → all fail
5. Marks fundamental block as "not_supported"
6. Continues with technical analysis only
7. Analysis completes with technical-only results

**User Sees:** "Analysis complete for 688001. Note: Fundamental analysis limited for recent STAR market listing. Technical analysis shows [results]."

---

### Example 3: User Escalation

**User Request:** "Analyze 平安"

**Internal Execution:**
1. watchlist-import tries to resolve "平安"
2. Finds multiple matches: 000001.SZ (Ping An Bank), 601318.SH (Ping An Insurance)
3. fix-everything detects ambiguity
4. Cannot auto-resolve (both are valid, user intent unclear)
5. Escalates to user with clear options

**User Sees:** "I found two symbols matching '平安': 1) 000001.SZ - Ping An Bank, 2) 601318.SH - Ping An Insurance. Which would you like to analyze?"

---

## Implementation Notes

This skill is a meta-skill that wraps around all other skills. It should be invoked automatically by the agent framework whenever any error occurs, without requiring explicit user invocation.

The agent should treat this skill as a safety net that ensures workflow continuity and user experience quality, especially for non-technical users who should never see internal system errors.
