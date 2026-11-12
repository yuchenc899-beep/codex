import json
from pathlib import Path

import pytest

from smart_money_tracker.api_benchmark import ProbeResult
from smart_money_tracker.source_audit import (
    compare_congress_against_baseline,
    compare_house_against_baseline,
    compare_lobbying_against_baseline,
    compare_sec_against_baseline,
    get_secondary_references,
    get_source_inventory,
    load_doc_annotations,
    write_source_audit_artifacts,
)


class TestSourceInventory:
    def test_inventory_includes_active_and_reference_sources(self):
        inventory = get_source_inventory()
        ids = {item["id"] for item in inventory}

        assert "sec-submissions" in ids
        assert "insider-finance-static" in ids
        assert "house-clerk-financial-disclosures" in ids
        assert "lobbying-disclosure-doc" in ids
        assert "edgar-faq-doc" in ids

    def test_inventory_has_expected_classifications(self):
        inventory = {item["id"]: item for item in get_source_inventory()}

        assert inventory["sec-submissions"]["classification"] == "active"
        assert inventory["insider-finance-static"]["classification"] == "active"
        assert inventory["house-clerk-financial-disclosures"]["classification"] == "active"
        assert inventory["lobbying-disclosure-doc"]["classification"] == "reference-only"
        assert inventory["congress-trades-doc"]["classification"] == "reference-only"


class TestDocAnnotations:
    def test_doc_annotations_cover_all_local_docs(self):
        annotations = load_doc_annotations()
        paths = {Path(item["path"]).name for item in annotations}

        assert "congress-trades.json" in paths
        assert "lobbyingdisclosure.json" in paths
        assert "edgarSEC.md" in paths

    def test_doc_annotations_include_runtime_relationship(self):
        annotations = {Path(item["path"]).name: item for item in load_doc_annotations()}

        assert annotations["congress-trades.json"]["relationship"] in {
            "snapshot-baseline",
            "reference-only",
        }
        assert annotations["lobbyingdisclosure.json"]["classification"] == "reference-only"
        assert annotations["congress-trades.json"]["audited_source_id"] == "congress-trades-doc"
        assert annotations["edgarSEC.md"]["secondary_reference_urls"]


class TestSecondaryReferences:
    def test_secondary_references_cover_active_families(self):
        references = get_secondary_references()
        families = {item["family"] for item in references}

        assert {"sec", "congress", "house", "lobbying"}.issubset(families)


class TestBaselineComparisons:
    def test_compare_sec_against_baseline_verified(self):
        submissions = {
            "name": "BERKSHIRE HATHAWAY INC",
            "filings": {"recent": {"form": ["13F-HR"], "filingDate": ["2026-02-14"]}},
        }

        result = compare_sec_against_baseline(submissions, "0001067983")

        assert result["status"] == "verified"
        assert result["baseline_match"] is True

    def test_compare_congress_against_baseline_detects_missing_overlap(self):
        sample_trade = {"firstName": "Nancy", "lastName": "Pelosi", "symbol": "AAPL"}
        baseline_trade = {"office": "Nancy Pelosi", "amount": "$1,001 - $15,000"}

        result = compare_congress_against_baseline(sample_trade, baseline_trade, "200", "200")

        assert result["baseline_match"] is False
        assert result["discrepancies"]

    def test_compare_house_against_baseline_verified(self):
        sample_trade = {"name": "Rep. Example", "transaction_date": "2026-05-01", "chamber": "house"}

        result = compare_house_against_baseline(sample_trade, "200")

        assert result["status"] == "verified"
        assert result["baseline_match"] is True

    def test_compare_lobbying_against_baseline_tracks_migration(self):
        result = compare_lobbying_against_baseline(
            has_deprecation_notice=True,
            senate_status="200",
            successor_status="200",
        )

        assert result["status"] == "reference-verified"
        assert result["baseline_match"] is True


class TestArtifactWriting:
    def test_write_source_audit_artifacts_creates_expected_files(self, tmp_path):
        audit_result = {
            "inventory": [{"id": "sec-submissions"}],
            "docs": [{"path": "docs/example.md"}],
            "probes": [{"name": "SEC submissions", "status": "200"}],
            "verifications": [{"source_id": "sec-submissions", "status": "verified"}],
            "verification_evidence": [{"source_id": "sec-submissions", "command": "python3 main.py --verify-sources"}],
            "secondary_references": [{"family": "sec", "url": "https://www.sec.gov/about/developer-resources"}],
            "secondary_reference_checks": [{"family": "sec", "status": "reference-confirmed", "summary": "Official docs available."}],
            "doc_corrections": [{"path": "docs/example.md", "classification": "reference-only", "relationship": "reference-only"}],
            "discrepancies": [{"source_id": "congress", "reason": "schema mismatch"}],
            "open_questions": [
                "Ask the user if congressional source verification finds multiple plausible authorities or if a product-level source decision changes beyond the current InsiderFinance runtime policy."
            ],
            "generated_at": "2026-05-06T00:00:00Z",
        }

        paths = write_source_audit_artifacts(audit_result, output_dir=tmp_path)

        latest_json = tmp_path / "source-verification-latest.json"
        latest_md = tmp_path / "source-discrepancies-latest.md"

        assert latest_json.exists()
        assert latest_md.exists()
        assert paths["latest_json"] == str(latest_json)
        assert paths["latest_markdown"] == str(latest_md)

        payload = json.loads(latest_json.read_text())
        assert payload["verifications"][0]["source_id"] == "sec-submissions"
        assert payload["verification_evidence"][0]["command"] == "python3 main.py --verify-sources"
        assert "schema mismatch" in latest_md.read_text()


class TestProbeResultSerialization:
    def test_probe_result_dataclass_works_with_audit_inputs(self):
        probe = ProbeResult(
            name="SEC submissions",
            method="GET",
            url="https://data.sec.gov/submissions/CIK0001067983.json",
            status="200",
            elapsed_ms=120.5,
            bytes_read=1234,
        )

        assert probe.name == "SEC submissions"
        assert probe.status == "200"
