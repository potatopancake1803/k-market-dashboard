# K-Market Dashboard — Claude 맥락 인수인계 (Project_Market_Dashboard)

항상 "/Users/minjun1803/Documents/Python/Project_Market_Dashboard/application_build/CLAUDE.md"파일을 읽고 작업할 것.

> 한국 증시(개별주식·ETF) 통합 웹 대시보드. Flask + Plotly + DART/KRX/금융위/네이버 데이터.
> 이 파일은 이전 작업 맥락을 압축한 것. 새 세션은 이걸 먼저 읽고 이어서 작업.
>
> ⭐ **macOS 앱화 세션 인수인계는 루트 [`HANDOFF.md`](HANDOFF.md) 참고** — macOS 앱화(업데이트
> 기능·HIG 메뉴바·DMG), 앱 아이콘, **macOS 26 Liquid Glass 테마(랜딩+리포트+다크모드+차트 다크)** 작업 전체.
> 디자인 토큰/Figma 메모는 memory의 `macos26-theme.md`.

> 📌 **이 파일(루트 CLAUDE.md)은 아키텍처/함정의 압축본일 뿐, 최신 상태의 단일 진실원천이 아니다.**
> **정본 읽기 순서(새 세션):**
> 1. [`application_build/CLAUDE.md`](application_build/CLAUDE.md) — 작업 프로토콜(READ→DIAGNOSE→ACT→VERIFY→RECORD), Task Tier, 로깅 규칙
> 2. [`application_build/changes_history/_STATUS.md`](application_build/changes_history/_STATUS.md) — **현재 상태의 단일 진실원천**(기능 상태표·Active Traps·교정로그). 95% 세션은 여기까지면 충분.
> 3. [`docs/CODEMAP.md`](docs/CODEMAP.md) — 백엔드의 **라인맵 인덱스**(라우트·템플릿·`_inject_*`). 전체를 읽지 말고 여기서 라인 보고 부분 Read.
> 4. **오류를 만나면 먼저** [`docs/DEBUG_JOURNAL.md`](docs/DEBUG_JOURNAL.md) 를 증상 키워드로 grep — 같은 오류 재디버깅 금지.
> 5. 회귀 디버깅/미완 작업 이어갈 때만: 최신 `changes_X_*.md` 2–3개 + 루트 [`HANDOFF.md`](HANDOFF.md).
> 유지보수성 감사·개선 권고: [`docs/MAINTAINABILITY_AUDIT_2026-06-17.md`](docs/MAINTAINABILITY_AUDIT_2026-06-17.md).

---

## ★ 작업 운영 체계 — 지능형 학습·오류 구조 (반드시 따를 것)

> 이 프로젝트의 #1 실패 모드: ① 오류 찾느라 빙빙 돌며 토큰 낭비, ② 고치면 다른 게 깨짐.
> 아래 4개 장치가 이를 직접 막는다. **에이전트는 매 작업에서 이 루프를 지킨다.**

1. **운영 루프 = READ → DIAGNOSE → ACT → VERIFY → RECORD** (상세: `application_build/CLAUDE.md`).
   - 컨텍스트 먼저 읽고, 근본원인 말한 뒤 고치고, **관찰로 검증**하고, **기록**한 뒤 끝낸다.

