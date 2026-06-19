---
id: 10
title: 해외주식 NameError 수정 + MA/FX UI 격상 + 발열 완화
date: 2026-06-14 KST
agent: Claude (Sonnet 4.6)
area: [bugfix, ui, perf]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  uv run scripts/market_dashboard3_realtime.py :8792 (MI_NO_OPEN=1 MI_NO_PREWARM=1)
  - /api/ov/detail?excd=NAS&symb=AAPL → ok=True, last=291.13, state=휴장 (이전: 500 Internal Server Error)
  - /api/ov/resolve · /api/ov/chart · /api/ov/news · /api/ov/suggest → 모두 200
  - overseas HTML(AAPL) grep initFX·countTiles·이동평균선·fx-in → 9 hits
  - node --check /tmp/ov_main.js → JS SYNTAX OK (12,657 chars)
  - py_compile scripts/market_dashboard3_realtime.py → OK
  - preview server 콘솔 에러: 없음 (main app 기존 기능 영향 없음)
---

# 해외주식 "네트워크 오류" 수정 + MA/FX UI 격상 + 발열 완화

## 🐛 수정한 버그 (주 목적)

### NameError: `datetime` is not defined — `/api/ov/detail` 500

**증상**: 해외 종목(예: AAPL) 탭을 열면 "해외 종목 정보를 불러오는 중…"이 뜨고
`.catch(function(){fail('네트워크 오류');})`로 떨어져 멈춤.

**원인**: `_is_us_dst(dt: datetime)` (line 675, 미국 서머타임 판정)가 `datetime(y,3,1)` 등을
직접 호출하는데, 모듈 상단에는 `from datetime import date`만 있어 전역에 `datetime` 클래스가
없었음. `datetime`·`timedelta`는 `_ov_market_state()` **함수 내부**에서만 지역 import 돼 있어
분리된 `_is_us_dst`에는 보이지 않음.

`_ov_detail()` → `_ov_market_state()` → `_is_us_dst()` → NameError → 500 → 브라우저 catch.

**동반 증상**: `start()` 흐름에서 `detail` 응답 이후에 `pollTid=setInterval(pollPrice,10000)`가
실행되므로, detail이 죽으면 10초 폴링 자체가 시작되지 않아 "실시간 주가가 안 움직임"도 같은 근원.

**수정** (`scripts/market_dashboard3_realtime.py`, line 63):
```python
# 전
from datetime import date
# 후
from datetime import date, datetime, timedelta
```

KIS API 자체(토큰·현재가·일봉·상세 모두)는 처음부터 정상이었음.

---

## ✨ UI 격상 — 해외 캔들차트 이동평균 (가벼운 격상)

`draw()` 함수 안, 캔들 루프 직후에 **MA5·MA20·MA60·MA120** 추가.
- `sma()` 함수: O(n) 슬라이딩 윈도우 평균.
- 색상: 주황·파랑·보라·초록 (국내 종목 차트와 동일 배색).
- 캔버스 좌상단에 MA 범례 레이블 표시.

## ✨ UI 격상 — 해외 페이지 FX 레이어 (국내 리포트 감성 동기화)

국내 `_inject_fx`와 동일 감성의 경량 FX를 `_OVERSEAS_HTML` CSS·JS에 직접 내장:

**CSS** (`.card` 클래스에 추가):
- 스크롤 등장 애니메이션: `@keyframes ovCardIn` (translateY+opacity, 0.55s, easeOutExpo).
- hover 3D 틸트: `perspective(1100px) rotateX·Y(±2.4°)` — `<canvas>` 포함 카드는 제외(렌더 흐림 방지).
- `prefers-reduced-motion` 전역 가드.

**JS** (`initFX()`, `countTiles()`):
- `initFX()`: `render()` 호출 시 1회 실행. IntersectionObserver로 `.card` 등장 트리거.
  hover 틸트 핸들러 바인딩(캔버스 카드 skip).
- `countTiles()`: `renderRets()` 완료 후 기간수익률 `.v` 값을 0→실제값 카운트업 (750ms, easeOutCubic).

---

## ⚡ 발열 완화 (3D 회전 차트 가시성 제어 + 백그라운드 폴링 정지)

프레임 throttle(30fps)은 사용자 요청으로 **제외**. 아래 세 가지만 적용.

### 1. 3D 자동회전 — 화면 밖 차트 스킵 (`autoRotate`)
```js
// 기존: 탭 안보여도 120Hz로 Plotly.relayout 계속 호출
// 수정: IntersectionObserver로 vis 추적, 화면 밖이면 relayout 생략
var vis=true;
try{var io=new IntersectionObserver(function(es){vis=es[0].isIntersecting;
  if(vis)last=performance.now();},{threshold:0.05});io.observe(gd);}catch(e){}
// frame 루프 조건:
if(!vis || document.hidden || window.MI_APP_ACTIVE === false){ last=now; requestAnimationFrame(frame); return; }
```
M4 퀀트 탭의 3D Surface(확률지형·변동성표면·상관행렬·리스크-리턴)가 모두 적용됨.
스크롤로 시야 밖에 있을 때 WebGL relayout 전혀 안 함 → CPU/GPU 유휴.

### 2. 트레이딩 데스크 interval 폴링 — 백그라운드 탭 정지
```js
// 전
setInterval(loadScr,5000);setInterval(loadFlow,15000);setInterval(loadPaper,4000);
// 후
setInterval(function(){if(!document.hidden)loadScr();},5000);
setInterval(function(){if(!document.hidden)loadFlow();},15000);
setInterval(function(){if(!document.hidden)loadPaper();},4000);
```

### 3. `themeCharts` 1초 폴링 — 백그라운드 탭 정지
```js
// 전
setInterval(function(){themeCharts(false);},1000);
// 후
setInterval(function(){if(!document.hidden)themeCharts(false);},1000);
```

### 4. 해외주식 `pollPrice` — 백그라운드 탭 정지
```js
function pollPrice(){
  if(!excd||!symb)return;
  if(document.hidden)return;  // 추가
  ...
}
```

---

## ⚠️ 비고 / 한계

- **재빌드 필요**: `application_build/build.sh` (CLAUDE.md 규칙 23). 이번 세션은 사용자가 직접 빌드 예정.
- **KIS 해외 지연 시세**: 무료 구독은 15~20분 지연. 진짜 실시간(틱)은 해외 실시간 WebSocket(`HDFSCNT0`) + 유료 신청 필요. 미국장(KST 22:30/23:30~05:00/06:00)에만 값 변동.
- **불가 항목** (데이터 소스 없음): 투자자 매매동향(외국인/기관/개인), 최대주주·지분구조 — KIS 해외 미제공.
- **가능하나 미구현**: 기업개요·투자지표·컨센서스·배당·재무는 Naver 월드스톡 비공식 API로 가능하나 취약(미국주 위주).
- `themeCharts` 1초 폴링은 `visibilitychange` 이벤트로 대체하는 게 더 정석이나, 기존 패턴(인터벌)을 최소 변경으로 유지.
