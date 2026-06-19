---
id: 42
title: World page rebuilt to Naver-style 3-view (국내/미국/글로벌) — index sparkline cards + KPI cluster + marketmap/heatmap + stock list
date: 2026-06-16 04:00 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
World 페이지(`/world_page`)를 첨부 네이버 스크린샷과 동일한 **3뷰 토글(🇰🇷 국내 / 🇺🇸 미국 / 🌍 글로벌)**
레이아웃으로 재구축. 각 뷰: **지수 요약 카드(미니 스파크라인) → KPI 카드 묶음 → 마켓맵/히트맵 → 종목 리스트**.
라이브 소스 → 재빌드 불필요.

- **미국**: 다우존스/나스닥종합/S&P500 카드(40p 스파크라인) + KPI(VIX·나스닥100·달러인덱스·미국10년물)
  + S&P500 섹터 히트맵(전체/NYSE/NASDAQ 토글, changes_41) + 미국 주요종목 40(시총순).
- **글로벌**: 상해종합·항셍·니케이225·유로스톡스50·독일DAX·브라질 BOVESPA 카드(스파크라인) +
  KPI(USD·달러인덱스·국제금·WTI·코스피·코스닥). 국가별 종목 리스트는 무료 데이터 한계로 안내 노트.
- **국내**: 코스피·코스닥 카드(스파크라인) + KPI(코스피200·USD·달러인덱스·금·WTI) + 국내 마켓맵
  (코스피/코스닥 토글) + 시총상위 30(클릭→종목).

## How it was done
- 백엔드 `_world_view(view)`(30초 캐시) — 뷰별로 cards/kpis/list 조립:
  - 지수 현재값: `_world_index_one`(해외)·`_world_domestic_one`(국내), 스파크라인: `_world_chart('index',code)`
    (해외 일봉 closes 40개)·`_index_chart('0001'/'1001')`(국내). 병렬(ThreadPool).
  - KPI: `_global_macro_snapshot`(VIX·달러인덱스·금·WTI·미국10년물)·`_world_snapshot` FX(USD)·`_kis_index`(코스피200).
  - 미국 리스트: `_usmap_pct`(가격+등락 1회 조회, 히트맵과 공유) + `_US_HEATMAP` 메타(시총가중치 정렬).
  - 국내 리스트: `_sector_stocks('0001')` 시총상위.
  - 라우트 `/api/world_view?view=kr|us|global`.
- Finnhub `_finnhub_quote_pct`→`_finnhub_quote`로 변경(가격 c + 등락 dp 반환), `_usmap_pct`가 {t:{c,dp,d}}
  캐시 → 히트맵·미국 리스트가 **한 번의 Finnhub 조회를 공유**(분당 60콜 보호).
- `_WORLD_HTML` 전면 재작성: `.vtabs` 토글, `.icard`(캔버스 스파크라인), `.kcard`, 공용 마켓맵 슬롯
  (`#theMap` — us=`/api/usmap`·kr=`/api/marketmap`, 레전드 색 뷰별), `.wtbl` 리스트. 라이트/다크·
  postMessage 테마 동기화. 종목 클릭 → `miOpenStockTab`(국내)/`miOpenUrlTab`(해외).

## Verification (live, uv + test_client + Finnhub/Naver/KIS)
- `_world_view("us")`: 3 cards(다우 51,671.03 +0.92%, 스파크 40p) / 4 KPI / 40 list rows(NVDA $212.45 +3.54%).
- `_world_view("global")`: 6 cards(상해 4,096.47 +1.61%) / 6 KPI / list note.
- `_world_view("kr")`: 코스피 8,545.98·코스닥 1,034.03 cards(스파크 40p) / 5 KPI(코스피200 1,360.26·USD 1,515.50·
  달러인덱스·금·WTI) / 30 list rows(삼성전자).
- `/world_page`: vtabs/idxRow/`/api/world_view` 각 1; 인라인 JS `node --check` 통과.
- `python3 -m py_compile` clean.
- **미검증(시각):** 실제 카드·스파크라인·맵·리스트 렌더·토글 인터랙션(WKWebView)·다크 — 앱 재실행 후 확인.

## Notes & Traps
- `_world_domestic_one` 은 `price` 키, icard 는 `value` 키 → 국내 카드에 `kp["value"]=kp["price"]` 매핑 필요.
- 국내 카드 등락 0.00% 는 장 phase(pre/closed)에서 `_zero_if_pre` 가 0 처리(기존 동작) — 장중엔 채워짐.
- **무료 데이터 한계(미충족):** 글로벌 국가별(중국/홍콩/일본/베트남) 종목 리스트, 미국 거래량/거래대금
  컬럼(Finnhub /quote 미제공 → 업종/시총으로 대체), 선물·코리아밸류업 등 일부 보조 지수 카드. 향후 유료/
  추가 소스 필요. 나머지(지수 카드+스파크라인+KPI+마켓맵+주요 리스트)는 스크린샷 구조와 동일.
- 미국 view 첫 진입 시 Finnhub ~59콜(히트맵+리스트 공유) → 120초 캐시.
