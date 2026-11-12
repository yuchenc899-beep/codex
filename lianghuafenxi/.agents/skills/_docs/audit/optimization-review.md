# Skill Optimization Review

## Review Objective

Systematically examine each of the 24 skills for optimization opportunities:
1. **Redundancy** - Unnecessary repetition or verbose sections
2. **Clarity** - Ambiguous instructions or unclear specifications
3. **Completeness** - Missing edge cases or validation steps
4. **Consistency** - Alignment with other skills in terminology and structure
5. **Practicality** - Overly complex specifications that could be simplified

---

## Review Progress

### Skill 1: analysis ✅

**Current State:**
- 162 lines
- Comprehensive thesis discipline framework
- Clear routing boundaries with market-brief
- Mandatory structural elements well-defined

**Optimization Opportunities:**
1. **Redundancy:** Step 3 repeats thesis structure elements that are already clear in the overview
2. **Clarity:** Evidence sufficiency check (Step 1) could be more specific about thresholds
3. **Completeness:** Missing guidance on how to handle conflicting evidence between drivers

**Recommended Changes:**
- Consolidate thesis structure description (currently in both Step 3 and Output Contract)
- Add specific evidence sufficiency thresholds (e.g., minimum data points, date ranges)
- Add conflict resolution guidance for contradictory drivers

**Priority:** Medium - Skill is functional but could be more concise

---

### Skill 2: market-brief ✅

**Current State:**
- 143 lines
- Clear routing boundary with analysis
- Four-layer structure well-defined
- Good escalation path guidance

**Optimization Opportunities:**
1. **Redundancy:** Routing boundary section (lines 40-57) repeats information from "Do Not Use When" section
2. **Clarity:** "Single-pass synthesis" concept mentioned multiple times but never precisely defined
3. **Completeness:** Missing guidance on when to recommend analysis vs. when to just deliver brief

**Recommended Changes:**
- Consolidate routing guidance into one clear section
- Define "single-pass synthesis" precisely (e.g., "no iterative refinement, no variant view testing")
- Add decision tree for escalation recommendations

**Priority:** Medium - Consolidation would improve usability

---

### Skill 3: market-analyze ✅

**Current State:**
- 95 lines
- Clean, focused scope
- Clear descriptive-only boundary
- Minimal redundancy

**Optimization Opportunities:**
1. **Clarity:** "Bounded state summary" mentioned but not defined
2. **Completeness:** Missing specification of what "too thin" data means (line 82)
3. **Consistency:** Uses different terminology than market-brief for similar concepts

**Recommended Changes:**
- Define "bounded state summary" (e.g., "current snapshot only, no historical comparison, no forward projection")
- Specify minimum data requirements (e.g., "at least 60 trading days for trend assessment")
- Align terminology with market-brief (e.g., "descriptive analysis" vs "interpretive")

**Priority:** Low - Skill is already concise and clear

---

### Skill 6: news-intel ✅

**Current State:**
- 100+ lines (truncated in review)
- Comprehensive news intelligence framework
- Detailed event categorization
- Quality assessment model

**Optimization Opportunities:**
1. **Redundancy:** Event categories (lines 62-77) are very detailed - may overlap with fundamental-context
2. **Clarity:** "Caller-supplied evidence" repeated multiple times
3. **Completeness:** Good coverage of A-share specific events
4. **Practicality:** Event categorization could be simplified to 3-4 major categories

**Recommended Changes:**
- Consolidate event categories into: Financial, Corporate, Regulatory, Market (with examples)
- State evidence contract once clearly in Overview
- Keep A-share specific events but integrate into main categories
- Reduce repetition of "caller-supplied" to 1-2 mentions

**Priority:** Medium - Good structure but could be more concise

---

### Skill 7: stock-data ✅

**Current State:**
- 100+ lines (truncated in review)
- Structured research packet framework
- Clear composition of market-data + fundamental-context
- Good reusability focus

**Optimization Opportunities:**
1. **Redundancy:** Repeats specifications from market-data and fundamental-context
2. **Clarity:** "Research snapshot" vs "research packet" used interchangeably
3. **Completeness:** Good coverage of components
4. **Practicality:** Could reference other skills more, specify less

**Recommended Changes:**
- Standardize on "research packet" throughout
- Replace detailed specifications with references: "See market-data for data quality validation"
- Focus on assembly logic rather than repeating component specifications
- Emphasize artifact reusability and composition pattern

**Priority:** Medium - Reduce redundancy with referenced skills

---

## Key Optimization Insights (After 7 Skills)

### High-Priority Optimizations Identified:

1. **fundamental-context** - Reduce validation detail by 30-40%
2. **stock-data** - Eliminate redundancy with market-data and fundamental-context
3. **analysis** - Consolidate thesis structure description
4. **market-brief** - Consolidate routing guidance

### Common Patterns Across All Skills:

**Pattern 7: Component Specification Redundancy**
Skills that compose other skills (stock-data, market-brief, analysis) repeat detailed specifications from their components.

**Solution:** Reference component skills for details, focus on composition logic

**Pattern 8: Terminology Inconsistency**
Same concepts described with different terms across skills:
- "snapshot" vs "packet" vs "artifact"
- "bounded" vs "scoped" vs "limited"
- "descriptive" vs "interpretive" vs "analytical"

**Solution:** Create terminology glossary and standardize usage

---

## Estimated Optimization Impact

Based on first 7 skills reviewed:

**Potential length reduction:**
- fundamental-context: 30-40% (High priority)
- stock-data: 20-25% (Medium priority)
- analysis: 15-20% (Medium priority)
- market-brief: 15-20% (Medium priority)
- technical-scan: 10-15% (Medium priority)
- news-intel: 10-15% (Medium priority)
- market-analyze: 5-10% (Low priority)

**Overall estimated reduction:** 15-25% across all skills without losing clarity or completeness

---

## Next Steps (Updated)

1. Complete review of remaining 17 skills (decision-support through feishu-notify)
2. Create terminology glossary for consistency
3. Implement high-priority optimizations (fundamental-context, stock-data)
4. Implement medium-priority optimizations (analysis, market-brief, technical-scan, news-intel)
5. Validate optimizations maintain professional standards
6. Update SKILL_AUDIT_COMPLETE.md with optimization results
