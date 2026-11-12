"""Report generator - generate markdown, JSON, and JUnit XML eval reports."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from skills_testing.eval_runner import EvalResult, EvalRun


def _normalize_error(error: str) -> str:
    """Normalize error message for clustering: lowercase, strip numbers and quoted strings."""
    norm = error.lower()
    norm = re.sub(r"'[^']*'", "''", norm)
    norm = re.sub(r'"[^"]*"', '""', norm)
    norm = re.sub(r"\d+", "N", norm)
    return norm.strip()


class ReportGenerator:
    """Generate markdown, JSON, and JUnit XML reports from eval runs."""

    def __init__(self, output_dir: Path | None = None, baseline_dir: Path | None = None):
        self.output_dir = Path(output_dir) if output_dir else Path("tests/skills/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_dir = Path(baseline_dir) if baseline_dir else Path("tests/skills/baselines")

    def _per_skill_summary(self, results: list[EvalResult]) -> list[dict[str, Any]]:
        """Aggregate results per skill: pass rate, duration, cost."""
        skills: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "total": 0, "passed": 0, "duration_ms": 0.0, "cost_usd": 0.0,
        })
        for r in results:
            s = skills[r.skill_name]
            s["total"] += 1
            if r.passed:
                s["passed"] += 1
            s["duration_ms"] += r.duration_ms
            s["cost_usd"] += r.cost_usd

        summary = []
        for name, s in sorted(skills.items()):
            pass_rate = (s["passed"] / s["total"] * 100) if s["total"] else 0.0
            summary.append({
                "skill": name,
                "total": s["total"],
                "passed": s["passed"],
                "failed": s["total"] - s["passed"],
                "pass_rate": round(pass_rate, 1),
                "avg_duration_ms": round(s["duration_ms"] / s["total"], 1),
                "total_cost_usd": round(s["cost_usd"], 6),
            })
        return summary

    def _cluster_errors(self, results: list[EvalResult]) -> list[dict[str, Any]]:
        """Group similar error messages across failed results."""
        clusters: dict[str, dict[str, Any]] = {}
        for r in results:
            if r.passed:
                continue
            for error in r.errors:
                key = _normalize_error(error)
                if key not in clusters:
                    clusters[key] = {"key": key, "representative": error, "count": 0, "examples": []}
                clusters[key]["count"] += 1
                clusters[key]["examples"].append(f"{r.skill_name}/{r.scenario_name}: {error}")

        return sorted(clusters.values(), key=lambda c: -c["count"])

    def _load_previous_run(self) -> dict[str, Any] | None:
        """Load the most recent baseline run JSON for trend comparison."""
        run_files = sorted(self.output_dir.glob("run_*.json"), reverse=True)
        if not run_files:
            return None
        return json.loads(run_files[0].read_text())

    def _trend_delta(self, current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
        """Compute trend deltas against previous baseline run."""
        if not previous:
            return {"has_baseline": False}

        cur_total = current["total_scenarios"]
        prev_total = previous["total_scenarios"]
        cur_passed = current["passed"]
        prev_passed = previous["passed"]
        cur_rate = (cur_passed / cur_total * 100) if cur_total else 0
        prev_rate = (prev_passed / prev_total * 100) if prev_total else 0

        return {
            "has_baseline": True,
            "previous_run_id": previous["run_id"],
            "scenario_delta": cur_total - prev_total,
            "pass_count_delta": cur_passed - prev_passed,
            "pass_rate_delta": round(cur_rate - prev_rate, 1),
            "duration_delta_ms": round(current["total_duration_ms"] - previous["total_duration_ms"], 1),
            "cost_delta_usd": round(current["total_cost_usd"] - previous["total_cost_usd"], 6),
        }

    def generate_markdown(self, eval_run: EvalRun) -> str:
        """Generate a markdown report with per-skill summaries, error clustering, and trend delta."""
        passed = sum(1 for r in eval_run.results if r.passed)
        failed = sum(1 for r in eval_run.results if not r.passed)

        lines = [
            "# Skill Eval Report",
            "",
            f"**Run ID:** {eval_run.run_id}",
            f"**Date:** {eval_run.timestamp}",
            f"**Total Scenarios:** {len(eval_run.results)}",
            f"**Passed:** {passed}",
            f"**Failed:** {failed}",
            f"**Total Cost:** ${eval_run.total_cost_usd:.4f}",
            f"**Total Duration:** {eval_run.total_duration_ms:.0f}ms",
        ]

        # Trend delta against baseline
        run_json = self._to_run_dict(eval_run)
        previous = self._load_previous_run()
        delta = self._trend_delta(run_json, previous)
        if delta["has_baseline"]:
            lines.extend([
                "",
                "## Trend vs Baseline",
                "",
                f"**Baseline Run:** {delta['previous_run_id']}",
                f"**Scenarios:** {delta['scenario_delta']:+d}",
                f"**Passed:** {delta['pass_count_delta']:+d}",
                f"**Pass Rate:** {delta['pass_rate_delta']:+.1f}%",
                f"**Duration:** {delta['duration_delta_ms']:+.0f}ms",
                f"**Cost:** ${delta['cost_delta_usd']:+.4f}",
            ])

        # Per-skill summary
        skill_summaries = self._per_skill_summary(eval_run.results)
        if skill_summaries:
            lines.extend([
                "",
                "## Per-Skill Summary",
                "",
                "| Skill | Scenarios | Passed | Failed | Pass Rate | Avg Duration | Total Cost |",
                "|-------|-----------|--------|--------|-----------|-------------|------------|",
            ])
            for s in skill_summaries:
                lines.append(
                    f"| {s['skill']} | {s['total']} | {s['passed']} | {s['failed']} | "
                    f"{s['pass_rate']}% | {s['avg_duration_ms']}ms | ${s['total_cost_usd']:.6f} |"
                )

        # Results table
        lines.extend([
            "",
            "## Results",
            "",
            "| Scenario | Skill | Status | Duration | Cost |",
            "|----------|-------|--------|----------|------|",
        ])
        for result in eval_run.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(
                f"| {result.scenario_name} | {result.skill_name} | {status} | "
                f"{result.duration_ms:.0f}ms | ${result.cost_usd:.4f} |"
            )

        # Error clusters
        if failed:
            clusters = self._cluster_errors(eval_run.results)
            if clusters:
                lines.extend(["", "## Error Clusters", ""])
                for i, c in enumerate(clusters, 1):
                    lines.append(f"**{i}. {c['representative'][:80]}** ({c['count']} occurrences)")
                    for ex in c["examples"][:3]:
                        lines.append(f"  - {ex}")
                    if len(c["examples"]) > 3:
                        lines.append(f"  - ... and {len(c['examples']) - 3} more")
                    lines.append("")

            # Detailed failures
            lines.extend(["## Failures", ""])
            for result in eval_run.results:
                if result.passed:
                    continue
                lines.append(f"### {result.scenario_name} ({result.skill_name})")
                for error in result.errors:
                    lines.append(f"- {error}")
                lines.append("")

        return "\n".join(lines)

    def _to_run_dict(self, eval_run: EvalRun) -> dict[str, Any]:
        """Serialize an EvalRun to a JSON-compatible dict."""
        passed = sum(1 for r in eval_run.results if r.passed)
        return {
            "run_id": eval_run.run_id,
            "timestamp": eval_run.timestamp,
            "total_scenarios": len(eval_run.results),
            "passed": passed,
            "failed": len(eval_run.results) - passed,
            "total_cost_usd": eval_run.total_cost_usd,
            "total_duration_ms": eval_run.total_duration_ms,
        }

    def generate_json(self, eval_run: EvalRun) -> str:
        """Generate a machine-readable JSON report."""
        report = self._to_run_dict(eval_run)
        report["per_skill"] = self._per_skill_summary(eval_run.results)
        report["error_clusters"] = self._cluster_errors(eval_run.results)

        previous = self._load_previous_run()
        report["trend"] = self._trend_delta(report, previous)

        report["results"] = [
            {
                "scenario": r.scenario_name,
                "skill": r.skill_name,
                "passed": r.passed,
                "duration_ms": r.duration_ms,
                "cost_usd": r.cost_usd,
                "errors": r.errors,
                "judge_score": r.judge_score,
            }
            for r in eval_run.results
        ]

        return json.dumps(report, indent=2)

    def save_json(self, eval_run: EvalRun) -> Path:
        """Save JSON report to file (also writes run_*.json for baseline trend tracking)."""
        content = self.generate_json(eval_run)
        path = self.output_dir / f"report_{eval_run.run_id}.json"
        path.write_text(content)
        # Also save as run_*.json for trend comparison
        run_path = self.output_dir / f"run_{eval_run.run_id}.json"
        run_path.write_text(content)
        return path

    def save_markdown(self, eval_run: EvalRun) -> Path:
        """Save markdown report to file."""
        content = self.generate_markdown(eval_run)
        path = self.output_dir / f"report_{eval_run.run_id}.md"
        path.write_text(content)
        return path

    def generate_junit_xml(self, eval_run: EvalRun) -> str:
        """Generate JUnit XML report for CI integration."""
        testsuite = ET.Element("testsuite")
        testsuite.set("name", "skill-eval")
        testsuite.set("tests", str(len(eval_run.results)))
        testsuite.set("failures", str(sum(1 for r in eval_run.results if not r.passed)))
        testsuite.set("time", str(eval_run.total_duration_ms / 1000))

        for result in eval_run.results:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", f"{result.skill_name} - {result.scenario_name}")
            testcase.set("time", str(result.duration_ms / 1000))
            if not result.passed:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", "; ".join(result.errors) or "Evaluation failed")
                failure.text = "\n".join(result.errors)

        return ET.tostring(testsuite, encoding="unicode")

    def save_junit_xml(self, eval_run: EvalRun) -> Path:
        """Save JUnit XML report to file."""
        content = self.generate_junit_xml(eval_run)
        path = self.output_dir / f"junit_{eval_run.run_id}.xml"
        path.write_text(content)
        return path
