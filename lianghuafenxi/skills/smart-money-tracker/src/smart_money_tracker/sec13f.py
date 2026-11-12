#!/usr/bin/env python3
"""
SEC 13F Whale Tracker Module
Fetches 13F holdings from SEC EDGAR, compares quarter-over-quarter changes.
Can run standalone or be imported as a module by main.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

# Clear proxy env vars that may interfere with direct connections
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

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "sec13f"
REPORTS_DIR = BASE_DIR / "reports"

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_SEARCH_INDEX_URL = "https://efts.sec.gov/LATEST/search-index"

USER_AGENT = "SmartMoneyTracker/1.0 (research@example.com)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}

# Extra pacing between funds; keep small because each HTTP call already rate-limits.
FUND_LOOP_DELAY_SEC = 0.15

# Tracked funds — default small set for quick runs.
# Use WHALE_FUNDS (defined below) for the full 30-whale watchlist.
FUNDS = {
    "0001067983": {"name": "Berkshire Hathaway", "manager": "Warren Buffett"},
    "0001350694": {"name": "Bridgewater Associates", "manager": "Ray Dalio"},
    "0001336528": {
        "name": "Pershing Square Capital Management",
        "manager": "Bill Ackman",
    },
    "0001029160": {"name": "Soros Fund Management", "manager": "George Soros"},
    "0001649339": {"name": "Scion Asset Management", "manager": "Michael Burry"},
}

# Manually verified CIK overrides (name → CIK).  These take precedence over live lookup.
WHALE_CIK_OVERRIDES: dict[str, str] = {
    # first-20 batch (auto-resolved)
    # 0001067983 = CIK for the 13F-filing entity (institutional investment manager)
    "BERKSHIRE HATHAWAY": "0001067983",
    "SITUATIONAL AWARENESS": "0002045724",
    "DUQUESNE FAMILY OFFICE": "0001536411",
    "BLACKROCK": "0002012383",
    "SCION ASSET MANAGEMENT": "0001649339",
    "PERSHING SQUARE CAPITAL MANAGEMENT": "0001336528",
    "NATIONAL PENSION SERVICE": "0001608046",
    "TCI FUND MANAGEMENT LTD": "0001647251",
    "RENAISSANCE TECHNOLOGIES": "0001037389",
    "APPALOOSA": "0001656456",
    "TIGER GLOBAL MANAGEMENT": "0001167483",
    "HIMALAYA CAPITAL MANAGEMENT": "0001709323",
    "ATREIDES MANAGEMENT": "0001777813",
    "COATUE MANAGEMENT": "0001135730",
    "BAKER BROS ADVISORS": "0001263508",
    "CITADEL ADVISORS": "0001423053",
    # manually provided by user (lookup returned null)
    "BRIDGEWATER ASSOCIATES": "0001350694",
    "ALTIMETER CAPITAL MANAGEMENT": "0001541617",
    "THE BAUPOST GROUP": "0001061768",
    "THE VANGUARD GROUP": "0000102909",
    # last-10 batch (auto-resolved)
    "D1 CAPITAL PARTNERS": "0001747057",
    "SOROS FUND MANAGEMENT": "0001029160",
    "WHALE ROCK CAPITAL MANAGEMENT": "0001387322",
    "LONE PINE CAPITAL": "0001061165",
    "MILLENNIUM MANAGEMENT": "0001273087",
    "VIKING GLOBAL INVESTORS": "0001103804",
    "GOLDMAN SACHS GROUP": "0000886982",
    "THIRD POINT": "0001040273",
    "GATES FOUNDATION TRUST": "0001166559",
    "TWO SIGMA INVESTMENTS": "0001179392",
}

# Pre-built FUNDS dict for all 30 whales (CIK → {name, manager})
WHALE_FUNDS: dict[str, dict[str, str]] = {
    cik: {"name": name.title(), "manager": name.title()}
    for name, cik in WHALE_CIK_OVERRIDES.items()
}

# Whale watchlist names provided by user; resolved to CIK via lookup helpers.
WHALE_CANDIDATES = [
    "BERKSHIRE HATHAWAY",
    "SITUATIONAL AWARENESS",
    "DUQUESNE FAMILY OFFICE",
    "BLACKROCK",
    "SCION ASSET MANAGEMENT",
    "PERSHING SQUARE CAPITAL MANAGEMENT",
    "BRIDGEWATER ASSOCIATES",
    "NATIONAL PENSION SERVICE",
    "TCI FUND MANAGEMENT LTD",
    "ALTIMETER CAPITAL MANAGEMENT",
    "RENAISSANCE TECHNOLOGIES",
    "APPALOOSA",
    "TIGER GLOBAL MANAGEMENT",
    "HIMALAYA CAPITAL MANAGEMENT",
    "ATREIDES MANAGEMENT",
    "THE VANGUARD GROUP",
    "COATUE MANAGEMENT",
    "BAKER BROS ADVISORS",
    "THE BAUPOST GROUP",
    "CITADEL ADVISORS",
    "D1 CAPITAL PARTNERS",
    "SOROS FUND MANAGEMENT",
    "WHALE ROCK CAPITAL MANAGEMENT",
    "LONE PINE CAPITAL",
    "MILLENNIUM MANAGEMENT",
    "VIKING GLOBAL INVESTORS",
    "GOLDMAN SACHS GROUP",
    "THIRD POINT",
    "GATES FOUNDATION TRUST",
    "TWO SIGMA INVESTMENTS",
]


def is_valid_cik(cik: str) -> bool:
    """Return True if CIK is 10-digit numeric string."""
    return bool(cik) and len(cik) == 10 and cik.isdigit()


def normalize_entity_name(name: str) -> str:
    """Normalize manager/entity names for stable matching."""
    if not name:
        return ""
    cleaned = " ".join(name.upper().strip().split())
    for suffix in [
        ", INC",
        " INC",
        " LLC",
        " LTD",
        " LP",
        " L P",
        " CO",
        " CORP",
        " GROUP",
    ]:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
    return cleaned


def _extract_cik_from_search_hit(hit: dict) -> str | None:
    """Extract a CIK from SEC search-index hit object across known shapes."""
    if not isinstance(hit, dict):
        return None
    for key in ("cik", "entityCik", "cikNumber", "companyCik"):
        val = hit.get(key)
        if val is None:
            continue
        cik = str(val).zfill(10)
        if is_valid_cik(cik):
            return cik
    return None


def lookup_cik_by_name(entity_name: str) -> str | None:
    """
    Resolve manager/entity name to CIK.

    Strategy:
      1) Try SEC search-index endpoint (if available).
      2) Fallback to SEC browse-edgar atom feed and parse CIK.
    """
    if not entity_name or not entity_name.strip():
        return None

    # 0) Check override map first (no network call needed).
    override_key = entity_name.upper().strip()
    if override_key in WHALE_CIK_OVERRIDES:
        return WHALE_CIK_OVERRIDES[override_key]
    # Also try with normalised name.
    norm_key = normalize_entity_name(entity_name)
    for name, cik in WHALE_CIK_OVERRIDES.items():
        if normalize_entity_name(name) == norm_key:
            return cik

    # 1) Try SEC search-index endpoint first.
    payload = {
        "keys": entity_name,
        "category": "custom",
        "forms": ["13F-HR", "13F-HR/A"],
        "startdt": "2000-01-01",
        "enddt": date.today().strftime("%Y-%m-%d"),
        "from": 0,
        "size": 25,
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    try:
        rate_limit()
        resp = requests.post(
            SEC_SEARCH_INDEX_URL,
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if resp.status_code < 400:
            data = resp.json()
            hits = data.get("hits", {})
            if isinstance(hits, dict):
                hits_list = hits.get("hits", [])
            elif isinstance(hits, list):
                hits_list = hits
            else:
                hits_list = []

            norm_target = normalize_entity_name(entity_name)
            candidates: list[tuple[int, str]] = []
            for hit in hits_list:
                source = hit.get("_source", hit)
                cik = _extract_cik_from_search_hit(source)
                if not cik:
                    continue
                hit_name = normalize_entity_name(
                    source.get("entityName", "")
                    or source.get("displayName", "")
                    or source.get("companyName", "")
                    or ""
                )
                if hit_name == norm_target:
                    score = 0
                elif norm_target and (
                    norm_target in hit_name or hit_name in norm_target
                ):
                    score = 1
                else:
                    score = 2
                candidates.append((score, cik))

            if candidates:
                candidates.sort(key=lambda x: x[0])
                return candidates[0][1]
    except Exception:
        # Continue to browse-edgar fallback.
        pass

    # 2) Fallback: SEC browse-edgar Atom endpoint.
    # Example returns entries with ID like: urn:tag:www.sec.gov:cik=0001081316
    rate_limit()
    try:
        resp = fetch_with_retry(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            headers=HEADERS,
            timeout=30,
            params={
                "action": "getcompany",
                "company": entity_name,
                "owner": "exclude",
                "output": "atom",
                "count": "20",
            },
        )
    except Exception:
        return None

    text = resp.text
    ciks = re.findall(r"cik=(\d{10})", text, flags=re.IGNORECASE)
    if not ciks:
        ciks = re.findall(r"CIK=(\d{10})", text)

    for cik in ciks:
        if is_valid_cik(cik):
            return cik
    return None


def resolve_whale_ciks(whale_names: list[str]) -> dict[str, str | None]:
    """Resolve whale names to CIK map using SEC lookup endpoint."""
    resolved: dict[str, str | None] = {}
    for name in whale_names:
        try:
            resolved[name] = lookup_cik_by_name(name)
        except Exception:
            resolved[name] = None
    return resolved


def build_funds_from_whales(whale_names: list[str]) -> dict[str, dict[str, str]]:
    """
    Build tracker-compatible FUNDS dict from whale names.
    Keeps only names that resolve to valid CIK.
    """
    resolved = resolve_whale_ciks(whale_names)
    funds: dict[str, dict[str, str]] = {}
    for whale_name, cik in resolved.items():
        if not cik or not is_valid_cik(cik):
            continue
        funds[cik] = {
            "name": whale_name.title(),
            "manager": whale_name.title(),
        }
    return funds


def rate_limit():
    """SEC EDGAR rate limit: max 10 req/sec"""
    time.sleep(0.15)


def fetch_with_retry(
    url: str,
    headers: dict,
    max_retries: int = 3,
    timeout: int = 60,
    params: dict | None = None,
) -> requests.Response:
    """GET a URL with exponential-backoff retry on network/HTTP errors."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, params=params)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            # Don't backoff-retry non-rate-limit 4xx errors; they are usually permanent.
            if status is not None and 400 <= status < 500 and status != 429:
                raise
            if attempt == max_retries - 1:
                raise
            wait = 2**attempt
            print(
                f"  [WARN] Fetch failed (attempt {attempt + 1}/{max_retries}, status={status}): {exc}"
            )
            print(f"  Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = 2**attempt
            print(f"  [WARN] Fetch failed (attempt {attempt + 1}/{max_retries}): {exc}")
            print(f"  Retrying in {wait}s...")
            time.sleep(wait)


def get_submissions(cik: str) -> dict:
    """Fetch all submissions for a CIK"""
    url = SUBMISSIONS_URL.format(cik=cik)
    rate_limit()
    resp = fetch_with_retry(url, headers=HEADERS, timeout=30)
    return resp.json()


def find_13f_filings(submissions: dict, limit: int = 2) -> list:
    """
    Find recent 13F-HR filings from submissions.
    Handles both old API structure (list of dicts) and new API structure (dict of parallel lists).
    """
    recent = submissions.get("filings", {}).get("recent", [])
    filings = []

    if isinstance(recent, dict):
        # New SEC API structure: dict of parallel lists
        # recent = {"accessionNumber": [...], "form": [...], "filingDate": [...], ...}
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])
        report_dates = recent.get("reportDate", [])

        for i in range(len(forms)):
            form = forms[i] if i < len(forms) else ""
            if form in ("13F-HR", "13F-HR/A"):
                filings.append(
                    {
                        "form": form,
                        "accession": (
                            accession_numbers[i] if i < len(accession_numbers) else ""
                        ),
                        "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                        "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                        "report_date": report_dates[i] if i < len(report_dates) else "",
                    }
                )
                if len(filings) >= limit:
                    break

    elif isinstance(recent, list):
        # Old SEC API structure: list of dicts
        for item in recent:
            if not isinstance(item, dict):
                continue
            form = item.get("form", "")
            if form in ("13F-HR", "13F-HR/A"):
                filings.append(
                    {
                        "form": form,
                        "accession": item.get("accessionNumber", ""),
                        "filing_date": item.get("filingDate", ""),
                        "primary_doc": item.get("primaryDocument", ""),
                        "report_date": item.get("reportDate", ""),
                    }
                )
                if len(filings) >= limit:
                    break

    return filings


