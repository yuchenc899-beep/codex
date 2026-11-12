"""Stable runtime layer used by markdown-defined A-Stockit skills."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

def bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


from backtest.engine import equity_curve_to_csv, render_backtest_report, run_strategy_backtest, trades_to_csv
from backtest.models import BacktestConfig
from core.config import load_config, runtime_root
from core.models import DecisionPacket, MarketSnapshot, StrategyPlan
from core.registry import (
    load_bundle_metadata,
    load_skill_registry,
    load_runtime_registry,
)
from core.storage import Storage
from integrations.notifications import NotificationManager
from market.capabilities import build_registry
from market.dashboards import build_decision_dashboard, render_decision_dashboard
from market.data import build_snapshot, enrich_market_frame, load_market_frame
from market.fundamentals import build_fundamental_context
from market.recap import get_market_strategy_blueprint
from market.watchlists import (
    parse_watchlist_file,
    parse_watchlist_text,
    render_watchlist_summary,
)
from research.analysis import (
    build_research_packet,
    build_stock_data_packet,
    render_research_packet,
)
from research.evaluation import evaluate_saved_run, load_state_payload, render_backtest_evaluation
from research.indicators import last_values
from research.model_advisor import recommend_models, render_model_recommendation
from research.news import build_news_intel_report, load_news_items, render_news_intel
from research.paper import apply_order, load_book, render_book, render_trade_result, save_book
from strategies.registry import get_strategy_preset, load_strategy_presets, select_strategy_ids
from strategies.signals import render_strategy_summary


RUNTIME_HELP = """A-Stockit runtime commands

  init-config [--force]
  registry bundle|skills|runtime
  watchlist-import --file ./watchlist.csv
  market-recap [--region cn|us --format markdown|prompt]
  fundamental-context 600519
  decision-dashboard 600519 000858 300750
  market-brief 600519 [--csv ./data/600519.csv --capital 200000 --position 1000 --notify]
  market-data 600519 [--export ./tmp/600519_enriched.csv]
  market-analyze 000300 [--csv ./data/000300.csv]
  decision-support 300750 [--cash 80000 --position 0]
  strategy-design 688981 [--strategy bull_trend]
  market-screen 600519 000858 300750
  stock-data 600519 [--csv ./data/600519.csv]
  news-intel 600519 [--headline "标题 | 摘要"]
  analysis 600519 [--headline-file ./headlines.txt --depth standard]
  backtest-evaluator 600519 [--state ./skills/astockit/_artifacts/runs/.../state.json --holding-days 10]
  backtest-evaluator 600519 --strategy bull_trend --csv ./data/600519.csv
  paper-trading 600519 --side buy --quantity 100 [--price 18.2]
  model-capability-advisor --workflow analysis --quick gemini-flash --deep claude-sonnet
  session-status
  feishu-notify --title "A-Stockit" "Daily scan completed"

Legacy aliases are still accepted:
  brief / data / analyze / decision / strategy / screen / status / notify / watchlist
