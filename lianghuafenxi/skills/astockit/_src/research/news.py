"""Query planning and deterministic news-intel helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from research.models import NewsIntelReport, NewsItem, QueryPlan
from research.stock_utils import build_symbol_aliases, get_market_info, is_etf_like


_POSITIVE = ("增长", "中标", "回购", "增持", "突破", "合作", "盈利", "新高", "升级", "利好")
_NEGATIVE = ("减持", "处罚", "诉讼", "亏损", "下修", "爆雷", "调查", "利空", "停牌", "暴跌")
_RISK = ("减持", "处罚", "诉讼", "质押", "下修", "调查", "问询", "违约", "风险", "亏损")
_CATALYST = ("订单", "中标", "回购", "增持", "产品", "突破", "预增", "合作", "景气", "涨价")
_NARRATIVE = ("AI", "出海", "算力", "芯片", "国企改革", "并购", "景气", "机器人", "医药", "新能源")
_AUTHORITATIVE = ("交易所", "公司公告", "证券时报", "上海证券报", "财联社", "Reuters", "Bloomberg")


def build_query_plan(symbol: str, company_name: str = "", max_queries: int = 4) -> list[QueryPlan]:
    market = get_market_info(symbol, company_name)
    normalized = market.normalized_symbol
    company = company_name or normalized
    if market.market == "cn":
        plan = [
            QueryPlan("latest", f"{company} {normalized} 最新消息", "抓取近端催化与公告。"),
            QueryPlan("risk", f"{company} 减持 处罚 诉讼 风险", "筛查实质性风险。"),
            QueryPlan("earnings", f"{company} 业绩预告 财报 增长", "确认盈利与预期变化。"),
            QueryPlan("industry", f"{company} 行业 景气 订单", "观察主叙事与板块联动。"),
        ]
    elif market.market == "hk":
        plan = [
            QueryPlan("latest", f"{company} {normalized} latest news", "抓取港股近端事件。"),
            QueryPlan("risk", f"{company} {normalized} risk warning litigation", "筛查港股风险披露。"),
            QueryPlan("earnings", f"{company} {normalized} earnings guidance", "观察财报与指引。"),
            QueryPlan("industry", f"{company} {normalized} sector trend", "整理行业主线。"),
        ]
    else:
        plan = [
            QueryPlan("latest", f"{company} {normalized} latest news", "抓取最新公司新闻。"),
            QueryPlan("risk", f"{company} {normalized} legal risk downgrade", "筛查评级下调与风险事件。"),
            QueryPlan("earnings", f"{company} {normalized} earnings outlook", "确认业绩节奏。"),
            QueryPlan("industry", f"{company} {normalized} narrative market trend", "追踪美股主题叙事。"),
        ]
    return plan[:max_queries]


def load_news_items(path: str | None = None, headlines: Iterable[str] | None = None) -> list[NewsItem]:
    items: list[NewsItem] = []
    if headlines:
        items.extend(_parse_lines(headlines, source="manual"))
    if not path:
        return items
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if file_path.suffix.lower() in {".json", ".jsonl"}:
        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() == ".jsonl":
            for line in content.splitlines():
                if line.strip():
                    items.append(_from_mapping(json.loads(line)))
        else:
            payload = json.loads(content)
            if isinstance(payload, dict):
                payload = [payload]
            items.extend(_from_mapping(entry) for entry in payload)
        return items
    return items + _parse_lines(file_path.read_text(encoding="utf-8").splitlines(), source=file_path.name)


def _parse_lines(lines: Iterable[str], *, source: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if " | " in line:
            title, summary = line.split(" | ", 1)
        elif "\t" in line:
            title, summary = line.split("\t", 1)
        else:
            title, summary = line, ""
        items.append(NewsItem(title=title.strip("- "), summary=summary.strip(), source=source))
    return items


def _from_mapping(payload: dict) -> NewsItem:
    return NewsItem(
        title=str(payload.get("title", "")).strip(),
        summary=str(payload.get("summary") or payload.get("snippet") or payload.get("content") or "").strip(),
        source=str(payload.get("source", "json")).strip(),
        published_at=str(payload.get("published_at") or payload.get("date") or "").strip(),
        url=str(payload.get("url", "")).strip(),
    )


def build_news_intel_report(
    symbol: str,
    items: list[NewsItem],
    company_name: str = "",
    aliases: list[str] | None = None,
    max_items: int = 8,
) -> NewsIntelReport:
    alias_list = aliases or build_symbol_aliases(symbol, company_name)
    plan = build_query_plan(symbol, company_name)
    ranked = sorted(
        (_score_item(item, alias_list, symbol, company_name) for item in items),
        key=lambda item: item.relevance,
        reverse=True,
    )[:max_items]
    catalysts: list[str] = []
    risks: list[str] = []
    narratives: list[str] = []
    sentiment_total = 0
    for item in ranked:
        text = f"{item.title} {item.summary}"
        if any(keyword in text for keyword in _CATALYST):
            catalysts.append(item.title)
        if any(keyword in text for keyword in _RISK):
            risks.append(item.title)
        for keyword in _NARRATIVE:
            if keyword in text and keyword not in narratives:
                narratives.append(keyword)
        sentiment_total += 1 if item.sentiment == "positive" else -1 if item.sentiment == "negative" else 0
    if sentiment_total > 1:
        bias = "positive"
    elif sentiment_total < -1:
        bias = "negative"
    else:
        bias = "neutral"
    confidence = round(min(0.95, 0.25 + len(ranked) * 0.08), 2)
    return NewsIntelReport(
        symbol=symbol,
        query_plan=plan,
        items=ranked,
        catalysts=catalysts[:5],
        risks=risks[:5],
        narratives=narratives[:6],
        sentiment_bias=bias,
        confidence=confidence,
    )


def _score_item(item: NewsItem, aliases: list[str], symbol: str, company_name: str) -> NewsItem:
    text = f"{item.title} {item.summary}"
    score = 0.0
    if symbol in text:
        score += 4
    if company_name and company_name in text:
        score += 3
    score += sum(1 for alias in aliases if alias and alias in text) * 0.5
    if any(keyword in text for keyword in _CATALYST):
        score += 1.5
    if any(keyword in text for keyword in _RISK):
        score += 1.5
    if any(keyword in item.source for keyword in _AUTHORITATIVE):
        score += 1
    if is_etf_like(symbol, company_name) and "公司治理" in text:
        score -= 1.5

    sentiment = "neutral"
    if any(keyword in text for keyword in _POSITIVE):
        sentiment = "positive"
        score += 0.5
    if any(keyword in text for keyword in _NEGATIVE):
        sentiment = "negative"
        score += 0.5

    published_at = _parse_datetime(item.published_at)
    if published_at:
        age_days = max(0.0, (datetime.now() - published_at).total_seconds() / 86400)
        score += max(0, 2 - age_days / 2)
    item.relevance = round(score, 2)
    item.sentiment = sentiment
    return item


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    candidates = [value, value.replace("/", "-")]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
        except TypeError:
            return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def render_news_intel(report: NewsIntelReport, *, include_items: bool = True) -> str:
    lines = [
        f"# {report.symbol} News Intel",
        "",
        f"- sentiment: {report.sentiment_bias}",
        f"- confidence: {report.confidence:.2f}",
    ]
    if report.catalysts:
        lines.extend(["", "## Catalysts", *[f"- {item}" for item in report.catalysts]])
    if report.risks:
        lines.extend(["", "## Risks", *[f"- {item}" for item in report.risks]])
    if report.narratives:
        lines.extend(["", "## Narratives", *[f"- {item}" for item in report.narratives]])
    if include_items and report.items:
        lines.append("")
        lines.append("## Ranked Items")
        for item in report.items:
            published = f" | {item.published_at}" if item.published_at else ""
            lines.append(
                f"- [{item.source}] score={item.relevance:.2f} sentiment={item.sentiment}{published}: {item.title}"
            )
            if item.summary:
                lines.append(f"  {item.summary}")
    if report.query_plan:
        lines.append("")
        lines.append("## Query Plan")
        for item in report.query_plan:
            lines.append(f"- {item.label}: {item.query}")
            lines.append(f"  {item.rationale}")
    return "\n".join(lines)

