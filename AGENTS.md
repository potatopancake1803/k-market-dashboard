# K-Market Dashboard — Codex 맥락 인수인계 (Project_Market_Dashboard)

> 한국 증시(개별주식·ETF) 통합 웹 대시보드. Flask + Plotly + DART/KRX/금융위/네이버 데이터.

> ⚠️ **이 아래 본문(§0~)은 2026-06-05 기준이라 낡았다(진입 파일·파일구조가 changes_73/77 이전).**
> **현재 정본은 아래 순서로 읽어라:**
> 1. `application_build/CLAUDE.md` — 작업 프로토콜(루프·검증·로깅). **§12 = 구조변경 시 지침 동기화·회귀 게이트.**
> 2. `application_build/changes_history/_STATUS.md` — 현재 상태 단일 진실원천(기능표·Active Traps).
> 3. `docs/CODEMAP.md` — 백엔드 라인맵 인덱스(전체 읽지 말고 부분 Read). 재생성 `python3 scripts/gen_codemap.py`.
> 4. `docs/DEBUG_JOURNAL.md` — **오류 만나면 먼저 grep**(재디버깅 금지). 1사이클+ 쓴 오류는 append.
>
> **필수 규칙(요약):**
> - 진입점은 `scripts/market_dashboard3_realtime.py`(로직) + `scripts/ui_templates.py`(템플릿). 실행 `uv run application_build/app.py`.
> - import/파일이동/라우트/템플릿 변경 후엔 **`uv run scripts/smoke_check.py` → `SMOKE PASS ✓`** 여야 "verified"(py_compile 단독 금지).
> - 구조를 바꾸면 **같은 세션에** CODEMAP 재생성 + `_STATUS.md`/이 파일 갱신.
> - 포트 8770(`sharingd`) 죽이지 말 것. 기본 8780.

---

## 0. 현재 상태 (2026-06-05 기준)

### 프로젝트 위치
- **현재 작업 디렉터리**: `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/`
- **원본 참조 디렉터리**: `/Users/minjun1803/Documents/Python/Market_Python/` (이전 세션 작업물)

### 최신 메인 진입 파일
- **`market_dashboard3.py`** — 현재 최신. `market_dashboard2.py`의 내용과 동일하며 파일명만 다름.
- 실행: `uv run market_dashboard3.py` → `http://127.0.0.1:8780/`
- **기본 포트: 8780** (macOS 시스템 데몬 `sharingd`가 8770 점유 → 8780으로 변경)
- 환경변수: `MARKET_PORT`(포트 override), `MI_NO_OPEN=1`(브라우저 자동오픈 끔), `MI_NO_PREWARM=1`(프리워밍 끔)

### 포트 충돌 주의사항
- macOS `sharingd`(AirDrop·Handoff 데몬)가 **8770을 점유**함 → 절대 죽이지 말 것.
- 다른 포트 사용 시: `lsof -nP -iTCP:XXXX -sTCP:LISTEN` 으로 먼저 확인.

### 파일 구조
```
Project_Market_Dashboard/
  market_dashboard3.py      ← 현재 최신 진입점 (M4 Pro · Pro Quant Edition, 포트 8780)
  market_dashboard.py       ← 기본 통합 진입점 (ver6 기반)
  company_report_ver2.py    ← 개별주식 리포트 빌더
  etf_dashboard_ver2.py     ← ETF 리포트 빌더
  company_report.py         ← 구버전
  etf_dashboard.py          ← 구버전 (add_detail_tab 등 재사용)
  API.env                   ← API 키 (DART_KEY, FSC_KEY, KRX_KEY, NAVER_*, ECOS_KEY)
  AGENTS.md                 ← 이 파일 (Codex 맥락 인수인계)
  output/                   ← 출력 디렉터리 (현재 비어 있음)
  .cache/
    dart_corps.pkl          ← DART 기업목록 로컬 캐시
    http/                   ← HTTP 응답 캐시 (*.json, 100여 개)
  market_intel/
    __init__.py
    config.py               ← load_settings(), business_days()
    httpx_client.py         ← Fetcher (비동기 HTTP)
    progress.py             ← gather_with_progress
    report/
      __init__.py
      dashboard.py          ← 핵심: Dashboard/Tab 빌더 + CSS/JS (1322줄)
      narrative.py          ← 텍스트 내러티브 생성
      xlsx.py               ← 엑셀 출력
    collectors/
      __init__.py
      naver.py              ← 실시간시세·차트·ETF분석·투자자동향·컨센서스
      dart.py               ← 기업목록·재무제표·배당·주주
      fsc.py                ← 금융위 지배구조·주가이력·배당이력
      krx.py                ← KRX 시장데이터 (ETF 스냅샷 등)
      news.py               ← 뉴스
      ecos.py               ← 한국은행 ECOS
      eia.py                ← EIA (에너지)
    analyze/
      __init__.py
      etf.py                ← ETF 스냅샷·latest_snapshot·find_etf
      valuation.py          ← 밸류에이션 지표·price_analytics
      market.py             ← 시장 분석
      rotation.py           ← 섹터 로테이션
      stock.py              ← 개별주식 분석
```

---

## 1. 아키텍처 / 데이터 흐름

```
market_dashboard3.py  (Flask 진입점, 포트 8780)
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

11. **카드 틸트 + 3D 차트 충돌**: `perspective` CSS가 Plotly 3D의 자체 perspective와 충돌.
    해결: `.m4-card-3d` 클래스로 분리, 틸트 JS에서 이 클래스 카드는 제외.

12. **포트 8770 충돌**: macOS `sharingd` 데몬이 8770 점유. **죽이지 말 것**. 8780 사용.

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
- **로컬 LLM 코멘터리**: MLX-LM 4비트 모델(~4GB)으로 퀀트 통계 → 자연어 투자 코멘트 생성 가능.
- **DuckDB 전 종목 스캔**: SSD parquet들을 DuckDB로 질의해 코스피 전체 모멘텀/저평가 스크리닝.
- **FSC/DART 지배구조·컨센서스 없는 종목**: 해당 섹션 자동 생략 (기존 동작).
- **포트 8780**: 혹시 충돌 시 `MARKET_PORT=XXXX uv run market_dashboard3.py`로 즉석 변경.
