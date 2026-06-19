---
id: 87
title: Align BOK and BOK MPC PDF features and optimize caching
date: 2026-06-18 20:47 KST
agent: Antigravity (Gemini 3.5 Flash)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Grouped Bank of Korea press releases (`bok` category) and Monetary Policy Committee minutes (`bok_mp` category) together in category checking conditions inside the backend script `scripts/market_dashboard3_realtime.py`.
- Unified and optimized PDF rendering in `/research_pdf2` by retrieving the PDF via `_research_pdf_bytes` for all categories, utilizing the in-memory cache and avoiding redundant BOK/Naver server requests when opening the PDF and asking questions in the AI widget.
- Added traceback and exception logging to `_research_pdf_bytes` to improve debuggability of PDF retrieval failures.

## How it was done
- Modified `_research_pdf_bytes`, `research_pdf2`, `pdf_view`, `api_research_summary`, `_ask_context`, and `llm_ask` to bypass strict `isdigit()` checking for both `"bok"` and `"bok_mp"`, checking `cat not in ("bok", "bok_mp")` or `_c in ("bok", "bok_mp")`.
- Replaced direct `httpx.get` calls in `research_pdf2` with a call to `_research_pdf_bytes` to stream PDF bytes directly from memory cache if already populated, preventing dual downloads and rate limiting.
- Replaced the blank exception handler in `_research_pdf_bytes` with `logger.exception` logging.

## Verification
- Ran `uv run scripts/smoke_check.py` -> **`SMOKE PASS ✓`** (All routes and renders compared successfully).
- Ran `uv run scripts/api_smoke.py` -> **`API-SMOKE PASS ✓`** (All data collectors executed and validated).
- Ran `python3 scripts/health_check.py` -> **`HEALTH: ✅ 모든 지표 정상.`**

## Notes & Traps
- Grouping `bok` and `bok_mp` makes the BOK-scraped data handling consistent. `bok` and `bok_mp` items bypass the pure digit verification for `nid` so that BOK-related formats are loaded properly.
