---
id: 44
title: AI agent major upgrade — FMP data layer + new tools (rich financials, analyst consensus, peers, price/technicals)
date: 2026-06-16 05:30 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (작업2 — AI 에이전트 대대적 업그레이드)
"실제 활용 가능" 수준으로 에이전트 도구 suite 를 대폭 확장. 라이브 소스 → 재빌드 불필요.
신규 키(FMP_KEY) 활용.

- **FMP 데이터 레이어**(`_fmp_get`/`_fmp_one`, stable 엔드포인트, 캐시): quote·profile·ratios-ttm·
  key-metrics-ttm·stock-peers·price-target-consensus·grades-consensus·movers. (FMP v3 는 2025-08 폐지,
  무료키는 `/stable/`)
- **해외 펀더멘털 대폭 강화**(`_get_overseas_financials` FMP 재작성, Finnhub 폴백): 섹터/산업·시총·현재가·
  52주·PER·EPS·거래량·50/200MA·유동/당좌/부채비율·순이익/영업/매출총이익률·ROE/ROA·배당·EV/EBITDA·EV/매출·PBR·PSR.
- **신규 도구 3종**:
  * `_get_analyst_view(scope,id)` — 미국=FMP grades(매수/보유/매도 분포)+price-target(컨센/중간/최고/최저),
    국내=KIS 투자의견(평균의견·목표가·분포).
  * `_get_valuation_peers(scope,id)` — 미국=FMP stock-peers 시총 상위 비교.
  * `_get_price_technicals(scope,id,excd)` — 모멘텀(5/20/60/120일)·52주 위치·연율변동성·MDD·MA배열(정/역배열).
    국내=`_afetch`, 해외=`_ov_chart`.
- **에이전트 gather 확장**(`/api/llm_ask`): 기존 (1)뉴스검색 (2)기사본문 (3)지배구조 (4)재무 +
  **(5)애널리스트** (목표주가/투자의견/컨센서스/매수매도/전망 키워드) **(6)동종업계 비교** (비교/경쟁/peer/밸류)
  **(7)가격·기술적** (주가/흐름/추세/모멘텀/52주/급등락/전망) **(8)파이썬 계산**. 모두 키워드 결정적 발동.

## How it was done
- 로컬 4B 모델이 도구를 못 고르는 한계(트랩#26) 유지 전제 → 도구는 시스템이 결정적으로 수집, 모델/Gemini 는
  합성만. 도구 풍부화로 합성 품질을 끌어올림.
- 미국 종목은 FMP 가 펀더멘털·애널리스트·peers 를 한 번에 커버(무료, 풍부) → Finnhub 보다 우수, 폴백 유지.
- `_fnum` 포맷 헬퍼(천단위·% 변환). FMP 캐시 TTL: quote 60s, ratios/peers 30m, profile 1h.

## Verification (live, uv + FMP + LM Studio qwen3-4b)
- 도구 단위: `_get_overseas_financials("TSLA")`=섹터/시총/유동2.04/당좌1.62/D-E0.11/순이익3.96%/EV-EBITDA127 …;
  `_get_analyst_view("ov","AAPL")`=매수69·보유33·매도7→Buy, 목표 $326.47; `_get_valuation_peers("ov","NVDA")`=
  GOOGL/AAPL/MSFT/TSM/AVGO/ADI 시총; `_get_price_technicals("ov","AAPL")`=모멘텀 5/20/60/120·52주84%·변동성29%·MA배열.
- end-to-end(`/api/llm_ask`): "애플 목표주가·밸류에이션·경쟁사 대비?" → 펀더멘털+애널리스트+동종업계+기술적
  발동, 답변에 목표가 $326.47(+9.8%)·PER·모멘텀 인용. "테슬라 기술적 상태?" → 뉴스+기사+기술적 스냅샷 →
  52주위치 57%·모멘텀·MA배열 근거 답변. **실전 수준 확인.**
- `python3 -m py_compile` clean.

## Notes & Traps
- **FMP 무료는 `/stable/` 만**(v3=403 Legacy). Twelve Data 무료=미국 quote만(글로벌/movers 유료).
  Polygon grouped-daily=전 미국종목 OHLCV 1콜(EOD, 거래대금/movers용 — 작업1에서 사용 예정).
- 국내 애널리스트는 KIS `fetch_invest_opinions` 사용(시간외 제약은 기존 트랩). 국내 peers 는 추후.
- 키워드 결정적 발동이라 한 질문에 여러 도구가 동시에 붙어 ctx 가 풍부해짐(합성 모델이 취사선택).
