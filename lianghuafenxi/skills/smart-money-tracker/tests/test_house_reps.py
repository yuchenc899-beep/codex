import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from smart_money_tracker.house_reps import (
    normalize_house_fd_trade,
    fetch_house_fd_trades,
    aggregate_house_reps_trades,
    generate_house_reps_report,
    run_house_reps_tracker,
    _download_and_extract_fds,
    _parse_fd_xml,
)


class TestNormalizeHouseFDTrade:
    """Unit tests for normalize_house_fd_trade()"""

    def test_valid_input(self):
        raw = {
            "name": "John Smith",
            "state_dst": "CA12",
            "filing_type": "Periodic Transaction Report",
            "filing_date": "2025-01-15",
            "doc_id": "12345",
        }
        result = normalize_house_fd_trade(raw)
        assert result is not None
        assert result["name"] == "John Smith"
        assert result["chamber"] == "house"
        assert result["state"] == "CA"
        assert result["district"] == "12"
        assert result["type"] == "Periodic Transaction Report"
        assert result["transaction_date"] == "2025-01-15"

    def test_missing_name(self):
        raw = {"state_dst": "CA12", "filing_date": "2025-01-15"}
        assert normalize_house_fd_trade(raw) is None

    def test_empty_name(self):
        raw = {"name": "", "filing_date": "2025-01-15"}
        assert normalize_house_fd_trade(raw) is None

    def test_no_state_dst(self):
        raw = {"name": "John Smith", "filing_date": "2025-01-15"}
        result = normalize_house_fd_trade(raw)
        assert result is not None
        assert result["state"] == ""
        assert result["district"] == ""

    def test_short_state_dst(self):
        raw = {"name": "John Smith", "state_dst": "NY", "filing_date": "2025-01-15"}
        result = normalize_house_fd_trade(raw)
        assert result is not None
        assert result["state"] == "NY"
        assert result["district"] == ""

    def test_empty_filing_date(self):
        raw = {"name": "John Smith", "filing_date": ""}
        result = normalize_house_fd_trade(raw)
        assert result is not None
        assert result["transaction_date"] == ""

    def test_ticker_always_empty(self):
        """House FD doesn't always include ticker, should be empty string"""
        raw = {"name": "John Smith", "filing_date": "2025-01-15"}
        result = normalize_house_fd_trade(raw)
        assert result["ticker"] == ""


class TestFetchHouseFDTrades:
    """Tests for fetch_house_fd_trades() - simplified"""

    def test_fetch_returns_list(self):
        """Test that fetch_house_fd_trades returns a list"""
        # Mock at module level to avoid complex setup
        import smart_money_tracker.house_reps as house_reps

        original = house_reps._download_and_extract_fds
        house_reps._download_and_extract_fds = lambda year: None
        result = fetch_house_fd_trades(days=90)
        house_reps._download_and_extract_fds = original
        assert isinstance(result, list)

    def test_fetch_no_data(self):
        """When download fails, return empty list"""
        import smart_money_tracker.house_reps as house_reps

        original = house_reps._download_and_extract_fds
        house_reps._download_and_extract_fds = lambda year: None
        result = fetch_house_fd_trades(days=90)
        house_reps._download_and_extract_fds = original
        assert result == []


class TestAggregateHouseRepsTrades:
    """Unit tests for aggregate_house_reps_trades()"""

    def test_empty_trades(self):
        result = aggregate_house_reps_trades([], days=90)
        assert result["total_trades"] == 0
        assert result["by_member"] == {}
        assert result["by_state"] == {}

    def test_single_trade(self):
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {
                "name": "John Smith",
                "state": "CA",
                "district": "12",
                "transaction_date": recent_date,
                "type": "Purchase",
            }
        ]
        result = aggregate_house_reps_trades(trades, days=90)
        assert result["total_trades"] == 1
        assert "John Smith" in result["by_member"]
        assert result["by_member"]["John Smith"]["total"] == 1
        assert result["by_member"]["John Smith"]["state"] == "CA"

    def test_multiple_members(self):
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {"name": "John Smith", "state": "CA", "transaction_date": recent_date},
            {"name": "Jane Doe", "state": "NY", "transaction_date": recent_date},
        ]
        result = aggregate_house_reps_trades(trades, days=90)
        assert result["total_trades"] == 2
        assert "John Smith" in result["by_member"]
        assert "Jane Doe" in result["by_member"]

    def test_by_state(self):
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {"name": "Person1", "state": "CA", "transaction_date": recent_date},
            {"name": "Person2", "state": "CA", "transaction_date": recent_date},
            {"name": "Person3", "state": "NY", "transaction_date": recent_date},
        ]
        result = aggregate_house_reps_trades(trades, days=90)
        assert result["by_state"]["CA"] == 2
        assert result["by_state"]["NY"] == 1

    def test_filter_by_days(self):
        old_date = (datetime.now().date() - timedelta(days=100)).strftime("%Y-%m-%d")
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        trades = [
            {"name": "Old Person", "state": "CA", "transaction_date": old_date},
            {"name": "Recent Person", "state": "NY", "transaction_date": recent_date},
        ]
        result = aggregate_house_reps_trades(trades, days=90)
        assert result["total_trades"] == 1
        assert "Recent Person" in result["by_member"]
        assert "Old Person" not in result["by_member"]


