---
id: 52
title: Gemini grounding 429 root-cause + search-off fallback; multi-turn memory; cloud-max prompt; 2.5-Flash-only search note; bigger avatar + UI polish
date: 2026-06-16 01:30 KST
agent: Claude (Opus 4.8 / Sonnet 4.6)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **429 root cause (corrects changes_51's "credits depleted" guess).** Reproduced live: a *plain*
  `streamGenerateContent` call on the free key returns **200 OK**; the **identical request + `tools:[{google_search:{}}]`**
  returns **429 RESOURCE_EXHAUSTED**. Cause = **Search grounding requires a billing-enabled Google Cloud project**
  even to use its free monthly allowance; a billing-less AI Studio key gets quota=0 for that tool only. Observed in
  app: 2.5-Flash grounding works for the user but Gemini-3.x grounding 429s (consistent with the screenshots).
- **`_gemini_stream` auto-fallback.** If a grounded request 429s, it now retries **once without** the search tool
  (`_stream(False)`), so Gemini still answers from the deterministic-gathered ctx instead of failing outright.
  Refactored body-build into `_build_body(with_search)` + `_stream(with_search)`. 429 message de-jargoned.
- **작업1 — bigger Gemini avatar.** `.kmkt-ai-av` 22→28px; Gemini glyph (✦) 12→19px with a violet glow +
  inset ring; `.kmkt-ai-who` gap/spacing tuned; `.kmkt-ai-nm` size/letter-spacing.
- **작업2 — multi-turn memory (Gemini).** Widget keeps an in-memory `convo[]` (each `{role,text}`); on send it
  posts `history` (last 12 turns) **only when provider=gemini**. `llm_ask` parses `history`; `_gemini_stream` now
  takes `history=` and prepends those turns to `contents` before the current user turn (cap 1500 chars/turn, 12
  turns). Local stays stateless (deterministic re-gather each call). Memory clears on window close (matches the
  existing "close wipes chat" UX) and is capped at 24 entries.
- **작업3 — maximize cloud model.** New `_GEMINI_SYS_ADDENDUM` appended to the Gemini system prompt only: asks for
  one level deeper, structured markdown analysis (①결론 ②근거 ③리스크·반론 ④점검포인트) instead of the terse
  local-oriented answer, while keeping all data-grounding guardrails. Output stays 4096 tokens.
- **작업4a — search-capability note.** When provider=gemini, the question needs search (`_SEARCH_KW`), and the model
  ≠ `gemini-2.5-flash`, a reasoning frame tells the user real-time search currently works only on Gemini 2.5 Flash.
- **작업4b — interface polish.** Header subtitle (`.kmkt-ai-sub`) now syncs to the active provider
  (로컬 LLM ↔ Gemini) via `applyProvUI()`.

## How it was done
- Diagnosis via two raw `curl`s to `generativelanguage.googleapis.com` (with vs without `google_search`) — 200 vs 429.
  Confirmed against the pricing/grounding docs (grounding billed per query on Gemini 3; free tier needs billing on).
- Multi-turn: frontend `convo.push({role:'user',text:q})`/`{role:'model',text:ansBuf}` after each completed answer;
  backend builds `contents=[...history, currentUser]`. System prompt is unchanged per-turn (grounding stays strict).

## Verification
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` → **PY OK**.
- `node --check` on extracted widget `<script>` (30,432 chars) → **NODE OK**.
- Live raw API: plain call → **HTTP 200** (answer streamed); same call + `google_search` → **HTTP 429
  RESOURCE_EXHAUSTED** (error body captured). A later attempt hit a separate Google-side **503 "high demand"** on
  3.5-flash (transient, confirmed via direct curl) — unrelated to our code.
- Headless (MARKET_PORT 8796/8797, /__ping keepalive per trap #8, single-invocation per trap #18):
  - 작업4a: `provider=gemini, model=gemini-3.1-pro-preview, q="오늘 코스피 최신 뉴스 알려줘"` → SSE contains
    **"ℹ️ 인터넷 실시간 검색은 현재 'Gemini 2.5 Flash' 모델에서만 동작합니다…"** (decoded; trap #4 — Korean is
    `\uXXXX`-escaped in SSE, must JSON-decode to match) + `meta{model:gemini-3.1-pro-preview}`. ✅
  - 작업2: `provider=gemini, model=gemini-2.5-flash, history:[{user},{model}]` → accepted, emits
    `meta{model:gemini-2.5-flash}` and streams (no 400). ✅ (full answer text gated by transient 429/503.)
- **Visual (avatar size/glow, header subtitle sync, multi-turn feel, dropdown harmony) = unverified** — needs GUI.
  Verify via `uv run application_build/app.py`: open AI 질문하기 → Gemini, confirm bigger ✦ avatar + subtitle reads
  "Gemini"; ask 2 linked questions and confirm the 2nd answer references the 1st (memory); on a 3.x model ask a
  "최신/뉴스" question and confirm the 2.5-Flash note; switch to 2.5 Flash and confirm search actually returns.

## Notes & Traps
- **NEW TRAP:** Google Search grounding needs a **billing-enabled** Google Cloud project even within the free 5,000/mo
  allowance. A billing-less key → 200 for plain calls, **429 only on grounded calls**. Fix path: link billing to the
  project behind `GEMINI_KEY`. Until then, 3.x grounding silently falls back to data-only (search off); 2.5-Flash
  grounding works without billing (different quota lane).
- `KMKT_GEMINI_MODEL` env still force-overrides when no per-request `gemini_model` is sent.
- `.app` not rebuilt (live-source via `app.py::_live_source()`); `./build.sh` is the protocol §23 follow-up.
