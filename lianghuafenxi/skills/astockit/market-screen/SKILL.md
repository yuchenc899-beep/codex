---
name: market-screen
description: "Rank multiple A-share symbols or CSV files. Use when user wants the breadth-first triage stage of the workflow: universe filtering, comparative scoring, shortlist creation, and explicit skip accounting before deeper single-name work."
argument-hint: [symbol-or-list]
allowed-tools: Bash(python3 *), Read, Glob
---

# Market Screen

Rank multiple A-share candidates for: $ARGUMENTS

## Overview

- Implementation status: code-backed
- Local entry script: `<bundle-root>/market-screen/run.py`
- Primary purpose: batch-score a candidate universe and return the strongest names first
- Research layer: universe formation and comparative ranking (Stage 1: Strategy Design & Hypothesis Formation - Universe definition, Stage 4: Feature Engineering & Signal Construction - Cross-sectional ranking)
- Workflow stages: stage 1 `Universe Formation` and stage 4 `Feature Engineering & Signal Construction` for breadth-first triage
- Local executor guarantee: apply the shared market score to each candidate, sort valid names, and list skipped entries when partial failures occur

## Use When

- The user wants a ranked candidate list.
- The user wants to score a watchlist before doing deeper single-name analysis.
- The user is starting from many symbols or a directory of per-symbol CSV files.
- The user wants to identify the strongest opportunities from a large universe.
- The user wants comparative ranking across multiple symbols.
- The user wants to filter a universe before applying deeper research or decision support.

## Do Not Use When

- The user wants a full report for one symbol. Use `market-brief` or `analysis`.
- The user wants a batch action summary rather than raw comparative ranking. Use `decision-dashboard`.
- The user wants only data normalization. Use `market-data`.
- The user expects this to be a statistically validated factor backtest or portfolio optimizer. It is not.
- The user wants portfolio construction or position sizing. Use `decision-support` or `strategy-design`.

## Inputs

- Direct positional symbols.
- Optional `--file PATH`: plain text file containing one symbol per line.
- Optional `--dir PATH`: directory of per-symbol CSV files.
- Optional `--top N`, `--start`, `--end`, `--source`.
- Important boundary: `--file` is a symbol-list file, not a market-data CSV.
- Universe-quality note:
  - import or file quality matters more than the ranking algorithm if the universe itself is polluted
  - the agent should state whether the screen is over a curated watchlist, a raw import, or a local directory dump

## Execution

### Step 1: Define universe and screening criteria

Before screening, clarify the universe and objectives:

**Universe definition:**
- [ ] Universe source (curated watchlist, sector, index, custom list)
- [ ] Universe size (number of symbols to screen)
- [ ] Universe quality (tradeable, liquid, non-suspended)
- [ ] Universe constraints (sector, market cap, board, etc.)

**Screening objectives:**
- [ ] Identify top opportunities (highest scores)
- [ ] Filter by specific criteria (trend, momentum, regime)
- [ ] Comparative ranking (relative strength across universe)
- [ ] Shortlist creation (top N for deeper analysis)

**Screening criteria:**
- **Technical criteria:** Trend, momentum, volatility, volume, support/resistance
- **Regime criteria:** Bull/bear/range/volatile/breakout/exhaustion
- **Risk criteria:** Overbought/oversold, divergence, price limits, suspensions
- **Liquidity criteria:** Volume, turnover, bid-ask spread
- **A-share criteria:** ST/\*ST status, suspension risk, price limit proximity

### Step 2: Validate universe quality

Before scoring, validate the candidate universe:

**Universe quality checks:**
- [ ] All symbols are valid A-share tickers
- [ ] Symbols are currently tradeable (not delisted)
- [ ] Symbols are not suspended (or suspension flagged)
- [ ] Symbols have sufficient data history (minimum 60 days)
- [ ] Symbols meet minimum liquidity requirements (if specified)

**Universe cleaning:**
- Remove invalid symbols (non-existent tickers)
- Flag suspended symbols (include with warning or exclude)
- Flag ST/\*ST symbols (higher risk, may exclude)
- Flag illiquid symbols (volume < threshold)
- Document removed symbols and reasons

**Universe provenance:**
- State universe source (watchlist, import, directory, user-supplied)
- State universe generation date (fresh vs. stale)
- State universe curation level (curated vs. raw)
- State universe quality (clean vs. noisy)

### Step 3: Batch score universe

Apply systematic scoring to each symbol:

**For each symbol in universe:**
1. Load market data (OHLCV, normalized and validated)
2. Calculate technical features (MAs, momentum, volatility, volume)
3. Assess market state (trend, regime, bias, score)
4. Identify risk flags (overbought, oversold, divergence, etc.)
5. Calculate composite score (0-100)
6. Record scoring timestamp and data freshness

