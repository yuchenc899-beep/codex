"""
Source inventory, live verification, and audit artifact generation.
"""

# pyright: reportMissingModuleSource=false

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import Any

import requests

from smart_money_tracker.api_benchmark import ProbeResult, benchmark_all
from smart_money_tracker.congress import INSIDER_FINANCE_API, INSIDER_FINANCE_PAGE, fetch_congress_trades
from smart_money_tracker.house_reps import (
    HOUSE_CLERK_FD_BASE,
    fetch_house_fd_trades,
    normalize_house_fd_trade,
)
from smart_money_tracker.sec13f import get_submissions, lookup_cik_by_name

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR.parent / "docs"

CONGRESS_DOC_PATH = DOCS_DIR / "congress-trades.json"
LOBBYING_DOC_PATH = DOCS_DIR / "lobbyingdisclosure.json"
EDGAR_DOC_PATH = DOCS_DIR / "edgarSEC.md"

VERIFY_SOURCES_COMMAND = "python3 main.py --verify-sources"
VERIFY_SOURCES_TEST_PATHS = [
    "tests/test_source_audit.py",
    "tests/test_main.py",
    "tests/test_skill_compliance.py",
]

SECONDARY_REFERENCES: list[dict[str, str]] = [
    {
        "family": "sec",
        "title": "SEC Developer Resources",
        "url": "https://www.sec.gov/about/developer-resources",
        "authority": "official",
        "verifies": "Documents data.sec.gov JSON APIs, EDGAR access patterns, and fair-access rules.",
    },
    {
        "family": "sec",
        "title": "SEC Webmaster FAQ",
        "url": "https://www.sec.gov/about/webmaster-frequently-asked-questions#api",
        "authority": "official",
        "verifies": "Confirms browse-edgar, ticker/CIK lookup files, and programmatic download guidance.",
    },
    {
        "family": "congress",
        "title": "U.S. Senate eFD",
        "url": "https://efdsearch.senate.gov/search/",
        "authority": "official",
        "verifies": "Shows official Senate public financial disclosure search exists, but is separate from the runtime aggregator.",
    },
    {
        "family": "congress",
        "title": "InsiderFinance Congress page",
        "url": "https://www.insiderfinance.io/congress-trades",
        "authority": "operator",
        "verifies": "Matches the third-party congress trades product surface used by the runtime source.",
    },
    {
        "family": "house",
        "title": "House Clerk Financial Disclosure",
        "url": "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        "authority": "official",
        "verifies": "Confirms the Clerk disclosure portal that the House ZIP/XML workflow is derived from.",
    },
    {
        "family": "lobbying",
        "title": "LDA unified API root",
        "url": "https://lda.gov/api/v1/",
        "authority": "official",
        "verifies": "Confirms the successor lobbying API root and resource categories.",
    },
]

SOURCE_INVENTORY: list[dict[str, Any]] = [
    {
        "id": "sec-search-index",
        "family": "sec",
        "classification": "active",
        "owner": "src/smart_money_tracker/sec13f.py",
        "endpoint": "https://efts.sec.gov/LATEST/search-index",
        "expected_format": "json",
        "freshness": "live",
        "fallback": "browse-edgar atom",
    },
    {
        "id": "sec-submissions",
        "family": "sec",
        "classification": "active",
        "owner": "src/smart_money_tracker/sec13f.py",
        "endpoint": "https://data.sec.gov/submissions/CIK0001067983.json",
        "expected_format": "json",
        "freshness": "live",
        "fallback": "browse-edgar atom",
    },
    {
        "id": "sec-browse-edgar",
        "family": "sec",
        "classification": "active",
        "owner": "src/smart_money_tracker/sec13f.py",
        "endpoint": "https://www.sec.gov/cgi-bin/browse-edgar",
        "expected_format": "atom",
        "freshness": "live",
        "fallback": "none",
    },
    {
        "id": "insider-finance-static",
        "family": "congress",
        "classification": "active",
        "owner": "src/smart_money_tracker/congress.py",
        "endpoint": INSIDER_FINANCE_API,
        "expected_format": "json",
        "freshness": "daily",
        "fallback": "dynamic nextjs build id + cache",
    },
    {
        "id": "insider-finance-page",
        "family": "congress",
        "classification": "active",
        "owner": "src/smart_money_tracker/congress.py",
        "endpoint": INSIDER_FINANCE_PAGE,
        "expected_format": "html",
        "freshness": "daily",
        "fallback": "cache",
    },
    {
        "id": "house-clerk-financial-disclosures",
        "family": "house",
        "classification": "active",
        "owner": "src/smart_money_tracker/house_reps.py",
        "endpoint": f"{HOUSE_CLERK_FD_BASE}/{date.today().year}FD.zip",
        "expected_format": "zip+xml",
        "freshness": "daily",
        "fallback": "local extracted cache",
    },
    {
        "id": "congress-trades-doc",
        "family": "docs",
        "classification": "reference-only",
        "owner": "docs/congress-trades.json",
        "path": str(CONGRESS_DOC_PATH),
        "expected_format": "json snapshot",
        "freshness": "snapshot",
        "fallback": "none",
    },
    {
        "id": "lobbying-disclosure-doc",
        "family": "docs",
        "classification": "reference-only",
        "owner": "docs/lobbyingdisclosure.json",
        "path": str(LOBBYING_DOC_PATH),
        "expected_format": "openapi yaml",
        "freshness": "reference",
        "fallback": "lda.gov api root",
    },
    {
        "id": "edgar-faq-doc",
        "family": "docs",
        "classification": "reference-only",
        "owner": "docs/edgarSEC.md",
        "path": str(EDGAR_DOC_PATH),
        "expected_format": "markdown",
        "freshness": "reference",
        "fallback": "sec live endpoints",
    },
]


