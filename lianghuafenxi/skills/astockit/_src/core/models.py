"""Shared dataclasses for A-Stockit runtime outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    board: str
    source: str
    start: str
    end: str
    rows: int
    last_close: float
    change_pct: float
    amplitude_pct: float
    volume_ratio: float
    atr_pct: float
    turnover_pct: float | None
    support: float
    resistance: float
    score: int
    regime: str
    trend: str
    limit_pct: float
    indicators: dict[str, float | None] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionPacket:
    action: str
    confidence: float
    target_position_pct: float
    quantity: int
    entry_ref: float
    stop_loss: float
    take_profit: float
    risk_budget: float
    reasons: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategyPlan:
    style: str
    holding_days: int
    entry_zone: str
    stop_zone: str
    take_profit_zone: str
    position_pct: float
    checklist: list[str] = field(default_factory=list)
    strategy_id: str = ""
    display_name: str = ""
    thesis: str = ""
    risk_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
