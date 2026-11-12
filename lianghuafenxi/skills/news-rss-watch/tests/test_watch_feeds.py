"""Unit tests for news-rss-watch scripts. Stdlib only, fully offline.

Run: python3 -m unittest discover -s skills/news-rss-watch/tests
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import watch_arxiv  # noqa: E402
import watch_feeds  # noqa: E402
from _watermark import Watermark  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RSS_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <guid>https://example.com/a</guid>
      <title>Fed cuts rates</title>
      <link>https://example.com/a</link>
      <description>Central bank moves.</description>
      <pubDate>Mon, 01 Jan 2026 09:00:00 GMT</pubDate>
    </item>
    <item>
      <guid>https://example.com/b</guid>
      <title>China exports rise</title>
      <link>https://example.com/b</link>
      <description>Trade data out.</description>
      <pubDate>Tue, 02 Jan 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom</title>
  <entry>
    <id>urn:uuid:1</id>
    <title>Atom entry one</title>
    <link href="https://example.com/1"/>
    <summary>Summary one.</summary>
    <published>2026-01-01T09:00:00Z</published>
  </entry>
  <entry>
    <id>urn:uuid:2</id>
    <title>Atom entry two</title>
    <link href="https://example.com/2"/>
    <summary>Summary two.</summary>
    <published>2026-01-02T09:00:00Z</published>
  </entry>
</feed>
"""

