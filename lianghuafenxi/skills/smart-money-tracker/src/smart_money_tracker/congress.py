#!/usr/bin/env python3
"""
Congress Trades Module (InsiderFinance.io source)

Fetches Congress trading data from InsiderFinance.io's Next.js data API using a
3-tier fetch strategy:
  1. Plain `requests` GET (fastest; works when Cloudflare is lenient)
  2. `cloudscraper` fallback (solves Cloudflare JS challenge; requires optional dep)
  3. Stale cache fallback (last resort when network is unavailable)

The API returns two trade arrays: `pageProps.data` (basic fields) and
`pageProps.hdata` (richer: district, disclosureDate, capitalGainsOver200USD).
This module prefers `hdata` when available and falls back to `data`.

Install cloudscraper for Cloudflare bypass:
    uv sync --group cloudscraper
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# Clear proxy env vars
for _pv in [
    "ALL_PROXY",
    "all_proxy",
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
]:
    os.environ.pop(_pv, None)

import requests

# Optional cloudscraper for Cloudflare bypass (installed via `uv sync --group cloudscraper`)
try:
    import cloudscraper
except ImportError:
    cloudscraper = None  # type: ignore

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

# Next.js data endpoints require this header (omitting returns 404)
NEXTJS_DATA_HEADERS = {
    **HEADERS,
    "x-nextjs-data": "1",
}

# InsiderFinance API endpoint
INSIDER_FINANCE_API = "https://www.insiderfinance.io/_next/data/congress-trades.json"
INSIDER_FINANCE_PAGE = "https://www.insiderfinance.io/congress-trades"

# Cache file
CACHE_FILE = DATA_DIR / "congress-trades.json"
CACHE_TTL_HOURS = 24


def fetch_with_retry(
    url: str,
    headers: dict,
    max_retries: int = 3,
    timeout: int = 60,
) -> requests.Response:
    """GET a URL with exponential-backoff retry on network/HTTP errors."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            # Retry only rate-limit or server-side failures.
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


def _get_cache_date() -> str | None:
    """Get the date when cache was last modified (YYYY-MM-DD format)."""
    if not CACHE_FILE.exists():
        return None
    mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d")


def _is_cache_from_today() -> bool:
    """Check if cache was modified today."""
    cache_date = _get_cache_date()
    if not cache_date:
        return False
    return cache_date == date.today().strftime("%Y-%m-%d")


def _is_cache_stale() -> bool:
    """Check if cache is stale (not from today or older than TTL)."""
    if not CACHE_FILE.exists():
        return True
    cache_date = _get_cache_date()
    if not cache_date:
        return True
    today = date.today().strftime("%Y-%m-%d")
    # If cache is from today, it's fresh
    if cache_date == today:
        return False
    # If cache is from yesterday or earlier, it's stale
    return True


def _extract_trades_from_response(data) -> list:
    """Extract trades list from API response. Prefers hdata over data."""
    if isinstance(data, dict):
        if "pageProps" in data:
            page_props = data.get("pageProps", {})
            if isinstance(page_props, dict):
                # Prefer richer hdata array (district, disclosureDate)
                hdata = page_props.get("hdata")
                if isinstance(hdata, list) and len(hdata) > 0:
                    return hdata
                # Fall back to basic data array
                if "data" in page_props and isinstance(page_props["data"], list):
                    return page_props["data"]
        # Legacy top-level data key
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
    elif isinstance(data, list):
        return data
    return []


def _is_valid_trade_data(data: dict) -> bool:
    """Validate that cached data contains real trades, not test fixtures."""
    if not isinstance(data, dict):
        return False
    trades = _extract_trades_from_response(data)
    if not trades or len(trades) < 1:
        return False
    # Check if all trades are test data (e.g., name="Test" with no ticker)
    test_indicators = 0
    for trade in trades:
        if not isinstance(trade, dict):
            test_indicators += 1
            continue
        name = trade.get("name", "")
        ticker = trade.get("ticker", "")
        # Single-item test fixture: name="Test" with no ticker
        if name == "Test" and not ticker:
            test_indicators += 1
    # If all trades look like test data, reject
    if test_indicators == len(trades):
        return False
    return True


