"""Filesystem-backed persistence for runtime sessions and run artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from core.config import BundleConfig


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") or "session"


def _jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


class Storage:
    """Persist lightweight session memory and date-scoped execution artifacts."""

    def __init__(self, root: Path, config: BundleConfig):
        self.root = root
        self.config = config
        self.sessions_dir = self.root / "sessions"
        self.runs_dir = self.root / "runs"
        self.reports_dir = self.root / "reports"
        self.history_dir = self.root / "history"
        self.exports_dir = self.root / "exports"
        self.paper_dir = self.root / "paper"
        self.backtests_dir = self.root / "backtests"
        self.manifests_dir = self.root / "manifests"
        self.runs_manifest = self.manifests_dir / "runs.jsonl"
        self.backtests_manifest = self.manifests_dir / "backtests.jsonl"
        self.paper_manifest = self.manifests_dir / "paper.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in (
            self.sessions_dir,
            self.runs_dir,
            self.reports_dir,
            self.history_dir,
            self.exports_dir,
            self.paper_dir,
            self.backtests_dir,
            self.manifests_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _now(self) -> datetime:
        return datetime.now(ZoneInfo(self.config.runtime.timezone))

    def session_path(self, channel: str, chat_id: str) -> Path:
        return self.sessions_dir / f"{_safe_name(channel)}__{_safe_name(chat_id)}.json"

    def load_session(self, channel: str, chat_id: str) -> dict:
        path = self.session_path(channel, chat_id)
        if not path.exists():
            return {"last_symbol": None, "history": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_session(
        self,
        channel: str,
        chat_id: str,
        *,
        command: str,
        summary: str,
        symbol: str | None = None,
        run_dir: Path | None = None,
    ) -> None:
        state = self.load_session(channel, chat_id)
        if symbol:
            state["last_symbol"] = symbol
        history = state.setdefault("history", [])
        history.append(
            {
                "at": self._now().isoformat(timespec="seconds"),
                "command": command,
                "summary": summary,
                "run_dir": str(run_dir) if run_dir else "",
            }
        )
        state["history"] = history[-self.config.runtime.history_limit :]
        self.session_path(channel, chat_id).write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._append_jsonl(
            self.history_dir / "sessions.jsonl",
            {
                "at": self._now().isoformat(timespec="seconds"),
                "channel": channel,
                "chat_id": chat_id,
                "command": command,
                "summary": summary,
                "symbol": symbol or "",
                "run_dir": str(run_dir) if run_dir else "",
            },
        )

    def write_run(self, symbol: str, command: str, payload: dict, report: str) -> Path:
        stamp = self._now()
        run_dir = (
            self.runs_dir
            / stamp.strftime("%Y%m%d")
            / f"{_safe_name(symbol)}_{_safe_name(command)}_{stamp.strftime('%H%M%S')}"
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        state_path = run_dir / "state.json"
        report_path = run_dir / "report.md"
        metadata_path = run_dir / "metadata.json"
        state_path.write_text(
            json.dumps(_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        report_path.write_text(report.strip() + "\n", encoding="utf-8")
        metadata = {
            "symbol": symbol,
            "command": command,
            "run_dir": str(run_dir),
            "state_path": str(state_path),
            "report_path": str(report_path),
            "generated_at": stamp.isoformat(timespec="seconds"),
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._append_jsonl(self.runs_manifest, metadata)
        return run_dir

    def list_runs(
        self,
        *,
        symbol: str | None = None,
        command: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        symbol_key = _safe_name(symbol) if symbol else None
        command_key = _safe_name(command) if command else None
        results: list[dict] = []
        for run_dir in sorted(self.runs_dir.glob("*/*"), reverse=True):
            if not run_dir.is_dir():
                continue
            name = run_dir.name
            if symbol_key and not name.startswith(f"{symbol_key}_"):
                continue
            if command_key and f"_{command_key}_" not in name:
                continue
            results.append(
                {
                    "name": name,
                    "run_dir": run_dir,
                    "state_path": run_dir / "state.json",
                    "report_path": run_dir / "report.md",
                }
            )
            if len(results) >= limit:
                break
        return results

    def latest_run(self, *, symbol: str | None = None, command: str | None = None) -> dict | None:
        runs = self.list_runs(symbol=symbol, command=command, limit=1)
        return runs[0] if runs else None

    def paper_book_path(self, account: str = "default") -> Path:
        path = self.paper_dir / f"{_safe_name(account)}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def backtest_run_dir(self, symbol: str, strategy: str) -> Path:
        stamp = self._now()
        run_dir = (
            self.backtests_dir
            / stamp.strftime("%Y%m%d")
            / f"{_safe_name(symbol)}_{_safe_name(strategy)}_{stamp.strftime('%H%M%S')}"
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_backtest_artifacts(
        self,
        *,
        symbol: str,
        strategy: str,
        payload: dict,
        report: str,
        trades_csv: str,
        equity_curve_csv: str,
    ) -> Path:
        run_dir = self.backtest_run_dir(symbol, strategy)
        metadata = {
            "symbol": symbol,
            "strategy": strategy,
            "run_dir": str(run_dir),
            "generated_at": self._now().isoformat(timespec="seconds"),
        }
        (run_dir / "config.json").write_text(
            json.dumps(_jsonable(payload.get("config", {})), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (run_dir / "state.json").write_text(
            json.dumps(_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (run_dir / "metrics.json").write_text(
            json.dumps(_jsonable(payload.get("metrics", {})), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (run_dir / "report.md").write_text(report.strip() + "\n", encoding="utf-8")
        (run_dir / "trades.csv").write_text(trades_csv, encoding="utf-8")
        (run_dir / "equity_curve.csv").write_text(equity_curve_csv, encoding="utf-8")
        (run_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._append_jsonl(self.backtests_manifest, metadata)
        return run_dir

    def record_paper_event(self, account: str, payload: dict) -> None:
        self._append_jsonl(
            self.paper_manifest,
            {
                "account": account,
                "at": self._now().isoformat(timespec="seconds"),
                **_jsonable(payload),
            },
        )

    def _append_jsonl(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(payload), ensure_ascii=False) + "\n")
