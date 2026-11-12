"""Eval runner - orchestrate LLM evaluations with skill context."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from skills_testing.agent_simulator import SimulationTrace
from skills_testing.trace_validator import TraceValidator


@dataclass
class EvalResult:
    scenario_name: str
    skill_name: str
    passed: bool
    duration_ms: float
    cost_usd: float = 0.0
    errors: list[str] = field(default_factory=list)
    judge_score: float | None = None
    judge_reasoning: str = ""


@dataclass
class EvalRun:
    run_id: str
    timestamp: float
    results: list[EvalResult] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0


class BudgetEnforcer:
    """Enforce daily cost budget for eval runs."""

    def __init__(self, daily_budget_usd: float, state_file: Path | None = None):
        self.daily_budget_usd = daily_budget_usd
        self.state_file = state_file or Path(".eval_budget_state.json")
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            self.today_cost = data.get("today_cost", 0.0)
            self.last_reset = data.get("last_reset", 0)
        else:
            self.today_cost = 0.0
            self.last_reset = 0

    def _save_state(self):
        self.state_file.write_text(json.dumps({
            "today_cost": self.today_cost,
            "last_reset": self.last_reset
        }))

    def can_spend(self, amount: float) -> bool:
        self._maybe_reset()
        return (self.today_cost + amount) <= self.daily_budget_usd

    def record_spend(self, amount: float):
        self._maybe_reset()
        self.today_cost += amount
        self._save_state()

    def _maybe_reset(self):
        now = time.time()
        day_seconds = 86400
        if now - self.last_reset > day_seconds:
            self.today_cost = 0.0
            self.last_reset = now


class EvalRunner:
    """Orchestrate deterministic and LLM-as-judge evaluations."""

    def __init__(
        self,
        skills_dir: Path,
        scenarios_dir: Path,
        budget_enforcer: BudgetEnforcer | None = None,
        llm_client: Callable | None = None,
    ):
        self.skills_dir = skills_dir
        self.scenarios_dir = scenarios_dir
        self.budget_enforcer = budget_enforcer or BudgetEnforcer(daily_budget_usd=10.0)
        self.llm_client = llm_client
        self.results: list[EvalResult] = []

    def run_deterministic_eval(
        self,
        skill_name: str,
        scenario: dict[str, Any],
        trace: SimulationTrace,
    ) -> EvalResult:
        """Run deterministic evaluation without LLM calls."""
        start = time.perf_counter()
        expected = scenario.get("expected", {})
        validator = TraceValidator(expected)
        validation = validator.validate(trace)
        duration_ms = (time.perf_counter() - start) * 1000
        return EvalResult(
            scenario_name=scenario["name"],
            skill_name=skill_name,
            passed=validation["passed"],
            duration_ms=duration_ms,
            errors=validation["errors"],
        )

    def run_llm_judge_eval(
        self,
        skill_name: str,
        scenario: dict[str, Any],
        trace: SimulationTrace,
        max_cost: float = 0.01,
    ) -> EvalResult:
        """Run LLM-as-judge evaluation."""
        if not self.budget_enforcer.can_spend(max_cost):
            return EvalResult(
                scenario_name=scenario["name"],
                skill_name=skill_name,
                passed=False,
                duration_ms=0.0,
                errors=["Budget exceeded - skipping LLM eval"],
            )

        if not self.llm_client:
            return EvalResult(
                scenario_name=scenario["name"],
                skill_name=skill_name,
                passed=False,
                duration_ms=0.0,
                errors=["No LLM client configured"],
            )

        start = time.perf_counter()
        try:
            judge_result = self.llm_client(
                skill_name=skill_name,
                scenario=scenario,
                trace=trace,
            )
            duration_ms = (time.perf_counter() - start) * 1000
            self.budget_enforcer.record_spend(judge_result.get("cost", 0.0))
            return EvalResult(
                scenario_name=scenario["name"],
                skill_name=skill_name,
                passed=judge_result.get("passed", False),
                duration_ms=duration_ms,
                cost_usd=judge_result.get("cost", 0.0),
                judge_score=judge_result.get("score"),
                judge_reasoning=judge_result.get("reasoning", ""),
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return EvalResult(
                scenario_name=scenario["name"],
                skill_name=skill_name,
                passed=False,
                duration_ms=duration_ms,
                errors=[f"LLM judge error: {e}"],
            )

    def run_scenario(
        self,
        skill_name: str,
        scenario: dict[str, Any],
        trace: SimulationTrace,
        use_judge: bool = False,
    ) -> EvalResult:
        """Run evaluation for a single scenario."""
        if use_judge:
            return self.run_llm_judge_eval(skill_name, scenario, trace)
        return self.run_deterministic_eval(skill_name, scenario, trace)
