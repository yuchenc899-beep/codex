from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import (
    add_market_args,
    add_strategy_args,
    build_skill_parser,
    execute_skill_command,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the strategy-design skill support script.")
    add_market_args(parser)
    add_strategy_args(parser)
    parser.add_argument("--capital", type=float, default=100000.0)
    parser.add_argument("--risk", type=float, default=0.01)
    parser.add_argument(
        "--style",
        default="auto",
    )
    parser.add_argument("--hold-days", dest="hold_days", type=int, default=15)
    return execute_skill_command("strategy-design", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
