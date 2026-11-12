# Reference Adaptations

This note records which external patterns have already been adapted into the
bundle, and which remain intentionally deferred.

## Implemented now

- news-intel planning, ranking, and deterministic summarization
  Backed by `_src/research/news.py`.

- richer indicator layer and research packet assembly
  Backed by `_src/research/indicators.py` and `_src/research/analysis.py`.

- bundle-local artifact persistence under `_artifacts/`
  Backed by `_src/core/storage.py`.

- structured strategy preset registry
  Backed by `_registry/strategies.json` plus `_src/strategies/`.

- deterministic strategy-driven backtest engine
  Backed by `_src/backtest/engine.py` and `_src/backtest/models.py`.

- lightweight paper-trading ledger
  Backed by `_src/research/paper.py`, with storage under `_artifacts/paper/`.

- model-capability recommendation heuristics
  Backed by `_src/research/model_advisor.py`.

## Deferred

- richer watchlist import parsing and symbol name resolution
- fuller history/report query surfaces over artifact manifests
- deeper market/news provider adapters
- optional semantic reranking for news relevance

## Design Intent

- `_src/core` remains runtime and persistence glue.
- `_src/market` remains market-data normalization and compact scoring.
- `_src/strategies` holds reusable strategy presets and deterministic signal rules.
- `_src/backtest` holds simulation logic and metrics.
- `_src/research` holds cross-cutting higher-level packet/intel/advisory helpers that
  do not fit cleanly into `market`, `strategies`, or `backtest`.
