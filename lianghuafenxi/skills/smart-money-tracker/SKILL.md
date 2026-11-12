---
name: smart-money-tracker
description: >-
  Track SEC 13F institutional holdings + congressional STOCK Act trades + House Clerk disclosures, produce convergence analysis between whales, politicians, and retail flows. Use whenever the user asks about hedge fund 13F filings, Berkshire/Bridgewater/Pershing Square/Soros/ARK portfolio changes, what Michael Burry or any other major investor is buying, politician stock trades (Pelosi, Tuberville, Cruz, etc.), STOCK Act disclosures, congressional insider trading, "smart money" flows, institutional positioning, whale conviction, cross-signal analysis between 13F and congressional trades, or wants a "smart money report" / "follow the whales" / "what are insiders doing" report. Triggers on phrases like "13F", "whale trades", "politician trades", "congress trading", "Pelosi bought", "smart money", "institutional holdings", "hedge fund positions", "Soros fund", "Berkshire portfolio", "what are insiders buying", "congressional insider", "follow the smart money", "rerun smart money report". Do NOT use for: single-ticker technical analysis, trade execution, options strategies, market commentary without picks, or non-equity flow analysis (use daily-market-watch or thematic-stock-picker instead).
---

# Smart Money Tracker

## When to Use

- User asks politician buying/selling
- User asks STOCK Act or congressional trading
- User asks institutional whale activity or 13F filings
- User asks overlap/divergence politician vs whale flows
- User asks rerun smart money report

## Important Notes

**Skill uses Python scripts with specific CLI args. Do NOT invent `--type` — it does not exist.**

**New:** Scripts now support `--date-range`, `--sort`, `--limit` for filtering, sorting, limiting.

## Runtime Assumptions

- Agent discovers skill path reading this file. Use absolute path as `<skill_dir>`.
- Execute from shell tool supporting working directory.
- **Agentic systems:** Use `python3 -m pip install "requests>=2.28.0"` (pip comes pre-installed).
- **Local/dev:** `uv run ...` also works after fixing `pyproject.toml` dependency-groups.
- For strict command guards, prefer `working_dir` + filename-only commands.

## Setup (One-Time)

**Agentic systems:** Use `python3 -m pip` (pip comes pre-installed).
**Local/dev:** `uv` also works (`uv run ...`) after fixing `pyproject.toml` dependency-groups.

Container sets `PYTHONUSERBASE`, `PIP_USER=1`, `PIP_BREAK_SYSTEM_PACKAGES=1` so pip installs to writable workspace.

```yaml
command: python3 -m pip install "requests>=2.28.0"
working_dir: <skill_dir>
```

> Do NOT use `python3 -m venv` or `source .venv/bin/activate` in non-interactive shells.
> If install fails, report exact error + stop — do not try multiple install variants.

## Workflow

Copy checklist + track progress:

```
Smart Money Run:
- [ ] 1) Install deps (if first run or dep error)
- [ ] 2) Run requested tracker mode
- [ ] 3) Confirm report files produced
- [ ] 4) Summarize key findings from generated report
```

### 1) Install deps (if needed)

```yaml
command: python3 -m pip install "requests>=2.28.0"
working_dir: <skill_dir>
```

### 2) Run tracker mode

