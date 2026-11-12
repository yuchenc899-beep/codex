"""Watchlist parsing helpers adapted from multi-source import workflows."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pandas as pd


CODE_ALIASES = {"code", "股票代码", "代码", "stock_code", "symbol"}
NAME_ALIASES = {"name", "股票名称", "名称", "stock_name"}


def is_symbol_like(value: str) -> bool:
    text = str(value or "").strip().upper()
    if not text:
        return False
    return bool(
        re.fullmatch(r"\d{6}", text)
        or re.fullmatch(r"(SH|SZ|BJ)\d{6}", text)
        or re.fullmatch(r"(HK)?\d{5}", text)
        or re.fullmatch(r"[A-Z]{1,5}(\.[A-Z]{1,4})?", text)
    )


def normalize_symbol(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if re.fullmatch(r"(SH|SZ|BJ)\d{6}", text):
        return text[2:]
    if re.fullmatch(r"\d{6}", text):
        return text
    if re.fullmatch(r"HK\d{5}", text):
        return text
    if re.fullmatch(r"\d{5}", text):
        return f"HK{text}"
    if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z]{1,4})?", text):
        return text
    return None


def _detect_column_indices(df: pd.DataFrame) -> tuple[int | None, int | None]:
    code_idx, name_idx = None, None
    for index, column in enumerate(df.columns):
        lowered = str(column).strip().lower()
        if lowered in {item.lower() for item in CODE_ALIASES}:
            code_idx = index
        if lowered in {item.lower() for item in NAME_ALIASES}:
            name_idx = index
    return code_idx, name_idx


def _records_from_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    code_idx, name_idx = _detect_column_indices(df)
    has_header = code_idx is not None or name_idx is not None
    records: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        raw_code = None
        raw_name = None
        if has_header:
            if code_idx is not None and code_idx < len(row):
                raw_code = row.iloc[code_idx]
            if name_idx is not None and name_idx < len(row):
                raw_name = row.iloc[name_idx]
        else:
            if len(row) >= 1:
                raw_code = row.iloc[0]
            if len(row) >= 2:
                raw_name = row.iloc[1]

        code_text = str(raw_code).strip() if raw_code is not None and str(raw_code).strip() else None
        name_text = str(raw_name).strip() if raw_name is not None and str(raw_name).strip() else None
        if not code_text and not name_text:
            continue

        symbol = normalize_symbol(code_text) if code_text else None
        if not symbol and name_text and is_symbol_like(name_text):
            symbol = normalize_symbol(name_text)
            name_text = None

        records.append(
            {
                "symbol": symbol,
                "name": name_text,
                "confidence": "high" if symbol else "low",
                "raw": {"code": code_text, "name": name_text},
            }
        )
    return records


def parse_watchlist_text(text: str) -> list[dict[str, Any]]:
    cleaned = text.strip()
    if not cleaned:
        return []

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if all(not re.search(r"[\t,;]", line) for line in lines):
        rows = [[line] for line in lines]
        return _records_from_dataframe(pd.DataFrame(rows))

    try:
        df = pd.read_csv(io.StringIO(cleaned), sep=None, engine="python", header=None, dtype=str).fillna("")
    except pd.errors.ParserError:
        rows = [re.split(r"[\t,; ]+", line) for line in lines]
        df = pd.DataFrame(rows).fillna("")

    first_row = [str(value).strip().lower() for value in df.iloc[0].tolist()]
    if any(item in {alias.lower() for alias in CODE_ALIASES | NAME_ALIASES} for item in first_row):
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    return _records_from_dataframe(df)


def parse_watchlist_file(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path).expanduser().resolve()
    if target.suffix.lower() == ".xlsx":
        df = pd.read_excel(target, sheet_name=0, header=None, dtype=str).fillna("")
        first_row = [str(value).strip().lower() for value in df.iloc[0].tolist()]
        if any(item in {alias.lower() for alias in CODE_ALIASES | NAME_ALIASES} for item in first_row):
            df.columns = df.iloc[0]
            df = df.iloc[1:].reset_index(drop=True)
        return _records_from_dataframe(df)
    return parse_watchlist_text(target.read_text(encoding="utf-8"))


def render_watchlist_summary(records: list[dict[str, Any]]) -> str:
    resolved = [item for item in records if item["symbol"]]
    unresolved = [item for item in records if not item["symbol"]]
    lines = [
        "导入结果",
        f"- 总条目: {len(records)}",
        f"- 已识别代码: {len(resolved)}",
        f"- 待人工确认: {len(unresolved)}",
    ]
    if resolved:
        lines.append("- 已识别:")
        lines.extend(
            [f"  - {item['symbol']}" + (f" | {item['name']}" if item['name'] else "") for item in resolved[:20]]
        )
    if unresolved:
        lines.append("- 待确认:")
        lines.extend(
            [f"  - {item['raw']['code'] or item['raw']['name']}" for item in unresolved[:10]]
        )
    return "\n".join(lines)
