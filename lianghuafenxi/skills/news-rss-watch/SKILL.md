---
name: news-rss-watch
description: >-
  Polls a seeded, deterministic RSS/Atom feed registry covering US news,
  China news, Singapore news, global market news, important/world news, and
  arXiv research feeds — with per-feed watermark dedup so each run surfaces
  ONLY new items. Use whenever the user asks to "check the news", "poll
  feeds", "what's new since yesterday", "morning news digest", "watch this
  feed", "seed/track RSS feeds", wants a comprehensive US+China+Singapore
  news outlook, or wants new arXiv papers on a finance/ML topic watched.
  Triggers on phrases like "news RSS", "add this feed", "what's new in the
  feeds", "daily news brief", "track arxiv papers on X". This is the
  deterministic data layer — pair with `daily-market-watch` when the user
  wants a synthesized, source-cited market report rather than raw new items.
---

# news-rss-watch

Deterministic, seedable news feed watcher. Polls a config-driven feed
registry (`feeds.json`) with watermark dedup — each run emits only items
published since the last run, as strict JSON. No LLM interpretation in
the fetch loop: the agent runs the script and renders the output.

## Works with any agent

This skill is agent-agnostic by construction:

- **Pure CLI + JSON contract.** The scripts take flags, print strict
  JSON/markdown to stdout, and exit with a status code. No agent
  framework APIs, no tool hooks, no environment variables beyond
  `NEWS_WATCHER_STATE_DIR` / `NEWS_WATCHER_DIGEST_DIR` (both optional).
- **Only needs a shell.** Any agent with a terminal tool (Claude Code,
  Codex, Cursor, OpenCode, Gemini CLI, plain cron, a human) can drive
  it — the SKILL.md is instructions for whatever agent is running it.
- **Stdlib-only Python.** No pip installs, no virtualenv, no network
  calls beyond fetching the feeds themselves.
- **Deterministic output.** Identical inputs → identical JSON, so any
  agent parses the same contract. The skill never depends on the
  agent's memory or prior turns.

## When to use

- "Check the news" / "what's new since yesterday" / "poll the feeds"
- "Daily news digest" for US + China + Singapore + markets + world
- "Add this feed / track this website" — deterministic `--action add`
- "What feeds are you tracking?" — `--action list`
- "Watch arXiv for new papers on <topic>" — `scripts/watch_arxiv.py`
- Any cron / scheduled briefing job: run the script, parse JSON, stay
  silent when the item count is 0.

## Mental model

1. `feeds.json` — the seed registry. Pre-seeded with **live-verified**
   feeds (checked 2026-08-08). Agent never edits feeds by hand; it uses
   `--action add` / `--action list` so the registry stays deterministic.
2. `scripts/watch_feeds.py` — batch poller. One command, all feeds,
   one JSON result. Per-feed isolation: a broken feed is reported in
   `errors`, never crashes the batch.
3. Watermark state — `~/.finance-skills/watcher-state/newsrss_<id>.json`
   (override with `NEWS_WATCHER_STATE_DIR`). First run = baseline:
   records IDs, emits nothing. This prevents flooding the agent's
   context with old articles on the first poll.
4. `scripts/watch_arxiv.py` — same pattern against the arXiv Atom API
   (one-shot arXiv search turned into a watcher).

## Feed registry (seeded categories)

| Category | Focus | Seed feeds |
| --- | --- | --- |
| `us` | US news + policy + regulators | NPR, CNBC, WSJ Markets, SEC press, Fed press, Google News US |
| `china` | China news (first-party + HK) | SCMP news/business, CGTN, Xinhua English, Google News CN (zh) |
| `singapore` | SG local news + markets | CNA, Straits Times, Business Times SG, Google News SG, SG business topic |
| `markets` | Global market news | MarketWatch, Yahoo Finance, FT, BBC Business, Investing.com, CoinDesk, Cointelegraph, Google Business |
| `important` | World / headline news | BBC World, Guardian World/Business, Google News World |
| `research` | arXiv finance + AI | q-fin.ST/EC/TR/PM/MF/RM/GN, econ.GN, cs.AI (weekday-only updates) |

Region-source rule (mirrors ADR-002): China category uses Chinese
first-party / HK sources (Xinhua, CGTN, SCMP) — not US outlets covering
China. Singapore uses local outlets only. See
`references/feed-registry.md` for verification notes and feeds that
were tested and rejected (dead, paywalled, rate-limited).

## Workflow

```
News poll run:
- [ ] 1) Pick scope: all categories, or --categories us,china,...
- [ ] 2) Run: python scripts/watch_feeds.py [--categories ...] [--max N] [--budget N]
- [ ] 3) Parse the JSON. count == 0 → reply "No new updates." Do NOT fabricate news.
- [ ] 4) Render stories grouped by category, with title + URL + score.
- [ ] 5) On user request, synthesize: use daily-market-watch for the full report.
```

### Polling (the default action)

```bash
python scripts/watch_feeds.py
# → JSON: {"count": N, "first_run": bool, "results": [{category, clusters: [...]}], "errors": [...]}
```

Clustering is ON by default (anti-noise): the same story picked up by N
feeds becomes ONE story. Each cluster:

```json
{
  "cluster_id": 0, "score": 3.5, "matched_keywords": ["fed", "cpi"],
  "category": "markets", "feed_id": "marketwatch_top",
  "feed_name": "MarketWatch Top Stories",
  "cluster_size": 2, "other_sources": ["Google News Business"],
  "items": [{"id", "title", "url", "summary", "published"}]
}
```

- **score** = source weight (3 = regulator/first-party, 2 = major outlet,
  1 = aggregator) + 0.5 per importance keyword hit (fed, cpi, tariff,
  mas, pboc, war, earnings, …). Sort by score when rendering.
