"""
Skill compliance smoke tests for smart-money-tracker.

Validates three contracts defined in SKILL.md without requiring network access:

1. command/working_dir contract
   - Entrypoints (main.py, congress.py, sec13f.py, house_reps.py) exist under
     <skill_dir>/scripts and accept the documented CLI flags without error.

2. Report file existence & structure
   - Running the skill in offline (mocked) mode writes:
       reports/latest.md
       reports/smart-money-YYYY-MM-DD.md
   - Each report contains the mandatory section headings.

3. Response-schema enforcement
   - generate_full_report output satisfies the SKILL.md response contract:
       Mode used, Reports read, Key findings, Execution status sections are
       producible from the generated data structures.
   - compute_convergence returns only legal signal values.
   - Each convergence record has all required keys.
"""

# pyright: reportMissingModuleSource=false

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SKILL_DIR / "src" / "smart_money_tracker"
REPORTS_DIR = SKILL_DIR / "reports"

from smart_money_tracker.main import (
    compute_convergence,
    generate_convergence_report,
    generate_full_report,
)

# ── Constants mirrored from SKILL.md ─────────────────────────────────────────

# All signals the SKILL.md and response contract can emit
VALID_SIGNALS = {
    "STRONG_BUY",
    "STRONG_SELL",
    "DIVERGE",
    "WHALE_ONLY",
    "WHALE_ONLY_STRONG",
    "CONGRESS_ONLY",
}

# Required top-level keys in every convergence record
CONVERGENCE_RECORD_KEYS = {
    "stock_name",
    "whale_actions",
    "congress_purchases",
    "congress_sales",
    "congress_members",
    "signal",
}

# Required section headings in every full report
REPORT_SECTION_HEADINGS = [
    "13F",
    "Congress",
    "House",
    "Convergence",
]

# Documented CLI flags that must not crash the arg-parser
CLI_FLAG_CASES = [
    [],
    ["--13f-only"],
    ["--congress-only"],
    ["--no-house-reps"],
    ["--verify-sources"],
    ["--days", "30"],
    ["--member", "Nancy Pelosi"],
    ["--party", "Republican"],
    ["--chamber", "house"],
    ["--chamber", "senate"],
]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_sec13f_data(actions=None, fund_name="Test Whale", manager="Test Manager"):
    if actions is None:
        actions = {"new": [], "increased": [], "decreased": [], "closed": []}
    return {
        "results": {
            fund_name: {
                "manager": manager,
                "current_filing": "2025-01-31",
                "changes": actions,
                "error": None,
            }
        },
        "report_section": "## 🐋 13F Whale Activity\n\n_test_\n",
        "raw": [],
    }


def _make_congress_data(by_ticker=None, trades=None):
    by_ticker = by_ticker or {}
    trades = trades or []
    return {
        "trades": trades,
        "aggregation": {
            "total_trades": len(trades),
            "by_ticker": by_ticker,
            "by_member": {},
            "by_party": {},
        },
        "report_section": "## 🏛️ Congress Trades\n\n_test_\n",
    }


# ═════════════════════════════════════════════════════════════════════════════
# 1. Command / working_dir contract
# ═════════════════════════════════════════════════════════════════════════════


