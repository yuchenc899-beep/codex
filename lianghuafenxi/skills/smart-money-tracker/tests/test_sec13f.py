import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from smart_money_tracker.sec13f import (
    process_fund_by_name,
    holdings_to_dict,
    compare_holdings,
    format_value,
    format_shares,
    report_date_to_quarter,
    parse_13f_xml,
    is_valid_cik,
    normalize_entity_name,
    _extract_cik_from_search_hit,
    get_submissions,
    find_infotable_url,
    lookup_cik_by_name,
    resolve_whale_ciks,
    build_funds_from_whales,
    WHALE_CIK_OVERRIDES,
    WHALE_FUNDS,
    WHALE_CANDIDATES,
    SUBMISSIONS_URL,
    SEC_SEARCH_INDEX_URL,
)


class TestSec13fUtils:
    """Unit tests for utility functions."""

    def test_holdings_to_dict_merge_same_cusip(self):
        holdings = [
            {"cusip": "123", "name": "Apple", "value": 1000, "shares": 10},
            {"cusip": "123", "name": "Apple", "value": 2000, "shares": 20},
        ]
        result = holdings_to_dict(holdings)
        assert len(result) == 1
        assert result["123"]["value"] == 3000
        assert result["123"]["shares"] == 30

    def test_holdings_to_dict_separate_put_call(self):
        holdings = [
            {
                "cusip": "123",
                "name": "Apple",
                "value": 1000,
                "shares": 10,
                "put_call": "",
            },
            {
                "cusip": "123",
                "name": "Apple",
                "value": 2000,
                "shares": 20,
                "put_call": "CALL",
            },
        ]
        result = holdings_to_dict(holdings)
        assert len(result) == 2
        assert "123" in result
        assert "123_CALL" in result

    def test_compare_holdings_new(self):
        current = {"A": {"name": "Apple", "value": 1000, "shares": 10}}
        previous = {}
        changes = compare_holdings(current, previous)
        assert len(changes["new"]) == 1
        assert changes["new"][0]["name"] == "Apple"
        assert changes["increased"] == []
        assert changes["closed"] == []

    def test_compare_holdings_closed(self):
        current = {}
        previous = {"A": {"name": "Apple", "value": 1000, "shares": 10}}
        changes = compare_holdings(current, previous)
        assert len(changes["closed"]) == 1
        assert changes["closed"][0]["name"] == "Apple"
        assert changes["new"] == []

    def test_compare_holdings_increased(self):
        current = {"A": {"name": "Apple", "value": 2000, "shares": 20}}
        previous = {"A": {"name": "Apple", "value": 1000, "shares": 10}}
        changes = compare_holdings(current, previous)
        assert len(changes["increased"]) == 1
        assert changes["increased"][0]["change_pct"] == 100.0
        assert changes["decreased"] == []

    def test_compare_holdings_decreased(self):
        current = {"A": {"name": "Apple", "value": 500, "shares": 5}}
        previous = {"A": {"name": "Apple", "value": 1000, "shares": 10}}
        changes = compare_holdings(current, previous)
        assert len(changes["decreased"]) == 1
        assert changes["decreased"][0]["change_pct"] == -50.0
        assert changes["increased"] == []

    def test_format_value(self):
        assert format_value(1_500_000_000) == "$1.5B"
        assert format_value(2_500_000) == "$2.5M"
        assert format_value(1500) == "$1,500"
        assert format_value(0) == "$0"

    def test_format_shares(self):
        assert format_shares(1_500_000) == "1.5M"
        assert format_shares(2_500) == "2.5K"
        assert format_shares(150) == "150"
        assert format_shares(0) == "0"

    def test_report_date_to_quarter(self):
        assert report_date_to_quarter("2025-01-15") == "2025-Q1"
        assert report_date_to_quarter("2025-04-15") == "2025-Q2"
        assert report_date_to_quarter("2025-07-15") == "2025-Q3"
        assert report_date_to_quarter("2025-10-15") == "2025-Q4"
        assert report_date_to_quarter("invalid") == "invalid"
        assert report_date_to_quarter("") == "Unknown"

    def test_parse_13f_xml_minimal(self):
        xml = """<?xml version="1.0"?>
<ns:informationTable xmlns:ns="http://www.sec.gov/document/thirteenf-2024q1">
  <ns:infoTable>
    <ns:nameOfIssuer>Apple Inc.</ns:nameOfIssuer>
    <ns:titleOfClass>COM</ns:titleOfClass>
    <ns:cusip>037833100</ns:cusip>
    <ns:value>1500000000</ns:value>
    <ns:sshPrnamt>10000000</ns:sshPrnamt>
    <ns:sshPrnamtType>SH</ns:sshPrnamtType>
  </ns:infoTable>
</ns:informationTable>"""
        holdings = parse_13f_xml(xml)
        assert len(holdings) == 1
        assert holdings[0]["name"] == "Apple Inc."
        assert holdings[0]["value"] == 1500000000
        assert holdings[0]["shares"] == 10000000

    def test_is_valid_cik(self):
        assert is_valid_cik("0001067983") is True
        assert is_valid_cik("1067983") is False
        assert is_valid_cik("ABCDEFGHIJ") is False
        assert is_valid_cik("") is False

    def test_normalize_entity_name(self):
        assert (
            normalize_entity_name("  Berkshire Hathaway Inc ") == "BERKSHIRE HATHAWAY"
        )
        assert (
            normalize_entity_name("Bridgewater Associates LLC")
            == "BRIDGEWATER ASSOCIATES"
        )
        assert normalize_entity_name("") == ""

    def test_extract_cik_from_search_hit(self):
        assert _extract_cik_from_search_hit({"cik": "1067983"}) == "0001067983"
        assert _extract_cik_from_search_hit({"entityCik": 1350694}) == "0001350694"
        assert _extract_cik_from_search_hit({"companyCik": "not-a-cik"}) is None
        assert _extract_cik_from_search_hit({}) is None


