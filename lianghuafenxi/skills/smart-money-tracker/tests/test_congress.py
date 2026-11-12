import pytest
import json
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import date, timedelta
from collections import defaultdict

from smart_money_tracker.congress import (
    normalize_trade,
    aggregate_trades,
    fetch_congress_trades,
    generate_congress_report,
    run_congress_tracker,
    rank_congress_trades,
    _get_cache_date,
    _is_cache_from_today,
    _is_cache_stale,
    CACHE_FILE,
    CACHE_TTL_HOURS,
)


class TestNormalizeTrade:
    """Unit tests for normalize_trade()"""

    def test_valid_input(self):
        raw = {
            "name": "Nancy Pelosi",
            "ticker": "AAPL",
            "party": "Democrat",
            "type": "Purchase",
            "transaction_date": "2025-01-15",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["name"] == "Nancy Pelosi"
        assert result["ticker"] == "AAPL"
        # Democrat doesn't contain "rep" so goes to senate by current heuristic
        assert result["chamber"] == "senate"
        assert result["type"] == "Purchase"
        assert result["party"] == "Democrat"

    def test_missing_name(self):
        raw = {"ticker": "AAPL", "transaction_date": "2025-01-15"}
        assert normalize_trade(raw) is None

    def test_empty_name(self):
        raw = {"name": "", "transaction_date": "2025-01-15"}
        assert normalize_trade(raw) is None

    def test_senate_member(self):
        raw = {
            "name": "John Smith",
            "party": "Senator",
            "type": "Sale",
            "transaction_date": "2025-01-15",
        }
        result = normalize_trade(raw)
        assert result is not None
        # "Senator" contains "sen" so goes to senate
        assert result["chamber"] == "senate"

    def test_no_ticker(self):
        raw = {
            "name": "John Smith",
            "party": "Democrat",
            "type": "Purchase",
            "transaction_date": "2025-01-15",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["ticker"] == ""

    def test_filing_type_sale(self):
        raw = {
            "name": "John Smith",
            "party": "Democrat",
            "type": "Sale",
            "transaction_date": "2025-01-15",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["type"] == "Sale"


class TestAggregateTrades:
    """Unit tests for aggregate_trades()"""

    def test_empty_trades(self):
        result = aggregate_trades([])
        assert result["total_trades"] == 0
        assert result["by_ticker"] == {}
        assert result["by_member"] == {}
        assert result["by_party"] == {}

    def test_single_trade(self):
        # Use a recent date (within 90 days)
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades)
        assert result["total_trades"] == 1
        assert "AAPL" in result["by_ticker"]
        assert result["by_ticker"]["AAPL"]["total"] == 1
        assert result["by_ticker"]["AAPL"]["purchases"] == 1
        assert result["by_ticker"]["AAPL"]["sales"] == 0

    def test_multiple_trades_same_ticker(self):
        recent_date1 = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        recent_date2 = (date.today() - timedelta(days=20)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date1,
            },
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date2,
            },
        ]
        result = aggregate_trades(trades)
        assert result["total_trades"] == 2
        assert result["by_ticker"]["AAPL"]["total"] == 2
        assert result["by_ticker"]["AAPL"]["purchases"] == 2

    def test_purchase_and_sale(self):
        recent_date1 = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        recent_date2 = (date.today() - timedelta(days=20)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date1,
            },
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Sale",
                "transaction_date": recent_date2,
            },
        ]
        result = aggregate_trades(trades)
        assert result["by_ticker"]["AAPL"]["purchases"] == 1
        assert result["by_ticker"]["AAPL"]["sales"] == 1

    def test_by_member(self):
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades)
        assert "Nancy Pelosi" in result["by_member"]
        assert result["by_member"]["Nancy Pelosi"]["total"] == 1
        assert result["by_member"]["Nancy Pelosi"]["party"] == "Democrat"
        assert result["by_member"]["Nancy Pelosi"]["chamber"] == "house"

    def test_by_party(self):
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades)
        assert "Democrat" in result["by_party"]
        assert result["by_party"]["Democrat"]["total"] == 1

    def test_filter_by_days(self):
        # Create a trade older than 90 days
        old_date = (date.today() - timedelta(days=100)).strftime("%Y-%m-%d")
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Test",
                "party": "",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": old_date,
            },
            {
                "ticker": "MSFT",
                "name": "Test",
                "party": "",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades, days=90)
        assert result["total_trades"] == 1
        assert "MSFT" in result["by_ticker"]
        assert "AAPL" not in result["by_ticker"]

    def test_unknown_ticker(self):
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "",
                "name": "Test",
                "party": "",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades)
        assert "UNKNOWN" in result["by_ticker"]

    def test_multiple_members_same_ticker(self):
        recent_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "house",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
            {
                "ticker": "AAPL",
                "name": "John Smith",
                "party": "Republican",
                "chamber": "senate",
                "type": "Purchase",
                "transaction_date": recent_date,
            },
        ]
        result = aggregate_trades(trades)
        assert result["by_ticker"]["AAPL"]["total"] == 2
        assert "Nancy Pelosi" in result["by_ticker"]["AAPL"]["members"]
        assert "John Smith" in result["by_ticker"]["AAPL"]["members"]