**Scoring methodology (consistent with market-analyze):**
- Trend component (30%): Strong uptrend = 90-100, Strong downtrend = 0-19
- Momentum component (25%): Strong positive = 90-100, Strong negative = 0-19
- Volume component (15%): Confirming = +10, Diverging = -10
- Volatility component (15%): Low vol = +10, High vol = -10
- Support/resistance component (15%): Near support = +10, Near resistance = -10

**Partial failure handling:**
- If symbol data unavailable: Skip and record reason
- If symbol data insufficient: Skip and record reason
- If symbol suspended: Flag and optionally skip
- If symbol calculation fails: Skip and record error
- Continue processing remaining symbols

**Batch processing efficiency:**
- Process symbols in parallel when possible
- Cache intermediate results to avoid recomputation
- Fail fast on invalid symbols
- Aggregate results as they complete

### Step 4: Rank and filter results

Apply ranking and filtering to scored universe:

**Primary ranking:**
- Sort by composite score (descending, highest first)
- Break ties by momentum strength
- Break further ties by volume confirmation

**Secondary filters (optional):**
- **Trend filter:** Only include symbols with specific trend (uptrend, downtrend, sideways)
- **Regime filter:** Only include symbols in specific regime (bull, bear, range, etc.)
- **Momentum filter:** Only include symbols above/below momentum threshold
- **Liquidity filter:** Only include symbols above volume/turnover threshold
- **Risk filter:** Exclude symbols with specific risk flags (overbought, suspended, etc.)

**Top N selection:**
- If `--top N` specified, return only top N symbols
- If not specified, return all valid symbols (sorted)
- Document cutoff score (score of Nth symbol)
- Document how many symbols excluded by filters

**Comparative metrics:**
- Score distribution (min, max, median, quartiles)
- Trend distribution (% uptrend, downtrend, sideways)
- Regime distribution (% bull, bear, range, etc.)
- Risk flag distribution (% overbought, oversold, etc.)

### Step 5: Document skipped symbols

Track and report symbols that could not be scored:

**Skip categories:**
- **Invalid symbols:** Non-existent tickers, wrong format
- **Suspended symbols:** Currently suspended, no recent data
- **Insufficient data:** < 60 days history, missing OHLCV
- **Calculation errors:** Technical indicator failures, data quality issues
- **Filter exclusions:** Failed secondary filters (liquidity, risk, etc.)

**For each skip category:**
- Count of symbols skipped
- List of specific symbols (if count < 20)
- Reason for skip (specific error or filter)
- Recommendation (fix data, wait for resumption, exclude permanently)

### Step 6: Generate screening report

Organize results into structured report:

**Part 1: Screening Summary**
- Universe source and size
- Screening timestamp
- Valid symbols scored
- Symbols skipped (by category)
- Top N cutoff (if applicable)

**Part 2: Top Ranked Symbols**
For each symbol in top N (or all if no limit):
- Symbol, name, board
- Composite score (0-100)
- Trend (direction, strength, classification)
- Regime (bull/bear/range/volatile/breakout/exhaustion)
- Bias (bullish/bearish/neutral/uncertain)
- Latest price, change %, volume ratio
- Key risk flags (if any)

**Part 3: Comparative Analysis**
- Score distribution across universe
- Trend distribution (% in each category)
- Regime distribution (% in each category)
- Risk flag distribution (% with each flag)
- Liquidity distribution (volume, turnover)

**Part 4: Skipped Symbols**
- Invalid symbols (count and list)
- Suspended symbols (count and list)
- Insufficient data (count and list)
- Calculation errors (count and list)
- Filter exclusions (count and list)

**Part 5: Universe Quality Assessment**
- Universe quality score (0-100)
- Data completeness (% with full data)
- Data freshness (average age of latest data)
- Liquidity profile (% meeting liquidity threshold)
- Risk profile (% with risk flags)

**Part 6: Screening Interpretation**
- What the ranking represents (comparative technical strength)
- What the ranking does NOT represent (expected returns, validated alpha)
- Recommended next steps (deeper analysis on top names)
- Caveats and limitations (scoring methodology, data quality, etc.)

**Part 7: Next Steps Guidance**
- For top-ranked symbols: Run `market-brief` or `analysis` for deeper review
- For symbols needing action: Run `decision-support` for position sizing
- For symbols needing execution: Run `strategy-design` for execution planning
- For batch action summary: Run `decision-dashboard` for portfolio view

### Step 7: Run the local executor

```bash
python3 <bundle-root>/market-screen/run.py <symbol ...> [--file PATH] [--dir PATH] [--top N]
```

### Step 8: Interpret ranking as triage, not validated alpha

When delivering results, maintain proper framing:

**Ranking interpretation:**
- This is comparative technical strength ranking, not expected return prediction
- Scores reflect current market state, not future performance
- High scores indicate favorable technical setup, not guaranteed profit
- Low scores indicate unfavorable technical setup, not guaranteed loss

