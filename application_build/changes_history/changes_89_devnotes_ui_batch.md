---
id: 89
title: Dev-notes UI batch — PDF toolbar, mic removal, default model, AI-prefs persistence, collapsible summary, macro text, consensus legend
date: 2026-06-19 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/ui_templates.py
  - scripts/market_dashboard3_realtime.py
  - market_intel/report/dashboard.py
---

## What was done
Processed two dev-mode capture sessions (now in `dev_notes/done/`):
`session_20260619_1539_260619-1.md` (6 tasks) + `session_20260618_1441_새-세션.md` (1 task).

1. **PDF viewer custom toolbar removed** (`_PDF_VIEW_HTML`). The zoom/fit/new-window `.bar`
   buttons didn't work; the native WKWebView/Chromium PDF viewer already provides a bottom
   toolbar. Removed the `.bar` markup + its JS; the iframe now loads `pf.src=SRC` directly.
2. **Mic button removed** from the floating AI chat bar (`_ASK_WIDGET_HTML`, `#kmktAiMic`).
   It was non-functional and crowded the input. Deleting the element is null-safe — the
   Web-Speech IIFE already early-returns when `micBtn` is null. Affects every page carrying the widget.
3. **Default local model → `gemma-4-12b-qat`** (`_LLM_PREFERRED`, was `qwen3-4b-2507`).
   `KMKT_LLM_MODEL` env override still wins.
4. **System prompt (and provider/gemini model) now persist across app restart.** New backend
   route `GET/POST /api/ai/prefs` (file-backed at `~/.cache/kmkt_m4/ai_prefs.json`, allow-list
   keys only). The landing AI popover seeds `localStorage` from the server on load and writes
   changes back (debounced). Fixes WKWebView `localStorage` being wiped on restart.
5. **Research AI summary is collapsible** (`_RESEARCH_HTML`). After it loads, the ✨ button
   toggles 접기/펼치기 (`panel._loaded` guard).
6. **Macro text** "로컬 LLM이" → "AI가" (`_MACRO_HTML`).
7. **Consensus gauge legend disambiguated** (`market_intel/report/dashboard.py:consensus_gauge`).
   The review found the value (e.g. 매수 4.00점) is the correct Naver `recommMean`; the
   "적극매도1 · 매도2 …" subtitle is a **1–5 scale legend**, not an opinion distribution
   (distribution renders separately via `_dist_html`). Reworded to
   `점수 기준 1=적극매도 · 2=매도 · 3=중립 · 4=매수 · 5=적극매수` to stop the misread.

## How it was done
- Markup/JS edits live in `scripts/ui_templates.py` (templates), the model constant + new
  route in `scripts/market_dashboard3_realtime.py`, the gauge legend in `market_intel/report/dashboard.py`.
- `/api/ai/prefs`: `_ai_prefs_read()` + GET returns the JSON; POST merges only `{gsys, provider,
  gemini_model}` (each ≤4000 chars) and writes the file. Frontend: a seed-on-load IIFE GETs the
  prefs and writes the `kmkt-ai-*` localStorage keys (so the existing widget/popover readers pick
  them up); `bindProv` POSTs on provider/model change and on gsys input (400ms debounce).

## Verification
- `uv run scripts/smoke_check.py --golden write` then plain `uv run scripts/smoke_check.py` →
  `SMOKE PASS ✓`. Golden re-baselined because `/`, `/macro_page`, `/research_page`, and the
  AI-widget-bearing pages (`/index_page`, `/backtest_page`, `/realtime_page`) changed intentionally.
- `/api/ai/prefs` exercised via Flask test client: POST `{gsys, provider, evil}` → GET returns
  the gsys + provider, `evil` rejected; file persisted then restored to pre-test state.
- `node --check` on the rendered `<script>` of `/`, `/research_page`, `/macro_page` → all OK.
- Asserted: PDF `.bar` gone + `pf.src=SRC` present; `#kmktAiMic` gone; research `_loaded` toggle
  present; macro text changed.

## Notes & Traps
- **status: partial** — code verified, but three items need the live app/runtime to confirm and
  stay ❓: Task3 actual model load (needs LM Studio with `gemma-4-12b-qat`), Task4 persistence
  across a real app restart (needs GUI), and the visual outcome of Task1/2/5.
- `_LLM_PREFERRED` is partial-match; `"gemma-4-12b-qat"` matches e.g. `google/gemma-4-12b-qat`.
- New routes `/api/ai/prefs` (GET+POST) → CODEMAP route count rises; regenerate `docs/CODEMAP.md`.
- `market_intel/report/dashboard.py` uses Py3.12 syntax (trap #35) — harmless text edit; the
  `uv` env is 3.12+ so smoke imports it fine. A frozen `.app` rebuild is recommended to ship
  the report change (not done here).