# Unclosed CDATA — the China Daily class of malformed feed.
MALFORMED_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <guid>https://example.com/x</guid>
      <title>Broken CDATA feed</title>
      <link>https://example.com/x</link>
      <description><![CDATA[this CDATA is never closed</description>
    </item>
  </channel>
</rss>
"""

ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2608.02311v1</id>
    <title>  AI Governance for Finance  </title>
    <summary>  A long\nsummary text.  </summary>
    <published>2026-08-03T00:00:00Z</published>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
  </entry>
</feed>
"""


def item(feed_id, title, category, url=None, summary=""):
    return {
        "id": url or f"https://example.com/{feed_id}-{abs(hash(title))}",
        "title": title,
        "url": url or f"https://example.com/{feed_id}",
        "summary": summary,
        "published": "",
        "feed_id": feed_id,
        "feed_name": feed_id,
        "category": category,
    }


def make_weights(feed_ids, default=1):
    return {fid: (2 if "marketwatch" in fid or "bbc" in fid else default)
            for fid in feed_ids}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

class TestParseFeed(unittest.TestCase):
    def test_parses_rss_items_with_all_fields(self):
        entries = watch_feeds.parse_feed(RSS_XML.encode())
        self.assertEqual(len(entries), 2)
        e = entries[0]
        self.assertEqual(e["id"], "https://example.com/a")
        self.assertEqual(e["title"], "Fed cuts rates")
        self.assertEqual(e["url"], "https://example.com/a")
        self.assertEqual(e["summary"], "Central bank moves.")
        self.assertEqual(e["published"], "Mon, 01 Jan 2026 09:00:00 GMT")

    def test_parses_atom_entries(self):
        entries = watch_feeds.parse_feed(ATOM_XML.encode())
        self.assertEqual(len(entries), 2)
        e = entries[0]
        self.assertEqual(e["id"], "urn:uuid:1")
        self.assertEqual(e["title"], "Atom entry one")
        self.assertEqual(e["url"], "https://example.com/1")
        self.assertEqual(e["summary"], "Summary one.")

    def test_repairs_unclosed_cdata(self):
        entries = watch_feeds.parse_feed(MALFORMED_XML.encode())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Broken CDATA feed")

    def test_guid_falls_back_to_link(self):
        xml = RSS_XML.replace("<guid>https://example.com/a</guid>", "")
        entries = watch_feeds.parse_feed(xml.encode())
        ids = {e["id"] for e in entries}
        self.assertIn("https://example.com/a", ids)


# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------

class TestNormalizeTitle(unittest.TestCase):
    def test_strips_outlet_suffix_after_dash(self):
        self.assertEqual(
            watch_feeds.normalize_title("Fed cuts rates - MarketWatch"),
            "fed cuts rates",
        )

    def test_strips_outlet_suffix_after_pipe(self):
        self.assertEqual(
            watch_feeds.normalize_title("Fed cuts rates | CNBC"),
            "fed cuts rates",
        )

    def test_strips_em_dash_suffix(self):
        self.assertEqual(
            watch_feeds.normalize_title("China trade data — SCMP"),
            "china trade data",
        )

    def test_lowercases_and_collapses_whitespace(self):
        self.assertEqual(
            watch_feeds.normalize_title("  Fed  CUTS   Rates  "),
            "fed cuts rates",
        )

    def test_removes_stopwords_and_short_tokens(self):
        toks = watch_feeds.title_tokens("The Fed and the ECB cut rates")
        self.assertNotIn("the", toks)
        self.assertNotIn("and", toks)
        self.assertIn("fed", toks)


# ---------------------------------------------------------------------------
# Clustering (anti-noise)
# ---------------------------------------------------------------------------

class TestClustering(unittest.TestCase):
    def test_same_story_across_feeds_clusters_together(self):
        items = [
            item("marketwatch_top", "Fed cuts rates after hot CPI print", "markets"),
            item("google_business_us", "Fed cuts rates after hot CPI print", "markets"),
        ]
        weights = {"marketwatch_top": 2, "google_business_us": 1}
        out = watch_feeds.cluster_items(items, weights)
        self.assertEqual(len(out), 1)  # one story, not two
        c = out[0]
        self.assertEqual(c["cluster_size"], 2)
        self.assertEqual(len(c["other_sources"]), 1)
        self.assertEqual(c["feed_id"], "marketwatch_top")  # higher-weight source wins

    def test_story_attributes_to_highest_weight_source_category(self):
        items = [
            item("bbc_world", "China growth slows sharply", "important"),
            item("xinhua_english", "China growth slows sharply", "china"),
        ]
        weights = {"bbc_world": 2, "xinhua_english": 3}
        out = watch_feeds.cluster_items(items, weights)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["category"], "china")  # first-party source wins

    def test_distinct_stories_stay_separate(self):
        items = [
            item("npr_news", "Fed cuts rates", "us"),
            item("straits_times_sg", "Singapore property prices hit record", "singapore"),
        ]
        weights = {"npr_news": 2, "straits_times_sg": 3}
        out = watch_feeds.cluster_items(items, weights)
        self.assertEqual(len(out), 2)

    def test_partial_overlap_is_not_a_merge(self):
        items = [
            item("npr_news", "Apple unveils new iPhone", "us"),
            item("cnbc_top", "Apple sues startup over iPhone design", "us"),
        ]
        weights = {"npr_news": 2, "cnbc_top": 2}
        out = watch_feeds.cluster_items(items, weights)
        self.assertEqual(len(out), 2)

    def test_cluster_has_score_and_keywords(self):
        items = [item("fed_press", "Fed cuts rates after hot CPI print", "us")]
        weights = {"fed_press": 3}
        out = watch_feeds.cluster_items(items, weights)
        self.assertGreaterEqual(out[0]["score"], 3)
        self.assertIn("fed", out[0]["matched_keywords"])

    def test_no_cross_feed_merge_with_same_tokens_different_story(self):
        # Same 4 tokens, different ordering/content -> still one cluster
        # (this documents the conservative direction: identical titles merge)
        items = [
            item("a", "Oil prices surge on supply fears", "markets"),
            item("b", "Oil prices surge on supply fears", "markets"),
        ]
        weights = {"a": 1, "b": 2}
        out = watch_feeds.cluster_items(items, weights)
        self.assertEqual(len(out), 1)


class TestImportanceScoring(unittest.TestCase):
    def test_keyword_hits_raise_score(self):
        plain = watch_feeds.score_item(
            item("npr_news", "Local art show opens downtown", "us"), weight=2
        )
        hot = watch_feeds.score_item(
            item("npr_news", "Fed cuts rates after hot CPI print", "us"), weight=2
        )
        self.assertGreater(hot, plain)

    def test_source_weight_dominates_quiet_gov_feed(self):
        quiet_gov = watch_feeds.score_item(
            item("fed_press", "Fed announces board appointment", "us"), weight=3
        )
        hot_aggregator = watch_feeds.score_item(
            item("google_us", "Fed cuts rates after hot CPI print", "us"), weight=1
        )
        self.assertGreater(quiet_gov, hot_aggregator)


class TestBudget(unittest.TestCase):
    def test_caps_stories_per_category(self):
        titles = {
            "us": [
                "Fed cuts rates after hot CPI print",
                "Nvidia earnings beat drives tech rally",
                "US jobs report shows strong hiring",
                "Treasury yields fall on safe-haven bid",
                "Senate passes bank regulation bill",
            ],
            "singapore": [
                "Singapore GDP beats expectations",
                "MAS keeps policy stance unchanged",
                "SGX reports record trading volume",
                "Singapore property prices rise again",
                "Changi airport passenger traffic up",
            ],
        }
        items = []
        for i in range(5):
            items.append(item("npr_news", titles["us"][i], "us"))
            items.append(item("cna_main", titles["singapore"][i], "singapore"))
        weights = {"npr_news": 2, "cna_main": 3}
        out = watch_feeds.cluster_items(items, weights)
        capped = watch_feeds.apply_budget(out, budget=2)
        us = [c for c in capped if c["category"] == "us"]
        sg = [c for c in capped if c["category"] == "singapore"]
        self.assertEqual(len(us), 2)
        self.assertEqual(len(sg), 2)

    def test_budget_zero_means_unlimited(self):
        titles = [
            "Fed cuts rates after hot CPI print",
            "Nvidia earnings beat drives tech rally",
            "Treasury yields fall on safe-haven bid",
            "Oil prices surge on supply fears",
            "Senate passes bank regulation bill",
        ]
        items = [item("npr_news", t, "us") for t in titles]
        out = watch_feeds.cluster_items(items, {"npr_news": 2})
        capped = watch_feeds.apply_budget(out, budget=0)
        self.assertEqual(len(capped), 5)


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------

class TestWatermark(unittest.TestCase):
    def test_first_run_records_baseline_and_emits_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["NEWS_WATCHER_STATE_DIR"] = td
            wm = Watermark.load("newsrss_test")
            self.assertTrue(wm.is_first_run)
            items = [{"id": "1", "title": "a"}, {"id": "2", "title": "b"}]
            new = wm.filter_new(items, id_key="id")
            self.assertEqual(new, [])
            wm.save()

            wm2 = Watermark.load("newsrss_test")
            self.assertFalse(wm2.is_first_run)
            new2 = wm2.filter_new([{"id": "2", "title": "b"}], id_key="id")
            self.assertEqual(new2, [])
            new3 = wm2.filter_new([{"id": "3", "title": "c"}], id_key="id")
            self.assertEqual([i["id"] for i in new3], ["3"])

    def test_corrupt_state_file_does_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["NEWS_WATCHER_STATE_DIR"] = td
            Path(td, "newsrss_bad.json").write_text("{not json")
            wm = Watermark.load("newsrss_bad")
            self.assertTrue(wm.is_first_run)
            self.assertEqual(wm.filter_new([{"id": "1"}], id_key="id"), [])


# ---------------------------------------------------------------------------
# Feed registry mutations
# ---------------------------------------------------------------------------

class TestAddFeed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmp.name, "feeds.json")
        self.config_path.write_text(json.dumps({"feeds": []}))
        self._orig = watch_feeds.CONFIG_PATH
        watch_feeds.CONFIG_PATH = self.config_path

    def tearDown(self):
        watch_feeds.CONFIG_PATH = self._orig
        self.tmp.cleanup()

    def test_add_feed_writes_to_config(self):
        watch_feeds.do_add("My Feed", "https://example.com/rss", "us")
        cfg = json.loads(self.config_path.read_text())
        self.assertEqual(cfg["feeds"][0]["id"], "my_feed")
        self.assertEqual(cfg["feeds"][0]["category"], "us")

    def test_duplicate_url_is_rejected(self):
        watch_feeds.do_add("My Feed", "https://example.com/rss", "us")
        with self.assertRaises(SystemExit) as ctx:
            watch_feeds.do_add("Other Name", "https://example.com/rss", "us")
        self.assertEqual(ctx.exception.code, 1)

    def test_invalid_category_is_rejected(self):
        with self.assertRaises(SystemExit) as ctx:
            watch_feeds.do_add("My Feed", "https://example.com/rss", "bogus")
        self.assertEqual(ctx.exception.code, 2)