- **Attribution**: the highest-weight source wins the category + link;
  `other_sources` lists the rest. A China story covered by Xinhua + BBC
  stays in `china`, not `important`.
- **Budget**: `--budget N` caps stories per category (default 8,
  `0` = unlimited).

Behavior flags:

- First ever run records a baseline and returns `count: 0` with
  `first_run: true` — tell the user the watcher is primed, then re-run
  (or use `--fresh` for a full digest).
- `--categories us,markets` — scope to one or more categories.
- `--fresh` — emit everything, ignoring watermarks (still records state
  so the next normal poll stays quiet).
- `--max 15` — per-feed cap (Google News feeds default to 15).
- `--with-summary` — include a ≤500-char summary snippet per item.
- `--no-cluster` — flat per-feed view (debugging single feeds; no dedup).
- `--format markdown` — machine-shaped markdown for cron delivery.

### Daily digest (cron-friendly)

```bash
python scripts/watch_feeds.py --action digest --max 5 --budget 5
# → writes ~/.finance-skills/digests/news-digest-YYYY-MM-DD.md (override
#   dir with NEWS_WATCHER_DIGEST_DIR), prints {"digest": path, "stories": N}
```

Fresh full poll → cluster → per-category markdown file. Zero LLM needed:
point a nightly cron at it and ship the file to your inbox/channel.

### Adding a feed (deterministic, no file editing)

```bash
python scripts/watch_feeds.py --action add --name "my_feed" --url "https://example.com/rss" --category us
```

Validation: `--category` must be one of
`us, china, singapore, markets, important, research`. Duplicate
url/id → hard error, no mutation.

### Search-as-feed (gap filler)

```bash
# Any topic/outlet Google News can cover — e.g. MAS has no RSS:
python scripts/watch_feeds.py --action add-search \
  --query "MAS Singapore monetary policy" --category singapore \
  --hl en-SG --gl SG --ceid SG:en
```

Builds a Google News search RSS feed and adds it like any other feed.
Region-scoped via `--hl/--gl/--ceid` (defaults en-US/US/US:en).

### Checking / resetting

```bash
python scripts/watch_feeds.py --action list                 # show registry
python scripts/watch_feeds.py --action check                # verify every feed URL + XML
python scripts/watch_feeds.py --action reset --feed-id cna_main   # clear one watermark
python scripts/watch_feeds.py --action reset                # clear all watermarks
```

### Watching arXiv topics (research category)

```bash
python scripts/watch_arxiv.py --query "cat:q-fin.ST AND agent" --name qfin_agents
python scripts/watch_arxiv.py --query "ti:LLM trading" --max 5
python scripts/watch_arxiv.py --query "all:deep learning volatility" --fresh
```

Each run emits only papers new since the last run (watermark keyed on
arXiv id). Exactly 1 API request per run — safe for cron. Supports the
full arXiv query syntax (`all:`, `ti:`, `abs:`, `au:`, `cat:`, AND/OR).

## Guardrails

- **Never fabricate news.** If `count` is 0, respond with no-new-updates.
  If a feed errored, report it from `errors` — never substitute another
  feed's items.
- **Never edit `feeds.json` by hand.** Use `--action add` / `add-search`.
  This keeps state deterministic and auditable.
- **Never rename a feed id mid-stream.** The watermark is keyed on the
  id; renaming resets dedup and floods context with old items.
- **First-run semantics are a feature.** Baseline recording prevents
  replay. Use `--fresh` only when the user explicitly wants a full
  digest.
- **Clustering is deterministic, not editorial.** Two stories are merged
  only when title tokens overlap ≥60% after stopword/outlet stripping.
  Do not hand-merge or hand-split clusters when rendering; show what
  the script emits. If clustering looks wrong (over-merge of distinct
  stories), report it — the threshold lives in the script.
- **Score is a sort key, not a verdict.** Higher score = more keywords +
  more authoritative source. Render in score order but never drop a
  story the user asked about just because it scored low.
- **Per-feed failure ≠ batch failure.** One dead feed goes to `errors`;
  the rest still poll. Report errors to the user, don't retry endlessly
  (respect HTTP 429 by backing off — the next scheduled poll retries).
- **High-churn feeds are capped.** Google News feeds emit dozens of
  items; `max_per_poll` in feeds.json caps them at 15, `--budget` caps
  stories per category.
- **Don't re-order or re-parse feeds yourself.** The script is the
  single source of truth; if a feed breaks, run `--action check`.

## Tests

```bash
python3 -m unittest discover -s skills/news-rss-watch/tests
```

27 offline tests: RSS/Atom parsing (incl. malformed-CDATA repair), title
normalization, clustering, importance scoring, budget caps, watermark
baseline/dedup/corruption, feed-add validation, search-URL building,
digest writing, arXiv Atom parsing. No network needed.

## Companion skills

- `daily-market-watch` — when the user wants a synthesized, source-cited
  market report (6 sections, region zoom) instead of raw new items: poll
  first with this skill, then hand the new items to daily-market-watch
  as the news layer.
- `smart-money-tracker` — when a news item mentions a 13F/STOCK Act
  filing, cross-check with the tracker.

## References

- `references/feed-registry.md` — how feeds were verified, what was
  rejected and why, notes on flaky feeds (arXiv weekend silence, SEC
  User-Agent requirement, Reddit rate limits, MAS has no working RSS).
- `feeds.json` — the live seed registry (edit via `--action add` only).

## Example

- `examples/sample-report.md` — a real clustered poll run (all 5 news
  categories, scores, dedup evidence). Golden output for the eval set;
  use it as the shape reference when rendering.
- `examples/sample-digest.md` — a real nightly digest file
  (`--action digest`). Use as the shape reference for cron delivery.
