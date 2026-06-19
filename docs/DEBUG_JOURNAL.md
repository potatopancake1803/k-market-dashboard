# DEBUG JOURNAL — 증상 → 원인 → 해결 → 가드 (append-only)

> **목적:** "이 증상 전에도 본 적 있나?"를 **grep 한 번**으로 끝내, 같은 오류를 다시 디버깅하느라
> 빙빙 돌며 토큰을 낭비하는 일을 막는다. 이 프로젝트의 #1 실패 모드는 (a) 오류 찾느라 순환,
> (b) 고치면 다른 게 깨짐. 이 저널 + `scripts/smoke_check.py`(회귀 게이트)가 그 두 가지를 직접 겨냥한다.
>
> **읽는 법:** 새 오류를 만나면 **먼저 이 파일에서 증상 키워드로 grep** 하라
> (예: `grep -i "흰 화면\|ModuleNotFound\|429\|tool_calls" docs/DEBUG_JOURNAL.md`).
> 맞는 항목이 있으면 그 FIX/GUARD 를 바로 적용 — 재진단 금지.
>
> **쓰는 법 (필수 — 작업 루프의 RECORD 단계):** 어떤 오류든 **진단에 1사이클 이상** 썼거나, 원인이
> 비자명했다면 **반드시** 아래 형식으로 한 항목 append 하라. 한 줄 `### SYMPTOM:` 헤더에 **나중에 grep 될
> 키워드**(에러 문자열·증상 표현·관련 파일)를 담는 게 핵심.
>
> **저널 vs 다른 문서:**
> - 이 저널 = *겪은 오류의 증상별 룩업*(raw 에피소드, 시간순 append).
> - `_STATUS.md` Active Traps = 그 에피소드에서 *증류된 영구 규칙*("항상/절대"). 저널 항목이 영구 규칙이
>   되면 Trap 으로 승격(저널엔 그대로 두고 GUARD 에 "Trap #N 승격" 표기).
> - `changes_history/changes_X` = *기능/변경* 기록(시간순, 불변).
>
> **항목 형식:**
> ```
> ### SYMPTOM: <한 줄, grep 가능한 키워드 포함>
> - **When:** YYYY-MM-DD · 어디서(라우트/파일/상황)
> - **Cause:** 근본 원인 (증상 아님)
> - **Fix:** 무엇을 어떻게
> - **Guard:** 재발 방지 장치 (smoke_check 항목 / 테스트 / Trap #N / 코드 가드)
> ```

---

### SYMPTOM: `ModuleNotFoundError: No module named 'company_report'` — 백엔드 import 실패, 앱/서버 미기동
- **When:** 2026-06-17 · `import market_dashboard3_realtime` (앱 시작·preview·smoke 전부)
- **Cause:** changes_73 이 `company_report.py`/`etf_dashboard.py` 를 `scripts/` → `scripts/archive/` 로 옮겼는데,
  라이브 빌더 `archive/company_report_ver2.py` 가 `from company_report import …`(절대 import)로 형제를 참조.
  `scripts/archive/` 가 `sys.path` 에 없어 해석 실패. 파일 이동을 `py_compile`+스텁테스트로만 "검증"해 놓침.
- **Fix:** `market_dashboard3_realtime.py` 상단에 `sys.path.insert(0, scripts/archive)` 쉼 추가(changes_74).
- **Guard:** `scripts/smoke_check.py`(실제 import 수행) + _STATUS Trap #38. **파일/import 이동은 반드시 smoke_check 통과로 검증.**

### SYMPTOM: 다크모드에서 페이지가 "흰 화면" / 글자 안 보임 (iframe 페이지)
- **When:** changes_8 외 · `/screener_page` `/sector` `/market` 등 iframe 로드 페이지
- **Cause:** iframe 페이지엔 부모 CSS 변수가 상속 안 됨 → `color:var(--label)` 가 흰색-투명으로 해석. 또
  iframe `body` 가 transparent 면 `.frame` 의 하드코딩 `background:#fff` 가 비쳐 흰 바탕에 흰 글자.
- **Fix:** iframe 페이지엔 *명시적* 색 사용 + `body{background:var(--bg)}`+`html.dark` 오버라이드.
  테마는 `localStorage('kmkt-theme')`+`postMessage({kmkt})` 로 동기화.
- **Guard:** _STATUS Trap #1·#12.

