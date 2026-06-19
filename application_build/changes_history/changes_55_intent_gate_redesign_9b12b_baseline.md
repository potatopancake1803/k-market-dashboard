---
id: 55
title: Deterministic intent gate — stop reflexive news search; chitchat short-circuit; route gathering by intent; redesign around 9B/12B local baseline
date: 2026-06-16 03:50 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **Problem:** every question (even "안녕") reflexively ran step-1 news search ("뉴스 10건 수집") because the
  deterministic agent's news step was unconditional — designed for a 4B local model that can't self-route tools.
  Wasteful latency, noise, and (for Gemini) burns the small free grounding quota.
- **New `_classify_intent(question, scope, has_entity)`** — a sophisticated deterministic gate run *before* any
  gathering. Returns flags: `chitchat, news, deep, governance, financials, analyst, peers, technical, calc`.
  - **chitchat** (인사·감사·필러·기능문의) via `_RE_CHITCHAT` + guards: only if no info-bearing token
    (no digit / no finance·news·tech keyword) and length ≤ 20. → **zero gathering**, light conversational answer.
  - **news** only when explicit fresh keywords (`_KW_NEWS`) OR (entity present AND opinion keywords `_KW_OPINION`).
    Pure screen-interpretation questions ("이 화면 해석해줘") → **no search**, screen context suffices.
  - 나머지 소스(deep/governance/financials/analyst/peers/technical/calc)는 각 키워드 집합으로 정밀 게이팅.
- **Agent refactor** (`llm_ask.generate`): wrapped all 8 gathering steps in the intent flags; news step is now
  conditional (`intent["news"]`), article-body read nested under it (`intent["deep"]`). chitchat fully skips
  gathering and emits a single "💬 일반 대화로 판단 — 데이터 수집 없이 바로 답합니다." note.
- **Synthesis prompts by intent:** chitchat → friendly 1–3 sentence assistant prompt (no data-grounding, no
  disclaimer); tool_used → grounded prompt; else → screen-only prompt.
- **9B/12B baseline redesign:** local answer budget 1800→**2000** tokens (chitchat 280); Gemini 4096 (chitchat 256,
  and `_GEMINI_SYS_ADDENDUM` structured-analysis suffix skipped for chitchat). `needs_search` now derives from
  `intent["news"]` (was always-on + `_SEARCH_KW`), unifying the search decision; local→Gemini auto-switch also
  guarded by `not intent["chitchat"]`.

## How it was done
- `_classify_intent` + keyword constants (`_KW_NEWS/_DEEP/_OPINION/_FIN/_GOV/_ANALYST/_PEERS/_TECH/_CALC`,
  `_RE_CHITCHAT`) added next to `_agent_search_query`.
- `_SEARCH_KW` is now superseded by `_KW_NEWS` via the gate (left defined, unused — harmless).

## Verification
- `python3 -m py_compile` → PY OK.
- Headless (MARKET_PORT 8792, /__ping keepalive, single invocation), `/api/llm_ask`, reasoning-frame inspection:
  - **"안녕"** → `chitchat=True, news-search=False`; answer "안녕하세요! K-Market Dashboard를 찾아주…" (friendly,
    no search). ✅ — the reflexive search is gone.
  - **world "이 화면 해석해줘"** → `chitchat=False, news=False`; structured read citing **나스닥 +3.07%, VIX**
    (screen-only, no wasted search). ✅
  - **stock "오늘 삼성전자 왜 올랐어?"** → `news=True, deep=True`; cites today + 미국-이란 종전·외국인 순매수. ✅
  - **stock "삼성전자 부채비율 알려줘"** → `financials=True, news=False`. ✅ (answer 503 transient)
  - **"고마워 ㅎㅎ"** → `chitchat=True`, no gathering. ✅ (answer 503 transient)
  - Server tracebacks: **0**.
- Transient Google **503** still appears on `gemini-3.5-flash` (high demand); graceful fallback message shown.

## Notes & Traps
- Intent gate is heuristic/deterministic by design (chosen over Gemini native function-calling to avoid extra API
  round-trips/latency). If future questions get mis-routed, tune the keyword sets / `_RE_CHITCHAT`, not the model.
- `_SEARCH_KW` is now dead (superseded by `_KW_NEWS`); safe to delete in a later cleanup.
- Local JIT-load default model id unchanged (picker still prefers an already-loaded model; only JIT-loads default
  when nothing is loaded). The 9B/12B assumption is reflected in prompts/budgets, not in a forced model swap.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
