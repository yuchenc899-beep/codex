"""Dataclasses for strategy backtesting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BacktestConfig:
    initial_cash: float = 100000.0
    max_position_pct: float = 0.2
    commission_rate: float = 0.0003
    min_commission: float = 5.0
    stamp_duty_rate: float = 0.001
    slippage_bps: float = 5.0
    lot_size: int = 100
    allow_same_day_sell: bool = False
    max_holding_days: int = 15
    risk_free_rate: float = 0.0
    conservative_intraday: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExecutedTrade:
    symbol: str
    strategy_id: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    quantity: int
    fees: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_days: int
    exit_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DailyEquityPoint:
    date: str
    cash: float
    position_qty: int
    close: float
    position_value: float
    equity: float
    drawdown_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BacktestMetrics:
    initial_cash: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    annual_volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    trade_count: int
    win_rate_pct: float
    average_trade_return_pct: float
    profit_factor: float
    exposure_pct: float
    turnover_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BacktestReport:
    symbol: str
    strategy_id: str
    metrics: BacktestMetrics
    trades: list[ExecutedTrade] = field(default_factory=list)
    equity_curve: list[DailyEquityPoint] = field(default_factory=list)
    signal_log: list[dict[str, Any]] = field(default_factory=list)
    config: BacktestConfig = field(default_factory=BacktestConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "metrics": self.metrics.to_dict(),
            "trades": [item.to_dict() for item in self.trades],
            "equity_curve": [item.to_dict() for item in self.equity_curve],
            "signal_log": self.signal_log,
            "config": self.config.to_dict(),
        }
