import pytest
from pathlib import Path

from skills_testing.agent_simulator import AgentSimulator, ScenarioLoader
from skills_testing.models import SkillMetadata, SkillContract
from skills_testing.skill_loader import load_skill
from skills_testing.trace_validator import TraceValidator

SKILLS_DIR = Path("/home/agent/.config/opencode/skills")
SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


class TestAgentSimulation:
    def test_simulate_tdd_red_phase(self):
        skill_path = SKILLS_DIR / "test-driven-development" / "SKILL.md"
        if not skill_path.exists():
            pytest.skip("Skill not found")
        metadata, body = load_skill(skill_path)
        simulator = AgentSimulator(metadata, body)
        scenario = {
            "name": "red_phase",
            "steps": [
                {"tool": "bash", "args": {"command": "create test file"}},
                {"tool": "edit", "args": {"action": "write failing test"}},
                {"tool": "bash", "args": {"command": "run tests"}, "expect_error": True}
            ]
        }
        trace = simulator.simulate(scenario)
        assert trace.skill_name == "test-driven-development"
        assert len(trace.tool_calls) == 3
        assert trace.errors

    def test_simulate_debugging_scenario(self):
        skill_path = SKILLS_DIR / "debugging-and-error-recovery" / "SKILL.md"
        if not skill_path.exists():
            pytest.skip("Skill not found")
        metadata, body = load_skill(skill_path)
        simulator = AgentSimulator(metadata, body)
        scenario = {
            "name": "test_failure",
            "steps": [
                {"tool": "bash", "args": {"command": "run failing test"}, "expect_error": True},
                {"tool": "read", "args": {"file": "test_calculator.py"}},
                {"tool": "edit", "args": {"action": "fix test"}},
                {"tool": "bash", "args": {"command": "run tests"}}
            ]
        }
        trace = simulator.simulate(scenario)
        assert len(trace.tool_calls) == 4
        assert trace.errors

    def test_trace_validation_pass(self):
        trace = AgentSimulator.__new__(AgentSimulator)
        trace = type('obj', (object,), {
            'skill_name': 'test',
            'scenario_name': 'test',
            'tool_calls': [
                type('obj', (object,), {'tool_name': 'bash', 'arguments': {}})(),
                type('obj', (object,), {'tool_name': 'edit', 'arguments': {}})()
            ],
            'errors': []
        })()
        validator = TraceValidator({
            "expected_tools": ["bash", "edit"],
            "forbidden_tools": ["dangerous_tool"],
            "min_tool_calls": 2,
            "max_tool_calls": 5
        })
        result = validator.validate(trace)
        assert result["passed"]
        assert result["tool_call_count"] == 2

    def test_trace_validation_missing_tool(self):
        trace = type('obj', (object,), {
            'skill_name': 'test',
            'scenario_name': 'test',
            'tool_calls': [
                type('obj', (object,), {'tool_name': 'bash', 'arguments': {}})()
            ],
            'errors': []
        })()
        validator = TraceValidator({
            "expected_tools": ["bash", "edit"]
        })
        result = validator.validate(trace)
        assert not result["passed"]
        assert "Missing required tool: edit" in result["errors"]


class TestScenarioLoader:
    def test_load_tdd_scenarios(self):
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_scenarios("test-driven-development")
        assert len(scenarios) == 3
        assert any(s["name"] == "red_phase" for s in scenarios)
        assert any(s["name"] == "green_phase" for s in scenarios)
        assert any(s["name"] == "refactor_phase" for s in scenarios)

    def test_load_debugging_scenarios(self):
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_scenarios("debugging-and-error-recovery")
        assert len(scenarios) == 3
        assert any(s["name"] == "test_failure" for s in scenarios)

    def test_load_incremental_scenarios(self):
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_scenarios("incremental-implementation")
        assert len(scenarios) == 2
        assert any(s["name"] == "feature_addition" for s in scenarios)
        assert any(s["name"] == "bug_fix" for s in scenarios)

    def test_load_missing_scenarios(self):
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_scenarios("nonexistent-skill")
        assert scenarios == []


class TestContractCompliance:
    def test_forbidden_pattern_compliance(self):
        metadata = SkillMetadata(
            name="test",
            description="test",
            contracts=SkillContract(forbidden_patterns=["as any", "@ts-ignore"])
        )
        body = "# Test\n\n## Overview\n\nClean code here."
        simulator = AgentSimulator(metadata, body)
        trace = simulator.simulate({"name": "test", "steps": []})
        assert not trace.errors

    def test_required_tools_in_scenario(self):
        metadata = SkillMetadata(
            name="test",
            description="test",
            contracts=SkillContract(required_tools=["bash", "edit"])
        )
        body = "# Test\n\n## Overview\n"
        simulator = AgentSimulator(metadata, body)
        scenario = {
            "name": "test",
            "steps": [
                {"tool": "bash", "args": {}},
                {"tool": "edit", "args": {}}
            ]
        }
        trace = simulator.simulate(scenario)
        tool_names = [tc.tool_name for tc in trace.tool_calls]
        assert "bash" in tool_names
        assert "edit" in tool_names

    def test_verification_required_enforcement(self):
        metadata = SkillMetadata(
            name="test",
            description="test",
            contracts=SkillContract(verification_required=True)
        )
        body = "# Test\n\n## Overview\n\n## Verification\n"
        simulator = AgentSimulator(metadata, body)
        scenario = {
            "name": "test",
            "steps": [
                {"tool": "edit", "args": {}},
                {"tool": "bash", "args": {"command": "verify"}}
            ]
        }
        trace = simulator.simulate(scenario)
        assert any(tc.tool_name == "bash" for tc in trace.tool_calls)
