"""Deterministic signal rules migrated from strategy presets."""

from __future__ import annotations

import math
from typing import Callable

import pandas as pd

from core.models import MarketSnapshot, StrategyPlan
from strategies.models import StrategySignal
from strategies.registry import get_strategy_preset


def evaluate_strategy_signal(strategy_id: str, frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    mapping: dict[str, Callable[[pd.DataFrame, MarketSnapshot], StrategySignal]] = {
        "bull_trend": _bull_trend_signal,
        "ma_golden_cross": _ma_golden_cross_signal,
        "volume_breakout": _volume_breakout_signal,
        "shrink_pullback": _shrink_pullback_signal,
        "box_oscillation": _box_oscillation_signal,
        "bottom_volume": _bottom_volume_signal,
    }
    if strategy_id not in mapping:
        preset = get_strategy_preset(strategy_id)
        return StrategySignal(
            strategy_id=strategy_id,
            signal="watch",
            strength=0.25,
            reasons=[preset.description if preset else "策略未注册为可执行规则。"],
            hold_days=preset.holding_days if preset else 10,
        )
    return mapping[strategy_id](frame, snapshot)


def build_strategy_plan(strategy_id: str, frame: pd.DataFrame, snapshot: MarketSnapshot, *, risk_pct: float, capital: float) -> StrategyPlan:
    preset = get_strategy_preset(strategy_id)
    signal = evaluate_strategy_signal(strategy_id, frame, snapshot)
    position_pct = signal.target_position_pct
    if position_pct is None:
        position_pct = min(0.35, max(0.06, risk_pct * 8 + signal.strength * 0.18))
    hold_days = signal.hold_days or (preset.holding_days if preset else 10)
    entry = signal.entry_ref if signal.entry_ref is not None else snapshot.last_close
    stop = signal.stop_loss if signal.stop_loss is not None else max(snapshot.support, entry * 0.95)
    take = signal.take_profit if signal.take_profit is not None else entry * 1.08
    return StrategyPlan(
        style=strategy_id,
        holding_days=hold_days,
        entry_zone=f"{entry * 0.995:.2f} - {entry * 1.005:.2f}",
        stop_zone=f"{stop:.2f} 下方",
        take_profit_zone=f"{take:.2f} 一带",
        position_pct=round(position_pct, 3),
        checklist=signal.reasons,
        strategy_id=strategy_id,
        display_name=preset.display_name if preset else strategy_id,
        thesis=preset.description if preset else "",
        risk_notes=[f"signal={signal.signal}", f"strength={signal.strength:.2f}"],
    )


def render_strategy_summary(strategy_id: str, frame: pd.DataFrame, snapshot: MarketSnapshot) -> str:
    preset = get_strategy_preset(strategy_id)
    signal = evaluate_strategy_signal(strategy_id, frame, snapshot)
    lines = [
        f"# {strategy_id}",
        "",
        f"- display_name: {preset.display_name if preset else strategy_id}",
        f"- signal: {signal.signal}",
        f"- strength: {signal.strength:.2f}",
    ]
    if signal.entry_ref is not None:
        lines.append(f"- entry_ref: {signal.entry_ref:.2f}")
    if signal.stop_loss is not None:
        lines.append(f"- stop_loss: {signal.stop_loss:.2f}")
    if signal.take_profit is not None:
        lines.append(f"- take_profit: {signal.take_profit:.2f}")
    for item in signal.reasons:
        lines.append(f"- note: {item}")
    return "\n".join(lines)


def _bull_trend_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    latest = frame.iloc[-1]
    strength = 0.35
    reasons = []
    bullish_alignment = _gte(latest.get("ma5"), latest.get("ma10")) and _gte(latest.get("ma10"), latest.get("ma20"))
    if bullish_alignment:
        strength += 0.3
        reasons.append("MA5/MA10/MA20 多头排列。")
    if snapshot.trend == "上升":
        strength += 0.15
        reasons.append("趋势状态维持向上。")
    if snapshot.volume_ratio >= 1.0:
        strength += 0.1
        reasons.append("量能未明显衰减。")
    signal = "buy" if strength >= 0.65 and snapshot.change_pct < 6 else "watch"
    return StrategySignal(
        strategy_id="bull_trend",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons or ["趋势不够整齐，继续观察。"],
        entry_ref=snapshot.last_close,
        stop_loss=max(snapshot.support, snapshot.last_close * 0.95),
        take_profit=max(snapshot.resistance, snapshot.last_close * 1.08),
        hold_days=15,
        target_position_pct=0.22 if signal == "buy" else 0.0,
    )


def _ma_golden_cross_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    latest = frame.iloc[-1]
    prev = frame.iloc[-2] if len(frame) >= 2 else latest
    reasons = []
    cross = _lt(prev.get("ma5"), prev.get("ma10")) and _gte(latest.get("ma5"), latest.get("ma10"))
    slow_cross = _lt(prev.get("ma10"), prev.get("ma20")) and _gte(latest.get("ma10"), latest.get("ma20"))
    strength = 0.25
    if cross:
        strength += 0.35
        reasons.append("MA5 上穿 MA10。")
    if slow_cross:
        strength += 0.2
        reasons.append("MA10 上穿 MA20。")
    if snapshot.volume_ratio >= 1.2:
        strength += 0.1
        reasons.append("量比确认金叉。")
    if snapshot.indicators.get("macd_hist") is not None and snapshot.indicators.get("macd_hist", 0) >= 0:
        strength += 0.1
        reasons.append("MACD 未走弱。")
    signal = "buy" if strength >= 0.65 and _bias(snapshot.last_close, latest.get("ma5")) < 5 else "watch"
    return StrategySignal(
        strategy_id="ma_golden_cross",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons or ["未形成有效均线金叉。"],
        entry_ref=snapshot.last_close,
        stop_loss=max(snapshot.support, snapshot.last_close * 0.96),
        take_profit=snapshot.last_close * 1.10,
        hold_days=12,
        target_position_pct=0.2 if signal == "buy" else 0.0,
    )


def _volume_breakout_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    latest = frame.iloc[-1]
    prior_high = frame["high"].iloc[-21:-1].max() if len(frame) > 21 else frame["high"].iloc[:-1].max()
    strength = 0.2
    reasons = []
    if snapshot.last_close > prior_high:
        strength += 0.35
        reasons.append("收盘价站上前高阻力。")
    if snapshot.volume_ratio >= 2.0:
        strength += 0.25
        reasons.append("量能显著放大。")
    if _bias(snapshot.last_close, latest.get("ma5")) < 5:
        strength += 0.1
        reasons.append("突破后乖离率仍可接受。")
    signal = "buy" if strength >= 0.7 else "watch"
    return StrategySignal(
        strategy_id="volume_breakout",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons or ["尚未形成有效放量突破。"],
        entry_ref=max(snapshot.last_close, prior_high),
        stop_loss=prior_high * 0.97 if not math.isnan(prior_high) else snapshot.last_close * 0.95,
        take_profit=max(snapshot.last_close * 1.12, prior_high * 1.08 if not math.isnan(prior_high) else snapshot.last_close * 1.12),
        hold_days=10,
        target_position_pct=0.24 if signal == "buy" else 0.0,
    )


def _shrink_pullback_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    latest = frame.iloc[-1]
    strength = 0.25
    reasons = []
    if _gte(latest.get("ma5"), latest.get("ma10")) and _gte(latest.get("ma10"), latest.get("ma20")):
        strength += 0.25
        reasons.append("回踩前提满足，多头结构未破坏。")
    near_ma5 = abs(snapshot.last_close - latest.get("ma5", snapshot.last_close)) / max(latest.get("ma5", 1), 1) <= 0.01
    near_ma10 = abs(snapshot.last_close - latest.get("ma10", snapshot.last_close)) / max(latest.get("ma10", 1), 1) <= 0.02
    if near_ma5 or near_ma10:
        strength += 0.2
        reasons.append("价格回踩关键均线附近。")
    if frame.iloc[-1].get("volume_ratio_5d", 1.0) <= 0.75:
        strength += 0.15
        reasons.append("回踩过程缩量。")
    signal = "buy" if strength >= 0.65 else "watch"
    base_stop = latest.get("ma20", snapshot.support)
    return StrategySignal(
        strategy_id="shrink_pullback",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons or ["未形成理想的缩量回踩节奏。"],
        entry_ref=snapshot.last_close,
        stop_loss=max(snapshot.support, float(base_stop) * 0.98),
        take_profit=max(snapshot.resistance, snapshot.last_close * 1.08),
        hold_days=10,
        target_position_pct=0.18 if signal == "buy" else 0.0,
    )


def _box_oscillation_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    lookback = frame.iloc[-40:] if len(frame) >= 40 else frame
    top = float(lookback["high"].max())
    bottom = float(lookback["low"].min())
    width_pct = (top - bottom) / bottom * 100 if bottom else 0
    strength = 0.2
    reasons = []
    if 5 <= width_pct <= 20:
        strength += 0.2
        reasons.append("箱体宽度可交易。")
    if snapshot.last_close <= bottom * 1.05:
        strength += 0.3
        reasons.append("价格接近箱底。")
        signal = "buy"
    elif snapshot.last_close >= top * 0.95:
        strength += 0.25
        reasons.append("价格接近箱顶。")
        signal = "sell"
    else:
        signal = "watch"
        reasons.append("价格处于箱体中部。")
    return StrategySignal(
        strategy_id="box_oscillation",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons,
        entry_ref=bottom * 1.02,
        stop_loss=bottom * 0.97,
        take_profit=top * 0.99,
        hold_days=8,
        target_position_pct=0.16 if signal == "buy" else 0.0,
    )


def _bottom_volume_signal(frame: pd.DataFrame, snapshot: MarketSnapshot) -> StrategySignal:
    latest = frame.iloc[-1]
    lookback = frame.iloc[-30:] if len(frame) >= 30 else frame
    recent_high = float(lookback["high"].max())
    recent_low = float(lookback["low"].min())
    drawdown_pct = (recent_high - recent_low) / recent_high * 100 if recent_high else 0
    strength = 0.2
    reasons = []
    if drawdown_pct >= 15:
        strength += 0.2
        reasons.append("前期已有充分下跌。")
    if snapshot.volume_ratio >= 3.0:
        strength += 0.3
        reasons.append("底部放量显著。")
    if latest.get("close", 0) > latest.get("open", 0):
        strength += 0.1
        reasons.append("当前K线收阳。")
    signal = "buy" if strength >= 0.7 else "watch"
    return StrategySignal(
        strategy_id="bottom_volume",
        signal=signal,
        strength=min(strength, 0.95),
        reasons=reasons or ["底部放量条件未完全成立。"],
        entry_ref=snapshot.last_close,
        stop_loss=recent_low * 0.98,
        take_profit=snapshot.last_close * 1.10,
        hold_days=12,
        target_position_pct=0.14 if signal == "buy" else 0.0,
    )


def _gte(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and not math.isnan(float(a)) and not math.isnan(float(b)) and float(a) >= float(b)


def _lt(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and not math.isnan(float(a)) and not math.isnan(float(b)) and float(a) < float(b)


def _bias(price: float, moving_average: float | None) -> float:
    if moving_average is None or moving_average == 0 or math.isnan(float(moving_average)):
        return 0.0
    return abs(price - float(moving_average)) / float(moving_average) * 100
