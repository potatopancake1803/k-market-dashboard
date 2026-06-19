---
id: 43
title: World index-card mini charts switched from canvas to Plotly (consistent with app's chart tool)
date: 2026-06-16 04:40 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- 세계 페이지 지수 카드의 미니 그래프(스파크라인)를 **캔버스 직접 드로잉 → Plotly 미니 영역 차트**로 교체.
  사용자 피드백: "작은 그래프가 그래픽이 아니라 이미지처럼 나온다 → 앱의 다른 차트처럼 툴(Plotly)로".

## How it was done
- `spark(el,arr)`: `Plotly.react(el, [{scatter, mode:lines, shape:spline, fill:tozeroy,
  fillcolor:rgba(dir색,0.12)}], {axes hidden, yaxis.range=[lo-pad,hi+pad], 투명 bg, height:48},
  {staticPlot:true, displayModeBar:false, responsive:true})`. 방향색은 `--up`/`--down` CSS var →
  `hexRgba()` 로 채움색 변환. `icard()` 는 `<div class="ispark">` 로 변경(캔버스 제거).
- 세계 페이지는 이미 `/plotly.js` 로드 → 추가 의존성 없음.

## Verification
- `_WORLD_HTML`: `Plotly.react` 1, `<canvas` 0; 인라인 JS `node --check` 통과.
- `python3 -m py_compile` clean.
- **미검증(시각):** 실제 렌더 모양·다크 — 앱 재실행 후 확인.

## Notes & Traps
- staticPlot:true 라 hover 없음(스파크라인 용도엔 적합·경량). 카드 6개여도 가벼움.
- 무료 데이터 한계 보완용 API 조사는 본 세션 대화로 사용자에게 전달(코드 변경 아님): 글로벌 국가별
  종목은 **이미 통합된 KIS 해외(홍콩 HKS·상해 SHS·심천 SZS·도쿄 TSE·베트남 HSX/HNX) 순위·시세**가
  1순위(추가 비용 0). 미국 거래대금/movers 는 FMP free(`/actives`,`/gainers`,`/losers`) 또는
  Polygon grouped-daily(EOD, 1콜 전종목 volume) 보강 가능.
