# Skill Catalog

All 25 A-Stockit skills have been systematically enhanced to institutional-grade quantitative finance standards. Each skill includes comprehensive technical specifications, quality gates, A-share market constraints, and workflow integration guidance.

**For detailed skill documentation, see each skill's `SKILL.md` file in its respective directory: `<bundle-root>/<skill>/SKILL.md`**

## Skill Categories

### Core Research & Analysis (7 skills)
- **analysis** - Institutional thesis discipline + quantitative strategy design
- **market-brief** - Default one-symbol entry point with composed layers
- **market-analyze** - Descriptive market state interpretation
- **technical-scan** - Technical-only chart analysis
- **fundamental-context** - Fundamental data collection with fail-open semantics
- **news-intel** - News intelligence ranking and catalyst identification
- **stock-data** - Structured research packet assembly

### Decision & Execution (3 skills)
- **decision-support** - Risk assessment and position sizing
- **strategy-design** - Execution planning and trade structure
- **paper-trading** - Simulated trading and performance tracking

### Backtesting & Evaluation (2 skills)
- **backtest-evaluator** - Retrospective performance evaluation
- **analysis-history** - Historical analysis tracking and comparison

### Artifact & History Management (2 skills)
- **reports** - Artifact retrieval and restatement
- **strategy-chat** - Multi-turn workflow continuity

### Data & Infrastructure (4 skills)
- **market-data** - Data quality assessment and normalization
- **data-sync** - Data freshness management and provider orchestration
- **session-status** - Runtime monitoring and artifact inventory
- **model-capability-advisor** - Model selection guidance

### Screening & Batch Operations (4 skills)
- **market-screen** - Universe screening and ranking
- **decision-dashboard** - Batch decision support
- **watchlist-import** - Symbol normalization and validation
- **watchlist** - Watchlist management and organization

### Utilities (2 skills)
- **market-recap** - Market review template generation
- **feishu-notify** - Fail-open notification delivery

### Special Meta-Skills (1 skill)
- **fix-everything** - Autonomous error recovery for non-technical users

## Implementation Status

### Code-Backed Skills (24 skills)
Skills with local `run.py` executors that generate persisted artifacts.

### Workflow-Only Skills (1 skill)
Skills that compose other skills or provide workflow orchestration without dedicated executors.

## Related Documentation

- [Audit Summary](../audit/audit-summary.md) - Complete audit process and achievements
- [Quantitative Workflow Framework](../authoring/quant-workflow-framework.md) - Workflow stage definitions
- [Workflow Integration Guide](../authoring/workflow-integration-guide.md) - Skill composition patterns