def get_filings_by_date_range(cik: str, start_date: str, end_date: str = None) -> list:
    """
    Get 13F filings within a date range.

    Args:
        cik: Fund CIK
        start_date: "YYYY-MM-DD" or "YTD" or "Q1-2026" or "-3Q" (last 3 quarters)
        end_date: "YYYY-MM-DD" or None for today

    Returns:
        List of filing dicts sorted by date (newest first)
    """
    submissions = get_submissions(cik)
    filings = find_13f_filings(submissions, limit=20)

    # Parse start_date
    if start_date == "YTD":
        start = f"{date.today().year}-01-01"
    elif start_date.startswith("Q"):
        # Q1-2026 → 2026-01-01 to 2026-03-31
        quarter, year = start_date[1:].split("-")
        start = f"{year}-{(int(quarter)-1)*3+1:02d}-01"
    elif start_date.startswith("-") and start_date.endswith("Q"):
        # -3Q → go back 3 quarters from current
        n = int(start_date[1:-1])
        current_q = (date.today().month - 1) // 3 + 1
        target_q = current_q - n
        target_year = date.today().year
        while target_q <= 0:
            target_q += 4
            target_year -= 1
        start = f"{target_year}-{(target_q-1)*3+1:02d}-01"
    else:
        start = start_date

    end = end_date or date.today().strftime("%Y-%m-%d")

    # Filter by date range
    filtered = [f for f in filings if start <= f["report_date"] <= end]
    return filtered


