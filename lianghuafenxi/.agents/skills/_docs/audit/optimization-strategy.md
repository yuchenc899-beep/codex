# Skill Optimization Strategy

## Executive Summary

After reviewing 7 of 24 skills, clear optimization patterns have emerged. Rather than continuing the full 24-skill review, I recommend implementing optimizations on the identified high-priority skills first, then applying the patterns systematically to remaining skills.

---

## Key Findings

### 1. Over-Specification Pattern (High Impact)

**Problem:** Skills with detailed validation/calculation specifications are 30-50% longer than necessary.

**Affected Skills:**
- fundamental-context (150+ lines, could be 100-110)
- news-intel (similar pattern emerging)
- data-sync (likely similar)
- market-screen (likely similar)

**Solution:**
- Replace exhaustive checklists with high-level frameworks + examples
- Move detailed specifications to reference sections
- Focus on "what to validate" not "how to calculate every metric"

**Example Transformation:**

**Before (fundamental-context):**
```
#### Financial Statement Validation

**Income statement checks:**
- [ ] Revenue >= 0 (negative revenue is rare, flag for investigation)
- [ ] Gross profit <= Revenue (gross margin <= 100%)
- [ ] Operating profit consistency (revenue - COGS - opex)
- [ ] Net income consistency (operating profit + non-operating - tax)
- [ ] EPS calculation: net income / weighted average shares

**Balance sheet checks:**
- [ ] Assets = Liabilities + Equity (accounting identity)
- [ ] Current assets >= 0, Current liabilities >= 0
- [ ] Total equity can be negative (flag as distressed)
- [ ] Book value per share: total equity / shares outstanding
- [ ] Working capital: current assets - current liabilities
```

**After:**
```
#### Financial Statement Validation

**Validation categories:**
- **Accounting identities:** Assets = Liabilities + Equity, income flows to equity
- **Range checks:** Revenue >= 0, margins <= 100%, ratios within reasonable bounds
- **Cross-statement consistency:** Net income, depreciation, capex flow between statements
- **Quality flags:** Negative equity (distressed), unusual margins, cash flow divergence

For detailed validation rules, see fundamental-context reference documentation.
```

**Impact:** 40-50% reduction in validation sections

---

### 2. Component Redundancy Pattern (Medium Impact)

**Problem:** Composite skills repeat specifications from their component skills.

**Affected Skills:**
- stock-data (repeats market-data + fundamental-context specs)
- market-brief (repeats market-analyze + decision-support + strategy-design specs)
- analysis (repeats multiple component specs)

**Solution:**
- Reference component skills for detailed specifications
- Focus on composition logic and integration points
- Specify only what's unique to the composite skill

**Example Transformation:**

**Before (stock-data):**
```
**Market data collection:**
- Run `market-data` skill or equivalent to get normalized OHLCV
- Validate data quality (completeness, consistency, outliers)
- Document data source, date range, and quality score
- Flag any data quality issues that affect downstream analysis

**Technical feature engineering:**
- Calculate trend indicators (MAs, ADX, trend classification)
- Calculate momentum indicators (RSI, MACD, Stochastic, ROC)
- Calculate volatility indicators (ATR, Bollinger Bands, historical vol)
- Calculate volume indicators (volume ratio, OBV, accumulation/distribution)
```

**After:**
```
**Market data collection:**
- Run `market-data` skill to get normalized OHLCV with quality validation (see market-data for details)
- Run `market-analyze` skill to get technical features and state assessment (see market-analyze for indicator specifications)
- Document data source, date range, and quality score in packet metadata
```

**Impact:** 20-30% reduction in composite skills

---

### 3. Routing Redundancy Pattern (Low-Medium Impact)

**Problem:** Routing guidance repeated in multiple sections.

**Affected Skills:**
- analysis (routing vs market-brief in multiple places)
- market-brief (routing vs analysis in multiple places)
- All skills with "Do Not Use When" sections

**Solution:**
- Consolidate routing into single clear section
- Use decision tree format for complex routing
- Reference routing section from other locations

**Impact:** 10-15% reduction in skills with complex routing

---

