---
id: 36
title: Implement Advanced Governance & Financial Statements Agent Tools
date: 2026-06-15 22:00 KST
agent: Antigravity (Gemini 3.5 Flash)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Solved the limitation where the local LLM routing agent yielded "I don't have this information on screen" when queried about complex governance structure (e.g. Samsung's shareholding hierarchy) or raw 3-year financials.
- Added new native tools to the 1st-stage routing loop (`_llm_complete`):
  * **`GOVERNANCE: <code_6>`**: Automatically pulls major shareholder holdings from FSC (1st-priority) and falls back to DART (2nd-priority).
  * **`FINANCIALS: <code_6>`**: Automatically pulls connecting/separated balance sheet, income, and cashflow statements from DART.
- Augmented the 1st-stage routing system prompt (`dec_sys`) to enforce these new tools when questions regarding shareholder percentages, corporate control disputes, or quantitative revenue/profit figures arise.
- Augmented the final streaming system prompt (`sys_msg`) to dynamically pivot: if tools successfully injected grounded data, it forbids the model from outputting passive "I don't know" phrases and enforces rich factual explanations instead.

## How it was done
- **FSC Shareholding Fetcher (`_get_governance_shareholders`)**:
  - Automatically queries OpenDART for `jurir_no` (corporate registration number) using the 6-digit stock code.
  - Spawns `fsc.fetch_governance_shareholders` (FSC API) within a temporary asyncio loop.
  - If fsc fails, falls back to `dart_c.fetch_major_shareholders` (OpenDART API).
  - Formats results into a clean, text-based shareholder list (Name, relationship, voting ratio %).
- **DART Statements Fetcher (`_get_financial_statements`)**:
  - Queries `dart_c.fetch_statements` for connecting connectivity CFS/OFS balance, income, and cashflow dataframes.
  - Formats dataframes using `to_string(index=False)` to render clean tables inside the LLM prompt.
- **Search Query Token Normalization**:
  - Instructed the routing decision model to strip postposition suffixes (josa) and output noun-only clean query keywords (e.g. `"삼성전자 지배구조"`) instead of long sentence strings to maximize search hits.

## Verification
- Verified syntax compiling: `python3 -m py_compile scripts/market_dashboard3_realtime.py` (Passed).
- Tested both tools via [test_ai_grounding.py](file:///Users/minjun1803/.gemini/antigravity/brain/872a46a9-5110-4551-978b-b50cd7db456f/scratch/test_ai_grounding.py) running within the `.venv-build` sandbox.
- **Test Case 1 (Governance)**: Asked *"삼성전자 현재 지배구조 상태는 어때?"* (How is Samsung's governance?).
  * *Observation*: Router called `🔍 지배구조/주주 현황 조회 중: '005930'...`, fetched major shareholder data (Samsung Life 8.51%, Samsung C&T 5.05%, Lee Jae-yong 1.65%, etc. with sum of 19.85%), and successfully explained the holding hierarchy and control structure.
- **Test Case 2 (Financials)**: Asked *"삼성전자 최근 3개년 매출과 영업이익 추이를 DART에서 직접 찾아서 알려줘."* (Show 3-year revenue and operating profit from DART).
  * *Observation*: Router called `📊 DART 재무제표 조회 중: '005930'...`, pulled 3-year data tables, and accurately computed and summarized revenue (e.g., 2025: 45.2T, 2024: 34.45T, 2023: 15.49T) and profit metrics.
- Both test paths returned status 200, confirming agentic tool calling and high-precision grounding.

## Notes & Traps
- **Zero App Rebuild Required**: Dynamically loaded on restart.
- System prompt redirection solved the passive refusal issue by explicitly checking if `tool_used` is active.
