---
id: 40
title: Overseas financial-health data (Finnhub) + Gemini cloud provider option for AI 질문하기
date: 2026-06-16 02:10 KST
agent: Claude (Opus 4.8)
files:
  - scripts/market_dashboard3_realtime.py
status: partial
---

## What was done (feedback round 3)
All live source → **no .app rebuild**.

- **피드백 — 해외 재무건전성 조회 실패:** TSLA 같은 해외 종목은 한국 코드가 없어 DART가 안 잡히고
  뉴스검색도 "재무건전성"으론 0건이라 답을 못 했다. **Finnhub `/stock/metric` 으로 해외 재무건전성
  지표를 수집**하도록 추가(유동·당좌비율, 부채비율 D/E, 마진, ROE/ROA, 성장률, PER/PBR, 52주). 검증:
  TSLA → 유동비율 2.04 / 당좌 1.44 / D/E 0.11 / 순이익률 3.95% / ROE 4.77% 정상 수집.
- **작업9 — 로컬/클라우드(Gemini) 선택:** AI 질문하기 챗에 `💻 로컬 / 🌩️ Gemini` 세그먼트 추가.
  Gemini 선택 시 **질문당 1회 호출**(결정적 에이전트가 무료 도구로 데이터를 먼저 다 모으고, Gemini는
  합성만) — 무료 20회/일 절약. 429/오류는 우아하게 처리(“한도 소진 → 로컬로 전환” 안내).
- **작업8 — 로드된 모델 사용:** 로컬 경로는 이미 `_pick_llm_model_ex` 가 **로드된 모델 우선**이라
  qwen3.5-9b 를 로드해두면 그걸로 합성한다(코드 변경 불필요). 도구 판단은 결정적 에이전트가 담당하므로
  9B/12B 는 "합성"만 잘하면 됨 → 24GB M4 Pro 에 qwen3.5-9b 권장(gemma-12b 도 가능).

## How it was done
- `_get_overseas_financials(symb)`: Finnhub `/stock/metric?metric=all` → 핵심 재무건전성 지표를
  한국어 라벨 텍스트로 포맷(키 폴백 다중: *Quarterly→*Annual, *TTM→*Rfy 등).
- 결정적 에이전트(`/api/llm_ask` generate): (4) 재무 분기를 한국=DART / **해외=Finnhub** 로 분기.
  키워드 확장(건전성·유동·당좌·마진·ROE·수익성·성장·밸류 등).
- `_gemini_stream(sys,user)`: `v1beta/models/{KMKT_GEMINI_MODEL=gemini-2.0-flash}:streamGenerateContent?alt=sse`
  → SSE 파싱 → `data:{text}` yield. HTTPError 429/400/403 별 안내 메시지.
- `/api/llm_ask` 에 `provider`("local"|"gemini") 파라미터 → 최종 합성을 `_gemini_stream` 또는
  `_llm_stream(think=)` 로 분기. 위젯: `#kmktAiProv` 세그먼트(.on 토글) + body 에 `provider`.

## Verification (live, uv + test_client + real network)
- `_get_overseas_financials("TSLA")` → 15개 지표 정상(위 수치).
- `_gemini_stream` → 현재 키가 **429 "prepayment credits depleted"** → 코드가 안내 메시지로 우아하게
  처리함을 확인(스트림이 시스템 알림 1건 yield).
- 위젯: `#kmktAiProv`(1) + `data-p="gemini"`(1) + `provider:aiProv`(1); `/api/llm_ask {provider:gemini}` → 200.
- `python3 -m py_compile` clean.
- **미검증:** Gemini 정상 응답(키 빌링 429 상태라 실응답 불가 — 사용자 키/티어 확인 필요);
  해외 재무 분기가 실제 에이전트 답변에 반영되는 라이브 LLM 합성(로컬/클라우드 모두 화면 확인 권장).

## Notes & Traps
- **Gemini 키 현재 429**: "prepayment credits are depleted"(계정/빌링 이슈, 모델 무관 — 2.0-flash/
  2.5-flash/flash-latest 모두 동일). 무료 티어로 쓰려면 AI Studio 키의 티어/빌링 확인 필요.
  `KMKT_GEMINI_MODEL` 로 모델 오버라이드 가능.
- **Finnhub 가 해외 재무건전성의 1순위 소스** (DART는 국내 전용). `FINNHUB_KEY`(root .env + api_documents).
- 로컬 모델은 여전히 도구를 스스로 호출하지 못함(트랩#26) → 도구는 결정적으로 수집, 모델/Gemini 는
  합성만. 그래서 Gemini도 "1회 호출"로 충분.