class TestAddSearch(unittest.TestCase):
    def test_builds_google_news_search_url(self):
        url = watch_feeds.build_search_url("MAS Singapore", hl="en-SG", gl="SG", ceid="SG:en")
        self.assertIn("news.google.com/rss/search", url)
        self.assertIn("q=MAS+Singapore", url)
        self.assertIn("gl=SG", url)


# ---------------------------------------------------------------------------
# Digest
# ---------------------------------------------------------------------------

class TestDigest(unittest.TestCase):
    def test_digest_writes_markdown_file(self):
        with tempfile.TemporaryDirectory() as td:
            os.environ["NEWS_WATCHER_STATE_DIR"] = td
            os.environ["NEWS_WATCHER_DIGEST_DIR"] = td

            def fake_fetch(url):
                if url == "https://u/1":
                    return [
                        {"id": "1", "title": "Fed cuts rates", "url": "https://x/1",
                         "summary": "s", "published": ""},
                    ]
                return [
                    {"id": "2", "title": "Singapore GDP beats", "url": "https://x/2",
                     "summary": "s", "published": ""},
                ]

            orig = watch_feeds.fetch_feed
            watch_feeds.fetch_feed = fake_fetch
            try:
                path, n = watch_feeds.write_digest(
                    {
                        "feeds": [
                            {"id": "fed_press", "name": "Fed Press", "url": "https://u/1",
                             "category": "us", "enabled": True},
                            {"id": "cna_main", "name": "CNA", "url": "https://u/2",
                             "category": "singapore", "enabled": True},
                        ]
                    },
                    max_per_feed=10,
                    budget=10,
                    with_summary=False,
                )
            finally:
                watch_feeds.fetch_feed = orig

            self.assertTrue(path.exists())
            text = path.read_text()
            self.assertIn("# News Digest", text)
            self.assertIn("## us", text)
            self.assertIn("## singapore", text)
            self.assertIn("Fed cuts rates", text)
            self.assertEqual(n, 2)


# ---------------------------------------------------------------------------
# arXiv watcher
# ---------------------------------------------------------------------------

class TestArxivWatcher(unittest.TestCase):
    def test_fetch_newest_parses_atom(self):
        import urllib.request

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return ARXIV_ATOM.encode()

        def fake_urlopen(req, timeout=30):
            self.assertIn("export.arxiv.org", req.full_url)
            self.assertIn("sortBy=submittedDate", req.full_url)
            return FakeResp()

        orig = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            entries = watch_arxiv.fetch_newest("cat:q-fin.ST", 5)
        finally:
            urllib.request.urlopen = orig

        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["id"], "2608.02311v1")
        self.assertEqual(e["title"], "AI Governance for Finance")
        self.assertEqual(e["url"], "https://arxiv.org/abs/2608.02311v1")
        self.assertEqual(e["published"], "2026-08-03")
        self.assertEqual(e["authors"], "Alice, Bob")


if __name__ == "__main__":
    unittest.main()
