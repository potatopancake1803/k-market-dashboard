---
id: 39
title: Deterministic research agent (real external fetch) + 증권사 리포트 viewer + LLM status dot/think toggle + mktcap/FRED/overseas-quant fixes
date: 2026-06-16 01:20 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (feedback round 2)
All in the live source → **no .app rebuild**.

- **피드백2b (핵심) — AI가 실제로 외부정보를 수집하게:** the changes_38 ReAct loop *still* failed
  because the local 4B model **ignores tool-calling entirely**. Diagnosed live against LM Studio:
  even with native OpenAI `tools=[web_search]`, qwen3-4b-2507 returned `tool_calls:[]` and
  hallucinated governance from memory. **Replaced model-driven routing with a deterministic
  keyword-driven research agent**: the system itself always web-searches + (when keywords match)
  reads article bodies, pulls FSC/DART governance, pulls DART financials, and runs python — then
  forces the model to answer ONLY from the gathered data. Verified live: "SK하이닉스 지배구조/최대주주"
  → searched 6 news + read 2 articles + fetched governance (SK스퀘어 20.07%) → grounded answer,
  no hallucination.
- **피드백2a — 시가총액 오류:** `d.tomv` is the raw listing-currency value (NVDA ≈ 5.11e12 USD),
  not 억. The 억-label math produced "511,248,232.0조". Fixed `fmtMcap(v,curr)` → currency symbol +
  T/B/M ("$5.11T").
- **작업5 — AI 버튼 로드상태 점 + 추론 토글:** green dot on the landing ✨AI button when a model is
  loaded (gray otherwise), via lightweight `/api/llm/loaded` polled every 30s (frugal). Floating
  chat now has a "🧠 심층 추론" toggle → `think` flows to `_llm_stream` (skips the thinking-suppress
  prefill for reasoning models; adds a step-by-step instruction for instruct models).
- **작업7 — 증권사 리포트 뷰어 (대규모 신규):** new `/research_page` (home card 📑) with 6 category
  tabs (데일리/종목분석/산업분석/투자전략/경제분석/채권분석), each listing 30 reports
  (제목·증권사·종목·날짜·TODAY badge), **원문 PDF 프록시** + **로컬 AI 요약(SSE)**.
- **피드백1:** (a) FRED 미국 금리(10년물·기준금리) added to global indicators via `FREED_KEY`.
  (b) overseas **M4 퀀트 탭 깨짐 수정** — page had only a partial M4 CSS subset, so cards rendered
  light and metrics stacked vertically; injected the full canonical `_M4_STYLE`.
- **env:** app now also loads `api_documents/API.env` (FREED_KEY etc.) with `override=False`.

## How it was done
- **Deterministic agent (`/api/llm_ask`)**: removed the `_llm_complete` ReAct loop. New flow in
  `generate()`: `_agent_entity(scope,id,excd)` → (name, code6); always `_naver_news(query)` (query =
  `_agent_search_query(name, question)`), collect rows + article links; if the question is "deep"
  (왜/이유/사유/배경/과징금/제재/소송/전망/영향…) fetch top-2 article bodies via `_fetch_url_text`;
  if Korean code6 + governance keywords → `_get_governance_shareholders`; + financials keywords →
  `_get_financial_statements`; + calc keywords → `_agent_make_python` (model writes python) →
  `_run_agent_python`. All observations appended to ctx; `tool_used` sys-prompt now hard-forbids
  using pretrained memory ("모든 사실은 주입된 데이터에서만 인용").
- **mktcap**: `fmtMcap(v,curr)` (USD→$, JPY→¥) with T/B/M; applied to `#kpiMcap` + details row.
- **작업5**: `/api/llm/loaded` (one `/api/v0/models` hit → `{up,loaded,id}`); landing `#aiDot`
  span + `.ai-dot/.ai-dot.on` CSS + 30s poll IIFE (skips when `document.hidden`). Chat widget
  `#kmktAiThink` checkbox → body `think` → `llm_ask` → `_llm_stream(...,think=)`.
