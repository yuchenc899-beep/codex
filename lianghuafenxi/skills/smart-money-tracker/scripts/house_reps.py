#!/usr/bin/env python3
"""Thin wrapper around smart_money_tracker.house_reps — House Clerk disclosure filter.

Usage:
    python scripts/house_reps.py --member "Nancy Pelosi" --days 90
    python scripts/house_reps.py --party Republican --date-range 2026-01-01,2026-03-31
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smart_money_tracker.house_reps import main  # noqa: E402

if __name__ == "__main__":
    main()
