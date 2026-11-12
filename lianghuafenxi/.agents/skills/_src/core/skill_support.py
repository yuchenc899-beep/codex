"""Shared parser and invocation helpers for skill-local support scripts."""

from __future__ import annotations

import argparse
from typing import Sequence

from core.runtime import RUNTIME_HELP, BundleRuntime


class SkillParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_skill_parser(description: str) -> argparse.ArgumentParser:
    parser = SkillParser(description=description)
    parser.add_argument("--config", help="Path to astockit.json")
    parser.add_argument("--context", default="default", help="Logical execution context")
    return parser


def add_market_args(parser: argparse.ArgumentParser, *, include_export: bool = False) -> None:
    parser.add_argument("symbol", nargs="?")
    parser.add_argument("--csv")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--source", choices=["auto", "akshare"], default="auto")
    if include_export:
        parser.add_argument("--export")


def add_position_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--capital", type=float, default=100000.0)
    parser.add_argument("--cash", type=float)
    parser.add_argument("--position", type=int, default=0)
    parser.add_argument("--risk", type=float, default=0.01)
    parser.add_argument("--max-position", dest="max_position", type=float, default=0.25)


def add_news_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--headline", action="append", help="One headline or 'title | summary' entry")
    parser.add_argument("--headline-file", dest="headline_file")
    parser.add_argument("--company-name", dest="company_name")
    parser.add_argument("--alias", action="append")
    parser.add_argument("--max-items", dest="max_items", type=int, default=8)


def add_backtest_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state", help="Path to saved state.json")
    parser.add_argument("--from-command", dest="from_command", default="analysis")
    parser.add_argument("--holding-days", dest="holding_days", type=int)
    parser.add_argument("--strategy", action="append", help="Strategy id to backtest")
    parser.add_argument("--initial-cash", dest="initial_cash", type=float, default=100000.0)
    parser.add_argument("--slippage-bps", dest="slippage_bps", type=float, default=5.0)
    parser.add_argument("--max-position-pct", dest="max_position_pct", type=float, default=0.2)


def add_paper_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--side", choices=["buy", "sell"])
    parser.add_argument("--quantity", type=int, default=0)
    parser.add_argument("--price", type=float)
    parser.add_argument("--account", default="default")
    parser.add_argument("--initial-cash", dest="initial_cash", type=float, default=100000.0)
    parser.add_argument("--trade-date", dest="trade_date")
    parser.add_argument("--note", default="")


def add_model_advisor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", nargs="?")
    parser.add_argument("--workflow", default="analysis")
    parser.add_argument("--quick", action="append")
    parser.add_argument("--deep", action="append")


def add_strategy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--strategy", action="append", help="Strategy id or preset to force")


def execute_skill_command(
    command: str,
    parser: argparse.ArgumentParser,
    argv: Sequence[str] | None = None,
) -> int:
    raw_argv = list(argv) if argv is not None else None
    try:
        namespace = parser.parse_args(raw_argv)
    except ValueError as exc:
        print(f"命令错误: {exc}\n\n{RUNTIME_HELP}")
        return 2
    namespace.command = command
    provided_flags = {
        token.split("=", 1)[0]
        for token in (raw_argv or [])
        if isinstance(token, str) and token.startswith("--")
    }
    namespace._provided_flags = sorted(provided_flags)
    try:
        runtime = BundleRuntime(getattr(namespace, "config", None))
        context = getattr(namespace, "context", "default")
        print(runtime.run(namespace, context=context))
        return 0
    except Exception as exc:
        print(f"执行失败: {exc}")
        return 1
