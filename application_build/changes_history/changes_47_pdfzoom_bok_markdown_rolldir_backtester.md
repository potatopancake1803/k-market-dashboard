---
id: 47
title: PDF zoom viewer + BOK 보도자료(RSS) in research + chat markdown rendering + realtime roll direction fix + backtester form polish
date: 2026-06-16 08:40 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (라이브 소스 → 재빌드 불필요)
- **#1 PDF 확대/축소 뷰어**: `/pdf_view?src=&title=` — 같은 출처 PDF 프록시를 임베드 + 줌 툴바
  (−/맞춤(page-width)/+ · 50~300% · 새 창). 네이티브 PDF `#zoom=` 사용(WKWebView 호환). 증권사 리포트
  `openPdf` 가 raw PDF 대신 `/pdf_view` 로 열도록 변경.
- **#2 한국은행 보도자료**: 증권사 리포트 뷰어에 **🏦 한국은행 탭** 추가(7번째). 목록=공식 RSS
  (`news.rss?menuNo=201263`), 본문/PDF=view.do → `/fileSrc/*.pdf`. PDF 뷰어(#1)+AI 요약 그대로 재사용.
- **#3 챗 마크다운 렌더링**: 플로팅 AI 답변을 raw 텍스트 대신 `mdToHtml()` 로 변환(헤더·**굵게**·*기울임*·
  불릿·`코드`·문단). 스트리밍 중 `ansBuf` 누적 후 재렌더. 전용 CSS(.mdh/.mdul/code) 추가.
- **#4 실시간 숫자 롤링 방향**: 굴림 방향이 전일대비 부호(dir)로 고정돼 그날 상승종목이면 하락 틱도 위로
  굴렀음 → **직전 표시값 대비 실제 틱 방향**(`px>=lastPx`)으로 수정(§12). 실시간 페이지 + 지수 페이지.
- **#6 백테스터 폼**: 애플톤·빈공간 제거(종목 필드 `flex:1` 로 남는 폭 흡수, 필드 폭 정리) + **자동완성
  드롭다운이 아래 차트 패널에 가려지던 문제 수정**(각 .panel 이 backdrop-filter 로 독립 stacking →
  `#formPanel{z-index:30}` + `.sgg{z-index:1000}`).
- **#5 KRX 종합시황**: KRX(open.krx.co.kr)는 OTP 토큰 기반 POST 라 별도 대규모 작업 → 이번엔 보류(노트).

## How it was done
- `_bok_list()`(RSS item→nid/title/date, RFC822·ISO 날짜 파싱) + `_bok_read(nttId)`(view→`/fileSrc/..pdf`
  +본문). `_research_list`/`_research_read`/`research_pdf2` 에 `cat=="bok"` 분기. `_RESEARCH_CATS["bok"]`
  + 프론트 CATS 에 `['bok','🏦 한국은행']`.
- `_PDF_VIEW_HTML` + `/pdf_view` 라우트(같은 출처 src 만 허용). 줌은 iframe `src#zoom=page-width|NN`.
- 위젯 `mdToHtml`(정규식 경량 파서) + `ansBuf` 누적 렌더. `_ASK_WIDGET_HTML` 내.
- 실시간 `updateHero`: `tickUp = lastPx ? (px>=lastPx) : up`. 지수 `updateHero`: 동일 패턴.
- 백테스터 CSS `.f-code/.f-strat/.f-num/.f-days` + `#formPanel` z-index + `.sgg` z-index↑, 마크업 클래스.

## Verification (live, uv + test_client + node --check)
- BOK: `_bok_list`=30건(날짜·nttId·제목), `_bok_read`=본문+실 PDF(/fileSrc), `/api/research?cat=bok`=30.
- `/pdf_view`: iframe+줌버튼+SRC(page-width) 존재. research `openPdf`→`/pdf_view`.
- 위젯: `mdToHtml`/md CSS/`ansBuf` 존재, 위젯 JS `node --check` 통과.
- 실시간/지수: `tickUp` 적용.
- 백테스터: `#formPanel`(z30)·`.sgg`(z1000)·`.f-code`, 폼 JS `node --check` 통과.
- `py_compile` clean.
- **미검증(시각):** PDF 줌 동작·BOK PDF 렌더·마크다운 모양·롤 방향·백테스터 드롭다운 — 앱 재실행 후 확인.

## Notes & Traps
- **backdrop-filter = 독립 stacking context** → 패널 내부 absolute 드롭다운이 다음 패널에 가려짐. 드롭다운
  있는 패널은 `position:relative;z-index` 를 올려야 한다(백테스터 자동완성 교훈).
- BOK RSS = `https://www.bok.or.kr/portal/bbs/B0000502/news.rss?menuNo=201263`(보도자료). 첨부 PDF 는
  `/fileSrc/...pdf`(HWP 만 있는 글은 PDF 없음 — 안내 표시). list.do 본문은 JS 렌더라 RSS 사용.
- `/pdf_view` 는 same-origin(`/`로 시작) src 만 허용(SSRF 방지). PDF 줌은 네이티브 `#zoom=`(pdf.js 불필요).
- KRX 종합시황은 OTP(generate.cmd) 흐름 필요 → 추후 별도 구현.
