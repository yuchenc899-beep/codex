"""Retrospective evaluation helpers for saved analysis runs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.models import BacktestEvaluation


def load_state_payload(path: str | Path) -> dict:
    payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    return payload


def evaluate_saved_run(payload: dict, future_frame: pd.DataFrame, holding_days: int | None = None) -> BacktestEvaluation:
    raw_blocks = payload.get("raw_blocks", {})
    snapshot = payload.get("snapshot", {}) or raw_blocks.get("snapshot", {})
    decision = payload.get("decision", {}) or raw_blocks.get("decision", {})
    strategy = payload.get("strategy", {}) or raw_blocks.get("strategy", {})
    symbol = snapshot.get("symbol") or payload.get("symbol") or "unknown"
    entry_price = float(decision.get("entry_ref") or snapshot.get("last_close") or future_frame.iloc[0]["close"])
    action = decision.get("action", "watch")
    stop_loss = decision.get("stop_loss")
    take_profit = decision.get("take_profit")
    window = int(holding_days or strategy.get("holding_days") or 10)
    result = evaluate_trade_plan(
        symbol=symbol,
        future_frame=future_frame,
        action=action,
        entry_price=entry_price,
        stop_loss=float(stop_loss) if stop_loss else None,
        take_profit=float(take_profit) if take_profit else None,
        holding_days=window,
    )
    result.notes.extend(
        [
            "entry_assumption=saved entry_ref or last_close fallback",
            "exit_assumption=window close",
            "stop_take_flags=intraday threshold touches, not actual fill path",
            "hindsight_guard=subsequent events inside the window were not knowable at decision time",
        ]
    )
    return result


def evaluate_trade_plan(
    *,
    symbol: str,
    future_frame: pd.DataFrame,
    action: str,
    entry_price: float,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    holding_days: int = 10,
) -> BacktestEvaluation:
    work = future_frame.sort_values("date").reset_index(drop=True).copy()
    window = max(1, min(holding_days, len(work)))
    sliced = work.iloc[:window]
    exit_price = float(sliced.iloc[-1]["close"])
    high = float(sliced["high"].max())
    low = float(sliced["low"].min())
    change_pct = round((exit_price - entry_price) / entry_price * 100, 2)
    max_upside_pct = round((high - entry_price) / entry_price * 100, 2)
    max_drawdown_pct = round((low - entry_price) / entry_price * 100, 2)
    stop_hit = bool(stop_loss and low <= stop_loss)
    take_hit = bool(take_profit and high >= take_profit)
    verdict, notes = _judge(action, change_pct, stop_hit, take_hit, max_upside_pct, max_drawdown_pct)
    return BacktestEvaluation(
        symbol=symbol,
        action=action,
        entry_price=round(entry_price, 4),
        exit_price=round(exit_price, 4),
        holding_days=window,
        change_pct=change_pct,
        max_upside_pct=max_upside_pct,
        max_drawdown_pct=max_drawdown_pct,
        stop_loss_hit=stop_hit,
        take_profit_hit=take_hit,
        verdict=verdict,
        notes=notes,
    )


def _judge(
    action: str,
    change_pct: float,
    stop_hit: bool,
    take_hit: bool,
    max_upside_pct: float,
    max_drawdown_pct: float,
) -> tuple[str, list[str]]:
    notes = []
    bullish = action in {"buy", "hold"}
    if stop_hit:
        notes.append("stop-loss would have triggered inside the window")
    if take_hit:
        notes.append("take-profit would have triggered inside the window")
    notes.append(f"max_upside={max_upside_pct:.2f}%")
    notes.append(f"max_drawdown={max_drawdown_pct:.2f}%")
    if bullish and change_pct > 0 and not stop_hit:
        return "outcome aligned", notes
    if bullish and stop_hit:
        return "outcome diverged", notes
    if not bullish and change_pct < 0:
        return "outcome aligned", notes
    if abs(change_pct) < 1 and not stop_hit and not take_hit:
        return "outcome inconclusive", notes
    return "outcome mixed", notes


def render_backtest_evaluation(result: BacktestEvaluation) -> str:
    lines = [
        f"# {result.symbol} Backtest Evaluation",
        "",
        f"- action: {result.action}",
        f"- holding_days: {result.holding_days}",
        f"- entry/exit: {result.entry_price} / {result.exit_price}",
        f"- change_pct: {result.change_pct:.2f}%",
        f"- max_upside_pct: {result.max_upside_pct:.2f}%",
        f"- max_drawdown_pct: {result.max_drawdown_pct:.2f}%",
        f"- stop_loss_hit: {result.stop_loss_hit}",
        f"- take_profit_hit: {result.take_profit_hit}",
        f"- outcome: {result.verdict}",
    ]
    for note in result.notes:
        lines.append(f"- note: {note}")
    return "\n".join(lines)
