---
id: 38
title: Multi-step ReAct AI agent + floating ChatGPT-style chat + overseas mktcap/chart unify + global macro indicators
date: 2026-06-16 00:30 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
Four user-requested features, all in the live source (`scripts/market_dashboard3_realtime.py`),
so **no .app rebuild required** (app.py loads it via `_live_source()`).

- **작업1 — AI 에이전트 능동화:** the `/api/llm_ask` router was a *single-step* tool picker
  (one of DIRECT/GOVERNANCE/FINANCIALS/SEARCH/PYTHON, then answer). Upgraded to a **bounded
  multi-step ReAct loop** (max 4 steps) so the small local model can chain tools
  (e.g. SEARCH → FETCH article body → answer) like Claude/Gemini. Added a new **FETCH tool**
  (`_fetch_url_text`) that pulls and strips a web/article page to readable text — realises the
  user's example "과징금 뉴스 제목 → 본문까지 읽어 자세히". News search now carries the article
  `link` so the model can FETCH it.
- **작업2 — 플로팅 챗 UI:** replaced the inline `_ASK_WIDGET_HTML` card with a **draggable
  bottom-right circular FAB ("AI 질문하기") + animated ChatGPT-style popup**, **ephemeral**
  (closing wipes the conversation). Injected **once per page at `</body>`** (body-direct so
  `position:fixed` is not broken by transformed ancestors). Light/dark + reduced-motion aware.
