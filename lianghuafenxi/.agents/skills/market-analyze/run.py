from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import (
    add_market_args,
    build_skill_parser,
    execute_skill_command,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the market-analyze skill support script.")
    add_market_args(parser)
    return execute_skill_command("market-analyze", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
