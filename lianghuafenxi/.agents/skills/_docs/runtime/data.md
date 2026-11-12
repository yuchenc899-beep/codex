# Data And Analysis

Shared A-share runtime logic covers the reusable support layer for the bundle’s stage-2 to stage-5 workflows.

Core capabilities:

- CSV and AkShare ingestion
- field normalization across Chinese and English column names
- board classification and limit-band logic
- rolling indicators and market-state snapshots
- watchlist import and normalization
- screening and decision dashboards
- fail-open fundamental context
- headline ranking and event tagging
- research-packet persistence
- retrospective evaluation and deterministic strategy backtests

Important boundary:

- these runtime helpers support the public skills
- they do not replace the public skill contracts
- a code-backed skill may define a broader process than the helper fully automates, but the contract must state that explicitly

Relevant implementation areas:

- `_src/market/data.py` for one-symbol data loading, normalization, and enrichment
- `_src/market/capabilities.py` for market-state scoring, decision packets, and baseline strategy planning
- `_src/market/dashboards.py` and `_src/market/watchlists.py` for universe intake and batch triage
- `_src/market/fundamentals.py` for fail-open non-price context
- `_src/research/analysis.py`, `_src/research/news.py`, and `_src/research/evaluation.py` for research packets, event blocks, and retrospective review
- `_src/backtest/engine.py` and `_src/research/paper.py` for deterministic backtesting and paper-book bookkeeping

See also:

- `_docs/authoring/quant-workflow-framework.md`
- `_docs/authoring/workflow-integration-guide.md`
- `_docs/contracts/runtime-interface.md`
