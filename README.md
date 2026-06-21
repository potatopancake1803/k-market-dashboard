# K-Market Dashboard — AI 협업으로 만든 한국 증시 분석 macOS 앱

> 코딩 관련 지식이 없는 비개발자 대학생이 AI 에이전트와의 협업으로 만든 증시 분석 macOS 네이티브 앱입니다.
> 1인 프로젝트로, 앱에는 정확하지 않은 정보가 있을 수 있습니다. 앱은 계속 업데이트 중입니다. 

<p align="left">
  <img src="https://img.shields.io/badge/platform-macOS-black" />
  <img src="https://img.shields.io/badge/backend-Flask-000" />
  <img src="https://img.shields.io/badge/desktop-pywebview-blue" />
  <img src="https://img.shields.io/badge/quant-NumPy%20%2F%20Plotly%203D-9b6bff" />
  <img src="https://img.shields.io/badge/updates-93%2B-success" />
</p>

---

## 한눈에 보기

| 항목 | 수치 |
|---|---|
| 총 버전 업데이트 | **93회 이상** (변경 이력 파일 95개) |
| 백엔드 코드 | **약 8,100줄** (분리 전 13,166줄 → 40% 감축) |
| 기능 경로(라우트) | **83개** |
| 연동 외부 데이터 소스 | **10개 이상** (KIS·DART·KRX·FSC·FRED·네이버·Finnhub·FMP·Polygon·한국은행) |
| AI 리서치 에이전트 도구 | **7종** |
| 개발 협업 AI | Claude Sonnet / Opus (앱 내부엔 로컬 LLM·Gemini 탑재) |

