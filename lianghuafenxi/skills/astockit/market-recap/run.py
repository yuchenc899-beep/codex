from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_src"))

from core.skill_support import build_skill_parser, execute_skill_command


def main(argv: list[str] | None = None) -> int:
    parser = build_skill_parser("Run the market-recap skill support script.")
    parser.add_argument("--region", choices=["cn", "us"], default="cn")
    parser.add_argument("--format", choices=["markdown", "prompt"], default="markdown")
    return execute_skill_command("market-recap", parser, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