def find_infotable_url(cik: str, accession: str) -> str | None:
    """Find infotable XML URL via filing index.json"""
    cik_int = str(int(cik))
    acc_clean = accession.replace("-", "")
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/"

    index_url = base_url + "index.json"
    rate_limit()
    resp = fetch_with_retry(index_url, headers=HEADERS, timeout=30)
    data = resp.json()

    items = data.get("directory", {}).get("item", [])
    xml_files = [item["name"] for item in items if item["name"].endswith(".xml")]

    for name in xml_files:
        lower = name.lower()
        if "infotable" in lower or "information" in lower:
            return base_url + name

    for name in xml_files:
        lower = name.lower()
        if "primary" not in lower and "cover" not in lower and "index" not in lower:
            return base_url + name

    return None


def parse_13f_xml(xml_text: str) -> list:
    """Parse 13F information table XML. Returns [] on malformed input."""
    holdings = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        idx = xml_text.find("<?xml")
        if idx > 0:
            xml_text = xml_text[idx:]
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            print(
                f"  [WARN] Malformed XML, skipping: {exc} | snippet: {xml_text[:200]!r}"
            )
            return []
    except Exception as exc:
        print(f"  [WARN] XML parse error: {exc}")
        return []

    for entry in root.iter():
        if entry.tag.endswith("infoTable"):
            holding = {}
            for child in entry:
                local_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                if local_tag == "nameOfIssuer":
                    holding["name"] = child.text.strip() if child.text else ""
                elif local_tag == "titleOfClass":
                    holding["class"] = child.text.strip() if child.text else ""
                elif local_tag == "cusip":
                    holding["cusip"] = child.text.strip() if child.text else ""
                elif local_tag == "value":
                    holding["value"] = int(child.text.strip()) if child.text else 0
                elif local_tag == "sshPrnamt":
                    holding["shares"] = int(child.text.strip()) if child.text else 0
                elif local_tag == "sshPrnamtType":
                    holding["share_type"] = child.text.strip() if child.text else "SH"
                elif local_tag == "putCall":
                    holding["put_call"] = child.text.strip() if child.text else ""
                elif local_tag == "investmentDiscretion":
                    holding["discretion"] = child.text.strip() if child.text else ""
                elif local_tag == "shrsOrPrnAmt":
                    for sub in child:
                        sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                        if sub_tag == "sshPrnamt":
                            holding["shares"] = int(sub.text.strip()) if sub.text else 0
                        elif sub_tag == "sshPrnamtType":
                            holding["share_type"] = (
                                sub.text.strip() if sub.text else "SH"
                            )

            if holding.get("name"):
                holdings.append(holding)

    return holdings