Two entrypoint styles are supported. **Prefer the `scripts/` wrappers** (they're the standard skill-format entrypoints and work from any cwd). Use the package entrypoints only when you need to import internals or run pytest.

**Recommended (scripts/ wrappers):**

All commands below work from the skill root directory. The wrappers add `src/` to `sys.path` and call the underlying entrypoint.

```text
All trackers (fast):        python3 scripts/smart_money.py --fast-13f
13F only (recommended):    python3 scripts/smart_money.py --13f-only --fast-13f
13F only (full whale set):  python3 scripts/smart_money.py --13f-only
Congress only (recommended): python3 scripts/smart_money.py --congress-only
Skip House Reps:            python3 scripts/smart_money.py --no-house-reps --fast-13f
Verify sources only:        python3 scripts/source_audit.py
Congress member filter:     python3 scripts/congress.py --member "Nancy Pelosi" --days 90
Congress party/chamber:     python3 scripts/congress.py --party Republican --chamber Senate
House Reps member filter:   python3 scripts/house_reps.py --member "Nancy Pelosi" --days 90
Date range filter:          python3 scripts/smart_money.py --date-range 2026-01-01,2026-03-31
Sort by date:               python3 scripts/congress.py --sort datedesc
Limit results:              python3 scripts/congress.py --limit 10
```

**Package entrypoints (advanced):**

Set `working_dir` to `<skill_dir>/src/smart_money_tracker` + use filename-only commands. Use this style only when you need direct access to the importable package (e.g. inside a test).

```text
python3 main.py --13f-only --fast-13f
python3 congress.py --member "Nancy Pelosi" --days 90
python3 house_reps.py --member "Nancy Pelosi" --days 90
```

**Important:** Scripts support these CLI args:

- `scripts/smart_money.py` (wraps `main.py`): `--13f-only`, `--congress-only`, `--no-house-reps`, `--fast-13f`, `--verify-sources`, `--force-download`, `--days`, `--member`, `--party`, `--chamber`, `--date-range`, `--sort`, `--limit`
- `scripts/congress.py`: `--member`, `--days`, `--party`, `--chamber`, `--date-range`, `--sort`, `--limit`, `--force-download`
- `sec13f.py`: library only (no CLI). Configure 13F behavior via `main.py` flags (`--fast-13f`, `--13f-only`, `--date-range`, `--sort`, `--limit`) — `use_top_100` is a Python param on `run_13f_tracker()`, not a CLI flag.
- `scripts/house_reps.py`: `--member`, `--days`, `--party`, `--date-range`, `--sort`, `--limit`

**Date range format:** `YYYY-MM-DD,YYYY-MM-DD` (e.g., `2026-01-01,2026-03-31`). Overrides `--days` when provided.

**Sort options:** `dateasc` (oldest first) or `datedesc` (newest first).

**Limit:** Positive integer specifying max results to return.

**Troubleshooting:**

1. **Congress API returns 404**: Script auto-resolves correct Next.js build-id. If fails, uses cached `data/congress/congress-trades.json`.
2. **Agent runtime timeout**: Use `--fast-13f` flag for 13F-only or all-trackers mode.
3. **"No such file or directory"**: Ensure `working_dir` is `<skill_dir>/src/smart_money_tracker`, not root.
4. **LLM generates wrong tool calls**: Ignore any `--type`, `--date_range` args — they don't exist.

**Congress API fallback:** Static URL `https://www.insiderfinance.io/_next/data/congress-trades.json` requires `x-nextjs-data: 1` header + Next.js build-id. If 404, script resolves build-id from page HTML (3 patterns: `/data/`, `/static/`, `__NEXT_DATA__`). If all fail, falls back to cached `data/congress/congress-trades.json`.

**Caching:** Congress trades cached daily. If cache from today, use immediately (skip API). If stale, try API then fallback to cache.

### 3) Validate outputs

Read reports from `<skill_dir>/reports/`:

- `latest.md` (combined latest)
- `smart-money-YYYY-MM-DD.md` (dated combined)
- `13f-report-YYYY-MM-DD.md`
- `congress-report-YYYY-MM-DD.md`
- `house-reps-YYYY-MM-DD.md`
- `source-verification-latest.json` (source inventory + verification evidence)
- `source-discrepancies-latest.md` (discrepancy summary + open questions)

Validation loop:

- If expected report files missing, rerun once.
- If rerun fails, return exact tool error + stop (do not fabricate analysis).
- If `--verify-sources` is used, response must cite both verification artifact files when they exist.

### 4) Respond to user

- Summarize top findings (new positions, conviction, net volume, convergence/divergence).
- State report date + mode used.
- If execution failed, report failure clearly + include relevant error.

Response contract (always follow):

- `Mode used`: one of `all`, `13f-only`, `congress-only`, `custom-filter`.
- `Reports read`: list exact report filenames used.
- `Key findings`: concise bullets with numbers (top increases/decreases, conviction, net volume).
- `Execution status`: `success` or `failed` with exact error text when failed.

When `--verify-sources` runs, also include:

- `Verification artifacts`: exact filenames for JSON + markdown discrepancy output
- `Verification summary`: concise bullets with verified sources, discrepancies, and open questions

If user asks "top 5 increased/decreased", compute from generated report data + return both lists in descending order.

## Guardrails

- `command` must not contain path separators for script execution (use `main.py`, not `src/smart_money_tracker/main.py`).
- Always set `working_dir` to `<skill_dir>/src/smart_money_tracker` for script execution.
- For this skill, do not call `web_search` as primary data path; use local tracker scripts + generated reports.
- `exec` tool arguments must be valid JSON with only `command` and `working_dir` (do not include malformed nested JSON strings).
- Do not append unsupported flags (e.g., `--timeout`) to tracker commands.
- Do not use heredoc (`<<EOF`) or temp script writes in `/tmp` for this skill.
- Do not claim results unless tool output confirms successful execution.
- If `--verify-sources` fails, report the exact failure and do not infer verification results from stale reports.
- Treat InsiderFinance as the congress runtime source of truth unless the user explicitly changes that product-level source decision; if verification finds multiple plausible authorities, ask the user instead of switching sources silently.
- Keep paths Unix-style with forward slashes.

## Data Sources

| Source                | Coverage                | Update    | Auth              |
| --------------------- | ----------------------- | --------- | ----------------- |
| SEC EDGAR 13F         | 30 institutional whales | Quarterly | None (User-Agent) |
| InsiderFinance.io API | Congress trades         | Daily     | None (User-Agent) |
| House Clerk FD Search | House Rep disclosures   | Daily     | None              |

## Default Tracked

**13F Whales (30):** Berkshire Hathaway, Bridgewater, Pershing Square, Soros Fund, ARK Invest, + 25 more (see `sec13f.py`).

**Congress:** All active House and Senate members with PTR disclosures.

## Technical Notes

- SEC EDGAR: 150ms rate limit between requests
- InsiderFinance.io: `https://www.insiderfinance.io/_next/data/congress-trades.json`
- House Clerk: `https://disclosures-clerk.house.gov/`
- Caches stored in `data/` (13F: quarterly, Congress: daily, House Reps: quarterly)
- Net Volume = Purchase Volume - Sales Volume (BULLISH/BEARISH)
- Whale Conviction = % of whales holding a stock

## Companion Skills

- `daily-market-watch` (same repo) — for current macro tape / Fed signals to ground any "why are they buying this?" question.
- `thematic-stock-picker` (same repo) — for theme-driven baskets; use the smart-money signal as a corroborating data point in Section C of the picker.

## Examples

A canonical output structure lives at `examples/sample-report.md`, with a guide to the real-data output format at `examples/README.md`. When this skill is the only one the user needs, the report's **Convergence Signals** section is the value-add — that's where whale + congressman overlap gets flagged.
