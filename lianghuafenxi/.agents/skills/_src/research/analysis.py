"""Richer packet assembly for analysis and stock-data skills."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.models import DecisionPacket, MarketSnapshot, StrategyPlan
from research.models import NewsIntelReport, StockResearchPacket
from research.stock_utils import get_market_info


def build_analyst_workflow(depth: str = "standard") -> list[dict[str, str]]:
    workflow = [
        {"stage": "market", "purpose": "trend, price-position, and volume diagnostics"},
        {"stage": "fundamentals", "purpose": "growth, valuation, and flow context"},
        {"stage": "news", "purpose": "catalyst, narrative, and risk filtering"},
    ]
    if depth in {"standard", "deep"}:
        workflow.extend(
            [
                {"stage": "bull_case", "purpose": "distill upside thesis"},
                {"stage": "bear_case", "purpose": "stress downside path"},
            ]
        )
    workflow.append({"stage": "decision", "purpose": "translate evidence into action framing"})
    if depth == "deep":
        workflow.append({"stage": "risk_manager", "purpose": "challenge position sizing and invalidation"})
    return workflow


def build_stock_data_packet(
    snapshot: MarketSnapshot,
    *,
    indicators: dict[str, Any],
    fundamentals: dict[str, Any],
) -> StockResearchPacket:
    market_info = get_market_info(snapshot.symbol).to_dict()
    packet = StockResearchPacket(
        symbol=snapshot.symbol,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        workflow=build_analyst_workflow(depth="compact"),
        core_conclusion={
            "one_sentence": f"{snapshot.symbol} 当前处于 {snapshot.trend}/{snapshot.regime}，适合先做数据化观察。",
            "score": snapshot.score,
        },
        data_perspective={
            "quote": {
                "last_close": snapshot.last_close,
                "change_pct": snapshot.change_pct,
                "amplitude_pct": snapshot.amplitude_pct,
                "volume_ratio": snapshot.volume_ratio,
                "atr_pct": snapshot.atr_pct,
                "turnover_pct": snapshot.turnover_pct,
            },
            "levels": {"support": snapshot.support, "resistance": snapshot.resistance},
            "indicators": indicators,
        },
        intelligence={
            "market": market_info,
            "fundamentals": fundamentals,
            "notes": snapshot.notes,
            "risk_flags": snapshot.risk_flags,
        },
        raw_blocks={"snapshot": snapshot.to_dict()},
    )
    return packet


def build_research_packet(
    snapshot: MarketSnapshot,
    *,
    indicators: dict[str, Any],
    analysis_summary: dict[str, Any],
    decision: DecisionPacket,
    strategy: StrategyPlan,
    fundamentals: dict[str, Any],
    news_report: NewsIntelReport | None = None,
    depth: str = "standard",
    assumptions: list[str] | None = None,
    non_modeled_risks: list[str] | None = None,
    symbol_source: str = "显式输入",
) -> StockResearchPacket:
    market_info = get_market_info(snapshot.symbol).to_dict()
    catalysts = news_report.catalysts if news_report else []
    risks = list(snapshot.risk_flags)
    if news_report:
        risks.extend(item for item in news_report.risks if item not in risks)
    thesis_statement = _thesis_statement(snapshot, analysis_summary, decision)
    key_drivers = _key_drivers(snapshot, analysis_summary, fundamentals, news_report)
    primary_catalyst = _primary_catalyst(news_report)
    variant_view = _variant_view(snapshot, decision)
    disconfirming_evidence = _disconfirming_evidence(snapshot, fundamentals, news_report)
    invalidation_conditions = _invalidation_conditions(snapshot, decision)
    evidence_gaps = _evidence_gaps(fundamentals, news_report)
    position_advice = {
        "no_position": _entry_advice(decision.action),
        "has_position": _holding_advice(decision.action),
    }
    packet = StockResearchPacket(
        symbol=snapshot.symbol,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        workflow=build_analyst_workflow(depth=depth),
        core_conclusion={
            "one_sentence": f"{snapshot.symbol} 评分 {snapshot.score}/100，{analysis_summary['bias']}，当前更适合 {decision.action}。",
            "position_advice": position_advice,
            "confidence": decision.confidence,
            "thesis_statement": thesis_statement,
            "key_drivers": key_drivers,
            "primary_catalyst": primary_catalyst,
            "variant_view": variant_view,
            "scope_note": "thesis_disciplined_memo",
        },
        data_perspective={
            "trend": snapshot.trend,
            "regime": snapshot.regime,
            "levels": {"support": snapshot.support, "resistance": snapshot.resistance},
            "source_window": {
                "source": snapshot.source,
                "start": snapshot.start,
                "end": snapshot.end,
                "rows": snapshot.rows,
                "symbol_source": symbol_source,
            },
            "quote": {
                "last_close": snapshot.last_close,
                "change_pct": snapshot.change_pct,
                "volume_ratio": snapshot.volume_ratio,
                "atr_pct": snapshot.atr_pct,
            },
            "indicators": indicators,
            "analysis_notes": analysis_summary.get("notes", []),
        },
        intelligence={
            "market": market_info,
            "fundamentals": fundamentals,
            "catalysts": catalysts,
            "risk_alerts": risks,
            "narratives": news_report.narratives if news_report else [],
            "sentiment_bias": news_report.sentiment_bias if news_report else "neutral",
            "disconfirming_evidence": disconfirming_evidence,
            "evidence_gaps": evidence_gaps,
        },
        battle_plan={
            "action": decision.action,
            "heuristic_confidence": decision.confidence,
            "sniper_points": {
                "entry_ref": decision.entry_ref,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
            },
            "target_position_pct": decision.target_position_pct,
            "quantity": decision.quantity,
            "style": strategy.style,
            "action_checklist": strategy.checklist,
            "invalidation_conditions": invalidation_conditions,
            "assumptions": assumptions or [],
            "non_modeled_risks": non_modeled_risks or [],
        },
        raw_blocks={
            "snapshot": snapshot.to_dict(),
            "analysis": analysis_summary,
            "decision": decision.to_dict(),
            "strategy": strategy.to_dict(),
            "fundamentals": fundamentals,
            "news": news_report.to_dict() if news_report else None,
        },
    )
    return packet


def render_research_packet(packet: StockResearchPacket) -> str:
    lines = [
        f"# {packet.symbol} Analysis",
        "",
        f"- generated_at: {packet.generated_at}",
        f"- conclusion: {packet.core_conclusion.get('one_sentence', '')}",
    ]
    source_window = packet.data_perspective.get("source_window", {})
    if source_window:
        lines.append(
            f"- data_window: {source_window.get('start')} -> {source_window.get('end')} | "
            f"source={source_window.get('source')} | rows={source_window.get('rows')}"
        )
        lines.append(f"- symbol_source: {source_window.get('symbol_source')}")
    if packet.core_conclusion.get("scope_note"):
        lines.append("- scope: thesis-disciplined memo built from the saved research packet")
    lines.extend(
        [
            "",
            "## Thesis Framework",
            f"- thesis: {packet.core_conclusion.get('thesis_statement', packet.core_conclusion.get('one_sentence', ''))}",
            f"- primary_catalyst: {packet.core_conclusion.get('primary_catalyst', 'n/a')}",
            f"- variant_view: {packet.core_conclusion.get('variant_view', 'n/a')}",
            f"- heuristic_confidence: {packet.core_conclusion.get('confidence', 0.0):.2f}",
        ]
    )
    drivers = packet.core_conclusion.get("key_drivers", [])
    if drivers:
        lines.append("- key_drivers:")
        for item in drivers:
            lines.append(f"  - {item}")
    quote = packet.data_perspective.get("quote", {})
    if quote:
        lines.extend(
            [
                "",
                "## Data Perspective",
                f"- last_close: {quote.get('last_close')}",
                f"- change_pct: {quote.get('change_pct')}",
                f"- volume_ratio: {quote.get('volume_ratio')}",
                f"- atr_pct: {quote.get('atr_pct')}",
            ]
        )
    levels = packet.data_perspective.get("levels", {})
    if levels:
        lines.append(f"- support/resistance: {levels.get('support')} / {levels.get('resistance')}")
    indicators = packet.data_perspective.get("indicators", {})
    if indicators:
        lines.append("- indicators:")
        for key, value in indicators.items():
            lines.append(f"  - {key}: {value}")
    intelligence = packet.intelligence
    if intelligence:
        lines.append("")
        lines.append("## Intelligence")
        for key in ("catalysts", "risk_alerts", "narratives"):
            values = intelligence.get(key) or []
            if values:
                lines.append(f"- {key}:")
                for item in values:
                    lines.append(f"  - {item}")
        for key in ("disconfirming_evidence", "evidence_gaps"):
            values = intelligence.get(key) or []
            if values:
                lines.append(f"- {key}:")
                for item in values:
                    lines.append(f"  - {item}")
    battle_plan = packet.battle_plan
    if battle_plan:
        lines.append("")
        lines.append("## Conditional Action Frame")
        lines.append(f"- action: {battle_plan.get('action')}")
        lines.append(f"- heuristic_confidence: {battle_plan.get('heuristic_confidence')}")
        sniper = battle_plan.get("sniper_points", {})
        lines.append(
            f"- entry/stop/take: {sniper.get('entry_ref')} / {sniper.get('stop_loss')} / {sniper.get('take_profit')}"
        )
        lines.append(f"- quantity: {battle_plan.get('quantity')}")
        lines.append(f"- style: {battle_plan.get('style')}")
        for item in battle_plan.get("action_checklist", []):
            lines.append(f"- checklist: {item}")
        invalidation = battle_plan.get("invalidation_conditions") or []
        if invalidation:
            lines.append("- invalidation_conditions:")
            for item in invalidation:
                lines.append(f"  - {item}")
        assumptions = battle_plan.get("assumptions") or []
        if assumptions:
            lines.append("- assumptions:")
            for item in assumptions:
                lines.append(f"  - {item}")
        non_modeled = battle_plan.get("non_modeled_risks") or []
        if non_modeled:
            lines.append("- non_modeled_risks:")
            for item in non_modeled:
                lines.append(f"  - {item}")
    lines.append("")
    lines.append("## Workflow Blueprint")
    for item in packet.workflow:
        lines.append(f"- {item['stage']}: {item['purpose']}")
    return "\n".join(lines)


def _entry_advice(action: str) -> str:
    mapping = {
        "buy": "允许分批试仓，但仍需确认量价与新闻没有明显背离。",
        "watch": "先观察触发位，不抢先手。",
        "hold": "未持仓不需要硬追，等待更好的回踩。",
        "reduce": "不建议新开仓，优先等待风险释放。",
        "avoid": "当前不做。",
    }
    return mapping.get(action, "保持审慎。")


def _holding_advice(action: str) -> str:
    mapping = {
        "buy": "已有仓位可沿计划加到目标仓位，不要超配。",
        "watch": "已有仓位继续观察，等待确认再动作。",
        "hold": "按原计划持有，但要盯住失效位。",
        "reduce": "已有仓位优先减风险，不和市场硬扛。",
        "avoid": "已有仓位以防守为主。",
    }
    return mapping.get(action, "保持纪律。")


def _thesis_statement(snapshot: MarketSnapshot, analysis_summary: dict[str, Any], decision: DecisionPacket) -> str:
    return (
        f"{snapshot.symbol} 当前呈现 {snapshot.trend}/{snapshot.regime} 结构，"
        f"在 {analysis_summary['bias']} 框架下更适合 {decision.action} 的条件决策。"
    )


def _key_drivers(
    snapshot: MarketSnapshot,
    analysis_summary: dict[str, Any],
    fundamentals: dict[str, Any],
    news_report: NewsIntelReport | None,
) -> list[str]:
    drivers = [
        f"市场状态评分 {snapshot.score}/100，对应 {analysis_summary['bias']} 偏向。",
        f"趋势/状态为 {snapshot.trend}/{snapshot.regime}，支撑 {snapshot.support:.2f}，阻力 {snapshot.resistance:.2f}。",
        f"量比 {snapshot.volume_ratio:.2f}，ATR {snapshot.atr_pct:.2f}% ，反映当前波动与量能结构。",
    ]
    growth = fundamentals.get("fundamentals", {}).get("growth", {})
    if growth:
        revenue_yoy = growth.get("revenue_yoy")
        net_profit_yoy = growth.get("net_profit_yoy")
        if revenue_yoy is not None or net_profit_yoy is not None:
            drivers.append(
                f"基本面上下文显示营收同比 {_fmt_value(revenue_yoy)}、净利同比 {_fmt_value(net_profit_yoy)}。"
            )
    if news_report and news_report.catalysts:
        drivers.append(f"外部事件线索集中在：{news_report.catalysts[0]}")
    return drivers[:5]


def _primary_catalyst(news_report: NewsIntelReport | None) -> str:
    if news_report and news_report.catalysts:
        return news_report.catalysts[0]
    return "No identifiable near-term catalyst from the current saved evidence."


def _variant_view(snapshot: MarketSnapshot, decision: DecisionPacket) -> str:
    if decision.action in {"buy", "hold"}:
        return (
            f"Alternative view: 当前强势可能只是 {snapshot.regime} 阶段的延伸，"
            "若量能不能继续确认或关键支撑失守，乐观框架会迅速削弱。"
        )
    return (
        f"Alternative view: 当前谨慎判断也可能只是 {snapshot.regime} 阶段中的过度防守，"
        "若价格重新站稳阻力并获得量能确认，偏空结论会失效。"
    )


def _disconfirming_evidence(
    snapshot: MarketSnapshot,
    fundamentals: dict[str, Any],
    news_report: NewsIntelReport | None,
) -> list[str]:
    items = []
    for flag in snapshot.risk_flags[:3]:
        items.append(f"技术风险标记：{flag}")
    if snapshot.atr_pct >= 5:
        items.append("波动率偏高，执行与止损路径可能明显劣化。")
    if news_report and news_report.sentiment_bias == "negative":
        items.append("新闻情绪偏负面，与主观乐观解释存在冲突。")
    if fundamentals.get("fundamentals", {}).get("status") != "ok":
        items.append("基本面上下文不是完整或严格点时版本，非价格论据存在信息缺口。")
    return items[:5]


def _invalidation_conditions(snapshot: MarketSnapshot, decision: DecisionPacket) -> list[str]:
    if decision.action in {"buy", "hold"}:
        return [
            f"若价格有效跌破参考止损 {decision.stop_loss:.2f}，原始多头框架失效。",
            f"若价格回到关键支撑 {snapshot.support:.2f} 下方且风险标记继续扩张，需要重估 thesis。",
            "若后续事件与当前叙事相反且量价确认转弱，需停止沿用当前结论。",
        ]
    return [
        f"若价格重新站上关键阻力 {snapshot.resistance:.2f} 并获得量能确认，当前谨慎判断失效。",
        "若风险标记显著收敛且价格结构转强，需要重估原始防守框架。",
        "若后续事件或公告明显改善风险收益比，应重新生成分析而非继续沿用旧结论。",
    ]


def _evidence_gaps(fundamentals: dict[str, Any], news_report: NewsIntelReport | None) -> list[str]:
    items = []
    if fundamentals.get("fundamentals", {}).get("status") != "ok":
        items.append("基本面上下文不是完整、严格点时、可审计的财务仓库结果。")
    if news_report is None:
        items.append("未提供外部新闻证据，催化剂与风险判断主要依赖价格和已有上下文。")
    if not items:
        items.append("当前证据仍未包含组合层约束、基准框架与真实执行容量。")
    return items


def _fmt_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}%"
    return str(value)
