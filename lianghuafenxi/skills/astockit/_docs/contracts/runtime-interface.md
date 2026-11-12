# Bundle Interface Contract

This document defines the execution boundary for the A-Stockit bundle.

## Invocation Modes

A-Stockit supports two skill modes.

### Code-Backed Skill

Use the local `run.py` beside that skill.

Properties:

- executable locally through `python3`
- returns readable terminal text
- may write runtime artifacts
- may update session history
- may still require broader agent-composed workflow steps beyond the script itself

### Workflow-Only Skill

Use the skill contract plus other bundle skills, docs, and `_src` helpers as the current backing path.

Properties:

- describes a valid workflow surface
- does not imply a dedicated local executor exists yet
- must state what currently backs it
- must state what it does not guarantee locally

## Result Semantics

Code-backed skills should behave as follows:

- Success: exit code `0`, readable output, status indicator (`ok`, `partial`, `stale`)
- Parse or argument error: non-zero exit, readable `命令错误` message
- Runtime or data failure: non-zero exit or readable `执行失败:` output with status indicator (`error`), but never an unexplained traceback as the public contract
- Partial success: exit code `0`, readable output with degradation notice, status indicator (`partial`)

Workflow-only skills should behave as follows:

- return a concrete workflow answer or next-step plan
- say explicitly when local automation is missing
- avoid implying a durable artifact or executor that does not exist
- include status indicators when relevant

## Status Tracking Model

Skills should return structured status indicators:

**Status Values:**
- `ok` - Full success, all data available, no degradation
- `partial` - Partial success, some data missing but workflow can continue
- `not_supported` - Feature not available for this context (e.g., US-only feature for CN symbol)
- `stale` - Data available but outdated (beyond freshness threshold)
- `error` - Failure requiring recovery or escalation

**Status Reporting:**
- Code-backed skills should include status in output or metadata
- Workflow-only skills should communicate status through structured responses
- Callers should surface status to users when it affects interpretation
- `partial` and `stale` statuses should specify what degraded

**Status Usage:**
- Status indicators guide error recovery strategies
- `partial` and `stale` allow workflow continuation with degraded data
- `not_supported` prevents inappropriate skill invocation
- `error` triggers fix-everything meta-skill invocation

## Local Guarantee Boundary

For code-backed skills, the contract should distinguish:

- what the local executor guarantees on its own
- what the agent should do around the executor to satisfy the full workflow
- what still depends on host-framework support or external systems

This keeps bundle contracts operationally rich without overstating local automation.

## Artifact Lifecycle

When a skill writes artifacts, the contract should make that explicit.

Rules:

- persisted artifacts live under the configured runtime root
- a skill should name the artifact types it creates, for example `report.md` and `state.json`
- downstream skills should prefer existing artifacts over regenerating them
- history-oriented skills should identify which saved artifact they used
- when available, callers should also surface `metadata.json`, generating command, and generation time

## Evidence And Confidence

Callers should keep evidence provenance explicit.

Rules:

- distinguish fresh computation from reused artifact content
- distinguish optional fail-open enrichments from core local output
- distinguish user-supplied assumptions from local defaults or inferred context
- if a skill exposes `score` or `confidence`, say whether it is heuristic, ordinal, or validated
- do not present heuristic confidence as probability unless the bundle validates that claim
- if a result depends on caller-supplied or external-file evidence, label that evidence basis explicitly

## Session Context Reuse

The bundle allows bounded reuse of session context.

Rules:

- code-backed skills may reuse the last symbol in the current execution context
- this reuse must be documented in the skill’s `Inputs` or `Failure Handling`
- if context is missing or ambiguous, the skill should say so instead of silently guessing
- workflow-only skills should say when they rely on host-framework conversation state
- if a symbol is reused rather than explicitly supplied, the caller should say so in the response when it matters

## Fail-Open Policy

Some bundle features are intentionally fail-open.

Current fail-open areas:

- outbound notification delivery
- optional fundamental enrichment
- optional headline/news enrichment when the core analysis path can still proceed

Rules:

- fail-open means the main workflow still returns a usable result
- fail-open does not mean failures are hidden; they should be surfaced as status, warnings, or degraded blocks
- a skill should not claim a complete context block when the block is partial or unavailable

## Error Recovery

The bundle integrates with the `fix-everything` meta-skill for autonomous error recovery.

**Recovery Contract:**
- All skill failures automatically invoke `fix-everything`
- Progressive recovery strategies: retry, alternative source, graceful degradation, data reconstruction, workflow rerouting, config auto-fix, dependency auto-install, simplified approach
- Recovery attempts are transparent but not exposed to non-technical users
- Users only see clean results or clear escalation questions

**Skill Requirements:**

For code-backed skills:
- Raise structured exceptions with recovery hints
- Return partial results with status indicators when possible
- Document which errors are recoverable vs. terminal
- Include error context for recovery analysis

For workflow-only skills:
- Specify graceful degradation paths
- Document expected failure modes
- Indicate which components are fail-open vs. fail-closed
- Provide clear escalation criteria

**Recovery Semantics:**
- Closed-loop recovery: detect → analyze → fix → verify → continue
- Fail-open for optional features (notifications, enrichments)
- Fail-closed for critical workflow components (data access, core analysis)
- User escalation only when all recovery strategies exhausted

**Integration:**
- fix-everything automatically invoked on skill failures
- Recovery strategies selected based on error type and context
- Status indicators guide recovery approach (partial/stale allow continuation, error triggers recovery)
- Workflow state preserved through recovery attempts

## Code-Backed Skill Contract Requirements

Every code-backed `SKILL.md` should document:

- implementation status
- local entry script
- `Use When`
- `Do Not Use When`
- required and optional inputs
- output format and side effects
- failure behavior
- composition with neighboring skills
- any assumptions or defaults that materially affect action, sizing, or planning output
- realism limits for action, execution, or retrospective evaluation workflows
- the difference between local executor guarantees and agent-required process steps when the workflow is broader than the script

## Workflow-Only Skill Contract Requirements

Every workflow-only `SKILL.md` should document:

- implementation status as workflow-only
- current backing path
- inputs and current execution path
- output expectations
- local limitations
- composition with neighboring skills
- what is actually automated locally versus what the host framework must compose or clarify

## Retrospective Evaluation Guardrails

When a workflow evaluates prior output or runs a simulation:

- disclose the evaluation assumptions explicitly
- identify the evaluated saved state or artifact directory
- state which realism layers are not modeled locally
- avoid presenting retrospective verdicts as proof of predictive edge

## Source Of Truth

- public skill metadata: `_registry/skills.json`
- bundle metadata: `_registry/bundle.json`
- bundle design and routing model: `index.md`
- skill-level operational contract: `<skill>/SKILL.md`
