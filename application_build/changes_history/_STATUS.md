# _STATUS.md — Live Project State (READ THIS FIRST)

> **Audience: the next LLM agent.** This is the single source of truth for the
> *current* state of `application_build/`. Unlike `changes_X_*.md` (which are an
> immutable, append-only history), this file is a **living document**: whoever
> makes a change updates it in the same session. If this file and prose history
> disagree, **this file wins** — but if you find it stale, fix it.
>
> Read order for a new session:
> 1. `application_build/CLAUDE.md`  (the protocol — how to log & verify)
> 2. **this file** (`_STATUS.md`)   (what currently works / how to run / traps) ← sufficient for 95% of sessions
> 3. Last 2–3 `changes_X_*.md` (highest X only) — only when debugging regression or continuing partial work

- **Last updated:** 2026-06-19 KST by Claude (Opus 4.8) — TIER 1 agent-upgrade: Hooks regression gate + guarded auto-reflect
- **Latest history entry (this dir):** `changes_88_agent_upgrade.md` (plan: `changes_88_plan_agent_upgrade.md`; prev: `changes_87` BOK MPC PDF ask fix, `changes_86` BOK MPC viewer, `changes_85` devmode health check)
- 🪝 **자동화 레이어 (changes_88):** `.claude/settings.json` Hooks 가 **회귀 게이트를 자동 강제**한다 — 백엔드/템플릿(`scripts/*.py`) 편집 후 `Stop` 훅이 `smoke_check` 를 1회 실행, FAIL 이면 턴 종료를 막는다(`scripts/hooks/gate_dispatch.py`). `SessionStart` 훅은 trap/health 요약을 주입(`session_brief.py`). **교정 자동포착**: `scripts/reflect/{capture,apply}.py` — 사용자 교정 발화를 포착→큐, **기본 `propose` 모드(정본 자동수정 OFF, 전부 `dev_notes/` 로)**. `KMKT_REFLECT_MODE=auto` + 확신도≥0.90 일 때만 백업→구조보존append→(구조검증 AND smoke)→출처로그, 실패 시 자동 롤백으로 `_STATUS.md` 의 `## ▶ Auto-reflect log` 섹션에 기록. `apply.py --undo` 로 되돌리기. (트랩 #42)
- 🧭 **능동 자기학습 레이어 (changes_85):** `python3 scripts/health_check.py` — 구조 비효율/doc-drift 를 임계치로 감지해 WARN+제안. 세션 시작 시 실행, WARN 이면 사용자에게 재설계 제안(Tier-L 승인 후 실행). Dev Mode 도 현재 스타일·차트힌트 캡처 추가.
- ✅ **Dev Mode 첫 실사용 처리 완료 (changes_84):** 사용자 세션#1(4건) 처리 → overseas 등락 간격·차트 날짜 솎음·마켓맵 폰트·**macro 미국 10년물 라인(FRED `_fred_series`)**. 세션은 `dev_notes/done/` 로 이관. (golden `/macro_page` 재기준선됨.)
- 📌 **세션 처리 후**: 에이전트는 `[ ]`→`[x]` + 세션 md 맨 아래 `## ✅ 처리 결과`(바꾼 file:line·changes_X·smoke) 채우고, 다 끝나면 파일을 `dev_notes/done/` 로 이동(changes_83). 세션 시작 시 `dev_notes/` 미처리 확인.
- 🛠 **Developer Mode (changes_81/82):** run `KMKT_DEV=1 uv run application_build/app.py`, ⌘⇧D, click an element → location+source(file:line)+memo. **세션 배칭**: 팝오버 `➕ 세션 추가` + 배지 `📌 N` 칩 → 드롭다운(제목·목록·`💾 세션 저장`) → 여러 캡처를 하나의 `dev_notes/session_*.md` TODO 로. 부모 역추적(id/class 없는 요소도 매칭). Off by default (zero impact). Module `scripts/dev_overlay.py`; routes `/api/dev/{locate,note,session/*}`.
- 🔜 **Deferred (user choice, plan ready):** staged `core.py` decouple → `data_sources.py` collector split. Step-by-step in `changes_80_plan_*`. Gated by `api_smoke.py`. (Trap #41.)
- 🧭 **Agent-nav + safety system (changes_76/77):**
  - `scripts/smoke_check.py` = **regression gate** (import+boot+routes+golden render hash). Run `uv run scripts/smoke_check.py` after any structural/backend/template change → `SMOKE PASS ✓` before "verified". `--golden write` to re-baseline.
  - `docs/CODEMAP.md` = backend line-index (regenerate: `python3 scripts/gen_codemap.py`).
  - `docs/DEBUG_JOURNAL.md` = symptom→fix lookup (grep before re-debugging; append after solving).
  - Backend split: logic in `scripts/market_dashboard3_realtime.py` (~7.8k lines), templates in `scripts/ui_templates.py` (~5.3k), pure quant/format/SSE helpers in `scripts/pure_helpers.py` (~0.2k, changes_78). All re-imported into main → call sites unchanged.
- 🔴 **changes_73 regression FIXED (changes_74):** moving `company_report.py`/`etf_dashboard.py` into `scripts/archive/` broke the live builders' absolute sibling imports → backend failed to import → **app would not start**. Fixed by a `sys.path` shim atop `market_dashboard3_realtime.py`. (See trap #38.)
- ✅ **History-dir drift RESOLVED (2026-06-17):** the repo-root `../../changes_history/` fork (Claude lineage, seq 7–15) has been **consolidated into this canonical dir**, renumbered `changes_7→62 … changes_15→70` (each carries an "이전 위치" provenance header; internal frontmatter `id:` kept as historical 7–15). The root dir now holds only `MOVED.md` (redirect + mapping); originals were **copied, not deleted** (cleanup of root originals pending a separate session). **New changes logs go ONLY in this dir.** (changes_71 Notes; see memory `changes-history-fork`.)
- **Workflow contract:** all agents follow the **🔁 Operating Loop** in `CLAUDE.md`
  (READ → DIAGNOSE → ACT → VERIFY → RECORD) — read context before acting, log & verify
  automatically without being asked.

---

## ▶ How to run

| What | Command | Notes |
|---|---|---|
| Native app (dev) | `uv run application_build/app.py` | Opens WKWebView window. PEP723 deps in `app.py` include `duckdb`, `mlx`. |
| Backend only (debug) | `MI_NO_OPEN=1 MI_NO_PREWARM=1 MARKET_PORT=8793 uv run --directory <root> scripts/market_dashboard3_realtime.py` | Bare uv env: **no `duckdb`/`mlx`** → exercises fallback paths. Good for testing resilience. |
| Build `.app` | `cd application_build && ./build.sh` | Installs `requirements.txt` into `.venv-build`, then PyInstaller. |
| **Regression gate (render)** | `uv run scripts/smoke_check.py` | **Run after ANY structural/backend/template change.** import+boot+routes+golden hash. `SMOKE PASS ✓` = verified for that class. `--golden write` to re-baseline after intentional markup edits. |
| **API gate (collectors)** | `uv run scripts/api_smoke.py` | **Run after moving/refactoring any data collector.** Calls collectors; `NameError/Attr/Import` → FAIL, network/env → SKIP. Green = no broken name refs (works offline/after-hours). |
| Codemap regen | `python3 scripts/gen_codemap.py` | Refresh `docs/CODEMAP.md` line numbers after large edits. |
| **Health check** | `python3 scripts/health_check.py` | **능동 구조 점검** — 세션 시작·구조 변경 시. WARN(비대화·거대함수·❓ 누적·CODEMAP/_STATUS drift·dev_notes 적체)이면 사용자에게 재설계 제안. (changes_85) |

- **Backend source of truth:** `scripts/market_dashboard3_realtime.py`.
  `app.py` loads this **live** at runtime (see `_live_source()`), so editing it +
  restarting the app applies changes without a rebuild.
- **Default port 8780** (`MARKET_PORT` overrides). **Never kill PID on 8770** —
  macOS `sharingd` (AirDrop/Handoff) owns it.
- **Env flags:** `MI_NO_OPEN=1` (no browser), `MI_NO_PREWARM=1` (no prewarm), `MARKET_PORT`.

---

## ▶ Feature health (verify before trusting; update after touching)

| Feature | Endpoint / entry | Status | Last verified | Depends on |
|---|---|---|---|---|
| DuckDB screener (data) | `GET /api/screener?q=momentum` | ✅ WORKS | 2026-06-11 (41 rows) | duckdb **or** pyarrow fallback |
| Screener page (UI) | `GET /screener_page` (iframe tab) | ✅ WORKS | 2026-06-11 (light+dark, 41 rows, glass card) | theme-aware, no parent CSS vars; now wrapped in macOS glass card + themed body bg (changes_8) |
| Sector / Market pages | `GET /sector`, `GET /market` (iframe) | ✅ WORKS | 2026-06-11 (sector light, 23 rows) | system up/down colors + radius 16 (changes_8); theme via localStorage+postMessage |
| Landing macOS Tahoe theme | `GET /` | ✅ WORKS | 2026-06-11 (light) | reference surface; kit-faithful |
| App launch splash | `_LANDING_HTML` `#splash` overlay | ✅ WORKS | 2026-06-11 (rendered + FOUC hidden=True sync) | actual squircle_fixed.png logo; PyWebView FOUC eliminated via window.events.loaded sync; session-gated (`sessionStorage.kmkt_splash`); web-level, no rebuild needed (changes_7) |
| Launch flicker | `app.py::_apply_glass_transparency` | ⚠️ code fixed (changes_16) + **.app rebuilt & installed 06-12 06:38** — user visual confirm pending | 2026-06-12 (build.sh exit 0, dist+DMG fresh) | terminal-vs-.app difference was a stale frozen bundle; changes_17 ships the fix. If still blinking: raise 0.3s defer |
| Overseas stocks (US+JP) | `/overseas`, `/api/ov/{suggest,detail,chart,news,resolve,price}` | ✅ WORKS — unified tabbed layout (Hero + KPI grid + details + M4 quant + AI popup) | 2026-06-15 (unified layout, M4 quant paging fetch, AI popup stream; changes_37) | Naver ac autocomplete + KIS price-detail HHDFS76200200/dailyprice/news; `/api/ov/price` = lightweight HHDFS00000300 for polling; shows "실시간 · HH:MM:SS" ticker |
| World tab placement | landing `#worldCard` (under 시장 현황) | ✅ WORKS | 2026-06-12 (mktSeg+worldCard in /, worldBtn removed) | moved from topbar button to `.sector-card`; opens `/world_page` (changes_15, 피드백2) |
| Company profile card (작업2) | domestic `/dashboard` inject + overseas `/api/ov/detail` `profile_html` | ✅ domestic verified; overseas via fallback (changes_32) | 2026-06-15 (005930 DART 대표/설립/본사/홈페이지; AAPL 섹터·산업 via search fallback) | `_dart_company_profile` (DART company.json) / `_yahoo_profile` (assetProfile crumb + search fallback); `_profile_card_html`; `_inject_profile` |
| Overseas AI commentary (작업3) | 해외 report `🤖 AI 코멘터리` → `/api/llm_commentary {ov_excd,ov_symb}` | ✅ WORKS (changes_33) | 2026-06-15 (AAPL: 8.6s, 309 chars, real WWDC/버핏 news grounding) | `_build_ov_ai_context` (detail+chart+yahoo+news); reuses prefill/model-pick |
| App-wide "AI 질문하기" 에이전트 | `POST /api/llm_ask {scope,id,excd,question,user_context,think,provider}` + floating chat | ✅ WORKS — **deterministic research agent, 8 tools** (뉴스검색·기사본문·지배구조·재무·**애널리스트·동종업계·기술적**·파이썬), grounded; local/Gemini provider (changes_39/44) | 2026-06-16 (live: AAPL "목표주가·밸류·경쟁사"→FMP 펀더+애널(목표 $326)+peers+기술적; TSLA 기술적 OK) | `_agent_*` + FMP layer(`_fmp_get`/`_get_overseas_financials`/`_get_analyst_view`/`_get_valuation_peers`/`_get_price_technicals`) + `_llm_stream`/`_gemini_stream` |
| AI 의도 게이트(반사적 검색 차단) (changes_55) | `_classify_intent` → chitchat/news/deep/fin/gov/analyst/peers/tech/calc 플래그로 수집 라우팅 | ✅ WORKS (changes_55) | 2026-06-16 (안녕→수집0+친근답변; "이 화면 해석"→검색없이 화면만; "오늘 왜 올랐"→news+deep; "부채비율"→fin만) | 잡담 단축회로(0수집·280tok); `needs_search=intent.news`; 9B/12B 가정 answer 2000tok |
| AI 위젯 = 리포트 PDF 뷰어 (changes_56) | `/pdf_view` 에 위젯 주입 + KMKT_ASK `{scope:research,id:cat:nid}`; `_ask_context` 가 그 리포트 원문 읽음 | ✅ WORKS (changes_56) | 2026-06-16 (daily:36408 "3줄 요약"→리포트 본문 인용 287자, 반사검색 X) | `_research_read(cat,nid)`; 비리포트 PDF는 scope=market 폴백; 이미지PDF는 참고데이터 안내 |
| AI 팝오버 로컬/Gemini 토글 (changes_57) | `#aiPop` 상단 세그먼트 + Gemini 모델 select + 시스템프롬프트 textarea; AI 요약·해석·코멘터리 Gemini 라우팅 | ✅ WORKS (changes_57) | 2026-06-16 (commentary/summary provider=gemini 실답변; gsys "한 문장" 준수) | `/api/llm_commentary`·`/api/research_summary` `{provider,gemini_model,gsys}`; localStorage 공유(`kmkt-ai-*`); `window.kmktAiProv()` |
| AI 버튼 라벨 Local/Gemini (changes_57) | `#aiLbl` ← 로컬로드=Local / Gemini선택=Gemini / else AI | ✅ code (changes_57); ❓ visual pending | 2026-06-16 | `window.__kmktAiBtnSync`; dot-poll IIFE |
| Gemini PDF 직독 (changes_58) | 리포트 뷰어 AI(Gemini)가 PDF 원본을 multimodal inline_data 로 직접 읽음(표·OCR) | ✅ WORKS (changes_58) | 2026-06-16 (company:93565 749KB PDF→표 수치 목표가12만/PER10.3배 추출; daily 무PDF→텍스트 폴백) | `_research_pdf_bytes`; `_gemini_stream(pdf_bytes=)`; `/api/llm_ask`·`/api/research_summary` research scope; 18MB cap |
| AI 자원효율 감사 (changes_59) | research scope 뉴스검색 OFF; Gemini+PDF면 텍스트스크랩 생략; PDF바이트 10분 캐시 | ✅ WORKS (changes_59) | 2026-06-16 (research 뉴스검색 안 함 확인; summary 텍스트스크랩 스킵 확인) | `_classify_intent` research→news False; `_synth` PDF우선; `_PDF_BYTES_CACHE` TTL 600s |
| AI 답변 마크다운 기본화 (changes_60) | 리포트 'AI 요약' raw→`.kmkt-md` 렌더; CLAUDE.md §11.9 지침 | ✅ WORKS (changes_60) | 2026-06-16 (research 페이지 kmkt-md/kmktMd 확인) | 답변=`md(ansBuf)`, 추론=dim plain |
| 발열↓ 절전 (changes_60) | 전면 wallpaper 애니 idle 정지+reduced-motion; KOSPI 폴링 적응형 | ✅ code (changes_60); ❓ thermal visual pending | 2026-06-16 (kmkt-bg-off/ktTick 확인) | `body.kmkt-bg-off animation-play-state:paused`; pollKospi 장마감 30s·숨김 skip |
| 디자인 일관성 — AI 서페이스 pass1 (changes_61) | 추론박스 accent 블루 통일(종목·해외·리포트·채팅 4곳)+답변 마크다운 통일 | ✅ code (changes_61); ❓ visual pending | 2026-06-16 (blue accent 4개·gray 0 확인) | `rgba(10,132,255,.4)` border-left; `.kmkt-md` |
| 🚧 전역 디자인 일관성 (작업3 잔여) | 로더 2종(bounce/pulse)·AI버튼 종류·비AI 페이지 CSS | 🚧 후속 (GUI 필요) | 2026-06-16 | broad CSS는 GUI 확인 후 |
| US/global stock lists (작업1) | `/api/us_list?filter=` (거래대금/상승/하락/시총), `/api/global_list?country=cn\|hk\|jp\|vn` | ✅ WORKS (live) | 2026-06-16 (US: Polygon turnover MU/NVDA/TSLA; global: KIS 텐센트/토요타/빈그룹) | Polygon grouped(turnover) + FMP movers + KIS 해외(`_ov_price`) 국가별 큐레이션 |
| World 지수 카드 (네이버 형식) | `/api/world_view` cards (`info`+`spark{c,d}`) | ✅ data WORKS; ❓ visual pending (changes_46) | 2026-06-16 (다우 info 전일/고가/저가/52주 + 60p 축차트) | `_world_index_one.info`(stockItemTotalInfos) / `_index_chart`(국내); Plotly 우y축·x날짜·정보그리드·2단 |
| AI 위젯 모든 화면 (작업2) | sector/market/screener/backtest/realtime/world/world_detail/overseas/macro/index/research + **랜딩(홈)** + 리포트 | ✅ WORKS (FAB=1/page; 홈은 탭 열리면 숨김) | 2026-06-16 (changes_50) | `_inject_floating_ai`/`_LANDING_AI`(framewrap.show 감지) |
| AI 채팅 Gemini형 입력바 + 보내기↔중지 | `_ASK_WIDGET_HTML` 푸터 (`.kmkt-ai-bar` 캡슐 + `#kmktAiMenu` 모델 팝업 + `#kmktAiPlus`/`#kmktAiMic`) | ✅ **WORKS — visual verified (light+dark) + stop flow** (changes_75) | 2026-06-17 (Preview :8781: 캡슐바·모델팝업·다크 스샷; 스트림중 ■ 중지→부분텍스트 보존+⏹중지됨) | AbortController; localStorage 키 공유 유지; mic=Web Speech(미지원시 숨김) |
| AI 출력 타이핑+마크다운 통일 (작업1) | streamLLM(macro/backtest)·stock/overseas AI 모달·ask 위젯 | ✅ code (changes_50); ❓ visual pending | 2026-06-16 | 공통 `window.kmktMd` + `.kmkt-md` CSS + `.ai-cur`/`.kmkt-ai-cur` 커서 |
| AI 채팅창 이동/리사이즈 (작업2) | `_ASK_WIDGET_HTML` 헤더 드래그 + 가장자리 8방향 리사이즈 | ✅ code (changes_50); ❓ visual pending | 2026-06-16 | pointer-capture; min 300×360; `userPlaced` 가드 |
| 세계 시장 카드 차트 (작업3) | `/world_page` 지수카드 ispark + `/api/world/spark` | ✅ overflow 수정 + 카드별 일/주/월 토글 (changes_50); ❓ visual pending | 2026-06-16 | render() 순서(body 표시→그리기); `loadCardSpark`; spark endpoint OHLC60 |
| 증권사 리포트 뷰어 (작업7) | `/research_page` (📑), `/api/research`, `/research_pdf2`, `/pdf_view`(줌), `/api/research_summary` | ✅ data WORKS + **7th tab 🏦 한국은행(BOK RSS)** + **8th tab 🏛️ 금융통화위원회(BOK listCont.do)** + **PDF 확대/축소 뷰어** (changes_87); ❓ visual pending | 2026-06-18 (6 naver cats + BOK RSS + BOK MPC listCont; `/fileSrc` PDF; pdf_view zoom) | naver EUC-KR + `_bok_list`(RSS)/`_bok_read`/`_bok_mp_list`/`_bok_mp_read`(view→/fileSrc.pdf); `/pdf_view` native `#zoom=` |
| Chat markdown render | floating widget `mdToHtml` | ✅ WORKS (changes_47) | 2026-06-16 (헤더·굵게·불릿·코드; node-check OK) | `ansBuf` 누적 후 재렌더 |
| 거래소 종합시황 브리핑 | research 📊 종합시황 탭 → `/api/research_summary?cat=market` | ✅ WORKS — now **KRX 공식 API** (실제 지수·거래대금 상위) (changes_49) | 2026-06-16 (코스피 8545.98 거래대금 40조·SK하이닉스 8.9조 등 KRX 실데이터) | `_krx_market_brief`(data-dbg.krx AUTH_KEY) + KIS 시장폭 + 글로벌 + 시황뉴스 |
| KRX 공식 Open API | `_krx_api(path,basDd)` (data-dbg.krx, AUTH_KEY=KRX_KEY) | ✅ WORKS (changes_49) | 2026-06-16 (kospi/kosdaq_dd_trd, stk_bydd_trd) | 문서 API_documents/KRX_API_tem; ETF·채권·금·선물·옵션 등 다수 미사용분 |
| AI on-screen context (작업1) | `_ask_context` stock=기업정보(DART) / research=리포트 본문 자동 읽기 | ✅ WORKS (changes_49) | 2026-06-16 | DART profile facts; research top-2 본문 + 현재 cat 전달 |
| World index cards chart | candlestick (국내 동일 툴) | ✅ data WORKS (changes_49) | 2026-06-16 (OHLC 60봉; node-check OK) | `_wv_spark` OHLC; Plotly candlestick #C0392B/#2E75B6 |
| Realtime/index roll direction | `updateHero` tickUp | ✅ FIXED (changes_47) | 2026-06-16 | 직전 표시값 대비 px>=lastPx (§12); 전일대비 부호와 분리 |
| Backtester form/autocomplete | `/backtest_page` `#formPanel`/`.sgg` | ✅ FIXED (changes_47) | 2026-06-16 | backdrop-filter stacking → formPanel z30/sgg z1000; 종목 flex 채움 |
| 해외 재무건전성 (피드백) | agent tool `_get_overseas_financials(symb)` (Finnhub) | ✅ WORKS | 2026-06-16 (TSLA: 유동2.04/당좌1.44/D-E0.11/ROE4.77%…) | Finnhub `/stock/metric`; agent fires on 재무/건전성/유동 keywords for scope=ov |
| AI provider 선택 (작업9) | `/api/llm_ask {provider:local\|gemini}` + chat 세그먼트 | ✅ local WORKS; ✅ Gemini plain-call 200 (changes_52). 검색 그라운딩만 billing 필요 → 미연결 시 429 (search-off 폴백) | 2026-06-16 (plain 200, grounded 429 실측) | `_gemini_stream` streamGenerateContent, 1 call/Q (deterministic gather feeds it); `GEMINI_KEY`; `KMKT_GEMINI_MODEL` |
| Gemini 모델 picker + 검색 그라운딩 (작업1·2) | `/api/llm_ask {gemini_model}` + `#kmktAiGModel` select | ✅ wired; ✅ plain 200; grounded 429 시 **검색끄고 1회 자동재시도**(changes_52) | 2026-06-16 | `_GEMINI_MODELS`(3.5-flash 기본/3.1-pro/2.5-flash/3.1-lite); `_gemini_stream(model,use_search,4096,history)` |
| Gemini 멀티턴 메모리 (작업2/52) | chat `convo[]` → `history` (gemini만), `_gemini_stream(history)` → contents prepend | ✅ code+endpoint accepts (changes_52); ❓ visual pending | 2026-06-16 (history 전송 시 meta 200, no 400) | 1500자/턴·12턴 cap; 닫으면 휘발; local은 stateless |
| Gemini 클라우드-극대화 프롬프트 (작업3/52) | gemini만 `_GEMINI_SYS_ADDENDUM` (구조적 심층 분석) | ✅ code (changes_52); ❓ 품질 visual pending | 2026-06-16 | 결론·근거·리스크·점검 구조; grounding 가드 유지 |
| Gemini 검색=2.5만 안내 (작업4/52) | gemini+needs_search+model≠2.5-flash → ℹ️ 안내 reasoning | ✅ WORKS (changes_52) | 2026-06-16 (decoded SSE에서 안내문 확인) | billing 미연결 환경: 2.5-flash만 grounding 동작 |
| AI가 세계 시장 화면 읽기 (changes_53) | `_ask_context(scope=world,id=view)` → `_world_ai_text` (지수·KPI·리스트 직렬화) | ✅ WORKS (changes_53) | 2026-06-16 (world/us+gemini: 답변이 "나스닥 +3.07%" 등 화면값 인용, 빈데이터 불평 사라짐) | `render()`가 `window.__wview` 설정 → KMKT_ASK `{scope:world,id:view}`; `_WORLDVIEW_CACHE` 재사용 |
| Gemini 모델 선택 라우팅 (재검증) | dropdown `gemini_model` → server validate → meta+답변 모델 일치 | ✅ WORKS (changes_53) | 2026-06-16 (3.5-flash/2.5-flash 모두 meta.model 일치, 1239~1360자 답변) | `_GEMINI_MODELS` 검증; 잘못된 값은 `_GEMINI_DEFAULT` |
| AI가 모든 화면 읽기 (changes_54) | `_ask_context` market/backtest 분기 추가 → `_market_ai_text` | ✅ WORKS (changes_54) | 2026-06-16 (backtest+2.5: 답변이 "코스피 8,726.60 +2.11%" 화면값 인용) | 코스피/코스닥+시총상위20; 모든 scope 비어있지 않음 |
| Gemini 무료티어 모델 게이팅 (changes_54) | 카탈로그=무료모델만(Pro Preview 제외), 검색=2.5계열만 | ✅ WORKS (changes_54) | 2026-06-16 (3.5→검색OFF+안내, 2.5→검색ON; 제거모델→기본값 무오류) | `_GEMINI_SEARCH_OK`; `use_search=needs_search&2.5`; thinkingBudget로 thought 누출 차단 |
| AI 검색필요 시 모델 자동전환 (작업5) | llm_ask `needs_search & !tool_used & local & GEMINI_KEY → gemini` | ✅ WORKS (changes_51) | 2026-06-16 (양 분기 라이브 확인: 뉴스있음→local, 빈수집→gemini) | `_SEARCH_KW`; meta 이벤트로 전환 표시 |
| AI 메시지 모델 아바타 (작업6) | chat 어시스턴트 메시지 ✦Gemini/✨로컬 + 모델명 | ✅ code (changes_51); ❓ visual pending | 2026-06-16 | SSE `meta{provider,model,name}` → `setWho()`; `_short_model_name` |
| AI 로컬 미로드 안내 + 선택 기억 (작업4) | chat 입력창 placeholder + localStorage | ✅ code (changes_51); ❓ visual pending | 2026-06-16 | `/api/llm/loaded` → "로컬 LLM 모델을 로드해 주세요."; `kmkt-ai-prov`/`kmkt-ai-gmodel` 복원 |
| AI 채팅 Mac 리사이즈 핸들 (작업3) | `.kmkt-ai-rs-*` 8핸들 (리포트 `.mi-rs` 방식) | ✅ code (changes_51); ❓ visual pending | 2026-06-16 | ns/ew/nesw/nwse-resize 커서; 헤더 드래그 이동 유지 |
| AI 버튼 로드상태 점 (작업5) | landing ✨AI `#aiDot` ← `/api/llm/loaded` (30s) | ✅ WORKS | 2026-06-16 (loaded:true → green) | lightweight `/api/v0/models` check; `document.hidden` guard |
| AI 심층 추론 토글 (작업5) | floating chat `#kmktAiThink` → `think` | ✅ wired; ❓ visual pending | 2026-06-16 (param threads to `_llm_stream`) | skips reasoning-suppress prefill / adds CoT for instruct |
| 글로벌 미국금리 (FRED) | `_global_macro_snapshot` via `FREED_KEY` | ✅ WORKS | 2026-06-16 (DGS10 4.45% / FEDFUNDS 3.63%) | `api_documents/API.env` now loaded; `_fred_one` |
| Overseas M4 quant CSS | `/overseas` 🚀 M4 탭 | ✅ code fixed; ❓ visual pending (changes_39) | 2026-06-16 (`_M4_STYLE` injected; m4-met-grid present) | page had only partial M4 CSS → cards light/metrics stacked; full `_M4_STYLE` now in `<head>` |
| Floating AI chat UI (작업2) | `_ASK_WIDGET_HTML` FAB+popup injected once at `</body>` on report/overseas/macro/index | ✅ markup verified (fab:1/page, body-direct), JS node-syntax OK; ❓ visual/drag/animation pending (changes_38) | 2026-06-16 (test_client: fab:1 win:1; node --check OK) | draggable FAB (localStorage pos) + ephemeral on close; light/dark via `kmkt-ai-dark`; reuses `window.KMKT_ASK()` |
| Global macro indicators (작업4) | `GET /api/global_macro` + 🌐 card on `/macro_page` | ✅ WORKS (live) | 2026-06-16 (6/6 rows live: S&P/나스닥/VIX/달러인덱스/금/WTI + 5 해석 points) | Naver `/index/{.INX,.IXIC,.VIX}` + `/marketindex/{exchange .DXY, metals GCcv1, energy CLcv1}`; `_global_macro_snapshot` 60s cache; also feeds `_macro_text` AI ctx |
| Overseas mktcap / chart (작업3) | `/overseas` KPI `#kpiMcap` + `#plotlyChart` | ✅ code fixed; ❓ visual pending (changes_38) | 2026-06-16 (py_compile OK) | `fmtMcap()` 억→조 compaction + `.k-val` overflow guard; candlestick now filled + domestic `candle_chart()` colors (#C0392B/#2E75B6, MA 2E8B57/C0392B/E08E3C/7030A0) |
| Built-in backtester | `/backtest_page`, `GET /api/backtest` (🧪 card) | ✅ WORKS | 2026-06-12 (005930 SMA 5y: +337.8% vs bench +391.4%, MDD -28 vs -43; bh≡bench sanity) | SMA/MOM/RSI/BH, no look-ahead, cost bp; data via `_afetch` parquet+Naver; NumPy local — no Docker/account (changes_17) |
| World detail charts | `/world_detail`, `GET /api/world/chart` | ✅ WORKS | 2026-06-12 (.DJI/.N225 110 candles day/week/month; FX 300d line+table) | world_page cells clickable (foreign idx + FX; KR rows excluded — that Naver domestic path returns []); generic `miOpenUrlTab` (changes_17) |
| Landing UI polish | `.btn-glass`, `.mkt-seg` HIG segmented | ✅ WORKS (markup verified; visual = web-level, no rebuild needed) | 2026-06-12 (m4-badge gone, glass buttons, recessed-track toggle) | Figma MCP checked — file still Cover-only (trap #13) → Tahoe kit tokens + HIG (changes_17) |
| Local AI commentary | `POST /api/llm_commentary` (SSE, `{code}`/`mode`) | ✅ WORKS — **reasoning models fixed via Assistant-Prefill** (changes_30) | 2026-06-15 (live SSE macro w/ qwen3.5-9b: first 2.2s, 529 clean answer chars, reason 0, finish=stop, no endnote; 4b/gemma clean too; loaded-model-first, no 2nd JIT-load) | LM Studio; `_pick_llm_model_ex()`; `_llm_model_profile()` w/ `prefill:"<think>\n\n</think>"` for reasoning; `_build_ai_context()`; env `KMKT_LLM_MODEL` |
| Local AI popover (`#aiPop`) | landing AI button → `/api/llm/{status,load,unload}` | ⚠️ status/context ✅ verified; stays-open-on-Load logic-only (visual pending) (changes_30) | 2026-06-15 (status returns per-model max_ctx 256K / loaded_ctx 8192 / def_tokens / rec range — observed; mousedown close not yet browser-confirmed) | `_llm_status()` adds kind/max_ctx/loaded_ctx/def_tokens/rec_ctx_lo·hi; outside-close on `mousedown`; `aipTokModel` guard |
| Screen transitions | `activate()`, `closeTab()`, `goHome()`, overlay, tabstrip, `.sg`, Spotlight | ❓ UNVERIFIED (syntax OK) | 2026-06-11 (py_compile pass) | CSS `transition` on opacity/transform; `.framewrap.exit` upward slide; overlay opacity fade; `.empty.hide` class; tabstrip `max-height`; `.sg` symmetric fade; Spotlight symmetric scale+fade (changes_8) |
| Spotlight (Cmd+K) | landing JS + `/suggest` | ❓ UNVERIFIED this session | changes_0, changes_8 (exit anim) | opacity+pointer-events; symmetric enter/exit |
| Dock right-click menu | PyObjC `applicationDockMenu:` | ❓ UNVERIFIED this session | changes_0 | macOS only |
| Power Saving Mode | `appBecameActive_` / `MI_APP_ACTIVE` | ✅ WORKS | 2026-06-11 (pauses rAF and polling for both inactive app and background tabs) | native Cocoa NSNotification + JS polling hooks + iframe postMessage (changes_10) |
| Index/price snapshot fallback | `_kis_index`, `_kis_price` | ❓ UNVERIFIED this session | changes_1/2 | KIS API / Naver / snapshot json |
| Realtime desk page (UI) | `GET /realtime_page` (📡 실시간 tab) | ✅ WORKS (Chart sync & URL param fixed in changes_20) | 2026-06-12 | Toss-style: colored hero+rolling digits, 3-col grid, canvas candlestick chart (now dynamic), accepts `?code=`; py_compile OK; visual unverified |
| Overseas stocks hero UI | `GET /overseas` (히어로 블록) | ✅ WORKS (Grid layout & domestic hero sync in changes_20) | 2026-06-12 | 2-col main grid matching domestic, floating rounded hero, rolling digit animation; py_compile OK; visual unverified |
| Orderbook snapshot | `GET /api/rt/orderbook?code=` | ✅ WORKS | 2026-06-12 (005930 live 10-level REST FHKST01010200) | KIS keys (in-process OK) |
| Live screener (rank) | `GET /api/rt/screener?mkt=&blng=` | ✅ WORKS | 2026-06-12 (live volume-rank FHPST01710000 rows) | KIS keys |
| Supply-demand flows | `GET /api/rt/flows?code=&mkt=` | ⚠️ investor live; program passthrough | 2026-06-12 (005930 frgn/orgn/prsn live; 당일은 장후) | inquire-investor FHKST01010900 + HHPPG046600C1 |
| Paper trading (local sim) | `/api/paper/state\|order\|reset` | ✅ WORKS | 2026-06-12 (buy 005930 fill 299000, cash math EXACT) | SQLite `~/.cache/kmkt_m4/paper.db`; marks via `_kis_price`; **no real orders** |
| Realtime WS→SSE bridge | `GET /api/rt/stream?code=` (SSE) | ⚠️ SSE+REST-seed verified; live WS ticks ❓ | 2026-06-12 (2048B frame, REST-seeded book) | live H0STASP0/H0STCNT0 need KRX 09:00–15:30; `_RT_STATE` + idle-stop 30s (changes_12) |
| World Market 3-view (작업1) | `GET /world_page`, `GET /api/world_view?view=kr\|us\|global` | ✅ data WORKS; ❓ visual pending (changes_42) | 2026-06-16 (us 3cards+40list, global 6cards, kr 코스피8545+30list; all sparklines) | `_world_view`: `_world_index_one`/`_world_domestic_one` + `_world_chart`/`_index_chart` sparks + `_global_macro_snapshot` KPIs + `_usmap_pct`(US list) + `_sector_stocks`(KR list); marketmap/heatmap slot |
| US S&P500 heatmap (작업1) | World page 🇺🇸 섹터 트리맵 (전체/NYSE/NASDAQ) + `/api/usmap?exch=` | ✅ data WORKS; ❓ visual pending (changes_41) | 2026-06-16 (all=71/nyse=47/nasdaq=30 tiles; 4.5s first then cached) | `_US_HEATMAP` curated ~59 names + `_usmap_pct` (Finnhub /quote, 1 fetch shared by 3 views, 120s); green-up colors |
| Domestic marketmap placement (작업2) | `/market` `.ovw`→🗺️마켓맵→시총상위 | ✅ already positioned (cards→map→list) | 2026-06-16 (confirmed in `_MARKET_HTML`) | existing `/api/marketmap`; no change needed |

| 핵심 순수함수 회귀 테스트 (외부평가 #1) | `tests/test_core_functions.py` (`uv run pytest`) | ✅ WORKS — 26/26 pass | 2026-06-17 (Py3.10 sandbox, 26 passed in 0.23s) | `_krx_won`·`_cu`·`_risk_stats`·`_clean_closes`·`_is_open_day`·`_sse_*` 순수함수만; 네트워크 0. ⚠ `fmtMcap`은 JS-only라 제외(`_krx_won`로 대체). 레거시 archive 모듈은 테스트가 스텁으로 격리(트랩#35) |
| Developer Mode (changes_81/82) | `KMKT_DEV=1` → ⌘⇧D; `/api/dev/{locate,note,session/*}` → `dev_notes/*.md` | ✅ WORKS — backend(주입·grep·노트·세션·부모역추적) headless 검증 + 오버레이/팝오버/세션패널 시각 스샷 | 2026-06-17 (locate가 ui_templates.py 실라인; 세션 add/save→session_*.md TODO; ancestor만으로도 매칭; DEV OFF시 골든 불변) | `scripts/dev_overlay.py`; after_request 주입; env gate; in-proc `_DEV_SESSION`; spec hiddenimports |
| `_inject_*` 앵커 실패 로깅 (외부평가 #4) | `_inject_m4_tab`/`_fx`/`_realtime`/`_loader`/`_floating_ai` | ✅ code (py_compile OK, 26 tests green); ❓ 런타임 경고출력 visual pending | 2026-06-17 | 앵커(`</nav>`/`<footer`/`</head>`/`</body>`/swap) 미발견 시 `logger.warning` (로직 불변). `logging.basicConfig(WARNING)`+`logger=getLogger("kmkt")` |
| `.gitignore` API키 보강 (외부평가 #5) | repo-root `.gitignore` | ✅ rules added; ❓ `git check-ignore` 미검증(샌드박스 마운트가 git work-tree 아님) | 2026-06-17 | `*.env`/`**/*.env`/`**/API.env`/`**/API_Key_*.env`/`**/한국투자증권/` 추가. 현재 추적 키파일 0건(확인). 사용자 머신에서 `git check-ignore -v .env` 로 최종 확인 권장 |
| changes_history 통합 (외부평가 #7) | `application_build/changes_history/` ← root fork | ✅ DONE (copy) | 2026-06-17 | root 7–15 → canonical 62–70 복사·재넘버링; root에 `MOVED.md`. 원본 보존(삭제는 후속 세션) |
| Hooks 회귀 게이트 자동강제 (changes_88) | `.claude/settings.json` PostToolUse→`mark`/Stop→`gate` (`scripts/hooks/gate_dispatch.py`) | ✅ WORKS — sentinel+Stop 설계: 백엔드 편집 후 Stop 에서 smoke 1회, FAIL→exit2(턴 차단), stop_hook_active 가드 | 2026-06-19 (mark gated/non-gated/subdir 격리, gate PASS rc0·induced FAIL rc2·guard rc0 실측) | smoke_check 1.13s network-free; hooks/·reflect/ 는 비게이트(백엔드 미import) |
| SessionStart trap/health 다이제스트 (changes_88) | `scripts/hooks/session_brief.py` | ✅ WORKS — ~9줄 캡 주입(health WARN+dev_notes 적체+최신 trap 5개) | 2026-06-19 (실측 출력 확인) | _STATUS 444줄 재독 대신 토큰 절약; fail-open |
| 교정 자동포착·정본 가드반영 (changes_88) | `scripts/reflect/{capture,apply}.py` (UserPromptSubmit/Stop) | ✅ WORKS — capture 다국어 스코어(floor 0.75), apply 3가드(백업·구조검증+smoke·출처로그)+2단 게이팅; **기본 propose(정본 자동수정 OFF)** | 2026-06-19 (capture 4/5, propose→dev_notes, auto≥0.90 가드write+undo, **golden깨면 auto-rollback** 실측; _STATUS sha256 불변) | `KMKT_REFLECT_MODE=auto` + ≥0.90 만 정본; 트랩#42; `apply.py --undo` |
| 파일/폴더 구조 정리 (changes_73) | 루트·application_build·scripts 정돈 | ✅ verified (compile OK, 26 tests, live paths OK) | 2026-06-17 | mv-only. tests/legacy·docs/legacy·application_build/_archive/icon_attempts 신설; scripts 레거시 4개→archive. **API.env(루트)·app_icon_final/·AGENTS/ANTIGRAVITY.md·icon.png/icns 는 라이브/사용자결정으로 미이동** |

Legend: ✅ verified working · ⚠️ works with a precondition · ❌ broken · ❓ not verified by the latest agent.

---

## ▶ 미검증 소거 대기열 (세션당 1~2개 확인 목표)

> 도입: 2026-06-17 (외부 평가 #2 — "선언된 상태 ≠ 실제 동작" 간극 추적).
> 확인 방법: 앱 실행(`uv run application_build/app.py`) 후 해당 기능을 **직접 눈으로 확인** →
> ✅/❌ 로 위 Feature health 표를 갱신하고, 본 대기열에서 해당 행을 제거(또는 ✔ 표시).
> ⚠️ 대부분 GUI/시각 항목이라 headless 로는 소거 불가 — 실제 앱 실행이 필요하다(정직하게 ❓ 유지).
> **운영 루프(§2)에 합류:** 세션 시작 시 이 대기열에서 할 수 있는 항목을 **1개 이상** 확인할 것.

| 항목 | 확인 방법 | 우선순위 |
|------|-----------|---------|
| Screen transitions (activate/closeTab/goHome) | 탭 전환 시 슬라이드/페이드 애니가 부드러운지 | 높음 |
| Spotlight (Cmd+K) | Cmd+K → 검색창 등장/퇴장이 대칭(scale+fade)인지 | 높음 |
| Launch flicker fix (`_apply_glass_transparency`, changes_16/17) | `.app` 실행 시 흰 화면 깜박임 없는지(스플래시 전 데스크톱 노출 X) | 높음 |
| Floating AI chat UI (드래그·애니·라이트/다크) | FAB 드래그 이동, 팝업 열림 애니, 닫으면 대화 휘발 | 높음 |
| AI 채팅창 이동/리사이즈 (8방향 핸들) | 헤더 드래그 이동 + 가장자리 리사이즈(min 300×360) | 중간 |
| AI 출력 타이핑+마크다운 통일 (`kmkt-md`) | 답변이 마크다운 렌더(굵게/불릿/헤더), raw `**` 안 보임 | 중간 |
| AI 메시지 모델 아바타 (✦Gemini/✨로컬) | 어시스턴트 메시지에 provider/모델명 배지 표시 | 중간 |
| AI 로컬 미로드 안내 + 선택 기억 | 모델 미로드 시 placeholder 안내, 재방문 시 provider/모델 복원 | 중간 |
| AI 심층 추론 토글 (`#kmktAiThink`) | 토글 ON 시 추론 박스 출력(instruct에 CoT) | 중간 |
| AI 버튼 라벨 Local/Gemini (`#aiLbl`) | 로컬로드=Local / Gemini선택=Gemini / else AI 로 라벨 갱신 | 낮음 |
| Gemini 멀티턴 메모리 | 대화 이어가기 시 직전 맥락 반영(닫으면 휘발) | 중간 |
| Gemini 클라우드-극대화 프롬프트 품질 | 결론·근거·리스크·점검 구조로 답하는지(품질) | 낮음 |
| World 지수 카드 (네이버 형식) | 다우 등 카드의 우y축 차트·정보그리드(52주/전일/고저) 렌더 | 중간 |
| 세계 시장 카드 차트 (일/주/월 토글) | `/world_page` 지수카드 스파크라인 overflow 없이 토글 동작 | 중간 |
| World Market 3-view (kr/us/global) | 토글별 카드·리스트·스파크라인 시각 정상 | 중간 |
| US S&P500 heatmap (전체/NYSE/NASDAQ) | 트리맵 타일 색(초록상승)·토글 시각 | 낮음 |
| 증권사 리포트 뷰어 + PDF 줌 | `/research_page` 6+1 탭, PDF `#zoom=` 툴바 동작 | 중간 |
| Overseas M4 quant CSS / mktcap·chart | 🚀 M4 탭 카드 다크·지표 그리드; 시총 overflow 없음 | 중간 |
| 발열↓ 절전 (idle 애니 정지) | idle 시 wallpaper 애니 멈춤(`kmkt-bg-off`), 발열 체감 | 낮음 |
| 디자인 일관성 — AI 서페이스(추론박스 블루) | 종목·해외·리포트·채팅 4곳 추론박스 accent 통일 | 낮음 |
| Realtime WS→SSE live ticks | KRX 장중(09:00–15:30) 📡 실시간에서 `book.src=="ws"` + 체결 히트맵 이동 | 중간(장중 한정) |
| Index/price snapshot fallback | KIS→네이버→snapshot 폴백 경로 실제 값 표시 | 중간 |
| Dock right-click menu (PyObjC) | Dock 아이콘 우클릭 메뉴 표시(macOS) | 낮음 |

---

## ▶ Active traps (hard-won; ignore at your peril)

1. **Embedded iframe pages get NO parent CSS variables.** `/screener_page`,
   `/sector`, `/market` load as `<iframe>`. `color: var(--label, #fff)` resolved
   to white-on-transparent → invisible "blank" page. Always use *explicit* colors
   and sync theme via `localStorage('kmkt-theme')` + `postMessage({kmkt})` (same-origin).
2. **Flask SSE: read `request.*` OUTSIDE the generator.** A streaming generator runs
   *after* the request context is popped → `request.json` inside it raises
   `RuntimeError: Working outside of request context` (→ HTTP 500 every time).
   Read the body in the view function, pass values into the closure.
3. **Imports used in `except` must be imported before the `try` that can fail early.**
   `import json` inside a `try` whose first line throws → `UnboundLocalError: json`
   masks the real error. Import at view-function top.
4. **`duckdb`/`mlx` are NOT in `.venv-build` yet** (it was created before they were
   added to `requirements.txt`). The built `.app` therefore lacked duckdb → screener
   `No module named 'duckdb'`. Runtime is now **safe regardless** via a pyarrow
   fallback (`_screener_rows_pandas`), but a clean rebuild should re-run
   `pip install -r requirements.txt` so the fast duckdb path is present.
5. **One code may have multiple parquet files** (`chart_{code}_160`, `_2400`, …).
   Joining on code alone = cartesian product = duplicate rows. Pick the file with the
   most rows per code (longest history) before computing.
6. **LM Studio cold-loads models on first request** (auto-evicts when idle). First
   token can take 10s–minutes for 9–12B. Mitigation: small model (3–4B) + "keep
   loaded" in LM Studio; backend timeout is 300s. Not a hardware limit on M4 Pro.
7. **Shell `_safe_eval` hook** intermittently fails `cd`, absolute-path `ls`, and
   network calls. Use `uv run --directory <root>`, Python for file ops, and
   `python3 -m py_compile "<abs>"` to compile-check.
8. **Auto-shutdown watchdog kills headless tests.** `_monitor_heartbeat`
   (`_PING_TIMEOUT = 15s`) `os._exit(0)`s the server if no `/__ping` for 15s. The real
   app pings ~every 2s (`miPing`); a `curl`/script test without a keepalive ping loop
   gets the server killed mid-request (truncated/empty response — looks like a bug but
   isn't). When testing endpoints headless, run a background `/__ping` loop every ~2s.
9. **LM Studio model pick is explicit, not `data[0]`.** `/v1/models` order is unstable
   and includes embedding + 9B/12B models; `_pick_llm_model()` deterministically prefers
   `qwen3-4b-2507`, excludes `embed`, and deprioritizes `thinking`/`vl`. Force any model
   with env `KMKT_LLM_MODEL`. Prefer a non-thinking Instruct model for low latency.
10. **KIS [141] `FID_INPUT_ISCD` does NOT filter by stock.** The 종합시황·공시 news-title
    endpoint returns market-wide / large-cap news regardless of the code you pass (e.g.
    009150 query returns mostly 005930/000660/KOSPI rows). Using it raw makes the LLM
    misattribute other stocks' news (삼성전기↔삼성전자 "삼전닉스"). Always filter rows by
    matching the target `code` against the row's `iscd1..iscd10` tags and drop non-matches
    (`_kis_stock_news`, changes_7). No match ⇒ omit news, don't pad.
11. **This app's data is a simulated/future dataset.** KOSPI ~7,721, 삼성전기 ~1.8M KRW,
    60d momentum +350% — these are dataset-real, not bad ticks. Do not "correct" large
    price/momentum magnitudes; only guard genuine single-tick outliers (52w percentile clamp).
12. **iframe pages must paint their own `body` background** (don't leave it `transparent`).
    `.framewrap .frame` has a hardcoded `background:#fff`, so a transparent iframe body shows
    white in dark mode → light text on white = invisible. Set `body{background:var(--bg)}`
    with a `html.dark` override (screener fixed in changes_8; sector/market already did this).
13. **macOS Tahoe kit tokens are the UI yardstick** (memory `macos26-theme.md`): blur 50px /
    saturate 180%, system blue #007AFF, up/down #FF3B30(#FF453A)/#2E75B6(#64B5FF), radii
    pill100/glass26/lg16/md11, ease cubic-bezier(.32,.72,0,1), SF Pro scale. Landing `GET /`
    is the reference implementation — match new UI to it. The Figma duplicate
    (`a6AegNuDiPrlC5qdbXbn9R`) only holds the Cover, so rely on these extracted tokens + HIG.
14. **Preview MCP needs `.claude/launch.json` in the cwd** (`application_build/`), and it
    refuses to reuse a non-preview server on the same port — free the port first, then
    `preview_start` launches its own. Keep a `/__ping` loop alive (trap #8) while navigating
    to non-landing pages, since only the landing self-pings.
15. **Launch splash is session-gated + faster than headless tooling.** The `#splash` overlay
    (changes_9) shows once per WebView session (`sessionStorage.kmkt_splash`) and auto-removes
    after ~1.85s — shorter than a preview eval/screenshot round-trip, so a live screenshot
    almost always misses it. To inspect: `curl /` to grab the `<div id="splash">…</div>` block
    and re-inject it via `insertAdjacentHTML` (inserted `<script>` won't run, so it persists),
    then screenshot. To replay a real load: `sessionStorage.removeItem('kmkt_splash')`.
16. **Realtime WS data only flows during KRX open (09:00–15:30 KST).** The realtime desk's
    live 호가/체결 (`H0STASP0`/`H0STCNT0`, 체결 히트맵, 체결강도) need market hours. Outside
    them, `/api/rt/stream` correctly REST-seeds the orderbook and the heatmap stays empty —
    that is *not* a bug. To verify live ticks, open 📡 실시간 during the session and confirm
    `book.src=="ws"` + moving heatmap dots. REST orderbook/screener/flows work anytime.
17. **Naver/KIS world-data quirks (changes_17).** ① `ac.stock.naver.com/ac?q=&target=stock` is
    the only Korean-name autocomplete for overseas tickers (typeCode NASDAQ/NYSE/AMEX/TOKYO).
    ② `marketindex/exchange/{pair}/prices` hard-caps `pageSize` at 60 (>60 ⇒ non-JSON error) —
    paginate. ③ KIS overseas news [HHPSTH60100C1] has no JP `NATION_CD` (only 공백/CN/HK/US) and
    `SYMB=` per-stock filter usually returns nothing ⇒ fall back symbol→nation→global.
    ④ `api.stock.naver.com/chart/domestic/index/KOSPI/day` returns `[]` — use KIS for domestic
    indices; the `chart/foreign/index/{reuters}` endpoint works (110 bars, day/week/month).
18. **A dead backend looks exactly like an SSE bug.** While testing `/api/rt/stream` headless,
    an "empty stream" was actually the watchdog (trap#8) `os._exit(0)`-ing the server during
    the multi-second *gap between tool calls* (pings only run inside one bash invocation). Run
    the server start + ping loop + the SSE read **in a single invocation**; an aborted stream
    also isn't logged by werkzeug, so absence of a log line ≠ request never arrived.
19. **Reasoning LLMs (qwen3.5-9b 등) emit ZERO answer `content` for short tasks** — they dump everything into
    `delta.reasoning_content` and hit `finish_reason=length` (0 answer chars at 3600 tok / 119 s, measured).
    `/no_think`, `enable_thinking:false`, `chat_template_kwargs` are all **ignored** by LM Studio's fast path.
    ✅ **SOLUTION (changes_30): Assistant Prefilling** — append `{"role":"assistant","content":"<think>\n\n</think>"}`
    to `messages`; the engine treats thinking as done → `reasoning_tokens=0`, `finish_reason=stop`, immediate clean
    answer (qwen3.5-9b: first 1.7s, 754 chars — measured). `_llm_model_profile()` carries `prefill`; endpoint
    appends it; strip leading `\n`/`</think>` off the first chunk. Kept as safety: dim 추론 stream + Instruct
    end-note if a reasoning model *still* yields no content. (Picker still prefers a *loaded* model — trap #20.)
20. **`/v1/models` lists ALL downloaded models, not just loaded ones** (LM Studio JIT mode). Picking from it and
    POSTing an unloaded id makes LM Studio JIT-load a 2nd model → two models resident at once. Use
    `/api/v0/models` (has `state:"loaded"`) to know what is actually loaded (`_llm_chat_models_with_state`).
21. **Realtime/grid overflow:** grid children default `min-width:auto` → long numbers overflow. Use
    `minmax(0,1fr)` + `min-width:0` + ellipsis (changes_31, guideline §10.2).
22. **Yahoo `quoteSummary` needs cookie+crumb now** (bare v10 → HTTP 401); rapid hits → 429 IP cooldown.
    `_yahoo_session()` seeds finance.yahoo.com cookie + `v1/test/getcrumb` (cached ~50min). When it 401/429s,
    `_yahoo_profile` falls back to the **no-auth** `v1/finance/search` (sector/industry/exchange) so the
    overseas 기업 개요 card is never blank. 6h profile cache. Real (infrequent) usage rarely throttles.
21. **`\n` in a RAW page string (`r"""…"""`) is two backslashes, not LF.** `_MACRO_HTML`/`_BACKTEST_HTML`/
    `_INDEX_HTML`/… are `r"""`. JS `buf.split('\\n')` / `.replace(/\\n/g,…)` / `.join('\\n')` written there
    reach the browser as backslash+n, so SSE line-splitting on real LF silently fails → **the AI box renders
    nothing for any model** (this killed 경제지표·백테스팅 commentary; the stock modal `_AI_SCRIPT` is non-raw so
    it worked). In raw pages use **single** `'\n'`. Same trap for `\uXXXX` emoji escapes — use the literal char
    (💭/추론) in raw strings. (changes_29)

23. **`position:fixed` widgets must be injected body-direct (`</body>`), not inside a card/pane.**
    Reports apply CSS `transform` to `.card`/`.pane` (FX tilt, `m4PaneIn`), which re-roots any
    descendant `position:fixed` to that ancestor → the floating AI FAB/window would mis-position.
    `_inject_ask` and the overseas/macro/index injections all append at the **last `</body>`**
    (changes_38). The floating widget must render exactly **once per page** (verify: `fab:1 win:1`).
24. **Naver auth-free global indicators (changes_38, probed live).** Indices/VIX via
    `/index/{code}/basic` (`.INX` S&P, `.IXIC` 나스닥, `.VIX`). Commodities/dollar via
    `/marketindex/{cat}` list (`metals`→`GCcv1` 금, `energy`→`CLcv1` WTI; `exchange`→`normalList`
    →`.DXY` 달러인덱스). **No US Treasury yield / Fed funds** on Naver (`.TNX` etc → 409,
    `/marketindex/bond` → 404); would need FRED (no key) or ECOS international tables.
25. **Non-raw page strings use `\\n` for a JS string-literal newline.** `_ASK_WIDGET_HTML` is a
    plain `"""…"""` (not `r"""`), so SSE line-splitting `buf.split('\\n')` and `replace(/\\n/g,…)`
    are written with `\\n` (→ JS `'\n'`). Verified via `node --check` on the rendered script.
    (Contrast trap #21 which is about *raw* `r"""` pages needing single `'\n'`.)

26. **Local ~4B models do NOT reliably call tools — neither free-text ("SEARCH: …") nor native
    OpenAI `tools=[…]`.** Measured: qwen3-4b-2507 with a `web_search` tool returned `tool_calls:[]`
    and hallucinated. So **do not build agents that rely on the model deciding to use a tool.** Drive
    tool use deterministically from question keywords/heuristics, gather data first, then force the
    model to answer ONLY from the gathered data (`/api/llm_ask` deterministic agent, changes_39).
    The changes_38 model-driven ReAct loop was abandoned for this reason.
27. **KIS overseas `tomv` = raw listing-currency market cap, not 억.** NVDA ≈ 5.11e12 USD →
    format with currency symbol + T/B/M (`fmtMcap(v,curr)`), never label as 억/조.
28. **Naver research pages are EUC-KR.** `finance.naver.com/research/{slug}_list.naver` /
    `{slug}_read.naver` must be `.decode("euc-kr")` explicitly; `_fetch_url_text`'s charset sniff
    mis-decodes them to mojibake. Slugs: daily=market_info, company=company, industry=industry,
    invest=invest, economy=economy, debenture=debenture. PDF needs `Referer: finance.naver.com`.
29. **FRED key is `FREED_KEY` (typo) in `api_documents/API.env`** — which the app now loads
    (override=False) in addition to root `.env`. Root `.env` holds NAVER/DART/FSC/KIS keys.

30. **`backdrop-filter`(글라스 패널)은 독립 stacking context 를 만든다.** 패널 내부의 `position:absolute`
    드롭다운(자동완성 등)은 z-index 를 높여도 *그 패널의* 컨텍스트에 갇혀, DOM 상 뒤에 오는 다른 글라스
    패널에 가려진다. 해결: 드롭다운이 있는 패널 자체에 `position:relative;z-index:(높게)` 부여
    (백테스터 자동완성, changes_47). 일반 모달은 `position:fixed`+body직속이 더 안전(트랩#23 참고).
31. **PDF 확대/축소는 pdf.js 없이 네이티브 `#zoom=` 로.** WKWebView/Chromium PDF 뷰어는 iframe src
    뒤에 `#zoom=page-width|NN&toolbar=0` 프래그먼트를 지원. `/pdf_view?src=`(same-origin only)로 감싸
    줌 툴바 제공(changes_47). 한국은행 PDF=`/fileSrc/...pdf`, 증권사=stock.pstatic.net(Referer 필요).

32. **Gemini Google Search 그라운딩은 billing-enabled 프로젝트에서만 동작.** 빌링 미연결 AI Studio 키는
    *일반* `streamGenerateContent` 는 200 OK 지만, `tools:[{google_search:{}}]` 가 붙으면 그 툴만
    quota=0 → **429 RESOURCE_EXHAUSTED**(크레딧 소진이 아님 — changes_51의 추측을 changes_52에서 정정).
    실측: 같은 키로 plain=200, grounded=429. 2.5-flash 는 빌링 없이도 grounding 동작(다른 quota lane).
    대응: `_gemini_stream` 이 grounded 429 시 검색 끄고 1회 자동 재시도 → 답변은 끊기지 않음. 근본 해결은
    `GEMINI_KEY` 프로젝트에 billing 연결. **무료 티어 모델만 노출**(Pro Preview는 free 미지원→제외, changes_54).
    검색은 `_GEMINI_SEARCH_OK`(2.5계열)에서만 켠다.

33. **Gemini 2.5 그라운딩 시 thought/tool_code 가 답변 텍스트로 누출.** `google_search` 켜면 2.5 모델이
    `tool_code\nprint(google_search.search(...))\nthought\n...` 를 *답변* `text` 파트로 흘린다(thought 플래그
    없이). 해결: `generationConfig.thinkingConfig={includeThoughts:true, thinkingBudget:1024}` (검색 경로만) →
    사고가 `thought:true` 파트로 분리되어 dim 'reasoning' 박스로 가고 답변은 깨끗. budget 없으면 사고가
    maxOutputTokens 를 다 먹어 **답변이 0자**가 되므로 budget 필수. 비텍스트 파트(executableCode 등)는 스킵. (changes_54)

34. **중첩 제너레이터에서 외부 변수 재할당 = UnboundLocalError.** `llm_ask.generate()` 안에서 `gemini_model`
    을 재할당(검색 자동전환)하면 Python 이 그걸 generate-지역변수로 보고 *읽는 순간* UnboundLocalError →
    Gemini 요청 전부 무응답(reasoning 만 나오고 meta/답변 없음). 해결: generate() 첫 줄 `nonlocal gemini_model`.
    증상이 "스트림이 중간에 끊김"이면 서버 로그의 Traceback 을 먼저 봐라. (changes_54)

35. **코드베이스는 Python 3.12+ 전용 문법을 쓴다 — 3.10/3.11 에서는 import 자체가 SyntaxError.**
    `market_intel/report/dashboard.py:692` 가 **f-string 내부에 백슬래시**(`{" class=\"active\"" if ...}`)를 쓰는데
    이는 Python 3.12 에서 허용된 문법이라 3.10/3.11 컴파일 단계에서 터진다. 메인 백엔드는 import 시
    `from archive import company_report_ver2/etf_dashboard_ver2` 를 즉시 실행하고 이들이 그 dashboard 를 끌어오므로,
    **구버전 인터프리터에서는 `import market_dashboard3_realtime` 자체가 실패**한다(실제 앱 런타임은 3.12+ → 무해).
    영향: ① headless 테스트/툴이 3.10 환경이면 모듈 import 불가. ② `tests/test_core_functions.py` 는 대상 6함수가
    순수함수(레거시 무의존)임을 이용해 import 전 `sys.modules` 에 archive 더미 스텁을 심어 격리 → 3.10/3.12 모두 통과.
    교훈: 새 환경에서 import 깨지면 dashboard.py 의 3.12 문법부터 의심. (changes_71)

36. **루트 `API.env` 는 라이브 파일이며 `API_documents/API.env` 와 내용이 다르다 — "중복"으로 보고 지우지 말 것.**
    루트 `API.env`(12키)는 `app.py:158`(`_r/"API.env"`)과 `realtime.py:5412/5891`(`"API.env"`/`"../API.env"`)이
    실제로 로드한다. `API_documents/API.env`(17키, FMP/FREED/GEMINI/POLYGON/TWELVE_DATA 추가분)는 `realtime.py:76`
    이 별도로 로드한다. **둘 다 살아 있고 키 집합이 다르므로** 한쪽을 지우면 일부 키가 사라진다. (changes_73)

37. **앱 아이콘 빌드 소스 = `application_build/app_icon_final/squircle_fixed.png`** (NOT 루트 icon.png 도, 아카이브된
    `icon_attempt_*` 도 아님). 체인: `build.sh → make_app_icon.py(SRC=app_icon_final/squircle_fixed.png) → icon_normalize.py`
    → `icon.png`/`icon.icns` 생성, `.spec` 가 번들. `make_icon.sh` 는 `application_icon/`(단수, 미존재)를 찾고 없으면
    `icon.png` 폴백 — 아카이브된 `application_icon_0/` 은 빌드가 읽지 않으니 "복원"해도 효과 없음. 잔재 아이콘은
    `application_build/_archive/icon_attempts/` 에 보관(개명됨). (changes_73)

38. **`scripts/archive/` 의 라이브 빌더(`*_ver2.py`)는 형제 모듈을 절대 import 한다 → archive 가 `sys.path` 에 있어야 한다.**
    `company_report_ver2.py` → `from company_report import …`, `etf_dashboard_ver2.py` → `import etf_dashboard`.
    `scripts/archive/` 엔 `__init__.py` 가 없고(네임스페이스 pkg) 이 import 들은 상대(`from .`)가 아니라 절대라,
    대상 모듈이 `sys.path` 위에 없으면 `ModuleNotFoundError`. changes_73 이 `company_report.py`/`etf_dashboard.py` 를
    `scripts/` → `scripts/archive/` 로 옮기며 **백엔드 import 전체가 실패**(앱/서버 미기동)했고, changes_74 가
    `market_dashboard3_realtime.py` 상단에 `sys.path.insert(0, scripts/archive)` 쉼을 넣어 고쳤다. **이 쉼이나 형제
    파일을 "정리"로 지우지 말 것.** 근본 해결은 archive 를 진짜 패키지로 만들고 상대 import 로 바꾸는 것(보류).
    교훈: import 경로를 건드리는 이동/개명은 반드시 **상위 모듈을 실제 import**(또는 앱 기동)해 검증할 것 —
    `py_compile` + 스텁 단위테스트만으로는 절대 못 잡는다(TECH_REVIEW #1·#2 실증). (changes_74)

39. **백엔드 템플릿은 `scripts/ui_templates.py` 에 산다(changes_77).** 페이지/위젯 마크업(HTML/CSS/JS) 상수 20개는
    main 이 아니라 `ui_templates.py`. **마크업 수정은 거기서, 조립(`.replace`)·주입(`_inject_*`)·로직은 main 에서.**
    main 은 `from ui_templates import (…)` 후 모듈레벨 조립을 돌린다 — import 가 조립보다 먼저라 순서 OK. 템플릿을
    main 에서 grep 해도 안 나온다(거기 없음). **마크업을 바꿨으면 골든이 깨지므로** `uv run scripts/smoke_check.py
    --golden write` 로 재기준선(안 하면 다음 에이전트가 거짓 실패를 본다). 둘 다 `scripts/` 가 sys.path 에 있어야 import 됨.
    **순수 계산/포맷/SSE 헬퍼는 `scripts/pure_helpers.py`(changes_78)** — 거기엔 순수 함수만(모듈 globals·I/O 금지). main 이 `from pure_helpers import` 로 재내보내기.

40. **동적 로드 모듈은 `market_dashboard.spec` `hiddenimports` 에 명시해야 빌드된 .app 에 포함된다(changes_79).**
    `app.py` 가 `market_dashboard3_realtime` 를 importlib 로 동적 로드 → PyInstaller 정적 분석이 그 모듈과
    그 모듈이 `from … import` 하는 분리 모듈(`ui_templates`/`pure_helpers`/향후 `data_sources` 등)을 못 따라간다.
    현재 등록: `market_dashboard3_realtime`,`ui_templates`,`pure_helpers`,archive 빌더들. **새 모듈을 scripts/ 로
    분리할 때마다 여기에 추가**(§12 구조→지침 동기화의 일부). 라이브 실행은 `app.py` 가 scripts/ 를 sys.path 에
    올려 디스크에서 로드하므로 무관 — 이 규칙은 *동결 .app 폴백* 용. requirements.txt 는 새 모듈이 새 의존성을
    쓸 때만 갱신(현재 ui_templates=무, pure_helpers=numpy/pandas/difflib(stdlib) → 갱신 불필요).

41. **수집기(데이터 소스) 함수는 단순 이동으로 분리 불가 — 공유 인프라와 깊게 얽혀 있다(changes_79).**
    해외/글로벌 수집기 폐포가 KIS 인프라(`_kis_token` 등 38곳 호출)·공유 async `_afetch`·`_gmac_*`·가변 캐시
    (`_KIS_TOKEN`/`_FMP_CACHE`/`_GMAC_CACHE`/`_OV_CACHE`/`_POLY_GROUPED_CACHE`)를 끌어온다. 통째 이동은 순환
    import/공유상태 분기 위험. **올바른 길 = 단계적 `core.py` 디커플**(KIS토큰·`_afetch`·캐시·기반설정을 core 로,
    main 과 `data_sources.py` 가 core 를 import). Tier-L·사용자 승인 필요. `api_smoke.py` 가 그 게이트.

42. **reflect 자동 문서수정 정책 — 정본은 고확신+auto 모드에서만, 무조건 가드 통과(changes_88).**
    `scripts/reflect/capture.py`(UserPromptSubmit)가 사용자 교정 발화를 다국어 정규식으로 스코어(floor 0.75)해
    `_autoreflect/queue.jsonl` 에 큐잉(정본 미수정·비차단). `scripts/reflect/apply.py`(Stop)가 처리하되 **기본
    `DEFAULT_MODE="propose"` → 전부 `dev_notes/*_autoreflect_*.md` 로만**(정본 자동수정 OFF). `KMKT_REFLECT_MODE=auto`
    이고 확신도 ≥ 0.90 일 때만 정본 자동기록을 하며, 그때도 **반드시 3가드**: ① 백업
    `_autoreflect/_STATUS_bak_*.md`, ② **무결성 게이트 = 구조검증(필수섹션 존재·비축소·UTF-8) AND `smoke_check`** —
    실패 시 백업으로 **자동 롤백**, ③ 출처로그 `_autoreflect_log.md`. ⚠️ **`smoke_check` 단독은 문서 편집을 검증하지
    못한다**(`_STATUS.md`/`CLAUDE.md` 는 백엔드가 import 안 함) — 그래서 *구조검증*이 진짜 문서 가드다. 자동 내용은
    번호 트랩 목록을 건드리지 않고 파일 끝 전용 `## ▶ Auto-reflect log` 섹션에만 append(번호목록 자동수정 금지 —
    오염 위험). 두 CLAUDE.md 에 동시 기록 금지(단일 진실원천=_STATUS). 되돌리기 `apply.py --undo`. **이 정책을 끄려면**
    `DEFAULT_MODE`/env 를 propose 로 두면 된다. `.claude/settings.json` Hooks 가 capture/apply/gate/brief 를 호출.

---

## ▶ Correction log (where past entries were wrong — prevents repeating)

- **changes_73** logged `status: verified` and "live paths OK" for the file-structure cleanup,
  but moving `company_report.py`/`etf_dashboard.py` into `scripts/archive/` **broke the live
  builders' absolute sibling imports** → `import market_dashboard3_realtime` raised
  `ModuleNotFoundError: No module named 'company_report'` → **the app/server could not start at
  all**. The PHASE 1 claim "company_report.py not imported anywhere" was false (it's imported by
  `company_report_ver2`). The "verification" was `py_compile` (no import executed) + the core
  pytest suite (which *stubs* the archive modules, trap #35) — neither exercises the real import,
  so the break slipped through. **Fixed in changes_74** (sys.path shim). This is the canonical
  example of TECH_REVIEW #1/#2 ("py_compile = verified").

- **changes_38** built a multi-step ReAct loop assuming the local model would emit tool actions
  (free-text `SEARCH:`/`FETCH:`…). It did **not** — the 4B model answered `DIRECT`/hallucinated and
  never triggered tools, so the user still saw "외부 정보를 못 가져옴". **Fixed in changes_39** by
  making tool use deterministic (keyword-driven), not model-decided. (Verified live.)
- **changes_38** `fmtMcap` treated overseas `tomv` as 억 → "511,248,232.0조" for NVDA. `tomv` is raw
  currency; **fixed in changes_39** (`fmtMcap(v,curr)` → "$5.11T").
- **changes_2** claimed *"Fixed Local AI Model Loading"* and *"Fixed Screener"*, but
  neither was actually working afterward:
  - AI: every `POST /api/llm_commentary` returned **HTTP 500** (`request.json` read
    inside the SSE generator — trap #2), so commentary never streamed. Also
    `timeout=5.0` < model load time. **Fixed in changes_3.**
  - Screener: the runtime env had no `duckdb` (installed only into *system* python via
    `pip --break-system-packages`, not the uv/app env) → endpoint errored; and the
    page rendered white-on-white (trap #1) so even errors were invisible. **Fixed in changes_3.**
  - Root cause of the bad record: changes were logged as "fixed" **without an
    end-to-end verification step**. The protocol now *requires* a Verification section.
- **changes_13** claimed the launch flicker was fixed by deferring the window reveal 80ms
  past `loaded`. It was **not** — the user still saw the blink. The real cause was that
  `_style_native_window` made the window *transparent* (`setOpaque_(False)` + `clearColor` +
  `drawsBackground=False`) **before** `show()`, so the transparent window briefly showed the
  **desktop** before the splash painted. **Fixed in changes_16** by revealing an opaque-dark
  window first and deferring the glass transparency 0.3s. (Still pending user visual confirm.)
- **changes_28** added a "model-specific prompt" that told **qwen** models to "깊이 있는 추론(Thinking)을 거쳐
  …답변" and only captured `reasoning_content`. For a *reasoning* model (qwen3.5-9b) this is the **opposite** of
  what's needed: it makes the model spend the entire token budget thinking and emit **0 answer chars**
  (`finish_reason=length`) → the user saw "응답 없음". It also still JIT-loaded `qwen3-4b-2507` regardless of the
  loaded model → **two models resident** (user's 2nd complaint). **Fixed in changes_29:** loaded-model-first
  picking via `/api/v0/models`, `_llm_model_profile()` (reasoning vs instruct), reasoning streamed to a dim block
  + Instruct end-note, and the harmful "think deeply" suffix removed.
- **changes_6** added `_kis_stock_news()` assuming KIS [141] `FID_INPUT_ISCD=code` returns
  only that stock's news. It does **not** — it returns market/large-cap news regardless, so
  009150 commentary pulled in 005930/market headlines (005930/000660 looked fine only by
  coincidence). **Fixed in changes_7** by filtering rows on their `iscd1..10` tags (trap #10).
