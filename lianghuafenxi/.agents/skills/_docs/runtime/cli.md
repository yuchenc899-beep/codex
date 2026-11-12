# Skill Support Scripts

A-Stockit no longer uses one unified CLI as its public command surface.

Instead:

- reusable implementation support lives under `src/`
- code-backed skills may ship a local `run.py` beside `SKILL.md`
- workflow-only skills may have no local script yet

Examples:

- `market-brief/run.py`
- `watchlist-import/run.py`
- `decision-dashboard/run.py`
