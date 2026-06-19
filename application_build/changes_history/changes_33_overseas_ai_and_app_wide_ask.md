---
id: 33
title: 작업3 overseas AI commentary + 작업4 app-wide "AI 질문하기" (RAG chat) with freshness grounding
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **작업3:** Overseas stocks now have the same AI 코멘터리 as domestic (button on the 해외주식 report).
- **작업4:** App-wide "💬 AI에게 질문하기" chat widget on stock / ETF / overseas / 거시(한국 경제) / 지수
  screens — the user asks about the current screen, the local LLM answers from freshly-fetched data.
- **Freshness (요청사항):** all AI prompts now hard-ground on live data + today's date and explicitly tell
  the model NOT to trust its (stale) pretrained knowledge → no hallucinated old facts.

## How it was done
- **Refactor:** extracted the LLM SSE core into `_llm_stream(sys_msg, user_msg, max_tokens=None)` (model
  pick → profile → reasoning prefill → stream → reasoning/endnote). Reused by both new endpoints.
  (`/api/llm_commentary` keeps its own copy — left untouched to avoid risk.)
- **작업3:** `_build_ov_ai_context(excd, symb)` — fresh sheet from `_ov_detail` (price/52w/PER/sector),
  `_ov_chart` momentum, `_yahoo_profile` (기업개요), `_ov_news`. `/api/llm_commentary` accepts
  `{ov_excd, ov_symb}` (news-first, data-grounded, "오늘 기준 데이터만, 학습지식 신뢰말 것"). The
  해외 report got a `🤖 AI 코멘터리` card + button + a reasoning-aware `streamLLM` (raw-page → single `\n`).
- **작업4:** `/api/llm_ask` (SSE) `{scope,id,excd,question}` → `_ask_context(scope,…)` routes to
  stock/ETF (`_build_ai_context`), overseas (`_build_ov_ai_context`), macro (`_macro_text`), index
  (`_index_text`). System prompt = strong freshness guard (today's date, "pretrained knowledge is ~1yr
  stale, cite only provided data, say '제공된 화면 정보로는 알 수 없습니다' if absent"). Streams via
  `_llm_stream`. Reusable widget `_ASK_WIDGET_HTML` (self-contained card+input+SSE script, reads
  `window.KMKT_ASK()` at send-time for dynamic scope/id). Injected: domestic stock/ETF via
  `_inject_ask` (after hero in pane0) from `/dashboard`; overseas via `__KMKT_ASK_WIDGET__` placeholder +
  `window.KMKT_ASK` in `render()`; macro/index via batch `.replace("</body>", setter+widget)`.

## Verification (live server, ping-kept-alive, qwen3.5-9b reasoning model loaded)
- 작업3: `/overseas?symb=AAPL` has `aiCmtBtn`; `POST /api/llm_commentary {ov_excd:NAS,ov_symb:AAPL}` →
  first 8.6s, **309 answer chars, reason 0**, grounded in real AAPL news (WWDC/버핏/인도 조사).
- 작업4: `askCard` + `KMKT_ASK` present on dashboard(stock), overseas, macro_page, index_page (all 1/2).
  `POST /api/llm_ask {scope:stock,id:005930,question:"최근 악재…"}` → first 5.0s, 220 chars, reason 0,
  and it correctly said "제공된 화면 정보로는 …확인할 수 없습니다" citing only the real provided news
  (레미콘 노사·갤럭시S26) — **freshness grounding confirmed working** (no stale hallucination).
- `python3 -m py_compile` clean.

## Notes & Traps
- ETF ask reuses `_build_ai_context` (6-digit code path) — same as stock; not separately load-tested but
  identical code path.
- Visual confirm of the widgets in the real app still pending (web-level; live via `_live_source()`).
  `.app` rebuild deferred (user).
- `_llm_stream` is now the canonical place to evolve LLM behavior; `/api/llm_commentary` still has an
  inline copy (consider unifying later).