### SYMPTOM: SSE 엔드포인트가 매번 HTTP 500 / `RuntimeError: Working outside of request context`
- **When:** changes_3 외 · `/api/llm_*` 등 스트리밍 제너레이터
- **Cause:** 제너레이터가 request 컨텍스트 pop 이후 실행 → 제너레이터 *안*에서 `request.json/args` 읽으면 터짐.
- **Fix:** 뷰 함수에서 request 값을 **미리** 읽어 클로저로 넘긴다.
- **Guard:** _STATUS Trap #2.

### SYMPTOM: 로컬 LLM 이 도구를 안 부름 / `tool_calls:[]` / 외부정보 못 가져와 환각
- **When:** changes_38→39 · `/api/llm_ask`
- **Cause:** 로컬 ~4B 모델은 자유텍스트(`SEARCH:`)·native `tools=[]` **둘 다 무시**. 모델이 도구사용을
  "결정"하길 기대하는 ReAct 설계가 근본적으로 안 됨.
- **Fix:** 도구 사용을 **질문 키워드로 결정적 발동** → 먼저 수집 → "수집데이터로만 답" 강제.
- **Guard:** _STATUS Trap #26 · memory `local-llm-agent`.

### SYMPTOM: 추론모델(qwen3.5 등) 답변이 0자 / `finish_reason=length`, content 비어있음
- **When:** changes_28→30 · `/api/llm_commentary`·`_llm_stream`
- **Cause:** reasoning 모델은 전부 `reasoning_content` 로 쏟고 답변 토큰을 안 냄. `/no_think`·
  `enable_thinking:false` 모두 LM Studio fast-path 가 무시.
- **Fix:** Assistant Prefilling — `{"role":"assistant","content":"<think>\n\n</think>"}` 를 messages 끝에 추가
  → 엔진이 사고 완료로 간주, 즉시 깨끗한 답변. 첫 청크의 앞 `\n`/`</think>` 제거.
- **Guard:** _STATUS Trap #19 · `_llm_model_profile().prefill`.

### SYMPTOM: Gemini 검색 그라운딩 시 `429 RESOURCE_EXHAUSTED` (plain 호출은 200)
- **When:** changes_51→52 · `_gemini_stream`
- **Cause:** 빌링 미연결 키는 `tools:[{google_search:{}}]` 만 quota=0 → 429(크레딧 소진 아님). 2.5-flash 는
  별도 quota lane 이라 무빌링도 동작.
- **Fix:** grounded 429 시 검색 끄고 1회 자동 재시도. 검색은 `_GEMINI_SEARCH_OK`(2.5계열)만 켬.
- **Guard:** _STATUS Trap #32.

