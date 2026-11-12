# A-Stockit Documentation

A-Stockit is a bundle-first A-share skill library for agent frameworks.

This documentation is organized around routing and execution, not around marketing categories.

## Bundle Surfaces

The bundle root contains five important surfaces:

- `index.md` for bundle positioning, routing defaults, and execution boundaries
- `_registry/` for machine-readable skill and bundle metadata
- `<skill>/SKILL.md` for the public operational contract of each skill
- `_docs/` for readable explanations and extension guidance
- `_src/` for shared Python implementation support

## Reading Order

If you are unsure where to start:

1. Read `index.md`
2. Read `_registry/bundle.json`
3. Read `_registry/skills.json`
4. Read `_docs/index.md` (this file)
5. Read `_docs/skills/index.md` for skill catalog
6. Read the selected `<skill>/SKILL.md` for detailed skill documentation
7. Read `_docs/contracts/runtime-interface.md` if execution semantics are still unclear

**Note:** Individual skill documentation is maintained in each skill's `SKILL.md` file (`<bundle-root>/<skill>/SKILL.md`), not in `_docs/skills/`. The `_docs/skills/index.md` provides a catalog and categorization of all skills.

## Code-Backed vs Workflow-Only

The docs assume two classes of skills:

- code-backed skills with local `run.py` executors
- workflow-only skills that define stable routing and composition contracts without promising a dedicated executor

Both classes are first-class. They differ in execution depth, not in public visibility.

## Quant Workflow

The bundle is documented as an end-to-end research workflow as well as a skill catalog.

Key references:

- `authoring/evidence-sufficiency.md` for claim discipline
- `authoring/quant-workflow-framework.md` for the seven-stage quantitative workflow
- `authoring/workflow-integration-guide.md` for mapping workflow stages onto public skills

## Artifact and Session Rules

The bundle assumes that some skills produce durable outputs and some skills may reuse bounded session context.

Current rules:

- artifact-producing skills should write named outputs under the configured runtime root
- downstream review skills should prefer stored artifacts over regeneration
- code-backed skills may reuse the last symbol in the same execution context only where their contract says so
- optional enrichments and notifications are fail-open rather than hard blockers

## Sections

- [skills/index.md](./skills/index.md) - Complete catalog of all 25 skills
- [audit/index.md](./audit/index.md) - Skill enhancement audit documentation
- [runtime/index.md](./runtime/index.md) - Runtime configuration and execution
- [contracts/index.md](./contracts/index.md) - Interface contracts and protocols
- [authoring/index.md](./authoring/index.md) - Skill authoring and workflow guidance