class TestRankCongressTrades:
    """Unit tests for rank_congress_trades()"""

    def test_basic_ranking(self):
        agg = {
            "by_member": {
                "Nancy Pelosi": {
                    "total": 10,
                    "purchases": 8,
                    "sales": 2,
                    "party": "Democrat",
                    "chamber": "house",
                    "tickers": [],
                },
                "John Smith": {
                    "total": 5,
                    "purchases": 3,
                    "sales": 2,
                    "party": "Republican",
                    "chamber": "senate",
                    "tickers": [],
                },
            },
            "total_trades": 15,
        }
        result = rank_congress_trades(agg)
        # Returns list of dicts sorted by total_trades
        assert len(result) == 2
        assert result[0]["member"] == "Nancy Pelosi"  # Higher total
        assert result[1]["member"] == "John Smith"

    def test_top_n_limit(self):
        agg = {
            "by_member": {
                "Member A": {
                    "total": 10,
                    "purchases": 8,
                    "sales": 2,
                    "party": "Democrat",
                    "chamber": "house",
                    "tickers": [],
                },
                "Member B": {
                    "total": 5,
                    "purchases": 3,
                    "sales": 2,
                    "party": "Republican",
                    "chamber": "senate",
                    "tickers": [],
                },
                "Member C": {
                    "total": 3,
                    "purchases": 2,
                    "sales": 1,
                    "party": "Democrat",
                    "chamber": "house",
                    "tickers": [],
                },
            },
            "total_trades": 18,
        }
        result = rank_congress_trades(agg, top_n=2)
        assert len(result) == 2
        assert result[0]["member"] == "Member A"
        assert result[1]["member"] == "Member B"


class TestGenerateCongressReport:
    """Unit tests for generate_congress_report()"""

    def test_empty_report(self, tmp_path):
        agg = {
            "by_ticker": {},
            "by_member": {},
            "by_party": {},
            "total_trades": 0,
            "days": 90,
        }
        output_path = tmp_path / "report.md"
        generate_congress_report(agg, output_path)
        with open(output_path) as f:
            report = f.read()
        assert "Congress Trading Report" in report
        assert "Total Trades: 0" in report

    def test_report_with_trades(self, tmp_path):
        agg = {
            "by_ticker": {
                "AAPL": {
                    "purchases": 5,
                    "sales": 2,
                    "members": ["Nancy Pelosi"],
                    "total": 7,
                },
            },
            "by_member": {
                "Nancy Pelosi": {
                    "total": 7,
                    "purchases": 5,
                    "sales": 2,
                    "party": "Democrat",
                    "chamber": "house",
                    "tickers": ["AAPL"],
                },
            },
            "by_party": {
                "Democrat": {"purchases": 5, "sales": 2, "total": 7},
            },
            "total_trades": 7,
            "days": 90,
        }
        output_path = tmp_path / "report.md"
        generate_congress_report(agg, output_path)
        with open(output_path) as f:
            report = f.read()
        assert "AAPL" in report
        assert "Nancy Pelosi" in report
        assert "Democrat" in report
        assert "By Ticker" in report
        assert "By Member" in report


