---
id: 41
title: US S&P 500 sector heatmap (NYSE/NASDAQ toggle) on World page; domestic marketmap placement confirmed
date: 2026-06-16 03:00 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (마켓맵 우선 — user-chosen scope)
Live source → **no .app rebuild**.

- **작업1 — 미국 S&P 500 마켓맵 신규:** World 페이지(`/world_page`)의 📈 주요 지수와 💱 환율 사이에
  **🇺🇸 미국 S&P 500 섹터 히트맵**(트리맵)을 추가. **전체 / 뉴욕 NYSE / 나스닥** 토글. 색은 미국 관례
  (상승=초록 / 하락=빨강), -3~+3%. (참조: 첨부 Yahoo S&P500 heatmap 이미지)
- **작업2 — 국내 마켓맵 위치:** `/market`(시장 현황)은 이미 `지수 카드(.ovw) → 🗺️ 마켓맵 → 시총상위 리스트`
  순서라 "카드↔리스트 사이" 요구가 이미 충족됨(별도 변경 불필요). 확인만 함.
- 범위: 사용자 선택대로 "마켓맵 우선 + 미국 ~60종목". 세계 페이지의 네이버식 전면 재구축(지수 스파크라인
  카드·국가별 종목리스트)은 다음 세션으로 보류.

## How it was done
- 데이터 제약 진단(라이브): Finnhub `/index/constituents`=403(유료), Yahoo `v7/quote` 벌크=401,
  EODHD 벌크=실패 → **핵심 대형주 ~59종목을 GICS 섹터별로 큐레이션**(`_US_HEATMAP`: ticker, 거래소
  N/Y, 근사 시총가중치 $B). 등락률만 Finnhub `/quote`(dp)로 조회.
- `_usmap_pct()`: 전체 59종목 등락률을 **1회만** 병렬 조회(ThreadPool 10)하고 120초 캐시 →
  전체/NYSE/NASDAQ 3개 뷰가 **공유**(Finnhub 분당 60콜 한도 보호; 토글은 캐시 재사용→즉시).
- `_usmap_fig(exch)`: 거래소 필터 후 Plotly `go.Treemap`(섹터 parent→티커), value=가중치, color=등락률,
  colorscale 빨강↔회색↔초록, 섹터 라벨 한글(`_US_SECTOR_KR`). figure 캐시 per exch.
- 라우트 `/api/usmap?exch=all|nasdaq|nyse`. World 페이지: `<script src="/plotly.js">` + 토글 세그
  (`#usSeg`) + `#usMap` + `loadUsMap()`(진입·전환 시에만 조회, 실시간 폴링 없음 — 발열↓).

## Verification (live, uv + test_client + Finnhub)
- `_usmap_fig`: all=71 tiles / nyse=47 / nasdaq=30, 첫 로드 4.5s(59 Finnhub 콜, <60/분), 이후 토글은
  캐시로 즉시. pct 캐시 59종목. 리프 샘플 NVDA/AAPL/MSFT/AVGO/ORCL.
- `/api/usmap?exch=nyse` ok=true; World 페이지에 `#usMap`/`#usSeg`/plotly.js 각 1개.
- World 페이지 인라인 JS `node --check` 통과.
- `python3 -m py_compile` clean.
- **미검증(시각):** 실제 트리맵 렌더 모양·다크 대비·토글 인터랙션(WKWebView) — 앱 재실행 후 확인 권장.

## Notes & Traps
- **Finnhub 무료 60콜/분.** 한 번에 59콜 버스트는 한도 내. 등락률을 1회만 받아 3뷰가 공유하므로 토글로는
  추가 콜 없음. 다른 Finnhub 기능(_get_overseas_financials)과 같은 분에 겹치면 일부 429 가능 → 그땐 빈 타일.
- S&P500 구성종목은 큐레이션(고정 목록)이라 지수 리밸런싱은 수동 반영 필요. 가중치도 근사값(시총 변동
  느림). 등락률만 실시간.
- 색 관례: 미국 히트맵=초록 상승(US), 국내 마켓맵=빨강 상승(KR) — 의도된 차이.
- 세계 페이지 네이버식 전면 클론(국내/미국/글로벌 토글 + 지수 스파크라인 카드 + 국가별 종목 리스트)은
  대규모 → 다음 세션. 이번엔 미국 히트맵 + 국내 마켓맵 배치 확인까지.
