---
id: 25
title: Add UI Control for LLM Max Tokens
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **Max Tokens UI Control**: Added an interactive text field (number input) inside the AI popover (로컬 AI 모델) to manually override the `max_tokens` value.
- **Recommended Range Logic**: Dynamically displays a recommended token range (`Recommended`) based on the currently selected model (e.g., `qwen` models display `1024 ~ 4096`, while others display `512 ~ 2048`).
- **Fetch Logic Plumbing**: Plumbed the user-defined token value (`window._llmMaxTokens`) down through the JS `streamLLM` fetch payloads to dynamically adjust generation length at the `api/llm_commentary` backend endpoint.
