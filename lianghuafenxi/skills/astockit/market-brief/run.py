from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import (
    add_market_args,
    add_position_args,
    build_skill_parser,
    execute_skill_command,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the market-brief skill support script.")
    add_market_args(parser)
    add_position_args(parser)
    parser.add_argument(
        "--style",
        choices=["auto", "breakout", "trend_pullback", "range_trade", "defensive"],
        default="auto",
    )
    parser.add_argument("--hold-days", dest="hold_days", type=int, default=15)
    parser.add_argument("--notify", action="store_true")
    return execute_skill_command("market-brief", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