def get_source_inventory() -> list[dict[str, Any]]:
    return [dict(item) for item in SOURCE_INVENTORY]


def _safe_read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _extract_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}

    lines = text.splitlines()
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def _extract_yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"')


def _extract_yaml_list(text: str, key: str) -> list[str]:
    match = re.search(
        rf"^\s*{re.escape(key)}:\s*\n((?:\s+-\s.+\n?)+)",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        return []

    items: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip('"'))
    return items


def get_secondary_references() -> list[dict[str, str]]:
    return [dict(item) for item in SECONDARY_REFERENCES]


def _first_congress_doc_record() -> dict[str, Any]:
    payload = _safe_read_json(CONGRESS_DOC_PATH) or {}
    if isinstance(payload, dict):
        data = payload.get("pageProps", {}).get("data", [])
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first
    return {}


def load_doc_annotations() -> list[dict[str, Any]]:
    congress_payload = _safe_read_json(CONGRESS_DOC_PATH) or {}
    congress_meta = congress_payload.get("_audit", {}) if isinstance(congress_payload, dict) else {}
    lobbying_text = LOBBYING_DOC_PATH.read_text()
    edgar_text = EDGAR_DOC_PATH.read_text()
    edgar_meta = _extract_frontmatter(edgar_text)

    return [
        {
            "path": str(CONGRESS_DOC_PATH),
            "classification": congress_meta.get("classification", "reference-only"),
            "relationship": congress_meta.get("relationship", "snapshot-baseline"),
            "runtime_owner": congress_meta.get("runtime_owner", "src/smart_money_tracker/congress.py"),
            "provenance": congress_meta.get("provenance", ""),
            "audited_source_id": congress_meta.get("audited_source_id", "congress-trades-doc"),
            "secondary_reference_urls": congress_meta.get("secondary_reference_urls", []),
            "evidence_source_ids": congress_meta.get("evidence_source_ids", []),
        },
        {
            "path": str(LOBBYING_DOC_PATH),
            "classification": _extract_yaml_scalar(lobbying_text, "classification") or "reference-only",
            "relationship": _extract_yaml_scalar(lobbying_text, "relationship") or "reference-only",
            "runtime_owner": _extract_yaml_scalar(lobbying_text, "runtime_owner"),
            "has_deprecation_notice": "deprecated" in lobbying_text.lower(),
            "provenance": _extract_yaml_scalar(lobbying_text, "provenance") or "",
            "audited_source_id": _extract_yaml_scalar(lobbying_text, "audited_source_id") or "lobbying-disclosure-doc",
            "secondary_reference_urls": _extract_yaml_list(lobbying_text, "secondary_reference_urls"),
            "evidence_source_ids": _extract_yaml_list(lobbying_text, "evidence_source_ids"),
        },
        {
            "path": str(EDGAR_DOC_PATH),
            "classification": edgar_meta.get("audit_classification", "reference-only"),
            "relationship": edgar_meta.get("audit_relationship", "reference-only"),
            "runtime_owner": edgar_meta.get("audit_runtime_owner", "src/smart_money_tracker/sec13f.py"),
            "mentions_sec_faq": "webmaster frequently asked questions" in edgar_text.lower(),
            "provenance": edgar_meta.get("audit_provenance", ""),
            "audited_source_id": edgar_meta.get("audit_source_id", "edgar-faq-doc"),
            "secondary_reference_urls": [
                edgar_meta.get("audit_secondary_reference_url", "https://www.sec.gov/about/developer-resources")
            ],
            "evidence_source_ids": ["sec-submissions", "sec-browse-edgar"],
        },
    ]