> 이 프로젝트의 진짜 가치는 기능 목록이 아니라, **AI가 실수하는 패턴을 직접 관찰하고 그 실수를 막는 운영 시스템을 AI와 함께 설계한 과정**에 있습니다. (→ [AI 에이전트 제어 시스템](#ai-에이전트-제어-시스템--이-프로젝트의-핵심))

---

## 무엇을 만들었나

**Flask 백엔드**(주식 데이터를 모아 계산하고 HTML 화면을 생성하는 '두뇌')가 만든 웹 화면을, **pywebview**가 macOS 네이티브 앱 창으로 감싸 보여주는 구조입니다. 웹 기술로 만들었지만 사용자에게는 DMG로 설치하는 평범한 Mac 응용프로그램으로 보입니다.

### 주요 기능

**📈 실시간 시세 & 트레이딩 데스크**
한국투자증권(KIS) API 직접 연동으로 실시간 국내·해외 시세, 10단계 호가창, 거래량 순위 스크리너, 모의 투자(페이퍼 트레이딩) 제공.

**🚀 M4 Pro 퀀트 분석** *(가장 차별화되는 부분)*
몬테카를로 미래주가 시뮬레이션(25,000경로 × 252일, 벡터화 NumPy), 16코어 GPU를 활용한 3D 확률 지형도·변동성 표면(WebGL), Sharpe·Sortino·VaR·CVaR·MDD·CAPM 베타/알파 회귀 등 리스크 지표 자동 산출. ETF는 HHI 집중도·월별 히트맵·DCA 백테스트·3D 상관행렬까지.

**🤖 AI 투자 분석 에이전트**
로컬 LLM(qwen3·gemma) + Gemini 연동 채팅. 뉴스·재무·지배구조·애널리스트 등 7종 도구를 키워드 기반으로 **미리 수집한 뒤** 답하는 결정적(deterministic) 구조로 AI 환각을 차단. 증권사 리포트 PDF 뷰어 + AI 요약 포함.

**🎨 macOS 26 'Liquid Glass' 테마**
반투명 유리 질감, 다크모드, 숫자 롤링 애니메이션 등 Apple HIG를 반영. PyInstaller로 설치 가능한 DMG 빌드.

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 백엔드 | Python · Flask · asyncio (병렬 I/O) · SSE 스트리밍 |
| 데스크톱 | pywebview · PyInstaller (DMG 패키징) |
| 정량 분석 | NumPy(벡터화) · SciPy · Plotly 3D(WebGL) |
| 데이터 | KIS · DART · KRX · 금융위(FSC) · FRED · 네이버 금융 · 한국은행 ECOS 외 |
| AI | Claude(개발 협업) · 로컬 LLM(LM Studio) · Gemini |
| 캐싱 | SSD parquet 디스크 캐시 + RAM TTL 캐시 + 시작 프리워밍 |

---

## AI 에이전트 제어 시스템 — 이 프로젝트의 핵심

작업을 거듭하며 문제가 생길 때마다, AI 협업자가 잘 작동하도록 통제하는 장치를 하나씩 쌓아 올렸습니다.

- **`CODEMAP.md` (코드 내비게이션 인덱스)** — 83개 라우트·템플릿이 *몇 번째 줄에 있는지* 표로 정리한 "AI를 위한 목차". 전체를 읽는 대신 필요한 줄만 펼쳐 읽어 토큰을 절약.
- **`smoke_check.py` (회귀 게이트)** — import 성공·엔드포인트 응답·화면 출력 동일성(골든 해시)을 자동 검증. `SMOKE PASS ✓`가 떠야만 작업을 완료로 인정.
- **코드베이스 모듈화** — 13,000줄 단일 파일을 핵심 로직 / 화면 템플릿 / 순수 계산 함수 셋으로 분리해 컨텍스트를 작고 명확하게.
- **`DEBUG_JOURNAL.md` (버그 방지 저널)** — 증상→원인→해결→예방 구조의 룩업 문서. 세션이 바뀌어도 같은 버그를 다시 디버깅하지 않게.
- **Developer Mode (`⌘⇧D`)** — 실행 중 앱에서 화면 요소를 클릭하면 소스 파일·줄 번호를 역추적해 AI가 읽을 노트로 저장. 사용자의 눈과 에이전트의 입력을 잇는 직접 채널.
- **Claude Code Hooks (자동 회귀 게이트)** — 백엔드 편집 시 회귀 검사를 강제 실행, 실패하면 턴 종료 자체를 차단. 우회 불가능한 자동 품질 게이트.
- **Reflect System (교정 자동 포착)** — 사용자 교정 발화를 신뢰도 점수화해 축적. 백업→무결성 검증→실패 시 자동 롤백의 3중 안전장치.
- **`health_check.py` (능동 구조 점검)** — 파일 비대화·문서-코드 드리프트를 임계치로 감지해 재설계를 먼저 제안. 에이전트가 스스로를 감사하는 구조.

> 이것은 단순히 AI를 *사용한* 경험이 아니라, **사전 엔지니어링 지식 없이 AI 운영 시스템을 처음부터 설계한** 경험입니다.

---

## 실행 방법

```bash
# 네이티브 앱 실행 (권장)
uv run application_build/app.py

# 백엔드만 디버그 실행
MI_NO_OPEN=1 MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py

# 앱 빌드 (DMG)
cd application_build && ./build.sh
```

> 실시간 데이터 소스(KIS·DART 등)는 각 기관 API 키가 필요합니다. 키는 `.env` / `API.env`로 주입하며 **저장소에는 포함되지 않습니다.**

---

## 저장소 구성

```
scripts/           ← 라이브 백엔드(market_dashboard3_realtime.py), 회귀 게이트, 자동화 훅
market_intel/      ← 데이터 수집·분석·리포트 생성 패키지
application_build/ ← pywebview 런처, 빌드 스크립트, 변경 이력(changes_history)
docs/              ← CODEMAP(라인맵 인덱스), DEBUG_JOURNAL(증상→해결 룩업)
tests/             ← 순수함수 단위 테스트 + 골든 렌더 기준선
```

---

*개발: 1인 · AI 에이전트 협업 · 2026년 진행 중*
