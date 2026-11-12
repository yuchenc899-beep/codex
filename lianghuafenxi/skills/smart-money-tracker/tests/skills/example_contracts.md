# Example Skill Contracts

These files show how to add contracts to the 5 critical skills.
Place these in the skill's YAML frontmatter (between the `---` markers).

## test-driven-development

```yaml
contracts:
  required_sections: [overview, when_to_use, the_tdd_cycle, verification]
  required_tools: [bash, edit]
  forbidden_patterns: ["as any", "@ts-ignore", "@ts-expect-error"]
  verification_required: true
```

## debugging-and-error-recovery

```yaml
contracts:
  required_sections: [overview, when_to_use, the_debugging_process, verification]
  required_tools: [bash, read, edit]
  forbidden_patterns: ["as any", "@ts-ignore"]
  verification_required: true
```

## incremental-implementation

```yaml
contracts:
  required_sections: [overview, when_to_use, implementation_strategy, verification]
  required_tools: [bash, edit]
  forbidden_patterns: ["as any", "@ts-expect-error"]
  verification_required: true
```

## code-review-and-quality

```yaml
contracts:
  required_sections: [overview, when_to_use, review_axes, verification]
  required_tools: [read, edit]
  forbidden_patterns: ["as any"]
  verification_required: true
```

## frontend-ui-engineering

```yaml
contracts:
  required_sections: [overview, when_to_use, design_principles, verification]
  required_tools: [read, edit]
  forbidden_patterns: ["as any", "@ts-ignore", "@ts-expect-error"]
  verification_required: true
```
