import os

import pytest

from skills_testing.agent_simulator import AgentSimulator, SimulationTrace
from skills_testing.models import SkillMetadata
from skills_testing.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    OllamaStreamError,
    ollama_judge,
)


def _ollama_health_check() -> bool:
    try:
        client = OllamaClient(timeout=3.0)
        return client.health_check()
    except Exception:
        return False


@pytest.fixture(name="ollama_available")
def ollama_available_fixture():
    if not _ollama_health_check():
        pytest.skip(
            "Ollama not available — set OLLAMA_AVAILABLE=1 or start Ollama"
        )


def _make_trace() -> SimulationTrace:
    return AgentSimulator(
        SkillMetadata(name="test-skill", description="Test skill"),
        "## Test Workflow\n\n1. Run command\n2. Verify output",
    ).simulate(
        {
            "name": "test_scenario",
            "steps": [
                {"tool": "bash", "args": {"command": "run_test"}},
                {"tool": "bash", "args": {"command": "verify"}},
            ],
        }
    )


class TestOllamaClient:
    def test_health_check_returns_bool_when_offline(self):
        client = OllamaClient(host="http://localhost", port=19999, timeout=1.0)
        assert client.health_check() is False

    def test_connection_error_has_host_port(self):
        client = OllamaClient(host="http://localhost", port=19999, timeout=1.0)
        with pytest.raises(OllamaConnectionError) as exc_info:
            client.generate("test prompt")
        assert "localhost:19999" in str(exc_info.value)

    def test_ollama_judge_returns_dict(self):
        trace = _make_trace()
        result = ollama_judge(
            "test-skill",
            {"name": "sc1", "description": "Test scenario"},
            trace,
            client=OllamaClient(host="http://localhost", port=19999, timeout=1.0),
        )
        assert isinstance(result, dict)
        assert "passed" in result
        assert "cost" in result
        assert "score" in result
        assert "reasoning" in result
        assert result["cost"] == 0.0

    def test_ollama_judge_graceful_skip_when_offline(self):
        trace = _make_trace()
        result = ollama_judge(
            "test-skill",
            {"name": "sc1", "description": "Test"},
            trace,
            client=OllamaClient(host="http://localhost", port=19999, timeout=1.0),
        )
        assert result["passed"] is False
        assert "Ollama not available" in result["reasoning"]
        assert result["cost"] == 0.0
        assert result["score"] is None


class TestOllamaE2E:
    def test_health_check_passes(self, ollama_available):
        client = OllamaClient(timeout=3.0)
        assert client.health_check()

    def test_generate_returns_text(self, ollama_available):
        client = OllamaClient()
        result = client.generate("Say hello in one word.")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_ollama_judge_evaluates_pass(self, ollama_available):
        trace = _make_trace()
        result = ollama_judge(
            "test-skill",
            {
                "name": "complete_workflow",
                "description": "Agent follows a two-step command-verify workflow",
                "expected": {"expected_tools": ["bash"], "min_steps": 2},
            },
            trace,
        )
        assert isinstance(result, dict)
        assert "passed" in result
        assert isinstance(result["reasoning"], str)

    def test_stream_error_recovery(self, ollama_available):
        client = OllamaClient(max_tokens=5)
        result = client.generate("Count from 1 to 100")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_custom_model_config(self, ollama_available):
        client = OllamaClient(model="gemma4")
        result = client.generate("Say yes")
        assert isinstance(result, str)
        assert len(result) > 0


class TestOllamaExceptions:
    def test_connection_error_is_ollama_error(self):
        assert issubclass(OllamaConnectionError, OllamaError)

    def test_model_error_is_ollama_error(self):
        assert issubclass(OllamaModelError, OllamaError)

    def test_stream_error_is_ollama_error(self):
        assert issubclass(OllamaStreamError, OllamaError)

    def test_connection_error_includes_host_port_timeout(self):
        err = OllamaConnectionError("http://localhost", 11434, 30.0)
        msg = str(err)
        assert "localhost:11434" in msg
        assert "30" in msg

    def test_model_error_includes_model_name(self):
        err = OllamaModelError("nonexistent-model")
        assert "nonexistent-model" in str(err)

    def test_stream_error_includes_partial_text(self):
        err = OllamaStreamError("partial response here")
        assert "partial response here" in str(err)