- **작업7**: `_RESEARCH_CATS` (cat→legacy slug); `_research_list(cat,page)` parses EUC-KR
  `finance.naver.com/research/{slug}_list.naver` rows (nid/title/broker/date/pdf/stock, 5-min cache);
  `_research_read(cat,nid)` decodes EUC-KR → strips to text + finds PDF url; routes `/api/research`,
  `/research_pdf2` (PDF proxy w/ Referer), `/api/research_summary` (SSE → `_llm_stream` summary),
  `/research_page` (`_RESEARCH_HTML`, glass UI, light/dark, floating AI widget). Landing
  `#researchCard` → `openTab('__research__',{url:'/research_page',...})`.
- **FRED**: `_fred_one(series_id,label)` (latest + Δ vs prior obs); added DGS10/FEDFUNDS to
  `_global_macro_snapshot` (ThreadPool), + a US-10Y interpretation point; flows into `_macro_text`.
- **overseas quant**: `_OVERSEAS_HTML = _OVERSEAS_HTML.replace("</head>", _M4_STYLE + "</head>")`.

## Verification (live, via uv + app.test_client + real network/LM Studio)
- **Agent (live LM Studio, qwen3-4b loaded):** SK하이닉스 governance Q → progress showed
  `🔍 검색 → 📄 본문×2 → 🏛️ 지배구조` and the answer cited SK스퀘어 20.07% (real FSC/DART data),
  not memory. Confirms external fetch works end-to-end.
- **Native tool-calling probe:** qwen3-4b-2507 with `tools=[web_search]` → `tool_calls:[]` +
  hallucinated answer (documents WHY model-routing was abandoned).
- **mktcap:** `fmtMcap(5.11e12,'USD')` → "$5.11T" (no overflow).
- **작업5:** `/api/llm/loaded` → `{up:true,loaded:true,id:qwen/qwen3-4b-2507}`; landing has 1
  `#aiDot` + CSS; overseas/macro pages have the `#kmktAiThink` toggle.
- **작업7:** `/api/research` daily/company/economy each 30 rows matching the live site (마켓레이더 …,
  Corporate Day …, 가던 길을 간다 …); `_research_read` returns clean Korean text (1.4k chars);
  `/research_page` renders tabs+list+fab; landing `#researchCard` present.
- **FRED:** global snapshot now includes 미국 국채 10년 4.45% / 미국 기준금리 3.63% + a US-rate
  interpretation point; `_macro_text` tail includes them.
- **overseas quant:** `_OVERSEAS_HTML` now has `id="m4-style"` (1) + `.m4-met-grid` (1) + plotly.js.
- `python3 -m py_compile` clean throughout.
- **NOT visually verified this session (web-level, live source — just restart app):** floating-chat
  look/drag, research page rendering + PDF render in WKWebView + AI summary stream, overseas M4 cards
  after the CSS fix, the green dot in-app.

## Notes & Traps
- **Local 4B models will not reliably call tools** (free-text OR native `tools`). For agentic
  external-data behavior, drive tool use deterministically from keywords/heuristics and force
  grounding — do not rely on the model to "decide". (This is the key lesson; see changes_38 which
  wrongly assumed model-driven routing would work.)
- `d.tomv` (KIS overseas) = raw listing-currency market cap, NOT 억.
- Research list/read pages are **EUC-KR**; decode explicitly (do not rely on `_fetch_url_text`'s
  charset sniff, which mis-decoded them to mojibake).
- PDF route is `/research_pdf2` (avoids cl.ashing w/ existing `/report_pdf`); needs Referer header.
- FRED key var is **`FREED_KEY`** (sic) in `api_documents/API.env`; app loads that file now.
- `_global_macro_snapshot` / `_research_*` reference `_TPE`/`_WORLD_UA`/`_fetch_url_text` defined
  later/elsewhere — fine, resolved at call time.
- To verify the agent live: LM Studio on :1234 with an Instruct model loaded; ask a stock screen a
  "왜/지배구조/최근" question and watch the reasoning box chain searches/fetches.
