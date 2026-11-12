"""Dashboard summarization helpers for batch decision workflows."""

from __future__ import annotations


def build_decision_dashboard(rows: list[dict], *, top_n: int = 10) -> dict:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["action"]] = counts.get(row["action"], 0) + 1
    ranked = sorted(rows, key=lambda item: item["score"], reverse=True)
    return {
        "total": len(rows),
        "counts": counts,
        "top": ranked[: min(max(1, top_n), len(ranked))],
    }


def render_decision_dashboard(summary: dict) -> str:
    lines = [
        "决策仪表盘",
        f"- 总标的: {summary['total']}",
        "- 动作分布: "
        + ", ".join(f"{action}={count}" for action, count in sorted(summary["counts"].items()))
        if summary["counts"]
        else "- 动作分布: 无",
    ]
    if summary["top"]:
        lines.append("- 重点关注:")
        lines.extend(
            [
                f"  - {item['symbol']}: action={item['action']} score={item['score']} trend={item['trend']} regime={item['regime']}"
                for item in summary["top"]
            ]
        )
    return "\n".join(lines)
