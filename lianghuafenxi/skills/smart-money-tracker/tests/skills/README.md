# Skill Testing Framework

Fast, deterministic tests for skill structure and contracts. Slower, probabilistic tests for agent behavior quality.

## Structure

```
src/skills_testing/        # Python package with test helpers
├── __init__.py
├── models.py              # Pydantic models: SkillContract, SkillMetadata, ValidationResult
├── skill_loader.py        # Parse YAML frontmatter from SKILL.md
├── agent_simulator.py     # Mock agent state machine
├── trace_validator.py     # Compare traces to expected patterns
├── eval_runner.py         # Orchestrate evals (deterministic + LLM judge)
├── regression_tracker.py  # Compare results across runs
└── report_generator.py    # Markdown + JUnit XML reports

tests/skills/
├── conftest.py              # Pytest fixtures
├── unit/                    # Fast schema validation tests
│   └── test_skill_schema.py
├── integration/             # Agent simulation + contract tests
│   └── test_agent_simulation.py
├── e2e/                     # Real LLM evals (nightly)
│   └── test_llm_evals.py
├── scenarios/               # JSON scenario definitions
│   ├── test-driven-development.json
│   ├── debugging-and-error-recovery.json
│   └── incremental-implementation.json
├── pre-commit-hook.sh       # Schema validation pre-commit hook
├── example_contracts.md     # Example contracts for critical skills
└── README.md                # This file
```

## Running Tests

```bash
# Unit tests (fast, no LLM calls)
uv run pytest tests/skills/unit/ -v

# Integration tests (fast, deterministic)
uv run pytest tests/skills/integration/ -v

# E2E tests (deterministic only, no LLM)
uv run pytest tests/skills/e2e/ -v -k "not llm_judge"

# Full suite (unit + integration + e2e deterministic)
uv run pytest tests/skills/ -v -k "not llm_judge"

# Real LLM evals (slow, requires API key)
export LLM_API_KEY=sk-...
uv run pytest tests/skills/e2e/ -v -k "llm_judge"
```

## Adding New Scenarios

1. Create a JSON file in `tests/skills/scenarios/{skill-name}.json`
2. Follow the existing schema:
   ```json
   [
     {
       "name": "scenario_name",
       "description": "What this scenario tests",
       "user_prompt": "The user input",
       "expected_behavior": "What the agent should do",
       "steps": [
         {"tool": "bash", "args": {"command": "run tests"}},
         {"tool": "edit", "args": {"action": "fix code"}}
       ],
       "expected": {
         "expected_tools": ["bash", "edit"],
         "forbidden_tools": ["dangerous_tool"],
         "min_tool_calls": 2,
         "max_tool_calls": 5
       }
     }
   ]
   ```
3. Add integration tests in `tests/skills/integration/test_agent_simulation.py`

## Adding Skill Contracts

Edit a skill's YAML frontmatter in `/home/agent/.config/opencode/skills/{skill}/SKILL.md`:

```yaml
---
name: my-skill
description: "..."
contracts:
  required_sections: [overview, when_to_use, verification]
  required_tools: [bash, edit]
  forbidden_patterns: ["as any", "@ts-ignore"]
  verification_required: true
---
```

Contracts are optional. Skills without contracts are loaded but not contract-tested.

## CI Integration

- **PRs**: Unit + integration tests run on every PR (`.github/workflows/skill-tests.yml`)
- **Nightly**: Real LLM evals run at 2 AM UTC (`.github/workflows/nightly-llm-evals.yml`)
- **Pre-commit**: Schema validation runs before each commit (`tests/skills/pre-commit-hook.sh`)

To install the pre-commit hook:
```bash
ln -s ../../tests/skills/pre-commit-hook.sh .git/hooks/pre-commit
```

## Budget Enforcement

Real LLM evals enforce a daily budget (default $10). Configure via:
```bash
export EVAL_BUDGET_USD=5.00
```

When budget is exceeded, LLM evals are skipped (not failed).

## Reports

Eval runs generate:
- Markdown reports: `tests/skills/reports/report_{run_id}.md`
- JUnit XML: `tests/skills/reports/junit_{run_id}.xml`
- Baselines: `tests/skills/baselines/`