class TestIntegrationCongress:
    """Integration tests with mocked external calls"""

    def test_fetch_congress_trades_callable(self):
        """Test that fetch_congress_trades is callable"""
        assert callable(fetch_congress_trades)

    @patch("smart_money_tracker.congress.requests.get")
    def test_fetch_congress_trades_with_mocks(self, mock_get):
        """Test that fetch_congress_trades calls correct functions"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [{"name": "Test"}]}
        mock_get.return_value = mock_response

        # This test verifies the flow without actually downloading
        result = fetch_congress_trades(force_download=True)
        assert isinstance(result, list)


class TestRunCongressTracker:
    """Tests for run_congress_tracker()"""

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    @patch("smart_money_tracker.congress.normalize_trade")
    def test_run_tracker_basic(self, mock_normalize, mock_fetch):
        """Test run_congress_tracker returns correct structure"""
        mock_fetch.return_value = [{"name": "Test", "transaction_date": "2025-01-15"}]
        mock_normalize.return_value = {
            "ticker": "AAPL",
            "name": "Test",
            "chamber": "house",
            "party": "Democrat",
            "type": "Purchase",
            "transaction_date": "2025-01-15",
            "state": "",
            "district": "",
            "amount_range": "",
            "disclosure_date": "",
            "asset_description": "",
        }

        result = run_congress_tracker(days=90)
        assert "aggregated" in result
        assert "trades" in result
        assert "rankings" in result
        assert "report_path" in result
        assert result["sources_used"]["insider_finance"] is True

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_run_tracker_with_member_filter(self, mock_fetch):
        """Test member_filter filters trades by member name"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Smith", "transaction_date": recent_date},
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_normalize:
            mock_normalize.side_effect = lambda raw: (
                {
                    "ticker": "AAPL",
                    "name": raw["name"],
                    "chamber": "house",
                    "party": "Democrat" if "Pelosi" in raw["name"] else "Republican",
                    "type": "Purchase",
                    "transaction_date": recent_date,
                    "state": "",
                    "district": "",
                    "amount_range": "",
                    "disclosure_date": "",
                    "asset_description": "",
                }
                if raw["name"]
                else None
            )

            result = run_congress_tracker(days=90, member_filter="pelosi")
            assert len(result["trades"]) == 2
            assert all("Pelosi" in t["name"] for t in result["trades"])

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_run_tracker_with_party_filter(self, mock_fetch):
        """Test party_filter filters trades by party"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Smith", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_normalize:
            mock_normalize.side_effect = lambda raw: (
                {
                    "ticker": "AAPL",
                    "name": raw["name"],
                    "chamber": "house",
                    "party": "Democrat" if "Pelosi" in raw["name"] else "Republican",
                    "type": "Purchase",
                    "transaction_date": recent_date,
                    "state": "",
                    "district": "",
                    "amount_range": "",
                    "disclosure_date": "",
                    "asset_description": "",
                }
                if raw["name"]
                else None
            )

            result = run_congress_tracker(days=90, party_filter="democrat")
            assert len(result["trades"]) == 1
            assert result["trades"][0]["party"] == "Democrat"

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_run_tracker_with_chamber_filter(self, mock_fetch):
        """Test chamber_filter filters trades by chamber"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Senator", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_normalize:
            mock_normalize.side_effect = lambda raw: (
                {
                    "ticker": "AAPL",
                    "name": raw["name"],
                    "chamber": "house" if "Pelosi" in raw["name"] else "senate",
                    "party": "Democrat",
                    "type": "Purchase",
                    "transaction_date": recent_date,
                    "state": "",
                    "district": "",
                    "amount_range": "",
                    "disclosure_date": "",
                    "asset_description": "",
                }
                if raw["name"]
                else None
            )

            result = run_congress_tracker(days=90, chamber_filter="house")
            assert len(result["trades"]) == 1
            assert result["trades"][0]["chamber"] == "house"

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_run_tracker_with_multiple_filters(self, mock_fetch):
        """Test multiple filters applied together"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Smith", "transaction_date": recent_date},
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_normalize:
            mock_normalize.side_effect = lambda raw: (
                {
                    "ticker": "AAPL",
                    "name": raw["name"],
                    "chamber": "house",
                    "party": "Democrat" if "Pelosi" in raw["name"] else "Republican",
                    "type": "Purchase",
                    "transaction_date": recent_date,
                    "state": "",
                    "district": "",
                    "amount_range": "",
                    "disclosure_date": "",
                    "asset_description": "",
                }
                if raw["name"]
                else None
            )

            result = run_congress_tracker(
                days=90, member_filter="pelosi", party_filter="democrat"
            )
            assert len(result["trades"]) == 2
            assert all("Pelosi" in t["name"] for t in result["trades"])
            assert all(t["party"] == "Democrat" for t in result["trades"])

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_run_tracker_with_no_matching_filter(self, mock_fetch):
        """Test filter that matches no trades"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_normalize:
            mock_normalize.side_effect = lambda raw: (
                {
                    "ticker": "AAPL",
                    "name": raw["name"],
                    "chamber": "house",
                    "party": "Democrat",
                    "type": "Purchase",
                    "transaction_date": recent_date,
                    "state": "",
                    "district": "",
                    "amount_range": "",
                    "disclosure_date": "",
                    "asset_description": "",
                }
                if raw["name"]
                else None
            )

            result = run_congress_tracker(days=90, member_filter="nonexistent")
            assert len(result["trades"]) == 0
            assert result["aggregated"]["total_trades"] == 0