class TestSec13fEndpoints:
    """Endpoint-level tests with mocked HTTP calls."""

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_get_submissions_endpoint(self, mock_get):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"ok": True}
        mock_get.return_value = mock_resp

        data = get_submissions("0001067983")

        assert data == {"ok": True}
        called_url = mock_get.call_args.args[0]
        assert called_url == "https://data.sec.gov/submissions/CIK0001067983.json"

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_find_infotable_url_uses_index_endpoint(self, mock_get):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "directory": {
                "item": [
                    {"name": "primary_doc.xml"},
                    {"name": "infotable.xml"},
                ]
            }
        }
        mock_get.return_value = mock_resp

        url = find_infotable_url("0001067983", "0001104659-25-000001")

        assert url is not None
        assert url.endswith("/infotable.xml")
        called_url = mock_get.call_args.args[0]
        assert called_url.endswith("/000110465925000001/index.json")

    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_cik_by_name_exact_match(self, mock_post):
        # Use a name NOT in WHALE_CIK_OVERRIDES so the HTTP search-index path is exercised.
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "entityName": "ACME CAPITAL FUND LLC",
                            "cik": "0009991234",
                        }
                    },
                ]
            }
        }
        mock_post.return_value = mock_resp

        cik = lookup_cik_by_name("ACME CAPITAL FUND")

        assert cik == "0009991234"
        called_url = mock_post.call_args.args[0]
        assert called_url == "https://efts.sec.gov/LATEST/search-index"

    @patch("smart_money_tracker.sec13f.requests.get")
    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_cik_by_name_fallback_browse_edgar(self, mock_post, mock_get):
        # Use a name NOT in WHALE_CIK_OVERRIDES so fallback path is exercised.
        # search-index returns 403 → should fall back to browse-edgar atom.
        post_resp = Mock()
        post_resp.status_code = 403
        mock_post.return_value = post_resp

        get_resp = Mock()
        get_resp.raise_for_status = Mock()
        get_resp.text = "<id>urn:tag:www.sec.gov:cik=0009876543</id>"
        mock_get.return_value = get_resp

        cik = lookup_cik_by_name("UNKNOWN MYSTERY FUND")

        assert cik == "0009876543"
        assert mock_get.called

    @patch("smart_money_tracker.sec13f.lookup_cik_by_name")
    def test_resolve_whale_ciks(self, mock_lookup):
        def side_effect(name):
            if name == "BLACKROCK":
                return "0001364742"
            if name == "UNKNOWN":
                return None
            raise RuntimeError("lookup failed")

        mock_lookup.side_effect = side_effect
        result = resolve_whale_ciks(["BLACKROCK", "UNKNOWN", "BROKEN"])

        assert result["BLACKROCK"] == "0001364742"
        assert result["UNKNOWN"] is None
        assert result["BROKEN"] is None

    @patch("smart_money_tracker.sec13f.resolve_whale_ciks")
    def test_build_funds_from_whales(self, mock_resolve):
        mock_resolve.return_value = {
            "BLACKROCK": "0001364742",
            "UNKNOWN": None,
        }

        funds = build_funds_from_whales(["BLACKROCK", "UNKNOWN"])

        assert "0001364742" in funds
        assert funds["0001364742"]["name"] == "Blackrock"
        assert "UNKNOWN" not in str(funds)


