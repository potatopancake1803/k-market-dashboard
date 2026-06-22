# K-Market Dashboard — 아키텍처 & 기능 설명서

> 한국 주식시장(개별주식·ETF·해외·세계지수) 통합 분석 **macOS 네이티브 데스크톱 앱**의 구조·기능·운영
> 체계를 정리한 기술 문서입니다. AI 코딩 에이전트(Claude Code)와 협업해 개발한 1인 프로젝트로, 지금도
> 업데이트가 이어지고 있습니다.
>
> - **최종 갱신:** 2026-06-23 (changes_94 기준)
> - **공개 저장소:** https://github.com/potatopancake1803/k-market-dashboard
> - **단일 진실 원천:** 현재 상태 `application_build/changes_history/_STATUS.md` · 백엔드 라인맵
>   `docs/CODEMAP.md` · 작업 프로토콜 `application_build/CLAUDE.md`
> - 이 문서는 위 세 문서를 근거로 한 **구조·기능 개요**입니다. 라인 번호 등 세부는 수시로 변하므로,
>   정확한 위치는 항상 `CODEMAP.md`(`python3 scripts/gen_codemap.py`로 재생성)를 확인하세요.

---

## 목차

1. [한눈에 보기](#1-한눈에-보기)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [모듈 구성과 의존 관계](#3-모듈-구성과-의존-관계)
4. [요청 처리 흐름](#4-요청-처리-흐름)
5. [라우트 맵 (84개)](#5-라우트-맵-84개)
6. [기능 상세](#6-기능-상세)
7. [AI 리서치 에이전트 — 환각을 막는 결정적 구조](#7-ai-리서치-에이전트--환각을-막는-결정적-구조)
8. [성능 — M4 Pro 활용 & 캐싱 계층](#8-성능--m4-pro-활용--캐싱-계층)
9. [AI 협업 운영 체계 (8개 장치)](#9-ai-협업-운영-체계-8개-장치)
10. [실행·빌드·환경변수](#10-실행빌드환경변수)
11. [기술 스택](#11-기술-스택)
12. [프로젝트 규모](#12-프로젝트-규모)
13. [알려진 한계 & 로드맵](#13-알려진-한계--로드맵)

---

## 1. 한눈에 보기

| 구분 | 내용 |
|---|---|
| 무엇 | 한국 증시 통합 분석 데스크톱 앱(개별주식·ETF·해외주식·세계지수·거시·리포트·실시간·AI) |
| 어떻게 | Flask 백엔드가 데이터를 모아 HTML을 그리고, pywebview가 macOS 네이티브 창으로 감쌈 |
| 차별점 | M4 Pro GPU 퀀트 3D 분석 · **환각을 차단한 결정적 AI 에이전트** · 증권사 리포트 AI 요약 |
| 규모 | 백엔드 ~8,170줄 · 템플릿 ~5,290줄 · 라우트 84개 · 외부 데이터 10종 · changes 94회 |
| 기본 AI | 로컬 **EXAONE-3.5-7.8B-Instruct**(LG AI연구원) + 클라우드 Gemini 듀얼 엔진 |

---

## 2. 시스템 아키텍처

### 2-1. 2층 구조

```
┌──────────────────────────────────────────────────────────────┐
│  데스크톱 셸 — pywebview (WKWebView)            application_build/app.py
│  · macOS HIG 메뉴바 · 자동 업데이트 · DMG 패키징
│  · 백엔드 소스를 importlib 로 런타임 로드(_live_source) → 편집 후 재시작=즉시반영
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Flask 백엔드 (포트 8780, threaded=True)
│  │     scripts/market_dashboard3_realtime.py  (~8,170줄, 84 라우트)
│  │  · 데이터 수집 · 계산 · HTML 조립 · 비파괴 주입 · SSE 스트리밍
│  │  · asyncio 병렬 I/O · SSD/RAM 캐시 · 프리워밍
│  │      ├── ui_templates.py   (마크업 상수 20종, ~5,290줄)
│  │      ├── pure_helpers.py   (순수 계산/포맷/SSE, ~180줄)
│  │      └── archive/*_ver2.py (개별주식·ETF 리포트 빌더 — 라이브)
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
        ▲ HTTP/JSON · SSE                ▲ 외부 데이터 10종
        │                                 (KIS·DART·KRX·FSC·FRED·네이버·한국은행·Finnhub·FMP·Polygon)
   브라우저 렌더링(WKWebView)        로컬 LLM(LM Studio) · Gemini API
```

### 2-2. 핵심 설계 원칙 3가지

1. **비파괴 주입(non-destructive injection)** — 기존 리포트 빌더(`*_ver2.py`)를 수정하지 않고, 빌드된
   HTML 문자열에 FX 레이어와 M4 퀀트 탭을 **삽입**한다. 빌더와 신규 기능이 독립적으로 진화한다.
2. **마크업·로직·계산 분리** — 화면 템플릿은 `ui_templates.py`, 순수 계산은 `pure_helpers.py`,
   조립·주입·I/O·라우트는 main. "겉모습 고칠 땐 템플릿만, 계산 고칠 땐 헬퍼만" 본다.
3. **라이브 로드** — `app.py`가 백엔드를 importlib로 로드하므로, 백엔드 수정 후 앱 재시작만으로 반영
   (재빌드 불필요). `.app` 번들 배포 시에만 PyInstaller 빌드.

---

## 3. 모듈 구성과 의존 관계

| 파일 | 역할 | 주요 의존 |
|---|---|---|
| `application_build/app.py` | pywebview 런처(메뉴·업데이트·라이브 로드) | → 백엔드 importlib |
| `scripts/market_dashboard3_realtime.py` | **라이브 백엔드** — 라우트·수집·계산·조립·주입·SSE | → ui_templates, pure_helpers, archive/*_ver2 |
| `scripts/ui_templates.py` | 페이지/위젯 템플릿 상수 20종(HTML/CSS/JS) | (순수 문자열) |
| `scripts/pure_helpers.py` | 순수 계산/포맷/SSE 헬퍼(`_risk_stats`·`_clean_ohlc`·`_bt_signal`·`_sse_*`·`_krx_won` 등) | numpy |
| `scripts/archive/company_report_ver2.py` | 개별주식 리포트 빌더(`build_company_html`) | → company_report.py(형제 절대 import) |
| `scripts/archive/etf_dashboard_ver2.py` | ETF 리포트 빌더(`build_dashboard_html`) | → etf_dashboard.py |
| `scripts/smoke_check.py` | 렌더 회귀 게이트 | → 백엔드 import·기동 |
| `scripts/api_smoke.py` | 수집기 코드버그 게이트 | → 수집기 호출 |
| `scripts/health_check.py` | 구조 자기점검(비대화·drift) | (정적 분석) |
| `scripts/gen_codemap.py` | CODEMAP 재생성 | (AST/정규식) |

> ⚠️ **구조 함정**: `archive/*_ver2.py`는 형제 모듈(`company_report.py` 등)을 **절대 경로로 import**
> 하므로, 백엔드 상단이 `scripts/archive`를 `sys.path`에 추가한다. 이 shim을 지우면 앱이 기동되지
> 않는다(과거 changes_73 회귀 사고의 원인, _STATUS 트랩 #38).

---

## 4. 요청 처리 흐름

### 4-1. 리포트 페이지 (동기 렌더 + 비파괴 주입)

```
GET /dashboard?q=삼성전자
  │
  ├─ detect_type(q) ─────────────► "stock" | "etf"
  │
  ├─ RAM 캐시 조회 _rget(key) ─── hit ─► 즉시 반환 (TTL 30분)
  │                              miss
  ├─ build_company_html(q)  /  build_dashboard_html(q)   ← archive/*_ver2 빌더
  │       └─ 내부에서 SSD parquet 캐시 _disk_read/_disk_write 활용
  │
  ├─ _inject_fx(html)        ← </head>·</body> 앞에 FX CSS/JS 삽입(카운트업·등장·틸트·테마)
  ├─ _inject_m4_tab(html)    ← </nav>·<footer> 앞에 M4 퀀트 탭 버튼·패널 삽입(인덱스 자동계산)
  │
  └─ _rput(key, html) ─► HTML 응답
```

### 4-2. 퀀트 분석 (SSE 스트리밍, lazy-load)

탭을 클릭할 때 비로소 로딩을 시작하고, 진행률을 단계별로 흘려보낸다(`threaded=True` 필수).

```
GET /api/quant/stock?code=005930   (EventSource)
  └─ _gen_stock_quant(code)  ── 제너레이터 ──►
       progress 10% ─ 리스크·수익 지표 타일(Sharpe·Sortino·VaR·CVaR·MDD·연율)
       progress 30% ─ 몬테카를로(GBM 25,000경로×252일, 벡터화) + 부채꼴 분포
       progress 50% ─ 3D 확률 지형도(go.Surface, KDE)
       progress 70% ─ 3D 변동성 표면 / 수익률 분포·팻테일(왜도·첨도)
       progress 90% ─ CAPM 베타·알파(vs KODEX 200 069500 회귀) / 프랙탈 패턴
       done ─► 완성 HTML   |   failed ─► 에러 메시지
```

`_sse_progress / _sse_done / _sse_failed`(pure_helpers)가 `text/event-stream` 포맷을 만든다.
ETF는 `_gen_etf_quant`가 HHI·유효종목수·평균상관·월별 히트맵·언더워터·롤링변동성·DCA·3D 상관행렬·
3D 리스크-리턴 지형을 같은 방식으로 스트리밍한다.

### 4-3. AI 질문 (결정적 수집 후 생성)

```
POST /api/llm_ask {question, scope, code}
  └─ _classify_intent(question, scope, has_entity)   ← 의도 분류(news/deep/governance/financials/analyst/peers/chitchat)
       └─ 시스템이 의도에 맞는 도구만 골라 실데이터 수집(아래 §7)
            └─ "이 데이터 안에서만 답하라" 프롬프트 → 로컬 LLM(EXAONE 등) 또는 Gemini 생성
                 └─ 근거 부족 + 실시간 필요 → Gemini(웹검색)로 자동 전환·고지
```

---

## 5. 라우트 맵 (84개)

`@app.route/get/post` 기준. 그룹별 대표 경로만 발췌(전체·라인번호는 `CODEMAP.md`).

| 그룹 | 대표 라우트 | 역할 |
|---|---|---|
| **페이지(HTML)** | `/` · `/dashboard` · `/overseas` · `/realtime_page` · `/world_page` · `/macro_page` · `/index_page` · `/market` · `/backtest_page` · `/research_page` · `/screener_page` · `/sector` | 각 화면 진입점 |
| **퀀트(SSE)** | `/api/quant/stock` · `/api/quant/etf` | M4 퀀트 분석 스트리밍 |
| **실시간** | `/api/rt/history` · `/api/rt/orderbook` · `/api/rt/stream` · `/api/rt/screener` · `/api/rt/flows` | 호가·체결·수급 |
| **모의투자** | `/api/paper/state` · `/api/paper/order` · `/api/paper/reset` | 페이퍼 트레이딩 |
| **해외주식** | `/api/ov/suggest` · `/api/ov/detail` · `/api/ov/chart` · `/api/ov/news` · `/api/ov/resolve` · `/api/ov/price` | 해외 종목 |
| **세계지수** | `/api/world` · `/api/world/chart` · `/api/world/spark` · `/api/world_view` · `/world_detail` | 글로벌 지수 |
| **거시·지수** | `/api/macro` · `/api/global_macro` · `/api/index` · `/api/index_chart` | ECOS·FRED·지수 |
| **시장 현황** | `/api/market_top` · `/api/updown` · `/api/market_news` · `/api/market_overview` · `/api/marketmap` · `/api/usmap` · `/api/sectors` · `/api/screener` | 시황·맵·스크리너 |
| **리포트** | `/api/research` · `/api/research_summary` · `/research_pdf2` · `/pdf_view` · `/report_pdf` | 증권사 리포트 뷰어·AI 요약 |
| **AI(LLM)** | `/api/llm_ask` · `/api/llm_commentary` · `/api/llm/status` · `/api/llm/loaded` · `/api/llm/load` · `/api/llm/unload` · `/api/llm/hardware` · `/api/ai/prefs` | 질문·코멘터리·모델관리·환경설정 |
| **개발자 모드** | `/api/dev/locate` · `/api/dev/note` · `/api/dev/session/*`(8) | 요소→소스 역추적·세션 |
| **정적·수명주기** | `/logo.png` · `/favicon.ico` · `/exaone_logo.png` · `/plotly.js` · `/suggest` · `/__ping` · `/__bye` | 에셋·자동완성·헬스 |

> `/exaone_logo.png`는 changes_94에서 추가 — AI 채팅 아바타에 EXAONE 로고를 쓰기 위한 라우트.

---

## 6. 기능 상세

### 📈 실시간 시세 & 트레이딩 데스크 (`/realtime_page`, `/api/rt/*`)
- KIS API 직접 연동 실시간 국내·해외 시세, **10단계 호가창**, 거래량 순위 스크리너, 투자자 수급(flows).
- **모의 투자(페이퍼 트레이딩)** — 로컬 매수·매도 시뮬레이션. 현금 잔고 계산을 정확히 검증하며 **실제
  주문은 절대 나가지 않는다.** 상태/주문/리셋 API 분리.
- 호가창+페이퍼를 세로 스택 레이아웃으로 정리(changes_93), 드래그로 폭 조절(300~760px).

### 🚀 M4 Pro 퀀트 분석 (`/api/quant/*`, SSE)
- **주식**: 리스크·수익 타일(Sharpe·Sortino·VaR95·CVaR·MDD·연율) → 몬테카를로(GBM 25,000경로×252일,
  벡터화 NumPy) → 3D 확률 지형도(KDE) → 3D 변동성 표면 → 수익률 분포·팻테일(왜도·첨도) → CAPM
  베타/알파(KODEX 200 회귀, R²) → 프랙탈 패턴 매칭(sliding-window).
- **ETF**: HHI 집중도·유효 종목수·평균 상관 → 월별 수익률 히트맵 → 누적수익·언더워터(MDD) → 롤링
  변동성(63일) → 적립식(DCA) 백테스트 → 3D 편입종목 상관행렬 → 3D 리스크-리턴-비중 지형.
- 다크 콕핏 테마(plotly_dark) + 3D 자동회전 카메라(rAF, 호버 시 정지).

### 🤖 AI 투자 분석 (`/api/llm_ask`, `/api/llm_commentary`) — 상세는 §7
- 플로팅 채팅 위젯(`_ASK_WIDGET_HTML`)이 **현재 보고 있는 화면의 실데이터**를 읽어 답한다(scope 인식).
- **기본 로컬 모델 = EXAONE-3.5-7.8B-Instruct.** Instruct 프로파일(prefill 불필요)로 처리하며,
  채팅 아바타에 EXAONE 로고를 표시(Gemini는 ✦). `KMKT_LLM_MODEL`로 모델 강제 가능.
- 시스템 프롬프트는 `~/.cache/kmkt_m4/ai_prefs.json`에 영구 저장(앱 재시작에도 유지).
- **AI 코멘터리** — 퀀트 통계(리스크·수익·밸류에이션)에 오늘 날짜·실데이터를 함께 넣어, 모델이 옛 기억이
  아닌 최신 사실로 코멘트하게 한다.

### 📄 증권사 리포트 뷰어 + AI 요약 (`/research_page`, `/api/research*`, `/pdf_view`)
- 네이버 6개 카테고리(시황·종목·산업·투자전략·경제·채권) + 한국은행 RSS·금통위 자료 목록화.
- 원문 PDF를 앱 내 뷰어(줌)로 열고, AI 요약 버튼으로 표·수치를 직접 읽어 핵심 정리(접기/펼치기).

### 🌏 해외주식·세계지수·거시 (`/overseas`, `/world_page`, `/macro_page`)
- 해외 종목 히어로·KPI·차트·M4 퀀트, 세계 3뷰(국내/미국/글로벌), ECOS·FRED·글로벌 거시지표.

### 🎨 디자인·완성도
- macOS 26 'Liquid Glass' 테마(반투명 유리·라이트/다크·**바뀐 자릿수만 세로 슬라이드하는 숫자 롤링**),
  전 페이지 1200px 중앙정렬·배경 full-bleed(changes_93), PyInstaller DMG 빌드.

---

## 7. AI 리서치 에이전트 — 환각을 막는 결정적 구조

이 앱 AI 기능의 핵심 원칙: **모델의 기억이 아니라, 시스템이 먼저 모은 실데이터 안에서만 답하게 한다.**

### 7-1. 왜 이렇게 했나 (문제)
로컬 소형 모델(7B~12B급)은 "도구를 쓰라"고 줘도 무시하고 기억에서 그럴듯하게 지어내, 한 기업의
지배구조를 사실과 다르게 답한 적이 있다(changes_38→39). "모델이 알아서 도구를 고른다"는 가정이 틀렸다.

### 7-2. 어떻게 풀었나 (구조)
모델에게 도구 선택을 맡기지 않고, **시스템이 확정한다.**

```
질문 → _classify_intent(question, scope, has_entity)
        ├ chitchat   → 잡담이면 수집 생략
        ├ news/deep  → 뉴스 검색 + (deep) 기사 본문 추출
        ├ governance → 지배구조(최대주주 등, code 필요)
        ├ financials → 재무제표
        ├ analyst    → 애널리스트 컨센서스(stock/etf/ov + 종목)
        └ peers      → 동종업계(ov + 종목)
   → 수집된 실데이터만 컨텍스트에 주입 → "이 데이터 안에서만 답하라" 강제 → 생성
```

수집에 쓰이는 **에이전트 도구는 7종**: 뉴스 검색 · 기사/웹페이지 본문 추출 · 지배구조 · 재무 ·
애널리스트 · 동종업계 · 기술적 지표. 의도에 맞는 것만 호출해 토큰을 아낀다.

### 7-3. 폴백
로컬 모델은 웹을 못 본다. 실시간 정보(최신 뉴스 등)가 필요한데 로컬에서 근거를 못 모으면, 검색이
가능한 **Gemini(Google Search 그라운딩)로 자동 전환**하고 그 사실을 화면에 고지한다. PDF 원문
직독(스캔본 OCR 포함)도 Gemini 경로를 쓴다.

---

## 8. 성능 — M4 Pro 활용 & 캐싱 계층

### 캐싱 (3계층)
| 계층 | 구현 | 효과 |
|---|---|---|
| SSD parquet 디스크 캐시 | `_disk_read/_disk_write` → `~/.cache/kmkt_m4/chart_{code}_{days}.parquet` | 당일 수집분 재사용 → 재조회 **18초→0.x초** |
| RAM 결과 캐시(TTL 30분) | `_rget/_rput` → 최종 HTML 메모리 보관 | 동일 요청 즉시 응답 |
| 시작 프리워밍 | `_prewarm` → 기동 6초 후 백그라운드 005930·069500 선계산 | 첫 조회 체감속도↑ |

### 병렬·GPU
- **asyncio 병렬 I/O** — `_fetch_etf_bundle`이 메인 차트 + ETF 분석 + 편입종목 시계열을
  `asyncio.gather`로 동시 수집.
- **16코어 GPU WebGL** — `go.Surface`/`go.Scatter3d` 3D 렌더링 + 자동회전(rAF).
- **벡터화 연산** — 몬테카를로 25,000경로 등 명시적 루프 대신 NumPy 벡터화.

---

## 9. AI 협업 운영 체계 (8개 장치)

코딩 사전 지식 없이 AI 에이전트와 협업하며, **AI의 실수 패턴을 관찰하고 막는 장치를 누적 설계**한
것이 이 프로젝트의 핵심 자산이다. 모두 실제 changes 이력에 근거한다.

| # | 장치 | 파일 | 한 줄 요약 |
|---|---|---|---|
| A | 코드 내비게이션 인덱스 | `docs/CODEMAP.md` | 라우트·템플릿이 *몇 번째 줄*인지 표 → AI가 필요한 줄만 읽음(`gen_codemap.py` 자동생성) |
| B | 회귀 게이트 | `scripts/smoke_check.py` | import+기동+라우트+골든해시 → `SMOKE PASS ✓`라야 '완료' |
| C | 코드베이스 모듈화 | 로직/템플릿/헬퍼 3분리 | 봐야 할 컨텍스트를 작게 — 13k줄 단일파일을 분할(회귀 게이트로 출력 동일성 검증 후 확정) |
| D | 버그 방지 저널 | `docs/DEBUG_JOURNAL.md` | 증상→원인→해결→예방. 디버깅 전 grep 의무화 → "AI를 위한 기관 기억" |
| E | 개발자 모드 | `KMKT_DEV=1`(⌘⇧D), `dev_overlay.py` | 화면 요소 클릭→소스 file:line 역추적·메모. 다중선택·세션배칭·⌘⇧C 복사 |
| F | 자동 회귀 훅 | `.claude/settings.json`, `hooks/gate_dispatch.py` | 백엔드 편집 후 Stop 훅이 smoke_check 1회 강제, FAIL이면 턴 종료 차단 |
| G | 교정 자동 포착 | `scripts/reflect/{capture,apply}.py` | 사용자 교정을 신뢰도 점수화. 기본 `propose`(노트만), `auto`+≥0.90만 백업·검증·롤백 거쳐 반영 |
| H | 능동 구조 점검 | `scripts/health_check.py` | 비대화·거대함수·doc-drift를 임계치로 감지→WARN+재설계 제안(대수술은 승인 후) |

**비용 통제 — Task Tier**: 모든 작업을 N(사소)·S(단일 기능)·L(새 구조) 3단계로 분류, L은 계획
파일+승인 후 진행. **운영 루프**: READ → DIAGNOSE → ACT → VERIFY → RECORD (`CLAUDE.md`).

---

## 10. 실행·빌드·환경변수

| 목적 | 명령 |
|---|---|
| 네이티브 앱(권장) | `uv run application_build/app.py` |
| 백엔드만(디버그) | `MI_NO_OPEN=1 MI_NO_PREWARM=1 MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py` |
| 개발자 모드 | `KMKT_DEV=1 uv run application_build/app.py` → ⌘⇧D |
| 앱 빌드(.app/DMG) | `cd application_build && ./build.sh` |
| 회귀 게이트(렌더) | `uv run scripts/smoke_check.py` (`--golden write`로 재기준선) |
| API 게이트(수집기) | `uv run scripts/api_smoke.py` |
| 구조 자기점검 | `python3 scripts/health_check.py` |
| CODEMAP 재생성 | `python3 scripts/gen_codemap.py` |

**환경변수**: `MARKET_PORT`(포트, 기본 8780) · `MI_NO_OPEN=1`(브라우저 미오픈) ·
`MI_NO_PREWARM=1`(프리워밍 끔) · `KMKT_LLM_MODEL`(로컬 모델 강제) · `KMKT_DEV=1`(개발자 모드) ·
`KMKT_REFLECT_MODE=auto`(교정 자동반영, 기본 propose).

> ⚠️ macOS `sharingd`(AirDrop/Handoff)가 점유한 **8770 포트는 사용·종료 금지.**

---

## 11. 기술 스택

| 레이어 | 기술 |
|---|---|
| 백엔드 | Python · Flask(`threaded=True`) · asyncio(병렬 I/O) · SSE 스트리밍 |
| 데스크톱 | pywebview(WKWebView) · PyInstaller(DMG) |
| 정량 분석 | NumPy(벡터화) · SciPy(KDE) · Plotly 3D(WebGL) |
| 데이터 | KIS · DART · KRX · 금융위(FSC) · FRED · 네이버 금융 · 한국은행(ECOS) · Finnhub · FMP · Polygon |
| AI(앱 내부) | 로컬 LLM(LM Studio — **EXAONE 3.5**·qwen3·gemma) · Gemini(웹검색·PDF 직독) |
| AI(개발 협업) | Claude Sonnet/Opus 4.8 (Claude Code) |
| 캐싱 | SSD parquet + RAM TTL(30분) + 시작 프리워밍 |

---

## 12. 프로젝트 규모 (2026-06-23, CODEMAP 기준)

| 항목 | 수치 |
|---|---|
| 버전 업데이트(changes 파일) | **94회 이상** |
| 백엔드 로직 라인 | 약 **8,170줄** (`market_dashboard3_realtime.py`) |
| 화면 템플릿 | 약 **5,290줄** / 템플릿 상수 **20종** (`ui_templates.py`) |
| 순수 계산 헬퍼 | 약 **180줄** (`pure_helpers.py`) |
| 기능 경로(라우트) | **84개** |
| top-level 함수 | 약 268개 |
| 외부 데이터 소스 | **10종 이상** |
| AI 리서치 도구 | **7종** |
| 회귀 테스트 | 순수함수 26개 + smoke(렌더)·api_smoke(수집기) 게이트 |
| 화면 캡처(docs) | 31장 |

> ⚠️ 라인·라우트 수는 갱신 시점 값이며 개발 진행에 따라 변동. 정확한 수치·위치는 `CODEMAP.md`가 기준.

---

## 13. 알려진 한계 & 로드맵

- **안정성 지표**: 네이버 분기 유동비율 미제공 → 당좌비율로 대체(진짜 유동비율은 DART 분기 BS 다수 호출 필요).
- **ETF 버블 비중**: 일부 ETF는 `etfWeight`가 `null`.
- **3.12+ 전용 문법**: `market_intel/report/*` 일부 모듈은 3.10/3.11에서 import만 SyntaxError(런타임 3.12+라 무해).
- **로드맵 아이디어**: MLX GPU 몬테카를로(100만 경로) · DuckDB로 SSD parquet 전 종목 스크리닝 ·
  EXAONE 도메인 특화 한국어 리포트 코멘터리 심화 · `core.py`/`data_sources.py` 단계적 디커플(계획 `changes_80_plan_*`).

---

*근거 문서: `application_build/changes_history/_STATUS.md`(현재 상태)·`docs/CODEMAP.md`(라인맵)·
`application_build/CLAUDE.md`(작업 프로토콜)·`docs/DEBUG_JOURNAL.md`(증상→해결). 인턴십 지원용 요약은
저장소 외부 문서를 별도 운용.*
