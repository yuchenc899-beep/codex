"""Run bounded, read-only API probes and preserve public response evidence."""
import concurrent.futures
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CASES = [
    ("a_quotes", "stock_zh_a_spot_em", {}),
    ("hk_quotes", "stock_hk_spot_em", {}),
    ("etf_quotes", "fund_etf_spot_em", {}),
    ("cn_indices", "stock_zh_index_spot_em", {"symbol": "沪深重要指数"}),
    ("global_indices", "index_global_spot_em", {}),
    ("a_history", "stock_zh_a_hist", {"symbol": "600905", "start_date": "20231111", "end_date": "20261111", "adjust": "qfq"}),
    ("hk_history", "stock_hk_hist", {"symbol": "00762", "start_date": "20231111", "end_date": "20261111", "adjust": "qfq"}),
    ("etf_history", "fund_etf_hist_em", {"symbol": "588080", "start_date": "20231111", "end_date": "20261111", "adjust": "qfq"}),
    ("a_intraday", "stock_zh_a_hist_min_em", {"symbol": "600905", "period": "1"}),
    ("hk_intraday", "stock_hk_hist_min_em", {"symbol": "00762", "period": "1"}),
    ("a_financials", "stock_financial_report_sina", {"stock": "sh600905", "symbol": "利润表"}),
    ("hk_financials", "stock_financial_hk_report_em", {"stock": "00762", "symbol": "利润表", "indicator": "年度"}),
    ("a_profile", "stock_individual_info_em", {"symbol": "600905"}),
    ("hk_profile", "stock_hk_company_profile_em", {"symbol": "00762"}),
    ("dividends", "stock_fhps_detail_em", {"symbol": "600905"}),
    ("announcements", "stock_zh_a_disclosure_report_cninfo", {"symbol": "600905", "market": "沪深京", "start_date": "20261001", "end_date": "20261111"}),
    ("fx", "forex_spot_em", {}),
    ("a_balance", "stock_financial_report_sina", {"stock": "sh600905", "symbol": "资产负债表"}),
    ("a_cashflow", "stock_financial_report_sina", {"stock": "sh600905", "symbol": "现金流量表"}),
    ("hk_balance", "stock_financial_hk_report_em", {"stock": "00762", "symbol": "资产负债表", "indicator": "年度"}),
    ("hk_cashflow", "stock_financial_hk_report_em", {"stock": "00762", "symbol": "现金流量表", "indicator": "年度"}),
    ("etf_intraday", "fund_etf_hist_min_em", {"symbol": "588080", "period": "1"}),
    ("a_history_raw", "stock_zh_a_hist", {"symbol": "600905", "start_date": "20231111", "end_date": "20261111", "adjust": ""}),
    ("public_index_quotes", "tencent_indices", {}),
]


def probe(case):
    import akshare
    import requests
    name, method, params = case
    started = time.monotonic()
    if method == "tencent_indices":
        symbols = ["sh000001", "sz399001", "sz399006", "sh000300", "hkHSI",
                   "hkHSTECH", "usINX", "usIXIC", "usDJI"]
        response = requests.get("https://qt.gtimg.cn/q=" + ",".join(symbols), timeout=12)
        response.raise_for_status()
        response.encoding = "gbk"
        return {"status": "returned", "http_status": response.status_code,
                "requested_public_indices": symbols, "raw_response": response.text,
                "elapsed_s": round(time.monotonic()-started, 3)}
    function = getattr(akshare, method)
    frame = function(**params)
    evidence = {}
    if method == "stock_financial_report_sina" and "报告日" in frame:
        annual = frame[frame["报告日"].astype(str).str.endswith("1231")]
        evidence["annual_dates"] = annual["报告日"].astype(str).tolist()
        fields = [f for f in ("报告日", "归属于母公司所有者的净利润", "营业收入", "公告日期", "币种") if f in annual]
        evidence["recent_five_annual"] = json.loads(annual[fields].head(5).to_json(orient="records",force_ascii=False))
    if method == "stock_financial_hk_report_em":
        evidence["report_dates"] = sorted(frame["REPORT_DATE"].unique().tolist(),reverse=True)
        evidence["profit_fields"] = sorted(frame.loc[frame["STD_ITEM_NAME"].str.contains("股东|母公司|盈利|溢利|利润",regex=True),"STD_ITEM_NAME"].unique().tolist())
    if method in ("index_global_spot_em", "stock_zh_index_spot_em"):
        evidence["identities"] = json.loads(frame.to_json(orient="records",force_ascii=False))
    if method == "forex_spot_em":
        evidence["hkd_pairs"] = json.loads(frame.loc[frame["代码"].str.contains("HKD")].to_json(orient="records",force_ascii=False))
    return {"status": "returned" if len(frame) else "empty", "rows": len(frame), "evidence": evidence,
            "columns": list(map(str, frame.columns)),
            "sample": json.loads(frame.head(2).to_json(orient="records", date_format="iso", force_ascii=False)),
            "tail": json.loads(frame.tail(2).to_json(orient="records", date_format="iso", force_ascii=False)),
            "signature": str(inspect.signature(function)),
            "elapsed_s": round(time.monotonic()-started, 3)}


def bounded(case):
    started = time.monotonic()
    try:
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", case[0]],
                             capture_output=True, encoding="utf-8", errors="replace", timeout=35)
        lines = [line for line in run.stdout.splitlines() if line.startswith("PROBE_JSON=")]
        result = json.loads(lines[-1].removeprefix("PROBE_JSON=")) if lines else {
            "status": "process_error", "error": (run.stderr or run.stdout)[-1200:]}
    except subprocess.TimeoutExpired:
        result = {"status": "timeout", "error": "35 second process limit"}
    result.update({"name": case[0], "method": case[1], "params": case[2],
                   "total_elapsed_s": round(time.monotonic()-started, 3)})
    return result


if __name__ == "__main__":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if "--child" in sys.argv:
        case = next(case for case in CASES if case[0] == sys.argv[-1])
        try:
            result = probe(case)
        except Exception as error:
            result = {"status": "error", "error": f"{type(error).__name__}: {error}"[:1200]}
        print("PROBE_JSON=" + json.dumps(result, ensure_ascii=False))
    else:
        selected = [c for c in CASES if "--only" not in sys.argv or c[0] in sys.argv[sys.argv.index("--only")+1].split(",")]
        filename = "api-probe-2026-11-11.json"
        if "--only" in sys.argv:
            filename = "api-probe-public-indices-2026-11-11.json" if len(selected) == 1 and selected[0][0] == "public_index_quotes" else "api-probe-detail-2026-11-11.json"
        output = ROOT / "docs" / "validation" / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(bounded, selected):
                results.append(result)
                print(result["name"], result["status"], result.get("rows"), flush=True)
                output.write_text(json.dumps({"tested_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                    "environment": "Windows local outbound network, configured proxy", "results": results},
                    ensure_ascii=False, indent=2), encoding="utf-8")
