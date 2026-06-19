---
id: 20
title: Refactor overseas UI layout to match domestic, and fix realtime page chart/URL parameters
date: 2026-06-12 KST
agent: Antigravity
area: [ui, realtime, overseas]
status: partial
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  python3 -m py_compile scripts/market_dashboard3_realtime.py -> OK (no syntax errors)
  Visual verification requires live browser run.
---

# Refactor overseas UI layout and fix realtime page

## 🛠️ What was done

### 1. 해외주식 UI 전면 개편 (국내 주식 UI 룩앤필 동기화)
- **Hero Card**: 이전 작업(changes_19)에서 도입된 `.hero-block` (화면 폭을 꽉 채우는 형태) 대신 국내 주식의 실시간 트레이딩 페이지와 완전히 동일한 `.hero` (모서리가 둥근 플로팅 카드 형태, `margin: 10px 14px 12px; border-radius: 14px;`)로 교체했습니다.
- **Rolling Animation CSS 동기화**: `h-px`의 애니메이션이 국내와 완벽히 일치하도록 `display: inline-flex` 대신 `display: inline-block`을 적용하고 `line-height` 등 기타 속성값을 국내 UI와 일치시켰습니다. JS 쪽의 높이 계산 기준선도 38에서 34로 통일했습니다.
- **2단 그리드 레이아웃**: 핵심지표, 기간수익률, 차트, 뉴스 등을 일렬로 나열하던 방식에서 벗어나, `_REALTIME_HTML`과 유사한 `.main` 그리드 레이아웃(`grid-template-columns: 1fr 300px`)을 도입해 2단으로 콘텐츠가 배치되도록 구조를 개선했습니다.

### 2. 실시간 데스크 페이지(Realtime Page) 기능 미구현 문제 해결
- **현재가 차트 동적 업데이트 누락 수정**: 이전에는 `loadHistory()`를 통해 최초 로드 시 한 번만 캔들과 현재가 점선이 그려졌습니다. 시세가 웹소켓(`es.onmessage`)을 통해 들어올 때마다 `drawChart()`를 호출하도록 수정해, 실시간 틱이 변할 때마다 차트상의 현재가 점선 위치도 즉각적으로 반응하도록 개선했습니다.
- **초기 종목 코드 연동 로직 추가**: 실시간 버튼을 통해 탭이 열릴 때 종목 코드를 URL 파라미터로 넘겨받도록 JS 초기화 코드를 수정(`new URLSearchParams(location.search).get('code')`)했습니다. 이를 통해 타 화면에서 특정 종목을 확인하다가 '실시간' 기능을 진입할 때 무조건 삼성전자(005930)가 아닌 현재 보고 있던 종목의 실시간 데스크가 즉시 열립니다.

## ⚙️ How it was done (Technical Details)
- `_OVERSEAS_HTML` 내부 CSS 및 DOM 요소명 리팩토링 (`.hero-block` -> `.hero`, `.h-sym-row` -> `.h-top`, `.wrap` -> `.main` `.col-left`/`.col-right` 구성).
- `_REALTIME_HTML` 내 `es.onmessage` 구문 안에서 `if(d.last>0) { ... drawChart(); }` 호출을 추가해 성능 최적화가 되어있는 Canvas 리렌더링을 틱마다 트리거시켰습니다.
- `_REALTIME_HTML` 초기화 변수 선언 시 `code=(new URLSearchParams(location.search).get('code')||'005930')`로 할당하여 연동성을 높였습니다.

## ✅ Verification (commands + observed output)
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` 구문 검사 이상 없음.
- 브라우저 상의 실제 시각적 레이아웃과 렌더링 확인이 필요하므로 `status: partial`로 설정합니다.

## ⚠️ Notes & Pending Issues
- Canvas를 `es.onmessage` 내에서 지속 렌더링하도록 묶어뒀습니다. 브라우저 성능 최적화를 위해 차트 렌더링 함수(`drawChart`)에는 이미 `devicePixelRatio` 스케일링과 Canvas Clear 처리 로직이 효율적으로 작성되어 있어 별다른 퍼포먼스 저하가 없을 것으로 예상됩니다.