**Methodology transparency:**
- Scoring uses same methodology as `market-analyze` (trend, momentum, volume, volatility, support/resistance)
- Weights are heuristic (30% trend, 25% momentum, etc.), not optimized
- No statistical validation or backtesting performed
- No fundamental or news analysis included

**Limitations and caveats:**
- **Not a factor backtest:** No historical validation of score predictiveness
- **Not portfolio optimization:** No correlation, diversification, or risk budgeting
- **Not execution ready:** Requires deeper analysis before action
- **Data quality dependent:** Garbage in, garbage out
- **Point-in-time only:** Scores reflect current state, change rapidly

**Recommended workflow:**
1. Use screening to identify top candidates (top 10-20)
2. Run `market-brief` or `analysis` on top candidates for deeper review
3. Run `decision-support` on selected candidates for position sizing
4. Run `strategy-design` on selected candidates for execution planning
5. Monitor positions and rescreen periodically to identify new opportunities

### Step 9: Hand off cleanly to downstream skills

Pass shortlist to appropriate next skill:

**For deeper single-name analysis:**
- `market-brief`: Quick overview of top candidates
- `analysis`: Full thesis development for selected candidates
- `market-analyze`: Detailed technical state for selected candidates
- `technical-scan`: Pattern recognition for selected candidates

**For decision and execution:**
- `decision-support`: Position sizing for selected candidates
- `strategy-design`: Execution planning for selected candidates
- `paper-trading`: Simulated execution for selected candidates

**For batch operations:**
- `decision-dashboard`: Portfolio-level action summary
- `watchlist`: Save shortlist for ongoing monitoring

## Output Contract

- Minimum local executor output: human-readable text beginning with `批量筛选`.
- Core content: ranked symbols with score, trend, regime, change percentage, and volume ratio.
- Partial failure behavior: invalid symbols or malformed per-symbol files are listed under `跳过` if at least one valid result exists.
- Caller-facing delivery standard:
  - **Seven-part structure:** Screening summary, top ranked symbols, comparative analysis, skipped symbols, universe quality, screening interpretation, next steps guidance
  - **Universe provenance:** Identify source and quality of universe being screened
  - **Skip accounting:** Distinguish kept names from skipped names with specific reasons
  - **Ranking interpretation:** Treat screen as comparative technical strength ranking, not expected return prediction
  - **Methodology transparency:** Explain scoring methodology and weights (trend 30%, momentum 25%, etc.)
  - **Limitations disclosure:** State what ranking does NOT represent (validated alpha, portfolio optimization, execution readiness)
  - **Next steps guidance:** Recommend appropriate downstream skills for shortlisted symbols
  - **Comparative metrics:** Provide score distribution, trend distribution, regime distribution across universe
  - **Quality assessment:** Universe quality score, data completeness, freshness, liquidity profile
  - **No action claims:** Keep strictly descriptive; shortlist needs deeper review before action

## Failure Handling

- Parse and argument errors: non-zero exit with a readable `命令错误` message.
- If all candidates fail: readable failure text beginning with `执行失败:`.
- Mixed candidate quality: valid results still return, and invalid entries are summarized under `跳过`.
- If the input universe is obviously weak, noisy, or unresolved, say so rather than over-interpreting the rank order.
- Invalid symbols: Skip and list under "Invalid symbols" category.
- Suspended symbols: Flag and optionally skip, list under "Suspended symbols" category.
- Insufficient data: Skip and list under "Insufficient data" category.
- Calculation errors: Skip and list under "Calculation errors" category.

## Key Rules

- **Prefer this skill for breadth-first triage.**
- **Keep the distinction between symbol lists and data-file directories explicit.**
- **Do not use this output as a substitute for one-symbol research, execution planning, or backtest validation.**
- **If the user wants action distribution instead of raw ranking, route to `decision-dashboard`.**
- **Universe quality validation is mandatory.** Check for invalid, suspended, illiquid symbols.
- **Skip accounting must be comprehensive.** Document all skipped symbols with specific reasons.
- **Ranking interpretation must be qualified.** This is comparative technical strength, not expected returns.
- **Methodology must be transparent.** Explain scoring components and weights.
- **Limitations must be disclosed.** State what this is NOT (factor backtest, portfolio optimization, etc.).
- **Next steps must be explicit.** Guide user to appropriate downstream skills.
- **Comparative metrics must be provided.** Score distribution, trend distribution, regime distribution.
- **No action claims without deeper analysis.** Shortlist requires review before execution.

## Composition

- Often follows `watchlist-import`.
- Often feeds `market-brief`, `analysis`, `market-analyze`, or `decision-support` for shortlisted symbols.
- Shares the same score path as `decision-dashboard`.
- Can feed `decision-dashboard` for batch action summary on shortlist.
- Can feed `watchlist` to save shortlist for ongoing monitoring.
- Should be rerun periodically to identify new opportunities as market conditions change.