"""


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"


def _fmt_num(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _resolve_symbol(candidate: str | None, session: dict) -> str | None:
    return candidate or session.get("last_symbol")


def _screen_items(namespace) -> list[tuple[str, str | None]]:
    pairs: list[tuple[str, str | None]] = [(symbol, None) for symbol in namespace.symbols]
    if namespace.file:
        path = Path(namespace.file).expanduser().resolve()
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if text and not text.startswith("#"):
                pairs.append((text, None))
    if namespace.dir:
        directory = Path(namespace.dir).expanduser().resolve()
        for item in sorted(directory.glob("*.csv")):
            match = re.search(r"(\d{6})", item.stem)
            symbol = match.group(1) if match else item.stem
            pairs.append((symbol, str(item)))
    seen = set()
    deduped = []
    for symbol, csv_path in pairs:
        key = (symbol, csv_path)
        if key not in seen:
            deduped.append(key)
            seen.add(key)
    return deduped


def _requested_strategies(namespace) -> list[str]:
    values = getattr(namespace, "strategy", None) or []
    return [item for item in values if get_strategy_preset(item)]


def _backtest_config(namespace, default_lot_size: int) -> BacktestConfig:
    return BacktestConfig(
        initial_cash=getattr(namespace, "initial_cash", 100000.0),
        max_position_pct=getattr(namespace, "max_position_pct", 0.2),
        slippage_bps=getattr(namespace, "slippage_bps", 5.0),
        lot_size=default_lot_size,
    )


class BundleRuntime:
    """Reusable runtime over config, storage, data, registry, and notifications."""

    def __init__(self, config_path: str | None = None):
        self.bundle_root = bundle_root()
        self.config, self.config_path = load_config(config_path)
        self.storage = Storage(runtime_root(self.config, self.config_path), self.config)
        self.registry = build_registry()
        self.notifications = NotificationManager(self.config)

    def render_registry(self, kind: str) -> str:
        payload = {
            "bundle": load_bundle_metadata,
            "skills": load_skill_registry,
            "runtime": load_runtime_registry,
        }[kind]()
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _market_bundle(self, namespace) -> tuple[Any, MarketSnapshot]:
        frame, source = load_market_frame(
            namespace.symbol,
            csv_path=getattr(namespace, "csv", None),
            start=getattr(namespace, "start", None),
            end=getattr(namespace, "end", None),
            source=getattr(namespace, "source", self.config.market.preferred_source),
            adjust=self.config.market.adjust,
        )
        enriched = enrich_market_frame(frame)
        snapshot = build_snapshot(namespace.symbol, enriched, source)
        return enriched, snapshot

    def _format_data(self, result: dict) -> str:
        summary = result["summary"]
        exported = f"\n导出文件: {summary['exported']}" if summary.get("exported") else ""
        return (
            f"数据处理\n"
            f"- 标的: {summary['symbol']}\n"
            f"- 数据源: {summary['source']}\n"
            f"- 区间: {summary['date_range'][0]} -> {summary['date_range'][1]}\n"
            f"- K 线数: {summary['rows']}\n"
            f"- 最新收盘: {summary['last_close']:.2f}\n"
            f"- 最新成交量: {summary['last_volume']}\n"
            f"- 换手率: {_fmt_pct(summary['turnover_pct'])}{exported}"
        )

    def _format_analysis(self, snapshot: MarketSnapshot, result: dict) -> str:
        summary = result["summary"]
        notes = "；".join(summary["notes"]) if summary["notes"] else "无"
        risk_flags = "；".join(summary["risk_flags"]) if summary["risk_flags"] else "无"
        return (
            f"市场分析\n"
            f"- 标的: {snapshot.symbol} ({snapshot.board})\n"
            f"- 数据窗口: {snapshot.start} -> {snapshot.end} | source={snapshot.source}\n"
            f"- 评分: {summary['score']}/100，倾向: {summary['bias']}\n"
            f"- 趋势: {summary['trend']}，状态: {summary['regime']}\n"
            f"- 涨跌幅: {_fmt_pct(snapshot.change_pct)}，振幅: {_fmt_pct(snapshot.amplitude_pct)}\n"
            f"- 量比: {snapshot.volume_ratio:.2f}，ATR: {_fmt_pct(snapshot.atr_pct)}\n"
            f"- 支撑/阻力: {summary['key_levels']['support']:.2f} / {summary['key_levels']['resistance']:.2f}\n"
            f"- 备注: {notes}\n"
            f"- 风险: {risk_flags}\n"
            f"- 说明: 当前状态描述，非收益预测、非投资建议。"
        )

    def _flag_provided(self, namespace, flag: str) -> bool:
        return flag in set(getattr(namespace, "_provided_flags", []) or [])

    def _symbol_origin_text(self, namespace) -> str:
        return "会话复用" if getattr(namespace, "_symbol_from_session", False) else "显式输入"

    def _assumption_lines(
        self,
        namespace,
        snapshot: MarketSnapshot,
        *,
        include_account: bool = False,
        include_strategy: bool = False,
        include_news: bool = False,
    ) -> list[str]:
        lines = [
            f"symbol_source: {self._symbol_origin_text(namespace)}",
            f"data_window: {snapshot.start} -> {snapshot.end} | source={snapshot.source} | rows={snapshot.rows}",
        ]
        if include_account and hasattr(namespace, "capital"):
            lines.append(
                f"capital: {_fmt_num(getattr(namespace, 'capital', None))} "
                f"({'显式提供' if self._flag_provided(namespace, '--capital') else '默认'})"
            )
            cash_value = getattr(namespace, "cash", None)
            cash_source = "显式提供" if self._flag_provided(namespace, "--cash") else "默认=capital"
            if cash_value is None:
                cash_value = getattr(namespace, "capital", None)
            lines.append(f"cash: {_fmt_num(cash_value)} ({cash_source})")
            lines.append(
                f"position: {_fmt_num(getattr(namespace, 'position', None))} "
                f"({'显式提供' if self._flag_provided(namespace, '--position') else '默认'})"
            )
            lines.append(
                f"risk_pct: {_fmt_num(getattr(namespace, 'risk', None))} "
                f"({'显式提供' if self._flag_provided(namespace, '--risk') else '默认'})"
            )
            if hasattr(namespace, "max_position"):
                lines.append(
                    f"max_position_pct: {_fmt_num(getattr(namespace, 'max_position', None))} "
                    f"({'显式提供' if self._flag_provided(namespace, '--max-position') else '默认'})"
                )
        if include_strategy and hasattr(namespace, "style"):
            lines.append(
                f"style: {_fmt_num(getattr(namespace, 'style', None))} "
                f"({'显式提供' if self._flag_provided(namespace, '--style') else '默认'})"
            )
            if hasattr(namespace, "hold_days"):
                lines.append(
                    f"hold_days: {_fmt_num(getattr(namespace, 'hold_days', None))} "
                    f"({'显式提供' if self._flag_provided(namespace, '--hold-days') else '默认'})"
                )
            requested = getattr(namespace, "strategy", None) or []
            if requested:
                lines.append(
                    f"strategy_ids: {', '.join(requested)} "
                    f"({'显式提供' if self._flag_provided(namespace, '--strategy') else '默认/自动'})"
                )
        if include_news and (
            hasattr(namespace, "headline")
            or hasattr(namespace, "headline_file")
            or hasattr(namespace, "company_name")
        ):
            headline_count = len(getattr(namespace, "headline", None) or [])
            headline_file = getattr(namespace, "headline_file", None)
            if headline_count or headline_file:
                source_bits = []
                if headline_count:
                    source_bits.append(f"manual_headlines={headline_count}")
                if headline_file:
                    source_bits.append(f"headline_file={headline_file}")
                lines.append(
                    "news_context: "
                    + ", ".join(source_bits)
                    + f" ({'显式提供' if headline_count or headline_file else '默认无'})"
                )
        return lines

    def _decision_non_modeled_risks(
        self,
        snapshot: MarketSnapshot,
        packet: DecisionPacket,
    ) -> list[str]:
        lines = [
            "置信度为启发式分数，不是概率预测或胜率估计。",
            "未建模盘口深度、冲击成本与分笔成交路径。",
            f"A股涨跌停约束为 ±{snapshot.limit_pct * 100:.0f}% ，可能导致参考止损/止盈无法按计划成交。",
            "开盘跳空、停牌与公告驱动风险未建模，参考价仅为条件锚点。",
        ]
        if snapshot.turnover_pct is None:
            lines.append("缺少换手率字段，无法对流动性做更细致判断。")
        else:
            lines.append(
                f"换手率={snapshot.turnover_pct:.2f}%、量比={snapshot.volume_ratio:.2f} 仅提供流动性线索，不等于可成交容量。"
            )
        if packet.quantity == 0:
            lines.append("当前建议数量为 0，表示这是状态判断或受约束结果，而非可直接下单仓位。")
        return lines

    def _strategy_realism_notes(self, snapshot: MarketSnapshot) -> list[str]:
        return [
            "入场区间、止损区间和止盈区间是计划锚点，不保证真实成交。",
            f"A股涨跌停约束为 ±{snapshot.limit_pct * 100:.0f}% ，极端行情下可能无法按计划止损或止盈。",
            "未建模ADV容量、冲击成本、分拆执行算法与停牌风险。",
            "开盘跳空可能直接跨越计划区间，需人工判断是否继续执行。",
        ]

    def _analysis_non_modeled_risks(
        self,
        snapshot: MarketSnapshot,
        fundamentals: dict[str, Any],
        news_report: Any,
    ) -> list[str]:
        lines = [
            "结论依赖当前快照与已提供上下文，不代表概率化预测。",
            "未建模盘口冲击、资金容量、基准约束和组合层相关性。",
            "若后续出现公告、停牌或价格限制，原始 thesis 可能需要重新评估。",
        ]
        if fundamentals.get("fundamentals", {}).get("status") != "ok":
            lines.append("基本面上下文为 best-effort 适配结果，不构成完整点时财务数据库。")
        if news_report is None:
            lines.append("未提供外部新闻证据，催化剂与风险判断主要来自价格和现有上下文。")
        return lines

    def _paper_modeled_features(self) -> list[str]:
        return [
            "本地账本持久化。",
            "手数归一、佣金和卖出印花税。",
            "买入成本价与 lot 级别持仓跟踪。",
            "T+1 可卖数量检查。",
        ]

    def _paper_non_modeled_risks(
        self,
        snapshot: MarketSnapshot | None,
        *,
        price_from_runtime: bool,
    ) -> list[str]:
        lines = [
            "未自动建模滑点、盘口冲击、ADV 容量、分笔执行算法与组合集中度。",
            "这是模拟账本，不连接券商，也不代表真实成交回报。",
            (
                "价格来自 runtime 默认市场价格上下文。"
                if price_from_runtime
                else "价格由用户显式提供，系统未验证真实可成交性。"
            ),
        ]
        if snapshot is not None:
            lines.append(
                f"A股涨跌停约束为 ±{snapshot.limit_pct * 100:.0f}% ，极端行情下可能无法按参考价格成交或止损。"
            )
        return lines

    def _render_paper_account_output(self, book) -> str:
        modeled = "\n".join(f"  - {item}" for item in self._paper_modeled_features())
        non_modeled = "\n".join(
            f"  - {item}" for item in self._paper_non_modeled_risks(None, price_from_runtime=False)
        )
        return (
            f"{render_book(book)}\n\n"
            f"Simulation Notice\n"
            f"- This is simulated trading only; no real capital is at risk.\n"
            f"- Modeled Locally:\n{modeled}\n"
            f"- Not Modeled Locally:\n{non_modeled}"
        )

    def _render_paper_trade_output(
        self,
        book,
        trade,
        snapshot: MarketSnapshot,
        namespace,
        *,
        price_from_runtime: bool,
    ) -> str:
        modeled = "\n".join(f"  - {item}" for item in self._paper_modeled_features())
        non_modeled = "\n".join(
            f"  - {item}" for item in self._paper_non_modeled_risks(snapshot, price_from_runtime=price_from_runtime)
        )
        price_source = "runtime_default_price" if price_from_runtime else "user_specified_price"
        return (
            f"{render_trade_result(book, trade)}\n\n"
            f"Execution Context\n"
            f"- price_source: {price_source}\n"
            f"- symbol_source: {self._symbol_origin_text(namespace)}\n"
            f"- market_source: {snapshot.source} | data_window: {snapshot.start} -> {snapshot.end}\n\n"
            f"Simulation Notice\n"
            f"- This is simulated trading only; no real capital is at risk.\n"
            f"- Modeled Locally:\n{modeled}\n"
            f"- Not Modeled Locally:\n{non_modeled}"
        )

    def _format_decision(self, packet: DecisionPacket, namespace, snapshot: MarketSnapshot) -> str:
        reasons = "\n".join(f"  - {item}" for item in packet.reasons)
        risk_flags = "；".join(packet.risk_flags) if packet.risk_flags else "无"
        assumptions = "\n".join(
            f"  - {item}" for item in self._assumption_lines(namespace, snapshot, include_account=True)
        )
        non_modeled = "\n".join(
            f"  - {item}" for item in self._decision_non_modeled_risks(snapshot, packet)
        )
        return (
            f"决策支持\n"
            f"- 条件动作: {packet.action}\n"
            f"- 启发式置信分: {packet.confidence:.2f}（非概率）\n"
            f"- 目标仓位: {packet.target_position_pct:.1%}\n"
            f"- 建议数量: {packet.quantity}\n"
            f"- 参考价/止损/止盈: {packet.entry_ref:.2f} / {packet.stop_loss:.2f} / {packet.take_profit:.2f}\n"
            f"- 单笔风险预算: {packet.risk_budget:.2f}\n"
            f"- 风险标记: {risk_flags}\n"
            f"- 依据:\n{reasons}\n"
            f"- 显式假设:\n{assumptions}\n"
            f"- 未建模风险:\n{non_modeled}"
        )

    def _format_strategy(self, plan: StrategyPlan, namespace, snapshot: MarketSnapshot) -> str:
        checklist = "\n".join(f"  - {item}" for item in plan.checklist)
        header = f"{plan.display_name} ({plan.strategy_id})" if plan.display_name and plan.strategy_id else plan.style
        risk_notes = "\n".join(f"  - {item}" for item in plan.risk_notes) if plan.risk_notes else ""
        assumptions = "\n".join(
            f"  - {item}"
            for item in self._assumption_lines(
                namespace,
                snapshot,
                include_account=True,
                include_strategy=True,
            )
        )
        realism = "\n".join(f"  - {item}" for item in self._strategy_realism_notes(snapshot))
        return (
            f"策略设计\n"
            f"- 风格/策略: {header}\n"
            f"- 说明: 这是条件执行计划，不是自动下单指令。\n"
            f"- 计划持有: {plan.holding_days} 天\n"
            f"- 建议仓位: {plan.position_pct:.1%}\n"
            f"- 入场区间: {plan.entry_zone}\n"
            f"- 止损区间: {plan.stop_zone}\n"
            f"- 止盈区间: {plan.take_profit_zone}\n"
            f"- 策略说明: {plan.thesis or 'n/a'}\n"
            f"- 检查清单:\n{checklist}\n"
            f"- 显式假设:\n{assumptions}"
            + (f"\n- 风险备注:\n{risk_notes}" if risk_notes else "")
            + f"\n- 执行现实性提示:\n{realism}"
        )

    def _brief_report(
        self,
        namespace,
        snapshot: MarketSnapshot,
        data_result: dict,
        analysis_result: dict,
        decision_result: DecisionPacket,
        strategy_result: StrategyPlan,
    ) -> str:
        header = "\n".join(
            [
                f"# {snapshot.symbol} A 股简报",
                "",
                "- scope: 单次综合快照，未做 thesis pressure-testing",
                f"- symbol_source: {self._symbol_origin_text(namespace)}",
                f"- data_window: {snapshot.start} -> {snapshot.end} | source={snapshot.source}",
            ]
        )
        return "\n\n".join(
            [
                header,
                self._format_data(data_result),
                self._format_analysis(snapshot, analysis_result),
                self._format_decision(decision_result, namespace, snapshot),
                self._format_strategy(strategy_result, namespace, snapshot),
            ]
        )

    def _status_text(self, context: str) -> str:
        session = self.storage.load_session("runtime", context)
        history = session.get("history", [])[-5:]
        bundle_meta = load_bundle_metadata()
        lines = [
            "A-Stockit runtime status",
            f"- 名称: {bundle_meta['display_name']}",
            f"- 命名空间: {bundle_meta['namespace']}",
            f"- Bundle 根目录: {self.bundle_root}",
            f"- 配置文件: {self.config_path}",
            f"- Artifacts 目录: {self.storage.root}",
            f"- Feishu 模式: {self.config.integrations.feishu.mode}",
            f"- 最近标的: {session.get('last_symbol') or 'n/a'}",
        ]
        if history:
            lines.append("- 最近上下文:")
            lines.extend(
                [f"  - {item['at']} | {item['command']} | {item['summary']}" for item in history]
            )
        return "\n".join(lines)

    def _friendly_error(self, message: str) -> str:
        return f"执行失败: {message}"

    def _format_fundamental_context(self, payload: dict[str, Any]) -> str:
        bundle = payload["fundamentals"]
        flow = payload["capital_flow"]
        dragon = payload["dragon_tiger"]
        growth = bundle.get("growth", {})
        earnings = bundle.get("earnings", {})
        institution = bundle.get("institution", {})
        lines = [
            "基本面上下文",
            f"- 标的: {payload['symbol']}",
            f"- Fundamentals 状态: {bundle.get('status')}",
            f"- Capital Flow 状态: {flow.get('status')}",
            f"- 龙虎榜: {'是' if dragon.get('is_on_list') else '否'}",
            f"- 营收同比: {_fmt_pct(growth.get('revenue_yoy'))}",
            f"- 净利同比: {_fmt_pct(growth.get('net_profit_yoy'))}",
            f"- ROE: {_fmt_pct(growth.get('roe'))}",
            f"- 毛利率: {_fmt_pct(growth.get('gross_margin'))}",
        ]
        if earnings.get("forecast_summary"):
            lines.append(f"- 业绩预告: {earnings['forecast_summary']}")
        if institution:
            lines.append(
                f"- 机构/股东变化: institution={institution.get('institution_holding_change')} top10={institution.get('top10_holder_change')}"
            )
        if flow.get("stock_flow"):
            stock_flow = flow["stock_flow"]
            lines.append(
                f"- 主力净流入: {stock_flow.get('main_net_inflow')} | 5日={stock_flow.get('inflow_5d')} | 10日={stock_flow.get('inflow_10d')}"
            )
        if flow.get("sector_rankings", {}).get("top"):
            leaders = ", ".join(item["name"] for item in flow["sector_rankings"]["top"][:3])
            lines.append(f"- 资金流入板块: {leaders}")
        return "\n".join(lines)

    def _fundamentals_fail_open(self, symbol: str) -> dict[str, Any]:
        try:
            return build_fundamental_context(symbol)
        except Exception as exc:
            return {
                "symbol": symbol,
                "fundamentals": {"status": "unavailable", "error": str(exc)},
                "capital_flow": {"status": "unavailable"},
                "dragon_tiger": {"is_on_list": False},
            }

    def _load_news_report(self, namespace) -> Any:
        items = load_news_items(
            path=getattr(namespace, "headline_file", None),
            headlines=getattr(namespace, "headline", None) or [],
        )
        if not items and getattr(namespace, "news_required", False):
            raise ValueError("未提供 headline 或 headline-file。")
        if not items:
            return None
        return build_news_intel_report(
            symbol=namespace.symbol,
            items=items,
            company_name=getattr(namespace, "company_name", ""),
            aliases=getattr(namespace, "alias", None),
            max_items=getattr(namespace, "max_items", 8),
        )

    def _resolve_backtest_state(self, symbol: str | None, requested: str | None, default_command: str) -> tuple[dict, Path]:
        if requested:
            state_path = Path(requested).expanduser().resolve()
            return load_state_payload(state_path), state_path
        for command in [default_command, "market-brief"]:
            latest = self.storage.latest_run(symbol=symbol, command=command)
            if latest and latest["state_path"].exists():
                return load_state_payload(latest["state_path"]), latest["state_path"]
        raise FileNotFoundError("没有找到可评估的 state.json，请传入 --state 或先运行 analysis/market-brief。")

    def run(self, namespace, *, context: str = "default") -> str:
        command = namespace.command or "help"
        if command == "help":
            return RUNTIME_HELP
        if command == "registry":
            return self.render_registry(namespace.kind)
        if command == "watchlist-import":
            if namespace.file:
                records = parse_watchlist_file(namespace.file)
            else:
                source_text = namespace.text or "\n".join(namespace.items or [])
                records = parse_watchlist_text(source_text)
            text = render_watchlist_summary(records)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"导入 {len(records)} 条观察列表",
            )
            return text
        if command == "market-recap":
            blueprint = get_market_strategy_blueprint(namespace.region)
            text = (
                blueprint.to_prompt_block()
                if namespace.format == "prompt"
                else blueprint.to_markdown_block()
            )
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.region} 市场复盘框架",
            )
            return text
        if command == "session-status":
            text = self._status_text(context)
            self.storage.save_session("runtime", context, command=command, summary="查看状态")
            return text
        if command == "feishu-notify":
            body = " ".join(namespace.body).strip()
            ok = self.notifications.notify(namespace.event, namespace.title, body)
            summary = f"{namespace.event}:{namespace.title}"
            self.storage.save_session("runtime", context, command=command, summary=summary)
            return "Feishu 通知已发送。" if ok else "Feishu 通知已跳过。请检查 mode/webhook 配置。"
        if command == "model-capability-advisor":
            workflow = getattr(namespace, "workflow", None) or getattr(namespace, "target", None) or "analysis"
            recommendation = recommend_models(
                workflow,
                quick_candidates=getattr(namespace, "quick", None),
                deep_candidates=getattr(namespace, "deep", None),
            )
            text = render_model_recommendation(recommendation)
            self.storage.save_session("runtime", context, command=command, summary=f"{workflow} 模型建议")
            return text
        if command == "paper-trading":
            book_path = self.storage.paper_book_path(getattr(namespace, "account", "default"))
            book = load_book(
                book_path,
                account=getattr(namespace, "account", "default"),
                initial_cash=getattr(namespace, "initial_cash", 100000.0),
            )
            if not getattr(namespace, "side", None):
                self.storage.save_session("runtime", context, command=command, summary=f"{book.account} 账户概览")
                return self._render_paper_account_output(book)

        session = self.storage.load_session("runtime", context)

        if command == "market-screen":
            items = _screen_items(namespace)
            if not items:
                return "market-screen 需要 symbols、--file 或 --dir。"
            rows = []
            failures = []
            for symbol, csv_path in items:
                try:
                    frame, source = load_market_frame(
                        symbol,
                        csv_path=csv_path,
                        start=namespace.start,
                        end=namespace.end,
                        source=namespace.source,
                        adjust=self.config.market.adjust,
                    )
                    snapshot = build_snapshot(symbol, enrich_market_frame(frame), source)
                except Exception as exc:
                    failures.append(f"{symbol}: {exc}")
                    continue
                rows.append(
                    {
                        "symbol": symbol,
                        "score": snapshot.score,
                        "regime": snapshot.regime,
                        "trend": snapshot.trend,
                        "change_pct": snapshot.change_pct,
                        "volume_ratio": snapshot.volume_ratio,
                    }
                )
            if not rows:
                return self._friendly_error("；".join(failures) or "没有可用筛选结果。")
            result = self.registry.execute("screen", rows=rows)["summary"][: namespace.top]
            text = ["批量筛选"]
            for item in result:
                text.append(
                    f"- {item['symbol']}: score={item['score']} trend={item['trend']} regime={item['regime']} change={item['change_pct']:.2f}% vr={item['volume_ratio']:.2f}"
                )
            if failures:
                text.append("")
                text.append("跳过")
                text.extend(f"- {item}" for item in failures[:5])
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"筛选 {len(result)} 个标的",
            )
            return "\n".join(text)
        if command == "decision-dashboard":
            items = _screen_items(namespace)
            if not items:
                return "decision-dashboard 需要 symbols、--file 或 --dir。"
            rows = []
            failures = []
            for symbol, csv_path in items:
                try:
                    frame, source = load_market_frame(
                        symbol,
                        csv_path=csv_path,
                        start=namespace.start,
                        end=namespace.end,
                        source=namespace.source,
                        adjust=self.config.market.adjust,
                    )
                    snapshot = build_snapshot(symbol, enrich_market_frame(frame), source)
                    packet = self.registry.execute(
                        "decision",
                        snapshot=snapshot,
                        capital=namespace.capital,
                        cash=namespace.cash,
                        position=0,
                        risk_pct=namespace.risk,
                        max_position_pct=namespace.max_position,
                        lot_size=self.config.market.lot_size,
                    )["summary"]
                except Exception as exc:
                    failures.append(f"{symbol}: {exc}")
                    continue
                rows.append(
                    {
                        "symbol": symbol,
                        "action": packet.action,
                        "score": snapshot.score,
                        "trend": snapshot.trend,
                        "regime": snapshot.regime,
                    }
                )
            if not rows:
                return self._friendly_error("；".join(failures) or "没有可用仪表盘结果。")
            summary = build_decision_dashboard(rows, top_n=namespace.top)
            text = render_decision_dashboard(summary)
            if failures:
                text += "\n\n跳过\n" + "\n".join(f"- {item}" for item in failures[:5])
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"仪表盘 {summary['total']} 个标的",
            )
            return text

        if command == "backtest-evaluator" and not getattr(namespace, "symbol", None) and getattr(namespace, "state", None):
            try:
                payload = load_state_payload(getattr(namespace, "state"))
                namespace.symbol = payload.get("symbol") or payload.get("snapshot", {}).get("symbol")
            except Exception:
                namespace.symbol = None
        requested_symbol = getattr(namespace, "symbol", None)
        namespace.symbol = _resolve_symbol(requested_symbol, session)
        namespace._symbol_from_session = requested_symbol is None and namespace.symbol is not None
        if not namespace.symbol:
            return "缺少标的代码。请传入 symbol，或先运行一次带 symbol 的命令。"

        if command == "fundamental-context":
            payload = build_fundamental_context(namespace.symbol)
            text = self._format_fundamental_context(payload)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} 基本面上下文",
                symbol=namespace.symbol,
            )
            return text
        if command == "news-intel":
            report = self._load_news_report(namespace)
            if report is None:
                report = build_news_intel_report(
                    symbol=namespace.symbol,
                    items=[],
                    company_name=getattr(namespace, "company_name", ""),
                    aliases=getattr(namespace, "alias", None),
                    max_items=getattr(namespace, "max_items", 8),
                )
            text = render_news_intel(report)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} news-intel",
                symbol=namespace.symbol,
            )
            return text

        try:
            frame, snapshot = self._market_bundle(namespace)
            data_result = self.registry.execute(
                "data",
                symbol=namespace.symbol,
                frame=frame,
                snapshot=snapshot,
                export_path=getattr(namespace, "export", None),
            )
            analysis_result = self.registry.execute("analyze", snapshot=snapshot)
        except Exception as exc:
            return self._friendly_error(str(exc))

        if command == "market-data":
            text = self._format_data(data_result)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} 数据处理",
                symbol=namespace.symbol,
            )
            return text

        if command == "market-analyze":
            text = self._format_analysis(snapshot, analysis_result)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} 市场分析",
                symbol=namespace.symbol,
            )
            return text
        if command == "stock-data":
            indicators = last_values(frame)
            fundamentals = self._fundamentals_fail_open(namespace.symbol)
            packet = build_stock_data_packet(
                snapshot,
                indicators=indicators,
                fundamentals=fundamentals,
            )
            text = render_research_packet(packet)
            run_dir = self.storage.write_run(namespace.symbol, command, packet.to_dict(), text)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} stock-data snapshot",
                symbol=namespace.symbol,
                run_dir=run_dir,
            )
            return f"{text}\n\nArtifacts\n- {run_dir / 'state.json'}\n- {run_dir / 'report.md'}"
        if command == "analysis":
            indicators = last_values(frame)
            fundamentals = self._fundamentals_fail_open(namespace.symbol)
            news_report = self._load_news_report(namespace)
            requested_strategies = _requested_strategies(namespace)
            packet = self.registry.execute(
                "decision",
                snapshot=snapshot,
                capital=namespace.capital,
                cash=namespace.cash,
                position=namespace.position,
                risk_pct=namespace.risk,
                max_position_pct=namespace.max_position,
                lot_size=self.config.market.lot_size,
            )["summary"]
            plan = self.registry.execute(
                "strategy",
                snapshot=snapshot,
                frame=frame,
                capital=namespace.capital,
                style=namespace.style,
                risk_pct=namespace.risk,
                holding_days=namespace.hold_days,
                strategies_requested=requested_strategies,
            )["summary"]
            research_packet = build_research_packet(
                snapshot,
                indicators=indicators,
                analysis_summary=analysis_result["summary"],
                decision=packet,
                strategy=plan,
                fundamentals=fundamentals,
                news_report=news_report,
                depth=getattr(namespace, "depth", "standard"),
                assumptions=self._assumption_lines(
                    namespace,
                    snapshot,
                    include_account=True,
                    include_strategy=True,
                    include_news=True,
                ),
                non_modeled_risks=self._analysis_non_modeled_risks(snapshot, fundamentals, news_report),
                symbol_source=self._symbol_origin_text(namespace),
            )
            text = render_research_packet(research_packet)
            run_dir = self.storage.write_run(namespace.symbol, command, research_packet.to_dict(), text)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} analysis {packet.action}",
                symbol=namespace.symbol,
                run_dir=run_dir,
            )
            return f"{text}\n\nArtifacts\n- {run_dir / 'state.json'}\n- {run_dir / 'report.md'}"
        if command == "paper-trading":
            price_from_runtime = getattr(namespace, "price", None) is None
            price = getattr(namespace, "price", None) or snapshot.last_close
            trade_date = getattr(namespace, "trade_date", None) or datetime.now().strftime("%Y-%m-%d")
            trade = apply_order(
                book,
                symbol=namespace.symbol,
                side=namespace.side,
                quantity=namespace.quantity,
                price=price,
                trade_date=trade_date,
                note=getattr(namespace, "note", ""),
            )
            save_book(book_path, book)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{trade.side} {trade.quantity} {trade.symbol}",
                symbol=namespace.symbol,
            )
            self.storage.record_paper_event(book.account, {"trade": trade.to_dict()})
            return self._render_paper_trade_output(
                book,
                trade,
                snapshot,
                namespace,
                price_from_runtime=price_from_runtime,
            )
        if command == "backtest-evaluator":
            if getattr(namespace, "strategy", None):
                strategy_reports = []
                for strategy_id in _requested_strategies(namespace):
                    config = _backtest_config(namespace, self.config.market.lot_size)
                    report = run_strategy_backtest(namespace.symbol, frame, strategy_id, config)
                    report_text = render_backtest_report(report)
                    run_dir = self.storage.write_backtest_artifacts(
                        symbol=namespace.symbol,
                        strategy=strategy_id,
                        payload=report.to_dict(),
                        report=report_text,
                        trades_csv=trades_to_csv(report),
                        equity_curve_csv=equity_curve_to_csv(report),
                    )
                    strategy_reports.append((strategy_id, report, run_dir))
                if not strategy_reports:
                    return "backtest-evaluator 需要至少一个有效的 --strategy。"
                lines = ["# Strategy Backtests", ""]
                for strategy_id, report, run_dir in strategy_reports:
                    metrics = report.metrics
                    lines.append(
                        f"- {strategy_id}: ret={metrics.total_return_pct:.2f}% sharpe={metrics.sharpe_ratio:.2f} mdd={metrics.max_drawdown_pct:.2f}% trades={metrics.trade_count} artifacts={run_dir}"
                    )
                self.storage.save_session(
                    "runtime",
                    context,
                    command=command,
                    summary=f"{namespace.symbol} strategy-backtest x{len(strategy_reports)}",
                    symbol=namespace.symbol,
                )
                return "\n".join(lines)
            payload, state_path = self._resolve_backtest_state(
                namespace.symbol,
                getattr(namespace, "state", None),
                getattr(namespace, "from_command", "analysis"),
            )
            evaluation = evaluate_saved_run(
                payload,
                future_frame=frame,
                holding_days=getattr(namespace, "holding_days", None),
            )
            text = render_backtest_evaluation(evaluation)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{evaluation.symbol} {evaluation.verdict}",
                symbol=evaluation.symbol,
            )
            return f"{text}\n- evaluated_state: {state_path}"

        if command == "decision-support":
            packet = self.registry.execute(
                "decision",
                snapshot=snapshot,
                capital=namespace.capital,
                cash=namespace.cash,
                position=namespace.position,
                risk_pct=namespace.risk,
                max_position_pct=namespace.max_position,
                lot_size=self.config.market.lot_size,
            )["summary"]
            text = self._format_decision(packet, namespace, snapshot)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} {packet.action}",
                symbol=namespace.symbol,
            )
            return text

        if command == "strategy-design":
            requested_strategies = _requested_strategies(namespace)
            plan = self.registry.execute(
                "strategy",
                snapshot=snapshot,
                frame=frame,
                capital=namespace.capital,
                style=namespace.style,
                risk_pct=namespace.risk,
                holding_days=namespace.hold_days,
                strategies_requested=requested_strategies,
            )["summary"]
            text = self._format_strategy(plan, namespace, snapshot)
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=f"{namespace.symbol} {plan.style}",
                symbol=namespace.symbol,
            )
            return text

        if command == "market-brief":
            requested_strategies = _requested_strategies(namespace)
            packet = self.registry.execute(
                "decision",
                snapshot=snapshot,
                capital=namespace.capital,
                cash=namespace.cash,
                position=namespace.position,
                risk_pct=namespace.risk,
                max_position_pct=namespace.max_position,
                lot_size=self.config.market.lot_size,
            )["summary"]
            plan = self.registry.execute(
                "strategy",
                snapshot=snapshot,
                frame=frame,
                capital=namespace.capital,
                style=namespace.style,
                risk_pct=namespace.risk,
                holding_days=namespace.hold_days,
                strategies_requested=requested_strategies,
            )["summary"]
            report = self._brief_report(namespace, snapshot, data_result, analysis_result, packet, plan)
            run_dir = self.storage.write_run(
                namespace.symbol,
                "market-brief",
                {
                    "snapshot": snapshot,
                    "data": data_result,
                    "analysis": analysis_result,
                    "decision": packet,
                    "strategy": plan,
                    "assumptions": self._assumption_lines(
                        namespace,
                        snapshot,
                        include_account=True,
                        include_strategy=True,
                    ),
                    "non_modeled_risks": self._decision_non_modeled_risks(snapshot, packet),
                },
                report,
            )
            summary = f"{namespace.symbol} {packet.action} score={snapshot.score}"
            self.storage.save_session(
                "runtime",
                context,
                command=command,
                summary=summary,
                symbol=namespace.symbol,
                run_dir=run_dir,
            )
            if namespace.notify:
                self.notifications.notify(
                    "strategy_ready",
                    f"{namespace.symbol} {packet.action}",
                    f"score={snapshot.score}\n\nstyle={plan.style}\n\nreport={run_dir / 'report.md'}",
                )
            return f"{report}\n\nArtifacts\n- {run_dir / 'state.json'}\n- {run_dir / 'report.md'}"

        return RUNTIME_HELP
