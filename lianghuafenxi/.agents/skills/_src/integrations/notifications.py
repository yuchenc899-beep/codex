"""Feishu notification helpers for the A-Stockit runtime layer."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from core.config import BundleConfig, FeishuConfig


FEISHU_COLORS = {
    "market_scan_done": "green",
    "strategy_ready": "blue",
    "checkpoint_needed": "orange",
    "job_failed": "red",
    "session_completed": "purple",
    "custom": "blue",
}

@dataclass(slots=True)
class FeishuBridge:
    """Feishu webhook bridge used by runtime workflows and skills."""

    config: FeishuConfig

    def available(self) -> bool:
        return self.config.mode in {"push", "interactive"}

    def push_event(self, event: str, title: str, body: str) -> bool:
        if self.config.mode == "off" or not self.config.webhook_url:
            return False
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title[:80]},
                    "template": FEISHU_COLORS.get(event, "blue"),
                },
                "elements": [{"tag": "markdown", "content": body[:6000]}],
            },
        }
        data = json.dumps(card, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.config.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=8):
                return True
        except (urllib.error.URLError, TimeoutError, ValueError):
            return False


class NotificationManager:
    """Small facade over optional outbound notification channels."""

    def __init__(self, config: BundleConfig):
        self.feishu = FeishuBridge(config.integrations.feishu)

    def notify(self, event: str, title: str, body: str) -> bool:
        return self.feishu.push_event(event, title, body)
