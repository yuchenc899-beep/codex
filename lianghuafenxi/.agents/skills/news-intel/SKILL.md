---
name: news-intel
description: "Gather and rank symbol-relevant news intelligence from manual headlines or a local headline file. Use when user wants an explicit evidence-ingestion workflow for catalysts, risks, narrative tags, and freshness-aware headline triage."
argument-hint: [symbol]
allowed-tools: Bash(python3 *), Read, Glob, Grep
---

# News Intel

Gather ranked news intelligence for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/news-intel/run.py`
- Primary purpose: turn provided headline evidence into a ranked catalyst, risk, and narrative block for downstream research use
- Research layer: event-driven context (Stage 2: Data Collection & Quality Assurance, Stage 4: Feature Engineering & Signal Construction - Alternative data subset)
- Workflow stages: stage 2 `Data Collection & Quality Assurance` and stage 4 `Feature Engineering & Signal Construction` for event-oriented context
- Local executor guarantee: parse manual or file-backed headlines, rank them, tag catalysts and risks, and emit a compact report plus query-plan scaffolding

## Use When

- The user wants symbol-relevant catalyst and risk context.
- The caller already has headlines and wants structured ranking rather than raw browsing.
- The user wants a compact narrative block before `analysis`, `stock-data`, or `strategy-chat`.
- The user wants to understand how news events may impact technical or fundamental analysis.
- The user wants to identify potential catalysts for thesis formation or invalidation triggers.

## Do Not Use When

- The user expects this skill to crawl the web on its own. The current local executor ranks provided headlines rather than performing broad autonomous search.
- The user wants a full one-symbol report. Use `analysis` or `market-brief`.
- The user wants historical artifact review rather than fresh headline ingestion. Use `reports` or `analysis-history`.
- The user wants real-time news monitoring or alerting. This skill processes provided headlines, not live feeds.

## Inputs

- Normal case: one stock symbol.
- Optional `--headline "title | summary"` repeated multiple times.
- Optional `--headline-file PATH` for local text, JSON, or JSONL headline input.
- Optional `--company-name`, `--alias`, `--max-items`.
- If `symbol` is omitted, the skill may reuse `last_symbol` from the same execution context.
- Evidence contract:
  - headline items are caller-supplied or file-supplied evidence
  - source quality, timeliness, and completeness are not guaranteed by the local executor
  - if no headlines are provided, the skill returns a minimal query-plan-oriented scaffold rather than pretending current news coverage exists

## Execution

### Step 1: Define news intelligence requirements

Before processing headlines, clarify the intelligence needs:

**News intelligence objectives:**
- [ ] Identify potential catalysts (positive events that could drive price up)
- [ ] Identify potential risks (negative events that could drive price down)
- [ ] Extract narrative themes (market sentiment, sector trends, company positioning)
- [ ] Assess event materiality (which events are likely to impact price)
- [ ] Determine event timing (when events occurred, when they may impact price)
- [ ] Evaluate information quality (source credibility, freshness, completeness)

**Event categories to identify:**
- **Earnings and financial:** Results, guidance, analyst ratings, forecasts
- **Corporate actions:** M&A, restructuring, capital raising, dividends, buybacks
- **Regulatory and policy:** Approvals, investigations, policy changes, compliance
- **Product and business:** New products, contracts, partnerships, market expansion
- **Management and governance:** Leadership changes, strategy shifts, governance issues
- **Market and sector:** Industry trends, competitive dynamics, macro factors
- **Technical and trading:** Price moves, volume spikes, institutional activity

**A-share specific events:**
- **Regulatory:** CSRC approvals, delisting risk, ST/\*ST designation changes
- **Policy:** Industry policy changes, subsidy programs, environmental regulations
- **State ownership:** SOE reforms, state asset transfers, mixed ownership reforms
- **Capital markets:** IPO/refinancing approvals, index inclusion/exclusion, Stock Connect changes
- **Corporate governance:** Shareholder disputes, related-party transactions, pledge releases

### Step 2: Collect and validate headline evidence

Process provided headlines with quality assessment:

**Headline collection:**
- Accept manual headlines via `--headline` flag
- Accept headline file via `--headline-file` flag
- Parse headline format: "title | summary" or structured JSON/JSONL
- Extract metadata: timestamp, source, relevance score (if provided)

**Headline validation:**
- [ ] Timestamp present and parseable (if available)
- [ ] Source identified (official, media, social, user-supplied)
- [ ] Title and summary distinguishable
- [ ] Symbol relevance (mentions company name, ticker, or aliases)
- [ ] Language consistency (Chinese for A-share news)
- [ ] Duplicate detection (same event reported multiple times)

**Evidence quality assessment:**
- **Freshness:** How old is the headline?
  - Fresh: < 1 day old
  - Recent: 1-7 days old
  - Stale: > 7 days old
  - Undated: Timestamp missing (treat as low quality)
- **Source credibility:**
  - Official: Company announcements, exchange filings (highest credibility)
  - Established media: Major financial news outlets (high credibility)
  - Social media: Weibo, forums, blogs (medium credibility)
  - User-supplied: Unknown provenance (low credibility)
- **Completeness:**
  - Complete: Title, summary, timestamp, source all present
  - Partial: Missing some metadata
  - Minimal: Only title present
- **Duplication:**
  - Unique: First report of this event
  - Duplicate: Same event as another headline
  - Update: New information on previously reported event

### Step 3: Rank and categorize headlines

Apply systematic ranking and categorization:

**Relevance scoring (0-100):**
- **Direct mention (80-100):** Company name or ticker in title
- **Indirect mention (50-79):** Company in summary, or sector/industry mention
- **Tangential (20-49):** Related company, supply chain, or macro factor
- **Irrelevant (0-19):** No clear connection to symbol

**Materiality scoring (0-100):**
- **High materiality (80-100):** Likely to significantly impact price
  - Earnings surprise, major M&A, regulatory approval/rejection
  - Management change, fraud allegation, delisting risk
- **Medium materiality (50-79):** May impact price moderately
  - Analyst rating change, contract win/loss, product launch
  - Industry policy change, competitor news
- **Low materiality (20-49):** Minor impact expected
  - Routine announcements, minor partnerships, general commentary
- **Negligible (0-19):** Unlikely to impact price
  - Historical information, general industry trends

**Sentiment classification:**
- **Bullish:** Positive catalyst, likely to drive price up
- **Bearish:** Negative risk, likely to drive price down
- **Neutral:** Informational, no clear directional impact
- **Mixed:** Contains both positive and negative elements

**Event timing classification:**
- **Immediate:** Event just occurred, market may not have fully reacted
- **Recent:** Event occurred 1-7 days ago, likely already priced in
- **Historical:** Event occurred > 7 days ago, definitely priced in
- **Forward-looking:** Event expected in future (guidance, scheduled events)

**Confidence scoring (0-100):**
- **High confidence (80-100):** Official source, complete information, clear impact
- **Medium confidence (50-79):** Established media, mostly complete, probable impact
- **Low confidence (20-49):** Unverified source, incomplete information, unclear impact
- **Speculative (0-19):** Rumor, no source, highly uncertain

### Step 4: Extract catalysts and risks

Identify specific catalysts and risks from ranked headlines:

**Catalyst extraction:**
For each bullish headline with materiality > 50:
- **Catalyst type:** Earnings beat, M&A, approval, contract, etc.
- **Catalyst description:** Brief summary of the positive event
- **Expected impact:** How this could drive price up
- **Timing:** When impact may materialize
- **Confidence:** How certain is this catalyst
- **Evidence:** Which headline(s) support this catalyst

**Risk extraction:**
For each bearish headline with materiality > 50:
- **Risk type:** Earnings miss, investigation, competition, regulation, etc.
- **Risk description:** Brief summary of the negative event
- **Expected impact:** How this could drive price down
- **Timing:** When impact may materialize
- **Confidence:** How certain is this risk
- **Evidence:** Which headline(s) support this risk

**Narrative theme extraction:**
Identify recurring themes across headlines:
- **Growth narrative:** Expansion, market share gains, new products
- **Quality narrative:** Margin improvement, efficiency gains, competitive moats
- **Value narrative:** Undervaluation, asset sales, shareholder returns
- **Risk narrative:** Regulatory pressure, competition, macro headwinds
- **Sentiment narrative:** Market enthusiasm, skepticism, controversy

### Step 5: Assess evidence quality and gaps

Evaluate the overall quality of news intelligence:

**Evidence quality summary:**
- Total headlines processed
- Freshness distribution (fresh/recent/stale/undated)
- Source distribution (official/media/social/user-supplied)
- Completeness distribution (complete/partial/minimal)
- Duplication rate (% of headlines that are duplicates)

**Evidence gaps:**
- **Missing event types:** Which important event categories have no coverage?
- **One-sided coverage:** Are headlines predominantly bullish or bearish?
- **Stale information:** Is most information > 7 days old?
- **Low credibility:** Are most headlines from unverified sources?
- **Sparse coverage:** Are there too few headlines to draw conclusions?

**Quality flags:**
- [ ] **Insufficient evidence:** < 3 relevant headlines (cannot draw strong conclusions)
- [ ] **Stale evidence:** > 50% of headlines > 7 days old (may be outdated)
- [ ] **Low credibility:** > 50% of headlines from unverified sources (unreliable)
- [ ] **One-sided:** > 80% bullish or bearish (missing counterarguments)
- [ ] **Duplicate-heavy:** > 30% duplicates (less information than it appears)

### Step 6: Synthesize news intelligence report

Organize findings into structured report:

**Part 1: Intelligence Summary**
- Symbol and company name
- Total headlines processed
- Date range of headlines
- Overall sentiment (bullish/bearish/neutral/mixed)
- Evidence quality score (0-100)

**Part 2: Key Catalysts**
For each catalyst (ranked by materiality × confidence):
- Catalyst type and description
- Expected impact and timing
- Confidence level
- Supporting evidence (headline titles)

**Part 3: Key Risks**
For each risk (ranked by materiality × confidence):
- Risk type and description
- Expected impact and timing
- Confidence level
- Supporting evidence (headline titles)

**Part 4: Narrative Themes**
- Dominant narratives across headlines
- Sentiment trends (improving/deteriorating/stable)
- Market positioning (how company is perceived)
- Sector context (industry trends affecting company)

**Part 5: Ranked Headlines**
Top 10-20 headlines by relevance × materiality:
- Title and summary
- Timestamp and source
- Relevance, materiality, sentiment scores
- Confidence level

**Part 6: Evidence Quality Assessment**
- Freshness summary
- Source credibility summary
- Completeness summary
- Duplication summary
- Quality flags (if any)

**Part 7: Evidence Gaps and Limitations**
- Missing event types
- One-sided coverage concerns
- Stale information concerns
- Low credibility concerns
- Sparse coverage concerns
- Recommended additional research

**Part 8: Query Plan (Optional)**
If evidence is insufficient, suggest queries for additional research:
- Specific events to investigate
- Sources to check (exchange filings, company website, etc.)
- Time periods to focus on
- Related companies or sectors to monitor

### Step 7: Run the local executor

```bash
python3 <bundle-root>/news-intel/run.py <symbol> [--headline "标题 | 摘要"] [--headline-file PATH]
```

### Step 8: Deliver bounded intelligence block

When presenting results, maintain strict boundaries:

**Evidence provenance:**
- State that headlines are user-supplied or file-supplied evidence
- Identify source for each major catalyst or risk claim
- Distinguish official sources from media reports from speculation

**Ranking transparency:**
- Explain that scores are heuristic rankings, not truth scores
- State that relevance/materiality/confidence are model outputs, not guarantees
- Acknowledge that ranking cannot assess information not provided

**Freshness and duplication:**
- Highlight when most relevant items are stale (> 7 days old)
- Flag when multiple headlines report the same event
- Note when evidence is sparse or one-sided

**Inference boundaries:**
- Separate directly supplied evidence from derived insights
- Label narrative themes as interpretive synthesis, not facts
- Qualify catalyst/risk claims based on evidence quality

**Integration with analysis:**
- Catalysts can support thesis formation in `analysis` skill
- Risks can inform disconfirming evidence in `analysis` skill
- Narrative themes can inform variant view in `analysis` skill
- Evidence gaps should narrow claim strength in downstream memos

## Output Contract

- Minimum local executor output: human-readable text beginning with `# <symbol> News Intel`.
- Possible sections: `Catalysts`, `Risks`, `Narratives`, `Ranked Items`, and `Query Plan`.
- Side effects: updates session memory for the current execution context.
- Caller-facing delivery standard:
  - **Eight-part structure:** Intelligence summary, key catalysts, key risks, narrative themes, ranked headlines, evidence quality, evidence gaps, query plan (if needed)
  - **Evidence provenance:** Label headline basis as supplied evidence, not independently verified truth
  - **Ranking transparency:** Treat confidence and relevance scores as heuristic ranking outputs, not completeness or truth scores
  - **Freshness disclosure:** Surface freshness and duplication profile when it materially affects conclusions
  - **Quality assessment:** Provide evidence quality score and flag quality concerns
  - **Inference boundaries:** Separate supplied evidence, ranking output, and narrative interpretation
  - **Narrow claims when evidence is thin:** If evidence is sparse, stale, or one-sided, qualify conclusions accordingly
  - **Integration guidance:** Explain how catalysts/risks feed into thesis formation, disconfirming evidence, and invalidation triggers
  - **No fabricated certainty:** Incomplete evidence should degrade conclusion strength, not be hidden
