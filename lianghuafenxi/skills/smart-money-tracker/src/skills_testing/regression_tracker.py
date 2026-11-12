"""Regression tracker - compare eval results across runs and flag regressions."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from skills_testing.eval_runner import EvalResult, EvalRun


class RegressionTracker:
    """Track eval results across runs and detect regressions."""

    def __init__(self, baseline_dir: Path | None = None):
        self.baseline_dir = baseline_dir or Path("tests/skills/baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def _baseline_path(self, skill_name: str, scenario_name: str) -> Path:
        safe_name = f"{skill_name}_{scenario_name}".replace("/", "_")
        return self.baseline_dir / f"{safe_name}.json"

    def record_baseline(self, result: EvalResult) -> None:
        """Record a result as the baseline for future comparison."""
        path = self._baseline_path(result.skill_name, result.scenario_name)
        path.write_text(json.dumps({
            "passed": result.passed,
            "judge_score": result.judge_score,
            "errors": result.errors,
        }))

    def compare_to_baseline(self, result: EvalResult) -> dict[str, Any]:
        """Compare a result to its baseline and report changes."""
        path = self._baseline_path(result.skill_name, result.scenario_name)
        if not path.exists():
            self.record_baseline(result)
            return {"status": "new_baseline", "regression": False}

        baseline = json.loads(path.read_text())
        regressions = []

        if baseline.get("passed") and not result.passed:
            regressions.append("was passing, now failing")
        if baseline.get("judge_score") and result.judge_score:
            if result.judge_score < baseline["judge_score"] - 0.1:
                regressions.append(f"score dropped: {baseline['judge_score']:.2f} -> {result.judge_score:.2f}")

        if regressions:
            return {
                "status": "regression",
                "regression": True,
                "details": regressions,
            }

        if not baseline.get("passed") and result.passed:
            return {"status": "improvement", "regression": False}

        return {"status": "stable", "regression": False}

    def get_all_baselines(self) -> dict[str, dict[str, Any]]:
        """Load all recorded baselines."""
        baselines = {}
        for path in self.baseline_dir.glob("*.json"):
            data = json.loads(path.read_text())
            baselines[path.stem] = data
        return baselines
