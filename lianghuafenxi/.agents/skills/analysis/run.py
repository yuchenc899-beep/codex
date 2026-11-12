from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import (
    add_market_args,
    add_news_args,
    add_position_args,
    add_strategy_args,
    build_skill_parser,
    execute_skill_command,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the analysis skill support script.")
    add_market_args(parser)
    add_position_args(parser)
    add_news_args(parser)
    add_strategy_args(parser)
    parser.add_argument(
        "--style",
        choices=["auto", "breakout", "trend_pullback", "range_trade", "defensive"],
        default="auto",
    )
    parser.add_argument("--hold-days", dest="hold_days", type=int, default=10)
    parser.add_argument("--depth", choices=["compact", "standard", "deep"], default="standard")
    return execute_skill_command("analysis", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
