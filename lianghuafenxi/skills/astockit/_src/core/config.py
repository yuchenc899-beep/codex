"""Configuration helpers for the bundle-first A-Stockit runtime layer."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any


CONFIG_ENV = "ASTOCKIT_CONFIG"
DEFAULT_CONFIG_NAME = "astockit.json"


@dataclass(slots=True)
class RuntimeConfig:
    output_dir: str = "_artifacts"
    timezone: str = "Asia/Shanghai"
    history_limit: int = 24


@dataclass(slots=True)
class MarketConfig:
    preferred_source: str = "auto"
    adjust: str = "qfq"
    lookback_days: int = 180
    lot_size: int = 100
    risk_per_trade: float = 0.01
    max_position_pct: float = 0.25


@dataclass(slots=True)
class FeishuConfig:
    mode: str = "off"
    webhook_url: str = ""
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    chat_id: str = ""
    allow_from: list[str] = field(default_factory=lambda: ["*"])
    group_policy: str = "mention"
    command_prefix: str = "/astockit"


@dataclass(slots=True)
class IntegrationsConfig:
    feishu: FeishuConfig = field(default_factory=FeishuConfig)


@dataclass(slots=True)
class BundleConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    market: MarketConfig = field(default_factory=MarketConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)


def resolve_config_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    env = os.getenv(CONFIG_ENV)
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / DEFAULT_CONFIG_NAME).resolve()


def _apply(instance: Any, payload: dict[str, Any]) -> Any:
    for item in fields(instance):
        if item.name not in payload:
            continue
        current = getattr(instance, item.name)
        value = payload[item.name]
        if is_dataclass(current) and isinstance(value, dict):
            _apply(current, value)
        else:
            setattr(instance, item.name, value)
    return instance


def load_config(path: str | Path | None = None) -> tuple[BundleConfig, Path]:
    config_path = resolve_config_path(path)
    config = BundleConfig()
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        _apply(config, payload)
    return config, config_path


def save_config(config: BundleConfig, path: str | Path | None = None) -> Path:
    config_path = resolve_config_path(path)
    config_path.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return config_path


def init_config(path: str | Path | None = None, *, force: bool = False) -> Path:
    config, config_path = load_config(path)
    if config_path.exists() and not force:
        return config_path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    return save_config(config, config_path)


def bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


def runtime_root(config: BundleConfig, config_path: Path) -> Path:
    output_dir = Path(config.runtime.output_dir)
    if output_dir.is_absolute():
        return output_dir
    return (bundle_root() / output_dir).resolve()
