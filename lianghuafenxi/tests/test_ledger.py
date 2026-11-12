import unittest
from pathlib import Path
from sqlite3 import connect

from quant_app.ledger import import_archive, parse_archive, read_archive

ARCHIVE = Path(__file__).resolve().parents[1] / "自选与持仓清单_2026-11-11.md"


class LedgerTest(unittest.TestCase):
    def test_archive_preserves_source_dates_and_market_identity(self):
        archive = parse_archive(ARCHIVE.read_text(encoding="utf-8"))
        self.assertEqual(len(archive["positions"]), 16)
        self.assertEqual(len(archive["watchlist"]), 323)
        self.assertEqual(archive["positions_as_of"], "2026-10-23")
        self.assertEqual(archive["watchlist_as_of"], "2026-10-16")
        ids = {row["id"] for row in archive["positions"]}
        self.assertTrue({"HK:00384", "HK:00762", "SH:600050", "SH:588080"} <= ids)

    def test_same_archive_is_imported_once(self):
        with connect(":memory:") as db:
            import_archive(db, ARCHIVE)
            import_archive(db, ARCHIVE)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM archives").fetchone()[0], 1)
            self.assertEqual(len(read_archive(db)["watchlist"]), 323)
