#!/usr/bin/env python3
"""
API endpoint benchmark utility for Smart Money Tracker.

Measures response time for all external API/data endpoints used by:
- sec13f.py
- congress.py
- house_reps.py
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

import requests

HEADERS = {
    "User-Agent": "SmartMoneyTracker/1.0 (research@example.com)",
    "Accept-Encoding": "gzip, deflate",
}


@dataclass
class ProbeResult:
    name: str
    method: str
    url: str
    status: str
    elapsed_ms: float
    bytes_read: int
    error: str = ""


def _probe_get(
    name: str, url: str, timeout: int = 30, stream: bool = False
) -> ProbeResult:
    start = time.perf_counter()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=stream)
        elapsed_ms = (time.perf_counter() - start) * 1000
        status = str(resp.status_code)
        size = 0
        if stream:
            # Read one chunk to include TTFB-ish behavior without full download cost.
            for chunk in resp.iter_content(chunk_size=8192):
                size += len(chunk)
                break
            resp.close()
        else:
            size = len(resp.content)
        return ProbeResult(name, "GET", url, status, round(elapsed_ms, 1), size)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(name, "GET", url, "ERR", round(elapsed_ms, 1), 0, str(exc))


def _probe_post(
    name: str, url: str, payload: dict[str, Any], timeout: int = 30
) -> ProbeResult:
    start = time.perf_counter()
    try:
        resp = requests.post(
            url,
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name,
            "POST",
            url,
            str(resp.status_code),
            round(elapsed_ms, 1),
            len(resp.content),
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(name, "POST", url, "ERR", round(elapsed_ms, 1), 0, str(exc))


def benchmark_all() -> list[ProbeResult]:
    today = date.today().strftime("%Y-%m-%d")

    results: list[ProbeResult] = []

    # SEC endpoints
    results.append(
        _probe_post(
            "SEC search-index",
            "https://efts.sec.gov/LATEST/search-index",
            {
                "keys": "BERKSHIRE HATHAWAY",
                "category": "custom",
                "forms": ["13F-HR", "13F-HR/A"],
                "startdt": "2000-01-01",
                "enddt": today,
                "from": 0,
                "size": 10,
                "sort": [{"filedAt": {"order": "desc"}}],
            },
            timeout=30,
        )
    )

    results.append(
        _probe_get(
            "SEC submissions (Berkshire)",
            "https://data.sec.gov/submissions/CIK0001067983.json",
            timeout=30,
        )
    )

    results.append(
        _probe_get(
            "SEC browse-edgar atom",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=BERKSHIRE+HATHAWAY&owner=exclude&output=atom&count=20",
            timeout=30,
        )
    )

    # One known filing index and infotable URLs (may rotate over time)
    results.append(
        _probe_get(
            "SEC filing index.json",
            "https://www.sec.gov/Archives/edgar/data/1067983/000119312526054580/index.json",
            timeout=30,
        )
    )
    results.append(
        _probe_get(
            "SEC infotable XML",
            "https://www.sec.gov/Archives/edgar/data/1067983/000119312526054580/50240.xml",
            timeout=30,
        )
    )

    # Congress endpoints
    results.append(
        _probe_get(
            "InsiderFinance static data URL",
            "https://www.insiderfinance.io/_next/data/congress-trades.json",
            timeout=30,
        )
    )
    results.append(
        _probe_get(
            "InsiderFinance congress page",
            "https://www.insiderfinance.io/congress-trades",
            timeout=30,
        )
    )

    # House endpoint
    current_year = date.today().year
    results.append(
        _probe_get(
            "House Clerk FD ZIP (first byte)",
            f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{current_year}FD.zip",
            timeout=60,
            stream=True,
        )
    )

    return results


def print_results(results: list[ProbeResult]) -> None:
    print("\nAPI Benchmark Results")
    print("=" * 110)
    print(f"{'Name':34} {'Method':6} {'Status':6} {'Time(ms)':10} {'Bytes':10} URL")
    print("-" * 110)
    for r in results:
        print(
            f"{r.name[:34]:34} {r.method:6} {r.status:6} {r.elapsed_ms:10.1f} {r.bytes_read:10d} {r.url}"
        )
        if r.error:
            print(f"{'':34} {'':6} {'':6} {'':10} {'':10} ERROR: {r.error}")

    ok = [r for r in results if r.status.isdigit() and 200 <= int(r.status) < 400]
    slow = sorted(ok, key=lambda x: x.elapsed_ms, reverse=True)
    print("\nTop slow successful endpoints:")
    for r in slow[:3]:
        print(f"- {r.name}: {r.elapsed_ms:.1f} ms (status {r.status})")


def main() -> None:
    results = benchmark_all()
    print_results(results)


if __name__ == "__main__":
    main()
