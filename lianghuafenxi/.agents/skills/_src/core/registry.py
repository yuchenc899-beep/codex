"""Registry readers for bundle metadata, skills, and runtime contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_root() -> Path:
    return bundle_root() / "_registry"


def _load_json(name: str) -> dict[str, Any]:
    path = registry_root() / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_bundle_metadata() -> dict[str, Any]:
    return _load_json("bundle.json")


def load_skill_registry() -> dict[str, Any]:
    return _load_json("skills.json")


def load_runtime_registry() -> dict[str, Any]:
    return _load_json("runtime.json")
