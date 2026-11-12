"""Fail-open fundamental context adapter adapted from AkShare-based probes."""

from __future__ import annotations

import contextlib
import io
import re
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    text = str(value).strip().replace(",", "").replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize_code(raw: Any) -> str:
    text = _safe_str(raw).upper()
    if "." in text:
        text = text.split(".", 1)[0]
    return re.sub(r"^(SH|SZ|BJ)", "", text)


def _pick_by_keywords(row: pd.Series, keywords: list[str]) -> Any:
    for column in row.index:
        label = str(column)
        if any(keyword in label for keyword in keywords):
            value = row.get(column)
            if value is not None and str(value).strip() not in {"", "-", "nan", "None"}:
                return value
    return None


def _extract_latest_row(df: pd.DataFrame, stock_code: str) -> pd.Series | None:
    if df is None or df.empty:
        return None
    code_cols = [
        column
        for column in df.columns
        if any(keyword in str(column) for keyword in ("代码", "股票代码", "证券代码", "ts_code", "symbol"))
    ]
    target = _normalize_code(stock_code)
    if code_cols:
        for column in code_cols:
            try:
                series = df[column].astype(str).map(_normalize_code)
                matched = df[series == target]
                if not matched.empty:
                    return matched.iloc[0]
            except Exception:
                continue
        return None
    return df.iloc[0]


