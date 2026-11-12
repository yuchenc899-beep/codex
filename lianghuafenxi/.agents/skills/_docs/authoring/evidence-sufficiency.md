# Evidence Sufficiency Guidance

This document defines when available evidence supports thesis-level claims versus when it only supports descriptive observations.

## Purpose

This guidance helps agents and analysts determine:
- When to route to `analysis` (thesis-level) vs. `market-brief` (descriptive synthesis)
- When to narrow claims within `analysis` due to evidence gaps
- How to handle evidence-thin scenarios honestly

## Evidence Levels

### Level 1: Minimal Evidence (Descriptive Only)

**What you have:**
- Basic price and volume data (< 60 days of history)
- Current technical indicators (MA, RSI, etc.)
- No fundamental context
- No identifiable catalysts
- No sector or benchmark comparison

**What you can claim:**
- Current technical state (trend, support/resistance, regime)
- Recent price behavior description
- Basic pattern observations

**What you cannot claim:**
- Thesis statements about why the move is happening
- Key drivers (insufficient context to identify drivers)
- Variant views (insufficient evidence to frame alternatives)
- Invalidation conditions beyond simple technical levels

**Routing decision:** Use `market-brief` for descriptive synthesis. Do not route to `analysis`.

**If forced to use `analysis`:** Explicitly state in each mandatory section: "Evidence insufficient to support [thesis statement / key drivers / variant view]. Analysis limited to technical description."

### Level 2: Moderate Evidence (Conditional Thesis)

**What you have:**
- Sufficient price history (60+ days) to identify trend structure and regime
- Technical indicators with context
- Observable technical drivers (e.g., breakout, MA alignment, volume surge)
- Basic sector or benchmark comparison
- Limited or no fundamental context
- No clear catalyst

**What you can claim:**
- Technical thesis statements (e.g., "positioned for trend continuation based on technical structure")
- Technical key drivers (3-5 specific technical factors)
- Technical variant views (alternative technical interpretations)
- Technical invalidation conditions (price levels, technical breakdowns)

**What you cannot claim:**
- Fundamental drivers without fundamental data
- Catalyst-dependent thesis without identifiable catalyst
- Conviction about sustainability without fundamental support

**Routing decision:** Can use `analysis` but must acknowledge evidence limits.

**Thesis framing example:**
- **Acceptable:** "Technical thesis: 600519 positioned for trend continuation based on institutional accumulation pattern and sector relative strength"
- **Not acceptable:** "600519 is a strong buy based on improving fundamentals" (no fundamental evidence)

**Mandatory acknowledgments:**
- Thesis statement: "Technical thesis based on price and volume evidence; fundamental drivers not assessed"
- Primary catalyst: "No identifiable near-term catalyst; thesis depends on continuation of current technical structure"
- Evidence gaps: "No visibility into fundamental drivers, earnings trajectory, or regulatory developments"

### Level 3: Strong Evidence (Full Thesis)

**What you have:**
- Comprehensive price history (90+ days)
- Technical indicators with full context
- Observable technical drivers
- Fundamental context (earnings, margins, growth, sector position)
- Identifiable catalyst or catalyst window
- Sector and benchmark comparison
- Optional: news context, institutional flow data

**What you can claim:**
- Full thesis statements combining technical and fundamental factors
- Comprehensive key drivers (technical + fundamental)
- Rich variant views incorporating multiple perspectives
- Specific invalidation conditions (technical, fundamental, and catalyst-based)

**Routing decision:** Use `analysis` with full thesis structure.

**Thesis framing example:**
- **Full thesis:** "600519 positioned for trend continuation driven by: (1) institutional accumulation pattern, (2) sector rotation tailwinds, (3) margin expansion visible in Q3 results, (4) upcoming policy catalyst in Q1 2026"

## Evidence Sufficiency Checklist

Before claiming thesis-level analysis, verify:

### For Thesis Statement:
- [ ] Can you articulate a specific, falsifiable view?
- [ ] Is the view grounded in observable evidence (not speculation)?
- [ ] Can you identify what would prove the thesis wrong?

### For Key Drivers:
- [ ] Can you name 3-5 specific, observable factors?
- [ ] Are these factors monitorable going forward?
- [ ] Can you rank them by importance?

### For Primary Catalyst:
- [ ] Can you identify a specific near-term event or condition?
- [ ] Does the catalyst have observable timing or trigger conditions?
- [ ] If no catalyst exists, can you acknowledge that explicitly?

### For Variant View:
- [ ] Can you articulate an intellectually honest alternative interpretation?
- [ ] Is the alternative grounded in the same evidence (not a strawman)?
- [ ] Would a reasonable investor find the alternative plausible?

### For Disconfirming Evidence:
- [ ] Can you identify specific observations that weaken the thesis?
- [ ] Is the disconfirming evidence current and material?
- [ ] Are you being honest about evidence that contradicts your view?

### For Invalidation Conditions:
- [ ] Can you specify observable conditions that would falsify the thesis?
- [ ] Are the conditions monitorable in real-time or near-real-time?
- [ ] Do you have both price-based and non-price-based conditions?

## Handling Evidence Gaps

### When Evidence is Insufficient:

