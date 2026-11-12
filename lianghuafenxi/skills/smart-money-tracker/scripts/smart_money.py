#!/usr/bin/env python3
"""Thin wrapper around smart_money_tracker.main — run from project root or scripts/ dir.

Usage:
    python scripts/smart_money.py --13f-only --fast-13f
    python scripts/smart_money.py --congress-only
    python scripts/smart_money.py --no-house-reps --fast-13f
    python scripts/smart_money.py --verify-sources
    python scripts/smart_money.py --date-range 2026-01-01,2026-03-31

The actual implementation lives at src/smart_money_tracker/main.py.
This shim only exists so the skill follows the standard `scripts/` convention
while keeping the package importable for tests.
"""
import os
import sys

# Allow import from src/ when this script is run from any cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smart_money_tracker.main import main  # noqa: E402

if __name__ == "__main__":
    main()
