"""Dataclasses shared by richer research-oriented skill helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class QueryPlan:
    label: str
    query: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NewsItem:
    title: str
    summary: str
    source: str
    published_at: str = ""
    url: str = ""
    sentiment: str = "neutral"
    relevance: float = 0.0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NewsIntelReport:
    symbol: str
    query_plan: list[QueryPlan] = field(default_factory=list)
    items: list[NewsItem] = field(default_factory=list)
    catalysts: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    narratives: list[str] = field(default_factory=list)
    sentiment_bias: str = "neutral"
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "query_plan": [item.to_dict() for item in self.query_plan],
            "items": [item.to_dict() for item in self.items],
            "catalysts": self.catalysts,
            "risks": self.risks,
            "narratives": self.narratives,
            "sentiment_bias": self.sentiment_bias,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class StockResearchPacket:
    symbol: str
    generated_at: str
    workflow: list[dict[str, str]] = field(default_factory=list)
    core_conclusion: dict[str, Any] = field(default_factory=dict)
    data_perspective: dict[str, Any] = field(default_factory=dict)
    intelligence: dict[str, Any] = field(default_factory=dict)
    battle_plan: dict[str, Any] = field(default_factory=dict)
    raw_blocks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BacktestEvaluation:
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    holding_days: int
    change_pct: float
    max_upside_pct: float
    max_drawdown_pct: float
    stop_loss_hit: bool
    take_profit_hit: bool
    verdict: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperLot:
    quantity: int
    trade_date: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    market: str
    quantity: int = 0
    avg_cost: float = 0.0
    last_price: float | None = None
    lots: list[PaperLot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "market": self.market,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "last_price": self.last_price,
            "lots": [item.to_dict() for item in self.lots],
        }


@dataclass(slots=True)
class PaperTrade:
    trade_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    fees: float
    notional: float
    trade_date: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PaperBook:
    account: str
    cash: float
    positions: dict[str, PaperPosition] = field(default_factory=dict)
    trades: list[PaperTrade] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "cash": self.cash,
            "positions": {key: value.to_dict() for key, value in self.positions.items()},
            "trades": [item.to_dict() for item in self.trades],
        }


@dataclass(slots=True)
class CapabilityProfile:
    model: str
    speed: int
    reasoning: int
    tool_calling: int
    context_window: int
    cost_efficiency: int
    strengths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModelRecommendation:
    workflow: str
    quick_model: str | None
    deep_model: str | None
    rationale: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    candidate_profiles: list[CapabilityProfile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "quick_model": self.quick_model,
            "deep_model": self.deep_model,
            "rationale": self.rationale,
            "warnings": self.warnings,
            "candidate_profiles": [item.to_dict() for item in self.candidate_profiles],
        }

