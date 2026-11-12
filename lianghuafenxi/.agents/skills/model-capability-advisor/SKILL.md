---
name: model-capability-advisor
description: "Recommend fast/deep model pairings for a workflow. Use when user wants meta-workflow guidance on which model profiles fit analysis, chat, batch, backtest, or paper-trading tasks, while staying explicit that the advice is heuristic and local."
argument-hint: [workflow-or-model]
allowed-tools: Bash(python3 *), Read, Glob, Grep
---

# Model Capability Advisor

Recommend model capability choices for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/model-capability-advisor/run.py`
- Primary purpose: score provided model names against workflow needs and return quick/deep recommendation pairs
- Research layer: meta-workflow optimization (Cross-cutting concern for agent execution design)
- Workflow role: meta-planning support for agent execution design, not a market-analysis surface
- Local executor guarantee: produce heuristic workflow-fit advice from the local capability profiles it knows about

## Use When

- The user asks which model names fit a workflow.
- The caller wants quick/deep pairing advice for `analysis`, `chat`, `batch`, `backtest`, or `paper`.
- The user wants warnings about likely model tradeoffs before assigning a workflow.
- The user wants to optimize agent execution for speed vs. depth.
- The user wants to understand model capability differences for quantitative workflows.

## Do Not Use When

- The caller needs verification that a provider is actually configured or reachable.
- The user expects benchmark-backed precision or live provider comparison; this skill is heuristic and local.
- The question is about investment analysis rather than agent execution design.
- The user wants actual performance benchmarks rather than capability profiles.

## Inputs

- Optional positional `target`.
- Optional `--workflow`; defaults to `analysis`.
- Optional repeatable `--quick MODEL`.
- Optional repeatable `--deep MODEL`.
- Scope note:
  - the local advisor reasons over known capability profiles and workflow heuristics
  - the agent should say when a recommendation is only based on naming heuristics or incomplete local profiles

## Execution

### Step 1: Define workflow requirements

Identify specific needs for the target workflow:

**Workflow types and requirements:**

**Analysis workflow:**
- **Speed priority:** Fast iteration for exploratory analysis
- **Depth priority:** Deep reasoning for thesis development
- **Key capabilities:** Long context, structured output, evidence synthesis
- **Typical use:** `analysis`, `market-brief`, `stock-data`

**Chat workflow:**
- **Speed priority:** Low latency for interactive conversation
- **Depth priority:** Contextual understanding for multi-turn dialogue
- **Key capabilities:** Context retention, clarification, follow-up
- **Typical use:** `strategy-chat`, interactive Q&A

**Batch workflow:**
- **Speed priority:** High throughput for screening many symbols
- **Depth priority:** Consistent quality across batch
- **Key capabilities:** Parallel processing, cost efficiency
- **Typical use:** `market-screen`, `decision-dashboard`, `watchlist-import`

**Backtest workflow:**
- **Speed priority:** Fast iteration for parameter tuning
- **Depth priority:** Rigorous evaluation for validation
- **Key capabilities:** Numerical reasoning, statistical analysis
- **Typical use:** `backtest-evaluator`, performance analysis

**Paper trading workflow:**
- **Speed priority:** Real-time decision making
- **Depth priority:** Risk assessment and validation
- **Key capabilities:** Numerical precision, rule adherence
- **Typical use:** `paper-trading`, `strategy-design`, `decision-support`

### Step 2: Define model capability profiles

Establish capability dimensions for model evaluation:

**Capability dimensions:**

**Speed:**
- Tokens per second (throughput)
- Time to first token (latency)
- Total response time
- Cost per token

**Reasoning depth:**
- Complex problem solving
- Multi-step reasoning
- Abstract thinking
- Nuanced judgment

**Context handling:**
- Maximum context window
- Context retention quality
- Long-range dependency handling
- Context compression efficiency

**Structured output:**
- JSON/XML generation quality
- Table formatting
- Numerical precision
- Consistency across outputs

**Tool use:**
- Function calling reliability
- Parameter extraction accuracy
- Error handling
- Multi-tool orchestration

**Domain knowledge:**
- Financial domain understanding
- Quantitative reasoning
- Statistical analysis
- A-share market specifics

### Step 3: Score candidate models

Evaluate available models against workflow requirements:

**Model scoring methodology:**

For each model, score (0-100) on each dimension:
- **Speed:** Based on known throughput and latency
- **Reasoning:** Based on benchmark performance and complexity handling
- **Context:** Based on window size and retention quality
- **Structure:** Based on output formatting reliability
- **Tools:** Based on function calling accuracy
- **Domain:** Based on financial knowledge demonstrations

**Workflow-specific weighting:**

**Analysis workflow weights:**
- Reasoning: 40%
- Context: 25%
- Structure: 15%
- Domain: 15%
- Speed: 5%

**Chat workflow weights:**
- Speed: 35%
- Context: 30%
- Reasoning: 20%
- Structure: 10%
- Tools: 5%

**Batch workflow weights:**
- Speed: 50%
- Structure: 20%
- Tools: 15%
- Reasoning: 10%
- Context: 5%

**Backtest workflow weights:**
- Reasoning: 35%
- Structure: 30%
- Domain: 20%
- Speed: 10%
- Context: 5%

**Paper trading workflow weights:**
- Reasoning: 30%
- Tools: 25%
- Structure: 25%
- Speed: 15%
- Domain: 5%

**Composite score calculation:**
- Weighted sum of dimension scores
- Normalize to 0-100 scale
- Rank models by composite score

### Step 4: Generate quick/deep recommendations

Select optimal model pairing:

**Quick model selection:**
- Prioritize speed and cost efficiency
- Acceptable reasoning depth for routine tasks
- Good enough for screening, monitoring, batch operations
- Typical candidates: Gemini Flash, Claude Haiku, GPT-3.5

**Deep model selection:**
- Prioritize reasoning depth and accuracy
- Acceptable speed for critical decisions
- Required for thesis development, risk assessment, validation
- Typical candidates: Claude Opus, GPT-4, Gemini Pro

**Pairing strategy:**
- Use quick model for initial screening and routine tasks
- Escalate to deep model for critical decisions and complex analysis
- Balance cost vs. quality based on workflow stage
- Consider fallback options if primary unavailable

**Escalation triggers:**
- High uncertainty in quick model output
- Critical decision point (large position, high risk)
- Complex reasoning required (multi-factor analysis)
- Validation needed (cross-check quick model)
- User explicitly requests deeper analysis

### Step 5: Identify model tradeoffs

Highlight important considerations:

**Speed vs. depth tradeoffs:**
- Quick models: 5-10× faster but may miss nuances
- Deep models: More thorough but higher latency and cost
- Batch operations: Speed matters more than individual quality
- Critical decisions: Depth matters more than speed

**Context window tradeoffs:**
- Large context: Can process more data but slower and costier
- Small context: Faster and cheaper but may miss connections
- Long documents: Require large context models
- Iterative workflows: Can use smaller context with state management

**Cost tradeoffs:**
- Quick models: $0.001-0.01 per 1K tokens
- Deep models: $0.01-0.10 per 1K tokens
- Batch operations: Cost scales linearly with volume
- Critical decisions: Cost is secondary to quality

**Reliability tradeoffs:**
- Established models: More reliable but may be slower or costlier
- Newer models: Faster and cheaper but less proven
- Tool use: Some models better at function calling
- Structured output: Some models better at JSON/table generation

### Step 6: Generate capability advice report

Organize findings into structured report:

**Part 1: Workflow Requirements**
- Target workflow type
- Speed vs. depth priority
- Key capability requirements
- Typical use cases

**Part 2: Quick Model Recommendation**
- Recommended model name
- Composite score for workflow
- Dimension scores (speed, reasoning, context, etc.)
- Strengths for this workflow
- Limitations to be aware of

**Part 3: Deep Model Recommendation**
- Recommended model name
- Composite score for workflow
- Dimension scores
- Strengths for this workflow
- Limitations to be aware of

**Part 4: Pairing Rationale**
- Why this quick/deep pairing
- When to use quick vs. deep
- Escalation triggers
- Cost/quality tradeoff

**Part 5: Alternative Candidates**
- Other viable quick models (with scores)
- Other viable deep models (with scores)
- Fallback options if primary unavailable
- Experimental models to consider

**Part 6: Model Tradeoffs**
- Speed vs. depth considerations
- Context window considerations
- Cost considerations
- Reliability considerations

**Part 7: Important Unknowns**
- Provider availability (not verified)
- Actual latency in host environment (not measured)
- Tool-call reliability (not tested)
- Cost in production (estimates only)
- Model updates (profiles may be outdated)

**Part 8: Recommendations**
- Use quick model for: [specific tasks]
- Use deep model for: [specific tasks]
- Monitor performance and adjust
- Consider benchmarking in production

### Step 7: Run the local executor

```bash
python3 <bundle-root>/model-capability-advisor/run.py --workflow analysis --quick gemini-flash --deep claude-sonnet
```

### Step 8: Deliver as heuristic planning support

When delivering results, maintain proper framing:

**Advice interpretation:**
- This is heuristic workflow-fit advice, not empirical benchmarking
- Scores are based on known capability profiles, not production testing
- Recommendations assume typical use cases, not specific edge cases
- Actual performance may vary based on host environment

**Verification needed:**
- Provider availability (is model actually configured?)
- Actual latency (measure in production environment)
- Tool-call reliability (test with actual workflows)
- Cost in production (monitor actual usage)
- Model updates (check for newer versions)

**Limitation disclosure:**
- Profiles may be outdated (models update frequently)
- Heuristics may not match specific use case
- No guarantee of availability or performance
- Recommendations are starting point, not final answer
- Empirical testing recommended for high-stakes workflows

## Output Contract

- Success format: readable text beginning with `# Model Capability Advice (<workflow>)`.
- Sections: selected quick model, selected deep model, rationale, optional warnings, and candidate profiles.
- Caller-facing delivery standard:
  - **Eight-part structure:** Workflow requirements, quick model recommendation, deep model recommendation, pairing rationale, alternative candidates, model tradeoffs, important unknowns, recommendations
  - **Heuristic framing:** Label result as workflow-fit advice, not empirical benchmarking
  - **Scoring transparency:** Provide dimension scores and composite scores for each model
  - **Pairing rationale:** Explain why this quick/deep pairing and when to use each
  - **Tradeoff disclosure:** Speed vs. depth, context, cost, reliability considerations
  - **Unknown identification:** Provider availability, actual latency, tool reliability not verified
  - **Verification guidance:** State what needs to be verified in production
  - **No authoritative claims:** Avoid implying recommended model is installed, configured, or benchmark-dominant unless verified

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Missing candidates do not cause failure; the output degrades into workflow-level guidance.
- Unknown workflow type: provide general guidance and suggest closest known workflow.
- No models provided: recommend based on typical model profiles for workflow.
- Conflicting requirements: highlight tradeoffs and recommend multiple options.

## Key Rules

- **Keep this skill advisory rather than authoritative.**
- **Do not imply that a recommended model is installed or configured unless separately verified.**
- **Use it to improve workflow design, not to replace empirical benchmarking when high-stakes performance matters.**
- **Scoring must be transparent.** Provide dimension scores and weighting methodology.
- **Tradeoffs must be explicit.** Speed vs. depth, cost vs. quality, etc.
- **Unknowns must be identified.** Provider availability, actual latency, tool reliability.
- **Verification must be recommended.** State what needs testing in production.
- **Profiles may be outdated.** Acknowledge that models update frequently.
- **Heuristic framing is mandatory.** This is planning support, not empirical truth.

## Composition

- Often used before `analysis`, `strategy-chat`, `backtest-evaluator`, or `paper-trading`.
- Works as a planning helper rather than a market-analysis skill.
- Can inform agent execution design across all workflow stages.
- Should be rerun when new models become available or requirements change.
- Results can inform cost optimization and performance tuning.
