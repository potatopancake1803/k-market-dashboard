---
id: 54
title: AI reads every screen (market/backtest scopes) + free-tier-only Gemini model gating, search-capability gating, thinking-leak fix
date: 2026-06-16 03:05 KST
agent: Claude (Opus 4.8)
status: verified
supersedes: [51]
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
### 작업1 — every screen readable by the AI ask widget
- `_ask_context()` had no handler for `scope=='market'` (home·시장·섹터·실시간) nor `scope=='backtest'`, so those
  screens gave the model empty data. Added both:
  - New `_market_ai_text()` → 코스피/코스닥 지수 + 시총 상위 20 종목 (reuses `_world_domestic_one` + `_sector_stocks`).
  - `market` → `_market_ai_text()`; `backtest` → `_market_ai_text()` + a hint to paste strategy/results into the
    "참고 데이터" box for precise analysis.
- Net: all scopes (stock/etf/ov/macro/world/market/backtest/index/research) now return non-empty screen context.

### 작업2 — free-tier-only model gating + precise prompt process (per attached Gemini_API_Models.md)
- **Removed `gemini-3.1-pro-preview`** — its free tier is "지원 안 함", so a free key errors on it. Catalog is now
  free-tier-only: `gemini-3.5-flash` (default), `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`.
  Dropdown options updated to match; a stale localStorage model id (e.g. the removed Pro) auto-resets to default.
  Server already coerces unknown `gemini_model` → `_GEMINI_DEFAULT` (verified no error).
- **Search feature gating** (`_GEMINI_SEARCH_OK = {2.5-flash, 2.5-flash-lite}`): Google Search grounding is only
  enabled where it actually works on a billing-less free key — the **2.5 series**. (3.x grounding needs billing →
  429; trap #32.) Also gated on `needs_search` so the small free search quota (2.5: 500–1,500/mo) isn't burned on
  non-search questions. `use_search = needs_search and model∈_GEMINI_SEARCH_OK`.
- **Auto-switch target fixed:** the local→Gemini search auto-switch now forces `gemini-2.5-flash` (a search-capable
  free model) instead of leaving a non-search model selected.
- **Search note refined:** on a search question with a non-search model, the ℹ️ note now says search works on
  2.5 Flash / 2.5 Flash-Lite and that the answer will use gathered news/data only.
- **Thinking-leak fix:** with grounding, 2.5 models streamed their `tool_code`/`thought` chain-of-thought as
  *answer* text. Fixed by requesting `generationConfig.thinkingConfig={includeThoughts:true, thinkingBudget:1024}`
  (search path only) so thoughts arrive as proper `thought:true` parts → routed to the dim 생각 과정 box, and the
  bounded budget guarantees the final answer still arrives. Non-text parts (executableCode/functionCall) skipped.

## How it was done
- `llm_ask.generate()` reassigns `gemini_model` on auto-switch → needed `nonlocal gemini_model` (without it,
  Python made `gemini_model` a generate-local → **UnboundLocalError on every Gemini request**; caught + fixed).
- `_gemini_stream._build_body` adds `thinkingConfig` + tools only when `with_search`; `_stream` routes
  `part.thought` → `kind:reasoning`, else → answer.

## Verification
- `python3 -m py_compile` → PY OK; `node --check` widget (post-edit) → NODE OK; no stale `3.1-pro` refs in code.
- Headless (MARKET_PORT 8795–8797, /__ping keepalive, single-invocation):
  - **A** `scope=market, gemini-3.5-flash, "오늘 코스피…최신"` → `meta=3.5-flash`, ℹ️ 2.5-only note shown, search
    OFF; reads market (answer attempt; transient Google 503 on 3.5-flash — unrelated).
  - **B** `scope=backtest, gemini-2.5-flash, "최근 코스피 변동성"` → search ON, **answer 621 chars, NO tool_code
    leak**, ①결론 ②근거 structure, cites **screen data "오늘 코스피 8,726.60 +2.11%, 코스닥 1,018.68 -1.48%"**
    + gathered news → backtest/market screen-reading + grounding both confirmed. ✅
  - **C** `gemini_model=gemini-3.1-pro-preview` (removed) → server defaults to 3.5-flash, **no error/exception**.
  - Server tracebacks across runs after the nonlocal fix: **0**.

## Notes & Traps
- Transient `503 "high demand"` still hits `gemini-3.5-flash` intermittently (Google-side, confirmed via raw curl);
  the graceful "[시스템 알림] … 로컬로 전환" message covers it.
- `realtime` page uses `scope:'market'` (market overview), not the page's active single stock — a future refinement
  could make it pass `scope:'stock', id:activeCode` like the world page passes its view.
- Supersedes changes_51's model catalog (which included the non-free Pro Preview and assumed all models ground).
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
