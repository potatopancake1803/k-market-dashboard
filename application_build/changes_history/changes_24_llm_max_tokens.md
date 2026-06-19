---
id: 24
title: Fix LLM Max Tokens Cutoff
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **LLM Max Tokens Bug Fix**: `_LLM_MAX_TOKENS` was set to `400`, which was excessively short for generating Korean interpretations (especially for the lengthy Macro/ECOS prompts that require 6~8 sentences). This caused the model's generation to abruptly cut off mid-sentence (e.g., "따라서 지금식") and damaged the grammatical structure near the cutoff point. Increased `_LLM_MAX_TOKENS` from `400` to `1200`.
