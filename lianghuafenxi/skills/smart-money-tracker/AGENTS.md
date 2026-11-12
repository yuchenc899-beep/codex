# Agent Skills

## Testing Framework

This project includes a comprehensive skill testing framework in `tests/skills/`.

### Running Tests

```bash
# Fast unit + integration tests (run before commits)
uv run pytest tests/skills/unit/ tests/skills/integration/ -v

# Full deterministic suite
uv run pytest tests/skills/ -v -k "not llm_judge"
```

### Test Structure

- **Unit tests**: Validate skill YAML frontmatter, schema, and contracts
- **Integration tests**: Simulate agent behavior and verify contract compliance
- **E2E tests**: Real LLM evaluations (run nightly, not on PRs)

See `tests/skills/README.md` for full documentation on adding scenarios and contracts.
