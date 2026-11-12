#!/usr/bin/env bash
set -euo pipefail

echo "Validating skill schema..."
uv run pytest tests/skills/unit/test_skill_schema.py -q --tb=short

echo "Checking skill contracts..."
uv run pytest tests/skills/integration/test_agent_simulation.py -q --tb=short

echo "All skill validations passed."
