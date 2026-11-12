# Feed Registry — verification notes

All feeds in `feeds.json` were HTTP-tested and XML-parsed live on
**2026-08-08**. This file records what passed, what was rejected, and
the quirks to know before adding a feed.

## Verified working (seeded)

| Feed | URL | Notes |
| --- | --- | --- |
| NPR News / Business | `feeds.npr.org/1001|1014/rss.xml` | Solid, frequent updates |
| CNBC Top News | `cnbc.com/id/100003114/device/rss/rss.html` | Works; item id = link URL |
| WSJ Markets | `feeds.a.dj.com/rss/RSSMarketsMain.xml` | Works (no auth needed for RSS) |
| MarketWatch Top / MarketPulse | `feeds.content.dowjones.io/public/rss/mw_*` | Works |
| Yahoo Finance (symbol) | `feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US` | URL-encode `^` as `%5E` in config |
| SEC Press Releases | `sec.gov/news/pressreleases.rss` | **Requires browser-like User-Agent** — SEC blocks generic bots (403). Script sends one. |
| Fed Press | `federalreserve.gov/feeds/press_all.xml` | Works |
| SCMP News (4) / Business (91) | `scmp.com/rss/<id>/feed` | Works; guid = article URL |
| CGTN World | `cgtn.com/subscribe/rss/section/world.xml` | Works |
| Xinhua English | `xinhuanet.com/english/rss/worldrss.xml` | **HTTP only** — script follows it. Slow updates. |
| Google News editions/topics | `news.google.com/rss?hl=..&gl=..&ceid=..` | High churn → cap 15/poll. Topic sections: WORLD, BUSINESS, TECHNOLOGY, SCIENCE, HEALTH, ENTERTAINMENT, SPORTS, NATION. |
| CNA Latest | `channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml` | Works. Category param (`&category=1062`) ignored → returns main feed. Use Google News SG Business for SG business. |
| Straits Times | `straitstimes.com/news/singapore/rss.xml` | Works. `straitstimes.com/rss.xml` also works. |
| Business Times SG | `businesstimes.com.sg/rss.xml` | Works |
| BBC World / Business | `feeds.bbci.co.uk/news/{world,business}/rss.xml` | Works |
| Guardian World / Business | `theguardian.com/{world,business}/rss` | Works |
| FT | `ft.com/news-feed?format=rss` | Works |
| Investing.com | `investing.com/rss/news_25.rss` (top), `news_1.rss` (realtime) | Works |
| CoinDesk | `coindesk.com/arc/outboundfeeds/rss/` | Works |
| Cointelegraph | `cointelegraph.com/rss` | Works |
| arXiv RSS | `arxiv.org/rss/<cat>` | **Empty on weekends** (skipDays Sat/Sun); daily updates ~00:00 ET. q-fin.ST/EC/TR/PM/MF/RM/GN, econ.GN, cs.AI all live. Redirects to export.arxiv.org. |

## Tested and rejected

| Feed | Result | Why |
| --- | --- | --- |
| AP Top News | 404 | `apnews.com/feed` dead; AP killed public RSS |
| Politico | 403 | Blocks non-browser agents |
| White House | 404 | `whitehouse.gov/feed/` dead |
| Treasury press | 404 | `home.treasury.gov/news/press-releases/rss` dead |
| China Daily | parse error | Malformed XML (unclosed CDATA) — script retries with CDATA strip but feed remains unreliable; prefer CGTN/Xinhua/SCMP |
| Caixin Global | 403 | Blocks agents (paywall-ish). Use SCMP + Google News CN |
| MAS (SG central bank) | HTML page | `mas.gov.sg/rss.xml` returns an 850KB HTML page, not RSS. MAS has no working RSS — use Google News SG search for "MAS" or CNA Business |
| gov.sg | 404 | No RSS |
| Reddit r/economics | 429 | Rate-limited even with browser UA; r/worldnews worked once, then 429. Unreliable → not seeded |
| Google News topic MARKETS | HTML | Section doesn't exist in RSS form — redirects to news.google.com/home. Use topic/BUSINESS |
| Straits Times Business | 404 | `straitstimes.com/business/rss.xml` dead — ST only exposes section-level feeds via the main URL |

## Quirks cheat-sheet

- **SEC**: User-Agent must look like a browser. The script's UA handles it; `curl` without `-A` gets 403.
- **arXiv**: weekend-empty feeds are not errors. Don't report "feed broken" on Sat/Sun; report "no new papers (arXiv updates weekdays)".
- **Xinhua**: HTTP (not HTTPS). If the environment blocks plain HTTP, disable `xinhua_english`.
- **Google News**: geolocates to the `gl`/`ceid` you pass, not your IP — that's the point: US/CN/SG editions stay stable regardless of where the machine runs.
- **Redirects**: arXiv, MarketWatch, and several others 302 to canonical hosts. The script follows redirects (urllib default).
- **Malformed feeds**: the parser strips namespaces, tolerates broken CDATA, and isolates failures per feed. A feed that fails twice in a row should be reported to the user and replaced via `--action add` + disable in feeds.json.

## How to vet a new feed (before adding)

1. `curl -s -A "Mozilla/5.0" -o /tmp/f.xml "<url>"` then check it parses:
   `python3 -c "import xml.etree.ElementTree as ET; ET.parse('/tmp/f.xml')"`
2. Check the first item has a stable guid/link (dedup key).
3. `python scripts/watch_feeds.py --action check` after adding.
4. If the feed is high-churn, add `"max_per_poll": 15` to its entry.
