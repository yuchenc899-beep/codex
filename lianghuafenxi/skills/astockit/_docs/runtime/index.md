# Shared Source

The `_src/` tree is the shared implementation area underneath A-Stockit skills.

It is not the public API. The public API is the skill layer. `_src/` exists to prevent duplicated implementation across multiple skills.

## Internal Structure

- `_src/core/` for runtime, config, registry, persistence, and local script support
- `_src/market/` for A-share market logic, scoring, recap, dashboards, and watchlist parsing
- `_src/integrations/` for optional outbound delivery helpers
- `_src/research/` for richer packet assembly, evaluation, model-advice, and paper-ledger helpers

## What Belongs Here

Put code in `_src/` only when it is shared by multiple skills or when a skill-local runner would otherwise duplicate non-trivial logic.

Do not put code here just because it is “backend code.” If it only serves one skill and is unlikely to be reused, it can stay with that skill.

## Shared Runtime Semantics

The shared implementation layer is also where bundle-wide execution behavior lives.

Important semantics:

- some skills write durable artifacts for later reuse
- some skills may reuse session-local symbol context
- optional enrichments and outbound notifications are fail-open
- error recovery infrastructure supports autonomous fix-everything meta-skill

These rules should be reflected in the corresponding skill contracts rather than hidden only in code.

## Primary References

- [cli.md](cli.md)
- [data.md](data.md)
- [feishu.md](feishu.md)
- [registry.md](registry.md)
