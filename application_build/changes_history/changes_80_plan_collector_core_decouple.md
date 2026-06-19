---
id: 80
title: PLAN — staged core.py decouple so data collectors can be split into data_sources.py
date: 2026-06-17 22:50 KST
agent: Claude (Opus 4.8)
area: [refactor-plan]
status: plan
files:
  - (none yet — execution deferred to a future session, per user)
---

> This is a **plan only** (Tier-L, per CLAUDE.md §3). The user chose to defer execution.
> changes_79 established WHY a verbatim collector move is unsafe (shared KIS infra used in 38+
> sites, shared `_afetch`, mutable caches) and built `scripts/api_smoke.py` as the gate for this.

## Goal
Move the data collectors out of `scripts/market_dashboard3_realtime.py` into
`scripts/data_sources.py`, WITHOUT circular imports or shared-state divergence, by first
extracting the shared infrastructure they depend on into a leaf module `scripts/core.py`.

## Target module DAG (no cycles)
```
core.py          (leaf: shared infra + foundational config + mutable caches/locks)
  ▲      ▲
  │      │
pure_helpers.py  data_sources.py   (collectors; imports core + pure_helpers)
  ▲      ▲            ▲
  └──────┴────────────┘
        market_dashboard3_realtime.py  (imports core, pure_helpers, ui_templates, data_sources)
```

## Step 1 — `core.py`: shared infra (do first, gate, commit)
Move (byte-exact, explicit re-import into main) the app's shared spine:
- **KIS auth/infra:** `_kis_keys`, `_kis_token`, `_rt_kis_get`, `_rtf`.
- **Shared async fetcher:** `_afetch` (+ whatever IT closes over — compute its closure first).
- **Mutable shared state:** `_KIS_TOKEN`, `_FMP_CACHE`, `_GMAC_CACHE`, `_OV_CACHE`,
  `_POLY_GROUPED_CACHE` and the locks `_KIS_LOCK`, `_RLOCK`, `_TPE`.
  ⚠ These must be mutated **in place** (never reassigned). Verify none are reassigned via `global`
  (current scan: only `_MARKET_SNAPSHOT`/`_PLOTLY_JS_CACHE` are — keep those in main).
- **Foundational config:** `_CACHE_DIR`, `_KIS_BASE`, `_KIS_ENV_FILE`, `_KIS_TOKEN_FILE`,
  `_FMP_BASE`, `_GMAC_SPEC`, `_GMAC_TTL`, KIS TTLs.
- main: `from core import (…explicit names…)` near the top (BEFORE any module-level use, e.g.
  `_SNAPSHOT_FILE = _CACHE_DIR/…`). `core.py` imports only stdlib + httpx + `market_intel` Fetcher.
- **Gate:** `py_compile` → `uv run scripts/smoke_check.py` → `uv run scripts/api_smoke.py`
  → `uv run --with pytest … pytest tests/test_core_functions.py` → live preview boot. Roll back on red.

## Step 2 — `data_sources.py`: the collectors (after Step 1 is green)
Move the overseas/global collectors: `_finnhub_quote`, `_fmp_get`, `_fmp_one`, `_fnum`, `_fred_one`,
`_polygon_grouped_one`, `_get_overseas_financials`, `_get_analyst_view`, `_get_valuation_peers`,
`_get_price_technicals`, `_global_macro_snapshot`, `_gmac_idx_one`, `_gmac_list_one`, `_ov_chart`.
- `data_sources.py` does `from core import *`-equivalent (explicit) + `from pure_helpers import …`.
- main: `from data_sources import (…)` (re-export; collectors are called from ~12 external sites).
- Same gate sequence as Step 1.
- Consider a second module later for KR collectors (KIS/DART/Naver/KRX) — bigger, do separately.

## Step 3 — build + docs sync (§12)
- Add `core`, `data_sources` to `application_build/market_dashboard.spec` `hiddenimports` (trap #40).
- `python3 scripts/gen_codemap.py`; update root `CLAUDE.md` §0 + `_STATUS.md` + write `changes_81`.
- `cd application_build && ./build.sh` once to confirm the frozen .app still launches.

## Hard rules / traps for the executor
- **Move verbatim** (ast source-slice like changes_77/78's throwaway scripts). Do NOT hand-retype or
  add lazy imports inside moved functions (that changes behavior → defeats byte-exact verification).
- **Explicit imports only** — `from X import *` skips underscore names; ALL these names start with `_`.
- Re-run BOTH gates after EACH step; the api_smoke gate is what proves no broken collector name refs.
- If a moved function turns out to reference a main-only global you can't cleanly move, STOP and
  reduce scope rather than introduce a circular/lazy-import hack.