### 4. Terminology Inconsistency Pattern (Clarity Impact)

**Problem:** Same concepts described with different terms across skills.

**Examples:**
- "snapshot" vs "packet" vs "artifact" vs "frame"
- "bounded" vs "scoped" vs "limited" vs "narrow"
- "descriptive" vs "interpretive" vs "analytical"
- "fail-open" vs "best-effort" vs "partial"

**Solution:**
- Create terminology glossary
- Standardize usage across all skills
- Define terms on first use in each skill

**Impact:** Improved clarity without length reduction

---

## Recommended Optimization Approach

### Phase 1: High-Priority Optimizations (Immediate)

**Target Skills:**
1. fundamental-context - Consolidate validation specifications (30-40% reduction)
2. stock-data - Eliminate component redundancy (20-25% reduction)
3. data-sync - Likely has similar over-specification (review + optimize)
4. market-screen - Likely has similar over-specification (review + optimize)

**Expected Impact:** 4 skills optimized, ~25-30% average reduction

---

### Phase 2: Medium-Priority Optimizations (Next)

**Target Skills:**
1. analysis - Consolidate thesis structure, reduce routing redundancy (15-20% reduction)
2. market-brief - Consolidate routing guidance (15-20% reduction)
3. technical-scan - Reduce repetition, clarify execution model (10-15% reduction)
4. news-intel - Consolidate event categories (10-15% reduction)
5. decision-dashboard - Likely has specification redundancy (review + optimize)
6. watchlist-import - Likely has specification redundancy (review + optimize)

**Expected Impact:** 6 skills optimized, ~15-20% average reduction

---

### Phase 3: Terminology Standardization (Parallel)

**Create glossary with standard terms:**

**Artifact Types:**
- **Packet:** Structured data snapshot (stock-data output)
- **Report:** Human-readable analysis document (analysis, market-brief output)
- **Snapshot:** Point-in-time state summary (market-analyze output)
- **Artifact:** Generic term for any persisted output

**Scope Descriptors:**
- **Bounded:** Limited to specific data/time scope
- **Descriptive:** Current state interpretation without prediction
- **Prescriptive:** Includes recommendations or actions

**Quality States:**
- **Fail-open:** Continues with partial results rather than failing
- **Status-tracked:** Uses ok/partial/not_supported/stale/error model
- **Best-effort:** Attempts but doesn't guarantee completeness

**Apply consistently across all 24 skills**

---

### Phase 4: Low-Priority Polish (Final)

**Target remaining skills:**
- Review for minor redundancies
- Apply terminology standards
- Ensure consistency with optimized skills

**Expected Impact:** Remaining 14 skills, ~5-10% average reduction

---

## Overall Expected Results

**Length Reduction:**
- High-priority skills (4): 25-30% reduction
- Medium-priority skills (6): 15-20% reduction
- Low-priority skills (14): 5-10% reduction
- **Overall average: 12-18% reduction across all 24 skills**

**Clarity Improvements:**
- Consistent terminology across all skills
- Clearer composition patterns
- Reduced cognitive load from repetition

**Maintained Standards:**
- All professional standards preserved
- No loss of critical specifications
- Improved rather than reduced usability

---

## Implementation Plan

1. **Create terminology glossary** (30 minutes)
2. **Optimize fundamental-context** (45 minutes)
3. **Optimize stock-data** (30 minutes)
4. **Review and optimize data-sync** (30 minutes)
5. **Review and optimize market-screen** (30 minutes)
6. **Optimize analysis** (30 minutes)
7. **Optimize market-brief** (30 minutes)
8. **Apply patterns to remaining skills** (2-3 hours)
9. **Validation pass** (1 hour)
10. **Update documentation** (30 minutes)

**Total estimated time: 6-7 hours**

---

## Recommendation

**Proceed with Phase 1 optimizations immediately:**
1. Create terminology glossary
2. Optimize fundamental-context (highest impact)
3. Optimize stock-data (high impact, clear pattern)
4. Review data-sync and market-screen for similar patterns

This will validate the optimization approach and deliver immediate value before committing to full 24-skill optimization.