**Option 1: Route to `market-brief`**
- Use when user wants current positioning quickly
- Acknowledge: "This is descriptive synthesis without thesis-level claims"
- Recommend: "For deeper analysis including drivers and invalidation logic, use the analysis skill"

**Option 2: Proceed with `analysis` but narrow claims**
- Use when user explicitly requests `analysis` despite thin evidence
- In each mandatory section, state the evidence gap explicitly
- Example thesis statement: "Technical thesis only: [statement]. Fundamental drivers not assessed due to limited data."
- Example key drivers: "Technical drivers identified: [list]. Fundamental drivers cannot be assessed with available evidence."
- Example variant view: "Alternative technical interpretation: [view]. Fundamental alternatives cannot be framed without fundamental data."

### Never Do This:
- ❌ Pad evidence-thin sections with generic narrative
- ❌ Fabricate conviction to fill mandatory sections
- ❌ Pretend fundamental drivers exist when you only have technical data
- ❌ Create strawman variant views just to fill the section
- ❌ Use vague invalidation conditions like "if the market changes"

## Evidence Staleness

Evidence can become stale even if it was once sufficient:

**Staleness triggers:**
- Price data more than 5 trading days old for short-term positioning
- Fundamental data more than 1 quarter old
- Pre-dates material events (earnings, news, regime change)
- Regime has shifted since evidence was gathered

**Staleness handling:**
- State the evidence date explicitly
- Acknowledge staleness: "Analysis based on data through [date]; recommend refresh for current positioning"
- If staleness is material, recommend regeneration rather than reusing stale artifacts

## Examples

### Example 1: Insufficient Evidence

**Scenario:** User asks for analysis of 600519, but only 30 days of price data available, no fundamental context.

**Correct response:**
"Evidence insufficient for thesis-level analysis. Available data supports descriptive technical synthesis only. Recommend using `market-brief` for current state description, or gathering additional data (60+ days history, fundamental context) before attempting thesis-level analysis."

**If user insists on `analysis`:**
Proceed but state in each section:
- Thesis statement: "Evidence insufficient to support thesis statement. Analysis limited to technical description."
- Key drivers: "Evidence insufficient to identify key drivers. Observable technical factors: [list]."
- Variant view: "Evidence insufficient to frame variant view."

### Example 2: Moderate Evidence (Technical Only)

**Scenario:** User asks for analysis of 600519, 90 days of price data available, clear technical structure, no fundamental context.

**Correct response:**
Proceed with `analysis` using technical thesis structure:
- Thesis statement: "Technical thesis: 600519 positioned for trend continuation based on institutional accumulation pattern and sector relative strength. Fundamental drivers not assessed."
- Key drivers: "1) Net institutional inflow pattern over 10 sessions, 2) Sector relative strength vs. benchmark, 3) Technical breakout above 200-day resistance"
- Primary catalyst: "No identifiable near-term catalyst; thesis depends on continuation of current technical structure"
- Variant view: "Alternative technical interpretation: current strength reflects late-cycle momentum exhaustion rather than institutional accumulation; volume profile suggests retail participation"
- Evidence gaps: "No visibility into fundamental drivers, earnings trajectory, margin trends, or regulatory developments"

### Example 3: Strong Evidence

**Scenario:** User asks for analysis of 600519, comprehensive price history, fundamental data available, identifiable catalyst.

**Correct response:**
Proceed with `analysis` using full thesis structure:
- Thesis statement: "600519 positioned for trend continuation driven by institutional accumulation, sector rotation, margin expansion, and upcoming policy catalyst"
- Key drivers: "1) Net institutional inflow over 10 consecutive sessions, 2) Sector relative strength vs. benchmark, 3) Q3 margin expansion to 25% (up from 22%), 4) Technical breakout above 200-day resistance, 5) Policy catalyst expected Q1 2026"
- Primary catalyst: "Industry policy announcement expected January 2026; historical pattern shows 2-3 week advance positioning"
- Variant view: "Alternative interpretation: margin expansion is cyclical peak rather than structural improvement; institutional flow may reverse post-catalyst; sector rotation may be late-cycle rather than early-cycle"
- Disconfirming evidence: "Sector breadth narrowing (only 30% of constituents above 50-day MA); volume profile shows increasing retail participation; valuation at 95th percentile of 5-year range"
- Invalidation conditions: "Thesis invalidated if: 1) price closes below 180 support on volume, 2) sector relative strength turns negative for 3+ sessions, 3) institutional flow reverses to net selling, 4) Q4 margins contract below 23%, 5) policy catalyst delayed beyond Q1"

## Integration with Skills

### For `market-brief`:
- Assumes Level 1 or Level 2 evidence
- Does not require thesis structure
- Focuses on current state description and conditional guidance

### For `analysis`:
- Requires Level 2 (conditional thesis) or Level 3 (full thesis) evidence
- Enforces mandatory thesis structure
- Must acknowledge evidence gaps explicitly when they exist

### For `decision-support`:
- Can operate at any evidence level
- Must disclose evidence limitations in "Non-Modeled Risks" section
- Must state when decision frame is based on limited evidence

### For `backtest-evaluator`:
- Must acknowledge what evidence was available at the time of original decision
- "What Was Not Knowable Then" section guards against hindsight bias
- Cannot claim validation when original decision was based on insufficient evidence
