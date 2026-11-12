import pytest
from pathlib import Path
import time

from skills_testing.agent_simulator import AgentSimulator, ScenarioLoader
from skills_testing.eval_runner import BudgetEnforcer, EvalResult, EvalRun, EvalRunner
from skills_testing.models import SkillContract, SkillMetadata
from skills_testing.regression_tracker import RegressionTracker
from skills_testing.report_generator import ReportGenerator
from skills_testing.skill_loader import load_skill
from skills_testing.trace_validator import TraceValidator

SKILLS_DIR = Path("/home/agent/.config/opencode/skills")
SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


class TestE2EEvalRunner:
    def test_deterministic_eval_pass(self):
        skill_path = SKILLS_DIR / "test-driven-development" / "SKILL.md"
        if not skill_path.exists():
            pytest.skip("Skill not found")
        metadata, body = load_skill(skill_path)
        simulator = AgentSimulator(metadata, body)
        scenario = {
            "name": "green_phase",
            "expected": {
                "expected_tools": ["edit", "bash"],
                "min_tool_calls": 2,
            },
            "steps": [
                {"tool": "edit", "args": {"action": "implement factorial"}},
                {"tool": "bash", "args": {"command": "run tests"}}
            ]
        }
        trace = simulator.simulate(scenario)
        runner = EvalRunner(SKILLS_DIR, SCENARIOS_DIR)
        result = runner.run_scenario("test-driven-development", scenario, trace, use_judge=False)
        assert result.passed
        assert result.scenario_name == "green_phase"

    def test_deterministic_eval_fail_missing_tool(self):
        scenario = {
            "name": "missing_tool_test",
            "expected": {
                "expected_tools": ["edit", "bash", "lsp_diagnostics"],
            },
            "steps": [
                {"tool": "edit", "args": {}},
                {"tool": "bash", "args": {}}
            ]
        }
        trace = AgentSimulator(
            SkillMetadata(name="test", description="test"), ""
        ).simulate(scenario)
        runner = EvalRunner(SKILLS_DIR, SCENARIOS_DIR)
        result = runner.run_scenario("test", scenario, trace, use_judge=False)
        assert not result.passed
        assert "Missing required tool: lsp_diagnostics" in result.errors

    def test_budget_enforcer_blocks_over_budget(self):
        enforcer = BudgetEnforcer(daily_budget_usd=0.001)
        assert not enforcer.can_spend(0.01)

    def test_budget_enforcer_allows_under_budget(self):
        enforcer = BudgetEnforcer(daily_budget_usd=10.0)
        assert enforcer.can_spend(0.01)

    def test_regression_tracker_new_baseline(self, tmp_path):
        tracker = RegressionTracker(baseline_dir=tmp_path)
        result = EvalResult(
            scenario_name="test_scenario",
            skill_name="test_skill",
            passed=True,
            duration_ms=100.0,
            judge_score=0.9,
        )
        comparison = tracker.compare_to_baseline(result)
        assert comparison["status"] == "new_baseline"
        assert not comparison["regression"]

    def test_regression_tracker_detects_regression(self, tmp_path):
        tracker = RegressionTracker(baseline_dir=tmp_path)
        baseline = EvalResult(
            scenario_name="test_scenario",
            skill_name="test_skill",
            passed=True,
            duration_ms=100.0,
            judge_score=0.9,
        )
        tracker.record_baseline(baseline)
        new_result = EvalResult(
            scenario_name="test_scenario",
            skill_name="test_skill",
            passed=False,
            duration_ms=100.0,
        )
        comparison = tracker.compare_to_baseline(new_result)
        assert comparison["status"] == "regression"
        assert comparison["regression"]

    def test_report_generator_markdown(self):
        run = EvalRun(
            run_id="test-001",
            timestamp=time.time(),
            results=[
                EvalResult("scenario1", "skill1", True, 100.0),
                EvalResult("scenario2", "skill1", False, 200.0, errors=["timeout"]),
            ],
            total_cost_usd=0.05,
            total_duration_ms=300.0,
        )
        gen = ReportGenerator()
        md = gen.generate_markdown(run)
        assert "# Skill Eval Report" in md
        assert "scenario1" in md
        assert "scenario2" in md
        assert "timeout" in md

    def test_report_generator_junit_xml(self):
        run = EvalRun(
            run_id="test-002",
            timestamp=time.time(),
            results=[
                EvalResult("scenario1", "skill1", True, 100.0),
                EvalResult("scenario2", "skill1", False, 200.0, errors=["fail"]),
            ],
        )
        gen = ReportGenerator()
        xml = gen.generate_junit_xml(run)
        assert "<testsuite" in xml
        assert "<testcase" in xml
        assert "<failure" in xml

    def test_llm_judge_skips_without_client(self):
        scenario = {"name": "judge_test", "steps": []}
        trace = AgentSimulator(
            SkillMetadata(name="test", description="test"), ""
        ).simulate(scenario)
        runner = EvalRunner(SKILLS_DIR, SCENARIOS_DIR)
        result = runner.run_scenario("test", scenario, trace, use_judge=True)
        assert not result.passed
        assert "No LLM client configured" in result.errors
