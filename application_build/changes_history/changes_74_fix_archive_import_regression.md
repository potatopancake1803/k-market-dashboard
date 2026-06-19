---
id: 74
title: Fix app-breaking import regression from changes_73 (archived builders' absolute sibling imports)
date: 2026-06-17 18:30 KST
agent: Claude (Opus 4.8)
area: [bugfix, packaging]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Added a 5-line `sys.path` shim at the top of `scripts/market_dashboard3_realtime.py`
  (immediately before `from archive import company_report_ver2 / etf_dashboard_ver2`) that
  inserts `scripts/archive/` onto `sys.path`. This makes the live builders' **absolute
  sibling imports** resolvable again.

## How it was done — root cause
- **changes_73 moved `company_report.py` and `etf_dashboard.py` from `scripts/` into
  `scripts/archive/`**, on the (incorrect) PHASE 1 finding that they were "not imported
  anywhere → safe to archive."
- They ARE imported — transitively by the **live** report builders:
  - `scripts/archive/company_report_ver2.py:59` → `from company_report import MARKET_MAP, _fmt_metric, _krx_snapshot, _pivot_trend, _won`
  - `scripts/archive/etf_dashboard_ver2.py` → `import etf_dashboard as base`
  These are **absolute** imports (not `from .company_report`). `scripts/archive/` has no
  `__init__.py` (namespace pkg), so submodule code still resolves absolute imports against
  `sys.path`. Before changes_73 the targets sat in `scripts/` (on `sys.path`) → resolved.
  After the move they were only in `scripts/archive/` (NOT on `sys.path`) → `ModuleNotFoundError`.
- Because the failing import is at module top of `market_dashboard3_realtime.py` (line ~78),
  **the entire backend failed to import** → app/server would not start at all. Both entry
  points were broken:
  - `uv run scripts/market_dashboard3_realtime.py` (direct, launch.json, preview)
  - `application_build/app.py` (`_load_live_module` via importlib — it only adds `scripts/`
    + project root to `sys.path`, not `scripts/archive/`).
- changes_73 was logged `status: verified` but the verification was `py_compile` (no import)
  + `pytest tests/test_core_functions.py` (which **stubs the archive modules** — trap #35 —
    so it never actually imports the real builders). This is exactly the
    "py_compile = verified" failure mode flagged in `TECH_REVIEW_2026-06-17.md` (#1/#2).

## Why the fix lives in the source (not app.py)
- Putting the shim in `market_dashboard3_realtime.py` fixes **every** entry point at once
  (direct script, app.py importlib load, preview, future tests) — single source of truth.
  It is idempotent (`if dir not in sys.path`).

## Verification
```
$ python3 -m py_compile scripts/market_dashboard3_realtime.py    # OK
# Preview MCP started the dashboard via .claude/launch.json (direct script):
#   BEFORE fix: ModuleNotFoundError: No module named 'company_report' (server failed to start)
#   AFTER fix:  "Server started successfully on port 8781" → landing rendered, AI widget rendered
```
Observed live: landing page renders, floating AI widget renders, no console errors.

## Notes & Traps
- **NEW TRAP (added to _STATUS.md):** the live report builders in `scripts/archive/`
  (`*_ver2.py`) import their non-`_ver2` siblings by **absolute name**. `scripts/archive/`
  must be on `sys.path`. Do not "clean up" by removing the shim or the sibling files.
- The proper long-term fix would be relative imports inside the `archive` package
  (`from .company_report import …`) + an `__init__.py`, OR moving the four files back to
  `scripts/`. Deferred — the shim is the minimal, safe, fully-verified fix for now.
- Lesson reinforced: a move/rename "cleanup" that touches anything on an import path MUST be
  verified by actually importing the top module (or starting the app), never by `py_compile`
  + stubbed unit tests alone.