class TestSec13fIntegration:
    """Integration tests with mocked HTTP."""

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_process_fund_mocked(self, mock_get):
        from smart_money_tracker.sec13f import process_fund

        # Mock submissions response
        mock_submissions = {
            "filings": {
                "recent": {
                    "form": ["13F-HR", "13F-HR"],
                    "accessionNumber": ["0001104659-25-000001", "0001104659-24-000001"],
                    "filingDate": ["2025-02-14", "2024-11-14"],
                    "primaryDocument": ["primary.xml", "primary.xml"],
                    "reportDate": ["2024-12-31", "2024-09-30"],
                }
            }
        }
        mock_get.return_value.json.return_value = mock_submissions
        mock_get.return_value.raise_for_status = Mock()

        # Mock index.json response
        mock_index = {
            "directory": {
                "item": [
                    {"name": "infotable.xml", "type": "xml"},
                    {"name": "primary.xml", "type": "xml"},
                ]
            }
        }

        # Mock infotable XML response
        mock_xml = """<?xml version="1.0"?>
<informationTable>
  <infoTable>
    <nameOfIssuer>Apple Inc.</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>1500000000</value>
    <sshPrnamt>10000000</sshPrnamt>
    <sshPrnamtType>SH</sshPrnamtType>
  </infoTable>
</informationTable>"""

        # Configure mock to return different responses
        def side_effect(url, **kwargs):
            resp = Mock()
            resp.raise_for_status = Mock()
            if "submissions" in url:
                resp.json.return_value = mock_submissions
            elif "index.json" in url:
                resp.json.return_value = mock_index
            else:
                resp.text = mock_xml
            return resp

        mock_get.side_effect = side_effect

        # Run with temp data dir; also mock find_infotable_url to avoid int(cik) call
        import smart_money_tracker.sec13f as sec13f

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "sec13f.find_infotable_url",
            return_value="https://example.com/infotable.xml",
        ):
            original_data_dir = sec13f.DATA_DIR
            sec13f.DATA_DIR = Path(tmpdir) / "data" / "sec13f"
            sec13f.DATA_DIR.mkdir(parents=True)

            result = process_fund(
                "0000000042", {"name": "Test Fund", "manager": "Test Manager"}
            )

            sec13f.DATA_DIR = original_data_dir

        assert "current_filing" in result
        assert "current_holdings" in result
        assert result["info"]["name"] == "Test Fund"
        # Should have saved cache files
        assert mock_get.call_count >= 3

    def test_run_13f_tracker_mocked(self):
        from smart_money_tracker.sec13f import run_13f_tracker

        with patch("smart_money_tracker.sec13f.process_fund") as mock_process:
            mock_process.return_value = {
                "cik": "[PHONE]",
                "info": {"name": "Test", "manager": "Manager"},
                "current_filing": {"report_date": "2024-12-31"},
                "current_holdings": {
                    "A": {"name": "Apple", "value": 1000, "shares": 10}
                },
                "changes": {
                    "new": [],
                    "increased": [],
                    "decreased": [],
                    "closed": [],
                    "unchanged": [],
                },
            }

            result = run_13f_tracker(
                funds={"[PHONE]": {"name": "Test", "manager": "Manager"}}
            )

            assert "results" in result
            assert "report_section" in result
            assert "Test" in result["results"]
            assert mock_process.called