def fetch_13f_holdings(cik: str, filing: dict) -> list:
    """Fetch and parse a 13F filing's holdings. Returns [] on HTTP or parse errors."""
    infotable_url = find_infotable_url(cik, filing["accession"])
    if not infotable_url:
        print(f"  [WARN] Could not find infotable XML for {filing['accession']}")
        return []

    print(f"  Fetching infotable: {infotable_url}")
    rate_limit()
    try:
        resp = fetch_with_retry(infotable_url, headers=HEADERS, timeout=60)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            print(
                "  [WARN] Rate-limited (429) fetching infotable; returning empty holdings"
            )
        else:
            print(f"  [WARN] HTTP error fetching infotable: {exc}")
        return []
    except Exception as exc:
        print(f"  [WARN] Failed to fetch infotable after retries: {exc}")
        return []

    holdings = parse_13f_xml(resp.text)
    print(f"  Parsed {len(holdings)} holdings")
    return holdings


def holdings_to_dict(holdings: list) -> dict:
    """Convert holdings list to CUSIP-keyed dict, merging same-CUSIP entries"""
    result = {}
    for h in holdings:
        cusip = h.get("cusip", "")
        key = cusip
        if h.get("put_call"):
            key = f"{cusip}_{h['put_call']}"

        if key in result:
            result[key]["value"] += h.get("value", 0)
            result[key]["shares"] += h.get("shares", 0)
        else:
            result[key] = {
                "name": h.get("name", ""),
                "cusip": cusip,
                "class": h.get("class", ""),
                "value": h.get("value", 0),
                "shares": h.get("shares", 0),
                "share_type": h.get("share_type", "SH"),
                "put_call": h.get("put_call", ""),
            }
    return result


