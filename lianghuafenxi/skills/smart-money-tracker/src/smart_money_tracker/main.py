#!/usr/bin/env python3
# pyright: reportMissingModuleSource=false
"""
Smart Money Tracker — Orchestrator
Runs SEC 13F + Congress trackers, computes convergence, writes unified report.
Agent can choose which trackers to run via CLI flags.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict
from typing import Any, Mapping

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"

from smart_money_tracker.sec13f import run_13f_tracker, FUNDS as DEFAULT_FUNDS
from smart_money_tracker.congress import run_congress_tracker
from smart_money_tracker.house_reps import run_house_reps_tracker
from smart_money_tracker.source_audit import run_source_audit


def compute_convergence(
    sec13f_data: Mapping[str, Any], congress_data: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    """
    Cross-reference 13F whale changes with Congress trades.
    Returns dict keyed by ticker with signal classification.
    """
    # Build whale action map: ticker → list of actions
    whale_actions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fund_name, fund_data in sec13f_data.get("results", {}).items():
        changes = fund_data.get("changes")
        if not changes:
            continue
        manager = fund_data.get("manager", fund_name)

        for h in changes.get("new", []):
            name = h.get("name", "")
            whale_actions[name].append(
                {
                    "fund": fund_name,
                    "manager": manager,
                    "action": "new_position",
                    "value": h.get("value", 0),
                    "change_pct": h.get("change_pct", 0),
                }
            )
        for h in changes.get("increased", []):
            name = h.get("name", "")
            whale_actions[name].append(
                {
                    "fund": fund_name,
                    "manager": manager,
                    "action": "increased",
                    "value": h.get("value", 0),
                    "change_pct": h.get("change_pct", 0),
                }
            )
        for h in changes.get("decreased", []):
            name = h.get("name", "")
            whale_actions[name].append(
                {
                    "fund": fund_name,
                    "manager": manager,
                    "action": "decreased",
                    "value": h.get("value", 0),
                    "change_pct": h.get("change_pct", 0),
                }
            )
        for h in changes.get("closed", []):
            name = h.get("name", "")
            whale_actions[name].append(
                {
                    "fund": fund_name,
                    "manager": manager,
                    "action": "closed",
                    "value": h.get("value", 0),
                }
            )

    # Build congress action map: ticker → {purchases, sales, members}
    congress_by_ticker = congress_data.get("aggregation", {}).get("by_ticker", {})

    # Match by stock name (13F uses full names, Congress uses tickers)
    # We need a name→ticker mapping from congress trades
    name_to_ticker: dict[str, str] = {}
    for trade in congress_data.get("trades", []):
        desc = trade.get("asset_description", "").strip()
        ticker = trade.get("ticker", "").strip()
        if desc and ticker:
            name_to_ticker[desc.lower()] = ticker

    # Also try matching by ticker directly (some 13F holdings have ticker-like names)
    convergence: dict[str, dict[str, Any]] = {}

    for stock_name, actions in whale_actions.items():
        # Try to find matching ticker
        matched_ticker = None

        # Direct match on stock name in congress ticker
        for ticker in congress_by_ticker:
            if ticker.lower() == stock_name.lower():
                matched_ticker = ticker
                break

        # Match via asset description
        if not matched_ticker:
            lower_name = stock_name.lower()
            for desc, ticker in name_to_ticker.items():
                if lower_name in desc or desc in lower_name:
                    matched_ticker = ticker
                    break

        # Partial match: stock name contains ticker or vice versa
        if not matched_ticker:
            for ticker in congress_by_ticker:
                if (
                    ticker.lower() in stock_name.lower()
                    or stock_name.lower() in ticker.lower()
                ):
                    matched_ticker = ticker
                    break

        if not matched_ticker:
            continue

        congress_info = congress_by_ticker.get(matched_ticker, {})
        whale_bullish = any(
            a["action"] in ("new_position", "increased") for a in actions
        )
        whale_bearish = any(a["action"] in ("decreased", "closed") for a in actions)

        # Check portfolio % threshold (strong signal if >2% of portfolio)
        whale_portfolio_pct = 0.0
        for a in actions:
            if "change_pct" in a and a["change_pct"]:
                whale_portfolio_pct = max(whale_portfolio_pct, abs(a["change_pct"]))

        congress_bullish = congress_info.get("purchases", 0) > congress_info.get(
            "sales", 0
        )
        congress_bearish = congress_info.get("sales", 0) > congress_info.get(
            "purchases", 0
        )

        if whale_bullish and congress_bullish:
            signal = "STRONG_BUY"
        elif whale_bearish and congress_bearish:
            signal = "STRONG_SELL"
        elif (whale_bullish and congress_bearish) or (
            whale_bearish and congress_bullish
        ):
            signal = "DIVERGE"
        elif whale_bullish or whale_bearish:
            # Stronger signal if portfolio % >2%
            if whale_portfolio_pct > 2.0:
                signal = "WHALE_ONLY_STRONG"
            else:
                signal = "WHALE_ONLY"
        else:
            signal = "CONGRESS_ONLY"

        convergence[matched_ticker] = {
            "stock_name": stock_name,
            "whale_actions": actions,
            "congress_purchases": congress_info.get("purchases", 0),
            "congress_sales": congress_info.get("sales", 0),
            "congress_members": congress_info.get("members", []),
            "signal": signal,
        }

    # Add congress-only tickers (traded by congress but not in 13F changes)
    for ticker, data in congress_by_ticker.items():
        if ticker not in convergence:
            convergence[ticker] = {
                "stock_name": ticker,
                "whale_actions": [],
                "congress_purchases": data.get("purchases", 0),
                "congress_sales": data.get("sales", 0),
                "congress_members": data.get("members", []),
                "signal": "CONGRESS_ONLY",
            }

    # Sort: STRONG_BUY first, then STRONG_SELL, then DIVERGE, then WHALE_ONLY, then CONGRESS_ONLY
    signal_order = {
        "STRONG_BUY": 0,
        "STRONG_SELL": 1,
        "DIVERGE": 2,
        "WHALE_ONLY": 3,
        "CONGRESS_ONLY": 4,
    }
    sorted_convergence = dict(
        sorted(
            convergence.items(),
            key=lambda x: (
                signal_order.get(x[1]["signal"], 99),
                -(x[1]["congress_purchases"] + x[1]["congress_sales"]),
            ),
        )
    )

    return sorted_convergence


def generate_convergence_report(
    convergence: Mapping[str, Mapping[str, Any]],
    congress_data: Mapping[str, Any] | None = None,
) -> str:
    """Generate convergence section of markdown report"""
    lines = ["## 🎯 Convergence Signals\n"]
    lines.append("Whale + Congress overlap on same tickers.\n")

    # Add congress net volume summary if available
    if congress_data and "aggregated" in congress_data:
        agg = congress_data["aggregated"]
        if "by_net_volume" in agg:
            lines.append("### 💰 Congress Trading by Net Volume (Top 10)\n")
            lines.append("> Net Volume = Purchase Volume - Sales Volume\n")
            for ticker, data in list(agg["by_net_volume"].items())[:10]:
                net_vol = data["net_volume"]
                direction = data["net_direction"]
                emoji = (
                    "🟢"
                    if direction == "BULLISH"
                    else "🔴" if direction == "BEARISH" else "⚪"
                )
                lines.append(
                    f"- {emoji} **{ticker}**: ${abs(net_vol):,} ({direction}) "
                    f"[{data['purchases']} buys, {data['sales']} sells]"
                )
            lines.append("")

    # Group by signal
    by_signal = defaultdict(list)
    for ticker, data in convergence.items():
        by_signal[data["signal"]].append((ticker, data))

    signal_emoji = {
        "STRONG_BUY": "🟢",
        "STRONG_SELL": "🔴",
        "DIVERGE": "🟡",
        "WHALE_ONLY": "🐋",
        "CONGRESS_ONLY": "🏛️",
    }

    signal_desc = {
        "STRONG_BUY": "Whales buying + Congress buying",
        "STRONG_SELL": "Whales selling + Congress selling",
        "DIVERGE": "Whales and Congress disagree",
        "WHALE_ONLY": "Whale activity, no Congress trades",
        "CONGRESS_ONLY": "Congress trades, no whale activity",
    }

    for signal in [
        "STRONG_BUY",
        "STRONG_SELL",
        "DIVERGE",
        "WHALE_ONLY",
        "CONGRESS_ONLY",
    ]:
        items = by_signal.get(signal, [])
        if not items:
            continue

        emoji = signal_emoji.get(signal, "")
        lines.append(f"### {emoji} {signal} — {signal_desc[signal]}\n")

        if signal in ("STRONG_BUY", "STRONG_SELL", "DIVERGE"):
            lines.append(
                "| Ticker | Stock | Whale Action | Congress Buys | Congress Sells | Members |"
            )
            lines.append(
                "|--------|-------|-------------|---------------|----------------|---------|"
            )
            for ticker, data in items[:20]:
                whale_str = ", ".join(
                    f"{a['manager']} {a['action']}" for a in data["whale_actions"][:3]
                )
                members_str = ", ".join(data["congress_members"][:3])
                if len(data["congress_members"]) > 3:
                    members_str += f" +{len(data['congress_members'])-3}"
                lines.append(
                    f"| {ticker} | {data['stock_name']} | {whale_str} | "
                    f"{data['congress_purchases']} | {data['congress_sales']} | {members_str} |"
                )
            lines.append("")
        else:
            # Simpler table for single-source signals
            lines.append("| Ticker | Congress Buys | Congress Sells |")
            lines.append("|--------|---------------|----------------|")
            for ticker, data in items[:15]:
                lines.append(
                    f"| {ticker} | {data['congress_purchases']} | {data['congress_sales']} |"
                )
            lines.append("")

    return "\n".join(lines)


def generate_full_report(
    sec13f_section: str,
    congress_section: str,
    house_reps_section: str,
    convergence_section: str,
    conviction_section: str = "",
) -> str:
    """Generate the complete unified report"""
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        f"# Smart Money Tracker — {today}\n",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "---\n",
        sec13f_section,
        "\n---\n",
        conviction_section if conviction_section else "",
        congress_section,
        "\n---\n",
        house_reps_section,
        "\n---\n",
        convergence_section,
        f"\n---\n_Generated by Smart Money Tracker | {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Smart Money Tracker")
    parser.add_argument(
        "--13f-only", action="store_true", help="Run only SEC 13F tracker"
    )
    parser.add_argument(
        "--congress-only", action="store_true", help="Run only Congress tracker"
    )
    parser.add_argument(
        "--days", type=int, default=90, help="Congress lookback days (default: 90)"
    )
    parser.add_argument(
        "--member", type=str, default=None, help="Filter Congress by member name"
    )
    parser.add_argument(
        "--party", type=str, default=None, help="Filter Congress by party"
    )
    parser.add_argument(
        "--chamber",
        type=str,
        default=None,
        choices=["house", "senate"],
        help="Filter Congress by chamber",
    )
    parser.add_argument(
        "--no-house-reps",
        action="store_true",
        help="Skip House Reps tracker",
    )
    parser.add_argument(
        "--fast-13f",
        action="store_true",
        help="Use small default 13F fund set (faster, lower timeout risk)",
    )
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
        "--verify-sources",
        action="store_true",
        help="Run source inventory + live verification audit and write evidence artifacts",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force download from API even if today's cache exists",
    )
    args = parser.parse_args()

    # In constrained agent runtimes, full 30-whale 13F runs can exceed tool timeout.
    # Default 13f-only mode to fast profile unless caller explicitly sets --fast-13f false (not exposed).
    if args.__dict__.get("13f_only") and not args.fast_13f:
        args.fast_13f = True

    print("=" * 60)
    print("  Smart Money Tracker")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Parse date range if provided
    date_range = None
    if args.date_range:
        try:
            start_str, end_str = args.date_range.split(",")
            date_range = (start_str.strip(), end_str.strip())
        except Exception:
            print(f"  [WARN] Invalid date-range format: {args.date_range}")
            print("  Expected format: YYYY-MM-DD,YYYY-MM-DD")

    if args.verify_sources:
        print("\n🔎 Running source verification audit...\n")
        audit_result = run_source_audit(run_live=True, output_dir=REPORTS_DIR)
        artifact_paths = audit_result.get("artifact_paths", {})
        print(f"  Source verification JSON: {artifact_paths.get('latest_json', 'n/a')}")
        print(f"  Source discrepancies report: {artifact_paths.get('latest_markdown', 'n/a')}")
        return Path(artifact_paths.get("latest_json", REPORTS_DIR / "source-verification-latest.json"))

    sec13f_section = ""
    congress_section = ""
    convergence_section = ""
    sec13f_data = {}
    congress_data = {}

    # Run SEC 13F tracker
    if not args.congress_only:
        print("\n📊 Running SEC 13F tracker...\n")
        if args.fast_13f:
            print("  [INFO] fast-13f enabled: using default small fund set")
            sec13f_data = run_13f_tracker(
                funds=DEFAULT_FUNDS,
                date_range=date_range,
                sort_order=args.sort,
                result_limit=args.limit,
            )
        else:
            sec13f_data = run_13f_tracker(
                date_range=date_range,
                sort_order=args.sort,
                result_limit=args.limit,
            )
        sec13f_section = sec13f_data.get("report_section", "")
    else:
        sec13f_section = (
            "## 🐋 13F Whale Activity\n\n_Skipped ( --congress-only flag )_\n"
        )

    # Run Congress tracker
    if not args.__dict__.get("13f_only"):
        print("\n🏛️ Running Congress tracker...\n")
        congress_data = run_congress_tracker(
            days=args.days,
            member_filter=args.member,
            party_filter=args.party,
            chamber_filter=args.chamber,
            date_range=date_range,
            sort_order=args.sort,
            result_limit=args.limit,
            force_download=args.force_download,
        )
        congress_section = congress_data.get("report_section", "")
    else:
        congress_section = "## 🏛️ Congress Trades\n\n_Skipped ( --13f-only flag )_\n"

    # Run House Reps tracker
    house_reps_section = ""
    house_reps_data = {}
    if (
        not args.no_house_reps
        and not args.__dict__.get("13f_only")
        and not args.congress_only
    ):
        print("\n🏠 Running House Reps tracker...\n")
        house_reps_data = run_house_reps_tracker(
            days=args.days,
            member_filter=args.member,
            party_filter=args.party,
            date_range=date_range,
            sort_order=args.sort,
            result_limit=args.limit,
        )
        house_reps_section = house_reps_data.get("report_section", "")
    else:
        house_reps_section = "## 🏠 House Reps Disclosures\n\n_Skipped ( --no-house-reps or --13f-only or --congress-only flag )_\n"

    # Compute convergence (only if both trackers ran)
    if sec13f_data and congress_data:
        print("\n🎯 Computing convergence signals...\n")
        convergence = compute_convergence(sec13f_data, congress_data)
        convergence_section = generate_convergence_report(convergence, congress_data)
    else:
        convergence_section = (
            "## 🎯 Convergence Signals\n\n_Skipped (need both 13F and Congress data)_\n"
        )

    # Generate and save report
    conviction_section = ""
    if sec13f_data and "conviction_stats" in sec13f_data:
        stats = sec13f_data["conviction_stats"]
        if stats.get("top_conviction"):
            conviction_section = "\n## 🐋 Whale Conviction Stats\n"
            conviction_section += f"> Based on {stats['total_whales']} whales\n\n"
            conviction_section += "### Top Conviction Stocks (held by most whales)\n"
            for item in stats["top_conviction"][:10]:
                conviction_section += f"- **{item['stock']}**: {item['whale_count']} whales ({item['conviction_pct']}%)"
                if item["whales"]:
                    conviction_section += f" — {', '.join(item['whales'][:3])}"
                conviction_section += "\n"

    report = generate_full_report(
        sec13f_section,
        congress_section,
        house_reps_section,
        convergence_section,
        conviction_section,
    )

    today = date.today().strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"smart-money-{today}.md"
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
