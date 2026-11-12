#!/usr/bin/env python3
"""Watch arXiv for NEW papers on a topic, using the arXiv Atom API.

The arXiv REST API (export.arxiv.org) is turned from a one-shot search
into a watcher: run repeatedly, and each run emits only papers
published since the last run. Watermark keyed on arXiv entry id
(e.g. 2402.03300).

Rate limit: arXiv asks ~1 req / 3s — this script makes exactly 1 request
per run, so it's safe on any cron.

Usage:
  python watch_arxiv.py --query "LLM trading agents" --name llm-trading [--max 10] [--fresh] [--format json|markdown]

  --query   arXiv search (supports all: / ti: / abs: / au: / cat: syntax)
  --name    watermark id (default: derived from query)
  --max     max new items to emit (default 10)
  --fresh   emit everything, ignore watermark (still records it)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _watermark import Watermark, format_items_as_markdown  # type: ignore

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def fetch_newest(query: str, max_results: int) -> list:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "finance-skills news-rss-watch/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    entries = []
    for entry in root.findall("a:entry", NS):
        arxiv_id = _text(entry.find("a:id", NS)).split("/abs/")[-1]
        title = re.sub(r"\s+", " ", _text(entry.find("a:title", NS)))
        published = _text(entry.find("a:published", NS))[:10]
        summary = re.sub(r"\s+", " ", _text(entry.find("a:summary", NS)))
        authors = ", ".join(
            _text(a.find("a:name", NS)) for a in entry.findall("a:author", NS)
        )
        entries.append(
            {
                "id": arxiv_id,
                "title": title,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "summary": summary,
                "published": published,
                "authors": authors,
            }
        )
    return entries


def main() -> int:
    p = argparse.ArgumentParser(description="Watch arXiv for new papers")
    p.add_argument("--query", required=True, help="arXiv search query")
    p.add_argument("--name", help="watermark id (default: derived from query)")
    p.add_argument("--max", type=int, default=10)
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--format", choices=["json", "markdown"], default="json")
    args = p.parse_args()

    name = args.name or re.sub(r"[^a-z0-9]+", "_", args.query.lower()).strip("_")
    wm = Watermark.load(f"arxiv_{name}")
    first_run = wm.is_first_run

    try:
        entries = fetch_newest(args.query, max(20, args.max * 2))
    except Exception as e:
        print(f"watch_arxiv: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if args.fresh:
        new_items = list(entries[: args.max])
        wm.filter_new(entries, id_key="id")  # record for future runs
    else:
        new_items = wm.filter_new(entries, id_key="id")[: args.max]
    wm.save()

    payload = {
        "query": args.query,
        "first_run": bool(first_run),
        "count": len(new_items),
        "items": new_items,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        out = format_items_as_markdown(
            new_items,
            body_key="summary",
        )
        if out:
            sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
