#!/usr/bin/env python3
"""
House Representatives Financial Disclosure Module
Fetches House Representative buy/sell disclosures from House Clerk Financial Disclosures.

Data source:
  1. House Clerk FD ZIP files: https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip
  2. Parse XML to extract transaction data
  3. Cache downloaded files per year (keep previous years, current year re-downloads)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# Clear proxy env vars
for _proxy_var in [
    "ALL_PROXY",
    "all_proxy",
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
]:
    os.environ.pop(_proxy_var, None)

import requests
from requests.exceptions import RequestException
import xml.etree.ElementTree as ET

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "congress"
REPORTS_DIR = BASE_DIR / "reports"

USER_AGENT = "SmartMoneyTracker/1.0 ([EMAIL])"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json",
}

# House Clerk FD base URL
HOUSE_CLERK_FD_BASE = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs"

# Cache TTL for current year (re-download daily), previous years (keep forever)
CURRENT_YEAR_TTL_HOURS = 24


def _cache_path(year: int) -> Path:
    """Get cache directory for a year's FD data"""
    return DATA_DIR / f"house_fd_{year}"


def _download_and_extract_fds(year: int) -> Path | None:
    """
    Download and extract House Clerk FD ZIP for a year.
    Returns path to extracted directory, or None on failure.
    """
    url = f"{HOUSE_CLERK_FD_BASE}/{year}FD.zip"
    cache_dir = _cache_path(year)

    # Check if we already have current year data (with TTL check)
    if cache_dir.exists() and year == date.today().year:
        # Check TTL
        xml_files = list(cache_dir.glob("*.xml"))
        if xml_files:
            newest_file = max(xml_files, key=lambda p: p.stat().st_mtime)
            mtime = datetime.fromtimestamp(newest_file.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=CURRENT_YEAR_TTL_HOURS):
                print(f"  Using cached {year} FD data (within TTL)")
                return cache_dir

    # For previous years, keep forever once downloaded
    if cache_dir.exists() and year < date.today().year:
        print(f"  Using cached {year} FD data (previous year)")
        return cache_dir

    print(f"  Downloading {year} FD ZIP from House Clerk...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        resp.raise_for_status()

        # Ensure parent data directory exists before writing ZIP
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Save ZIP temporarily
        zip_path = DATA_DIR / f"{year}FD.zip"
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  Downloaded {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

        # Extract ZIP
        cache_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(cache_dir)
        print(f"  Extracted to {cache_dir}")

        # Clean up ZIP
        zip_path.unlink()

        return cache_dir

    except RequestException as e:
        print(f"  [WARN] Download failed for {url}: {e}")
        return cache_dir if cache_dir.exists() else None


def _parse_fd_xml(xml_path: Path) -> list[dict]:
    """
    Parse a House Clerk FD XML file.
    Returns list of transaction dicts.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"  [WARN] Failed to parse {xml_path.name}: {e}")
        return []

    transactions = []

    # XML structure: <FinancialDisclosure> → <Member> → transaction data
    for member in root.iter("Member"):
        # Extract member info
        first = member.findtext("First", "").strip()
        last = member.findtext("Last", "").strip()
        prefix = member.findtext("Prefix", "").strip()
        suffix = member.findtext("Suffix", "").strip()

        name_parts = [prefix, first, last, suffix]
        name = " ".join(p for p in name_parts if p).strip()

        state_dst = member.findtext("StateDst", "").strip()
        filing_type = member.findtext("FilingType", "").strip()
        filing_date = member.findtext("FilingDate", "").strip()
        doc_id = member.findtext("DocID", "").strip()

        if name and filing_date:
            transactions.append(
                {
                    "name": name,
                    "state_dst": state_dst,
                    "filing_type": filing_type,
                    "filing_date": filing_date,
                    "doc_id": doc_id,
                }
            )

    return transactions


def fetch_house_fd_trades(days: int = 90) -> list[dict]:
    """
    Fetch House trades from House Clerk Financial Disclosures.
    Downloads current year + previous year if needed.
    Returns list of normalized trade dicts.
    """
    cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    current_year = date.today().year

    all_trades = []

    # Download current year and previous year
    for year in [current_year, current_year - 1]:
        if year < 2020:  # Don't go back too far
            continue

        extracted_dir = _download_and_extract_fds(year)
        if not extracted_dir:
            continue

        print(f"  Scanning {year} FD data in {extracted_dir}...")

        # Find all XML files
        xml_files = list(extracted_dir.glob("*.xml"))
        print(f"  Found {len(xml_files)} XML files")

        for xml_path in xml_files:
            if xml_path.stat().st_size == 0:
                continue
            transactions = _parse_fd_xml(xml_path)
            all_trades.extend(transactions)

    # Filter by date
    recent = [t for t in all_trades if t.get("filing_date", "") >= cutoff]

    print(f"  Total trades (last {days} days): {len(recent)}")
    return recent


def normalize_house_fd_trade(raw: dict) -> dict | None:
    """Normalize a House FD transaction to unified schema"""
    name = raw.get("name", "").strip()
    if not name:
        return None

    # Use transaction_date if available, otherwise fall back to filing_date
    transaction_date = raw.get("transaction_date") or raw.get("filing_date", "")

    return {
        "ticker": "",  # House FD doesn't always include ticker
        "name": name,
        "chamber": "house",
        "party": "",  # Would need lookup
        "state": raw.get("state_dst", "")[:2] if raw.get("state_dst") else "",
        "district": (
            raw.get("state_dst", "")[2:]
            if raw.get("state_dst") and len(raw.get("state_dst", "")) > 2
            else ""
        ),
        "type": raw.get("filing_type", ""),
        "amount_range": "",
        "transaction_date": transaction_date,
        "disclosure_date": raw.get("filing_date", ""),
        "asset_description": "",
    }


def aggregate_house_reps_trades(trades: list[dict], days: int = 90) -> dict:
    """
    Aggregate normalized House Reps trades within the last N days.
    Returns: {by_member, by_state, total_trades}
    """
    from datetime import datetime, timedelta

    cutoff = (datetime.now().date() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Filter by filing date
    recent = []
    for t in trades:
        fd = t.get("transaction_date", "")
        if fd and fd >= cutoff:
            recent.append(t)

    by_member = {}
    by_state = {}

    for t in recent:
        name = t["name"]
        state = t.get("state", "")

        if name not in by_member:
            by_member[name] = {
                "total": 0,
                "state": state,
                "district": t.get("district", ""),
                "filings": [],
            }
        by_member[name]["total"] += 1
        by_member[name]["filings"].append(t.get("filing_type", ""))

        if state:
            by_state[state] = by_state.get(state, 0) + 1

    return {
        "by_member": dict(
            sorted(by_member.items(), key=lambda x: x[1]["total"], reverse=True)
        ),
        "by_state": dict(sorted(by_state.items(), key=lambda x: x[1], reverse=True)),
        "total_trades": len(recent),
        "days": days,
    }


def generate_house_reps_report(aggregated: dict, output_path: Path) -> str:
    """Generate markdown report section from aggregated data"""
    lines = [
        "## 🏠 House Representatives Financial Disclosures\n",
        f"Total filings (last {aggregated.get('days', 90)} days): {aggregated['total_trades']}\n",
        "### By Member\n",
        "| Member | State | District | Filings |",
        "|--------|-------|----------|---------|",
    ]

    for name, data in aggregated.get("by_member", {}).items():
        lines.append(
            f"| {name} | {data['state']} | {data['district']} | {data['total']} |"
        )

    if aggregated.get("by_state"):
        lines.extend(
            [
                "\n### By State\n",
                "| State | Filings |",
                "|-------|---------|",
            ]
        )
        for state, count in aggregated["by_state"].items():
            lines.append(f"| {state} | {count} |")

    report_section = "\n".join(lines)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_section)
    print(f"  Report written to {output_path}")

    return report_section


def run_house_reps_tracker(
    days: int = 90,
    member_filter: str | None = None,
    party_filter: str | None = None,
    date_range: tuple[str, str] | None = None,
    sort_order: str | None = None,
    result_limit: int | None = None,
) -> dict:
    """
    Main entry point for House Reps FD tracking.

    Args:
        days: Number of days to look back
        member_filter: Filter by member name (substring match)
        party_filter: Filter by party (exact match, case-insensitive)
        date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
        sort_order: 'dateasc' or 'datedesc' for sorting by transaction date
        result_limit: Maximum number of results to return

    Returns:
        Dict with trades, aggregated data, report_section, sources_used
    """
    print("  Fetching House Representative Financial Disclosures...")
    trades = fetch_house_fd_trades(days)

    normalized = []
    for t in trades:
        norm = normalize_house_fd_trade(t)
        if norm:
            normalized.append(norm)

    # Apply date range filter if provided, otherwise apply days filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = [
            t
            for t in normalized
            if start_date <= t.get("transaction_date", "") <= end_date
        ]
    else:
        # Only apply days filter if days > 0
        if days and days > 0:
            cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
            filtered = [
                t for t in normalized if t.get("transaction_date", "") >= cutoff
            ]
        else:
            filtered = normalized

    # Apply other filters
    if member_filter:
        member_filter_lower = member_filter.lower()
        filtered = [t for t in filtered if member_filter_lower in t["name"].lower()]

    if party_filter:
        party_filter_lower = party_filter.lower()
        filtered = [
            t for t in filtered if t.get("party", "").lower() == party_filter_lower
        ]

    # Apply sorting
    if sort_order:
        reverse = sort_order.lower() == "datedesc"
        filtered.sort(key=lambda t: t.get("transaction_date", ""), reverse=reverse)

    # Apply limit
    if result_limit and result_limit > 0:
        filtered = filtered[:result_limit]

    aggregated = aggregate_house_reps_trades(filtered, days)

    # Generate report
    report_path = (
        REPORTS_DIR / f"house-reps-{datetime.now().date().strftime('%Y-%m-%d')}.md"
    )
    report_section = generate_house_reps_report(aggregated, report_path)

    return {
        "trades": filtered,
        "aggregated": aggregated,
        "report_section": report_section,
        "sources_used": {"house_clerk_fd": True},
        "report_path": str(report_path),
    }


def main() -> None:
    """CLI entrypoint for House Representatives Financial Disclosure Tracker."""
    print("=" * 60)
    print("  House Representatives Financial Disclosure Tracker")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import argparse

    parser = argparse.ArgumentParser(description="House Reps FD Tracker")
    parser.add_argument("--days", type=int, default=90, help="Days to look back")
    parser.add_argument(
        "--member", type=str, default=None, help="Filter by member name"
    )
    parser.add_argument("--party", type=str, default=None, help="Filter by party")
    parser.add_argument(
        "--date-range",
        type=str,
        default=None,
        help="Date range: YYYY-MM-DD,YYYY-MM-DD (overrides --days)",
    )
    parser.add_argument(
        "--sort",
        type=str,
        default=None,
        choices=["dateasc", "datedesc"],
        help="Sort output by transaction date",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of results returned"
    )

    args = parser.parse_args()

    # Parse date range if provided
    date_range = None
    if args.date_range:
        try:
            start_str, end_str = args.date_range.split(",")
            date_range = (start_str.strip(), end_str.strip())
        except Exception:
            print(f"  [WARN] Invalid date-range format: {args.date_range}")
            print("  Expected format: YYYY-MM-DD,YYYY-MM-DD")

    data = run_house_reps_tracker(
        days=args.days,
        member_filter=args.member,
        party_filter=args.party,
        date_range=date_range,
        sort_order=args.sort,
        result_limit=args.limit,
    )
    print(f"Total trades: {len(data['trades'])}")
    print(f"Report: {data.get('report_path', 'N/A')}")


if __name__ == "__main__":
    main()
