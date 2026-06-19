---
id: 78
title: Extract self-contained pure helpers → scripts/pure_helpers.py (quant/risk math, format, SSE)
date: 2026-06-17 21:10 KST
agent: Claude (Opus 4.8)
area: [refactor, modularity]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - scripts/pure_helpers.py (new)
  - docs/CODEMAP.md (regenerated)
---

## What was done
Continued the modularization (next safe slice after the changes_77 template split). Extracted
**11 genuinely pure, side-effect-free functions** into `scripts/pure_helpers.py`:
`_risk_stats`, `_clean_closes`, `_clean_ohlc`, `_bt_signal`, `_cu`, `_krx_won`, `_sse_done`,
`_sse_failed`, `_sse_progress`, `_news_similar`, `_is_us_dst`.
Main file does `from pure_helpers import (...)` (re-export) so every call site is unchanged.

## How it was done — why this set was safe
- ast call-graph analysis proved these 11 are a **closed cluster**: they reference **no module-level
  globals**, call **no non-moved functions** (verified: "calls to NON-moved module funcs: []"), and
  need only `numpy`, `pandas`, `datetime`, `json`.
- Deliberately EXCLUDED tempting-but-impure neighbours: `detect_type` (calls archive `etf`/`company`
  data loaders), `_bt_run` (async, calls `_ai_stock_name` → network). Moving those would couple
  modules / risk latent NameErrors the smoke gate can't catch.
- Extracted **byte-exact** (ast source slice) by a throwaway script (deleted) + pre-edit backup
  (deleted after verification). Main: 7,946 → 7,813 lines. `pure_helpers.py` = 176 lines.

## Verification
```
$ python3 -m py_compile scripts/pure_helpers.py scripts/market_dashboard3_realtime.py   # OK
$ uv run scripts/smoke_check.py
  · import backend OK · test client OK · 10 routes 200 · golden compared (9 routes)
  SMOKE PASS ✓                                   ← rendering byte-identical
$ uv run --with pytest --with numpy --with pandas ... pytest tests/test_core_functions.py -q
  26 passed in 13.92s                            ← the moved fns are called via md.* and behave identically
$ python3 scripts/gen_codemap.py                 # regenerated (line numbers shifted)
```
Both the render gate AND the unit suite (which exercises `_risk_stats`/`_clean_closes`/`_cu`/
`_krx_won`/`_sse_*` through `md.<name>`) pass → behaviour is provably unchanged.

## Notes & Traps
- **`scripts/pure_helpers.py` must stay PURE** (no module globals, no I/O, no Flask). It is the home
  for deterministic input→output helpers and the natural place to grow unit tests. Anything needing
  network/state stays in the main file.
- `tests/test_core_functions.py` imports `market_dashboard3_realtime as md` and calls `md._risk_stats`
  etc.; the re-export keeps that working with no test change. Run with the test's PEP723 deps
  (numpy/pandas/… ) or it errors on `import numpy` in a bare env (not a code bug).
- Running tally of the split: main 13,166 → **7,813** (−41%); markup in `ui_templates.py` (5,269),
  pure helpers in `pure_helpers.py` (176).
- **Next Tier-L (not done — needs approval + broader gate):** extracting the data collectors
  (Naver/KIS/DART/KRX/Finnhub/FMP/Polygon/FRED) is the big remaining mass, but they do network I/O
  that the current smoke gate cannot exercise → a latent NameError after a move wouldn't be caught.
  Do that only after adding network-capable API smoke checks (or in small, reviewed steps).