- **작업3 — 해외주식:** (a) NVIDIA-class **시가총액 overflow fixed** — `fmtMcap()` compacts 억→조
  (e.g. 48,000,000억 → 4,800.0조) + `.eh-kpi/.k-val` overflow guards (§10.2). (b) **price chart
  unified with the domestic `candle_chart()`**: filled candles (fillcolor), fixed up=#C0392B /
  down=#2E75B6 (theme-independent, matching the dashboard.py report), and identical MA palette
  (MA5 #2E8B57 / MA20 #C0392B / MA60 #E08E3C / MA120 #7030A0, width 1.3).
- **작업4 — 글로벌 경제지표:** the 경제지표 page was Korea-only (ECOS). Added a
  **🌐 글로벌 경제지표 card**: S&P500, 나스닥, VIX, 달러인덱스, 국제 금, WTI — all from Naver
  auth-free endpoints — with rule-based 증시 영향 해석. Global data also feeds the macro AI
  context (`_macro_text`) and the "AI 해석" prompt.

## How it was done
### 작업1 (ReAct agent) — `/api/llm_ask` + helpers
- `_fetch_url_text(url, max_chars=2500)` (new): httpx GET (browser UA, follow redirects),
  charset sniff (EUC-KR/MS949 → euc-kr fallback), strip script/style/nav/header/footer/aside,
  block tags → newlines, tags → space, unescape, collapse, 10-min cache `_FETCH_CACHE`.
- `_naver_news` now includes `link` (originallink|link) in each row (backward-compatible extra key).
- `llm_ask.generate()` rewritten: loop `for _step in range(4)`. Each step asks `_llm_complete`
  (temp 0.1, 180 tok) for ONE action given `[현재 화면 데이터]`+`[지금까지 수집한 정보]`+`[질문]`.
  Actions: `ANSWER`/`DIRECT` (break), `SEARCH:<kw>`, `FETCH:<url>`, `GOVERNANCE:<6>`,
  `FINANCIALS:<6>`, `PYTHON:<code>`. Observations accumulate into `observations[]`; `seen` set
  blocks repeats; unknown output → break. Progress streamed to the dim reasoning box
  (`kind:"reasoning"`). After the loop, all observations are appended to ctx and the final answer
  streams via `_llm_stream`. The existing GOVERNANCE/FINANCIALS/PYTHON tools and the tool-used
  system-prompt pivot are reused.

### 작업2 (floating chat) — `_ASK_WIDGET_HTML` + injection
- New self-contained component: `#kmktAiFab` (56px gradient circle, hover-expands to show label,
  draggable via pointer events with a 5px move threshold to distinguish click; position persisted
  in `localStorage 'kmkt-ai-fab-pos'`) and `#kmktAiWin` (380×560 glass panel, scale/opacity open
  animation with `transform-origin` chosen by FAB quadrant). Messages render as user/AI bubbles;
  reasoning goes to a collapsible `<details>`. `closeWin()` wipes `#kmktAiBody` + inputs
  (ephemeral). Theme via `kmkt-ai-dark` class toggled from `html.dark`/localStorage + a
  MutationObserver + `storage` event. Streaming/SSE parse reuses the proven `\\n`-split pattern.
- `_inject_ask` now inserts `setter + widget` before the **last `</body>`** (was: after pane0).
  Overseas: `__KMKT_ASK_WIDGET__` placeholder → "" and widget appended at `</body>`. Macro/index:
  widget moved to `</body>` direct (dropped the padding wrapper). `window.KMKT_ASK()` setters
  unchanged (overseas sets its own in `render()`).

### 작업3 (overseas) — `_OVERSEAS_HTML`
- `fmtMcap(eok)` (new): ≥10000억 → `(v/10000)조` (1 dp) else `fmtI(v)억`. Applied to `#kpiMcap`
  and the 시가총액 details row. `.eh-kpi{min-width:0;overflow:hidden}` +
  `.k-val{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}`.
- `draw()`: `upCol/dnCol` fixed to `#C0392B/#2E75B6` (was theme-variant). Candlestick trace gains
  `fillcolor` (solid) + `showlegend:false` + name '가격'. MA colors switched to the domestic
  `candle_chart()` palette. Volume bars inherit the same fixed up/down colors.

### 작업4 (global macro) — new fns + route + page
- `_global_macro_snapshot()` (60s cache): `_TPE(6)` parallel — `_gmac_idx_one` for `.INX/.IXIC/.VIX`
  via `/index/{code}/basic`; `_gmac_list_one` for `.DXY` (`/marketindex/exchange` → normalList),
  `GCcv1` (`/marketindex/metals`), `CLcv1` (`/marketindex/energy`). Returns rows
  `{key,price,pct,dir,unit}` + rule-based `points` (달러/위험심리/유가/미국증시/금). Route
  `/api/global_macro`.
- `_MACRO_HTML`: new `#globalCard` (tiles `#gtiles` + `#gPoints`) before the AI card;
  `renderGlobal()`/`gtile()`; an **independent** `fetch('/api/global_macro')` (reveals `#body`
  even if ECOS fails); header/lead reworded to "한국 · 글로벌". `aiExplainMacro` appends a
  `[글로벌 지표]` line; `_macro_text()` (app-wide AI context) appends one too.

## Verification
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` → clean (run after each task).
- Floating widget JS extracted from the rendered overseas page → `node --check` → **JS-SYNTAX-OK**
  (confirms the `\\n`/escape handling in the non-raw string is correct).
- Module imported via `uv run` + `app.test_client()`:
  - `/macro_page`, `/index_page` → exactly **fab:1 win:1** (widget injected once); overseas
    template `__KMKT_ASK_WIDGET__` placeholder count 0 (removed).
  - `_global_macro_snapshot()` live: **6/6 rows** with real values (S&P 7,559.72 +1.73%, 나스닥
    26,582.30 +2.68%, VIX 16.22 -8.26%, 달러인덱스 99.51 -0.23%, 국제 금 4,375.80 +3.23%,
    WTI 80.66 -4.97%), **5 interpretation points**. `/macro_page` renders `#globalCard`/`#gtiles`.
  - `_macro_text()` tail includes the `[글로벌 지표] …` line.
- **NOT verified live this session:** (a) the multi-step ReAct loop end-to-end with LM Studio
  (needs the local server + a loaded model); (b) visual/interaction of the floating chat (drag,
  open/close animation, ephemerality) in the real app; (c) the overseas filled-candle/colors and
  the 시총 compaction visually. All are web-level (live source) — no rebuild to test.

## Notes & Traps
- **No .app rebuild** — all edits are in the live source.
- `_global_macro_snapshot` references `_TPE`/`_WORLD_UA` which are defined later in the file;
  fine because they resolve at call (request) time, not import time. Verified by the live test.
- Naver global codes (probed live): VIX=`.VIX`, S&P=`.INX`, NASDAQ=`.IXIC` via `/index/{c}/basic`;
  Gold=`GCcv1` (`/marketindex/metals`), WTI=`CLcv1` (`/marketindex/energy`), Dollar index=`.DXY`
  (`/marketindex/exchange` → `normalList`). **US 10Y Treasury yield & Fed funds are NOT available
  via Naver** (`.TNX`/`US10YT=RR`/etc → 409; `/marketindex/bond` → 404) — omitted. If wanted
  later, needs FRED (no key configured) or an ECOS international-rates table.
- Floating widget must be injected **body-direct** (`</body>`), never inside a card/pane —
  reports apply CSS `transform` to `.card`/`.pane`, which would re-root `position:fixed`.
- To verify the ReAct loop live: start LM Studio (port 1234, load an Instruct model e.g.
  qwen3-4b-2507), run the backend with a `/__ping` keepalive (trap #8), POST `/api/llm_ask`
  `{scope:"stock",id:"...",question:"...최근 과징금 사유..."}` and watch the reasoning box for
  `🔍 검색 → 📄 본문 → ✅` chaining.
