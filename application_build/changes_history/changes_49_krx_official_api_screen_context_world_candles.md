---
id: 49
title: AI uses on-screen context (stock profile + report bodies) + KRX official Open API (real 종합시황/거래대금) + world cards → candlestick
date: 2026-06-16 10:30 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (라이브 소스 → 재빌드 불필요)
- **작업1 — AI 가 화면의 기수집 정보 활용**: `_ask_context` 강화.
  * 종목(stock): 화면에 떠 있는 **기업 정보(DART 프로필: 대표이사·설립일·본사·표준산업분류)**를 컨텍스트에
    포함 → 외부 재수집 없이 활용.
  * 리포트(research): 현재 카테고리 **목록 + 상위 2개 리포트 본문을 백그라운드에서 읽어** 컨텍스트로 제공
    (네이버 read 페이지/한국은행/종합시황). 리포트 페이지 `KMKT_ASK` 가 현재 `cat` 을 id 로 전달.
- **작업2 — KRX 공식 Open API 연동** (스크래핑 안티봇 대체): `data-dbg.krx.co.kr/svc/apis/*`,
  헤더 `AUTH_KEY=KRX_KEY`, `basDd` 지정. 📊 종합시황 브리핑이 **실제 KRX 데이터**를 사용 — 코스피·코스닥
  지수(종가·등락·거래대금·시총) + **유가증권 거래대금 상위 8종목**. (문서: API_documents/KRX_API_tem/md_conversion)
- **작업3 — 세계 시장 카드 그래프**: 스플라인 선/영역 차트 → **국내 종목과 동일한 캔들 차트 툴**(OHLC,
  상승=#C0392B/하락=#2E75B6)로 교체. 정확한 OHLC 출력.

## How it was done
- `_ask_context`: stock 분기에 `_dart_company_profile` facts(태그 제거) 추가; `research` 분기 신설
  (`_research_list(cat)` 목록 + `_research_read`/`_market_brief_text` 상위 2건 본문, 1800자 컷).
- KRX: `_krx_api(path,basDd)`(AUTH_KEY, 1h 캐시) + `_krx_latest(path)`(최근 거래일 역추적) + `_krx_won()`
  (원→조/억) + `_krx_market_brief()`(idx/kospi_dd_trd·kosdaq_dd_trd 메인지수 + sto/stk_bydd_trd 거래대금 정렬).
  `_market_brief_text()` 맨 앞에 prepend.
- 세계 카드: `_wv_spark`/국내 spark 가 OHLC({d,o,h,l,c}) 반환, 프론트 `spark()` 를 Plotly `candlestick`
  (rangeslider off, 우 y축·x 날짜) 로 재작성.

## Verification (live, uv + KRX/KIS/Naver/DART)
- `_krx_market_brief()`: 코스피 8545.98 (5.20%) 거래대금 40.0조원 시총 6992.2조원 · 코스닥 1034.03 ·
  거래대금 상위 SK하이닉스 8.9조/삼성전자 7.3조/삼성전기 16.63%/… (KRX 공식, 기준 20260615).
- `_ask_context("research","daily")` = 데일리 목록 6건 + 본문; `_ask_context("stock","005930")` 에
  `[화면의 기업 정보]` 포함.
- 세계 카드 spark = OHLC 60봉, 프론트 `type:'candlestick'`, world JS `node --check` 통과.
- `py_compile` clean.
- **미검증(시각):** 캔들 카드 렌더·AI 답변 품질(LLM) — 앱 재실행 후.

## Notes & Traps
- **KRX 정식 API**: `https://data-dbg.krx.co.kr/svc/apis/{idx/kospi_dd_trd, idx/kosdaq_dd_trd,
  sto/stk_bydd_trd, ...}` · 헤더 `AUTH_KEY` · param `basDd`(YYYYMMDD, EOD, '10년~). 비거래일/미게시일은
  빈 OutBlock → `_krx_latest` 로 역추적. (이전 트랩: open.krx/data.krx 웹 스크래핑은 안티봇 LOGOUT — 정식 API 사용.)
- 추가 KRX 엔드포인트 다수 보유(ETF·채권·금·석유·선물·옵션·종목기본정보·파생지수) — 향후 기능 확장 가능.
- 리포트 AI 질문은 상위 2건 본문을 그때 읽음(질문당 ~2 fetch). 캐시(_RESEARCH_CACHE/read)로 완화.
