---
name: feishu-notify
description: "Push one explicit Feishu notification card. Use when a workflow needs the stage-7 communication step: outbound delivery of a status, checkpoint, or recap artifact under explicit fail-open semantics."
argument-hint: [message-text]
allowed-tools: Bash(python3 *), Read, Glob
---

# Feishu Notify

Send one outbound Feishu notification for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/feishu-notify/run.py`
- Primary purpose: provide a fail-open outbound notification surface for A-Stockit workflows
- Workflow role: communication and operator handoff, not research generation
- Local executor guarantee: attempt to send a single outbound Feishu card and report either sent or skipped status

## Use When

- The caller wants to send a manual status card.
- Another workflow needs to deliver completion or checkpoint information outward.
- A recap, alert, or artifact path needs to be surfaced to an operator channel.

## Do Not Use When

- The user wants analysis content rather than message delivery.
- The caller requires guaranteed delivery semantics, delivery receipts, or escalation logic; this skill is intentionally fail-open.
- The notification body is being used as a substitute for preserving the underlying artifact.

## Inputs

- Required `--title`.
- Optional `--event`; defaults to `custom`.
- Required message body after the options.
- Operational note:
  - the message should summarize or point to a real artifact, not replace it
  - the agent should say what the message is communicating and which workflow or artifact it came from

## Execution

### Step 1: Validate notification prerequisites

Verify notification is appropriate and ready:

**Prerequisite checks:**
- [ ] Underlying artifact exists (analysis, recap, checkpoint, alert)
- [ ] Artifact is complete and validated
- [ ] Notification purpose is clear (status, completion, alert, handoff)
- [ ] Target audience is identified (operator, team, stakeholder)
- [ ] Timing is appropriate (not redundant, not premature)

**Notification appropriateness:**
- **Appropriate:** Workflow completion, critical alerts, checkpoint status, operator handoff
- **Inappropriate:** Routine progress updates, debug messages, redundant notifications, incomplete artifacts

### Step 2: Prepare notification content

Structure notification for clarity and actionability:

**Notification components:**

**Title (required):**
- Concise summary (< 50 characters)
- Action-oriented when applicable
- Context-specific (include symbol, workflow, or event)
- Examples: "Analysis Complete: 600519", "Alert: Portfolio Risk Threshold", "Daily Recap: 2026-03-15"

**Event type (optional):**
- `analysis` - Analysis workflow completion
- `decision` - Decision support output
- `backtest` - Backtest results
- `alert` - Risk alert or threshold breach
- `recap` - Market recap or summary
- `status` - System or workflow status
- `custom` - Other notification types

**Body (required):**
- Key findings or status (2-3 sentences)
- Artifact location (file path or reference)
- Action items (if any)
- Next steps (if applicable)
- Avoid lengthy details (link to artifact instead)

**Content guidelines:**
- **Concise:** 3-5 sentences maximum
- **Actionable:** Clear next steps if action required
- **Contextual:** Include relevant identifiers (symbol, date, workflow)
- **Artifact-linked:** Reference full artifact location
- **Operator-friendly:** Use clear language, avoid jargon

### Step 3: Check notification configuration

Verify Feishu integration is configured:

**Configuration checks:**
- [ ] Feishu mode enabled in config
- [ ] Webhook URL configured
- [ ] Webhook URL is valid format
- [ ] Network connectivity available
- [ ] Rate limits not exceeded

**Configuration states:**
- **Enabled:** Mode on, webhook configured, ready to send
- **Disabled:** Mode off, notifications will be skipped
- **Misconfigured:** Mode on but webhook missing/invalid
- **Rate-limited:** Too many recent notifications

### Step 4: Run the local executor

```bash
python3 <bundle-root>/feishu-notify/run.py --title "<title>" [--event EVENT] <body>
```

### Step 5: Handle delivery outcomes

Process delivery result with fail-open semantics:

**Delivery outcomes:**

**Sent successfully:**
- Notification delivered to Feishu
- Confirmation received from webhook
- Session history updated
- Workflow continues normally

**Skipped (mode disabled):**
- Feishu mode is off in config
- Notification not attempted
- Session history notes skip
- Workflow continues normally

**Skipped (misconfigured):**
- Webhook URL missing or invalid
- Notification not attempted
- Session history notes configuration issue
- Workflow continues normally

**Skipped (transport failed):**
- Network error or webhook rejection
- Notification attempted but failed
- Session history notes failure
- Workflow continues normally (fail-open)

**Failed (parse error):**
- Invalid arguments or malformed input
- Notification not attempted
- Error message returned
- Workflow may need correction

### Step 6: Report delivery state transparently

Communicate delivery outcome clearly:

**Delivery reporting:**
- State actual outcome (sent, skipped, failed)
- State reason for skip/failure (mode, config, transport)
- State artifact location (so operator can access directly)
- State workflow continuation (fail-open semantics)

**Operator guidance:**
- If skipped due to mode: "Feishu notifications are disabled. Enable in config if needed."
- If skipped due to config: "Feishu webhook not configured. Add webhook URL to config."
- If skipped due to transport: "Feishu delivery failed. Check network and webhook URL."
- If sent: "Notification delivered. Artifact available at [path]."

### Step 7: Update session history

Record notification attempt for audit trail:

**History record:**
- Timestamp
- Notification title and event type
- Delivery outcome (sent/skipped/failed)
- Artifact reference
- Workflow context

## Output Contract

- Success case: readable text `Feishu 通知已发送。` with delivery confirmation.
- Fail-open skip case: readable text `Feishu 通知已跳过。请检查 mode/webhook 配置。` with skip reason.
- Side effects: appends a notification record to session history with timestamp, title, event, outcome, and artifact reference.
- Caller-facing delivery standard:
  - **Seven-part structure:** Prerequisite validation, content preparation, configuration check, executor run, delivery outcome handling, transparent reporting, history update
  - **Artifact identification:** State which workflow or artifact triggered the notification (analysis, recap, decision, backtest, alert, status)
  - **Delivery transparency:** Distinguish sent, skipped (mode), skipped (config), skipped (transport), failed (parse)
  - **Fail-open semantics:** Workflow continues in all non-parse cases, skip is not workflow failure
  - **Artifact preservation:** Preserve underlying artifact path or run reference outside the message
  - **Operator guidance:** Provide specific resolution steps for skip/failure cases
  - **Content guidelines:** Concise (3-5 sentences), actionable, contextual, artifact-linked, operator-friendly
  - **No blocking behavior:** Never block wider workflow on Feishu delivery

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Missing webhook or disabled mode: returns a readable skip message instead of failing the wider workflow.
- Transport errors: fail open and return the same skip-style message.

## Key Rules

- **Never block the wider workflow on Feishu delivery.**
- **Do not treat a skip as a hard runtime failure.**
- **Keep notification payloads concise and operator-readable.**
- **Use this skill for communication, not as a storage or audit surface.**
- **Prerequisite validation is mandatory.** Verify underlying artifact exists and is complete before notifying.
- **Content must be actionable.** Include key findings, artifact location, action items, next steps.
- **Delivery transparency is required.** Distinguish sent, skipped (mode/config/transport), failed (parse).
- **Fail-open semantics are non-negotiable.** Workflow continues even if notification fails.
- **Artifact preservation is critical.** Notification supplements artifact, does not replace it.
- **Configuration checks are required.** Verify mode, webhook, connectivity before attempting delivery.
- **History recording is mandatory.** Log all notification attempts for audit trail.

## Composition

- Common downstream companion for `market-brief`, `market-recap`, and other reporting workflows.
- Usable as a standalone operational utility when a human operator explicitly wants outbound delivery.
