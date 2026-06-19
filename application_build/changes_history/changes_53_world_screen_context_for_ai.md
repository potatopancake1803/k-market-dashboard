---
id: 53
title: AI reads the 세계 시장 (world) screen — world-scope context + current-view plumbing; Gemini model routing re-verified
date: 2026-06-16 02:10 KST
agent: Claude (Opus 4.8)
files:
  - scripts/market_dashboard3_realtime.py
status: verified
---

## What was done
- **Bug:** On the 세계 시장 (world) page the AI answered "[현재 화면 데이터]가 비어 있으며…" because
  `_ask_context()` had **no handler for `scope=='world'`** (the floating widget posts `scope:'world'`), so the
  on-screen indices/marketmap were never given to the model.
- **Fix — world context.** New `_world_ai_text(view)` serializes the *currently displayed* world data
  (`_world_view(view)` → 지수 카드 + KPI 지표 + 종목 리스트 상위 20) into a compact text sheet. `_ask_context()`
  now routes `scope=='world'` → `_world_ai_text(view)` with `view ∈ {kr,us,global}` (default us).
- **Fix — current view plumbing.** The world page only knew its view client-side. `render()` now sets
  `window.__wview=view` (runs on load + every 국내/미국/글로벌 tab switch), and the injected
  `window.KMKT_ASK` setter was rewritten to `{scope:'world', id:(window.__wview||'us')}` so the AI gets the
  *exact* view the user is looking at.
- **작업(직전) re-verify — Gemini model routing.** Confirmed the dropdown-selected model is honored end-to-end:
  request `gemini_model` → server validates vs `_GEMINI_MODELS` → `meta.model` + answer header match.

## How it was done
- `_world_view()` returns `cards[{name,value,pct,dir,status}]`, `kpis[{name,value,pct,dir}]`,
  `list.rows[{name,price,pct,sector?,…}]`; `_world_ai_text` formats these with ▲▼ arrows. Reuses the existing
  30s `_WORLDVIEW_CACHE`, so opening the AI adds no extra network when the page is already loaded.
- Setter swap done as a post-build `_WORLD_HTML.replace(...)` right after `_inject_floating_ai`, matching the
  static string the injector emits.

## Verification
- `python3 -m py_compile` → **PY OK**.
- Headless (MARKET_PORT 8798, /__ping keepalive per trap #8, single invocation per trap #18),
  `POST /api/llm_ask {scope:world,id:us,question:"이 화면에 나오는 미국 시장 정보 해석해줘",provider:gemini}`:
  - **gemini-3.5-flash** → `meta.model=gemini-3.5-flash`, **answer 1360 chars**, opens
    *"…나스닥 종합지수가 3.07% 급등…"* — matches the on-screen 나스닥 +3.07%. **empty-complaint gone.** ✅
  - **gemini-2.5-flash** → `meta.model=gemini-2.5-flash`, answer 1239 chars, same screen-grounded read. ✅
  - Both used the changes_52 search-off fallback (grounding 429) yet still answered → screen data + gathered
    news drove the answer. Structured ①결론 ②근거 format (changes_52 작업3 addendum) present in output.
- Screen-reading + model routing both **verified live**.

## Notes & Traps
- Only `world` scope added here. `market`/`backtest` scopes still return empty `_ask_context` (the deterministic
  news agent still runs, so they aren't blind), but they don't yet serialize their own screen — a future follow-up
  if those pages need screen-grounded answers.
- `_world_ai_text` caps the list at 20 rows to bound tokens; `global` view has no list (KPIs only) by design.
- `.app` not rebuilt (live-source via `app.py::_live_source()`); `./build.sh` is the protocol §23 follow-up.