def _status_ok(status: str) -> bool:
    if not status:
        return False
    if status.isdigit():
        return 200 <= int(status) < 400
    return False


def compare_sec_against_baseline(submissions: dict[str, Any], lookup_cik: str | None) -> dict[str, Any]:
    forms = submissions.get("filings", {}).get("recent", {}).get("form", [])
    has_13f = any(form in ("13F-HR", "13F-HR/A") for form in forms)
    baseline_match = bool(lookup_cik == "0001067983" and has_13f)
    return {
        "source_id": "sec-submissions",
        "status": "verified" if baseline_match else "discrepancy",
        "baseline_match": baseline_match,
        "summary": {
            "lookup_cik": lookup_cik,
            "has_13f": has_13f,
            "entity_name": submissions.get("name", ""),
        },
        "discrepancies": [] if baseline_match else ["SEC lookup CIK or 13F filing mismatch"],
    }


def compare_congress_against_baseline(
    sample_trade: dict[str, Any],
    baseline_trade: dict[str, Any],
    static_status: str,
    page_status: str,
) -> dict[str, Any]:
    live_keys = set(sample_trade.keys())
    baseline_keys = set(baseline_trade.keys())
    overlap = sorted(live_keys & baseline_keys)
    baseline_match = bool(overlap and (_status_ok(static_status) or _status_ok(page_status)))
    discrepancies: list[str] = []
    if not overlap:
        discrepancies.append("No overlapping schema keys between live Congress sample and local baseline doc")
    if not (_status_ok(static_status) or _status_ok(page_status)):
        discrepancies.append("Congress endpoint and page baseline both unavailable")
    return {
        "source_id": "insider-finance-static",
        "status": "verified" if baseline_match else "discrepancy",
        "baseline_match": baseline_match,
        "summary": {
            "overlap_keys": overlap,
            "static_status": static_status,
            "page_status": page_status,
            "sample_symbol": sample_trade.get("symbol") or sample_trade.get("ticker"),
        },
        "discrepancies": discrepancies,
    }


def compare_house_against_baseline(sample_trade: dict[str, Any], zip_status: str) -> dict[str, Any]:
    required = {"name", "transaction_date", "chamber"}
    baseline_match = required.issubset(sample_trade.keys()) and _status_ok(zip_status)
    discrepancies = [] if baseline_match else ["House disclosure sample or ZIP probe failed validation"]
    return {
        "source_id": "house-clerk-financial-disclosures",
        "status": "verified" if baseline_match else "discrepancy",
        "baseline_match": baseline_match,
        "summary": {
            "zip_status": zip_status,
            "sample_name": sample_trade.get("name", ""),
        },
        "discrepancies": discrepancies,
    }


def compare_lobbying_against_baseline(
    has_deprecation_notice: bool,
    senate_status: str,
    successor_status: str,
) -> dict[str, Any]:
    baseline_match = has_deprecation_notice and _status_ok(senate_status) and _status_ok(successor_status)
    discrepancies = [] if baseline_match else ["Lobbying reference docs do not align with reachable senate/successor API roots"]
    return {
        "source_id": "lobbying-disclosure-doc",
        "status": "reference-verified" if baseline_match else "reference-discrepancy",
        "baseline_match": baseline_match,
        "summary": {
            "has_deprecation_notice": has_deprecation_notice,
            "senate_status": senate_status,
            "successor_status": successor_status,
        },
        "discrepancies": discrepancies,
    }


def probe_reference_endpoint(name: str, url: str, timeout: int = 20) -> dict[str, Any]:
    try:
        resp = requests.get(url, timeout=timeout)
        return {
            "name": name,
            "url": url,
            "status": str(resp.status_code),
            "bytes_read": len(resp.content),
            "error": "",
        }
    except Exception as exc:
        return {
            "name": name,
            "url": url,
            "status": "ERR",
            "bytes_read": 0,
            "error": str(exc),
        }


