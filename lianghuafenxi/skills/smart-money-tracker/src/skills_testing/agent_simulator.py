"""Agent simulator - state machine that parses skill instructions into decision trees."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from skills_testing.models import SkillMetadata


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class SimulationTrace(BaseModel):
    skill_name: str
    scenario_name: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AgentSimulator:
    """State machine that simulates an agent following skill instructions."""

    def __init__(self, metadata: SkillMetadata, body: str):
        self.metadata = metadata
        self.body = body
        self.sections = self._parse_sections(body)

    def _parse_sections(self, body: str) -> dict[str, str]:
        sections = {}
        current_section = None
        current_content = []
        for line in body.split("\n"):
            match = re.match(r"^##\s+(.+)$", line)
            if match:
                if current_section:
                    sections[current_section.lower().replace(" ", "_")] = "\n".join(current_content).strip()
                current_section = match.group(1)
                current_content = []
            else:
                current_content.append(line)
        if current_section:
            sections[current_section.lower().replace(" ", "_")] = "\n".join(current_content).strip()
        return sections

    def simulate(self, scenario: dict[str, Any]) -> SimulationTrace:
        trace = SimulationTrace(skill_name=self.metadata.name, scenario_name=scenario.get("name", "unknown"))
        steps = scenario.get("steps", [])
        for step in steps:
            tool_name = step.get("tool")
            if tool_name:
                trace.tool_calls.append(ToolCall(tool_name=tool_name, arguments=step.get("args", {})))
            if step.get("expect_error"):
                trace.errors.append(step.get("error_message", "Expected error"))
        return trace


class ScenarioLoader:
    """Load scenario definitions from JSON files."""

    def __init__(self, scenarios_dir: Path):
        self.scenarios_dir = scenarios_dir

    def load_scenarios(self, skill_name: str) -> list[dict[str, Any]]:
        scenario_file = self.scenarios_dir / f"{skill_name}.json"
        if not scenario_file.exists():
            return []
        data = json.loads(scenario_file.read_text())
        return data if isinstance(data, list) else [data]

    def load_all_scenarios(self) -> dict[str, list[dict[str, Any]]]:
        scenarios = {}
        for file in self.scenarios_dir.glob("*.json"):
            skill_name = file.stem
            scenarios[skill_name] = self.load_scenarios(skill_name)
        return scenarios
