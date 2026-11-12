"""Lightweight paper-trading bookkeeping helpers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from research.models import PaperBook, PaperLot, PaperPosition, PaperTrade
from research.stock_utils import get_market_info


def load_book(path: str | Path, *, account: str = "default", initial_cash: float = 100000.0) -> PaperBook:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        return PaperBook(account=account, cash=initial_cash)
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    positions = {
        symbol: PaperPosition(
            symbol=item["symbol"],
            market=item["market"],
            quantity=item["quantity"],
            avg_cost=item["avg_cost"],
            last_price=item.get("last_price"),
            lots=[PaperLot(**lot) for lot in item.get("lots", [])],
        )
        for symbol, item in payload.get("positions", {}).items()
    }
    trades = [PaperTrade(**trade) for trade in payload.get("trades", [])]
    return PaperBook(account=payload.get("account", account), cash=payload.get("cash", initial_cash), positions=positions, trades=trades)


def save_book(path: str | Path, book: PaperBook) -> Path:
    file_path = Path(path).expanduser().resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(book.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return file_path


def apply_order(
    book: PaperBook,
    *,
    symbol: str,
    side: str,
    quantity: int,
    price: float,
    trade_date: str,
    note: str = "",
) -> PaperTrade:
    market = get_market_info(symbol)
    normalized = market.normalized_symbol
    quantity = _normalize_quantity(quantity, market.lot_size)
    if quantity <= 0:
        raise ValueError("quantity must be positive after lot normalization")
    notional = round(quantity * price, 2)
    fees = round(_commission(market.market, notional, side), 2)
    position = book.positions.get(normalized) or PaperPosition(symbol=normalized, market=market.market)
    if side == "buy":
        total_cost = notional + fees
        if total_cost > book.cash:
            raise ValueError("insufficient cash for paper order")
        new_quantity = position.quantity + quantity
        weighted_cost = ((position.avg_cost * position.quantity) + notional + fees) / new_quantity
        position.quantity = new_quantity
        position.avg_cost = round(weighted_cost, 4)
        position.last_price = price
        position.lots.append(PaperLot(quantity=quantity, trade_date=trade_date))
        book.cash = round(book.cash - total_cost, 2)
    elif side == "sell":
        available = available_quantity(position, trade_date, market.t_plus_one)
        if quantity > available:
            raise ValueError(f"sell quantity exceeds available quantity: {available}")
        proceeds = notional - fees
        position.quantity -= quantity
        position.last_price = price
        _consume_lots(position, quantity)
        if position.quantity == 0:
            position.avg_cost = 0.0
        book.cash = round(book.cash + proceeds, 2)
    else:
        raise ValueError(f"unsupported side: {side}")
    book.positions[normalized] = position
    trade = PaperTrade(
        trade_id=uuid4().hex[:12],
        symbol=normalized,
        side=side,
        quantity=quantity,
        price=round(price, 4),
        fees=fees,
        notional=notional,
        trade_date=trade_date,
        note=note,
    )
    book.trades.append(trade)
    return trade


def available_quantity(position: PaperPosition, trade_date: str, t_plus_one: bool) -> int:
    if not t_plus_one:
        return position.quantity
    available = 0
    for lot in position.lots:
        if lot.trade_date < trade_date:
            available += lot.quantity
    return available


def render_book(book: PaperBook) -> str:
    lines = [
        f"# Paper Account {book.account}",
        "",
        f"- cash: {book.cash:.2f}",
        f"- positions: {len([item for item in book.positions.values() if item.quantity > 0])}",
        f"- trades: {len(book.trades)}",
    ]
    for position in book.positions.values():
        if position.quantity <= 0:
            continue
        lines.append(
            f"- {position.symbol}: qty={position.quantity} avg_cost={position.avg_cost:.4f} last_price={position.last_price}"
        )
    return "\n".join(lines)


def render_trade_result(book: PaperBook, trade: PaperTrade) -> str:
    lines = [
        f"# Paper Trade {trade.trade_id}",
        "",
        f"- symbol: {trade.symbol}",
        f"- side: {trade.side}",
        f"- quantity: {trade.quantity}",
        f"- price: {trade.price}",
        f"- fees: {trade.fees}",
        f"- notional: {trade.notional}",
        f"- trade_date: {trade.trade_date}",
        f"- cash_after: {book.cash:.2f}",
        "",
        render_book(book),
    ]
    return "\n".join(lines)


def _normalize_quantity(quantity: int, lot_size: int) -> int:
    if lot_size <= 1:
        return quantity
    return quantity // lot_size * lot_size


def _commission(market: str, notional: float, side: str) -> float:
    if market == "cn":
        fee = max(5.0, notional * 0.0003)
        if side == "sell":
            fee += notional * 0.001
        return fee
    if market == "hk":
        return max(3.0, notional * 0.0013)
    return 0.0


def _consume_lots(position: PaperPosition, quantity: int) -> None:
    remaining = quantity
    new_lots: list[PaperLot] = []
    for lot in position.lots:
        if remaining <= 0:
            new_lots.append(lot)
            continue
        if lot.quantity <= remaining:
            remaining -= lot.quantity
            continue
        new_lots.append(PaperLot(quantity=lot.quantity - remaining, trade_date=lot.trade_date))
        remaining = 0
    position.lots = new_lots

