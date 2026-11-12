"""A-share data loading, normalization, indicator, and scoring pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.models import MarketSnapshot


ALIASES = {
    "date": "date",
    "日期": "date",
    "交易日期": "date",
    "open": "open",
    "开盘": "open",
    "high": "high",
    "最高": "high",
    "low": "low",
    "最低": "low",
    "close": "close",
    "收盘": "close",
    "最新价": "close",
    "volume": "volume",
    "成交量": "volume",
    "成交额": "amount",
    "amount": "amount",
    "pct_chg": "pct_change",
    "涨跌幅": "pct_change",
    "turnover": "turnover",
    "turnoverrate": "turnover",
    "换手率": "turnover",
    "name": "name",
    "名称": "name",
}


def board_for_symbol(symbol: str) -> str:
    if symbol.startswith(("300", "301")):
        return "创业板"
    if symbol.startswith("688"):
        return "科创板"
    if symbol.startswith(("8", "43", "83", "87")):
        return "北交所"
    return "主板"


def limit_pct_for_symbol(symbol: str, name: str | None = None) -> float:
    label = (name or "").upper()
    if "ST" in label:
        return 0.05
    if symbol.startswith(("300", "301", "688")):
        return 0.20
    if symbol.startswith(("8", "43", "83", "87")):
        return 0.30
    return 0.10


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for column in frame.columns:
        rename[column] = ALIASES.get(str(column).strip(), str(column).strip().lower())
    return frame.rename(columns=rename)


def _load_from_akshare(symbol: str, start: str | None, end: str | None, adjust: str) -> pd.DataFrame:
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError(
            "AkShare is not installed. Install with `pip install akshare` or use --csv."
        ) from exc

    start_text = (start or "20200101").replace("-", "")
    end_text = (end or pd.Timestamp.today().strftime("%Y%m%d")).replace("-", "")
    frame = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_text,
        end_date=end_text,
        adjust=adjust,
    )
    return _normalize_columns(frame)


def _load_from_path(path: Path) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".json":
            frame = pd.read_json(path)
        else:
            frame = pd.read_csv(path)
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        raise RuntimeError(f"{path} is not a valid market data file.") from exc
    return _normalize_columns(frame)


def load_market_frame(
    symbol: str,
    *,
    csv_path: str | None = None,
    start: str | None = None,
    end: str | None = None,
    source: str = "auto",
    adjust: str = "qfq",
) -> tuple[pd.DataFrame, str]:
    if csv_path:
        frame = _load_from_path(Path(csv_path).expanduser().resolve())
        used_source = "csv"
    else:
        chosen = "akshare" if source in {"auto", "akshare"} else source
        if chosen != "akshare":
            raise RuntimeError(f"Unsupported source: {chosen}")
        frame = _load_from_akshare(symbol, start, end, adjust)
        used_source = "akshare"

    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {', '.join(sorted(missing))}")

    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"])
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "pct_change",
        "turnover",
    ]
    for column in numeric_columns:
        if column in work.columns:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if start:
        work = work[work["date"] >= pd.Timestamp(start)]
    if end:
        work = work[work["date"] <= pd.Timestamp(end)]
    work = work.reset_index(drop=True)
    if work.empty:
        raise RuntimeError(f"No market data available for {symbol}.")
    return work, used_source


def enrich_market_frame(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["prev_close"] = work["close"].shift(1)
    work["pct_change"] = work.get("pct_change")
    if "pct_change" not in work or work["pct_change"].isna().all():
        work["pct_change"] = work["close"].pct_change().mul(100)
    work["ma5"] = work["close"].rolling(5).mean()
    work["ma10"] = work["close"].rolling(10).mean()
    work["ma20"] = work["close"].rolling(20).mean()
    work["ma60"] = work["close"].rolling(60).mean()
    work["ema12"] = work["close"].ewm(span=12, adjust=False).mean()
    work["ema26"] = work["close"].ewm(span=26, adjust=False).mean()
    work["macd"] = work["ema12"] - work["ema26"]
    work["macd_signal"] = work["macd"].ewm(span=9, adjust=False).mean()
    work["macd_hist"] = work["macd"] - work["macd_signal"]

    delta = work["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(14).mean()
    avg_loss = losses.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    work["rsi14"] = 100 - (100 / (1 + rs))

    work["bb_mid"] = work["close"].rolling(20).mean()
    bb_std = work["close"].rolling(20).std()
    work["bb_upper"] = work["bb_mid"] + 2 * bb_std
    work["bb_lower"] = work["bb_mid"] - 2 * bb_std
    work["volume_ma20"] = work["volume"].rolling(20).mean()
    work["volume_ratio"] = work["volume"] / work["volume_ma20"].replace(0, pd.NA)
    work["support20"] = work["low"].rolling(20).min()
    work["resistance20"] = work["high"].rolling(20).max()

    tr = pd.concat(
        [
            work["high"] - work["low"],
            (work["high"] - work["prev_close"]).abs(),
            (work["low"] - work["prev_close"]).abs(),
        ],
        axis=1,
    ).max(axis=1)
    work["atr14"] = tr.rolling(14).mean()
    work["daily_return"] = work["close"].pct_change()
    work["drawdown"] = work["close"] / work["close"].cummax() - 1
    work["breakout_pct"] = work["close"] / work["resistance20"].replace(0, pd.NA) - 1
    return work


def _clip_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def build_snapshot(symbol: str, frame: pd.DataFrame, source: str) -> MarketSnapshot:
    latest = frame.iloc[-1]
    prev_close = (
        float(latest["prev_close"]) if pd.notna(latest["prev_close"]) else float(latest["close"])
    )
    close = float(latest["close"])
    board = board_for_symbol(symbol)
    limit_pct = limit_pct_for_symbol(symbol, latest.get("name"))
    change_pct = float(((close / prev_close) - 1) * 100) if prev_close else 0.0
    amplitude_pct = float((latest["high"] - latest["low"]) / prev_close * 100) if prev_close else 0.0
    volume_ratio = float(latest["volume_ratio"]) if pd.notna(latest["volume_ratio"]) else 1.0
    atr_pct = float(latest["atr14"] / close * 100) if pd.notna(latest["atr14"]) and close else 0.0
    turnover_pct = float(latest["turnover"]) if "turnover" in frame.columns and pd.notna(latest["turnover"]) else None

    score = 50.0
    score += 12 if close >= latest["ma20"] else -12
    score += 12 if pd.notna(latest["ma60"]) and close >= latest["ma60"] else -12
    score += 10 if pd.notna(latest["ma60"]) and latest["ma20"] >= latest["ma60"] else -10
    score += 8 if pd.notna(latest["macd_hist"]) and latest["macd_hist"] >= 0 else -8
    if pd.notna(latest["rsi14"]):
        if 45 <= latest["rsi14"] <= 68:
            score += 8
        elif latest["rsi14"] >= 75:
            score -= 8
        elif latest["rsi14"] <= 28:
            score -= 4
    score += 6 if volume_ratio >= 1.2 else -3 if volume_ratio < 0.8 else 0
    score += 8 if pd.notna(latest["breakout_pct"]) and latest["breakout_pct"] >= -0.01 else 0
    score -= 8 if atr_pct >= 5 else 0
    score -= 6 if latest["drawdown"] <= -0.25 else 0

    trend = "上升" if close >= latest["ma20"] and latest["ma20"] >= latest["ma60"] else "下降" if close < latest["ma20"] and latest["ma20"] < latest["ma60"] else "震荡"
    if trend == "上升" and pd.notna(latest["breakout_pct"]) and latest["breakout_pct"] >= -0.01:
        regime = "breakout_watch"
    elif trend == "上升" and close < latest["ma20"]:
        regime = "trend_pullback"
    elif trend == "下降":
        regime = "defensive"
    else:
        regime = "range"

    risk_flags: list[str] = []
    notes: list[str] = []
    if atr_pct >= 5:
        risk_flags.append("波动偏大")
    if turnover_pct and turnover_pct >= 20:
        risk_flags.append("换手偏热")
    if pd.notna(latest["rsi14"]) and latest["rsi14"] >= 75:
        risk_flags.append("短线过热")
    if change_pct >= limit_pct * 100 * 0.8:
        notes.append("接近涨停带")
    if change_pct <= -limit_pct * 100 * 0.8:
        notes.append("接近跌停带")
    if volume_ratio >= 1.5:
        notes.append("量能放大")
    if pd.notna(latest["breakout_pct"]) and latest["breakout_pct"] > 0:
        notes.append("站上20日阻力")

    return MarketSnapshot(
        symbol=symbol,
        board=board,
        source=source,
        start=frame.iloc[0]["date"].strftime("%Y-%m-%d"),
        end=frame.iloc[-1]["date"].strftime("%Y-%m-%d"),
        rows=len(frame),
        last_close=round(close, 2),
        change_pct=round(change_pct, 2),
        amplitude_pct=round(amplitude_pct, 2),
        volume_ratio=round(volume_ratio, 2),
        atr_pct=round(atr_pct, 2),
        turnover_pct=round(turnover_pct, 2) if turnover_pct is not None else None,
        support=round(float(latest["support20"]) if pd.notna(latest["support20"]) else close, 2),
        resistance=round(float(latest["resistance20"]) if pd.notna(latest["resistance20"]) else close, 2),
        score=_clip_score(score),
        regime=regime,
        trend=trend,
        limit_pct=limit_pct,
        indicators={
            "ma20": round(float(latest["ma20"]), 2) if pd.notna(latest["ma20"]) else None,
            "ma60": round(float(latest["ma60"]), 2) if pd.notna(latest["ma60"]) else None,
            "macd_hist": round(float(latest["macd_hist"]), 4) if pd.notna(latest["macd_hist"]) else None,
            "rsi14": round(float(latest["rsi14"]), 2) if pd.notna(latest["rsi14"]) else None,
            "bb_upper": round(float(latest["bb_upper"]), 2) if pd.notna(latest["bb_upper"]) else None,
            "bb_lower": round(float(latest["bb_lower"]), 2) if pd.notna(latest["bb_lower"]) else None,
        },
        risk_flags=risk_flags,
        notes=notes,
    )
