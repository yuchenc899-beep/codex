#!/usr/bin/env python3
"""Thin wrapper around smart_money_tracker.source_audit — verify external sources.

Usage:
    python scripts/source_audit.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smart_money_tracker.source_audit import main  # noqa: E402

if __name__ == "__main__":
    main()
