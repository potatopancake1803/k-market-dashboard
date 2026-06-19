---
id: 35
title: Implement Agentic Routing and Tool Calling (Search & Python Execution)
date: 2026-06-15 21:55 KST
agent: Antigravity (Gemini 3.5 Flash)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Implemented a 2-stage Agentic ReAct routing loop in the `/api/llm_ask` endpoint to break through the knowledge size limitations of smaller local LLM models.
- Added a fast synchronous 1st-stage routing query (`_llm_complete`) to decide if a query needs external tools.
- Integrated **Realtime Web Search Tool** using the internal `_naver_news` scraper when `SEARCH: <query>` is emitted by the router.
- Integrated **Local Python Execution Tool** (`_run_agent_python`) to run python scripts for math and backtest computations when `PYTHON: <code>` is emitted by the router.
- Added live system progress indicators (`🔍 실시간 뉴스 검색 중...` and `💻 로컬 파이썬 연산 엔진 구동 중...`) streamed to the client's dim reasoning box (`kind: "reasoning"`) to optimize UX during tool execution.

## How it was done
- **Routing Decision (`_llm_complete`)**:
  - Leverages a low-temperature (0.1) fast completion request (capped at 60 tokens, non-streaming) querying the local LLM.
  - Instructs the LLM to output only `DIRECT` (if local screen data suffices), `SEARCH: <query>`, or `PYTHON: <code>` without greetings.
- **Search Tool Integration**:
  - Automatically invokes the built-in `_naver_news(keyword, 6)` scraper to grab details, descriptions, and timestamps.
  - Dedupes results and appends them to the LLM context under `[실시간 인터넷 뉴스 검색 결과]`.
- **Python Execution Tool (`_run_agent_python`)**:
  - Spawns a subprocess using the current virtual environment's python executable (`sys.executable`) to run the generated code blocks securely with a 10s timeout protection.
  - Captures `stdout` and appends it to the LLM context under `[로컬 파이썬 연산 결과]`.

## Verification
- Verified code compilation via: `python3 -m py_compile scripts/market_dashboard3_realtime.py` (Clean pass).
- Expanded [test_ai_grounding.py](file:///Users/minjun1803/.gemini/antigravity/brain/872a46a9-5110-4551-978b-b50cd7db456f/scratch/test_ai_grounding.py) to simulate two distinct scenarios:
  1. **Scenario 1 (Search Tool)**: Asked about 삼양식품's recent antitrust fines and detailed reasons. 
     * *Observation*: Streamed `🔍 실시간 뉴스 검색 중: '삼양식품 과징금 사유'...` first, fetched 6 articles, and answered correctly: *"부과 날짜 2024년 7월 16일, 지앤에프 인수 관련 사유, 과징금 65억 원"*.
  2. **Scenario 2 (Python Executor)**: Asked to calculate `2**12 + 34567` using Python.
     * *Observation*: Streamed `💻 로컬 파이썬 연산 엔진 구동 중...`, executed the formula, and returned the exact math result: **38,663**.
- Both tests completed with HTTP status code 200, proving robust tool execution and contextual grounding.

## Notes & Traps
- **No Rebuild Required**: Dynamically loaded by `app.py` at runtime.
- Emitting progress text with `kind: "reasoning"` automatically integrates into the UI's collapsed reasoning box without frontend changes, making the agent feel very intelligent and responsive.