- Non-guarantees:
  - No web crawling guarantee (processes provided headlines only)
  - No durable report artifact unless another skill persists the result
  - No real-time monitoring or alerting capability

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- Missing or unreadable headline files: readable `执行失败:` text.
- Missing headlines: returns a reduced report with query plan suggestions.
- If evidence is incomplete, that should degrade the conclusion rather than cause fabricated certainty.
- Malformed headline format: skip malformed entries and report count of skipped items.
- Duplicate detection failures: proceed with ranking but flag potential duplication issues.

## Key Rules

- **Distinguish provided evidence from inferred narrative.**
- **Treat ranking as deterministic scoring over supplied items, not as a guarantee of external completeness.**
- **Prefer concise, source-labeled headline payloads over noisy dumps.**
- **When this skill feeds `analysis`, preserve provenance for each major catalyst or risk claim.**
- **Evidence quality assessment is mandatory.** Always evaluate freshness, source credibility, completeness, duplication.
- **Quality flags must be surfaced.** If evidence is insufficient, stale, low-credibility, one-sided, or duplicate-heavy, state it explicitly.
- **Confidence scores must reflect evidence quality.** Low-quality evidence = low confidence, regardless of headline content.
- **Narrative themes are interpretive synthesis.** Label them as such, not as facts.
- **Catalyst and risk claims must be qualified.** State expected impact, timing, and confidence level.
- **Evidence gaps must be acknowledged.** Missing event types, one-sided coverage, sparse information.
- **Integration with downstream skills must be explicit.** How do catalysts/risks inform thesis, disconfirming evidence, invalidation?
- **No web crawling or autonomous search.** This skill processes provided headlines only.

## Composition

- Often feeds `analysis`, `stock-data`, or `strategy-chat`.
- Shares research helpers with the broader packet-building logic, but it is not a substitute for full research verification.
- Catalysts feed into thesis formation and key drivers in `analysis` skill.
- Risks feed into disconfirming evidence and invalidation conditions in `analysis` skill.
- Narrative themes feed into variant view and market positioning in `analysis` skill.
- Evidence gaps inform evidence sufficiency assessment in `analysis` skill.
- Can be combined with `fundamental-context` for comprehensive non-price context.
- Should be rerun when new material events occur to update catalyst/risk assessment.
