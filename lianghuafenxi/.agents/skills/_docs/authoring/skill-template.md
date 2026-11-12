# Skill Template

A-Stockit standardizes every public skill definition around the same schema.

## Frontmatter

Use exactly these four fields:

```md
---
name: skill-name
description: "One-line purpose. Use when user says ..."
argument-hint: [primary-input]
allowed-tools: Bash(python3 *), Read, Glob
---
```

## Required Body Structure

Code-backed skills should use this section order:

```md
# Human Readable Skill Title

One-line summary for: $ARGUMENTS

## Overview

## Use When

## Do Not Use When

## Inputs

## Execution
### Step 1: ...
### Step 2: ...

## Output Contract

## Failure Handling

## Error Recovery

## Key Rules

## Composition
```

Workflow-only skills should keep the same section order, but:

- `## Overview` must say `implementation status: workflow-only`
- `## Execution` must describe the current composition path rather than a local script
- `## Output Contract` must say what is and is not guaranteed locally
- `## Failure Handling` must explain how the host framework should respond when local automation is missing
- `## Error Recovery` must specify graceful degradation paths

Code-backed skills may define a broader end-to-end workflow than the local script automates, but they must:

- say what the local executor actually guarantees
- say what additional agent reasoning or process steps are expected
- say what remains host-dependent or unguaranteed

## Contract Notes

- Keep a single `#` heading per file.
- Put implementation status in `## Overview`.
- `## Use When` should distinguish the skill from neighboring skills.
- `## Do Not Use When` should prevent routing ambiguity.
- `## Inputs` should distinguish explicit user inputs from defaults or reused session context when those defaults materially change the answer.
- `## Output Contract` should describe output format, important fields, side effects such as artifact creation, and whether the result is fresh computation, reused artifact content, or workflow-only synthesis. Should include status indicators (ok/partial/not_supported/stale/error).
- For code-backed skills, `## Output Contract` should separate local executor guarantees from broader agent-composed workflow obligations when they differ.
- `## Failure Handling` should distinguish parse errors from runtime/data errors, and specify integration with `fix-everything` meta-skill.
- `## Error Recovery` should document integration with autonomous recovery system, specify which errors are recoverable vs. terminal, and describe graceful degradation paths.
- `## Composition` should say which skills this one feeds into or depends on.
- Workflow-only skills should explicitly say what currently backs them and what they do not guarantee locally.

## Error Recovery Section

All skills should include an `## Error Recovery` section documenting integration with the `fix-everything` meta-skill:

**For code-backed skills:**
```md
## Error Recovery

**Integration with fix-everything:**
- Raises structured exceptions with recovery hints
- Returns partial results with status indicators when possible
- Documents which errors are recoverable vs. terminal

**Recoverable Errors:**
- [List specific error types that can be recovered]
- [Recovery strategy for each: retry, alternative source, graceful degradation, etc.]

**Terminal Errors:**
- [List errors requiring user escalation]
- [Clear escalation guidance for each]

**Status Indicators:**
- `ok` - Full success
- `partial` - [What partial means for this skill]
- `stale` - [What stale means for this skill]
- `error` - [What triggers error status]
```

**For workflow-only skills:**
```md
## Error Recovery

**Graceful Degradation:**
- [Describe how skill degrades when components fail]
- [What functionality remains available]

**Fail-Open Components:**
- [List optional features that don't block workflow]

**Fail-Closed Components:**
- [List critical features that require escalation on failure]

**Escalation Criteria:**
- [When to escalate to user]
- [What information to provide]
```

## Contract Notes

Public skill contracts should be explicit about analytical discipline, not just execution syntax.

- If the skill claims analytical depth, require thesis framing, major drivers, variant views, disconfirming evidence, and invalidation or monitoring conditions whenever the available evidence supports them.
- If the skill handles action or sizing, state the account assumptions clearly and separate descriptive analysis from decision support.
- If the skill handles execution planning, separate execution mechanics from the question of whether the position should exist at all.
- If the skill exposes `score` or `confidence`, state whether it is heuristic, ordinal, or validated. Never imply probability without validated evidence.
- If optional enrichments fail open, say what degraded and what still remains trustworthy.
- If the skill reuses artifacts, name the artifact types and provenance fields the caller should surface.
- If the skill performs retrospective evaluation, disclose the evaluation assumptions and the realism limits that are not modeled locally.
- If the skill covers a workflow stage larger than the local script, document the stage clearly and keep the automation boundary honest.

## Suggested `## Output Contract` Checklist

When relevant, use this checklist inside `## Output Contract`:

- minimum local executor output or workflow-only deliverable
- caller-facing delivery standard
- status indicators (ok/partial/not_supported/stale/error)
- artifact side effects and provenance disclosures
- explicit uncertainty, stale-data, or partial-evidence disclosures
- non-modeled risks or realism limits
