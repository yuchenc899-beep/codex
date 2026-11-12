"""Ollama LLM client for skill evaluation.

Connects to local Ollama's /api/generate endpoint using streaming NDJSON
protocol. Implements the EvalRunner llm_client callable interface."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import requests

from skills_testing.agent_simulator import SimulationTrace

logger = logging.getLogger(__name__)

# Default Ollama port — user's curl output shows port 11434
DEFAULT_HOST = "http://localhost"
DEFAULT_PORT = 11434
DEFAULT_MODEL = "gemma4"
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_TOKENS = 512


class OllamaError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Ollama server unreachable."""

    def __init__(self, host: str, port: int, timeout: float):
        self.host = host
        self.port = port
        self.timeout = timeout
        super().__init__(
            f"Ollama connection refused at {host}:{port} "
            f"(timeout {timeout:.0f}s). Is Ollama running?"
        )


class OllamaModelError(OllamaError):
    """Requested model not found in Ollama."""

    def __init__(self, model: str):
        self.model = model
        super().__init__(
            f"Model '{model}' not found. "
            f"Pull it with: ollama pull {model}"
        )


class OllamaStreamError(OllamaError):
    """Stream interrupted before completion."""

    def __init__(self, partial_text: str):
        self.partial_text = partial_text
        super().__init__(
            f"Ollama stream interrupted. Partial response: "
            f"{partial_text[:200]}..."
        )


@dataclass
class OllamaClient:
    """Client for Ollama's streaming /api/generate endpoint."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    model: str = DEFAULT_MODEL
    timeout: float = DEFAULT_TIMEOUT
    max_tokens: int = DEFAULT_MAX_TOKENS

    @property
    def base_url(self) -> str:
        return f"{self.host}:{self.port}"

    def health_check(self) -> bool:
        """Check if Ollama is reachable. Returns True if server responds."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags", timeout=5.0
            )
            return resp.status_code == 200
        except requests.ConnectionError:
            return False

    def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the complete generated text.

        Uses streaming NDJSON protocol: reads one JSON object per line,
        accumulates ``response`` fields until ``done: true``.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": self.max_tokens,
            },
        }
        url = f"{self.base_url}/api/generate"

        try:
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.ConnectionError:
            raise OllamaConnectionError(self.host, self.port, self.timeout)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                raise OllamaModelError(self.model)
            raise

        return self._read_stream(response)

    def _read_stream(self, response: requests.Response) -> str:
        """Read NDJSON stream, accumulating 'response' fields."""
        accumulated: list[str] = []
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Bad JSON line from Ollama: %r", line[:100])
                    continue

                chunk = obj.get("response", "")
                if chunk:
                    accumulated.append(chunk)

                if obj.get("done", False):
                    return "".join(accumulated)

            partial = "".join(accumulated)
            raise OllamaStreamError(partial)

        except requests.RequestException as e:
            partial = "".join(accumulated)
            if partial:
                raise OllamaStreamError(partial)
            raise OllamaConnectionError(self.host, self.port, self.timeout) from e


def ollama_judge(
    skill_name: str,
    scenario: dict[str, Any],
    trace: SimulationTrace,
    *,
    client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Judge callable conforming to EvalRunner llm_client interface.

    Args:
        skill_name: Name of the skill being evaluated.
        scenario: Scenario dict with ``name``, ``description``, ``expected``.
        trace: Simulation trace from the agent simulation run.
        client: Pre-configured OllamaClient. Creates default if None.

    Returns:
        Dict with keys: ``passed``, ``cost``, ``score``, ``reasoning``.
    """
    if client is None:
        client = OllamaClient()

    prompt = _build_judge_prompt(skill_name, scenario, trace)

    try:
        raw_output = client.generate(prompt)
    except OllamaConnectionError:
        # Graceful fallback — skip eval, report as not passed
        return {
            "passed": False,
            "cost": 0.0,
            "score": None,
            "reasoning": "Ollama not available — skipping LLM eval",
        }
    except OllamaModelError as e:
        return {
            "passed": False,
            "cost": 0.0,
            "score": None,
            "reasoning": str(e),
        }
    except OllamaStreamError as e:
        return {
            "passed": False,
            "cost": 0.0,
            "score": None,
            "reasoning": str(e),
        }

    return _parse_judgment(raw_output)


def _build_judge_prompt(
    skill_name: str,
    scenario: dict[str, Any],
    trace: SimulationTrace,
) -> str:
    """Build an eval prompt that includes skill context and trace data."""
    expected = scenario.get("expected", {})
    tool_steps = "\n".join(
        f"  [{tc.tool_name}] args={tc.arguments}"
        for tc in trace.tool_calls
    )
    errors_text = "\n".join(f"  Error: {e}" for e in trace.errors)

    prompt = f"""You are a skill testing judge. Evaluate whether the agent simulation
correctly followed the skill's workflow.

Skill: {skill_name}
Scenario: {scenario.get('name', 'unknown')}
Description: {scenario.get('description', '')}

Expected behaviors:
{json.dumps(expected, indent=2)}

Agent simulation trace:
Tools called:
{tool_steps}

Errors:
{errors_text if errors_text else "  (none)"}

Judge the trace against the expected behaviors. Output ONLY a JSON object:
{{"passed": true/false, "score": 0-100, "reasoning": "explanation"}}
"""
    return prompt


def _parse_judgment(raw_output: str) -> dict[str, Any]:
    """Parse LLM output into judgment dict. Tolerant of imperfect JSON."""
    text = raw_output.strip()
    json_start = text.find("{")
    json_end = text.rfind("}")

    if json_start == -1 or json_end == -1:
        return {
            "passed": False,
            "cost": 0.0,
            "score": None,
            "reasoning": f"Could not parse JSON from response: {text[:200]}",
        }

    json_str = text[json_start : json_end + 1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return {
            "passed": False,
            "cost": 0.0,
            "score": None,
            "reasoning": f"Invalid JSON in response: {json_str[:200]}",
        }

    return {
        "passed": bool(data.get("passed", False)),
        "cost": 0.0,  # Local Ollama has zero cost
        "score": data.get("score"),
        "reasoning": data.get("reasoning", ""),
    }
