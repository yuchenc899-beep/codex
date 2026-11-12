"""Strategy registry data structures."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StrategyPreset:
    id: str
    display_name: str
    category: str
    execution_mode: str
    description: str
    router_tags: list[str] = field(default_factory=list)
    holding_days: int = 10

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategySignal:
    strategy_id: str
    signal: str
    strength: float
    reasons: list[str] = field(default_factory=list)
    entry_ref: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    hold_days: int | None = None
    target_position_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
