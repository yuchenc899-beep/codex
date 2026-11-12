"""Ticker parsing and market normalization helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


_A_SHARE_RE = re.compile(r"^(?:SH|SZ)?(\d{6})$")
_HK_RE = re.compile(r"^(?:HK|0)?(\d{4,5})(?:\.HK)?$")
_US_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


@dataclass(slots=True)
class MarketInfo:
    market: str
    market_name: str
    currency: str
    currency_symbol: str
    lot_size: int
    t_plus_one: bool
    normalized_symbol: str
    aliases: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper().replace(" ", "")
    a_match = _A_SHARE_RE.match(value)
    if a_match:
        return a_match.group(1)
    hk_match = _HK_RE.match(value)
    if hk_match and not value.isalpha():
        digits = hk_match.group(1)
        return f"{digits.zfill(4)}.HK"
    return value


def identify_stock_market(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if normalized.endswith(".HK"):
        return "hk"
    if normalized.isdigit() and len(normalized) == 6:
        return "cn"
    if _US_RE.match(normalized):
        return "us"
    return "unknown"


def build_symbol_aliases(symbol: str, company_name: str = "") -> list[str]:
    normalized = normalize_symbol(symbol)
    aliases = {symbol.strip(), normalized}
    if normalized.endswith(".HK"):
        aliases.add(normalized.replace(".HK", ""))
    if normalized.isdigit():
        aliases.add(f"SH{normalized}")
        aliases.add(f"SZ{normalized}")
    if company_name:
        aliases.add(company_name.strip())
        aliases.add(company_name.replace("股份有限公司", "").strip())
    return sorted(item for item in aliases if item)


def get_market_info(symbol: str, company_name: str = "") -> MarketInfo:
    normalized = normalize_symbol(symbol)
    market = identify_stock_market(normalized)
    aliases = build_symbol_aliases(normalized, company_name)
    if market == "cn":
        return MarketInfo(
            market="cn",
            market_name="A-share",
            currency="CNY",
            currency_symbol="RMB",
            lot_size=100,
            t_plus_one=True,
            normalized_symbol=normalized,
            aliases=aliases,
        )
    if market == "hk":
        return MarketInfo(
            market="hk",
            market_name="Hong Kong",
            currency="HKD",
            currency_symbol="HK$",
            lot_size=100,
            t_plus_one=False,
            normalized_symbol=normalized,
            aliases=aliases,
        )
    if market == "us":
        return MarketInfo(
            market="us",
            market_name="US",
            currency="USD",
            currency_symbol="$",
            lot_size=1,
            t_plus_one=False,
            normalized_symbol=normalized,
            aliases=aliases,
        )
    return MarketInfo(
        market="unknown",
        market_name="Unknown",
        currency="",
        currency_symbol="",
        lot_size=1,
        t_plus_one=False,
        normalized_symbol=normalized,
        aliases=aliases,
    )


def is_etf_like(symbol: str, company_name: str = "") -> bool:
    normalized = normalize_symbol(symbol)
    text = f"{normalized} {company_name}".upper()
    return any(
        token in text
        for token in ("ETF", "INDEX", "指数", "LOF", "联接", "300ETF", "500ETF", "纳指")
    )