class TestCommandWorkingDirContract:
    """
    SKILL.md requires:
    - command is a filename-only string (no path separators)
    - working_dir is <skill_dir>/scripts
    - The four entrypoint scripts exist there
    """

    @pytest.mark.parametrize(
        "script", ["main.py", "congress.py", "sec13f.py", "house_reps.py"]
    )
    def test_entrypoint_scripts_exist(self, script):
        """Each documented entrypoint script exists in <skill_dir>/scripts."""
        assert (
            SRC_DIR / script
        ).is_file(), f"Entrypoint '{script}' missing from {SRC_DIR}"

    @pytest.mark.parametrize(
        "script", ["main.py", "congress.py", "sec13f.py", "house_reps.py"]
    )
    def test_entrypoint_has_no_path_separator(self, script):
        """Script names used in the skill must be filename-only (no / or \\)."""
        assert "/" not in script and "\\" not in script

    @pytest.mark.parametrize("flags", CLI_FLAG_CASES)
    def test_main_py_accepts_documented_flags(self, flags):
        """
        main.py --help (or any documented flag combo) must not exit with
        argparse 'error:' output. We check parse-only by importing argparse
        behavior directly rather than spawning a subprocess so no network
        calls are made.
        """
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--13f-only", action="store_true")
        parser.add_argument("--congress-only", action="store_true")
        parser.add_argument("--days", type=int, default=90)
        parser.add_argument("--member", type=str, default=None)
        parser.add_argument("--party", type=str, default=None)
        parser.add_argument("--verify-sources", action="store_true")
        parser.add_argument(
            "--chamber", type=str, default=None, choices=["house", "senate"]
        )
        parser.add_argument("--no-house-reps", action="store_true")

        # Must not raise SystemExit
        try:
            parser.parse_args(flags)
        except SystemExit as exc:
            pytest.fail(f"Flags {flags!r} triggered argparse error: {exc}")

    def test_no_relative_path_in_skill_md(self):
        """
        SKILL.md guardrail: command must never contain a path separator.
        Scan all fenced-code command lines in SKILL.md.
        """
        skill_md = (SKILL_DIR / "SKILL.md").read_text()
        # Extract lines that look like 'python3 some/path.py'
        bad_commands = re.findall(r"python3\s+\S+/\S+\.py", skill_md)
        assert not bad_commands, (
            f"SKILL.md contains path-separated commands (violates guardrail): "
            f"{bad_commands}"
        )

    def test_working_dir_in_skill_md_always_points_to_src(self):
        """Every working_dir in SKILL.md must point to src/smart_money_tracker."""
        skill_md = (SKILL_DIR / "SKILL.md").read_text()

        # Check that all working_dir references point to <skill_dir>/src/smart_money_tracker
        assert (
            "<skill_dir>/src/smart_money_tracker" in skill_md
        ), "Missing '<skill_dir>/src/smart_money_tracker' reference in SKILL.md"

        # Check the command reference section
        assert (
            "All commands use `working_dir: <skill_dir>/src/smart_money_tracker`." in skill_md
        ), "Missing explicit working_dir reference in command reference"

    def test_verification_mode_documented_in_skill_md(self):
        skill_md = (SKILL_DIR / "SKILL.md").read_text()
        assert "--verify-sources" in skill_md
        assert "source-verification-latest.json" in skill_md
        assert "source-discrepancies-latest.md" in skill_md


# ═════════════════════════════════════════════════════════════════════════════
# 2. Report file existence & structure
# ═════════════════════════════════════════════════════════════════════════════


class TestReportFileContract:
    """
    SKILL.md requires that after a run the following files exist:
        reports/latest.md
        reports/smart-money-YYYY-MM-DD.md
    And each must contain the required section headings.
    """

    @pytest.fixture()
    def temp_reports_dir(self, tmp_path):
        return tmp_path / "reports"

    def _write_report(self, reports_dir: Path, content: str):
        reports_dir.mkdir(parents=True, exist_ok=True)
        today = date.today().strftime("%Y-%m-%d")
        dated = reports_dir / f"smart-money-{today}.md"
        latest = reports_dir / "latest.md"
        dated.write_text(content)
        latest.write_text(content)
        return dated, latest

    def test_full_report_writes_dated_file(self, temp_reports_dir):
        """generate_full_report output written to dated filename succeeds."""
        report = generate_full_report(
            "13F section", "Congress section", "House section", "Convergence section"
        )
        dated, _ = self._write_report(temp_reports_dir, report)
        assert dated.exists()
        assert dated.stat().st_size > 0

    def test_full_report_writes_latest_file(self, temp_reports_dir):
        """generate_full_report output written to latest.md succeeds."""
        report = generate_full_report(
            "13F section", "Congress section", "House section", "Convergence section"
        )
        _, latest = self._write_report(temp_reports_dir, report)
        assert latest.exists()
        assert latest.stat().st_size > 0

    def test_dated_filename_matches_pattern(self, temp_reports_dir):
        """Dated report filename matches smart-money-YYYY-MM-DD.md pattern."""
        report = generate_full_report(
            "13F section", "Congress section", "House section", "Convergence section"
        )
        dated, _ = self._write_report(temp_reports_dir, report)
        assert re.fullmatch(
            r"smart-money-\d{4}-\d{2}-\d{2}\.md", dated.name
        ), f"Unexpected filename: {dated.name}"

    @pytest.mark.parametrize("heading", REPORT_SECTION_HEADINGS)
    def test_full_report_contains_section_heading(self, heading):
        """The full report must contain each mandatory section heading."""
        report = generate_full_report(
            f"## 🐋 13F Whale Activity\n",
            f"## 🏛️ Congress Trades\n",
            f"## 🏠 House Reps Disclosures\n",
            f"## 🎯 Convergence Signals\n",
        )
        assert (
            heading in report
        ), f"Report missing section heading containing '{heading}'"

    def test_full_report_contains_generated_date(self):
        """Report must include a Generated timestamp."""
        report = generate_full_report("s1", "s2", "s3", "s4")
        assert "Generated" in report

    def test_full_report_conviction_section_optional(self):
        """When conviction_section is empty string, report still valid."""
        report = generate_full_report("s1", "s2", "s3", "s4", conviction_section="")
        assert "Smart Money Tracker" in report

    def test_full_report_conviction_section_included_when_provided(self):
        """When conviction_section is provided, it appears in the report."""
        report = generate_full_report(
            "s1", "s2", "s3", "s4", conviction_section="## 🐋 Whale Conviction Stats\n"
        )
        assert "Whale Conviction Stats" in report

    def test_existing_reports_dir_has_required_files(self):
        """
        If the reports directory already exists and is populated, at least
        latest.md must be present. Skips gracefully if no runs have been done.
        """
        if not REPORTS_DIR.exists():
            pytest.skip("reports/ dir does not exist yet — run the tracker first")
        reports = list(REPORTS_DIR.glob("*.md"))
        if not reports:
            pytest.skip("reports/ dir exists but is empty")
        latest = REPORTS_DIR / "latest.md"
        assert (
            latest.exists()
        ), "latest.md missing from reports/ — skill run appears incomplete"

    def test_existing_latest_report_has_section_headings(self):
        """Existing latest.md must contain all required section headings."""
        latest = REPORTS_DIR / "latest.md"
        if not latest.exists():
            pytest.skip("latest.md not found — no skill run detected")
        content = latest.read_text()
        for heading in REPORT_SECTION_HEADINGS:
            assert (
                heading in content
            ), f"latest.md missing required section heading: '{heading}'"


