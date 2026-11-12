from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import build_skill_parser, execute_skill_command


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the market-screen skill support script.")
    parser.add_argument("symbols", nargs="*")
    parser.add_argument("--file")
    parser.add_argument("--dir")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--source", choices=["auto", "akshare"], default="auto")
    parser.add_argument("--top", type=int, default=10)
    return execute_skill_command("market-screen", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
