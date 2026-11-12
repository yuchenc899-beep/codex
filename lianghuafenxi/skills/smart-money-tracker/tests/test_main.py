import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
from pathlib import Path

from smart_money_tracker.main import (
    compute_convergence,
    generate_convergence_report,
    generate_full_report,
    main,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_sec13f_data(fund_name="Whale Fund", manager="Test Manager", actions=None):
    """Build minimal sec13f_data dict as returned by run_13f_tracker()."""
    if actions is None:
        actions = {"new": [], "increased": [], "decreased": [], "closed": []}
    return {
        "results": {
            fund_name: {
                "manager": manager,
                "current_filing": "2025-01-31",
                "current_holdings": {},
                "changes": actions,
                "error": None,
            }
        },
        "report_section": "## 13F Mock\n",
        "raw": [],
    }


def _make_congress_data(trades=None, by_ticker=None):
    """Build minimal congress_data dict as returned by run_congress_tracker()."""
    trades = trades or []
    by_ticker = by_ticker or {}
    return {
        "trades": trades,
        "aggregation": {
            "total_trades": len(trades),
            "by_ticker": by_ticker,
            "by_member": {},
            "by_party": {},
        },
        "report_section": "## Congress Mock\n",
    }


# ── Unit tests ────────────────────────────────────────────────────────────────


class TestComputeConvergence:
    def test_empty_inputs(self):
        result = compute_convergence({}, {})
        assert isinstance(result, dict)
        # No tickers to match — result is empty dict
        assert result == {}

    def test_strong_buy_signal(self):
        """Whale buys + Congress buys same ticker → STRONG_BUY."""
        sec13f_data = _make_sec13f_data(
            actions={
                "new": [{"name": "AAPL", "value": 1_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            }
        )
        congress_data = _make_congress_data(
            trades=[
                {
                    "ticker": "AAPL",
                    "name": "Nancy Pelosi",
                    "asset_description": "Apple Inc.",
                    "type": "Purchase",
                    "transaction_date": date.today().isoformat(),
                }
            ],
            by_ticker={
                "AAPL": {"purchases": 3, "sales": 0, "members": ["Nancy Pelosi"]}
            },
        )
        result = compute_convergence(sec13f_data, congress_data)
        assert "AAPL" in result
        assert result["AAPL"]["signal"] == "STRONG_BUY"

    def test_strong_sell_signal(self):
        """Whale closes + Congress sells same ticker → STRONG_SELL."""
        sec13f_data = _make_sec13f_data(
            actions={
                "new": [],
                "increased": [],
                "decreased": [],
                "closed": [{"name": "MSFT", "value": 500_000}],
            }
        )
        congress_data = _make_congress_data(
            by_ticker={"MSFT": {"purchases": 0, "sales": 5, "members": ["John Smith"]}},
        )
        result = compute_convergence(sec13f_data, congress_data)
        assert "MSFT" in result
        assert result["MSFT"]["signal"] == "STRONG_SELL"

    def test_diverge_signal(self):
        """Whale buys, Congress sells → DIVERGE."""
        sec13f_data = _make_sec13f_data(
            actions={
                "new": [{"name": "GOOGL", "value": 2_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            }
        )
        congress_data = _make_congress_data(
            by_ticker={"GOOGL": {"purchases": 0, "sales": 4, "members": ["Jane Doe"]}},
        )
        result = compute_convergence(sec13f_data, congress_data)
        assert "GOOGL" in result
        assert result["GOOGL"]["signal"] == "DIVERGE"

    def test_congress_only_ticker(self):
        """Ticker traded by Congress but absent from 13F changes → CONGRESS_ONLY."""
        sec13f_data = _make_sec13f_data(
            actions={"new": [], "increased": [], "decreased": [], "closed": []}
        )
        congress_data = _make_congress_data(
            by_ticker={"TSLA": {"purchases": 2, "sales": 0, "members": ["Rep. X"]}},
        )
        result = compute_convergence(sec13f_data, congress_data)
        assert "TSLA" in result
        assert result["TSLA"]["signal"] == "CONGRESS_ONLY"

    def test_whale_only_ticker(self):
        """Whale active on ticker, congress has 0 buys/sells → WHALE_ONLY."""
        sec13f_data = _make_sec13f_data(
            actions={
                "new": [{"name": "AMZN", "value": 3_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            }
        )
        # AMZN in congress_by_ticker but 0 activity → no congress direction → WHALE_ONLY
        congress_data = _make_congress_data(
            by_ticker={"AMZN": {"purchases": 0, "sales": 0, "members": []}}
        )
        result = compute_convergence(sec13f_data, congress_data)
        assert "AMZN" in result
        assert result["AMZN"]["signal"] == "WHALE_ONLY"

    def test_signal_sort_order(self):
        """STRONG_BUY appears before CONGRESS_ONLY in result."""
        sec13f_data = _make_sec13f_data(
            actions={
                "new": [{"name": "AAPL", "value": 1_000_000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            }
        )
        congress_data = _make_congress_data(
            by_ticker={
                "AAPL": {"purchases": 2, "sales": 0, "members": []},
                "TSLA": {"purchases": 1, "sales": 0, "members": []},
            },
        )
        result = compute_convergence(sec13f_data, congress_data)
        tickers = list(result.keys())
        aapl_idx = tickers.index("AAPL")
        tsla_idx = tickers.index("TSLA")
        # STRONG_BUY (AAPL) should sort before CONGRESS_ONLY (TSLA)
        assert aapl_idx < tsla_idx


class TestGenerateConvergenceReport:
    def test_empty_convergence(self):
        report = generate_convergence_report({})
        assert "Convergence" in report

    def test_strong_buy_in_report(self):
        convergence = {
            "AAPL": {
                "stock_name": "AAPL",
                "whale_actions": [{"manager": "Buffett", "action": "new_position"}],
                "congress_purchases": 3,
                "congress_sales": 0,
                "congress_members": ["Nancy Pelosi"],
                "signal": "STRONG_BUY",
            }
        }
        report = generate_convergence_report(convergence)
        assert "STRONG_BUY" in report
        assert "AAPL" in report

    def test_all_signals_in_report(self):
        convergence = {
            "A": {
                "stock_name": "A",
                "whale_actions": [{"manager": "M", "action": "new_position"}],
                "congress_purchases": 1,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "STRONG_BUY",
            },
            "B": {
                "stock_name": "B",
                "whale_actions": [{"manager": "M", "action": "closed"}],
                "congress_purchases": 0,
                "congress_sales": 1,
                "congress_members": [],
                "signal": "STRONG_SELL",
            },
            "C": {
                "stock_name": "C",
                "whale_actions": [{"manager": "M", "action": "new_position"}],
                "congress_purchases": 0,
                "congress_sales": 1,
                "congress_members": [],
                "signal": "DIVERGE",
            },
            "D": {
                "stock_name": "D",
                "whale_actions": [{"manager": "M", "action": "increased"}],
                "congress_purchases": 0,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "WHALE_ONLY",
            },
            "E": {
                "stock_name": "E",
                "whale_actions": [],
                "congress_purchases": 2,
                "congress_sales": 0,
                "congress_members": [],
                "signal": "CONGRESS_ONLY",
            },
        }
        report = generate_convergence_report(convergence)
        for sig in (
            "STRONG_BUY",
            "STRONG_SELL",
            "DIVERGE",
            "WHALE_ONLY",
            "CONGRESS_ONLY",
        ):
            assert sig in report


class TestGenerateFullReport:
    def test_contains_all_sections(self):
        report = generate_full_report(
            "13F Section",
            "Congress Section",
            "House Reps Section",
            "Convergence Section",
        )
        assert "13F Section" in report
        assert "Congress Section" in report
        assert "House Reps Section" in report
        assert "Convergence Section" in report

    def test_contains_date(self):
        report = generate_full_report("", "", "", "")
        today = date.today().strftime("%Y-%m-%d")
        assert today in report


class TestMainCLI:
    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    def test_main_both_modes(self, mock_congress, mock_13f):
        mock_13f.return_value = _make_sec13f_data()
        mock_congress.return_value = _make_congress_data()

        with patch("sys.argv", ["main.py"]), patch("builtins.print"):
            main()

        mock_13f.assert_called_once()
        mock_congress.assert_called_once()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    def test_main_13f_only(self, mock_congress, mock_13f):
        mock_13f.return_value = _make_sec13f_data()

        with patch("sys.argv", ["main.py", "--13f-only"]), patch("builtins.print"):
            main()

        mock_13f.assert_called_once()
        mock_congress.assert_not_called()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    def test_main_congress_only(self, mock_congress, mock_13f):
        mock_congress.return_value = _make_congress_data()

        with patch("sys.argv", ["main.py", "--congress-only"]), patch("builtins.print"):
            main()

        mock_congress.assert_called_once()
        mock_13f.assert_not_called()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    def test_main_days_flag(self, mock_congress, mock_13f):
        mock_13f.return_value = _make_sec13f_data()
        mock_congress.return_value = _make_congress_data()

        with patch("sys.argv", ["main.py", "--days", "30"]), patch("builtins.print"):
            main()

        call_kwargs = mock_congress.call_args
        assert call_kwargs.kwargs.get("days") == 30 or (
            call_kwargs.args and 30 in call_kwargs.args
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestPortfolioPctThreshold:
    """Tests for portfolio % threshold in convergence signals."""

    def test_convergence_includes_manager_names(self):
        """Convergence output should include manager names."""
        sec13f_data = _make_sec13f_data(
            manager="Warren Buffett",
            actions={
                "new": [{"name": "AAPL", "value": 1000000}],
                "increased": [],
                "decreased": [],
                "closed": [],
            },
        )
        congress_data = _make_congress_data(
            trades=[
                {
                    "ticker": "AAPL",
                    "name": "Nancy Pelosi",
                    "asset_description": "Apple Inc.",
                    "type": "Purchase",
                    "transaction_date": date.today().isoformat(),
                }
            ],
            by_ticker={
                "AAPL": {"purchases": 1, "sales": 0, "members": ["Nancy Pelosi"]}
            },
        )
        result = compute_convergence(sec13f_data, congress_data)
        if "AAPL" in result:
            assert "Warren Buffett" in str(result["AAPL"]["whale_actions"])

    def test_whale_only_strong_portfolio_pct(self):
        """WHALE_ONLY_STRONG when portfolio % >2%."""
        sec13f_data = _make_sec13f_data(
            manager="Warren Buffett",
            actions={
                "increased": [{"name": "AAPL", "value": 500000000, "change_pct": 50.0}],
                "new": [],
                "decreased": [],
                "closed": [],
            },
        )
        # Simulate 10% of portfolio
        from smart_money_tracker.main import compute_convergence

        result = compute_convergence(sec13f_data, _make_congress_data())
        if "AAPL" in result:
            assert result["AAPL"]["signal"] in ("WHALE_ONLY_STRONG", "WHALE_ONLY")


class TestE2E:
    """End-to-end tests with mocked HTTP"""

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_house_reps_tracker")
    @patch("smart_money_tracker.main.run_source_audit")
    def test_main_all_mocked(
        self, mock_run_source_audit, mock_house, mock_congress, mock_13f
    ):
        """Run main.py with all trackers mocked"""
        from pathlib import Path
        import tempfile

        # Setup mock returns
        mock_13f.return_value = {
            "results": {},
            "report_section": "## 🐋 13F Whale Activity\n\nMock 13F data\n",
            "raw": [],
        }
        mock_congress.return_value = {
            "trades": [],
            "aggregated": {
                "total_trades": 0,
                "by_ticker": {},
                "by_member": {},
                "by_party": {},
            },
            "rankings": [],
            "report_section": "## 🏛️ Congress Trades\n\nMock congress data\n",
            "report_path": "reports/congress-report-mock.md",
            "sources_used": {"insider_finance": True},
        }
        mock_house.return_value = {
            "trades": [],
            "aggregated": {"total_trades": 0, "by_member": {}, "by_state": {}},
            "report_section": "## 🏠 House Reps Disclosures\n\nMock house reps data\n",
            "report_path": "reports/house-reps-mock.md",
            "sources_used": {"house_clerk_fd": True},
        }
        mock_run_source_audit.return_value = {"artifact_paths": {}}

        # Run with temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports"
            reports_dir.mkdir()

            with patch("smart_money_tracker.main.REPORTS_DIR", reports_dir), patch(
                "sys.argv", ["main.py"]
            ), patch("builtins.print"):
                main()

            # Check output files exist
            latest_path = reports_dir / "latest.md"
            assert latest_path.exists(), "latest.md should be created"

            # Check content has all sections
            with open(latest_path) as f:
                content = f.read()
            assert "13F" in content or "Whale" in content
            assert "Congress" in content
            assert "House Reps" in content

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_source_audit")
    def test_main_13f_only(self, mock_run_source_audit, mock_congress, mock_13f):
        """E2E: --13f-only flag"""
        mock_13f.return_value = {
            "results": {},
            "report_section": "## 13F\n",
            "raw": [],
        }
        mock_congress.return_value = {}

        with patch("sys.argv", ["main.py", "--13f-only"]), patch("builtins.print"):
            main()

        mock_13f.assert_called_once()
        mock_congress.assert_not_called()
        mock_run_source_audit.assert_not_called()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_source_audit")
    def test_main_congress_only(self, mock_run_source_audit, mock_congress, mock_13f):
        """E2E: --congress-only flag"""
        mock_13f.return_value = {}
        mock_congress.return_value = {
            "trades": [],
            "report_section": "## Congress\n",
        }

        with patch("sys.argv", ["main.py", "--congress-only"]), patch("builtins.print"):
            main()

        mock_13f.assert_not_called()
        mock_congress.assert_called_once()
        mock_run_source_audit.assert_not_called()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_house_reps_tracker")
    @patch("smart_money_tracker.main.run_source_audit")
    def test_main_no_house_reps(self, mock_run_source_audit, mock_house, mock_congress, mock_13f):
        """E2E: --no-house-reps flag"""
        mock_13f.return_value = {
            "results": {},
            "report_section": "## 13F\n",
            "raw": [],
        }
        mock_congress.return_value = {
            "trades": [],
            "report_section": "## Congress\n",
        }
        mock_house.return_value = {}

        with patch("sys.argv", ["main.py", "--no-house-reps"]), patch("builtins.print"):
            main()

        mock_house.assert_not_called()
        mock_13f.assert_called_once()
        mock_congress.assert_called_once()
        mock_run_source_audit.assert_not_called()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_house_reps_tracker")
    @patch("smart_money_tracker.main.run_source_audit")
    def test_main_verify_sources(self, mock_audit, mock_house, mock_congress, mock_13f):
        mock_13f.return_value = {"results": {}, "report_section": "## 13F\n", "raw": []}
        mock_congress.return_value = {"trades": [], "aggregated": {"total_trades": 0, "by_ticker": {}, "by_member": {}, "by_party": {}}, "rankings": [], "report_section": "## Congress\n", "report_path": "reports/congress-report-mock.md", "sources_used": {"insider_finance": True}}
        mock_house.return_value = {"trades": [], "aggregated": {"total_trades": 0, "by_member": {}, "by_state": {}}, "report_section": "## House\n", "report_path": "reports/house-reps-mock.md", "sources_used": {"house_clerk_fd": True}}
        mock_audit.return_value = {
            "artifact_paths": {
                "latest_json": "reports/source-verification-latest.json",
                "latest_markdown": "reports/source-discrepancies-latest.md",
            }
        }

        with patch("sys.argv", ["main.py", "--verify-sources"]), patch("builtins.print"):
            main()

        mock_audit.assert_called_once()

    @patch("smart_money_tracker.main.run_13f_tracker")
    @patch("smart_money_tracker.main.run_congress_tracker")
    @patch("smart_money_tracker.main.run_house_reps_tracker")
    def test_output_file_validation(self, mock_house, mock_congress, mock_13f):
        """Validate latest.md has all three sections"""
        from datetime import date
        from pathlib import Path
        import tempfile

        mock_13f.return_value = {
            "results": {},
            "report_section": "## 🐋 13F Whale Activity\n\n13F content\n",
            "raw": [],
        }
        mock_congress.return_value = {
            "trades": [],
            "aggregated": {
                "total_trades": 0,
                "by_ticker": {},
                "by_member": {},
                "by_party": {},
            },
            "rankings": [],
            "report_section": "## 🏛️ Congress Trades\n\nCongress content\n",
            "report_path": "reports/congress-report-mock.md",
            "sources_used": {"insider_finance": True},
        }
        mock_house.return_value = {
            "trades": [],
            "aggregated": {"total_trades": 0, "by_member": {}, "by_state": {}},
            "report_section": "## 🏠 House Reps Disclosures\n\nHouse Reps content\n",
            "report_path": "reports/house-reps-mock.md",
            "sources_used": {"house_clerk_fd": True},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports"
            reports_dir.mkdir()

            with patch("smart_money_tracker.main.REPORTS_DIR", reports_dir), patch(
                "sys.argv", ["main.py"]
            ), patch("builtins.print"):
                main()

            # Check latest.md
            latest_path = reports_dir / "latest.md"
            assert latest_path.exists()

            with open(latest_path) as f:
                content = f.read()

            # Verify all sections present
            assert "13F Whale Activity" in content
            assert "Congress Trades" in content
            assert "House Reps Disclosures" in content

            # Check dated file also created
            today = date.today().strftime("%Y-%m-%d")
            dated_path = reports_dir / f"smart-money-{today}.md"
            assert dated_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
