#!/usr/bin/env python3
"""Thin wrapper around smart_money_tracker.congress — congress-only filter.

Usage:
    python scripts/congress.py --member "Nancy Pelosi" --days 90
    python scripts/congress.py --party Republican --chamber Senate
    python scripts/congress.py --date-range 2026-01-01,2026-03-31 --sort datedesc --limit 10
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smart_money_tracker.congress import main  # noqa: E402

if __name__ == "__main__":
    main()