class TestRunHouseRepsTracker:
    """Integration tests for run_house_reps_tracker()"""

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_run_with_mocked_data(self, mock_fetch):
        """run_house_reps_tracker returns correct shape"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {
                "name": "John Smith",
                "state": "CA",
                "district": "12",
                "transaction_date": recent_date,
                "type": "Purchase",
                "ticker": "",
                "chamber": "house",
                "party": "",
            }
        ]

        result = run_house_reps_tracker(days=90)

        assert "trades" in result
        assert "aggregated" in result
        assert "report_section" in result
        assert "sources_used" in result
        assert result["sources_used"] == {"house_clerk_fd": True}
        assert len(result["trades"]) == 1

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_member_filter(self, mock_fetch):
        """member_filter filters by substring match"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "John Smith", "transaction_date": recent_date},
            {"name": "Jane Doe", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90, member_filter="John")
        assert len(result["trades"]) == 1
        assert result["trades"][0]["name"] == "John Smith"

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_member_filter_nonexistent(self, mock_fetch):
        """member_filter with non-existent member returns empty"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "John Smith", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90, member_filter="XYZ123")
        assert len(result["trades"]) == 0

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_case_insensitive_filter(self, mock_fetch):
        """Filters should be case-insensitive"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "John Smith", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90, member_filter="john")
        assert len(result["trades"]) == 1


class TestNonDefaultEntities:
    """Tests with entities outside default lists"""

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_unknown_member(self, mock_fetch):
        """Test with a member not in any default list"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "Unknown Representative XYZ", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90)
        assert len(result["trades"]) == 1
        assert result["trades"][0]["name"] == "Unknown Representative XYZ"

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_empty_member_filter(self, mock_fetch):
        """Empty string filter should not filter anything"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "John Smith", "transaction_date": recent_date},
            {"name": "Jane Doe", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90, member_filter="")
        assert len(result["trades"]) == 2

    @patch("smart_money_tracker.house_reps.fetch_house_fd_trades")
    def test_special_chars_in_name(self, mock_fetch):
        """Test with special characters in member name"""
        recent_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        mock_fetch.return_value = [
            {"name": "O'Brien, John Jr.", "transaction_date": recent_date},
        ]

        result = run_house_reps_tracker(days=90, member_filter="O'Brien")
        assert len(result["trades"]) == 1


class TestGenerateHouseRepsReport:
    """Tests for generate_house_reps_report()"""

    def test_generates_report(self, tmp_path):
        aggregated = {
            "by_member": {
                "John Smith": {
                    "total": 5,
                    "state": "CA",
                    "district": "12",
                    "filings": [],
                }
            },
            "by_state": {"CA": 5},
            "total_trades": 5,
            "days": 90,
        }

        report_path = tmp_path / "house-reps-test.md"
        with patch("smart_money_tracker.house_reps.REPORTS_DIR", tmp_path):
            section = generate_house_reps_report(aggregated, report_path)

        assert "House Representatives" in section
        assert "John Smith" in section
        assert "CA" in section

    def test_empty_report(self, tmp_path):
        aggregated = {
            "by_member": {},
            "by_state": {},
            "total_trades": 0,
            "days": 90,
        }

        report_path = tmp_path / "house-reps-empty.md"
        section = generate_house_reps_report(aggregated, report_path)

        assert "Total filings" in section
        assert "0" in section