def _is_cache_valid() -> bool:
    """Check if cache exists, is from today, AND contains valid data."""
    if not _is_cache_from_today():
        return False
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        return _is_valid_trade_data(data)
    except (json.JSONDecodeError, OSError):
        return False


def _extract_build_id_from_html(html: str) -> str | None:
    """Extract Next.js buildId from insiderfinance HTML page."""
    # Pattern 1: direct /_next/data/<build-id>/congress-trades.json reference
    m = re.search(r"/_next/data/([A-Za-z0-9_-]+)/congress-trades\.json", html)
    if m:
        return m.group(1)

    # Pattern 2: /_next/static/<build-id>/_buildManifest.js reference
    m = re.search(r"/_next/static/([A-Za-z0-9_-]{8,})/_buildManifest\.js", html)
    if m:
        return m.group(1)

    # Pattern 3: inline __NEXT_DATA__ JSON with buildId field
    m = re.search(r'"buildId"\s*:\s*"([A-Za-z0-9_-]+)"', html)
    if m:
        return m.group(1)

    return None


def _fetch_with_cloudscraper(api_url: str) -> requests.Response:
    """Fetch via cloudscraper, solving Cloudflare challenge if needed."""
    if cloudscraper is None:
        raise ImportError("cloudscraper not installed")

    scraper = cloudscraper.create_scraper()
    print("  [INFO] Cloudflare detected, using cloudscraper fallback...")

    # Step 1: Fetch HTML page to solve challenge and get cookies
    page_resp = scraper.get(
        INSIDER_FINANCE_PAGE,
        headers={**HEADERS, "Accept": "text/html"},
        timeout=60,
    )
    page_resp.raise_for_status()

    # Step 2: Extract buildId from HTML
    build_id = _extract_build_id_from_html(page_resp.text)
    if not build_id:
        raise Exception("Could not find build-id in page HTML (cloudscraper)")

    print(f"  [INFO] Resolved build-id via cloudscraper: {build_id}")

    # Step 3: Fetch JSON data endpoint using same session (cookies persisted)
    resolved_url = (
        f"https://www.insiderfinance.io/_next/data/{build_id}/congress-trades.json"
    )
    resp = scraper.get(resolved_url, headers=NEXTJS_DATA_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp


def _fetch_live_data() -> dict:
    """
    3-tier fetch: requests -> cloudscraper -> exception.
    Returns raw JSON dict from API.
    """
    # Tier 1: Plain requests
    print("  [INFO] Trying plain requests...")
    try:
        resp = fetch_with_retry(
            INSIDER_FINANCE_API,
            headers=NEXTJS_DATA_HEADERS,
            timeout=60,
        )
        return resp.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status == 404:
            print("  [INFO] Static URL returned 404, resolving dynamic build-id...")
            # Try resolving build-id via plain requests first
            try:
                page_resp = fetch_with_retry(
                    INSIDER_FINANCE_PAGE,
                    headers={**HEADERS, "Accept": "text/html"},
                    timeout=60,
                )
                build_id = _extract_build_id_from_html(page_resp.text)
                if build_id:
                    resolved_url = (
                        f"https://www.insiderfinance.io/_next/data/{build_id}/congress-trades.json"
                    )
                    print(f"  [INFO] Resolved build-id: {build_id}")
                    resp = fetch_with_retry(
                        resolved_url,
                        headers=NEXTJS_DATA_HEADERS,
                        timeout=60,
                    )
                    return resp.json()
            except Exception:
                pass  # Fall through to cloudscraper
        # Any 4xx other than 404, or if build-id resolution failed: try cloudscraper
    except Exception:
        pass  # Fall through to cloudscraper

    # Tier 2: cloudscraper fallback
    print("  [INFO] Plain requests failed, trying cloudscraper...")
    try:
        resp = _fetch_with_cloudscraper(INSIDER_FINANCE_API)
        return resp.json()
    except ImportError:
        print("  [WARN] cloudscraper not installed, skipping Cloudflare bypass")
        raise
    except Exception as exc:
        print(f"  [WARN] cloudscraper failed: {exc}")
        raise


def fetch_congress_trades(force_download: bool = False) -> list:
    """
    Fetch Congress trades from InsiderFinance.
    Returns list of trade dicts.
    - If cache is from today AND valid: use it immediately (no API call)
    - If cache is stale or invalid: try API (requests -> cloudscraper), fallback to cache
    - If no cache: try API
    """
    # If cache is from today and has valid content, use it
    if not force_download and _is_cache_valid():
        cache_date = _get_cache_date()
        print(f"  Using cached data from {cache_date} (today)")
        with open(CACHE_FILE) as f:
            data = json.load(f)
        trades = _extract_trades_from_response(data)
        if trades:
            return trades
        print("  [WARN] Unexpected cached data structure, will try API")

    # Cache is stale or doesn't exist - try live fetch
    print("  Downloading Congress trades from InsiderFinance...")

    try:
        data = _fetch_live_data()
    except Exception as exc:
        print(f"  [WARN] Live fetch failed: {exc}")
        if CACHE_FILE.exists():
            print("  [INFO] Using stale cache")
            try:
                with open(CACHE_FILE) as f:
                    data = json.load(f)
                return _extract_trades_from_response(data)
            except json.JSONDecodeError:
                print(f"  [ERROR] Cache file corrupted, deleting and returning empty")
                try:
                    CACHE_FILE.unlink()
                except OSError:
                    pass
                return []
        print("  [ERROR] No cache available and live fetch failed")
        return []

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Cached to {CACHE_FILE}")
    except Exception as exc:
        print(f"  [WARN] Failed to write cache: {exc}")

    return _extract_trades_from_response(data)


def normalize_trade(raw: dict) -> dict | None:
    """Normalize a trade to unified schema (supports both data and hdata arrays)."""
    name = ""
    if raw.get("firstName") and raw.get("lastName"):
        name = f"{raw['firstName'].strip()} {raw['lastName'].strip()}".strip()
    if not name:
        name = (
            raw.get("name")
            or raw.get("politician")
            or raw.get("representative")
            or raw.get("senator")
            or ""
        ).strip()

    if not name:
        return None

    ticker = (raw.get("symbol") or raw.get("ticker") or "").strip()
    if not ticker or ticker in ("N/A", "--", "-", ""):
        ticker = ""

    party = (raw.get("party") or "").strip()
    trade_type = (raw.get("type") or raw.get("transaction_type") or "").strip()
    trans_date = (
        raw.get("transactionDate")
        or raw.get("transaction_date")
        or raw.get("date")
        or ""
    ).strip()
    amount_range = (raw.get("amount") or raw.get("amount_range") or "").strip()

    # hdata-specific fields
    district = (raw.get("district") or "").strip()
    disclosure_date = (raw.get("disclosureDate") or raw.get("disclosure_date") or "").strip()
    capital_gains = bool(raw.get("capitalGainsOver200USD", False))

    # Determine chamber from office field (more reliable than party)
    office = raw.get("office", "").strip()
    if office:
        if "senator" in office.lower() or "senate" in office.lower():
            chamber = "senate"
        elif "rep" in office.lower() or "house" in office.lower():
            chamber = "house"
        else:
            party_lower = party.lower()
            if "sen" in party_lower or "senate" in party_lower:
                chamber = "senate"
            elif (
                "rep" in party_lower
                or "house" in party_lower
                or "representative" in party_lower
            ):
                chamber = "house"
            else:
                chamber = "senate"
    else:
        party_lower = party.lower()
        if "sen" in party_lower or "senate" in party_lower:
            chamber = "senate"
        elif (
            "rep" in party_lower
            or "house" in party_lower
            or "representative" in party_lower
        ):
            chamber = "house"
        else:
            chamber = "senate"

    return {
        "ticker": ticker,
        "name": name,
        "chamber": chamber,
        "party": party,
        "state": "",
        "district": district,
        "type": trade_type,
        "amount_range": amount_range,
        "transaction_date": trans_date,
        "disclosure_date": disclosure_date,
        "capital_gains_over_200": capital_gains,
        "asset_description": raw.get("assetDescription")
        or raw.get("asset_description")
        or "",
    }


def _parse_amount_range(amount_range: str) -> int:
    """
    Parse amount range string to approximate dollar value (use midpoint).
    Examples: "$1,001 - $15,000" -> 8000, "$15,001 - $50,000" -> 32500
    Returns 0 if parsing fails.
    """
    if not amount_range:
        return 0

    # Extract numbers from range
    import re

    numbers = re.findall(r"\$([0-9,]+)", amount_range)
    if not numbers:
        return 0

    try:
        # Convert to integers
        values = []
        for n in numbers:
            n = n.replace(",", "")
            values.append(int(n))

        if len(values) == 1:
            return values[0]
        elif len(values) >= 2:
            # Return midpoint
            return (values[0] + values[-1]) // 2
    except (ValueError, IndexError):
        pass

    return 0


def aggregate_trades(trades: list[dict], days: int = 90) -> dict:
    """
    Aggregate normalized trades within the last N days.
    Returns: {by_ticker, by_member, by_party, total_trades, by_net_volume}
    """
    cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Filter by transaction date
    recent = []
    for t in trades:
        td = t.get("transaction_date", "")
        if td and td >= cutoff:
            recent.append(t)

    by_ticker = defaultdict(
        lambda: {
            "purchases": 0,
            "sales": 0,
            "members": set(),
            "total": 0,
            "purchase_volume": 0,
            "sales_volume": 0,
            "dollar_volume": 0,
        }
    )
    by_member = defaultdict(
        lambda: {
            "purchases": 0,
            "sales": 0,
            "tickers": set(),
            "total": 0,
            "party": "",
            "chamber": "",
            "purchase_volume": 0,
            "sales_volume": 0,
            "dollar_volume": 0,
        }
    )
    by_party = defaultdict(
        lambda: {
            "purchases": 0,
            "sales": 0,
            "total": 0,
            "purchase_volume": 0,
            "sales_volume": 0,
            "dollar_volume": 0,
        }
    )
    by_net_volume = defaultdict(
        lambda: {
            "purchases": 0,
            "sales": 0,
            "total": 0,
            "purchase_volume": 0,
            "sales_volume": 0,
            "net_volume": 0,  # purchase_volume - sales_volume
            "net_direction": "",  # "BULLISH", "BEARISH", "NEUTRAL"
            "members": set(),
            "trades": [],  # All trades for this ticker
        }
    )

    for t in recent:
        ticker = t["ticker"] or "UNKNOWN"
        member = t["name"]
        party = t["party"]
        ttype = t["type"]
        amount = _parse_amount_range(t.get("amount_range", ""))

        is_purchase = "Purchase" in ttype or "Buy" in ttype or "P" == ttype
        is_sale = "Sale" in ttype or "Sell" in ttype or "S" == ttype

        # By ticker
        by_ticker[ticker]["total"] += 1
        by_ticker[ticker]["dollar_volume"] += amount
        if is_purchase:
            by_ticker[ticker]["purchases"] += 1
            by_ticker[ticker]["purchase_volume"] += amount
        elif is_sale:
            by_ticker[ticker]["sales"] += 1
            by_ticker[ticker]["sales_volume"] += amount
        by_ticker[ticker]["members"].add(member)

        # By member
        by_member[member]["total"] += 1
        by_member[member]["dollar_volume"] += amount
        by_member[member]["party"] = party
        by_member[member]["chamber"] = t["chamber"]
        if t.get("district"):
            by_member[member]["district"] = t["district"]
        if is_purchase:
            by_member[member]["purchases"] += 1
            by_member[member]["purchase_volume"] += amount
        elif is_sale:
            by_member[member]["sales"] += 1
            by_member[member]["sales_volume"] += amount
        by_member[member]["tickers"].add(ticker)

        # By party
        by_party[party]["total"] += 1
        by_party[party]["dollar_volume"] += amount
        if is_purchase:
            by_party[party]["purchases"] += 1
            by_party[party]["purchase_volume"] += amount
        elif is_sale:
            by_party[party]["sales"] += 1
            by_party[party]["sales_volume"] += amount

        # By net volume (for sorting by net notional volume)
        by_net_volume[ticker]["total"] += 1
        if is_purchase:
            by_net_volume[ticker]["purchases"] += 1
            by_net_volume[ticker]["purchase_volume"] += amount
        elif is_sale:
            by_net_volume[ticker]["sales"] += 1
            by_net_volume[ticker]["sales_volume"] += amount
        by_net_volume[ticker]["members"].add(member)

        # Calculate net volume and direction
        by_net_volume[ticker]["net_volume"] = (
            by_net_volume[ticker]["purchase_volume"]
            - by_net_volume[ticker]["sales_volume"]
        )
        net_vol = by_net_volume[ticker]["net_volume"]
        if net_vol > 0:
            by_net_volume[ticker]["net_direction"] = "BULLISH"
        elif net_vol < 0:
            by_net_volume[ticker]["net_direction"] = "BEARISH"
        else:
            by_net_volume[ticker]["net_direction"] = "NEUTRAL"

        # Store trade details
        by_net_volume[ticker]["trades"].append(
            {
                "member": member,
                "type": ttype,
                "amount": amount,
                "date": t.get("transaction_date", ""),
                "party": party,
                "is_purchase": is_purchase,
                "is_sale": is_sale,
                "disclosure_date": t.get("disclosure_date", ""),
                "capital_gains_over_200": t.get("capital_gains_over_200", False),
            }
        )

    # Convert sets to sorted lists for JSON serialization
    for ticker_data in by_ticker.values():
        ticker_data["members"] = sorted(ticker_data["members"])
    for member_data in by_member.values():
        member_data["tickers"] = sorted(member_data["tickers"])
    for vol_data in by_net_volume.values():
        vol_data["members"] = sorted(vol_data["members"])
        # Sort trades by amount (largest first)
        vol_data["trades"] = sorted(
            vol_data["trades"], key=lambda x: x["amount"], reverse=True
        )

    # Sort by total trades
    by_ticker_sorted = dict(
        sorted(by_ticker.items(), key=lambda x: x[1]["total"], reverse=True)
    )
    by_member_sorted = dict(
        sorted(by_member.items(), key=lambda x: x[1]["total"], reverse=True)
    )
    by_party_sorted = dict(
        sorted(by_party.items(), key=lambda x: x[1]["total"], reverse=True)
    )
    # Sort by absolute net volume (largest absolute value first)
    by_net_volume_sorted = dict(
        sorted(
            by_net_volume.items(), key=lambda x: abs(x[1]["net_volume"]), reverse=True
        )
    )

    return {
        "by_ticker": by_ticker_sorted,
        "by_member": by_member_sorted,
        "by_party": by_party_sorted,
        "by_net_volume": by_net_volume_sorted,
        "total_trades": len(recent),
        "days": days,
    }


def generate_congress_report(aggregated: dict, output_path: Path) -> str:
    """Generate markdown report from aggregated data. Returns the report text."""
    lines = [
        "# Congress Trading Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Period: Last {aggregated['days']} days",
        f"Total Trades: {aggregated['total_trades']}",
        "",
        "## By Ticker (Trade Count)",
    ]

    for ticker, data in aggregated["by_ticker"].items():
        purchase_volume = data.get("purchase_volume", 0)
        sales_volume = data.get("sales_volume", 0)
        lines.append(f"### {ticker}")
        lines.append(f"- Purchases: {data.get('purchases', 0)} (${purchase_volume:,})")
        lines.append(f"- Sales: {data.get('sales', 0)} (${sales_volume:,})")
        lines.append(f"- Total: {data.get('total', 0)}")
        lines.append(f"- Net Volume: ${purchase_volume - sales_volume:,}")
        lines.append(f"- Dollar Volume: ${data.get('dollar_volume', 0):,}")
        lines.append(f"- Members: {', '.join(data.get('members', []))}")
        lines.append("")

    lines.extend(
        [
            "## By Member (Trade Count)",
        ]
    )

    for member, data in aggregated["by_member"].items():
        purchase_volume = data.get("purchase_volume", 0)
        sales_volume = data.get("sales_volume", 0)
        lines.append(f"### {member}")
        lines.append(f"- Party: {data.get('party', '')}")
        lines.append(f"- Chamber: {data.get('chamber', '')}")
        district = data.get('district', '')
        if district:
            lines.append(f"- District: {district}")
        lines.append(f"- Purchases: {data.get('purchases', 0)} (${purchase_volume:,})")
        lines.append(f"- Sales: {data.get('sales', 0)} (${sales_volume:,})")
        lines.append(f"- Total: {data.get('total', 0)}")
        lines.append(f"- Dollar Volume: ${data.get('dollar_volume', 0):,}")
        lines.append(f"- Tickers: {', '.join(data.get('tickers', []))}")
        lines.append("")

    # Add new section: By Net Volume (Net notional volume, largest first)
    lines.extend(
        [
            "",
            "## 💰 By Net Volume (Net Notional Volume, Largest First)",
            "> Shows net direction (BULLISH/BEARISH) and net volume (purchase volume - sales volume)",
        ]
    )

    for ticker, data in aggregated.get("by_net_volume", {}).items():
        net_vol = data["net_volume"]
        direction = data["net_direction"]
        emoji = (
            "🟢" if direction == "BULLISH" else "🔴" if direction == "BEARISH" else "⚪"
        )

        lines.append(f"### {emoji} {ticker} ({direction})")
        lines.append(f"- Total Trades: {data['total']}")
        lines.append(f"- Purchase Volume: ${data['purchase_volume']:,}")
        lines.append(f"- Sales Volume: ${data['sales_volume']:,}")
        lines.append(f"- **Net Volume: ${abs(net_vol):,}** ({direction})")
        lines.append(f"- Purchases: {data['purchases']}")
        lines.append(f"- Sales: {data['sales']}")
        lines.append(f"- Members: {', '.join(data['members'])}")

        # Show all trades sorted by amount (largest first)
        if data.get("trades"):
            lines.append("- Trades (by size):")
            for trade in data["trades"]:
                trade_type = (
                    "Purchase"
                    if trade["is_purchase"]
                    else "Sale" if trade["is_sale"] else trade["type"]
                )
                direction_marker = (
                    "↑" if trade["is_purchase"] else "↓" if trade["is_sale"] else "→"
                )
                detail = (
                    f"  {direction_marker} {trade['member']} ({trade['party']}): "
                    f"{trade_type} ${trade['amount']:,} on {trade['date']}"
                )
                if trade.get("disclosure_date"):
                    detail += f" (disclosed {trade['disclosure_date']})"
                if trade.get("capital_gains_over_200"):
                    detail += " [CG>200]"
                lines.append(detail)
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(report_text)

    print(f"  Report written to {output_path}")
    return report_text


def rank_congress_trades(aggregated: dict, top_n: int = 10) -> list[dict]:
    """Rank members by total trades"""
    rankings = []
    for member, data in aggregated["by_member"].items():
        rankings.append(
            {
                "member": member,
                "party": data["party"],
                "chamber": data["chamber"],
                "total_trades": data["total"],
                "purchases": data["purchases"],
                "sales": data["sales"],
                "tickers": len(data["tickers"]),
            }
        )

    return sorted(rankings, key=lambda x: x["total_trades"], reverse=True)[:top_n]


def run_congress_tracker(
    days: int = 90,
    member_filter: str | None = None,
    party_filter: str | None = None,
    chamber_filter: str | None = None,
    date_range: tuple[str, str] | None = None,
    sort_order: str | None = None,
    result_limit: int | None = None,
    force_download: bool = False,
) -> dict:
    """
    Main entry point for Congress trading tracker.

    Args:
        days: Number of days to look back
        member_filter: Filter by member name (substring match)
        party_filter: Filter by party (exact match, case-insensitive)
        chamber_filter: Filter by chamber ('house' or 'senate')
        date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
        sort_order: 'dateasc' or 'datedesc' for sorting by transaction date
        result_limit: Maximum number of results to return

    Returns:
        Dict with trades, aggregated data, rankings
    """
    print("  Fetching Congress trades from InsiderFinance...")
    raw_data = fetch_congress_trades(force_download=force_download)

    # Handle different response formats
    if isinstance(raw_data, dict) and "data" in raw_data:
        raw_trades = raw_data["data"]
    elif isinstance(raw_data, list):
        raw_trades = raw_data
    else:
        raw_trades = []

    all_trades = []
    for raw in raw_trades:
        if isinstance(raw, dict):
            norm = normalize_trade(raw)
            if norm:
                all_trades.append(norm)

    # Apply date range filter if provided, otherwise use days filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_trades = [
            t
            for t in all_trades
            if start_date <= t.get("transaction_date", "") <= end_date
        ]
    else:
        cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered_trades = [
            t for t in all_trades if t.get("transaction_date", "") >= cutoff
        ]

    # Apply other filters
    if member_filter:
        member_filter_lower = member_filter.lower()
        filtered_trades = [
            t for t in filtered_trades if member_filter_lower in t["name"].lower()
        ]

    if party_filter:
        party_filter_lower = party_filter.lower()
        filtered_trades = [
            t for t in filtered_trades if t["party"].lower() == party_filter_lower
        ]

    if chamber_filter:
        chamber_filter_lower = chamber_filter.lower()
        filtered_trades = [
            t for t in filtered_trades if t["chamber"].lower() == chamber_filter_lower
        ]

    # Apply sorting
    if sort_order:
        reverse = sort_order.lower() == "datedesc"
        filtered_trades.sort(
            key=lambda t: t.get("transaction_date", ""), reverse=reverse
        )

    # Apply limit
    if result_limit and result_limit > 0:
        filtered_trades = filtered_trades[:result_limit]

    aggregated = aggregate_trades(filtered_trades, days)
    rankings = rank_congress_trades(aggregated)

    # Generate report
    report_path = (
        REPORTS_DIR / f"congress-report-{date.today().strftime('%Y-%m-%d')}.md"
    )
    report_section = generate_congress_report(aggregated, report_path)

    return {
        "trades": filtered_trades,
        "aggregated": aggregated,
        "rankings": rankings,
        "report_path": str(report_path),
        "report_section": report_section,
        "sources_used": {"insider_finance": True},
    }


def main() -> None:
    """CLI entrypoint for Congress Trades Tracker."""
    print("=" * 60)
    print("  Congress Trades Tracker (InsiderFinance.io)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import argparse

    parser = argparse.ArgumentParser(description="Congress Trades Tracker")
    parser.add_argument("--days", type=int, default=90, help="Days to look back")
    parser.add_argument(
        "--member", type=str, default=None, help="Filter by member name"
    )
    parser.add_argument("--party", type=str, default=None, help="Filter by party")
    parser.add_argument("--chamber", type=str, default=None, help="Filter by chamber")
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
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force download from API even if today's cache exists",
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

    data = run_congress_tracker(
        days=args.days,
        member_filter=args.member,
        party_filter=args.party,
        chamber_filter=args.chamber,
        date_range=date_range,
        sort_order=args.sort,
        result_limit=args.limit,
        force_download=args.force_download,
    )

    print(f"\nTotal trades: {len(data['trades'])}")
    print(f"Report: {data['report_path']}")


if __name__ == "__main__":
    main()
