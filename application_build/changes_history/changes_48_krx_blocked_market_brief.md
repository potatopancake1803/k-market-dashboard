---
id: 48
title: KRX direct scrape blocked (anti-bot) → 거래소 종합시황 AI 브리핑 (KIS data) added to research menu
date: 2026-06-16 09:20 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (이전 보류분 #5 KRX 종합시황 이어서)
- **KRX 직접 스크래핑은 불가 판정** (토큰 절약 위해 5회 probe 후 중단): data.krx `GenerateOTP`·
  `getJsonData.cmd`(+ X-Requested-With/세션/Referer 조합) 모두 **`LOGOUT`(400)** 반환(강한 안티봇);
  open.krx OPN 보도자료·각종 RSS 후보 전부 404. 브라우저 에뮬레이션 없이는 불가 → 직접 연동 포기.
- **대안(동일 가치·신뢰 소스): 거래소 종합시황 AI 브리핑** 을 증권사 리포트 뷰어에 **📊 종합시황 탭**으로 추가.
  KIS 기반 `_market_overview`(코스피·코스닥 지수/등락/시장폭/상하한) + `_global_macro_snapshot`(글로벌 배경)
  + `_kis_market_news`(시황·공시 헤드라인) 을 모아 로컬 LLM 이 데일리 브리핑(지수요약·시장폭·글로벌·뉴스테마·
  총평)으로 합성. KRX OTP 의존 0, 안정적.

## How it was done
- `_RESEARCH_CATS["market"]=("market","📊 종합시황")` + 프론트 CATS 에 `['market','📊 종합시황']`.
- `_research_list("market")` → 합성 1행(제목 "📊 오늘의 거래소 종합시황 (AI 브리핑)", pdf=False → PDF 버튼 없음).
- `_market_brief_text()` 헬퍼(지수/시장폭/글로벌/뉴스, None 카운트는 생략).
- `api_research_summary` 에 `cat=="market"` 분기 → `_market_brief_text()` 를 근거로 종합시황 system prompt 로
  `_llm_stream`(1200 tok). 'AI 요약' 버튼이 곧 '시황 브리핑 생성'.

## Verification (live, uv + test_client + KIS/Naver)
- `/api/research?cat=market` → 1행(pdf=False). `_market_brief_text()`=684자(코스피 8726.6 +2.11%·코스닥·
  글로벌 6지표·시황 헤드라인). 종합시황 탭 CATS 존재. `py_compile` clean.
- **미검증(시각/LLM):** 실제 브리핑 텍스트 품질(LM Studio 필요)·탭 렌더 — 앱 재실행 후.

## Notes & Traps
- **KRX(data.krx/open.krx) 직접 스크래핑은 현재 안티봇으로 `LOGOUT` — 단순 httpx 로 불가.** 필요 시
  Playwright 등 브라우저 자동화 또는 유료 데이터가 있어야 함. 종합시황은 KIS 로 대체(이 변경).
- 시장 폭(up/down/상하한)은 장 시간 외엔 KIS 가 None → 브리핑에서 해당 줄 생략(있을 때만 표기).
