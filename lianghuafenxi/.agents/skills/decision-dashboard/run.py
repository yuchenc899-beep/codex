from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import build_skill_parser, execute_skill_command


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the decision-dashboard skill support script.")
    parser.add_argument("symbols", nargs="*")
    parser.add_argument("--file")
    parser.add_argument("--dir")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--source", choices=["auto", "akshare"], default="auto")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--capital", type=float, default=100000.0)
    parser.add_argument("--cash", type=float)
    parser.add_argument("--risk", type=float, default=0.01)
    parser.add_argument("--max-position", dest="max_position", type=float, default=0.25)
    return execute_skill_command("decision-dashboard", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
