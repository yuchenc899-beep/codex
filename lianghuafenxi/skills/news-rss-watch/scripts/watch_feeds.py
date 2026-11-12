#!/usr/bin/env python3
"""Deterministic batch RSS/Atom watcher for news-rss-watch.

Reads feeds.json (same directory), polls every enabled feed once, diffs
against per-feed watermarks, and prints ONE aggregated result to stdout.

Design rules (see SKILL.md):
- No LLM in the loop: output is strict JSON (or markdown), never prose.
- Per-feed isolation: one broken feed cannot fail the batch.
- First run = baseline: records IDs, emits nothing (no replay).
- Empty stdout/empty items = silent. Callers treat that as no-news.

Usage:
  poll (default):    python watch_feeds.py [--categories us,markets] [--max N] [--fresh] [--format json|markdown] [--with-summary]
  add:               python watch_feeds.py --action add --name <id> --url <url> --category <cat>
  list:              python watch_feeds.py --action list
  check:             python watch_feeds.py --action check [--categories ...]   # validate feed URLs + XML
  reset:             python watch_feeds.py --action reset [feed_id]            # clear watermark(s)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _watermark import Watermark, format_items_as_markdown  # type: ignore

VALID_CATEGORIES = {"us", "china", "singapore", "markets", "important", "research"}
CONFIG_PATH = Path(__file__).resolve().parent.parent / "feeds.json"
USER_AGENT = "Mozilla/5.0 (finance-skills news-rss-watch/1.0; feed validator)"
FETCH_TIMEOUT = 15.0
MAX_BYTES = 1_500_000

# --- anti-noise clustering config (deterministic, no LLM) ---
# Higher weight = more authoritative source. Wins cluster representation.
SOURCE_WEIGHTS = {
    # regulators / first-party / local outlets: 3
    "fed_press": 3, "sec_press": 3,
    "cna_main": 3, "straits_times_sg": 3, "businesstimes_sg": 3,
    "scmp_news": 3, "scmp_business": 3, "xinhua_english": 3, "cgtn_world": 3,
    # major outlets: 2
    "npr_news": 2, "cnbc_top": 2, "wsj_markets": 2,
    "marketwatch_top": 2, "marketwatch_pulse": 2, "yahoo_spx": 2,
    "bbc_business": 2, "bbc_world": 2,
    "guardian_world": 2, "guardian_business": 2, "ft_feed": 2,
    "investing_top": 2, "investing_realtime": 2,
    "coindesk": 2, "cointelegraph": 2,
    # google news aggregators: 1 (default)
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on",
    "for", "with", "as", "at", "by", "from", "is", "are", "was",
    "were", "be", "has", "have", "had", "it", "its", "this", "that",
    "says", "say", "said", "after", "before", "over", "under", "amid",
    "vs", "per", "into", "top", "will", "could", "would",
}

# Importance keywords — a story touching any of these scores higher and
# surfaces above pure noise. Keep market/policy/geopolitics-leaning.
IMPORTANT_KEYWORDS = {
    "fed", "fomc", "pboc", "mas", "ecb", "boj", "cpi", "ppi", "gdp",
    "inflation", "tariff", "sanction", "rate", "rates", "recession",
    "stimulus", "debt", "deficit", "earnings", "ipo", "etf", "bond",
    "bonds", "yield", "stock", "stocks", "market", "markets", "oil",
    "gold", "dollar", "yuan", "renminbi", "trade", "export", "exports",
    "import", "semiconductor", "chip", "chips", "ai", "regulation",
    "fraud", "merger", "acquisition", "lawsuit", "bankruptcy", "default",
    "crash", "rally", "surge", "plunge", "war", "ceasefire", "election",
    "missile", "attack", "shutdown", "blackout", "scam", "scams",
}

_CLUSTER_SIM_THRESHOLD = 0.6

_OUTLET_SEP = re.compile(r"\s+(?:-{1,2}|—|–|\|)\s+")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"watch_feeds: config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"watch_feeds: invalid feeds.json: {e}", file=sys.stderr)
        sys.exit(2)


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _repair_cdata(xml_bytes: bytes) -> bytes:
    """Fix common malformed-CDATA feeds (e.g. China Daily) enough to parse."""
    try:
        return xml_bytes.decode("utf-8", errors="replace")
    except Exception:
        return xml_bytes.decode("latin-1", errors="replace")


def parse_feed(xml_bytes: bytes):
    """Return list of {id, title, url, summary, published} dicts.

    Handles RSS 2.0 <item> and Atom <entry>. Tolerant of malformed CDATA.
    """
    raw = _repair_cdata(xml_bytes)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        # Retry once with CDATA markers stripped — some feeds emit broken
        # CDATA (unclosed or nested). Text content survives the strip.
        cleaned = raw.replace("<![CDATA[", "").replace("]]>", "")
        try:
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            raise ValueError(f"invalid XML: {e}")

    entries = []
    for node in root.iter():
        tag = _strip_ns(node.tag)
        if tag not in {"item", "entry"}:
            continue
        children = {_strip_ns(c.tag): c for c in node}

        guid_el = children.get("guid")
        if guid_el is None:
            guid_el = children.get("id")
        link_el = children.get("link")
        if link_el is not None:
            href = link_el.attrib.get("href") or (link_el.text or "").strip()
        else:
            href = ""
        guid = (guid_el.text or "").strip() if guid_el is not None else ""
        guid = guid or href
        if not guid:
            continue

        title_el = children.get("title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        summ_el = children.get("description")
        if summ_el is None:
            summ_el = children.get("summary")
        summary = (summ_el.text or "").strip() if summ_el is not None else ""

        pub_el = children.get("pubDate")
        if pub_el is None:
            pub_el = children.get("published")
        published = (pub_el.text or "").strip() if pub_el is not None else ""

        entries.append(
            {"id": guid, "title": title, "url": href, "summary": summary,
             "published": published}
        )
    return entries


def fetch_feed(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        data = resp.read(MAX_BYTES)
        if len(data) >= MAX_BYTES:
            raise ValueError("feed exceeds 1.5MB safety cap")
        return parse_feed(data)


# --- anti-noise clustering (cross-feed dedup + importance scoring) ---

def title_tokens(title: str) -> list:
    """Significant tokens of a title: lowercase, punctuation stripped,
    stopwords and 1-2 char tokens removed."""
    if not title:
        return []
    return [
        w for w in re.split(r"\W+", title.lower())
        if w and w not in STOPWORDS and len(w) > 2
    ]


def normalize_title(title: str) -> str:
    """Canonical story title: lowercase, outlet suffix stripped, whitespace
    collapsed. "Fed Cuts Rates - MarketWatch" and "Fed Cuts Rates | CNBC"
    both normalize to "fed cuts rates"."""
    if not title:
        return ""
    t = title.strip().lower()
    t = _OUTLET_SEP.split(t)[0]
    return re.sub(r"\s+", " ", t).strip()


def _containment(a: list, b: list) -> float:
    """|A ∩ B| / min(|A|, |B|); 1.0 if identical, 0.0 if disjoint."""
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / min(len(sa), len(sb))


def score_item(item: dict, weight: int = 1) -> float:
    """Importance score = source weight + 0.5 per keyword hit."""
    toks = set(title_tokens(item.get("title", "")))
    hits = toks & IMPORTANT_KEYWORDS
    return float(weight) + 0.5 * len(hits)


def cluster_items(items: list, weights: dict = None) -> list:
    """Group items covering the same story into clusters.

    Deterministic greedy: items ordered by source weight (desc, stable),
    each joins the first cluster whose title-token containment ≥ 0.6.
    Returns cluster dicts:
      {cluster_id, order, category, feed_id, feed_name, score,
       cluster_size, other_sources, matched_keywords, items}
    The representative item is the highest-weight member; category comes
    from that member too (first-party/regulator sources win attribution).
    """
    weights = weights or {}
    ordered = sorted(
        enumerate(items),
        key=lambda p: -weights.get(p[1].get("feed_id"), 1),
    )
    clusters = []
    for idx, it in ordered:
        toks = title_tokens(it.get("title", ""))
        joined = None
        for c in clusters:
            if _containment(toks, c["_tokens"]) >= _CLUSTER_SIM_THRESHOLD:
                joined = c
                break
        if joined is None:
            joined = {"cluster_id": len(clusters), "_tokens": toks, "members": []}
            clusters.append(joined)
        joined["members"].append((idx, it))

    out = []
    for c in clusters:
        members = c["members"]
        _, rep = members[0]  # highest weight, stable order
        kw = set()
        for _, m in members:
            kw |= set(title_tokens(m.get("title", ""))) & IMPORTANT_KEYWORDS
        weight = weights.get(rep.get("feed_id"), 1)
        out.append(
            {
                "cluster_id": c["cluster_id"],
                "order": c["cluster_id"],
                "category": rep.get("category", "other"),
                "feed_id": rep.get("feed_id"),
                "feed_name": rep.get("feed_name", rep.get("feed_id")),
                "score": round(float(weight) + 0.5 * len(kw), 1),
                "cluster_size": len(members),
                "other_sources": [
                    m.get("feed_name", m.get("feed_id")) for _, m in members[1:]
                ],
                "matched_keywords": sorted(kw),
                "items": [rep],
            }
        )
    return out


def apply_budget(clusters: list, budget: int = 8) -> list:
    """Cap stories per category at `budget` (0 = unlimited), keeping the
    highest-scoring clusters (stable order breaks ties)."""
    if budget <= 0:
        return clusters
    by_cat = {}
    for c in clusters:
        by_cat.setdefault(c["category"], []).append(c)
    out = []
    for cat in by_cat:
        by_cat[cat].sort(key=lambda c: (-c["score"], c["order"]))
        out.extend(by_cat[cat][:budget])
    return out


def do_poll(config: dict, categories, max_per_feed, fresh, with_summary,
            cluster, budget) -> tuple:
    feeds = config.get("feeds", [])
    cat_set = set(categories) if categories else None
    errors, all_new, first_run_feeds = [], [], []

    for feed in feeds:
        fid = feed["id"]
        if not feed.get("enabled", True):
            continue
        if cat_set and feed.get("category") not in cat_set:
            continue
        try:
            entries = fetch_feed(feed["url"])
        except Exception as e:
            errors.append({"feed_id": fid, "error": f"{type(e).__name__}: {e}"})
            continue

        wm = Watermark.load(f"newsrss_{fid}")
        first_run = wm.is_first_run
        if fresh:
            new_items = list(entries)
            # still record everything so the next non-fresh poll stays quiet
            wm.filter_new(entries, id_key="id")
        else:
            new_items = wm.filter_new(entries, id_key="id")
        wm.save()

        cap = feed.get("max_per_poll") or max_per_feed
        if cap and cap > 0:
            new_items = new_items[:cap]

        if first_run:
            first_run_feeds.append(fid)
        for it in new_items:
            it["feed_id"] = fid
            it["feed_name"] = feed.get("name", fid)
            it["category"] = feed.get("category", "other")
            all_new.append(it)

    if not cluster:
        # per-feed grouping (flat view, no dedup)
        results = []
        for fid in first_run_feeds:
            results.append({"feed_id": fid, "first_run": True, "items": []})
        seen = set()
        for it in all_new:
            if it["feed_id"] not in seen:
                seen.add(it["feed_id"])
                results.append(
                    {
                        "feed_id": it["feed_id"],
                        "feed_name": it["feed_name"],
                        "category": it["category"],
                        "first_run": False,
                        "items": [
                            {k: v for k, v in x.items()
                             if k in ("id", "title", "url", "summary", "published")}
                            for x in all_new if x["feed_id"] == it["feed_id"]
                        ],
                    }
                )
        return results, errors, len(all_new), len(first_run_feeds) > 0

    # clustered view: group new items by category with dedup + scoring
    weights = {f["id"]: SOURCE_WEIGHTS.get(f["id"], 1) for f in feeds}
    clusters = cluster_items(all_new, weights)
    clusters = apply_budget(clusters, budget)
    by_cat = {}
    for c in clusters:
        by_cat.setdefault(c["category"], []).append(
            {k: v for k, v in c.items() if k != "order"}
        )
    results = [
        {"category": cat, "clusters": by_cat[cat]} for cat in sorted(by_cat)
    ]
    return results, errors, len(clusters), len(first_run_feeds) > 0


def build_search_url(query: str, hl: str, gl: str, ceid: str) -> str:
    """Google News search RSS — pseudo-feed for any topic/outlet gap
    (e.g. "MAS Singapore", "Caixin"). Deterministic, no scraping."""
    q = urllib.parse.quote(query).replace("%20", "+")
    return (f"https://news.google.com/rss/search?q={q}"
            f"&hl={hl}&gl={gl}&ceid={ceid}")


def do_add_search(query, category, hl, gl, ceid) -> None:
    url = build_search_url(query, hl, gl, ceid)
    name = query.strip()[:48]
    do_add(name, url, category)


def write_digest(config: dict, max_per_feed: int, budget: int,
                 with_summary: bool) -> tuple:
    """Full-fresh poll → cluster → per-category markdown digest file.
    Returns (path, story_count)."""
    import datetime
    from collections import defaultdict

    weights = {f["id"]: SOURCE_WEIGHTS.get(f["id"], 1) for f in config.get("feeds", [])}
    all_items, errors = [], []
    for feed in config.get("feeds", []):
        if not feed.get("enabled", True):
            continue
        try:
            entries = fetch_feed(feed["url"])
        except Exception as e:
            errors.append({"feed_id": feed["id"], "error": f"{type(e).__name__}: {e}"})
            continue
        cap = feed.get("max_per_poll") or max_per_feed
        if cap and cap > 0:
            entries = entries[:cap]
        for it in entries:
            it["feed_id"] = feed["id"]
            it["feed_name"] = feed.get("name", feed["id"])
            it["category"] = feed.get("category", "other")
            all_items.append(it)

    clusters = apply_budget(cluster_items(all_items, weights), budget)
    by_cat = defaultdict(list)
    for c in clusters:
        by_cat[c["category"]].append(c)

    today = datetime.date.today().isoformat()
    ddir = Path(os.environ.get("NEWS_WATCHER_DIGEST_DIR")
                or Path.home() / ".finance-skills" / "digests")
    ddir.mkdir(parents=True, exist_ok=True)
    path = ddir / f"news-digest-{today}.md"

    lines = [f"# News Digest — {today}", ""]
    for cat in sorted(by_cat):
        lines.append(f"## {cat}")
        for c in by_cat[cat]:
            rep = c["items"][0]
            lines.append(f"1. **{rep.get('title', '(no title)')}** "
                         f"({c['feed_name']}) — score {c['score']}")
            if rep.get("url"):
                lines.append(f"   {rep['url']}")
            if c["other_sources"]:
                lines.append(f"   also: {', '.join(c['other_sources'])}")
            if with_summary and rep.get("summary"):
                s = rep["summary"][:300].rstrip()
                lines.append(f"   > {s}")
            lines.append("")
        lines.append("")
    if errors:
        lines.append("## errors")
        for e in errors:
            lines.append(f"- {e['feed_id']}: {e['error']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path, len(clusters)


def do_add(name, url, category) -> None:
    if category not in VALID_CATEGORIES:
        print(f"watch_feeds: category must be one of {sorted(VALID_CATEGORIES)}",
              file=sys.stderr)
        sys.exit(2)
    config = load_config()
    fid = name.lower().replace(" ", "_").replace("-", "_")
    for f in config["feeds"]:
        if f["id"] == fid or f["url"] == url:
            print(f"watch_feeds: feed already exists: {f['id']}", file=sys.stderr)
            sys.exit(1)
    config["feeds"].append(
        {"id": fid, "name": name, "url": url, "category": category,
         "enabled": True}
    )
    save_config(config)
    print(json.dumps({"added": fid, "url": url, "category": category}, indent=2))


def do_list(config: dict) -> None:
    print(json.dumps(config, indent=2, ensure_ascii=False))


def do_check(config: dict, categories) -> int:
    feeds = config.get("feeds", [])
    cat_set = set(categories) if categories else None
    bad = 0
    for feed in feeds:
        if cat_set and feed.get("category") not in cat_set:
            continue
        try:
            entries = fetch_feed(feed["url"])
            print(f"OK   {feed['id']:24s} {len(entries):3d} items  {feed['url']}")
        except Exception as e:
            bad += 1
            print(f"FAIL {feed['id']:24s} {type(e).__name__}: {e}  {feed['url']}")
    return bad


def do_reset(feed_id: str | None) -> None:
    from _watermark import _state_dir
    sdir = _state_dir()
    if feed_id:
        p = sdir / f"newsrss_{feed_id}.json"
        if p.exists():
            p.unlink()
            print(f"reset {p}")
        else:
            print(f"watch_feeds: no state file for {feed_id}", file=sys.stderr)
            sys.exit(1)
    else:
        n = 0
        for p in sdir.glob("newsrss_*.json"):
            p.unlink()
            n += 1
        print(f"reset {n} state file(s)")


def main() -> int:
    import datetime

    p = argparse.ArgumentParser(description="Batch RSS/Atom watcher")
    p.add_argument("--action",
                   choices=["poll", "add", "add-search", "list", "check",
                            "reset", "digest"],
                   default="poll")
    p.add_argument("--name", help="feed id for --action add")
    p.add_argument("--url", help="feed URL for --action add")
    p.add_argument("--category", help="category for --action add / add-search")
    p.add_argument("--query", help="search query for --action add-search")
    p.add_argument("--hl", default="en-US", help="Google News language (add-search)")
    p.add_argument("--gl", default="US", help="Google News country (add-search)")
    p.add_argument("--ceid", default="US:en", help="Google News edition (add-search)")
    p.add_argument("--categories", help="comma-separated filter (poll/check/digest)")
    p.add_argument("--feed-id", help="feed id for --action reset")
    p.add_argument("--max", type=int, default=10, help="max items per feed (default 10)")
    p.add_argument("--budget", type=int, default=8,
                   help="max stories per category after clustering (0 = unlimited)")
    p.add_argument("--no-cluster", action="store_true",
                   help="disable cross-feed dedup; per-feed flat output")
    p.add_argument("--fresh", action="store_true",
                   help="emit everything, ignore watermark (still records it)")
    p.add_argument("--with-summary", action="store_true",
                   help="include summary snippet per item")
    p.add_argument("--format", choices=["json", "markdown"], default="json")
    args = p.parse_args()

    categories = [c.strip() for c in args.categories.split(",")] if args.categories else None

    if args.action == "add":
        if not (args.name and args.url and args.category):
            print("watch_feeds: --name --url --category required for add",
                  file=sys.stderr)
            return 2
        do_add(args.name, args.url, args.category)
        return 0

    if args.action == "add-search":
        if not (args.query and args.category):
            print("watch_feeds: --query --category required for add-search",
                  file=sys.stderr)
            return 2
        do_add_search(args.query, args.category, args.hl, args.gl, args.ceid)
        return 0

    if args.action == "list":
        do_list(load_config())
        return 0

    if args.action == "reset":
        do_reset(args.feed_id)
        return 0

    if args.action == "check":
        return do_check(load_config(), categories)

    config = load_config()

    if args.action == "digest":
        path, count = write_digest(
            config, max_per_feed=args.max, budget=args.budget,
            with_summary=args.with_summary,
        )
        print(json.dumps({"digest": str(path), "stories": count}, indent=2))
        return 0

    # poll
    results, errors, count, first_run = do_poll(
        config, categories, args.max, args.fresh, args.with_summary,
        cluster=not args.no_cluster, budget=args.budget,
    )

    payload = {
        "polled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": count,
        "first_run": first_run,
        "results": results,
        "errors": errors,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        md = []
        if args.no_cluster:
            for r in results:
                if r["first_run"] and not r["items"]:
                    continue
                md.append(f"# {r['feed_name']} ({r['category']})")
                md.append(format_items_as_markdown(
                    r["items"], body_key="summary" if args.with_summary else None
                ))
        else:
            for r in results:
                md.append(f"# {r['category']}")
                for c in r["clusters"]:
                    rep = c["items"][0]
                    md.append(f"## {rep.get('title', '(no title)')} — score {c['score']}")
                    if rep.get("url"):
                        md.append(rep["url"])
                    if c["other_sources"]:
                        md.append(f"(also: {', '.join(c['other_sources'])})")
                    if args.with_summary and rep.get("summary"):
                        md.append("")
                        md.append(rep["summary"][:500])
                    md.append("")
        if md:
            sys.stdout.write("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