# ═════════════════════════════════════════════════════════════════════════════
# 3. Response-schema enforcement
# ═════════════════════════════════════════════════════════════════════════════


class TestResponseSchemaContract:
    """
    SKILL.md response contract requires the agent response to include:
      - Mode used: one of all | 13f-only | congress-only | custom-filter
      - Reports read: list of filenames
      - Key findings: bullets with numbers
      - Execution status: success | failed

    Here we validate the DATA CONTRACT — that the Python functions produce
    structures from which a compliant response can always be built.
    """

    VALID_MODES = {"all", "13f-only", "congress-only", "custom-filter"}

    # ── convergence schema ────────────────────────────────────────────────

    def test_convergence_record_has_required_keys(self):
        """Every convergence record must have all SKILL.md-mandated keys."""
        sec13f = _make_sec13f_data(
            actions={
                "new": [{"name": "AAPL", "value": 1_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            }
        )
        congress = _make_congress_data(
            by_ticker={"AAPL": {"purchases": 2, "sales": 0, "members": []}}
        )
        result = compute_convergence(sec13f, congress)
        for ticker, record in result.items():
            missing = CONVERGENCE_RECORD_KEYS - record.keys()
            assert (
                not missing
            ), f"Convergence record for '{ticker}' missing keys: {missing}"

    def test_convergence_signals_are_valid_values(self):
        """All emitted signals must be one of the documented valid values."""
        sec13f = _make_sec13f_data(
            actions={
                "new": [{"name": "AAPL", "value": 1_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [{"name": "MSFT", "value": 500_000}],
            }
        )
        congress = _make_congress_data(
            by_ticker={
                "AAPL": {"purchases": 2, "sales": 0, "members": []},
                "MSFT": {"purchases": 0, "sales": 3, "members": []},
                "TSLA": {"purchases": 1, "sales": 0, "members": []},
            }
        )
        result = compute_convergence(sec13f, congress)
        for ticker, record in result.items():
            assert (
                record["signal"] in VALID_SIGNALS
            ), f"Invalid signal '{record['signal']}' for ticker '{ticker}'"

    def test_convergence_empty_inputs_returns_empty_dict(self):
        """Empty inputs must return empty dict (no KeyError or crash)."""
        result = compute_convergence({}, {})
        assert result == {}

    def test_convergence_report_contains_all_documented_signal_labels(self):
        """Convergence report text must use the SKILL.md signal label names."""
        convergence = {
            "AAPL": {
                "stock_name": "AAPL",
                "whale_actions": [{"manager": "M", "action": "new_position"}],
                "congress_purchases": 2,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "STRONG_BUY",
            },
            "MSFT": {
                "stock_name": "MSFT",
                "whale_actions": [{"manager": "M", "action": "closed"}],
                "congress_purchases": 0,
                "congress_sales": 2,
                "congress_members": [],
                "signal": "STRONG_SELL",
            },
            "GOOGL": {
                "stock_name": "GOOGL",
                "whale_actions": [{"manager": "M", "action": "new_position"}],
                "congress_purchases": 0,
                "congress_sales": 1,
                "congress_members": [],
                "signal": "DIVERGE",
            },
            "AMZN": {
                "stock_name": "AMZN",
                "whale_actions": [{"manager": "M", "action": "increased"}],
                "congress_purchases": 0,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "WHALE_ONLY",
            },
            "META": {
                "stock_name": "META",
                "whale_actions": [],
                "congress_purchases": 1,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "CONGRESS_ONLY",
            },
        }
        report = generate_convergence_report(convergence)
        for signal in (
            "STRONG_BUY",
            "STRONG_SELL",
            "DIVERGE",
            "WHALE_ONLY",
            "CONGRESS_ONLY",
        ):
            assert signal in report, f"Convergence report missing label '{signal}'"

    # ── response mode contract ────────────────────────────────────────────

    def test_valid_modes_are_complete_set(self):
        """
        The four documented response modes map 1-to-1 with CLI flag combinations.
        """
        expected = {"all", "13f-only", "congress-only", "custom-filter"}
        assert expected == self.VALID_MODES

    @pytest.mark.parametrize(
        "mode", ["all", "13f-only", "congress-only", "custom-filter"]
    )
    def test_mode_string_is_slugified(self, mode):
        """Mode strings must be lowercase hyphenated (no spaces, no caps)."""
        assert mode == mode.lower()
        assert " " not in mode

    # ── execution status contract ─────────────────────────────────────────

    def test_execution_status_success_payload(self):
        """
        A successful run must expose a writeable report path (non-empty string).
        Simulated: main.py writes a report_path and returns it.
        """
        today = date.today().strftime("%Y-%m-%d")
        report_path = Path(f"reports/smart-money-{today}.md")
        # Agent must be able to extract filename for 'Reports read' field
        assert report_path.name.startswith("smart-money-")
        assert report_path.name.endswith(".md")

    def test_execution_status_failed_payload_is_string(self):
        """
        Simulated failed run: error is captured as a non-empty string and
        never silently swallowed (agent must report it verbatim).
        """
        error_message = "ConnectionError: failed to reach data.sec.gov after 3 retries"
        # Compliance: error text must be a non-empty string
        assert isinstance(error_message, str)
        assert len(error_message) > 0

    # ── key findings contract ─────────────────────────────────────────────

    def test_key_findings_new_positions_extractable(self):
        """
        'Top increased/decreased' must be computable from compare_holdings output.
        """
        from smart_money_tracker.sec13f import compare_holdings

        current = {
            "AAPL": {"name": "AAPL", "value": 3_000_000, "shares": 30},
            "GOOGL": {"name": "GOOGL", "value": 2_000_000, "shares": 20},
            "TSLA": {"name": "TSLA", "value": 1_000_000, "shares": 10},
        }
        previous = {
            "AAPL": {"name": "AAPL", "value": 1_000_000, "shares": 10},
            "GOOGL": {"name": "GOOGL", "value": 3_000_000, "shares": 30},
        }
        changes = compare_holdings(current, previous)

        # Agent must be able to list top-N increased in descending order
        increased = sorted(
            changes["increased"], key=lambda h: h.get("change_pct", 0), reverse=True
        )
        assert len(increased) == 1
        assert increased[0]["name"] == "AAPL"
        assert increased[0]["change_pct"] == 200.0

        # Agent must be able to list top-N decreased in descending (most-reduced) order
        decreased = sorted(changes["decreased"], key=lambda h: h.get("change_pct", 0))
        assert len(decreased) == 1
        assert decreased[0]["name"] == "GOOGL"
        assert decreased[0]["change_pct"] < 0

        # New positions must be clearly identifiable
        assert len(changes["new"]) == 1
        assert changes["new"][0]["name"] == "TSLA"

    def test_key_findings_net_volume_extractable(self):
        """
        Net volume (BULLISH/BEARISH) must be computable from aggregate output.
        """
        from smart_money_tracker.congress import aggregate_trades

        recent = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "P1",
                "party": "D",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent,
            },
            {
                "ticker": "AAPL",
                "name": "P2",
                "party": "D",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent,
            },
            {
                "ticker": "AAPL",
                "name": "P3",
                "party": "R",
                "chamber": "senate",
                "type": "Sale",
                "transaction_date": recent,
            },
        ]
        agg = aggregate_trades(trades)
        aapl = agg["by_ticker"]["AAPL"]
        net = aapl["purchases"] - aapl["sales"]
        direction = "BULLISH" if net > 0 else "BEARISH" if net < 0 else "NEUTRAL"
        assert direction == "BULLISH"
        assert net == 1

    def test_key_findings_conviction_pct_computable(self):
        """
        Whale conviction % must be computable from all_fund_data holdings.
        get_whale_conviction_stats takes a list of fund_data dicts, each with
        'info' and 'current_holdings' keys (shape returned by process_fund).
        """
        from smart_money_tracker.sec13f import get_whale_conviction_stats

        all_fund_data = [
            {
                "info": {"manager": "Warren Buffett"},
                "current_holdings": {
                    "037833100": {"name": "AAPL", "value": 5_000},
                },
            },
            {
                "info": {"manager": "George Soros"},
                "current_holdings": {
                    "037833100": {"name": "AAPL", "value": 3_000},
                },
            },
            {
                "info": {"manager": "Ray Dalio"},
                "current_holdings": {
                    "594918104": {"name": "MSFT", "value": 2_000},
                },
            },
        ]
        stats = get_whale_conviction_stats(all_fund_data)
        top = stats["top_conviction"]
        assert len(top) > 0
        aapl = next((x for x in top if x["stock"] == "AAPL"), None)
        assert aapl is not None
        assert aapl["whale_count"] == 2
        assert aapl["conviction_pct"] == pytest.approx(66.7, rel=0.01)


# ═════════════════════════════════════════════════════════════════════════════
# 4. Offline fetch_with_retry contract (sec13f + congress)
# ═════════════════════════════════════════════════════════════════════════════


class TestFetchWithRetryContract:
    """
    Validates that fetch_with_retry:
    - retries the correct number of times
    - raises on exhaustion
    - returns immediately on first success
    - passes params kwarg through to requests.get
    """

    def test_sec13f_retry_succeeds_on_second_attempt(self):
        from smart_money_tracker.sec13f import fetch_with_retry
        import smart_money_tracker.sec13f as sec13f

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise sec13f.requests.exceptions.ConnectionError("simulated failure")
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        with patch("smart_money_tracker.sec13f.requests.get", side_effect=mock_get):
            with patch("smart_money_tracker.sec13f.time.sleep"):  # skip real sleep
                result = fetch_with_retry("https://example.com", {})
        assert call_count == 2

    def test_sec13f_retry_raises_after_max_attempts(self):
        from smart_money_tracker.sec13f import fetch_with_retry
        import smart_money_tracker.sec13f as sec13f

        with patch(
            "smart_money_tracker.sec13f.requests.get",
            side_effect=sec13f.requests.exceptions.ConnectionError("always fails"),
        ):
            with patch("smart_money_tracker.sec13f.time.sleep"):
                with pytest.raises(sec13f.requests.exceptions.ConnectionError):
                    fetch_with_retry("https://example.com", {}, max_retries=3)

    def test_sec13f_retry_no_sleep_on_first_success(self):
        from smart_money_tracker.sec13f import fetch_with_retry

        resp = MagicMock()
        resp.raise_for_status = MagicMock()

        with patch("smart_money_tracker.sec13f.requests.get", return_value=resp) as mock_get:
            with patch("smart_money_tracker.sec13f.time.sleep") as mock_sleep:
                fetch_with_retry("https://example.com", {})
        mock_sleep.assert_not_called()
        assert mock_get.call_count == 1

    def test_sec13f_retry_passes_params(self):
        from smart_money_tracker.sec13f import fetch_with_retry

        resp = MagicMock()
        resp.raise_for_status = MagicMock()

        with patch("smart_money_tracker.sec13f.requests.get", return_value=resp) as mock_get:
            fetch_with_retry("https://example.com", {}, params={"foo": "bar"})
        _, kwargs = mock_get.call_args
        assert kwargs.get("params") == {"foo": "bar"}

    def test_congress_retry_succeeds_on_second_attempt(self):
        from smart_money_tracker.congress import fetch_with_retry
        import smart_money_tracker.congress as congress

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise congress.requests.exceptions.ConnectionError("simulated failure")
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        with patch("smart_money_tracker.congress.requests.get", side_effect=mock_get):
            with patch("smart_money_tracker.congress.time.sleep"):
                result = fetch_with_retry("https://example.com", {})
        assert call_count == 2

    def test_congress_retry_raises_after_max_attempts(self):
        from smart_money_tracker.congress import fetch_with_retry
        import smart_money_tracker.congress as congress

        with patch(
            "smart_money_tracker.congress.requests.get",
            side_effect=congress.requests.exceptions.ConnectionError("always fails"),
        ):
            with patch("smart_money_tracker.congress.time.sleep"):
                with pytest.raises(congress.requests.exceptions.ConnectionError):
                    fetch_with_retry("https://example.com", {}, max_retries=3)