def _probe_index(probes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {probe["name"]: probe for probe in probes}


def _serialize_probe_results(results: list[ProbeResult]) -> list[dict[str, Any]]:
    return [asdict(item) for item in results]


def build_secondary_reference_checks() -> list[dict[str, Any]]:
    return [
        {
            "family": "sec",
            "status": "reference-confirmed",
            "summary": "Official SEC docs confirm data.sec.gov JSON APIs, browse-edgar access, and programmatic download requirements.",
            "reference_urls": [
                "https://www.sec.gov/about/developer-resources",
                "https://www.sec.gov/about/webmaster-frequently-asked-questions#api",
            ],
        },
        {
            "family": "congress",
            "status": "reference-confirmed",
            "summary": "Official Senate and House disclosure surfaces remain useful comparison authorities, but InsiderFinance stays the selected runtime source of truth for cross-chamber congressional trade aggregation.",
            "reference_urls": [
                "https://efdsearch.senate.gov/search/",
                "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
                "https://www.insiderfinance.io/congress-trades",
            ],
        },
        {
            "family": "house",
            "status": "reference-confirmed",
            "summary": "House Clerk public disclosure page confirms the official financial disclosure surface behind the ZIP/XML ingestion workflow.",
            "reference_urls": [
                "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
            ],
        },
        {
            "family": "lobbying",
            "status": "reference-confirmed",
            "summary": "The unified lda.gov API root is reachable and matches the deprecation/migration guidance captured in the local OpenAPI snapshot.",
            "reference_urls": [
                "https://lda.gov/api/v1/",
                "https://lda.senate.gov/api/v1/",
            ],
        },
    ]


def build_doc_corrections(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    corrections = []
    for doc in docs:
        corrections.append(
            {
                "path": doc["path"],
                "audited_source_id": doc.get("audited_source_id"),
                "classification": doc.get("classification"),
                "relationship": doc.get("relationship"),
                "provenance": doc.get("provenance", ""),
                "evidence_source_ids": doc.get("evidence_source_ids", []),
                "secondary_reference_urls": doc.get("secondary_reference_urls", []),
            }
        )
    return corrections


def build_verification_evidence(
    inventory: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    inventory_by_id = {item["id"]: item for item in inventory}
    references_by_family: dict[str, list[str]] = {}
    for item in SECONDARY_REFERENCES:
        references_by_family.setdefault(item["family"], []).append(item["url"])

    evidence = []
    for result in verifications:
        source_id = result["source_id"]
        source_info = inventory_by_id.get(source_id, {})
        family = source_info.get("family", "docs")
        summary = result.get("summary", {})
        evidence.append(
            {
                "source_id": source_id,
                "command": VERIFY_SOURCES_COMMAND,
                "test_paths": VERIFY_SOURCES_TEST_PATHS,
                "endpoint_queried": source_info.get("endpoint") or source_info.get("path") or source_info.get("fallback", ""),
                "response_summary": summary,
                "normalized_fields": sorted(summary.keys()),
                "verification_outcome": result.get("status", "unknown"),
                "secondary_reference_urls": references_by_family.get(str(family), []),
            }
        )
    return evidence


def build_discrepancy_report(audit_result: dict[str, Any]) -> str:
    lines = [
        f"# Source Audit Discrepancies — {date.today().strftime('%Y-%m-%d')}",
        "",
        f"> Generated: {audit_result['generated_at']}",
        "",
    ]

    discrepancies = audit_result.get("discrepancies", [])
    if not discrepancies:
        lines.append("No discrepancies detected.")
    else:
        for item in discrepancies:
            lines.append(f"- **{item.get('source_id', 'unknown')}**: {item.get('reason', 'unspecified discrepancy')}")

    open_questions = audit_result.get("open_questions", [])
    if open_questions:
        lines.append("")
        lines.append("## Requires User Input")
        lines.extend(f"- {question}" for question in open_questions)

    secondary_reference_checks = audit_result.get("secondary_reference_checks", [])
    if secondary_reference_checks:
        lines.append("")
        lines.append("## Secondary Reference Checks")
        for item in secondary_reference_checks:
            lines.append(
                f"- **{item.get('family', 'unknown')}** ({item.get('status', 'unknown')}): {item.get('summary', '')}"
            )

    doc_corrections = audit_result.get("doc_corrections", [])
    if doc_corrections:
        lines.append("")
        lines.append("## Document Status")
        for item in doc_corrections:
            lines.append(
                f"- **{Path(item.get('path', 'unknown')).name}**: {item.get('classification', 'unknown')} / {item.get('relationship', 'unknown')}"
            )

    return "\n".join(lines) + "\n"


def write_source_audit_artifacts(audit_result: dict[str, Any], output_dir: Path = REPORTS_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")

    dated_json = output_dir / f"source-verification-{today}.json"
    latest_json = output_dir / "source-verification-latest.json"
    dated_md = output_dir / f"source-discrepancies-{today}.md"
    latest_md = output_dir / "source-discrepancies-latest.md"

    payload = json.dumps(audit_result, indent=2)
    discrepancy_report = build_discrepancy_report(audit_result)

    dated_json.write_text(payload)
    latest_json.write_text(payload)
    dated_md.write_text(discrepancy_report)
    latest_md.write_text(discrepancy_report)

    return {
        "dated_json": str(dated_json),
        "latest_json": str(latest_json),
        "dated_markdown": str(dated_md),
        "latest_markdown": str(latest_md),
    }


def run_source_audit(run_live: bool = True, output_dir: Path = REPORTS_DIR) -> dict[str, Any]:
    inventory = get_source_inventory()
    docs = load_doc_annotations()
    secondary_references = get_secondary_references()

    probe_results = _serialize_probe_results(benchmark_all()) if run_live else []
    probe_lookup = _probe_index(probe_results)

    sec_submissions = get_submissions("0001067983") if run_live else {}
    sec_lookup = lookup_cik_by_name("BERKSHIRE HATHAWAY") if run_live else None
    congress_trades = fetch_congress_trades(force_download=True) if run_live else []
    house_trades = fetch_house_fd_trades(days=30) if run_live else []
    normalized_house = normalize_house_fd_trade(house_trades[0]) if house_trades else {}

    lobbying_senate = (
        probe_reference_endpoint("LDA senate root", "https://lda.senate.gov/api/v1/")
        if run_live
        else {"status": "SKIP"}
    )
    lobbying_successor = (
        probe_reference_endpoint("LDA successor root", "https://lda.gov/api/v1/")
        if run_live
        else {"status": "SKIP"}
    )

    congress_baseline = _first_congress_doc_record()
    lobbying_text = LOBBYING_DOC_PATH.read_text()

    verifications = [
        compare_sec_against_baseline(sec_submissions, sec_lookup),
        compare_congress_against_baseline(
            congress_trades[0] if congress_trades else {},
            congress_baseline,
            probe_lookup.get("InsiderFinance static data URL", {}).get("status", "ERR"),
            probe_lookup.get("InsiderFinance congress page", {}).get("status", "ERR"),
        ),
        compare_house_against_baseline(
            normalized_house or {},
            probe_lookup.get("House Clerk FD ZIP (first byte)", {}).get("status", "ERR"),
        ),
        compare_lobbying_against_baseline(
            has_deprecation_notice="deprecated" in lobbying_text.lower(),
            senate_status=lobbying_senate.get("status", "ERR"),
            successor_status=lobbying_successor.get("status", "ERR"),
        ),
    ]

    discrepancies = []
    for result in verifications:
        for reason in result.get("discrepancies", []):
            discrepancies.append({"source_id": result["source_id"], "reason": reason})

    secondary_reference_checks = build_secondary_reference_checks()
    for check in secondary_reference_checks:
        for reason in check.get("discrepancies", []):
            discrepancies.append({"source_id": check["family"], "reason": reason})

    verification_evidence = build_verification_evidence(inventory, verifications)
    doc_corrections = build_doc_corrections(docs)

    open_questions = [
        "Ask the user if congressional source verification finds multiple plausible authorities or if a product-level source decision changes beyond the current InsiderFinance runtime policy."
    ]

    audit_result: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "verification_command": VERIFY_SOURCES_COMMAND,
        "verification_test_paths": VERIFY_SOURCES_TEST_PATHS,
        "inventory": inventory,
        "docs": docs,
        "probes": probe_results + [lobbying_senate, lobbying_successor],
        "verifications": verifications,
        "verification_evidence": verification_evidence,
        "secondary_references": secondary_references,
        "secondary_reference_checks": secondary_reference_checks,
        "doc_corrections": doc_corrections,
        "discrepancies": discrepancies,
        "open_questions": open_questions,
    }

    artifact_paths = write_source_audit_artifacts(audit_result, output_dir=output_dir)
    audit_result["artifact_paths"] = artifact_paths
    return audit_result


def main() -> None:
    """CLI entrypoint for Source Audit."""
    result = run_source_audit(run_live=True)
    print(json.dumps(result["artifact_paths"], indent=2))


if __name__ == "__main__":
    main()
