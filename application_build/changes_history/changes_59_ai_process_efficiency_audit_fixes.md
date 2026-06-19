---
id: 59
title: AI process efficiency audit (local vs Gemini) + fixes — no reflexive news on report scope, skip redundant PDF text-scrape, cache PDF bytes
date: 2026-06-16 06:30 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## Audit (local LLM vs Gemini) — how each AI path works
- **`/api/llm_ask`** (chat widget, all screens + PDF viewer): intent gate (`_classify_intent`, changes_55) →
  deterministic gather only what's needed → synth. Local = LM Studio (`_pick_llm_model_ex` prefers loaded model,
  `_llm_model_profile` reasoning/instruct + prefill). Gemini = `_gemini_stream` (multiturn ≤12×1500, search gated
  to 2.5+needs_search, thinkingBudget 1024 on grounding, 429→search-off retry, PDF-direct for research scope).
- **`/api/llm_commentary`** (종목/해외 코멘터리, macro/backtest 해설): `_build_ai_context` grounding → local inline
  stream OR Gemini (`use_search=False`, data already injected). provider/gsys from popover.
- **`/api/research_summary`** (리포트 요약, 종합시황): local OR Gemini via `_synth`; Gemini reads the PDF directly.

## Inefficiencies found → fixed
1. **Reflexive news search on report questions.** Asking about a report (`scope=research`) still ran the live news
   search + article fetches — pointless, the report/PDF *is* the source. → `_classify_intent` now forces
   `news=False` for `scope=="research"`. (Verified: "실시간 정보 검색" no longer runs.)
2. **research_summary fetched the report twice + sent a redundant 6,000-char text prompt when a PDF is attached.**
   The Gemini path called `_research_read` (read-page fetch + 6k-char body) *and* `_research_pdf_bytes`
   (read-page fetch again + PDF). When the PDF is the authoritative source, the text scrape is waste. → For
   Gemini, fetch the PDF first; if present, send **PDF only** (title prompt), skipping the text-scrape fetch and
   the 6k-char prompt entirely. Falls back to text scrape only when there's no PDF or for local. (Verified:
   "원문 불러오는 중" text-scrape step skipped; PDF-direct fires.)
3. **PDF re-downloaded on every follow-up question.** Each report-viewer question re-fetched the full ~750KB PDF.
   → `_PDF_BYTES_CACHE` (10-min TTL, keyed by cat:nid) on `_research_pdf_bytes` — multiturn report Q&A now reuses
   the bytes instead of re-downloading + re-base64-encoding.

## Reviewed and deliberately left as-is
- `/api/llm_commentary` keeps an inline LM-Studio stream copy (CLAUDE.md §11.6). It's a code dup, not a runtime
  waste (same work as `_llm_stream`); unifying is risky for no perf gain → noted, not changed.
- llm_ask research+Gemini still builds `_ask_context` text (small HTML fetch) as supplementary ctx alongside the
  PDF — acceptable; the heavy payload (PDF) is now cached.
- Gemini grounding + deterministic news can co-occur when `needs_search` (intentional freshness redundancy).

## Verification
- `python3 -m py_compile` → PY OK. Headless (MARKET_PORT 8799, /__ping keepalive):
  - research-scope question → `news-search ran: False` ✅, PDF-direct still fires ✅.
  - research_summary Gemini+PDF → `text-scrape step skipped: True` ✅, PDF-direct ✅.
  - 0 server tracebacks.
- Note: Gemini hit **429 (free daily request quota)** on some calls due to heavy same-session testing — graceful
  fallback message shown; unrelated to these changes (routing/gating all observed correct before the quota).

## Notes & Traps
- `_PDF_BYTES_CACHE` is unbounded dict w/ TTL; report nids are few per session → fine. Clears on restart.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
