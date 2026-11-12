"""Deterministic long-only strategy backtest engine."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from math import floor, sqrt

import pandas as pd

from backtest.models import BacktestConfig, BacktestMetrics, BacktestReport, DailyEquityPoint, ExecutedTrade
from market.data import build_snapshot
from research.indicators import add_all_indicators
from strategies.signals import evaluate_strategy_signal


@dataclass(slots=True)
class _OpenPosition:
    entry_date: str
    entry_price: float
    quantity: int
    fees_paid: float
    stop_loss: float | None
    take_profit: float | None
    signal_date: str


def run_strategy_backtest(symbol: str, frame: pd.DataFrame, strategy_id: str, config: BacktestConfig) -> BacktestReport:
    enriched = add_all_indicators(frame.sort_values("date").reset_index(drop=True))
    cash = config.initial_cash
    position: _OpenPosition | None = None
    trades: list[ExecutedTrade] = []
    equity_curve: list[DailyEquityPoint] = []
    signal_log: list[dict] = []
    turnover = 0.0
    exposure_days = 0
    peak_equity = config.initial_cash

    start_index = min(max(20, 1), max(len(enriched) - 2, 1))
    for idx in range(start_index, len(enriched)):
        window = enriched.iloc[: idx + 1].copy()
        row = enriched.iloc[idx]
        current_date = str(row["date"])
        close_price = float(row["close"])

        if position and idx > 0:
            exit_trade = _check_intraday_exit(symbol, strategy_id, row, position, config, idx)
            if exit_trade:
                cash += position.quantity * exit_trade.exit_price - exit_trade.fees
                turnover += position.quantity * exit_trade.exit_price
                trades.append(exit_trade)
                position = None

        if idx < len(enriched) - 1:
            snapshot = build_snapshot(symbol, window, "backtest")
            signal = evaluate_strategy_signal(strategy_id, window, snapshot)
            signal_log.append(
                {
                    "date": current_date,
                    "signal": signal.signal,
                    "strength": signal.strength,
                    "reasons": signal.reasons,
                }
            )
            next_row = enriched.iloc[idx + 1]
            next_open = float(next_row["open"])
            next_date = str(next_row["date"])

            if position is None and signal.signal == "buy":
                quantity = _position_size(cash, next_open, signal.target_position_pct or config.max_position_pct, config)
                if quantity > 0:
                    entry_price = _apply_slippage(next_open, "buy", config.slippage_bps)
                    fees = _commission(entry_price * quantity, "buy", config)
                    total_cost = entry_price * quantity + fees
                    if total_cost <= cash:
                        cash -= total_cost
                        turnover += entry_price * quantity
                        position = _OpenPosition(
                            entry_date=next_date,
                            entry_price=entry_price,
                            quantity=quantity,
                            fees_paid=fees,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            signal_date=current_date,
                        )
            elif position is not None and signal.signal == "sell":
                if config.allow_same_day_sell or position.entry_date < next_date:
                    exit_price = _apply_slippage(next_open, "sell", config.slippage_bps)
                    exit_fees = _commission(exit_price * position.quantity, "sell", config)
                    gross_pnl = (exit_price - position.entry_price) * position.quantity
                    net_pnl = gross_pnl - position.fees_paid - exit_fees
                    return_pct = net_pnl / (position.entry_price * position.quantity) * 100
                    trade = ExecutedTrade(
                        symbol=symbol,
                        strategy_id=strategy_id,
                        entry_date=position.entry_date,
                        entry_price=round(position.entry_price, 4),
                        exit_date=next_date,
                        exit_price=round(exit_price, 4),
                        quantity=position.quantity,
                        fees=round(position.fees_paid + exit_fees, 2),
                        gross_pnl=round(gross_pnl, 2),
                        net_pnl=round(net_pnl, 2),
                        return_pct=round(return_pct, 2),
                        holding_days=_holding_days(position.entry_date, next_date),
                        exit_reason="signal",
                    )
                    cash += position.quantity * exit_price - exit_fees
                    turnover += position.quantity * exit_price
                    trades.append(trade)
                    position = None

        position_value = 0.0
        if position is not None:
            exposure_days += 1
            position_value = position.quantity * close_price
            if _holding_days(position.entry_date, current_date) >= config.max_holding_days and idx < len(enriched) - 1:
                next_row = enriched.iloc[idx + 1]
                exit_price = _apply_slippage(float(next_row["open"]), "sell", config.slippage_bps)
                exit_fees = _commission(exit_price * position.quantity, "sell", config)
                gross_pnl = (exit_price - position.entry_price) * position.quantity
                net_pnl = gross_pnl - position.fees_paid - exit_fees
                return_pct = net_pnl / (position.entry_price * position.quantity) * 100
                trade = ExecutedTrade(
                    symbol=symbol,
                    strategy_id=strategy_id,
                    entry_date=position.entry_date,
                    entry_price=round(position.entry_price, 4),
                    exit_date=str(next_row["date"]),
                    exit_price=round(exit_price, 4),
                    quantity=position.quantity,
                    fees=round(position.fees_paid + exit_fees, 2),
                    gross_pnl=round(gross_pnl, 2),
                    net_pnl=round(net_pnl, 2),
                    return_pct=round(return_pct, 2),
                    holding_days=_holding_days(position.entry_date, str(next_row["date"])),
                    exit_reason="time",
                )
                cash += position.quantity * exit_price - exit_fees
                turnover += position.quantity * exit_price
                trades.append(trade)
                position = None
                position_value = 0.0

        equity = cash + position_value
        peak_equity = max(peak_equity, equity)
        drawdown_pct = 0.0 if peak_equity <= 0 else (equity - peak_equity) / peak_equity * 100
        equity_curve.append(
            DailyEquityPoint(
                date=current_date,
                cash=round(cash, 2),
                position_qty=position.quantity if position else 0,
                close=round(close_price, 4),
                position_value=round(position_value, 2),
                equity=round(equity, 2),
                drawdown_pct=round(drawdown_pct, 2),
            )
        )

    if position is not None:
        last_row = enriched.iloc[-1]
        exit_price = _apply_slippage(float(last_row["close"]), "sell", config.slippage_bps)
        exit_fees = _commission(exit_price * position.quantity, "sell", config)
        gross_pnl = (exit_price - position.entry_price) * position.quantity
        net_pnl = gross_pnl - position.fees_paid - exit_fees
        return_pct = net_pnl / (position.entry_price * position.quantity) * 100
        trades.append(
            ExecutedTrade(
                symbol=symbol,
                strategy_id=strategy_id,
                entry_date=position.entry_date,
                entry_price=round(position.entry_price, 4),
                exit_date=str(last_row["date"]),
                exit_price=round(exit_price, 4),
                quantity=position.quantity,
                fees=round(position.fees_paid + exit_fees, 2),
                gross_pnl=round(gross_pnl, 2),
                net_pnl=round(net_pnl, 2),
                return_pct=round(return_pct, 2),
                holding_days=_holding_days(position.entry_date, str(last_row["date"])),
                exit_reason="final_mark",
            )
        )
        cash += position.quantity * exit_price - exit_fees

    metrics = _compute_metrics(config, trades, equity_curve, turnover, exposure_days)
    return BacktestReport(
        symbol=symbol,
        strategy_id=strategy_id,
        metrics=metrics,
        trades=trades,
        equity_curve=equity_curve,
        signal_log=signal_log,
        config=config,
    )


def render_backtest_report(report: BacktestReport) -> str:
    metrics = report.metrics
    lines = [
        f"# {report.symbol} {report.strategy_id} Backtest",
        "",
        f"- final_equity: {metrics.final_equity:.2f}",
        f"- total_return_pct: {metrics.total_return_pct:.2f}",
        f"- cagr_pct: {metrics.cagr_pct:.2f}",
        f"- annual_volatility_pct: {metrics.annual_volatility_pct:.2f}",
        f"- sharpe_ratio: {metrics.sharpe_ratio:.2f}",
        f"- max_drawdown_pct: {metrics.max_drawdown_pct:.2f}",
        f"- trade_count: {metrics.trade_count}",
        f"- win_rate_pct: {metrics.win_rate_pct:.2f}",
        f"- average_trade_return_pct: {metrics.average_trade_return_pct:.2f}",
        f"- profit_factor: {metrics.profit_factor:.2f}",
        f"- exposure_pct: {metrics.exposure_pct:.2f}",
        f"- turnover_pct: {metrics.turnover_pct:.2f}",
    ]
    if report.trades:
        lines.append("")
        lines.append("## Trades")
        for trade in report.trades[:20]:
            lines.append(
                f"- {trade.entry_date}->{trade.exit_date} qty={trade.quantity} ret={trade.return_pct:.2f}% reason={trade.exit_reason}"
            )
    return "\n".join(lines)


def trades_to_csv(report: BacktestReport) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "symbol",
            "strategy_id",
            "entry_date",
            "entry_price",
            "exit_date",
            "exit_price",
            "quantity",
            "fees",
            "gross_pnl",
            "net_pnl",
            "return_pct",
            "holding_days",
            "exit_reason",
        ],
    )
    writer.writeheader()
    for trade in report.trades:
        writer.writerow(trade.to_dict())
    return output.getvalue()


def equity_curve_to_csv(report: BacktestReport) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["date", "cash", "position_qty", "close", "position_value", "equity", "drawdown_pct"],
    )
    writer.writeheader()
    for item in report.equity_curve:
        writer.writerow(item.to_dict())
    return output.getvalue()


def _check_intraday_exit(
    symbol: str,
    strategy_id: str,
    row: pd.Series,
    position: _OpenPosition,
    config: BacktestConfig,
    idx: int,
) -> ExecutedTrade | None:
    high = float(row["high"])
    low = float(row["low"])
    exit_reason = None
    exit_ref = None
    if position.stop_loss and low <= position.stop_loss:
        exit_reason = "stop_loss"
        exit_ref = position.stop_loss
    if position.take_profit and high >= position.take_profit:
        if exit_reason is None:
            exit_reason = "take_profit"
            exit_ref = position.take_profit
        elif config.conservative_intraday:
            exit_reason = "ambiguous_stop_first"
            exit_ref = position.stop_loss
        else:
            exit_reason = "ambiguous_take_first"
            exit_ref = position.take_profit
    if exit_ref is None:
        return None
    exit_price = _apply_slippage(float(exit_ref), "sell", config.slippage_bps)
    exit_fees = _commission(exit_price * position.quantity, "sell", config)
    gross_pnl = (exit_price - position.entry_price) * position.quantity
    net_pnl = gross_pnl - position.fees_paid - exit_fees
    return_pct = net_pnl / (position.entry_price * position.quantity) * 100
    return ExecutedTrade(
        symbol=symbol,
        strategy_id=strategy_id,
        entry_date=position.entry_date,
        entry_price=round(position.entry_price, 4),
        exit_date=str(row["date"]),
        exit_price=round(exit_price, 4),
        quantity=position.quantity,
        fees=round(position.fees_paid + exit_fees, 2),
        gross_pnl=round(gross_pnl, 2),
        net_pnl=round(net_pnl, 2),
        return_pct=round(return_pct, 2),
        holding_days=_holding_days(position.entry_date, str(row["date"])),
        exit_reason=exit_reason,
    )


def _position_size(cash: float, price: float, target_position_pct: float, config: BacktestConfig) -> int:
    budget = cash * min(max(target_position_pct, 0.01), config.max_position_pct)
    quantity = int(floor(budget / price / config.lot_size) * config.lot_size)
    return max(quantity, 0)


def _apply_slippage(price: float, side: str, slippage_bps: float) -> float:
    factor = 1 + slippage_bps / 10000 if side == "buy" else 1 - slippage_bps / 10000
    return round(price * factor, 4)


def _commission(notional: float, side: str, config: BacktestConfig) -> float:
    commission = max(notional * config.commission_rate, config.min_commission)
    if side == "sell":
        commission += notional * config.stamp_duty_rate
    return round(commission, 2)


def _holding_days(start: str, end: str) -> int:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    return max(1, (end_ts - start_ts).days)


def _compute_metrics(
    config: BacktestConfig,
    trades: list[ExecutedTrade],
    equity_curve: list[DailyEquityPoint],
    turnover: float,
    exposure_days: int,
) -> BacktestMetrics:
    initial_cash = config.initial_cash
    final_equity = equity_curve[-1].equity if equity_curve else initial_cash
    total_return_pct = (final_equity / initial_cash - 1) * 100 if initial_cash else 0.0
    if len(equity_curve) >= 2:
        start = pd.Timestamp(equity_curve[0].date)
        end = pd.Timestamp(equity_curve[-1].date)
        years = max((end - start).days / 365.25, 1 / 365.25)
        cagr_pct = ((final_equity / initial_cash) ** (1 / years) - 1) * 100 if initial_cash > 0 else 0.0
        equity_series = pd.Series([point.equity for point in equity_curve], index=[point.date for point in equity_curve])
        daily_returns = equity_series.pct_change().dropna()
        annual_volatility_pct = float(daily_returns.std(ddof=0) * sqrt(252) * 100) if not daily_returns.empty else 0.0
        sharpe = 0.0
        if not daily_returns.empty and float(daily_returns.std(ddof=0)) > 0:
            sharpe = float(((daily_returns.mean() - config.risk_free_rate / 252) / daily_returns.std(ddof=0)) * sqrt(252))
        max_drawdown_pct = abs(min((point.drawdown_pct for point in equity_curve), default=0.0))
    else:
        cagr_pct = 0.0
        annual_volatility_pct = 0.0
        sharpe = 0.0
        max_drawdown_pct = 0.0
    trade_count = len(trades)
    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    win_rate_pct = len(wins) / trade_count * 100 if trade_count else 0.0
    average_trade_return_pct = sum(trade.return_pct for trade in trades) / trade_count if trade_count else 0.0
    gross_profit = sum(trade.net_pnl for trade in wins)
    gross_loss = abs(sum(trade.net_pnl for trade in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
    exposure_pct = exposure_days / len(equity_curve) * 100 if equity_curve else 0.0
    turnover_pct = turnover / initial_cash * 100 if initial_cash else 0.0
    return BacktestMetrics(
        initial_cash=round(initial_cash, 2),
        final_equity=round(final_equity, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=round(cagr_pct, 2),
        annual_volatility_pct=round(annual_volatility_pct, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2),
        trade_count=trade_count,
        win_rate_pct=round(win_rate_pct, 2),
        average_trade_return_pct=round(average_trade_return_pct, 2),
        profit_factor=round(profit_factor, 2) if profit_factor != float("inf") else 999.0,
        exposure_pct=round(exposure_pct, 2),
        turnover_pct=round(turnover_pct, 2),
    )