### SYMPTOM: raw 페이지(`r"""…"""`)의 AI 박스/SSE 파싱이 아무것도 렌더 안 함
- **When:** changes_29 · `_MACRO_HTML`·`_BACKTEST_HTML`·`_INDEX_HTML` 등 raw 템플릿
- **Cause:** `r"""…"""` 안의 `'\\n'` 은 LF 가 아니라 백슬래시+n. JS `buf.split('\\n')` 가 실제 LF 로 안 쪼개짐.
- **Fix:** raw 페이지 JS 에선 **단일** `'\n'` 사용. (비-raw `"""…"""` 페이지는 반대로 `'\\n'` — Trap #25.)
- **Guard:** _STATUS Trap #21·#25.

### SYMPTOM: 헤드리스로 엔드포인트 테스트 시 응답이 빈/잘림 (SSE 정상인데 버그처럼 보임)
- **When:** trap #8·#18 · `curl`/스크립트로 라우트 테스트
- **Cause:** `_monitor_heartbeat`(15s 무 `/__ping` 시 `os._exit(0)`)가 툴 호출 사이 공백에 서버를 죽임.
- **Fix:** 헤드리스 테스트는 **import + test_client 로** 하라(`scripts/smoke_check.py` 방식 — 서버/워치독 없음).
  굳이 실서버면 백그라운드 `/__ping` 루프를 같은 호출 안에서 돌려라.
- **Guard:** _STATUS Trap #8·#18 · `smoke_check.py`(test_client 사용).

### SYMPTOM: FRED 시계열이 전부 `None`/빈 라인 (키는 있는데 데이터 안 옴) — `_fred_series`
- **When:** 2026-06-17 (changes_84) · `_fred_series("DGS10", months)` → `[None, None, None]`
- **Cause:** FRED `aggregation_method` 유효값은 `avg` / `sum` / `eop` 뿐. `eom`(존재하지 않는 값)을
  넣으면 FRED 가 400/에러 → `except` 가드가 `[None]*` 반환 → 차트 라인만 비고 조용히 지나감.
- **Fix:** `aggregation_method="eop"`(end of period). 그러면 실데이터(DGS10 → [3.97,4.3,4.4,4.45]).
- **Guard:** 키/네트워크 실패 시 `[None]*len(months)` 로 폴백(나머지 차트 정상). FRED 월별 집계는
  `frequency="m"` + `aggregation_method="eop"` 조합. (참고: 단일 최신값은 `_fred_one`.)

### SYMPTOM: 3.10/3.11 에서 `import` 자체가 SyntaxError (실제 앱은 3.12+ 라 멀쩡)
- **When:** trap #35 · `market_intel/report/dashboard.py` 등
- **Cause:** f-string 내부 백슬래시 등 3.12 전용 문법. 메인이 archive 빌더를 끌어와서 전이됨.
- **Fix:** 새 환경 import 깨지면 dashboard.py 의 3.12 문법부터 의심. 새 스크립트는 3.10 호환으로 작성
  (f-string 안 백슬래시 금지 — `body=...; f"{body}"` 로 분리).
- **Guard:** _STATUS Trap #35.

### SYMPTOM: 금융통화위원회(bok_mp) 탭 선택 시 "네트워크 오류"가 표시됨 (Flask 500 에러 발생)
- **When:** 2026-06-18 · 리서치 화면의 bok_mp 탭 조회 시 (`/api/research?cat=bok_mp`)
- **Cause:** `_bok_mp_list` 스크래퍼 함수 시작부(try-except 외부)에 `from bs4 import BeautifulSoup` 임포트가 위치해 있음. 앱이 패키징된 실행본이나 기본 가상환경에 `beautifulsoup4` 패키지가 없어 `ModuleNotFoundError`를 유발하고, 이것이 Flask 단까지 전파되어 500 Internal Server Error를 냄.
- **Fix:** 외부 라이브러리 의존성을 제거하기 위해 BeautifulSoup 파싱 방식을 표준 라이브러리(`re`, `html`) 기반의 정규표현식 파서로 교체하고, HTML 주석(`<!-- ... -->`)을 사전 정제하도록 리팩토링함.
- **Guard:** `scripts/smoke_check.py` regression gate 및 `scripts/api_smoke.py` gate를 통해 dynamic import 및 API 정상 로드를 사전 필터링함. 신규 외부 의존성 도입은 CLAUDE.md 규칙에 따라 극도로 자제함.

### SYMPTOM: 한국은행 보도자료(bok) 및 금통위 의사록(bok_mp) PDF를 보며 AI 질문 시 PDF 원문이 전달되지 않는 문제
- **When:** 2026-06-18 · PDF 뷰어 내 플로팅 AI 질문창 활용 시 (`/api/llm_ask`) 및 PDF 프록시 호출 시 (`/research_pdf2`)
- **Cause:** 
  1. `/api/llm_ask` 핸들러와 `_research_pdf_bytes` 등에서 `_n.isdigit()` 또는 `nid.isdigit()` 조건 검사를 수행함. 금통위 `bok_mp` 식별자(예: `B0000245_10098513`)는 숫자가 아니므로 통과하지 못해 `g_pdf = None` 처리됨.
  2. 한국은행 보도자료(`bok`)와 금통위 의사록(`bok_mp`)은 각각 `/research_pdf2`에서 캐싱 없이 매번 개별적으로 BOK 서버에서 PDF 파일을 중복 다운로드함. 이 과정에서 동시 요청 병목이나 BOK 차단이 발생하면 PDF 로드가 실패하여 `None`이 캐싱될 수 있음.
- **Fix:** 
  1. `_research_pdf_bytes`, `research_pdf2`, `pdf_view`, `api_research_summary`, `_ask_context`, `llm_ask` 등의 검증 조건식을 `cat not in ("bok", "bok_mp") and not nid.isdigit()` 또는 `_c in ("bok", "bok_mp") or _n.isdigit()`로 개선하여 두 BOK 관련 카테고리가 일관되게 숫자 검사를 우회하도록 처리함.
  2. `research_pdf2`가 직접 httpx 다운로드를 수행하는 대신 `_research_pdf_bytes`를 호출하도록 리팩토링함. 이를 통해 뷰어 로드 시점에 받아온 PDF 바이트가 `_PDF_BYTES_CACHE`에 자동 캐싱되어, AI 질문 시점에는 네트워크 호출 없이 즉시 RAM 캐시에서 PDF 바이트를 반환하도록 이중 다운로드 구조를 최적화함.
- **Guard:** `smoke_check.py`에서 라우트와 HTML 조립을 검증함. `api_smoke.py`를 통해 수집 기능을 회귀 방지함.