def compare_holdings(current: dict, previous: dict) -> dict:
    """Compare two quarters of holdings, return changes"""
    changes = {
        "new": [],
        "increased": [],
        "decreased": [],
        "closed": [],
        "unchanged": [],
    }

    all_keys = set(list(current.keys()) + list(previous.keys()))

    for key in all_keys:
        curr = current.get(key)
        prev = previous.get(key)

        if curr and not prev:
            changes["new"].append(
                {**curr, "change_pct": None, "share_change": curr["shares"]}
            )
        elif prev and not curr:
            changes["closed"].append(
                {**prev, "change_pct": -100, "share_change": -prev["shares"]}
            )
        elif curr and prev:
            if curr["shares"] == prev["shares"]:
                changes["unchanged"].append(curr)
            else:
                pct = (
                    ((curr["shares"] - prev["shares"]) / prev["shares"] * 100)
                    if prev["shares"] > 0
                    else 0
                )
                entry = {
                    **curr,
                    "prev_shares": prev["shares"],
                    "prev_value": prev["value"],
                    "change_pct": round(pct, 1),
                    "share_change": curr["shares"] - prev["shares"],
                }
                if pct > 0:
                    changes["increased"].append(entry)
                else:
                    changes["decreased"].append(entry)

    for cat in changes:
        changes[cat].sort(key=lambda x: x.get("value", 0), reverse=True)

    return changes


def calculate_portfolio_pct(holding: dict, total_value: int) -> float:
    """Calculate what % of the portfolio a holding represents."""
    if total_value <= 0:
        return 0.0
    return (holding.get("value", 0) / total_value) * 100


def rank_by_portfolio_pct(changes: dict, total_value: int) -> dict:
    """Add portfolio_pct to each holding in changes dict."""
    if total_value <= 0:
        return changes
    for action in ("increased", "new", "decreased", "closed"):
        for h in changes.get(action, []):
            h["portfolio_pct"] = round(calculate_portfolio_pct(h, total_value), 2)
    # Sort each list by portfolio_pct descending
    for action in ("increased", "new", "decreased"):
        changes[action] = sorted(
            changes.get(action, []),
            key=lambda x: x.get("portfolio_pct", 0),
            reverse=True,
        )
    return changes


def format_value(val_dollars: int) -> str:
    """Format dollar value"""
    val = val_dollars
    if val >= 1e12:
        return f"${val/1e12:.1f}T"
    elif val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.1f}M"
    else:
        return f"${val:,.0f}"


def format_shares(shares: int) -> str:
    """Format share count"""
    if shares >= 1e6:
        return f"{shares/1e6:.1f}M"
    elif shares >= 1e3:
        return f"{shares/1e3:.1f}K"
    return str(shares)


def report_date_to_quarter(report_date: str) -> str:
    """Convert report date to quarter string"""
    if not report_date:
        return "Unknown"
    try:
        d = datetime.strptime(report_date, "%Y-%m-%d")
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}"
    except ValueError:
        return report_date


