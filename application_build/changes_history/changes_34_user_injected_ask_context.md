---
id: 34
title: Support user-injected context and guidelines in AI Ask widget
date: 2026-06-15 21:45 KST
agent: Antigravity (Gemini 3.5 Flash)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Added a collapsible `<details>` panel to the `💬 AI에게 질문하기` widget UI (`_ASK_WIDGET_HTML`) containing a `<textarea id="askCtx">` for user-injected context (external news, reports, financial figures, or prompt persona instructions).
- Updated the Javascript in `_ASK_WIDGET_HTML` to capture this context and send it via the `user_context` body parameter on POST requests to `/api/llm_ask`.
- Updated the backend `/api/llm_ask` endpoint to receive `user_context`, clamp it to 4,000 characters (to prevent token overflows), and append it to the LLM query context under a new section: `[사용자 주입 참고 데이터 및 추가 지시사항]`.
- Updated system prompt instructions to guide the local AI model to prioritize analyzing this injected context alongside the live screen facts.

## How it was done
- **UI Widget (`_ASK_WIDGET_HTML`)**:
  - Inserted a glass-morphic styled `<details>` box below the widget title.
  - Included a `<textarea>` with a clear placeholder explaining that users can paste external articles or request specific analysis tones (e.g., "Analyze as a conservative value investor").
  - The textarea input is disabled during the streaming network call to preserve request sanity.
- **Backend Route (`/api/llm_ask`)**:
  - Read `user_context` from `request.json`.
  - Appended it to the prompt's `ctx` variable if present.
  - Augmented the `sys_msg` to command the model to base its reasoning on both the `[현재 화면 데이터]` and the `[사용자 주입 참고 데이터 및 추가 지시사항]`.

## Verification
- Ran syntax validation: `python3 -m py_compile scripts/market_dashboard3_realtime.py` (Passed cleanly).
- Created a unittest simulation script in `scratch/test_ai_grounding.py` using Flask's `test_client()` running within the target `.venv-build` python sandbox.
- **Test Case**: Passed a fictional user context (*"Samsung Electronics established its first Mars space branch on June 15, 2026, naming Kim Hwa-seong as director."*) and asked: *"What is the exact founding date of the Mars branch mentioned in the newly injected data?"*
- **Observed Output**: Streamed back **"2026년 6월 15일입니다."** successfully, proving the local Qwen model is successfully grounded on the user-injected runtime context.

## Notes & Traps
- **No App Rebuild Required**: Since `app.py` imports `market_dashboard3_realtime.py` dynamically at runtime, updates are live upon app restart or via the menu bar's "Check for Updates" restart mechanism.
- Context size is capped at 4,000 characters on the backend to safeguard low-latency context slots of smaller local models.
