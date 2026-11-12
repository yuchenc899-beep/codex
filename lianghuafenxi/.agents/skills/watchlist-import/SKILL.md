---
name: watchlist-import
description: "Import a watchlist from text or files and normalize symbols. Use when user wants the stage-1 universe intake workflow: raw list ingestion, symbol normalization, unresolved-item preservation, and explicit confidence labels before screening."
argument-hint: [text-or-file]
allowed-tools: Bash(python3 *), Read, Glob
---

# Watchlist Import

Import a watchlist for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/watchlist-import/run.py`
- Primary purpose: normalize raw universe input into resolved and unresolved items without silently guessing ambiguous names
- Research layer: universe formation (Stage 1: Strategy Design & Hypothesis Formation - Universe definition)
- Workflow stage: stage 1 `Strategy Design & Universe Formation`
- Local executor guarantee: parse raw text or supported files, normalize symbol-like items, preserve unresolved entries, and return a structured import summary

## Use When

- The user starts with pasted symbols, symbol-like text, or a watchlist file.
- The caller needs symbol normalization before screening, dashboards, or repeat coverage.
- The user wants unresolved names separated from recognized symbols instead of guessed mapping.
- The user wants to build a universe from external sources (spreadsheets, text files, web scraping results).
- The user wants to validate and clean a symbol list before analysis.

## Do Not Use When

- The user already has a clean symbol list and wants ranking. Use `market-screen` or `decision-dashboard`.
- The user wants post-import grouping, review cadence, or repeated tracking. Use `watchlist`.
- The user wants one-symbol analysis rather than universe construction.
- The user wants portfolio construction with position sizing. Use `decision-support` or `strategy-design`.

## Inputs

- Direct positional items interpreted as raw symbol-like text.
- Optional `--text TEXT`: explicit text payload as the watchlist source.
- Optional `--file PATH`: load from a local text or `.xlsx` file.
- Current implementation scope: text and `.xlsx` parsing only.
- Universe-construction note:
  - import does not validate liquidity, sector fit, tradeability, or strategy fit
  - it only resolves symbol identity as far as the local parser can do so safely

## Execution

### Step 1: Define import source and objectives

Before importing, clarify the source and purpose:

**Import source types:**
- [ ] Direct text input (pasted symbols, comma-separated, space-separated)
- [ ] Text file (one symbol per line, or delimited)
- [ ] Spreadsheet file (.xlsx, .csv with symbol column)
- [ ] Mixed format (symbols + company names + other text)
- [ ] Web scraping result (HTML table, JSON, etc.)

**Import objectives:**
- [ ] Build initial universe for screening
- [ ] Clean and validate existing watchlist
- [ ] Merge multiple watchlists
- [ ] Convert company names to symbols
- [ ] Validate symbol format and existence

**Expected output:**
- [ ] Clean symbol list (resolved symbols only)
- [ ] Unresolved items list (for manual review)
- [ ] Import statistics (total, resolved, unresolved, confidence)
- [ ] Ready for downstream screening or analysis

### Step 2: Parse and normalize input

Apply systematic parsing and normalization:

**Text parsing:**
- **Delimiter detection:** Identify separators (comma, space, newline, tab, semicolon)
- **Symbol extraction:** Extract symbol-like patterns (6-digit codes, alphanumeric with dots)
- **Company name detection:** Identify Chinese company names (contains 公司, 股份, 集团, etc.)
- **Noise removal:** Remove common non-symbol text (headers, labels, punctuation)

**Symbol normalization:**
- **A-share format:** 6-digit code (e.g., 600519, 000001, 300750)
- **Board prefix:** Add board prefix if missing (SH for 600xxx/601xxx/603xxx/688xxx, SZ for 000xxx/001xxx/002xxx/300xxx)
- **Case normalization:** Uppercase for consistency
- **Padding:** Pad short codes to 6 digits if needed (e.g., 1 → 000001)

**Company name resolution:**
- **Exact match:** Look up company name in symbol database
- **Fuzzy match:** Try partial matching for common abbreviations
- **Ambiguity handling:** If multiple matches, mark as unresolved
- **No match:** Keep in unresolved list for manual review

**Spreadsheet parsing:**
- **Column detection:** Identify symbol column (by header or content pattern)
- **Multi-column support:** Extract symbols from multiple columns if present
- **Row filtering:** Skip header rows, empty rows, total rows
- **Data type handling:** Convert numeric codes to strings with leading zeros

### Step 3: Validate and categorize symbols

Validate each resolved symbol:

**Symbol format validation:**
- [ ] 6-digit numeric code
- [ ] Valid board prefix (SH or SZ)
- [ ] Matches A-share symbol pattern
- [ ] No invalid characters

**Symbol existence validation:**
- [ ] Symbol exists in A-share market
- [ ] Symbol is not delisted
- [ ] Symbol has recent trading data
- [ ] Symbol board matches prefix

**Symbol categorization:**
- **Main board:** 600xxx, 601xxx, 603xxx (Shanghai), 000xxx, 001xxx (Shenzhen)
- **ChiNext:** 300xxx (Shenzhen)
- **STAR Market:** 688xxx (Shanghai)
- **Beijing Stock Exchange:** 8xxxxx, 4xxxxx
- **ST/\*ST:** Special treatment stocks (higher risk)

**Confidence scoring (0-100):**
- **High confidence (90-100):** Valid 6-digit code, exists in market, has recent data
- **Medium confidence (70-89):** Valid format, exists in market, but stale data or suspended
- **Low confidence (50-69):** Valid format, but cannot verify existence
- **Unresolved (0-49):** Invalid format, ambiguous, or no match found

### Step 4: Handle unresolved items

Process items that cannot be resolved:

**Unresolved categories:**
- **Invalid format:** Not a valid A-share symbol format
- **Ambiguous:** Multiple possible matches (e.g., company name matches multiple symbols)
- **Not found:** Valid format but symbol does not exist
- **Delisted:** Symbol was valid but is now delisted
- **Foreign:** Non A-share symbol (H-share, US stock, etc.)

**For each unresolved item:**
- Original text (as provided by user)
- Reason for non-resolution (invalid format, ambiguous, not found, etc.)
- Suggested actions (manual lookup, format correction, removal)
- Possible matches (if ambiguous, list candidates)

**Unresolved handling strategies:**
- **Preserve for manual review:** Keep in separate list for user to resolve
- **Suggest corrections:** Provide likely corrections based on fuzzy matching
- **Flag for removal:** Clearly invalid items that should be removed
- **Request clarification:** Ambiguous items that need user input

### Step 5: Generate import summary

Organize results into structured report:

**Part 1: Import Summary**
- Import source (text, file, spreadsheet)
- Import timestamp
- Total items processed
- Resolved symbols (count and %)
- Unresolved items (count and %)
- Average confidence score

**Part 2: Resolved Symbols**
For each resolved symbol:
- Symbol (with board prefix)
- Company name (if available)
- Board (Main/ChiNext/STAR/Beijing)
- Confidence score (0-100)
- Status (active/suspended/ST/\*ST)
- Latest price and date (if available)

**Part 3: Resolved Symbol Statistics**
- Board distribution (% Main, ChiNext, STAR, Beijing)
- Status distribution (% active, suspended, ST/\*ST)
- Confidence distribution (% high, medium, low)
- Sector distribution (if available)
- Market cap distribution (if available)

**Part 4: Unresolved Items**
For each unresolved item:
- Original text
- Reason for non-resolution
- Suggested action
- Possible matches (if any)

**Part 5: Unresolved Item Statistics**
- Unresolved by category (invalid format, ambiguous, not found, delisted, foreign)
- Unresolved by source (which part of input had most issues)
- Resolvability assessment (% that could be resolved with manual effort)

**Part 6: Import Quality Assessment**
- Import quality score (0-100)
  - Based on resolution rate, confidence scores, and data completeness
- Data completeness (% with company name, price, status)
- Source quality (clean vs. noisy input)
- Screening readiness (ready/needs cleanup/major issues)

**Part 7: Recommended Next Steps**
- **If high quality (>90% resolved, high confidence):**
  - Ready for `market-screen` or `decision-dashboard`
- **If medium quality (70-90% resolved):**
  - Review unresolved items, then proceed to screening
- **If low quality (<70% resolved):**
  - Manual cleanup required before screening
  - Suggest using `watchlist` for ongoing management

### Step 6: Run the local executor

```bash
python3 <bundle-root>/watchlist-import/run.py [--text TEXT] [--file PATH] [items...]
```

### Step 7: Review result as universe-intake artifact

When delivering results, maintain proper framing:

**Import interpretation:**
- This is symbol normalization and validation, not investment recommendation
- Resolved symbols are format-valid and exist in market, not necessarily good investments
- Confidence scores reflect data quality, not investment quality
- Unresolved items require manual review, not automatic exclusion

**Source transparency:**
- State import source (text, file, spreadsheet, mixed)
- State source quality (clean, noisy, mixed format)
- State whether source looked like pure symbols or mixed content
- State any parsing assumptions made

**Quality assessment:**
- State import quality score and what it means
- State resolution rate and confidence distribution
- State whether result is screening-ready or needs cleanup
- State specific issues found (invalid formats, ambiguous names, etc.)

**Ambiguity preservation:**
- Do not silently coerce ambiguous names into symbols
- Keep unresolved items explicit with reasons
- Provide suggested actions for each unresolved item
- Do not guess or fabricate symbol mappings

**Validation limitations:**
- Import validates format and existence, not tradeability
- Import does not validate liquidity, listing status, or strategy fit
- Import does not check for duplicates across different formats (e.g., 600519 vs. SH600519)
- Import does not validate sector fit, market cap range, or other strategy criteria

### Step 8: Route to appropriate next skill

Based on import quality, route to next step:

**High quality import (>90% resolved):**
- `market-screen`: Rank symbols by technical strength
- `decision-dashboard`: Generate batch decision summary
- `watchlist`: Save for ongoing monitoring

**Medium quality import (70-90% resolved):**
- Manual review of unresolved items first
- Then proceed to `market-screen` or `decision-dashboard`
- Consider using `watchlist` for ongoing cleanup

**Low quality import (<70% resolved):**
- Manual cleanup required
- Use `watchlist` for iterative refinement
- Consider re-importing with cleaner source

**For individual symbol analysis:**
- `market-brief`: Quick overview of specific symbols
- `analysis`: Full thesis development for selected symbols

## Output Contract

- Minimum local executor output: human-readable text beginning with `导入结果`.
- Core fields: total item count, resolved symbol count, unresolved count, resolved entries, unresolved entries.
- Side effects: stores a session-history entry for the import operation.
- Caller-facing delivery standard:
  - **Seven-part structure:** Import summary, resolved symbols, resolved statistics, unresolved items, unresolved statistics, quality assessment, recommended next steps
  - **Source transparency:** State source form (text, file, spreadsheet, mixed) and quality (clean, noisy)
  - **Resolution accounting:** Distinguish resolved symbols from unresolved items with specific reasons
  - **Confidence scoring:** Provide confidence scores (0-100) for each resolved symbol
  - **Ambiguity preservation:** Keep unresolved entries explicit, do not silently coerce or guess
  - **Quality assessment:** Import quality score, resolution rate, confidence distribution, screening readiness
  - **Validation scope:** State what was validated (format, existence) and what was NOT (liquidity, tradeability, strategy fit)
  - **Next steps guidance:** Recommend appropriate downstream skills based on import quality
  - **No investment claims:** Resolved symbols are format-valid, not investment recommendations
- Non-guarantees:
  - No liquidity, listing-status, survivorship, or strategy-fit validation is guaranteed here
  - No durable local watchlist store is created by this skill alone (use `watchlist` for persistence)
  - No duplicate detection across different symbol formats
  - No sector, market cap, or other strategy criteria validation

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- File read or parse failures: readable failure text beginning with `执行失败:`.
- Unrecognized names: stay in the unresolved list instead of being guessed.
- If the source format is unsupported, say so directly instead of partial silent import.
- Ambiguous company names: list all possible matches in unresolved items, do not pick one arbitrarily.
- Invalid symbol formats: keep in unresolved list with specific format error.
- Delisted symbols: flag as delisted in unresolved list, do not silently include.

## Key Rules

- **Treat import as preprocessing, not as recommendation.**
- **Preserve ambiguity and unresolved rows explicitly.**
- **Do not silently coerce names into symbols.**
- **Use the import result as the intake gate before ranking, dashboarding, or repeated coverage.**
- **Confidence scoring is mandatory.** Every resolved symbol must have confidence score.
- **Unresolved categorization is mandatory.** Every unresolved item must have reason.
- **Quality assessment is mandatory.** Provide import quality score and screening readiness.
- **Source transparency is mandatory.** State source type and quality.
- **Validation scope must be explicit.** State what was validated and what was NOT.
- **No silent guessing.** If ambiguous, keep unresolved with suggestions.
- **No fabricated mappings.** Only resolve when confident.
- **Routing guidance must be specific.** Recommend next skill based on import quality.

## Composition

- Natural upstream step for `market-screen`, `decision-dashboard`, and `watchlist`.
- Can also prepare symbol lists for `analysis` and repeated one-symbol workflows.
- Should be followed by `watchlist` for persistent storage and ongoing management.
- High quality imports can proceed directly to `market-screen` or `decision-dashboard`.
- Low quality imports should route to `watchlist` for iterative cleanup.
- Resolved symbols can feed into any single-symbol skill (`market-brief`, `analysis`, etc.).