def process_fund(cik: str, info: dict) -> dict:
    """Process a single fund: fetch, parse, compare, cache"""
    print(f"\n{'='*60}")
    print(f"Processing: {info['manager']} ({info['name']}) - CIK: {cik}")
    print(f"{'='*60}")

    result = {"cik": cik, "info": info}

    try:
        submissions = get_submissions(cik)
        filings = find_13f_filings(submissions, limit=2)
        if not filings:
            result["error"] = "No 13F filings found"
            return result

        print(f"  Found {len(filings)} recent 13F filings:")
        for f in filings:
            print(
                f"    - {f['form']} filed {f['filing_date']} (report date: {f['report_date']})"
            )

        current_filing = filings[0]
        result["current_filing"] = current_filing
        print(f"\n  Fetching current quarter ({current_filing['report_date']})...")
        current_raw = fetch_13f_holdings(cik, current_filing)
        current_holdings = holdings_to_dict(current_raw)
        result["current_holdings"] = current_holdings

        # Save current data
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        save_path = DATA_DIR / f"{cik}_{current_filing['report_date']}.json"
        with open(save_path, "w") as f:
            json.dump(
                {
                    "cik": cik,
                    "info": info,
                    "filing": current_filing,
                    "holdings": current_holdings,
                    "fetched_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )
        print(f"  Saved to {save_path}")

        # Fetch previous quarter for comparison
        if len(filings) >= 2:
            prev_filing = filings[1]
            print(f"\n  Fetching previous quarter ({prev_filing['report_date']})...")

            prev_path = DATA_DIR / f"{cik}_{prev_filing['report_date']}.json"
            if prev_path.exists():
                print(f"  Using cached data from {prev_path}")
                with open(prev_path) as f:
                    prev_data = json.load(f)
                prev_holdings = prev_data["holdings"]
            else:
                prev_raw = fetch_13f_holdings(cik, prev_filing)
                prev_holdings = holdings_to_dict(prev_raw)
                with open(prev_path, "w") as f:
                    json.dump(
                        {
                            "cik": cik,
                            "info": info,
                            "filing": prev_filing,
                            "holdings": prev_holdings,
                            "fetched_at": datetime.now().isoformat(),
                        },
                        f,
                        indent=2,
                    )

            changes = compare_holdings(current_holdings, prev_holdings)

            # Calculate total portfolio value and rank by portfolio %
            total_value = sum(h.get("value", 0) for h in current_holdings.values())
            changes = rank_by_portfolio_pct(changes, total_value)

            result["changes"] = changes
            print(
                f"  New: {len(changes['new'])}, Increased: {len(changes['increased'])}, "
                f"Decreased: {len(changes['decreased'])}, Closed: {len(changes['closed'])}, "
                f"Unchanged: {len(changes['unchanged'])}"
            )
        else:
            result["changes"] = None

    except Exception as e:
        result["error"] = str(e)
        import traceback

        traceback.print_exc()

    return result


def generate_13f_report(all_fund_data: list) -> str:
    """Generate 13F section of markdown report"""
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"## 🐋 13F Whale Activity\n"]
    lines.append(
        f"> Source: SEC EDGAR | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    )

    all_new = defaultdict(list)
    all_increased = defaultdict(list)
    all_closed = defaultdict(list)

    for fund_data in all_fund_data:
        info = fund_data["info"]
        current_filing = fund_data.get("current_filing", {})
        changes = fund_data.get("changes")
        current_holdings = fund_data.get("current_holdings", {})
        error = fund_data.get("error")

        lines.append(
            f"\n### {info['manager']} ({info['name']}) - Manager: {info.get('manager', 'Unknown')}\n"
        )

        if error:
            lines.append(f"⚠️ Fetch failed: {error}\n")
            continue

        quarter = report_date_to_quarter(current_filing.get("report_date", ""))
        filing_date = current_filing.get("filing_date", "Unknown")
        total_value = sum(h.get("value", 0) for h in current_holdings.values())
        num_holdings = len(current_holdings)

        lines.append(f"- **Period**: {quarter}")
        lines.append(f"- **Filed**: {filing_date}")
        lines.append(f"- **Total value**: {format_value(total_value)}")
        lines.append(f"- **Holdings**: {num_holdings}\n")

        if not changes:
            lines.append("_(No prior quarter data for comparison)_\n")
            lines.append(
                f"#### Top Holdings by Portfolio % (Manager: {info.get('manager', 'Unknown')})\n"
            )
            lines.append("| # | Stock | Value | Shares | Portfolio % |")
            lines.append("|---|-------|-------|--------|-------------|")
            sorted_h = sorted(
                current_holdings.values(), key=lambda x: x.get("value", 0), reverse=True
            )
            for i, h in enumerate(sorted_h[:20], 1):
                pc = f" ({h['put_call']})" if h.get("put_call") else ""
                pct = h.get("portfolio_pct", 0)
                lines.append(
                    f"| {i} | {h['name']}{pc} | {format_value(h['value'])} | {format_shares(h['shares'])} | {pct}% |"
                )
            lines.append("")
            continue

        if changes["new"]:
            lines.append(f"#### 🆕 New Positions ({len(changes['new'])})\n")
            lines.append("| Stock | Value | Shares |")
            lines.append("|-------|-------|--------|")
            # Sort by value (big to small)
            sorted_new = sorted(
                changes["new"], key=lambda x: x.get("value", 0), reverse=True
            )
            for h in sorted_new[:15]:
                pc = f" ({h['put_call']})" if h.get("put_call") else ""
                lines.append(
                    f"| {h['name']}{pc} | {format_value(h['value'])} | {format_shares(h['shares'])} |"
                )
                if info["manager"] not in all_new[h["name"]]:
                    all_new[h["name"]].append(info["manager"])
            if len(changes["new"]) > 15:
                lines.append(f"| ... +{len(changes['new'])-15} more | | |")
            lines.append("")

        if changes["increased"]:
            lines.append(f"#### 📈 Increased ({len(changes['increased'])})\n")
            lines.append("| Stock | Value | Change |")
            lines.append("|-------|-------|--------|")
            # Sort by value (big to small)
            sorted_inc = sorted(
                changes["increased"], key=lambda x: x.get("value", 0), reverse=True
            )
            for h in sorted_inc[:15]:
                pc = f" ({h['put_call']})" if h.get("put_call") else ""
                lines.append(
                    f"| {h['name']}{pc} | {format_value(h['value'])} | +{h.get('change_pct', 0)}% |"
                )
                if info["manager"] not in all_increased[h["name"]]:
                    all_increased[h["name"]].append(info["manager"])
            if len(changes["increased"]) > 15:
                lines.append(f"| ... +{len(changes['increased'])-15} more | | |")
            lines.append("")

        if changes["decreased"]:
            lines.append(f"#### 📉 Decreased ({len(changes['decreased'])})\n")
            lines.append("| Stock | Value | Change |")
            lines.append("|-------|-------|--------|")
            # Sort by value (big to small)
            sorted_dec = sorted(
                changes["decreased"], key=lambda x: x.get("value", 0), reverse=True
            )
            for h in sorted_dec[:15]:
                pc = f" ({h['put_call']})" if h.get("put_call") else ""
                lines.append(
                    f"| {h['name']}{pc} | {format_value(h['value'])} | {h.get('change_pct', 0)}% |"
                )
            if len(changes["decreased"]) > 15:
                lines.append(f"| ... +{len(changes['decreased'])-15} more | | |")
            lines.append("")

        if changes["closed"]:
            lines.append(f"#### 🚫 Closed ({len(changes['closed'])})\n")
            lines.append("| Stock | Prior Value | Prior Shares |")
            lines.append("|-------|-------------|--------------|")
            for h in changes["closed"][:15]:
                pc = f" ({h['put_call']})" if h.get("put_call") else ""
                lines.append(
                    f"| {h['name']}{pc} | {format_value(h['value'])} | {format_shares(h['shares'])} |"
                )
                if info["manager"] not in all_closed[h["name"]]:
                    all_closed[h["name"]].append(info["manager"])
            if len(changes["closed"]) > 15:
                lines.append(f"| ... +{len(changes['closed'])-15} more | | |")
            lines.append("")

        lines.append(
            f"**Summary**: New {len(changes['new'])} | Inc {len(changes['increased'])} | Dec {len(changes['decreased'])} | Closed {len(changes['closed'])} | Unch {len(changes['unchanged'])}\n"
        )

    # Cross-fund convergence
    lines.append("\n### 🎯 Cross-Fund Convergence\n")
    multi_new = {k: v for k, v in all_new.items() if len(v) >= 2}
    multi_inc = {k: v for k, v in all_increased.items() if len(v) >= 2}
    multi_closed = {k: v for k, v in all_closed.items() if len(v) >= 2}

    if multi_new or multi_inc:
        lines.append("**Multiple whales bullish on:**\n")
        for name, managers in {**multi_new, **multi_inc}.items():
            action = "new position" if name in multi_new else "increased"
            lines.append(f"- **{name}**: {', '.join(managers)} {action}")
        lines.append("")

    if multi_closed:
        lines.append("**Multiple whales exited:**\n")
        for name, managers in multi_closed.items():
            lines.append(f"- **{name}**: {', '.join(managers)} closed")
        lines.append("")

    if not multi_new and not multi_inc and not multi_closed:
        lines.append("- No strong cross-fund consensus this quarter.\n")

    return "\n".join(lines)


def process_fund_by_name(name: str, manager: str = "") -> dict:
    """
    Agent-friendly entry point: resolve a fund *name* to a CIK, then process.

    Use this when the caller supplies an arbitrary fund name (e.g. from an agent
    prompt) instead of a known CIK.  Checks WHALE_CIK_OVERRIDES first (zero
    network), then falls back to live SEC lookup.

    Returns the same dict shape as `process_fund`, with an ``error`` key set
    if the name cannot be resolved.
    """
    cik = lookup_cik_by_name(name)
    if not cik:
        print(f"  [WARN] Could not resolve CIK for: {name!r}")
        return {
            "error": f"Could not resolve CIK for: {name}",
            "info": {"name": name, "manager": manager or name},
        }
    return process_fund(cik, {"name": name, "manager": manager or name})


def run_13f_tracker(
    funds: dict | None = None,
    use_top_100: bool = False,
    date_range: tuple[str, str] | None = None,
    sort_order: str | None = None,
    result_limit: int | None = None,
) -> dict:
    """
    Main entry point for programmatic use.

    Args:
        funds: Optional dict of {cik: {name, manager}}. If None, uses WHALE_FUNDS.
        use_top_100: If True, resolves top 100 whales from SEC and uses them.
        date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format.
        sort_order: 'dateasc' or 'datedesc' for sorting by report date.
        result_limit: Maximum number of results to return.

    Returns dict: {fund_name: {current_filing, current_holdings, changes, error}}
    """
    if use_top_100:
        funds = get_top_100_whales()
        print(f"\n  Using {len(funds)} top whales")

    funds = funds or WHALE_FUNDS
    all_results = []
    for cik, info in funds.items():
        result = process_fund(cik, info)
        all_results.append(result)
        # Keep a small inter-fund delay; per-request rate limiting is handled in helpers.
        time.sleep(FUND_LOOP_DELAY_SEC)

    # Apply date range filter if provided
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_results = []
        for r in all_results:
            filing_date = r.get("current_filing", {}).get("report_date", "")
            if filing_date and start_date <= filing_date <= end_date:
                filtered_results.append(r)
        all_results = filtered_results

    # Apply sorting
    if sort_order:
        reverse = sort_order.lower() == "datedesc"
        all_results.sort(
            key=lambda r: r.get("current_filing", {}).get("report_date", ""),
            reverse=reverse,
        )

    # Apply limit
    if result_limit and result_limit > 0:
        all_results = all_results[:result_limit]

    report = generate_13f_report(all_results)

    # Add whale conviction stats
    conviction_stats = get_whale_conviction_stats(all_results)
    if conviction_stats["top_conviction"]:
        report += "\n\n## 🐋 Whale Conviction Stats\n"
        report += f"> Based on {conviction_stats['total_whales']} whales\n\n"
        report += "### Top Conviction Stocks (held by most whales)\n"
        for item in conviction_stats["top_conviction"][:10]:
            report += f"- **{item['stock']}**: {item['whale_count']} whales ({item['conviction_pct']}%)"
            if item["whales"]:
                report += f" — {', '.join(item['whales'][:3])}"
            report += "\n"

    # Build structured return for main.py
    structured = {}
    for r in all_results:
        name = r["info"]["name"]
        structured[name] = {
            "manager": r["info"]["manager"],
            "current_filing": r.get("current_filing"),
            "current_holdings": r.get("current_holdings", {}),
            "changes": r.get("changes"),
            "error": r.get("error"),
        }

    return {
        "results": structured,
        "report_section": report,
        "raw": all_results,
        "conviction_stats": conviction_stats,
    }


def get_whale_conviction_stats(all_fund_data: list) -> dict:
    """
    Aggregate whale conviction stats: how many whales hold each stock,
    and the conviction level (percentage of whales holding it).

    Returns:
        {
            "by_stock": {stock_name: {"whales": [manager1, manager2], "count": 2, "total_value": 12345}},
            "top_conviction": [(stock_name, conviction_pct, whales), ...],  # Sorted by conviction
            "total_whales": 30,
        }
    """
    stock_whales = defaultdict(
        lambda: {"whales": [], "total_value": 0, "managers": set()}
    )
    total_whales = len(all_fund_data)

    for fund_data in all_fund_data:
        info = fund_data.get("info", {})
        manager = info.get("manager", "Unknown")
        holdings = fund_data.get("current_holdings", {})

        for cusip, holding in holdings.items():
            name = holding.get("name", "")
            value = holding.get("value", 0)
            if name:
                stock_whales[name]["whales"].append(manager)
                stock_whales[name]["managers"].add(manager)
                stock_whales[name]["total_value"] += value

    # Calculate conviction % and sort
    conviction_list = []
    for stock, data in stock_whales.items():
        conviction_pct = (
            (len(data["managers"]) / total_whales * 100) if total_whales > 0 else 0
        )
        conviction_list.append(
            {
                "stock": stock,
                "conviction_pct": round(conviction_pct, 1),
                "whale_count": len(data["managers"]),
                "whales": sorted(data["managers"]),
                "total_value": data["total_value"],
            }
        )

    # Sort by conviction % descending
    conviction_list.sort(
        key=lambda x: (x["conviction_pct"], x["whale_count"]), reverse=True
    )

    return {
        "by_stock": stock_whales,
        "top_conviction": conviction_list,
        "total_whales": total_whales,
    }


def get_top_100_whales() -> dict[str, dict[str, str]]:
    """
    Resolve the top 100 institutional investment managers from SEC.

    Uses SEC search-index to find large asset managers, then resolves their CIKs.
    Returns WHALE_FUNDS-compatible dict (CIK -> {name, manager}).
    """
    print("\n" + "=" * 60)
    print("  Resolving Top 100 Whales from SEC")
    print("=" * 60)

    # Known large asset managers to seed the search
    seed_names = [
        "BERKSHIRE HATHAWAY",
        "BLACKROCK",
        "VANGUARD",
        "STATE STREET",
        "FIDELITY",
        "CAPITAL GROUP",
        "T. ROWE PRICE",
        "FRANKLIN TEMPLETON",
        "INVESCO",
        "MORGAN STANLEY",
        "GOLDMAN SACHS",
        "JPMORGAN",
        "BANK OF AMERICA",
        "WELLS FARGO",
        "NORTHERN TRUST",
        "BNY MELLON",
        "CRESCENT CAPITAL",
        "OAKTREE",
        "APOLLO",
        "CERBERUS",
        "FORTRESS",
        "CARLYLE",
    ]

    resolved = {}
    for name in seed_names[:100]:  # Limit to 100
        if len(resolved) >= 100:
            break
        cik = lookup_cik_by_name(name)
        if cik and is_valid_cik(cik):
            resolved[cik] = {"name": name.title(), "manager": name.title()}
        time.sleep(0.2)  # Rate limiting

    print(f"  Resolved {len(resolved)} whales")
    return resolved


def main():
    """Standalone entry point"""
    print("=" * 60)
    print("  SEC 13F Whale Tracker")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = run_13f_tracker()

    # Write standalone report
    today = date.today().strftime("%Y-%m-%d")
    report = f"# SEC 13F Whale Tracker — {today}\n\n{data['report_section']}"
    report += f"\n\n---\n_Generated by SEC 13F Tracker | {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"

    report_path = REPORTS_DIR / f"13f-report-{today}.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\n  Report saved to: {report_path}")

    latest_path = REPORTS_DIR / "latest.md"
    with open(latest_path, "w") as f:
        f.write(report)
    print(f"  Also saved as: {latest_path}")

    return report_path


if __name__ == "__main__":
    main()