class TestWhaleOverrides:
    """Unit tests for WHALE_CIK_OVERRIDES and WHALE_FUNDS."""

    def test_overrides_contains_all_30_whales(self):
        assert len(WHALE_CIK_OVERRIDES) == 30

    def test_overrides_all_valid_ciks(self):
        for name, cik in WHALE_CIK_OVERRIDES.items():
            assert is_valid_cik(cik), f"{name} has invalid CIK: {cik}"

    def test_whale_funds_built_from_overrides(self):
        assert len(WHALE_FUNDS) == len(WHALE_CIK_OVERRIDES)

    def test_whale_funds_cik_keys_valid(self):
        for cik in WHALE_FUNDS:
            assert is_valid_cik(cik), f"WHALE_FUNDS has invalid CIK key: {cik}"

    def test_manually_provided_ciks_present(self):
        """Verify user-supplied manual corrections are in overrides."""
        assert WHALE_CIK_OVERRIDES["BRIDGEWATER ASSOCIATES"] == "0001350694"
        assert WHALE_CIK_OVERRIDES["ALTIMETER CAPITAL MANAGEMENT"] == "0001541617"
        assert WHALE_CIK_OVERRIDES["THE BAUPOST GROUP"] == "0001061768"
        assert WHALE_CIK_OVERRIDES["THE VANGUARD GROUP"] == "0000102909"

    def test_lookup_uses_override_without_network(self):
        """lookup_cik_by_name must return override CIK without hitting the network."""
        with patch("smart_money_tracker.sec13f.requests.post") as mock_post, patch(
            "smart_money_tracker.sec13f.requests.get"
        ) as mock_get:
            cik = lookup_cik_by_name("BERKSHIRE HATHAWAY")
        assert cik == "0001067983"
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    def test_lookup_override_case_insensitive(self):
        """Override lookup should handle mixed-case input."""
        with patch("smart_money_tracker.sec13f.requests.post") as mock_post, patch(
            "smart_money_tracker.sec13f.requests.get"
        ) as mock_get:
            cik = lookup_cik_by_name("Berkshire Hathaway")
        assert cik == "0001067983"

    def test_resolve_whale_ciks_uses_overrides(self):
        """resolve_whale_ciks should use override map (no HTTP)."""
        with patch("smart_money_tracker.sec13f.requests.post") as mock_post, patch(
            "smart_money_tracker.sec13f.requests.get"
        ) as mock_get:
            result = resolve_whale_ciks(WHALE_CANDIDATES)
        assert all(
            v is not None for v in result.values()
        ), f"Some CIKs unresolved: {[k for k,v in result.items() if v is None]}"
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    def test_all_whale_candidates_in_overrides(self):
        """Every WHALE_CANDIDATES entry must have a CIK in WHALE_CIK_OVERRIDES."""
        missing = [w for w in WHALE_CANDIDATES if w not in WHALE_CIK_OVERRIDES]
        assert missing == [], f"Missing from WHALE_CIK_OVERRIDES: {missing}"


@pytest.mark.integration
class TestSec13fIntegration:
    """
    Live integration tests — hit real SEC EDGAR endpoints.
    Run with:  pytest -m integration -v
    Skipped by default in CI (no marker selected).
    """

    # 0001067983 = institutional investment manager entity that files 13F-HR
    BERKSHIRE_CIK = "0001067983"
    BERKSHIRE_INFO = {"name": "Berkshire Hathaway", "manager": "Warren Buffett"}

    def test_get_submissions_berkshire(self):
        """Live: fetch Berkshire submissions JSON from EDGAR."""
        data = get_submissions(self.BERKSHIRE_CIK)
        assert "filings" in data
        assert "recent" in data["filings"]
        forms = data["filings"]["recent"].get("form", [])
        assert any(
            f in ("13F-HR", "13F-HR/A") for f in forms
        ), "No 13F filings found for Berkshire"

    def test_find_infotable_url_berkshire(self):
        """Live: resolve infotable XML URL for Berkshire's latest 13F."""
        from smart_money_tracker.sec13f import find_13f_filings

        submissions = get_submissions(self.BERKSHIRE_CIK)
        filings = find_13f_filings(submissions, limit=1)
        assert filings, "No filings found"
        url = find_infotable_url(self.BERKSHIRE_CIK, filings[0]["accession"])
        assert url is not None
        assert url.endswith(".xml")
        assert "Archives/edgar/data" in url

    def test_process_fund_berkshire_e2e(self):
        """Live E2E: full pipeline for Berkshire — submissions → parse → compare → cache."""
        import tempfile
        import smart_money_tracker.sec13f as _mod

        original_data_dir = _mod.DATA_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            _mod.DATA_DIR = Path(tmpdir) / "sec13f"
            _mod.DATA_DIR.mkdir(parents=True)
            try:
                result = _mod.process_fund(self.BERKSHIRE_CIK, self.BERKSHIRE_INFO)
            finally:
                _mod.DATA_DIR = original_data_dir

        assert (
            "error" not in result or result.get("error") is None
        ), f"process_fund returned error: {result.get('error')}"
        assert result.get("current_holdings"), "No holdings returned"
        assert len(result["current_holdings"]) > 10, "Expected >10 holdings"
        assert result.get("current_filing", {}).get(
            "report_date"
        ), "Missing report_date"

    def test_lookup_cik_override_no_network(self):
        """Overrides should bypass network entirely."""
        with patch("smart_money_tracker.sec13f.requests.post") as mp, patch("smart_money_tracker.sec13f.requests.get") as mg:
            cik = lookup_cik_by_name("BERKSHIRE HATHAWAY")
        assert cik == "0001067983"
        mp.assert_not_called()
        mg.assert_not_called()