class AkshareFundamentalAdapter:
    """AkShare adapter for fundamentals, capital flow, and dragon-tiger signals."""

    def _call_df_candidates(
        self,
        candidates: list[tuple[str, dict[str, Any]]],
    ) -> tuple[pd.DataFrame | None, str | None, list[str]]:
        errors: list[str] = []
        try:
            import akshare as ak
        except Exception as exc:
            return None, None, [f"import_akshare:{type(exc).__name__}"]

        for func_name, kwargs in candidates:
            function = getattr(ak, func_name, None)
            if function is None:
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    df = function(**kwargs)
                if isinstance(df, pd.Series):
                    df = df.to_frame().T
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df, func_name, errors
            except Exception as exc:
                errors.append(f"{func_name}:{type(exc).__name__}")
        return None, None, errors

    def get_fundamental_bundle(self, stock_code: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "not_supported",
            "growth": {},
            "earnings": {},
            "institution": {},
            "source_chain": [],
            "errors": [],
        }

        fin_df, fin_source, fin_errors = self._call_df_candidates(
            [
                ("stock_financial_abstract", {"symbol": stock_code}),
                ("stock_financial_analysis_indicator", {"symbol": stock_code}),
                ("stock_financial_analysis_indicator", {}),
            ]
        )
        result["errors"].extend(fin_errors)
        if fin_df is not None:
            row = _extract_latest_row(fin_df, stock_code)
            if row is not None:
                result["growth"] = {
                    "revenue_yoy": _safe_float(_pick_by_keywords(row, ["营业收入同比", "营收同比", "收入同比", "同比增长"])),
                    "net_profit_yoy": _safe_float(_pick_by_keywords(row, ["净利润同比", "净利同比", "归母净利润同比"])),
                    "roe": _safe_float(_pick_by_keywords(row, ["净资产收益率", "ROE", "净资产收益"])),
                    "gross_margin": _safe_float(_pick_by_keywords(row, ["毛利率"])),
                }
                result["source_chain"].append(f"growth:{fin_source}")

        forecast_df, forecast_source, forecast_errors = self._call_df_candidates(
            [
                ("stock_yjyg_em", {"symbol": stock_code}),
                ("stock_yjyg_em", {}),
                ("stock_yjbb_em", {"symbol": stock_code}),
                ("stock_yjbb_em", {}),
            ]
        )
        result["errors"].extend(forecast_errors)
        if forecast_df is not None:
            row = _extract_latest_row(forecast_df, stock_code)
            if row is not None:
                result["earnings"]["forecast_summary"] = _safe_str(
                    _pick_by_keywords(row, ["预告", "业绩变动", "内容", "摘要", "公告"])
                )[:200]
                result["source_chain"].append(f"earnings_forecast:{forecast_source}")

        quick_df, quick_source, quick_errors = self._call_df_candidates(
            [("stock_yjkb_em", {"symbol": stock_code}), ("stock_yjkb_em", {})]
        )
        result["errors"].extend(quick_errors)
        if quick_df is not None:
            row = _extract_latest_row(quick_df, stock_code)
            if row is not None:
                result["earnings"]["quick_report_summary"] = _safe_str(
                    _pick_by_keywords(row, ["快报", "摘要", "公告", "说明"])
                )[:200]
                result["source_chain"].append(f"earnings_quick:{quick_source}")

        inst_df, inst_source, inst_errors = self._call_df_candidates(
            [("stock_institute_hold", {}), ("stock_institute_recommend", {})]
        )
        result["errors"].extend(inst_errors)
        if inst_df is not None:
            row = _extract_latest_row(inst_df, stock_code)
            if row is not None:
                result["institution"]["institution_holding_change"] = _safe_float(
                    _pick_by_keywords(row, ["增减", "变化", "变动", "持股变化"])
                )
                result["source_chain"].append(f"institution:{inst_source}")

        top10_df, top10_source, top10_errors = self._call_df_candidates(
            [
                ("stock_gdfx_top_10_em", {"symbol": stock_code}),
                ("stock_gdfx_top_10_em", {}),
                ("stock_zh_a_gdhs_detail_em", {"symbol": stock_code}),
                ("stock_zh_a_gdhs_detail_em", {}),
            ]
        )
        result["errors"].extend(top10_errors)
        if top10_df is not None:
            row = _extract_latest_row(top10_df, stock_code)
            if row is not None:
                result["institution"]["top10_holder_change"] = _safe_float(
                    _pick_by_keywords(row, ["增减", "变化", "持股变化", "变动"])
                )
                result["source_chain"].append(f"top10:{top10_source}")

        result["status"] = "partial" if any(result[key] for key in ("growth", "earnings", "institution")) else "not_supported"
        return result

    def get_capital_flow(self, stock_code: str, top_n: int = 5) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "not_supported",
            "stock_flow": {},
            "sector_rankings": {"top": [], "bottom": []},
            "source_chain": [],
            "errors": [],
        }

        stock_df, stock_source, stock_errors = self._call_df_candidates(
            [
                ("stock_individual_fund_flow", {"stock": stock_code}),
                ("stock_individual_fund_flow", {"symbol": stock_code}),
                ("stock_individual_fund_flow", {}),
                ("stock_main_fund_flow", {"symbol": stock_code}),
                ("stock_main_fund_flow", {}),
            ]
        )
        result["errors"].extend(stock_errors)
        if stock_df is not None:
            row = _extract_latest_row(stock_df, stock_code)
            if row is not None:
                result["stock_flow"] = {
                    "main_net_inflow": _safe_float(_pick_by_keywords(row, ["主力净流入", "净流入", "净额"])),
                    "inflow_5d": _safe_float(_pick_by_keywords(row, ["5日", "五日"])),
                    "inflow_10d": _safe_float(_pick_by_keywords(row, ["10日", "十日"])),
                }
                result["source_chain"].append(f"capital_stock:{stock_source}")

        sector_df, sector_source, sector_errors = self._call_df_candidates(
            [("stock_sector_fund_flow_rank", {}), ("stock_sector_fund_flow_summary", {})]
        )
        result["errors"].extend(sector_errors)
        if sector_df is not None:
            name_col = next(
                (column for column in sector_df.columns if any(keyword in str(column) for keyword in ("板块", "行业", "名称", "name"))),
                None,
            )
            flow_col = next(
                (column for column in sector_df.columns if any(keyword in str(column) for keyword in ("净流入", "主力", "flow", "净额"))),
                None,
            )
            if name_col and flow_col:
                work_df = sector_df[[name_col, flow_col]].copy()
                work_df[flow_col] = pd.to_numeric(work_df[flow_col], errors="coerce")
                work_df = work_df.dropna(subset=[flow_col])
                top_df = work_df.nlargest(top_n, flow_col)
                bottom_df = work_df.nsmallest(top_n, flow_col)
                result["sector_rankings"] = {
                    "top": [{"name": _safe_str(row[name_col]), "net_inflow": float(row[flow_col])} for _, row in top_df.iterrows()],
                    "bottom": [{"name": _safe_str(row[name_col]), "net_inflow": float(row[flow_col])} for _, row in bottom_df.iterrows()],
                }
                result["source_chain"].append(f"capital_sector:{sector_source}")

        has_content = bool(result["stock_flow"] or result["sector_rankings"]["top"] or result["sector_rankings"]["bottom"])
        result["status"] = "partial" if has_content else "not_supported"
        return result

    def get_dragon_tiger_flag(self, stock_code: str, lookback_days: int = 20) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "not_supported",
            "is_on_list": False,
            "recent_count": 0,
            "latest_date": None,
            "source_chain": [],
            "errors": [],
        }
        df, source, errors = self._call_df_candidates(
            [("stock_lhb_stock_statistic_em", {}), ("stock_lhb_detail_em", {}), ("stock_lhb_jgmmtj_em", {})]
        )
        result["errors"].extend(errors)
        if df is None:
            return result

        code_cols = [column for column in df.columns if any(keyword in str(column) for keyword in ("代码", "股票代码", "证券代码"))]
        target = _normalize_code(stock_code)
        matched = pd.DataFrame()
        for column in code_cols:
            try:
                series = df[column].astype(str).map(_normalize_code)
                current = df[series == target]
                if not current.empty:
                    matched = current
                    break
            except Exception:
                continue
        if matched.empty:
            result["source_chain"].append(f"dragon_tiger:{source}")
            result["status"] = "ok" if code_cols else "partial"
            return result

        date_col = next(
            (column for column in matched.columns if any(keyword in str(column) for keyword in ("日期", "上榜", "交易日", "time"))),
            None,
        )
        parsed_dates: list[datetime] = []
        if date_col is not None:
            for value in matched[date_col].astype(str).tolist():
                try:
                    parsed_dates.append(pd.to_datetime(value).to_pydatetime())
                except Exception:
                    continue
        now = datetime.now()
        start = now - timedelta(days=max(1, lookback_days))
        recent_dates = [item for item in parsed_dates if start <= item <= now]
        result["is_on_list"] = bool(recent_dates)
        result["recent_count"] = len(recent_dates) if recent_dates else int(len(matched))
        result["latest_date"] = max(recent_dates).date().isoformat() if recent_dates else (
            max(parsed_dates).date().isoformat() if parsed_dates else None
        )
        result["status"] = "ok"
        result["source_chain"].append(f"dragon_tiger:{source}")
        return result


def build_fundamental_context(stock_code: str) -> dict[str, Any]:
    adapter = AkshareFundamentalAdapter()
    return {
        "symbol": stock_code,
        "fundamentals": adapter.get_fundamental_bundle(stock_code),
        "capital_flow": adapter.get_capital_flow(stock_code),
        "dragon_tiger": adapter.get_dragon_tiger_flag(stock_code),
    }