2. **🛡️ 회귀 게이트 — 구조를 건드렸으면 `smoke_check` 통과 필수.**
   - import/파일이동/라우트/`_inject_*`/템플릿(`ui_templates.py`) 을 바꾼 뒤엔 반드시:
     `uv run scripts/smoke_check.py` → **PASS 여야** "verified". **`py_compile` 단독은 검증 아님**(changes_73 이 그래서 앱을 죽였다).
   - 의도적 마크업 변경 후 골든 불일치가 나면 `uv run scripts/smoke_check.py --golden write` 로 재기준선 + changes 로그에 명시.
   - 🪝 **이제 Claude Code Hooks 가 이 게이트를 자동 강제(changes_88)**: `.claude/settings.json` →
     `scripts/hooks/gate_dispatch.py` 가 백엔드 `scripts/*.py` 편집을 표시했다가 `Stop` 훅에서 `smoke_check`
     를 턴당 1회 돌리고 FAIL 이면 턴 종료를 막는다. **안전망일 뿐 프로토콜 대체가 아님** — 직접 돌려 로그에 인용하라
     (훅은 Claude Code 세션에서만 작동). 더불어 `scripts/reflect/{capture,apply}.py` 가 사용자 교정을 포착한다
     (기본 `propose` 모드=정본 자동수정 OFF·전부 `dev_notes/`; `_STATUS.md` 트랩 #42).

3. **📓 디버그 저널 — 오류는 한 곳에 모아 grep.**
   - 오류 만나면 **먼저** `docs/DEBUG_JOURNAL.md` 를 증상 키워드로 grep(예: `ModuleNotFound`,`흰 화면`,`429`,`tool_calls`).
   - 진단에 **1사이클 이상** 쓴/비자명한 오류는 **반드시** 저널에 `### SYMPTOM:` 항목으로 append(원인·해결·가드).
     영구 규칙이 되면 `_STATUS.md` Active Traps 로 승격.

4. **🔄 구조·작동방식 변경 = 지침 자동 동기화 (필수).**
   - **파일/폴더 추가·이동·삭제, 진입점·라우트·주요 상수/템플릿 변경 시 같은 세션에 아래를 갱신**한다:
     - `docs/CODEMAP.md` → `python3 scripts/gen_codemap.py` 재생성.
     - 이 루트 `CLAUDE.md`(§0 파일구조·진입점) + `application_build/changes_history/_STATUS.md`(상태표·트랩).
     - 새 함정이면 `docs/DEBUG_JOURNAL.md`/`_STATUS.md` 트랩에도.
   - **작동 방식(프로토콜·게이트·도구)이 바뀌면 이 루트 `CLAUDE.md` 와 `application_build/CLAUDE.md` 둘 다 갱신**한다.
   - **지침이 코드와 어긋난 채로 세션을 끝내지 말 것.** 문서-코드 drift 가 다음 세션의 순환을 부른다.
     (drift 는 `health_check.py`(아래 5)가 자동 감지한다.)

5. **🧭 능동 구조 점검 — 누적 비효율을 먼저 감지하고 재설계를 제안.**
   - 세션 시작 시(그리고 구조 변경 후) `python3 scripts/health_check.py` 를 돌린다.
   - ⚠️ WARN(파일 비대화·거대 함수·라우트 과밀·❓ 누적·CODEMAP/_STATUS drift·dev_notes 적체)이 뜨면
     **조용히 넘기지 말고 사용자에게 알리고 개선/재설계를 제안**한다. 재설계 자체는 Tier-L → **사용자 승인 후**
     계획 파일 + 게이트로 실행(절대 무단 대수술 금지).
   - 이것이 "에이전트가 작업을 거듭하며 비효율을 스스로 깨닫고 **능동적으로 효율적 구조를 제안·재설계**"하는 실행 장치다.

### 문서 지도 (어느 파일이 무슨 역할인가)
| 파일 | 역할 | 갱신 시점 |
|---|---|---|
| `application_build/CLAUDE.md` | **작업 프로토콜**(루프·Tier·로깅·검증 규칙) | 작업방식 자체가 바뀔 때 |
| `application_build/changes_history/_STATUS.md` | **현재 상태 단일 진실원천**(기능표·Active Traps·교정로그) | 매 Tier S/L 변경 |
| `application_build/changes_history/changes_X_*.md` | 불변 변경 이력 | 변경마다 1개 |
| `docs/CODEMAP.md` | 백엔드 라인맵 인덱스(토큰 절약) | 구조 변경 후 재생성 |
| `docs/DEBUG_JOURNAL.md` | 증상→해결 룩업(재디버깅 방지) | 오류 해결마다 append |
| `docs/MAINTAINABILITY_AUDIT_2026-06-17.md` | 유지보수성 감사·리팩터 권고 | 1회성(필요시 갱신) |
| 루트 `CLAUDE.md`(이 파일) | 오리엔테이션 + 운영체계 + §0 현황 | 구조/진입점 변경 시 |
| `scripts/smoke_check.py` | 회귀 게이트(렌더: import+라우트+골든) | 새 핵심 라우트 추가 시 |
| `scripts/api_smoke.py` | API 게이트(수집기 호출; 코드버그만 FAIL) | 수집기 이동/리팩터 후 |
| `scripts/health_check.py` | **능동 구조 점검**(비대화·거대함수·drift·적체 → WARN+제안) | 세션 시작·구조 변경 시 |
| `dev_notes/*.md` | 앱 Dev Mode 가 캡처한 수정요청 큐(위치+소스+메모). **세션 시작 시 미처리 확인** | 처리 후 `[x]`+`## ✅ 처리 결과` 채우고 `done/` 이동 |
| `application_build/market_dashboard.spec` | PyInstaller 빌드(동적로드 모듈은 hiddenimports 명시) | scripts/ 모듈 분리 시 |
| memory `*.md` | 세션 간 사용자 선호/지속 맥락 | 비자명한 선호·결정 |

---

## 0. 현재 상태 (2026-06-17 갱신)

### 프로젝트 위치 / 진입점
- **작업 디렉터리**: `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/`
- **라이브 백엔드(로직·71 라우트)**: **`scripts/market_dashboard3_realtime.py`** (~7.8k줄, changes_77/78 분할 후; 원래 13.2k).
  페이지/위젯 **템플릿 상수(HTML/CSS/JS)는 `scripts/ui_templates.py`(~5.3k줄)**, **순수 계산/포맷/SSE 헬퍼는 `scripts/pure_helpers.py`** 로 분리.
  마크업은 ui_templates, 순수함수는 pure_helpers, 조립·주입·I/O·라우트는 main. (모두 main 이 import → 호출부 동일.)
  과거 `market_dashboard3.py`/`market_dashboard.py`는 **레거시 → `scripts/archive/`** 로 이동(changes_73).
- **실행**:
  - 네이티브 앱(권장): `uv run application_build/app.py` — `app.py` 가 위 라이브 소스를 `importlib` 로 직접 로드(편집 후 재시작=재빌드 불필요).
  - 백엔드만(디버그): `MI_NO_OPEN=1 MI_NO_PREWARM=1 MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py`
  - **개발자 모드**: `KMKT_DEV=1 uv run application_build/app.py` → 앱에서 ⌘⇧D → 고칠 요소 클릭 → 위치·소스·메모를 `dev_notes/*.md` 로 저장(에이전트 전달용).
  - 앱 빌드: `cd application_build && ./build.sh`
- **기본 포트 8780**. 환경변수: `MARKET_PORT`(override), `MI_NO_OPEN=1`, `MI_NO_PREWARM=1`.

### 포트 충돌 주의
- macOS `sharingd`(AirDrop·Handoff 데몬)가 **8770 점유** → 절대 죽이지 말 것. 확인: `lsof -nP -iTCP:XXXX -sTCP:LISTEN`.

### ⚠️ 핵심 함정 (구조 관련, 자세히는 _STATUS.md Active Traps)
- **`scripts/archive/` 의 라이브 빌더(`*_ver2.py`)는 형제 모듈을 절대 import** 한다(`from company_report import …`).
  그래서 `market_dashboard3_realtime.py` 상단이 `scripts/archive` 를 `sys.path` 에 올린다 — **지우지 말 것**
  (changes_74, _STATUS 트랩#38). changes_73 이 이걸 놓쳐 앱이 안 떴던 회귀가 있었다.
- **import 경로/라우트/파일이동을 건드리면 `py_compile` 만으로 검증 금지** — 반드시 실제 `import`/앱 기동으로 확인.

### 파일 구조 (2026-06-17, changes_73 정리 반영)
```
Project_Market_Dashboard/
  scripts/
    market_dashboard3_realtime.py  ← ★ 라이브 백엔드 로직(71 라우트, ~7.8k줄)
    ui_templates.py                ← ★ 페이지/위젯 템플릿 상수(HTML/CSS/JS, ~5.3k줄, changes_77 분리)
    pure_helpers.py                ← ★ 순수 계산/포맷/SSE 헬퍼(quant·risk·_cu·_krx_won·_sse_*, changes_78)
    smoke_check.py                 ← ★ 렌더 회귀 게이트(import+기동+라우트+골든해시). `uv run scripts/smoke_check.py`
    api_smoke.py                   ← ★ API/수집기 게이트(코드버그만 FAIL, 네트워크는 SKIP). `uv run scripts/api_smoke.py`
    dev_overlay.py                 ← 개발자 모드(KMKT_DEV=1): 오버레이 + 소스 grep locate + 노트 저장
    gen_codemap.py                 ← docs/CODEMAP.md 재생성기
    hooks/                         ← ★ Claude Code 훅(changes_88): gate_dispatch.py(회귀게이트 자동강제), session_brief.py(세션 다이제스트). 백엔드 미import
    reflect/                       ← ★ 교정 자동포착(changes_88): capture.py(UserPromptSubmit), apply.py(Stop·3가드·propose 기본). 백엔드 미import
    archive/                       ← 레거시 + 라이브 리포트 빌더(절대 import로 묶임 — sys.path 필요)
      company_report_ver2.py       ← 개별주식 리포트 빌더(라이브)
      etf_dashboard_ver2.py        ← ETF 리포트 빌더(라이브)
      company_report.py            ← _ver2 가 import (라이브 의존)
      etf_dashboard.py             ← _ver2 가 import (라이브 의존)
      market_dashboard.py, market_dashboard3.py  ← 구 진입점(미사용)
    한국투자증권/                   ← KIS 명세 xlsx
  application_build/
    app.py                         ← pywebview 런처(라이브 소스 importlib 로드, HIG 메뉴, 업데이트)
    build.sh / market_dashboard.spec / requirements.txt
    changes_history/
      _STATUS.md                   ← ★ 현재 상태 단일 진실원천
      changes_0..75_*.md           ← immutable 변경 이력
  docs/
    CODEMAP.md                     ← ★ 백엔드 라인맵 인덱스(토큰 절약용; gen_codemap.py 재생성)
    DEBUG_JOURNAL.md               ← ★ 증상→해결 룩업(재디버깅 방지, append-only)
    MAINTAINABILITY_AUDIT_2026-06-17.md
    legacy/
  market_intel/                    ← 빌더 보조 패키지(config/httpx_client/report·collectors·analyze)
  API_documents/                   ← 외부 API 명세 + API.env(추가 키: FMP/FREED/GEMINI/POLYGON/TWELVE_DATA)
  .env / API.env                   ← API 키(둘 다 라이브·키집합 다름 — 합치지 말 것, _STATUS 트랩#36)
  tests/                           ← test_core_functions.py(순수함수 26개) + golden_render.json(smoke 기준선) + legacy/
  dev_notes/                       ← 개발자 모드(KMKT_DEV=1) 캡처 .md 큐(위치+소스+메모). 에이전트가 읽음. README.md 참고
  data/ · output/ · .cache/        ← 데이터·출력·캐시
  .claude/                         ← launch.json(Preview MCP) + settings.json(★ Hooks: 게이트 자동강제·reflect·세션 다이제스트, changes_88)
  application_build/changes_history/_autoreflect/ · _autoreflect_log.md  ← reflect 백업·큐·출처로그(런타임 생성)
  CLAUDE.md(이 파일) · HANDOFF.md · README.md · TECH_REVIEW_2026-06-17.md
  AGENTS.md · ANTIGRAVITY.md       ← 타 에이전트 진입 규약(사용자 결정으로 루트 유지)
```
> ℹ️ `market_intel/report/dashboard.py` 등 일부 모듈은 **Python 3.12+ 전용 문법** 사용 → 3.10/3.11 에선
> import 자체가 SyntaxError(실제 런타임은 3.12+ 라 무해). 새 환경에서 import 깨지면 여기부터 의심(_STATUS 트랩#35).

---

## 1. 아키텍처 / 데이터 흐름

> 아래 다이어그램의 진입점은 현재 **`scripts/market_dashboard3_realtime.py`**(앱은 `application_build/app.py`
> 가 이를 로드). 리포트 빌더 비파괴 주입(`_inject_fx`/`_inject_m4_tab`)의 개념 흐름은 그대로 유효.
> 실시간/해외/세계/AI/리포트뷰어 등 신규 기능은 `docs/CODEMAP.md`·`_STATUS.md` 참고.

```
scripts/market_dashboard3_realtime.py  (Flask 진입점, 포트 8780; app.py 가 importlib 로드)
  ├ 라우트: / (랜딩+탭+검색), /suggest, /dashboard?q=,
  │          /report_pdf?nid=, /api/quant/stock, /api/quant/etf,
  │          /__ping, /__bye
  ├ detect_type(query) → "etf" | "stock"
  ├ etf   → etf_dashboard_ver2.build_dashboard_html(q)
  │          + _inject_fx(html)       ← 기본 탭 3D FX 레이어
  │          + _inject_m4_tab(html)   ← M4 퀀트 분석 탭 주입
  └ stock → company_report_ver2.build_company_html(q)
             + _inject_fx(html)
             + _inject_m4_tab(html)

/api/quant/stock  → SSE 스트리밍 → _gen_stock_quant() 제너레이터
/api/quant/etf    → SSE 스트리밍 → _gen_etf_quant() 제너레이터
```

**핵심 설계 원칙**: 기존 빌더(`company_report_ver2`, `etf_dashboard_ver2`)를 건드리지 않고,
빌드된 HTML에 문자열 주입으로 탭·FX를 얹는다.
- `_inject_fx()`: `</head>` 전에 `_FX_STYLE`, `</body>` 전에 `_FX_JS` 삽입
- `_inject_m4_tab()`: `</nav>` 전에 버튼, `<footer` 전에 pane 삽입. 인덱스는 기존 `.tab-btn` 개수 카운팅으로 맞춤.

---

## 2. M4 Pro 활용 포인트

### 캐싱 인프라 (SSD + RAM)
- **SSD parquet 캐시**: `~/.cache/kmkt_m4/chart_{code}_{days}.parquet`
  - 당일 이미 수집한 시계열은 네트워크 생략 (`_disk_read` / `_disk_write`)
  - 재조회: 18초 → **0.x초**
- **RAM 결과 캐시**: `_RESULT` dict에 TTL 30분으로 최종 HTML 저장 (`_rget` / `_rput`)
- **프리워밍**: 시작 6초 후 백그라운드에서 005930·069500 선계산 (`_prewarm`)

### 비동기 병렬 I/O
- `_fetch_etf_bundle()`: 메인 차트 + ETF 분석 + 편입종목 시계열을 `asyncio.gather`로 동시 수집
- ETF 편입 상위 종목 시계열: `asyncio.gather(*[_achart(f, cc, 320) for cc in codes])`

### WebGL 3D 렌더링 (16-core GPU)
- `go.Surface` — 확률 지형도, 변동성 표면
- `go.Scatter3d` — 리스크-리턴-비중 지형, 편입종목 상관행렬
- 자동회전 카메라 + 인트로 애니메이션 (`_M4_WIRE` JS)

### SSE 실시간 진행률
- Flask Generator → `text/event-stream` → 브라우저 `EventSource`
- progress event(단계별 %) → done event(HTML) → failed event(에러)
- 탭 클릭 시 로드 시작 (lazy loading)

---

## 3. 기본 탭 FX 레이어 (`_inject_fx`) — 작업1·4

리포트 원본 HTML에 주입되는 레이어. 비파괴적(원본 모듈 불변).

- **`_FX_STYLE`**: `.pane .card` hover 3D 그림자, `nav .tab-btn` hover translateY
- **`_FX_JS`**: IntersectionObserver로 카드 스크롤 등장(translateY + opacity),
  `.ph-price`, `.k-val`, `.m-value` 숫자 카운트업 (0→값, 850ms easeOut),
  차트 외 카드 호버 3D 틸트 (perspective 1100px, ±2.4°),
  헤더 h1 마우스 패럴럭스

---

## 4. M4 퀀트 분석 탭 (다크 콕핏 테마)

### 공통
- **다크 콕핏 스타일**: `.m4-wrap` 라디얼 그라데이션 다크 배경 (`#0b0f20`)
- **플롯 테마**: `plotly_dark` + `paper_bgcolor="rgba(0,0,0,0)"`
- **자동회전 3D**: `setInterval 40ms` 로 `scene.camera.eye` 업데이트, 호버 시 정지
- **카드 등장**: 스태거(95ms 간격) opacity/translateY fade-in
- **카운트업**: `.cu` 클래스 span에 `data-to`, `data-dec`, `data-sign` 속성
- **카드 틸트**: 2D 카드 hover ±2.6°, 3D 카드(`.m4-card-3d`)는 제외

### 주식 퀀트 툴 (`_gen_stock_quant`) — 5단계 제너레이터
1. **리스크·수익 지표 타일**: Sharpe / Sortino / VaR 95% / CVaR 95% / MDD / 연율 수익률·변동성 / MC 1년 VaR
2. **몬테카를로 미래주가** (GBM, 25,000경로×252일, 벡터화 NumPy)
   + 부채꼴 분포 차트 (5/25/50/75/95 percentile band)
3. **3D 확률 지형도** (`go.Surface`, scipy KDE, `plotly_dark`, Plasma colorscale)
4. **3D 변동성 표면** (관측창 [5,10,21,42,63,126]일 × 시간, Cividis)
5. **수익률 분포·팻테일** (히스토그램 vs 정규분포, 왜도/초과첨도)
6. **CAPM 베타/알파** (vs KODEX 200 069500, 일간 로그수익 회귀, R²)
7. **프랙탈 패턴 매칭** (sliding_window_view 벡터화, 상위 5개, 겹침 제외)

### ETF 퀀트 툴 (`_gen_etf_quant`) — 5단계 제너레이터
1. **리스크·집중도 지표 타일**: Sharpe / MDD / VaR / **HHI** / **유효 종목수** / **평균 상관계수**
2. **월별 수익률 히트맵** (계절성, RdBu)
3. **누적 수익 + 언더워터(MDD)**
4. **롤링 변동성** (63일, 연율, 레짐 시각화)
5. **적립식 백테스트** (매월 100만원, DCA vs 일시불)
6. **3D 편입종목 상관관계 행렬** (`go.Surface`, ρ -1~1, RdBu)
7. **3D 리스크-리턴-비중 지형** (`go.Scatter3d`, 실데이터, 버블 크기=비중)

---

## 5. 랜딩 페이지 UX 고도화

- 헤더 배경: `linear-gradient(120deg, ...)` + `background-size:300%` 애니메이션 (16s)
- `🚀 M4 PRO · PRO QUANT` 배지: 펄싱 글로우 애니메이션
- 검색창 포커스: 바이올렛 링 `box-shadow`
- 탭 등장: `@keyframes tabPop` (translateY+scale 팝업)
- 탭 전환: `opacity + transform` 크로스페이드 (.34s)
- 빈 화면: `.stage::before` 배경 코닉 그라데이션 슬로우 스핀 (40s)
- 히어로 카드: 마우스 3D 패럴럭스 틸트 (±9°/±11°, `preserve-3d`)
- `prefers-reduced-motion` 가드 전역 적용

---

## 6. dashboard.py 마크업 클래스 (FX 타깃팅용)

| 클래스 | 위치 | FX 적용 |
|---|---|---|
| `.ph-price` | 현재가 히어로 큰 숫자 | 카운트업 |
| `.k-val` | KPI 박스 값 | 카운트업 |
| `.m-value` | metric-grid 값 | 카운트업 |
| `.card` | 모든 섹션 카드 | 등장 애니·틸트 |
| `.price-hero` | 현재가 히어로 박스 | `.card` 예외 처리 |
| `.fc-plot` | 재무 인터랙티브 차트 | `height:300px` 가드 필요 |
| `.pane` | 탭 콘텐츠 패널 | `.active` 시 `m4PaneIn` |
| `.tab-btn` | 탭 버튼 | hover translateY |

---

## 7. ⚠️ 핵심 함정 / 교훈 (기존 + 신규)

1. **Plotly + 숨은 탭**: 첫 화면에서 안 보이는 탭에 차트 렌더 → 백지/깨짐.
   해결: `miFinChart` draw()에 `if(el.offsetParent===null||!el.clientWidth)return;` + IntersectionObserver + `.fc-plot{height:300px}`

2. **스크립트 정의 순서**: 전역 함수 `miFinChart`는 `_JS`(페이지 하단) 정의 → 본문 인라인 호출이 먼저 실행되면 ReferenceError.
   해결: `function go(){if(window.miFinChart)miFinChart(c);else setTimeout(go,30);}go();`

3. **Plotly 숫자형 x축 오인**: `"2023.12"` → `"2,023.5"` 눈금.
   해결: `xaxis:{type:'category'}` + 라벨 재포맷

4. **Plotly 한글/태그 이스케이프**: JSON에 한글 `\uXXXX`, 볼드 `<b>`.
   테스트에서 한글 substring 검색 실패해도 실제 렌더는 정상.

5. **인코딩**: `finance.naver.com/item/main` = **UTF-8**, `research/*` = **EUC-KR**

6. **FSC(data.go.kr)**: serviceKey는 params로 전달. 여러 basDt 중 지분율 채워진 최신만 사용.

7. **컨센서스 점수**: 5=적극매수, 4=매수, 3=중립, 2=매도, 1=적극매도. 전원 매수=4.00 (5 아님).

8. **셸 `_safe_eval` 훅**: `cd`·`cp`·절대경로 `ls`·네트워크 호출이 간헐적 실패.
   회피: 절대경로 사용, 네트워크는 `uv run` + `dangerouslyDisableSandbox:true`, 파일조작은 Python.
   컴파일: `python3 -m py_compile "<abs>"`.

9. **SSE 스트리밍 + Flask**: `app.run(threaded=True)` 필수. 아니면 긴 연산 중 `/__ping` 못 받아 자동종료.

10. **3D 자동회전 타이밍**: `gd._fullLayout.scene` 이 준비되기 전에 `Plotly.relayout` 호출하면 오류.
    해결: `function wait(){if(gd._fullLayout&&gd._fullLayout.scene){autoRotate(gd);return;} if(n++<50)setTimeout(wait,80);}()`

21. **카드 틸트 + 3D 차트 충돌**: `perspective` CSS가 Plotly 3D의 자체 perspective와 충돌.
    해결: `.m4-card-3d` 클래스로 분리, 틸트 JS에서 이 클래스 카드는 제외.

22. **포트 8770 충돌**: macOS `sharingd` 데몬이 8770 점유. **죽이지 말 것**. 8780 사용.

23. **macOS `.app` 반영 규칙**: `scripts/` 내의 파이썬 스크립트나 주요 로직을 수정한 뒤에는 **반드시 macOS `.app` 번들 빌드를 수행하여 수정사항이 앱 실행 시에도 동일하게 적용되도록 유지**해야 합니다. 앱 빌드 스크립트(`build.py` 등)나 `pyinstaller` 명령이 있을 경우 이를 실행하고, 수정 내역에 반영 여부를 명시합니다.

---

## 8. 데이터 소스 (검증된 엔드포인트)

| 용도 | 소스 | 비고 |
|---|---|---|
| 실시간 시세 | `polling.finance.naver.com/api/realtime/domestic/stock/{code}` | naver.fetch_realtime_price |
| 일별 OHLCV | `api.stock.naver.com/chart/domestic/item/{code}/day` | 모든 종목/ETF |
| 투자자 매매동향 | `m.stock.naver.com/api/stock/{code}/trend?pageSize=N` | 외국인/기관/개인 |
| ETF 분석 | `m.stock.naver.com/api/stock/{code}/etfAnalysis` | 구성종목·섹터·자산 |
| 컨센서스+리서치 | `m.stock.naver.com/api/stock/{code}/integration` | recommMean·priceTargetMean |
| 실적/안정성/재무 | `finance.naver.com/item/main.naver?code=` (UTF-8, read_html) | 매출/영업이익/부채비율/당좌비율 |
| 리서치 목록 | `finance.naver.com/research/company_list.naver?...` (EUC-KR) | |
| 리서치 PDF | `finance.naver.com/research/company_read.naver?nid=` (EUC-KR) | `stock.pstatic.net/*.pdf` |
| 지배구조 | 금융위 `apis.data.go.kr/.../getStockholderInfo` | crno로 조회, FSC 우선 DART 폴백 |
| 재무제표 | DART fnlttSinglAcntAll | dart.fetch_statements |
| ETF 스냅샷 | KRX etf_bydd_trd | analyze/etf.py |
| **SSD 캐시** | `~/.cache/kmkt_m4/chart_{code}_{days}.parquet` | 당일분 있으면 네트워크 생략 |
| **CAPM 대용치** | KODEX 200 (코드 `069500`) | 시장 포트폴리오 proxy |

---

## 9. 개별주식 리포트 구성 (기존 그대로 + FX 레이어)

**탭0 "📊 종목 개요"** + 탭1 "💵 재무제표" (company_report_ver2 원본과 동일)
→ `_inject_fx()` 로 카운트업·카드 등장·틸트·헤더 패럴럭스 추가

**탭2 "🚀 M4 퀀트 분석"** (신규, lazy-load SSE)
→ 리스크 지표 타일 + 몬테카를로 + 3D 확률 지형 + 3D 변동성 표면 + 수익률 분포 + CAPM + 프랙탈

---

## 10. ETF 리포트 구성 (기존 + FX + M4 탭)

**탭0 "📊 ETF 개요"** (etf_dashboard_ver2 / etf_dashboard.add_detail_tab 원본)
→ `_inject_fx()` 로 FX 추가

**탭1 "🚀 M4 퀀트 분석"** (신규, lazy-load SSE)
→ 리스크·집중도 지표 + 히트맵 + 언더워터 + 롤링 변동성 + DCA + 3D 상관행렬 + 3D 리스크-리턴 지형

---

## 11. 공용 dashboard.py 주요 API

```
Tab 메서드:
  add_html_raw_card, add_table(search=,scroll_rows=,bold_first=),
  add_grouped_table, add_metrics, add_figure, add_candle_chart,
  add_figure_grid(restyle=), add_fin_charts(charts),
  add_research_table(reports,code),
  add_consensus_panel(rm,target,current,create_date,dist),
  add_donut_breakdown(...,gray_labels=,center=),
  add_investor_trend, add_callout

헬퍼 함수:
  price_hero_html, etf_header_html, metric_header_html,
  donut_breakdown_html, consensus_gauge, consensus_panel_html,
  fin_charts_html, research_table_html, grouped_line, opinion_label

전역 JS(_JS):
  miTab, miFilter, miSort, miFinChart,
  miOpenReport/miCloseReport(+리사이즈), miOpenStock

색상: 상승/매수=#c0392b(빨강), 하락/매도=#2e75b6(파랑), navy=#1F3864
M4 다크 테마 추가: #9b6bff(violet), #36c6ff(cyan), #cdd6f4(ink), #0b0f20(배경)
```

---

## 12. 숫자 애니메이션 기본 원칙 (프로젝트 전역)

> **이 프로젝트의 모든 숫자 전환 애니메이션은 아래 방식을 기본으로 한다.**

### 원칙: 바뀐 자릿수만 세로 슬라이드

- **바뀐 자릿수만 굴린다** — 이전 값과 새 값을 오른쪽 자리 기준으로 글자 단위로 비교.
  같은 글자(안 바뀐 상위 자릿수·콤마·단위)는 고정, 다른 글자(바뀐 자리)만 세로로 슬라이드.
- **방향**: 값 상승 시 숫자가 **위로** 슬라이드, 값 하락 시 **아래로** 슬라이드.
- **이징**: `cubic-bezier(.16,1,.3,1)` (easeOutExpo 계열), 지속시간 `0.62s`.
- **계단식 지연**: 하위 자릿수부터 26ms 간격 stagger → 낮은 자리부터 순차 굴러 자연스러움.
- **구현 참고**: `market_dashboard3_realtime.py` 의 `rollPrice()` (현재가 히어로용),
  `ktRollPrice()` (KOSPI 지수 티커용). 신규 숫자 UI 추가 시 이 함수 패턴을 재사용.
- **접근성**: `prefers-reduced-motion` 이 설정된 경우 애니메이션 없이 값만 교체.
- **tabular-nums**: 자릿수 폭 고정(`font-variant-numeric:tabular-nums`)으로 가로 흔들림 방지.

---

## 13. 다음 작업 아이디어 / 알려진 한계

- **안정성 차트**: 유동비율 대신 당좌비율 (네이버 분기 유동비율 미제공). 진짜 유동비율은 DART 분기 BS 다수 호출 필요.
- **ETF 버블 비중 데이터**: `etfAnalysis.etfTop10MajorConstituentAssets[].etfWeight` — 일부 ETF는 `null` 반환.
- **MLX GPU 몬테카를로**: `mlx.core`로 100만 경로 → 현재 25,000 경로보다 정밀도 대폭↑. 의존성 추가·macOS 전용 가드 필요.
- **로컬 LLM 코멘터리**: MLX-LM 12비트 모델(~12GB)으로 퀀트 통계 → 자연어 투자 코멘트 생성 가능.
- **DuckDB 전 종목 스캔**: SSD parquet들을 DuckDB로 질의해 코스피 전체 모멘텀/저평가 스크리닝.
- **FSC/DART 지배구조·컨센서스 없는 종목**: 해당 섹션 자동 생략 (기존 동작).
- **포트 8780**: 혹시 충돌 시 `MARKET_PORT=XXXX uv run scripts/market_dashboard3_realtime.py`로 즉석 변경.