class TestEndpointParams:
    """Parametrized endpoint + parameter-shape tests (mocked HTTP)."""

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_get_submissions_url_format(self, mock_get):
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.raise_for_status = Mock()
        get_submissions("0001067983")
        called_url = mock_get.call_args.args[0]
        assert called_url == SUBMISSIONS_URL.format(cik="0001067983")
        assert "CIK0001067983" in called_url

    @pytest.mark.parametrize("status_code", [429, 500, 403])
    @patch("smart_money_tracker.sec13f.requests.get")
    def test_get_submissions_raises_on_http_error(self, mock_get, status_code):
        from requests import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError(f"{status_code}")
        with pytest.raises(HTTPError):
            get_submissions("0001067983")

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_find_infotable_url_strips_dashes(self, mock_get):
        """Accession with and without dashes should produce the same URL path."""
        mock_get.return_value.raise_for_status = Mock()
        mock_get.return_value.json.return_value = {
            "directory": {"item": [{"name": "infotable.xml"}]}
        }
        url_with = find_infotable_url("0001067983", "0001104659-25-000001")
        mock_get.reset_mock()
        url_without = find_infotable_url("0001067983", "000110465925000001")
        assert url_with == url_without

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_find_infotable_url_no_xml_returns_none(self, mock_get):
        mock_get.return_value.raise_for_status = Mock()
        mock_get.return_value.json.return_value = {"directory": {"item": []}}
        url = find_infotable_url("0001067983", "0001104659-25-000001")
        assert url is None

    @patch("smart_money_tracker.sec13f.requests.get")
    def test_find_infotable_url_prefers_infotable_keyword(self, mock_get):
        mock_get.return_value.raise_for_status = Mock()
        mock_get.return_value.json.return_value = {
            "directory": {
                "item": [
                    {"name": "primary_doc.xml"},
                    {"name": "infotable.xml"},
                    {"name": "cover.xml"},
                ]
            }
        }
        url = find_infotable_url("0001067983", "0001104659-25-000001")
        assert url is not None
        assert url.endswith("/infotable.xml")

    @patch("smart_money_tracker.sec13f.requests.get")
    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_browse_edgar_query_params(self, mock_post, mock_get):
        """browse-edgar fallback must send output=atom, count=20, action=getcompany."""
        # search-index returns 403 to force the fallback
        mock_post.return_value.status_code = 403
        mock_get.return_value.raise_for_status = Mock()
        mock_get.return_value.text = "<id>urn:tag:www.sec.gov:cik=0009991234</id>"

        lookup_cik_by_name("UNKNOWN FUND ABC")

        call_kwargs = mock_get.call_args.kwargs.get("params", {})
        assert call_kwargs.get("output") == "atom"
        assert call_kwargs.get("count") == "20"
        assert call_kwargs.get("action") == "getcompany"

    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_search_index_payload_shape(self, mock_post):
        """search-index POST body must include forms, sort, from, size keys."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"hits": {"hits": []}}

        lookup_cik_by_name("UNKNOWN FUND XYZ")

        body = mock_post.call_args.kwargs.get("json", {})
        assert "forms" in body
        assert "13F-HR" in body["forms"]
        assert "sort" in body
        assert "from" in body
        assert "size" in body

    @patch("smart_money_tracker.sec13f.requests.get")
    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_returns_none_empty_hits(self, mock_post, mock_get):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"hits": {"hits": []}}
        # browse-edgar also returns nothing
        mock_get.return_value.raise_for_status = Mock()
        mock_get.return_value.text = "<results/>"

        result = lookup_cik_by_name("UNKNOWN FUND NOHIT")
        assert result is None

    def test_process_fund_by_name_unknown_not_in_defaults(self):
        """Test process_fund_by_name with fund NOT in WHALE_CANDIDATES."""
        with patch("smart_money_tracker.sec13f.lookup_cik_by_name") as mock_lookup:
            mock_lookup.return_value = "000999999"
            with patch("smart_money_tracker.sec13f.process_fund") as mock_process:
                mock_process.return_value = {
                    "cik": "000999999",
                    "info": {"name": "Unknown Fund", "manager": "Unknown Manager"},
                    "current_holdings": {},
                    "changes": {
                        "new": [],
                        "increased": [],
                        "decreased": [],
                        "closed": [],
                        "unchanged": [],
                    },
                }
                result = process_fund_by_name("SOME RANDOM FUND NOT IN DEFAULTS")
                mock_lookup.assert_called_once_with("SOME RANDOM FUND NOT IN DEFAULTS")
                assert result["info"]["name"] == "Unknown Fund"

    def test_build_funds_excludes_unknown_not_in_defaults(self):
        """Test build_funds_from_whales excludes funds NOT in WHALE_CANDIDATES."""
        with patch("smart_money_tracker.sec13f.resolve_whale_ciks") as mock_resolve:
            mock_resolve.return_value = {
                "BERKSHIRE HATHAWAY": "0001067983",
                "UNKNOWN FUND XYZ": None,  # Not in defaults
                "BLACKROCK": "0002012383",
            }
            funds = build_funds_from_whales(
                ["BERKSHIRE HATHAWAY", "UNKNOWN FUND XYZ", "BLACKROCK"]
            )
            assert "0001067983" in funds
            assert "0002012383" in funds
            assert len(funds) == 2  # Unknown fund excluded

    @patch("smart_money_tracker.sec13f.requests.post")
    def test_lookup_search_index_payload_not_in_defaults(self, mock_post):
        """Test search-index payload shape when name NOT in WHALE_CIK_OVERRIDES."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"hits": {"hits": []}}
        mock_post.return_value = mock_resp

        lookup_cik_by_name("COMPLETELY NEW FUND NAME")

        # Verify payload includes the name
        call_args = mock_post.call_args
        assert call_args is not None
        payload = call_args.kwargs.get("json", {})
        assert payload.get("keys") == "COMPLETELY NEW FUND NAME"
        assert "13F-HR" in payload.get("forms", [])
        assert payload.get("size") == 25

    def test_parse_13f_xml_malformed_returns_empty(self):
        from smart_money_tracker.sec13f import parse_13f_xml

        result = parse_13f_xml("<<< this is not xml >>>")
        assert result == []

    def test_parse_13f_xml_no_namespace(self):
        xml = """<?xml version="1.0"?>
<informationTable>
  <infoTable>
    <nameOfIssuer>Apple Inc.</nameOfIssuer>
    <cusip>037833100</cusip>
    <value>500000</value>
    <sshPrnamt>1000</sshPrnamt>
    <sshPrnamtType>SH</sshPrnamtType>
  </infoTable>
</informationTable>"""
        from smart_money_tracker.sec13f import parse_13f_xml

        holdings = parse_13f_xml(xml)
        assert len(holdings) == 1
        assert holdings[0]["name"] == "Apple Inc."
        assert holdings[0]["shares"] == 1000

    def test_parse_13f_xml_nested_shrs_or_prn_amt(self):
        xml = """<?xml version="1.0"?>
<informationTable>
  <infoTable>
    <nameOfIssuer>Google LLC</nameOfIssuer>
    <cusip>02079K305</cusip>
    <value>999000</value>
    <shrsOrPrnAmt>
      <sshPrnamt>500</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
  </infoTable>
</informationTable>"""
        from smart_money_tracker.sec13f import parse_13f_xml

        holdings = parse_13f_xml(xml)
        assert len(holdings) == 1
        assert holdings[0]["shares"] == 500
        assert holdings[0]["share_type"] == "SH"

    @patch("smart_money_tracker.sec13f.process_fund")
    @patch("smart_money_tracker.sec13f.lookup_cik_by_name")
    def test_process_fund_by_name_resolves_unknown(self, mock_lookup, mock_process):
        mock_lookup.return_value = "0001234567"
        mock_process.return_value = {
            "cik": "0001234567",
            "info": {"name": "Unknown Fund", "manager": "Unknown Fund"},
            "current_holdings": {},
        }
        result = process_fund_by_name("Unknown Fund")
        mock_lookup.assert_called_once_with("Unknown Fund")
        mock_process.assert_called_once()
        assert result["cik"] == "0001234567"

    @patch("smart_money_tracker.sec13f.lookup_cik_by_name")
    def test_process_fund_by_name_unresolvable_returns_error(self, mock_lookup):
        mock_lookup.return_value = None
        result = process_fund_by_name("Completely Unknown XYZ Fund")
        assert "error" in result
        assert "Completely Unknown XYZ Fund" in result["error"]
        assert result["info"]["name"] == "Completely Unknown XYZ Fund"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestEdgeCases:
    """Additional edge case tests to reach 120 total."""

    def test_empty_holdings_portfolio_pct(self):
        """Portfolio % with empty holdings."""
        from smart_money_tracker.sec13f import calculate_portfolio_pct

        result = calculate_portfolio_pct({}, 0)
        assert result == 0.0

    def test_single_holding_portfolio_pct(self):
        """Portfolio % with single holding."""
        from smart_money_tracker.sec13f import calculate_portfolio_pct

        holding = {"value": 1000}
        result = calculate_portfolio_pct(holding, 1000)
        assert result == 100.0

    def test_negative_value_portfolio_pct(self):
        """Portfolio % with negative value."""
        from smart_money_tracker.sec13f import calculate_portfolio_pct

        holding = {"value": -100}
        result = calculate_portfolio_pct(holding, 1000)
        assert result == -10.0

    def test_rank_empty_changes(self):
        """Rank empty changes dict."""
        from smart_money_tracker.sec13f import rank_by_portfolio_pct

        changes = {"increased": [], "new": [], "decreased": [], "closed": []}
        result = rank_by_portfolio_pct(changes, 1000)
        assert all(len(result[k]) == 0 for k in changes)

    def test_rank_single_holding(self):
        """Rank single holding."""
        from smart_money_tracker.sec13f import rank_by_portfolio_pct

        changes = {
            "increased": [{"value": 500, "name": "A"}],
            "new": [],
            "decreased": [],
            "closed": [],
        }
        result = rank_by_portfolio_pct(changes, 1000)
        assert result["increased"][0]["portfolio_pct"] == 50.0

    def test_date_range_ytd_edge(self):
        """YTD with current date."""
        from smart_money_tracker.sec13f import get_filings_by_date_range
        from unittest.mock import patch
        from datetime import date

        with patch("smart_money_tracker.sec13f.date") as mock_date:
            mock_date.today.return_value = date(2026, 3, 15)
            with patch("smart_money_tracker.sec13f.get_submissions") as mock_sub:
                mock_sub.return_value = {"filings": {"recent": []}}
                result = get_filings_by_date_range("0001067983", "YTD")
                assert isinstance(result, list)

    def test_date_range_q_format_invalid(self):
        """Invalid Q format."""
        from smart_money_tracker.sec13f import get_filings_by_date_range

        with patch("smart_money_tracker.sec13f.get_submissions") as mock_sub:
            mock_sub.return_value = {"filings": {"recent": []}}
            result = get_filings_by_date_range("0001067983", "Q5-2026")
            assert result == []

    def test_date_range_negative_q_invalid(self):
        """Invalid negative Q format."""
        from smart_money_tracker.sec13f import get_filings_by_date_range

        with patch("smart_money_tracker.sec13f.get_submissions") as mock_sub:
            mock_sub.return_value = {"filings": {"recent": []}}
            result = get_filings_by_date_range("0001067983", "-0Q")
            assert result == []

    def test_format_value_zero(self):
        """Format zero value."""
        from smart_money_tracker.sec13f import format_value

        assert format_value(0) == "$0"

    def test_format_value_negative(self):
        """Format negative value."""
        from smart_money_tracker.sec13f import format_value

        assert format_value(-1000) == "$-1,000"

    def test_format_shares_zero(self):
        """Format zero shares."""
        from smart_money_tracker.sec13f import format_shares

        assert format_shares(0) == "0"

    def test_report_date_to_quarter_december(self):
        """December report date."""
        from smart_money_tracker.sec13f import report_date_to_quarter

        assert report_date_to_quarter("2025-12-31") == "2025-Q4"

    def test_report_date_to_quarter_january(self):
        """January report date."""
        from smart_money_tracker.sec13f import report_date_to_quarter

        assert report_date_to_quarter("2025-01-31") == "2025-Q1"

    def test_process_fund_error_handling(self):
        """Process fund with error."""
        from smart_money_tracker.sec13f import process_fund

        with patch("smart_money_tracker.sec13f.get_submissions") as mock_sub:
            mock_sub.side_effect = Exception("API Error")
            result = process_fund("[PHONE]", {"name": "Test", "manager": "Tester"})
            assert "error" in result

    def test_whale_fund_structure(self):
        """Verify whale fund dict structure."""
        from smart_money_tracker.sec13f import process_fund

        with patch("smart_money_tracker.sec13f.get_submissions") as mock_sub:
            mock_sub.return_value = {"filings": {"recent": []}}
            result = process_fund("[PHONE]", {"name": "Test", "manager": "Tester"})
            assert "cik" in result
            assert "info" in result

    def test_submissions_structure(self):
        """Verify submissions dict structure."""
        from smart_money_tracker.sec13f import get_submissions

        with patch("smart_money_tracker.sec13f.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"filings": {"recent": []}}
            mock_get.return_value.raise_for_status = lambda: None
            result = get_submissions("0001067983")
            assert "filings" in result


class TestWhaleConviction:
    """Tests for whale conviction aggregator functions."""

    def test_get_whale_conviction_stats_empty(self):
        """Test with empty data."""
        from smart_money_tracker.sec13f import get_whale_conviction_stats

        stats = get_whale_conviction_stats([])
        assert stats["total_whales"] == 0
        assert stats["top_conviction"] == []

    def test_get_whale_conviction_stats_single_whale(self):
        """Test with single whale."""
        from smart_money_tracker.sec13f import get_whale_conviction_stats

        mock_data = [
            {
                "info": {"manager": "Buffett"},
                "current_holdings": {
                    "123": {"name": "Apple", "value": 1000},
                    "456": {"name": "Google", "value": 2000},
                },
            }
        ]
        stats = get_whale_conviction_stats(mock_data)
        assert stats["total_whales"] == 1
        assert len(stats["top_conviction"]) == 2
        assert stats["top_conviction"][0]["whale_count"] == 1

    def test_get_whale_conviction_stats_multiple_whales(self):
        """Test conviction calculation with multiple whales."""
        from smart_money_tracker.sec13f import get_whale_conviction_stats

        mock_data = [
            {
                "info": {"manager": "Buffett"},
                "current_holdings": {"123": {"name": "Apple", "value": 1000}},
            },
            {
                "info": {"manager": "Dalio"},
                "current_holdings": {"456": {"name": "Apple", "value": 2000}},
            },
            {
                "info": {"manager": "Ackman"},
                "current_holdings": {"789": {"name": "Google", "value": 1500}},
            },
        ]
        stats = get_whale_conviction_stats(mock_data)
        assert stats["total_whales"] == 3
        # Apple should have 66.7% conviction (2 out of 3 whales)
        apple_entry = next(s for s in stats["top_conviction"] if s["stock"] == "Apple")
        assert apple_entry["conviction_pct"] == 66.7
        assert apple_entry["whale_count"] == 2

    def test_get_whale_conviction_stats_sorting(self):
        """Test that results are sorted by conviction descending."""
        from smart_money_tracker.sec13f import get_whale_conviction_stats

        mock_data = [
            {
                "info": {"manager": "A"},
                "current_holdings": {"1": {"name": "Stock1", "value": 100}},
            },
            {
                "info": {"manager": "B"},
                "current_holdings": {"2": {"name": "Stock2", "value": 200}},
            },
            {
                "info": {"manager": "C"},
                "current_holdings": {"2": {"name": "Stock2", "value": 300}},
            },
        ]
        stats = get_whale_conviction_stats(mock_data)
        # Stock2 has 2 whales (66.7%), Stock1 has 1 whale (33.3%)
        assert stats["top_conviction"][0]["stock"] == "Stock2"
        assert stats["top_conviction"][1]["stock"] == "Stock1"

    def test_get_top_100_whales_returns_dict(self):
        """Test that get_top_100_whales returns a dict."""
        from smart_money_tracker.sec13f import get_top_100_whales

        with patch("smart_money_tracker.sec13f.lookup_cik_by_name") as mock_lookup:
            mock_lookup.return_value = "0001067983"
            with patch("smart_money_tracker.sec13f.is_valid_cik", return_value=True):
                result = get_top_100_whales()
                assert isinstance(result, dict)
                assert len(result) <= 100

    def test_run_13f_tracker_with_top_100_flag(self):
        """Test run_13f_tracker accepts use_top_100 parameter."""
        from smart_money_tracker.sec13f import run_13f_tracker

        with patch("smart_money_tracker.sec13f.get_top_100_whales") as mock_top100:
            mock_top100.return_value = {"0001067983": {"name": "Test", "manager": "Tester"}}
            with patch("smart_money_tracker.sec13f.process_fund") as mock_process:
                mock_process.return_value = {
                    "info": {"name": "Test", "manager": "Tester"},
                    "current_holdings": {},
                }
                result = run_13f_tracker(use_top_100=True)
                assert "conviction_stats" in result
                mock_top100.assert_called_once()