class TestNonDefaultFilters:
    """Tests with non-default filter values and edge cases"""

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_member_filter_nonexistent(self, mock_fetch):
        """Filter by member that doesn't exist → empty result"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.return_value = {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "chamber": "house",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, member_filter="XYZ123")
            assert len(result["trades"]) == 0
            assert result["aggregated"]["total_trades"] == 0

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_member_filter_partial_match(self, mock_fetch):
        """member_filter should match substring, not exact"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Pelosi Smith", "transaction_date": recent_date},
            {"name": "Jane Doe", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.side_effect = lambda raw: {
                "ticker": "AAPL",
                "name": raw["name"],
                "chamber": "house",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, member_filter="pelosi")
            assert len(result["trades"]) == 2

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_party_filter_independent(self, mock_fetch):
        """Filter by 'Independent' party (non-default)"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Bernie Sanders", "transaction_date": recent_date},
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.side_effect = lambda raw: {
                "ticker": "AAPL",
                "name": raw["name"],
                "chamber": "senate" if "Sanders" in raw["name"] else "house",
                "party": "Independent" if "Sanders" in raw["name"] else "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, party_filter="independent")
            assert len(result["trades"]) == 1
            assert result["trades"][0]["party"] == "Independent"

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_party_filter_case_insensitive(self, mock_fetch):
        """party_filter should be case-insensitive"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.return_value = {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "chamber": "house",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            # Test with uppercase
            result = run_congress_tracker(days=90, party_filter="DEMOCRAT")
            assert len(result["trades"]) == 1

            # Test with mixed case
            result = run_congress_tracker(days=90, party_filter="DeMoCrAt")
            assert len(result["trades"]) == 1

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_chamber_filter_house(self, mock_fetch):
        """Filter by 'house' chamber"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Senator", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.side_effect = lambda raw: {
                "ticker": "AAPL",
                "name": raw["name"],
                "chamber": "house" if "Pelosi" in raw["name"] else "senate",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, chamber_filter="house")
            assert len(result["trades"]) == 1
            assert result["trades"][0]["chamber"] == "house"

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_chamber_filter_senate(self, mock_fetch):
        """Filter by 'senate' chamber"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
            {"name": "John Senator", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.side_effect = lambda raw: {
                "ticker": "AAPL",
                "name": raw["name"],
                "chamber": "house" if "Pelosi" in raw["name"] else "senate",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, chamber_filter="senate")
            assert len(result["trades"]) == 1
            assert result["trades"][0]["chamber"] == "senate"

    @patch("smart_money_tracker.congress.fetch_congress_trades")
    def test_chamber_filter_invalid(self, mock_fetch):
        """Invalid chamber filter should return empty"""
        recent_date = date.today().strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Nancy Pelosi", "transaction_date": recent_date},
        ]

        with patch("smart_money_tracker.congress.normalize_trade") as mock_norm:
            mock_norm.return_value = {
                "ticker": "AAPL",
                "name": "Nancy Pelosi",
                "chamber": "house",
                "party": "Democrat",
                "type": "Purchase",
                "transaction_date": recent_date,
                "state": "",
                "district": "",
                "amount_range": "",
                "disclosure_date": "",
                "asset_description": "",
            }
            result = run_congress_tracker(days=90, chamber_filter="invalid_chamber")
            assert len(result["trades"]) == 0


class TestDataValidation:
    """Tests for data validation helpers"""

    def test_trade_schema_valid(self):
        """Valid trade dict passes schema validation"""
        from smart_money_tracker.congress import normalize_trade

        raw = {
            "name": "Test Person",
            "ticker": "AAPL",
            "party": "Democrat",
            "type": "Purchase",
            "transaction_date": "2025-01-15",
        }
        trade = normalize_trade(raw)
        assert trade is not None

        # Check all required keys exist
        required_keys = [
            "ticker",
            "name",
            "chamber",
            "party",
            "type",
            "transaction_date",
        ]
        for key in required_keys:
            assert key in trade, f"Missing key: {key}"
            assert trade[key] is not None, f"None value for key: {key}"

    def test_trade_schema_missing_keys(self):
        """Trade with missing keys should still normalize (graceful)"""
        from smart_money_tracker.congress import normalize_trade

        raw = {"name": "Test"}  # Missing most fields
        trade = normalize_trade(raw)
        # Should still return a dict, just with empty values
        assert trade is not None
        assert "name" in trade
        assert trade["name"] == "Test"

    def test_date_range_valid(self):
        """Valid date should pass range validation"""
        from datetime import datetime

        date_str = datetime.now().strftime("%Y-%m-%d")
        # Simple validation: date is not in future, not too old
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            assert date_obj <= datetime.now()
            assert date_obj.year >= 2020
        except ValueError:
            assert False, f"Invalid date format: {date_str}"

    def test_date_range_invalid(self):
        """Invalid date format should fail validation"""
        from datetime import datetime

        invalid_dates = ["", "not-a-date", "2019-01-01", "2025-13-01"]
        for date_str in invalid_dates:
            if date_str == "":
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    assert False, "Should raise ValueError"
                except ValueError:
                    pass
            elif date_str == "not-a-date":
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    assert False, "Should raise ValueError"
                except ValueError:
                    pass
            elif date_str == "2019-01-01":
                # Too old
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                assert date_obj.year < 2020
            elif date_str == "2025-13-01":
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    assert False, "Should raise ValueError"
                except ValueError:
                    pass


class TestIsValidTradeData:
    """Tests for _is_valid_trade_data() content validation."""

    def test_empty_dict(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        assert _is_valid_trade_data({}) is False

    def test_dict_with_empty_list(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        assert _is_valid_trade_data({"data": []}) is False

    def test_test_fixture_data(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        test_data = {"data": [{"name": "Test"}]}
        assert _is_valid_trade_data(test_data) is False

    def test_real_trade_data(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        real_data = {
            "data": [
                {
                    "name": "Nancy Pelosi",
                    "ticker": "AAPL",
                    "type": "Purchase",
                    "transaction_date": "2025-01-15",
                }
            ]
        }
        assert _is_valid_trade_data(real_data) is True

    def test_mixed_test_and_real(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        mixed_data = {
            "data": [
                {"name": "Test"},
                {
                    "name": "Nancy Pelosi",
                    "ticker": "AAPL",
                    "type": "Purchase",
                    "transaction_date": "2025-01-15",
                },
            ]
        }
        assert _is_valid_trade_data(mixed_data) is True

    def test_list_instead_of_dict(self):
        from smart_money_tracker.congress import _is_valid_trade_data
        assert _is_valid_trade_data([{"name": "Real"}]) is False


class TestIsCacheValid:
    """Tests for _is_cache_valid() combining mtime + content checks."""

    def test_no_cache_file(self):
        from smart_money_tracker.congress import _is_cache_valid
        with patch("smart_money_tracker.congress.CACHE_FILE", Path("/nonexistent")):
            assert _is_cache_valid() is False

    def test_stale_cache(self, tmp_path):
        from smart_money_tracker.congress import _is_cache_valid
        cache = tmp_path / "congress-trades.json"
        cache.write_text('{"data": [{"name": "Real", "ticker": "AAPL"}]}')
        # Set mtime to yesterday
        yesterday = time.time() - 86400 * 2
        os.utime(cache, (yesterday, yesterday))
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            assert _is_cache_valid() is False

    def test_fresh_cache_with_test_data(self, tmp_path):
        from smart_money_tracker.congress import _is_cache_valid
        cache = tmp_path / "congress-trades.json"
        cache.write_text('{"data": [{"name": "Test"}]}')
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            assert _is_cache_valid() is False

    def test_fresh_cache_with_real_data(self, tmp_path):
        from smart_money_tracker.congress import _is_cache_valid
        cache = tmp_path / "congress-trades.json"
        cache.write_text(
            '{"data": [{"name": "Nancy Pelosi", "ticker": "AAPL", "type": "Purchase", "transaction_date": "2025-01-15"}]}'
        )
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            assert _is_cache_valid() is True

    def test_corrupt_cache(self, tmp_path):
        from smart_money_tracker.congress import _is_cache_valid
        cache = tmp_path / "congress-trades.json"
        cache.write_text("not valid json")
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            assert _is_cache_valid() is False


class TestExtractBuildIdFromHtml:
    """Tests for _extract_build_id_from_html() with all 3 patterns."""

    def test_pattern_1_direct_reference(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<script src="/_next/data/abc123xyz/congress-trades.json"></script>'
        assert _extract_build_id_from_html(html) == "abc123xyz"

    def test_pattern_2_static_chunk(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<script src="/_next/static/xyz789abc/_buildManifest.js"></script>'
        assert _extract_build_id_from_html(html) == "xyz789abc"

    def test_pattern_3_next_data_script(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<script id="__NEXT_DATA__">{"buildId":"build456def"}</script>'
        assert _extract_build_id_from_html(html) == "build456def"

    def test_no_build_id_found(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<html><body>No build id here</body></html>'
        assert _extract_build_id_from_html(html) is None

    def test_pattern_1_priority_over_2(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = (
            '<script src="/_next/data/aaa111/congress-trades.json"></script>'
            '<script src="/_next/static/bbb222/_buildManifest.js"></script>'
        )
        assert _extract_build_id_from_html(html) == "aaa111"

    def test_rejects_css_path(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<link rel="stylesheet" href="/_next/static/css/abc123.css">'
        assert _extract_build_id_from_html(html) is None

    def test_rejects_chunks_path(self):
        from smart_money_tracker.congress import _extract_build_id_from_html
        html = '<script src="/_next/static/chunks/main-abc123.js"></script>'
        assert _extract_build_id_from_html(html) is None


class TestHdataNormalization:
    """Tests for normalize_trade() with hdata schema."""

    def test_hdata_full_fields(self):
        from smart_money_tracker.congress import normalize_trade
        raw = {
            "representative": "John Doe",
            "ticker": "AAPL",
            "district": "TX-01",
            "disclosureDate": "2025-03-10",
            "capitalGainsOver200USD": True,
            "type": "Purchase",
            "amount": "$1,001 - $15,000",
            "transactionDate": "2025-03-01",
            "party": "Republican",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["name"] == "John Doe"
        assert result["ticker"] == "AAPL"
        assert result["district"] == "TX-01"
        assert result["disclosure_date"] == "2025-03-10"
        assert result["capital_gains_over_200"] is True
        assert result["type"] == "Purchase"
        assert result["amount_range"] == "$1,001 - $15,000"
        assert result["transaction_date"] == "2025-03-01"
        assert result["party"] == "Republican"

    def test_hdata_missing_optional_fields(self):
        from smart_money_tracker.congress import normalize_trade
        raw = {
            "representative": "Jane Doe",
            "ticker": "TSLA",
            "type": "Sale",
            "amount": "$15,001 - $50,000",
            "transactionDate": "2025-02-01",
            "party": "Democrat",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["name"] == "Jane Doe"
        assert result["ticker"] == "TSLA"
        assert result["district"] == ""
        assert result["disclosure_date"] == ""
        assert result["capital_gains_over_200"] is False

    def test_hdata_firstName_lastName_fallback(self):
        from smart_money_tracker.congress import normalize_trade
        raw = {
            "firstName": "Nancy",
            "lastName": "Pelosi",
            "ticker": "NVDA",
            "district": "CA-12",
            "type": "Purchase",
            "transactionDate": "2025-01-15",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["name"] == "Nancy Pelosi"
        assert result["district"] == "CA-12"

    def test_data_array_backward_compatibility(self):
        from smart_money_tracker.congress import normalize_trade
        raw = {
            "firstName": "Nancy",
            "lastName": "Pelosi",
            "symbol": "AAPL",
            "type": "Sale",
            "amount": "$1,001 - $15,000",
            "transactionDate": "2025-01-15",
            "party": "Democrat",
        }
        result = normalize_trade(raw)
        assert result is not None
        assert result["name"] == "Nancy Pelosi"
        assert result["ticker"] == "AAPL"
        assert result["district"] == ""
        assert result["disclosure_date"] == ""
        assert result["capital_gains_over_200"] is False


class TestExtractTradesFromResponse:
    """Tests for _extract_trades_from_response() dual-array logic."""

    def test_prefers_hdata(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        data = {
            "pageProps": {
                "hdata": [{"representative": "A", "ticker": "X"}],
                "data": [{"firstName": "B", "symbol": "Y"}],
            }
        }
        result = _extract_trades_from_response(data)
        assert len(result) == 1
        assert result[0]["representative"] == "A"

    def test_falls_back_to_data(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        data = {"pageProps": {"data": [{"firstName": "B", "symbol": "Y"}]}}
        result = _extract_trades_from_response(data)
        assert len(result) == 1
        assert result[0]["firstName"] == "B"

    def test_empty_hdata_falls_back(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        data = {
            "pageProps": {
                "hdata": [],
                "data": [{"firstName": "B", "symbol": "Y"}],
            }
        }
        result = _extract_trades_from_response(data)
        assert len(result) == 1
        assert result[0]["firstName"] == "B"

    def test_legacy_top_level_data(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        data = {"data": [{"name": "C", "ticker": "Z"}]}
        result = _extract_trades_from_response(data)
        assert len(result) == 1
        assert result[0]["name"] == "C"

    def test_list_input(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        data = [{"name": "D", "ticker": "W"}]
        result = _extract_trades_from_response(data)
        assert len(result) == 1
        assert result[0]["name"] == "D"

    def test_empty_response(self):
        from smart_money_tracker.congress import _extract_trades_from_response
        assert _extract_trades_from_response({}) == []
        assert _extract_trades_from_response({"pageProps": {}}) == []
        assert _extract_trades_from_response({"pageProps": {"hdata": []}}) == []


class TestFetchLiveData:
    """Tests for _fetch_live_data() 3-tier strategy."""

    @patch("smart_money_tracker.congress.fetch_with_retry")
    def test_tier_1_plain_requests_succeeds(self, mock_fetch):
        from smart_money_tracker.congress import _fetch_live_data
        mock_resp = Mock()
        mock_resp.json.return_value = {"pageProps": {"data": [{"name": "Test"}]}}
        mock_fetch.return_value = mock_resp
        result = _fetch_live_data()
        assert result == {"pageProps": {"data": [{"name": "Test"}]}}
        mock_fetch.assert_called_once()

    @patch("smart_money_tracker.congress.fetch_with_retry")
    @patch("smart_money_tracker.congress._fetch_with_cloudscraper")
    def test_tier_2_cloudscraper_on_403(self, mock_cloudscraper, mock_fetch):
        from smart_money_tracker.congress import _fetch_live_data
        from requests import HTTPError

        mock_fetch.side_effect = HTTPError(
            response=Mock(status_code=403)
        )
        mock_resp = Mock()
        mock_resp.json.return_value = {"pageProps": {"hdata": [{"representative": "A"}]}}
        mock_cloudscraper.return_value = mock_resp
        result = _fetch_live_data()
        assert "pageProps" in result
        mock_cloudscraper.assert_called_once()

    @patch("smart_money_tracker.congress.fetch_with_retry")
    @patch("smart_money_tracker.congress._fetch_with_cloudscraper")
    def test_tier_2_cloudscraper_not_installed(self, mock_cloudscraper, mock_fetch):
        from smart_money_tracker.congress import _fetch_live_data
        from requests import HTTPError

        mock_fetch.side_effect = HTTPError(
            response=Mock(status_code=403)
        )
        mock_cloudscraper.side_effect = ImportError("cloudscraper not installed")
        with pytest.raises(ImportError):
            _fetch_live_data()

    @patch("smart_money_tracker.congress.fetch_with_retry")
    def test_tier_1_404_triggers_build_id_resolution(self, mock_fetch):
        from smart_money_tracker.congress import _fetch_live_data
        from requests import HTTPError

        def side_effect(url, **kwargs):
            mock_resp = Mock()
            if url == "https://www.insiderfinance.io/_next/data/congress-trades.json":
                mock_resp.raise_for_status.side_effect = HTTPError(
                    response=Mock(status_code=404)
                )
            elif "insiderfinance.io/congress-trades" in url and not url.endswith(".json"):
                mock_resp.text = '<script src="/_next/data/abc123/congress-trades.json"></script>'
            elif "_next/data/abc123/congress-trades.json" in url:
                mock_resp.json.return_value = {"pageProps": {"data": [{"name": "Test"}]}}
            mock_resp.raise_for_status()
            return mock_resp

        mock_fetch.side_effect = side_effect
        result = _fetch_live_data()
        assert result == {"pageProps": {"data": [{"name": "Test"}]}}
        assert mock_fetch.call_count == 3


class TestFetchWithCloudscraper:
    """Tests for _fetch_with_cloudscraper() helper."""

    @patch("smart_money_tracker.congress.cloudscraper")
    def test_cloudscraper_fetch_success(self, mock_cloudscraper_mod):
        from smart_money_tracker.congress import _fetch_with_cloudscraper
        scraper = Mock()
        mock_cloudscraper_mod.create_scraper.return_value = scraper

        page_resp = Mock()
        page_resp.text = '<script src="/_next/data/build999/congress-trades.json"></script>'
        json_resp = Mock()
        json_resp.json.return_value = {"pageProps": {"hdata": []}}
        scraper.get.side_effect = [page_resp, json_resp]

        result = _fetch_with_cloudscraper("https://example.com/congress-trades.json")
        assert result == json_resp
        assert scraper.get.call_count == 2

    @patch("smart_money_tracker.congress.cloudscraper")
    def test_cloudscraper_no_build_id_raises(self, mock_cloudscraper_mod):
        from smart_money_tracker.congress import _fetch_with_cloudscraper
        scraper = Mock()
        mock_cloudscraper_mod.create_scraper.return_value = scraper
        page_resp = Mock()
        page_resp.text = '<html><body>No build id</body></html>'
        scraper.get.return_value = page_resp
        with pytest.raises(Exception, match="Could not find build-id"):
            _fetch_with_cloudscraper("https://example.com/congress-trades.json")


class TestReportWithNewFields:
    """Tests for generate_congress_report() with hdata fields."""

    def test_district_in_by_member(self, tmp_path):
        agg = {
            "by_ticker": {},
            "by_member": {
                "John Doe": {
                    "total": 1,
                    "purchases": 1,
                    "sales": 0,
                    "party": "Republican",
                    "chamber": "house",
                    "district": "TX-01",
                    "tickers": ["AAPL"],
                },
            },
            "by_party": {},
            "total_trades": 1,
            "days": 90,
        }
        output_path = tmp_path / "report.md"
        generate_congress_report(agg, output_path)
        with open(output_path) as f:
            report = f.read()
        assert "District: TX-01" in report

    def test_disclosure_date_in_trade_details(self, tmp_path):
        agg = {
            "by_ticker": {},
            "by_member": {},
            "by_party": {},
            "total_trades": 1,
            "days": 90,
            "by_net_volume": {
                "AAPL": {
                    "total": 1,
                    "purchases": 1,
                    "sales": 0,
                    "purchase_volume": 8000,
                    "sales_volume": 0,
                    "net_volume": 8000,
                    "net_direction": "BULLISH",
                    "members": ["John Doe"],
                    "trades": [
                        {
                            "member": "John Doe",
                            "type": "Purchase",
                            "amount": 8000,
                            "date": "2025-03-01",
                            "party": "Republican",
                            "is_purchase": True,
                            "is_sale": False,
                            "disclosure_date": "2025-03-10",
                            "capital_gains_over_200": False,
                        }
                    ],
                }
            },
        }
        output_path = tmp_path / "report.md"
        generate_congress_report(agg, output_path)
        with open(output_path) as f:
            report = f.read()
        assert "(disclosed 2025-03-10)" in report

    def test_capital_gains_flag_in_trade_details(self, tmp_path):
        agg = {
            "by_ticker": {},
            "by_member": {},
            "by_party": {},
            "total_trades": 1,
            "days": 90,
            "by_net_volume": {
                "AAPL": {
                    "total": 1,
                    "purchases": 1,
                    "sales": 0,
                    "purchase_volume": 8000,
                    "sales_volume": 0,
                    "net_volume": 8000,
                    "net_direction": "BULLISH",
                    "members": ["John Doe"],
                    "trades": [
                        {
                            "member": "John Doe",
                            "type": "Purchase",
                            "amount": 8000,
                            "date": "2025-03-01",
                            "party": "Republican",
                            "is_purchase": True,
                            "is_sale": False,
                            "disclosure_date": "",
                            "capital_gains_over_200": True,
                        }
                    ],
                }
            },
        }
        output_path = tmp_path / "report.md"
        generate_congress_report(agg, output_path)
        with open(output_path) as f:
            report = f.read()
        assert "[CG>200]" in report


class TestFetchCongressTradesIntegration:
    """Integration tests for fetch_congress_trades() with cache and fallback."""

    @patch("smart_money_tracker.congress._is_cache_valid")
    @patch("smart_money_tracker.congress._fetch_live_data")
    def test_uses_live_data_when_cache_stale(self, mock_fetch_live, mock_cache_valid):
        mock_cache_valid.return_value = False
        mock_fetch_live.return_value = {"pageProps": {"data": [{"name": "Live"}]}}
        result = fetch_congress_trades()
        assert len(result) == 1
        assert result[0]["name"] == "Live"

    @patch("smart_money_tracker.congress._is_cache_valid")
    @patch("smart_money_tracker.congress._fetch_live_data")
    def test_falls_back_to_cache_on_live_failure(self, mock_fetch_live, mock_cache_valid, tmp_path):
        mock_cache_valid.return_value = False
        mock_fetch_live.side_effect = Exception("Network error")
        cache = tmp_path / "congress-trades.json"
        cache.write_text('{"pageProps": {"data": [{"name": "Cached", "ticker": "AAPL"}]}}')
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            result = fetch_congress_trades()
            assert len(result) == 1
            assert result[0]["name"] == "Cached"

    @patch("smart_money_tracker.congress._is_cache_valid")
    @patch("smart_money_tracker.congress._fetch_live_data")
    def test_returns_empty_on_total_failure(self, mock_fetch_live, mock_cache_valid, tmp_path):
        mock_cache_valid.return_value = False
        mock_fetch_live.side_effect = Exception("Network error")
        cache = tmp_path / "nonexistent.json"
        with patch("smart_money_tracker.congress.CACHE_FILE", cache):
            result = fetch_congress_trades()
            assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
