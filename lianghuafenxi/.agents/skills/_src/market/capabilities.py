"""Reusable domain utilities that power A-Stockit skills.

The project keeps trading logic in a small registry instead of scattering
similar implementations across individual workflow handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from core.models import DecisionPacket, MarketSnapshot, StrategyPlan
from strategies.registry import get_strategy_preset, select_strategy_ids
from strategies.signals import build_strategy_plan, evaluate_strategy_signal


@dataclass(slots=True)
class Capability:
    name: str
    summary: str
    handler: Callable[..., dict[str, Any]]


class CapabilityRegistry:
    """Minimal capability registry for named runtime handlers."""

    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, name: str, summary: str, handler: Callable[..., dict[str, Any]]) -> None:
        self._items[name] = Capability(name=name, summary=summary, handler=handler)

    def execute(self, name: str, **kwargs) -> dict[str, Any]:
        if name not in self._items:
            raise KeyError(name)
        return self._items[name].handler(**kwargs)

    def help_rows(self) -> list[tuple[str, str]]:
        return sorted((item.name, item.summary) for item in self._items.values())


def _round_lot(quantity: float, lot_size: int) -> int:
    return max(0, int(floor(quantity / lot_size) * lot_size))


def data_processing(
    *,
    symbol: str,
    frame: pd.DataFrame,
    snapshot: MarketSnapshot,
    export_path: str | None = None,
) -> dict[str, Any]:
    exported = None
    if export_path:
        target = Path(export_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(target, index=False)
        exported = str(target)
    latest = frame.iloc[-1]
    return {
        "summary": {
            "symbol": symbol,
            "source": snapshot.source,
            "rows": snapshot.rows,
            "date_range": [snapshot.start, snapshot.end],
            "last_close": snapshot.last_close,
            "last_volume": int(latest["volume"]),
            "turnover_pct": snapshot.turnover_pct,
            "exported": exported,
        }
    }


def market_analysis(*, snapshot: MarketSnapshot) -> dict[str, Any]:
    bias = "偏多" if snapshot.score >= 65 else "观望" if snapshot.score >= 45 else "偏谨慎"
    return {
        "summary": {
            "bias": bias,
            "score": snapshot.score,
            "regime": snapshot.regime,
            "trend": snapshot.trend,
            "key_levels": {"support": snapshot.support, "resistance": snapshot.resistance},
            "notes": snapshot.notes,
            "risk_flags": snapshot.risk_flags,
        }
    }


def decision_support(
    *,
    snapshot: MarketSnapshot,
    capital: float,
    cash: float | None,
    position: int,
    risk_pct: float,
    max_position_pct: float,
    lot_size: int,
) -> dict[str, Any]:
    cash = capital if cash is None else cash
    target_pct = max(0.0, min(max_position_pct, snapshot.score / 100 * max_position_pct))
    entry_ref = snapshot.last_close
    stop_loss = round(max(snapshot.support, snapshot.last_close * (1 - max(snapshot.atr_pct / 100 * 1.5, 0.03))), 2)
    take_profit = round(snapshot.last_close + (snapshot.last_close - stop_loss) * 2.5, 2)
    risk_budget = capital * risk_pct
    risk_per_share = max(snapshot.last_close - stop_loss, snapshot.last_close * 0.01)
    risk_qty = risk_budget / risk_per_share if risk_per_share else 0
    budget_qty = cash / snapshot.last_close if snapshot.last_close else 0
    max_position_qty = capital * target_pct / snapshot.last_close if snapshot.last_close else 0
    planned_qty = _round_lot(min(risk_qty, budget_qty, max_position_qty), lot_size)

    if snapshot.score >= 72 and snapshot.regime in {"breakout_watch", "trend_pullback"}:
        action = "buy"
    elif snapshot.score >= 55:
        action = "watch" if position == 0 else "hold"
    elif snapshot.score >= 38:
        action = "hold" if position > 0 else "avoid"
    else:
        action = "reduce" if position > 0 else "avoid"

    if action == "reduce":
        planned_qty = _round_lot(max(position * 0.5, lot_size), lot_size) if position >= lot_size else position
    if action in {"hold", "avoid", "watch"}:
        planned_qty = 0

    reasons = [
        f"综合评分 {snapshot.score}/100，当前处于 {snapshot.regime}。",
        f"趋势判定为 {snapshot.trend}，20日支撑 {snapshot.support:.2f}，20日阻力 {snapshot.resistance:.2f}。",
        f"量比 {snapshot.volume_ratio:.2f}，ATR 波动 {snapshot.atr_pct:.2f}%。",
    ]
    packet = DecisionPacket(
        action=action,
        confidence=round(min(0.95, max(0.35, snapshot.score / 100)), 2),
        target_position_pct=round(target_pct, 3),
        quantity=planned_qty,
        entry_ref=entry_ref,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_budget=round(risk_budget, 2),
        reasons=reasons,
        risk_flags=snapshot.risk_flags,
    )
    return {"summary": packet}


def strategy_design(
    *,
    snapshot: MarketSnapshot,
    frame: pd.DataFrame | None = None,
    capital: float,
    style: str,
    risk_pct: float,
    holding_days: int,
    strategies_requested: list[str] | None = None,
) -> dict[str, Any]:
    strategy_id = None
    if frame is not None:
        if style == "auto":
            strategy_id = select_strategy_ids(snapshot.regime, strategies_requested, max_count=1)[0]
        elif get_strategy_preset(style):
            strategy_id = style
        elif strategies_requested:
            selected = select_strategy_ids(snapshot.regime, strategies_requested, max_count=1)
            strategy_id = selected[0] if selected else None
    if strategy_id and frame is not None:
        plan = build_strategy_plan(
            strategy_id,
            frame,
            snapshot,
            risk_pct=risk_pct,
            capital=capital,
        )
        return {"summary": plan, "signal": evaluate_strategy_signal(strategy_id, frame, snapshot).to_dict()}

    chosen = style
    if style == "auto":
        if snapshot.regime == "breakout_watch":
            chosen = "breakout"
        elif snapshot.regime == "trend_pullback":
            chosen = "trend_pullback"
        elif snapshot.score < 45:
            chosen = "defensive"
        else:
            chosen = "range_trade"

    if chosen == "breakout":
        entry_zone = f"{snapshot.resistance * 0.998:.2f} - {snapshot.resistance * 1.01:.2f}"
        stop_zone = f"{max(snapshot.support, snapshot.last_close * 0.95):.2f} 下方"
        take_profit_zone = f"{snapshot.last_close * 1.08:.2f} - {snapshot.last_close * 1.15:.2f}"
        checklist = ["仅在放量站上阻力时执行。", "次日若缩量回落到阻力下方，撤退。", "避免追击接近涨停带。"]
    elif chosen == "trend_pullback":
        entry_zone = f"{snapshot.support:.2f} - {snapshot.last_close:.2f}"
        stop_zone = f"{snapshot.support * 0.97:.2f} 下方"
        take_profit_zone = f"{snapshot.resistance:.2f} - {snapshot.resistance * 1.05:.2f}"
        checklist = ["等待回踩 20 日均线附近缩量企稳。", "若 MACD 柱继续扩张转弱，取消挂单。", "先做分批建仓，不一次性满仓。"]
    elif chosen == "defensive":
        entry_zone = "以观察为主，不主动开新仓"
        stop_zone = "已有仓位跌破关键支撑即减仓"
        take_profit_zone = "反抽到阻力区优先兑现"
        checklist = ["仓位降到轻仓。", "优先保留高流动性品种。", "等待趋势重新转正后再恢复进攻。"]
    else:
        entry_zone = f"{snapshot.support:.2f} - {snapshot.resistance:.2f} 区间低吸"
        stop_zone = f"{snapshot.support * 0.98:.2f} 下方"
        take_profit_zone = f"{snapshot.resistance * 0.99:.2f} 一带"
        checklist = ["震荡市只做区间，不追涨。", "若放量突破阻力，切换为 breakout。", "若跌破支撑，立刻取消区间假设。"]

    position_pct = min(0.3, max(0.08, capital * risk_pct / max(capital, 1) * 8 + snapshot.score / 400))
    plan = StrategyPlan(
        style=chosen,
        holding_days=holding_days,
        entry_zone=entry_zone,
        stop_zone=stop_zone,
        take_profit_zone=take_profit_zone,
        position_pct=round(position_pct, 3),
        checklist=checklist,
        strategy_id=chosen,
        display_name=chosen,
    )
    return {"summary": plan}


def screen_market(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(rows, key=lambda item: item["score"], reverse=True)
    return {"summary": ranked}


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register("data", "标准化行情并输出指标数据。", data_processing)
    registry.register("analyze", "输出 A 股市场状态与关键位。", market_analysis)
    registry.register("decision", "基于评分、风险和仓位约束给出动作。", decision_support)
    registry.register("strategy", "设计执行风格、进出场区间和检查清单。", strategy_design)
    registry.register("screen", "批量排序多个 A 股标的。", screen_market)
    return registry
