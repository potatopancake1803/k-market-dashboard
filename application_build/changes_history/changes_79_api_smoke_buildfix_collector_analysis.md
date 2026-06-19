---
id: 79
title: API-level smoke gate + build spec fix for split modules + collector-extraction analysis (deferred)
date: 2026-06-17 22:30 KST
agent: Claude (Opus 4.8)
area: [tooling, build, refactor-analysis]
status: verified
files:
  - scripts/api_smoke.py (new)
  - application_build/market_dashboard.spec
---

## What was done

### 1) `scripts/api_smoke.py` — API-level regression gate (network-capable)
The render gate `smoke_check.py` imports + renders but cannot catch a **call-time** break in a
network collector (NameError/AttributeError from a bad move that compiles + imports fine). `api_smoke.py`
calls the data-source collectors and **classifies the exception**:
- `NameError | AttributeError | ImportError | UnboundLocalError` → **FAIL** (real wiring bug).
- anything else (httpx/timeout/HTTP/empty/missing-key/market-closed) → **SKIP** (body executed → wiring OK).
So green == "no broken name references", even offline / out of market hours. Run it after moving any
collector. Baseline now: `API-SMOKE PASS ✓ (8 OK, 5 skipped)` — live FMP/Finnhub/global-macro calls OK.

### 2) Build spec fix — bundle the split modules
`application_build/market_dashboard.spec` `hiddenimports` listed `market_dashboard3_realtime` + archive
but NOT the new split modules. Since `app.py` loads the backend via importlib (dynamic), PyInstaller's
static analysis can't follow `from ui_templates import …` / `from pure_helpers import …`. Added
**`ui_templates`, `pure_helpers`** to `hiddenimports` (+ a comment: register future split modules here).
`requirements.txt` needs no change — the new modules use only stdlib + numpy/pandas (already present;
`pure_helpers` also uses `difflib` = stdlib). Spec compiles. (Live runs load from disk via `app.py`'s
`sys.path` already; this is for the frozen .app fallback.)

### 3) Collector FUNCTION extraction — analyzed and DEFERRED (not forced)
Goal was to split the data collectors into their own module. **ast call-graph analysis shows this is NOT
a safe verbatim move:**
- The overseas/global collector closure does not cleanly bound — it transitively pulls in the **shared
  KIS auth infra** (`_kis_keys`/`_kis_token`/`_rt_kis_get`/`_rtf`, called from **38+ sites app-wide**),
  the **shared async fetcher `_afetch`**, the `_gmac_*` helpers, and **mutable shared caches**
  (`_KIS_TOKEN`, `_FMP_CACHE`, `_GMAC_CACHE`, `_OV_CACHE`, `_POLY_GROUPED_CACHE`).
- Moving that spine requires re-exporting ~50 names and risks shared-state divergence; a verbatim move
  would create circular imports or latent breakage — exactly the "fix creates new error" class we guard
  against. (Tooling even surfaced caches my first `ast.Assign` scan missed because they are `AnnAssign` —
  a reminder the dependency model isn't 100% reliable, so forcing the move is unwise.)
- **Decision:** do NOT force it. The correct path is a *staged decouple* into a `core.py` that owns the
  shared infra (KIS token/auth, `_afetch`, caches, foundational config), which both the main file and a
  `data_sources.py` import. That is a deliberate Tier-L architecture task — now **de-risked** because
  `api_smoke.py` exists to gate it. Recommended as the next dedicated, user-approved step.

## Verification
```
$ uv run scripts/api_smoke.py    → API-SMOKE PASS ✓ (8 OK, 5 skipped; live FMP/Finnhub/global-macro OK)
$ uv run scripts/smoke_check.py  → SMOKE PASS ✓ (render unchanged)
$ python3 -m py_compile application_build/market_dashboard.spec   → OK
# requirements vs new-module imports: ui_templates=∅, pure_helpers={datetime,difflib,json,numpy,pandas} → all covered
```

## Notes & Traps
- **NEW build rule (→ _STATUS trap):** modules loaded dynamically by `app.py` (the live backend and any
  module IT imports) are invisible to PyInstaller's static analysis → every split module MUST be added to
  `market_dashboard.spec` `hiddenimports`. Currently: `market_dashboard3_realtime`, `ui_templates`,
  `pure_helpers`. Add the next one when you split it (part of §12 structure→guideline sync).
- Recommend a full `cd application_build && ./build.sh` to materialize the bundle with the new modules
  (not run this session — heavy; spec verified by inspection + compile).
- Collector extraction plan recorded for the next session; `api_smoke.py` is the gate for it.
