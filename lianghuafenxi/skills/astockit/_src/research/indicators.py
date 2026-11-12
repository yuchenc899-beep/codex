"""Deterministic indicator helpers adapted from multi-agent trading references."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    name: str
    params: dict[str, Any] | None = None


def _require_cols(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def add_all_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    _require_cols(frame, ("close", "high", "low", "volume"))
    work = frame.copy()
    close = work["close"]
    high = work["high"]
    low = work["low"]

    for period in (5, 10, 20, 60):
        work[f"ma{period}"] = close.rolling(period, min_periods=1).mean()
        work[f"ema{period}"] = close.ewm(span=period, adjust=False).mean()

    work["dif"] = work["ema12"] - work["ema26"]
    work["dea"] = work["dif"].ewm(span=9, adjust=False).mean()
    work["macd_hist"] = work["dif"] - work["dea"]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    for period in (6, 12, 14, 24):
        avg_gain = gain.ewm(alpha=1 / float(period), adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / float(period), adjust=False).mean()
        rs = avg_gain / avg_loss.where(avg_loss != 0, 1e-12)
        rsi = 100 - (100 / (1 + rs))
        work[f"rsi{period}"] = rsi.clip(lower=0, upper=100)

    mid = close.rolling(20, min_periods=1).mean()
    std = close.rolling(20, min_periods=1).std()
    work["boll_mid"] = mid
    work["boll_upper"] = mid + std * 2
    work["boll_lower"] = mid - std * 2

    prev_close = close.shift(1)
    true_range = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    work["atr14"] = true_range.rolling(14, min_periods=1).mean()

    low_n = low.rolling(9, min_periods=1).min()
    high_n = high.rolling(9, min_periods=1).max()
    rsv = ((close - low_n) / (high_n - low_n).replace(0, pd.NA) * 100).fillna(50)
    work["kdj_k"] = rsv.ewm(alpha=1 / 3, adjust=False).mean()
    work["kdj_d"] = work["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
    work["kdj_j"] = work["kdj_k"] * 3 - work["kdj_d"] * 2

    work["volume_ma5"] = work["volume"].rolling(5, min_periods=1).mean()
    work["volume_ma20"] = work["volume"].rolling(20, min_periods=1).mean()
    work["volume_ratio_5d"] = work["volume"] / work["volume_ma5"].replace(0, pd.NA)
    return work


def compute_many(frame: pd.DataFrame, specs: list[IndicatorSpec]) -> pd.DataFrame:
    if not specs:
        return frame.copy()
    work = add_all_indicators(frame)
    wanted = set()
    for spec in specs:
        params = spec.params or {}
        name = spec.name.lower()
        if name in {"ma", "ema", "rsi", "atr"}:
            period = int(params.get("n", params.get("period", 14)))
            wanted.add(f"{name}{period}")
        elif name == "macd":
            wanted.update({"dif", "dea", "macd_hist"})
        elif name == "boll":
            wanted.update({"boll_mid", "boll_upper", "boll_lower"})
        elif name == "kdj":
            wanted.update({"kdj_k", "kdj_d", "kdj_j"})
    base = [column for column in ("date", "open", "high", "low", "close", "volume") if column in work.columns]
    return work[base + sorted(wanted)]


def last_values(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> dict[str, float | None]:
    work = add_all_indicators(frame)
    latest = work.iloc[-1]
    selected = list(columns) if columns is not None else [
        "ma5",
        "ma10",
        "ma20",
        "ma60",
        "dif",
        "dea",
        "macd_hist",
        "rsi6",
        "rsi12",
        "rsi14",
        "rsi24",
        "boll_mid",
        "boll_upper",
        "boll_lower",
        "atr14",
        "kdj_k",
        "kdj_d",
        "kdj_j",
        "volume_ratio_5d",
    ]
    result: dict[str, float | None] = {}
    for column in selected:
        value = latest.get(column)
        result[column] = None if pd.isna(value) else round(float(value), 4)
    return result
