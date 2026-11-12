"""Machine-readable strategy registry and routing helpers."""

from __future__ import annotations

import json
from pathlib import Path

from strategies.models import StrategyPreset


def _bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_strategy_registry() -> dict:
    path = _bundle_root() / "_registry" / "strategies.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_strategy_presets(*, execution_mode: str | None = None) -> list[StrategyPreset]:
    payload = load_strategy_registry()
    presets = [StrategyPreset(**item) for item in payload.get("strategies", [])]
    if execution_mode:
        presets = [item for item in presets if item.execution_mode == execution_mode]
    return presets


def get_strategy_preset(strategy_id: str) -> StrategyPreset | None:
    for preset in load_strategy_presets():
        if preset.id == strategy_id:
            return preset
    return None


def select_strategy_ids(regime: str | None, requested: list[str] | None = None, *, max_count: int = 3) -> list[str]:
    available = {item.id for item in load_strategy_presets()}
    if requested:
        selected = [item for item in requested if item in available]
        if selected:
            return selected[:max_count]
    if regime:
        tagged = [item.id for item in load_strategy_presets() if regime in item.router_tags]
        if tagged:
            return tagged[:max_count]
    fallback = [item.id for item in load_strategy_presets(execution_mode="deterministic")]
    return fallback[:max_count]
