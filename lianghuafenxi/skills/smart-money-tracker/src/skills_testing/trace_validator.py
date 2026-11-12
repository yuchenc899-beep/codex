"""Trace validator - compare generated traces against expected patterns."""

from __future__ import annotations

from typing import Any

from skills_testing.agent_simulator import SimulationTrace


class TraceValidator:
    """Validate simulation traces against expected patterns."""

    def __init__(self, expected: dict[str, Any]):
        self.expected = expected

    def validate(self, trace: SimulationTrace) -> dict[str, Any]:
        errors = []
        warnings = []

        expected_tools = self.expected.get("expected_tools", [])
        forbidden_tools = self.expected.get("forbidden_tools", [])
        actual_tools = [tc.tool_name for tc in trace.tool_calls]

        for tool in expected_tools:
            if tool not in actual_tools:
                errors.append(f"Missing required tool: {tool}")

        for tool in forbidden_tools:
            if tool in actual_tools:
                errors.append(f"Forbidden tool used: {tool}")

        if "max_tool_calls" in self.expected:
            if len(trace.tool_calls) > self.expected["max_tool_calls"]:
                errors.append(f"Too many tool calls: {len(trace.tool_calls)} > {self.expected['max_tool_calls']}")

        if "min_tool_calls" in self.expected:
            if len(trace.tool_calls) < self.expected["min_tool_calls"]:
                errors.append(f"Too few tool calls: {len(trace.tool_calls)} < {self.expected['min_tool_calls']}")

        passed = not errors
        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "actual_tools": actual_tools,
            "tool_call_count": len(trace.tool_calls),
        }
