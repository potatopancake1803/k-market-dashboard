---
id: 26
title: Make Recommended Tokens Dynamic by Model Context Length
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **Backend Model Metadata Payload Update**: Updated the Python backend's `api/llm/status` endpoint to extract `max_context_length` from the LM Studio `/api/v0/models` API and pass it as `max_ctx` in the frontend state payload.
- **Dynamic Recommended Range Calculation**: Modified the frontend `render(st)` logic to dynamically calculate the `Recommended` max tokens range as exactly `1/8 ~ 1/4` of the model's supported `max_ctx` (as requested).
- **Fallback Logic**: If LM Studio is not actively running (and thus cannot provide the exact context length), the UI gracefully falls back to the previous name-based heuristic. 
- **Max Input Limit Increase**: Increased the HTML input `max` attribute from `8192` to `100000` to support massive context length models (e.g., Qwen3.5-9b which supports up to 262K tokens, giving a recommendation of 32768 ~ 65536).
