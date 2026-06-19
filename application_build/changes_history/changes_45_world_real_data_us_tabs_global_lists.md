---
id: 45
title: World page real data — US list filter tabs (Polygon turnover + FMP movers) + global per-country lists (KIS)
date: 2026-06-16 06:10 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (작업1 — 세계 페이지 실데이터, 신규 키 활용)
무료 데이터 한계로 비워뒀던 부분(미국 거래대금/movers, 글로벌 국가별 종목)을 신규 키로 채움.
라이브 소스 → 재빌드 불필요.

- **미국 종목 리스트 필터 탭** (전: 큐레이션 1종 → 후: 4탭):
  * **거래대금 상위** = Polygon grouped-daily(전 미국종목 OHLCV 1콜) → 종가×거래량 정렬, 등락은 직전
    거래일 대비. ETF·페니주 제외 → MU·NVDA·TSLA·SNDK·INTC 등 네이버식 거래대금 리더.
  * **상승/하락** = FMP biggest-gainers/losers(price≥$5 필터로 잡주 제거).
  * **시가총액** = 큐레이션 메가캡 시총순(`_usmap_pct` 공유).
  * 행 클릭 → 해외 종목 탭.
- **글로벌 국가별 종목 리스트(중국/홍콩/일본/베트남)** — 이전 "추후 연동" 노트를 **실데이터로 대체**.
  이미 통합된 **KIS 해외시세**(`_ov_price`)가 홍콩(HKS)·상해(SHS)·심천(SZS)·도쿄(TSE)·호치민(HSX)
  전부 지원함을 확인 → 국가별 대표 ~10~12종목 큐레이션. 글로벌 뷰에 국가 탭 추가.

## How it was done
- `_polygon_grouped_one(date)` (1h 캐시) + `_polygon_turnover(40)`(최근 2거래일로 거래대금·등락), ETF
  블록리스트 `_US_ETF_EXCLUDE`. `_us_stock_list(filt)`: actives=Polygon(폴백 FMP), gainers/losers=FMP,
  mcap=큐레이션. 라우트 `/api/us_list?filter=`.
- `_GLOBAL_STOCKS`(country→(label,ccy,[(excd,symb,한글명)])) + `_global_country_list(country)`
  (`_ov_price` ThreadPool, 60s 캐시) + `/api/global_list?country=cn|hk|jp|vn`.
- World 페이지: US 리스트 `#usFilt` 탭 + `usLoad()`; 글로벌 `#glTabs`(중/홍/일/베) + `glLoad()`.
  컬럼: 거래대금 탭=현재가/전일대비/거래대금/거래량, movers=거래소, 시총=업종/시총, 글로벌=현재가/전일대비.

## Verification (live, uv + test_client + Polygon/FMP/KIS)
- `/api/us_list`: actives(Polygon)=40 (SPCX/MU $981/TSLA/SNDK $1980/NVDA/INTC — 거래대금 $B·거래량),
  gainers/losers(FMP, ≥$5), mcap(NVDA 기술 $212 …). ETF(SPY/QQQ) 제외 확인.
- `/api/global_list`: cn 12(귀주모태·CATL·BYD)·hk 12(텐센트·알리바바·메이퇀)·jp 11(토요타·소니·소프트뱅크)·
  vn 10(빈그룹·빈홈즈·베트콤뱅크) — 모두 실가격.
- World 페이지에 usFilt/glTabs 존재, 인라인 JS `node --check` 통과. `py_compile` clean.
- **미검증(시각):** 탭 인터랙션·렌더(WKWebView) — 앱 재실행 후 확인.

## Notes & Traps
- **Polygon 무료 5콜/분·EOD** — grouped 2콜(당일·전일) 1h 캐시로 충분. 거래대금=종가×거래량(진짜 turnover).
- **글로벌 국가별은 KIS(이미 보유)** 가 정답 — Twelve Data 무료는 미국만, FMP 무료도 미국 위주.
- 글로벌 종목 등락 0.0 은 현지 장 시간 외(KIS가 0 반환) — 장중엔 채워짐.
- 큐레이션 목록이라 종목 추가/교체는 `_US_HEATMAP`/`_GLOBAL_STOCKS` 수동 편집. (전종목 스크리닝은 Polygon
  grouped 확장으로 가능하나 이름 매핑 필요.)
