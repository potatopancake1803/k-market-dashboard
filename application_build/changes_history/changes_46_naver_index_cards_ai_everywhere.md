---
id: 46
title: Naver-style world index cards (axis chart + info grid) + AI 질문 widget on every screen + agent depth tuning (9B/12B)
date: 2026-06-16 07:20 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
라이브 소스 → 재빌드 불필요.

- **작업1 — 세계 지수 카드를 네이버 "다우존스" 형식으로 정밀화:**
  * 2단 큰 카드(`minmax(440px,1fr)`). 헤더(국기·이름·장마감/개장전 점) + 큰 값 + 등락(▲/▼·색).
  * **축 라벨 차트**: Plotly 영역차트에 **우측 y축 가격 눈금(3단)** + **x축 날짜 라벨(3개)** (네이버
    51,941/51,652/51,364 형식). 60일 일봉(인트라데이는 네이버 공개 API 막힘 → daily).
  * **정보 그리드**: 좌(52주 기준 최고/최저) + 우(전일·고가·저가) — 네이버 카드와 동일. 데이터는
    `/index/{code}/basic` 의 `stockItemTotalInfos`(해외) / `_index_chart`(국내).
- **작업2 — AI 질문 모든 화면 + 9B/12B 정밀도:**
  * **모든 콘텐츠 화면에 플로팅 위젯 주입**: 섹터·시장·백테스터·실시간·세계·세계상세·스크리너
    (+ 기존 리포트/해외/거시/지수/리서치). `_inject_floating_ai(html,scope)` 헬퍼(중복 FAB 방지).
  * **수집 깊이 상향**(상위 모델 가정): 뉴스 6→**10**건, 깊은 기사 본문 2→**3**건·2200→**3000**자,
    답변 토큰 로컬 **1800**/Gemini **2048**. (도구는 changes_44 의 8종 — 뉴스·기사·지배구조·재무·
    애널리스트·동종업계·기술적·파이썬 그대로 활용.)

## How it was done
- `_world_index_one` 에 `info`(전일/시가/고가/저가/52주최고/최저) 추가(basic 응답 1회에서 파싱).
  `_wv_idx_card` 가 info 전달. 국내는 `_world_view` kr 분기에서 `_index_chart` 로 info+spark 구성.
- `_wv_spark`/국내 spark 를 `{c:[종가],d:[날짜]}` 로 변경 → 프론트 x축 날짜 라벨.
- 프론트 `spark()` 재작성(우 y축 3눈금·x 날짜 3개·영역 fill·staticPlot), `icard()` 네이버 레이아웃
  (.ivrow/.iinfo/.icol/.irow), CSS 2단 큰 카드.
- `_inject_floating_ai` 모듈레벨 적용 + 스크리너 라우트 인라인 적용.

## Verification (live, uv + test_client + Naver/KIS)
- 카드 데이터: us 다우존스 value+60p spark(날짜)+info(전일 51,202/고가 51,945/저가 51,364/52주 51,660·41,981);
  kr 코스피 value+50p spark+info(52주 8,933·5,170). iinfo/ivrow CSS, 인라인 JS `node --check` 통과.
- 위젯 주입: SECTOR/MARKET/BACKTEST/REALTIME/WORLD/WORLD_DETAIL/OVERSEAS/MACRO/INDEX/RESEARCH 각 FAB=1,
  screener_page FAB=1.
- 에이전트 깊이: 뉴스 10·기사 3×3000·답변 1800/2048 반영. (도구 e2e 는 changes_44 에서 검증)
- `py_compile` clean.
- **미검증(시각):** 카드 렌더·차트 축·다크·위젯 동작(WKWebView) — 앱 재실행 후 확인.

## Notes & Traps
- **인트라데이 지수 차트는 네이버 공개 API 미제공**(`periodType=minute`→400). daily 60봉으로 형식만 일치.
  네이버 카드 자체도 이미지 차트(`imageCharts` URL) — 본 구현은 Plotly 실차트라 더 낫다.
- 카드 정보 그리드 출처: 해외=`stockItemTotalInfos`(전일=lastClosePrice 등), 국내=`_index_chart`
  (장 phase 에 따라 당일 O/H/L/C 가 종가와 같을 수 있음 — pre/closed 동작).
- 랜딩 top-frame 에는 FAB 미주입(콘텐츠 iframe 각자 FAB → 중복 방지). 콘텐츠 화면엔 전부 존재.
- 생성형 답변 max_tokens 상향은 9B/12B 가정 — 4B 에선 다소 길어질 수 있으나 무해.
