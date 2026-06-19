---
id: 28
title: Fix Qwen Reasoning Token Drop & Add Model Specific Prompts
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **Reasoning Token Parsing Fix**: Identified that the "no output" issue was specific to reasoning models like Qwen 3.5. These models emit their initial thought process in `delta.reasoning_content` rather than `delta.content`. The backend was ignoring `reasoning_content`, causing it to output nothing for tens of seconds while the model was thinking, often leading to timeouts or truncated outputs. Modified the Python backend stream parser to capture and yield `reasoning_content` seamlessly alongside normal `content`, allowing the UI to display the AI's real-time thinking process.
- **Model-Specific Prompt Injection**: Fulfilled the requirement to adjust the prompt based on the loaded model's specifications:
  - If the model is **Qwen** (reasoning-heavy), it dynamically appends instructions to think deeply and provide rich logical answers.
  - If the model is **Gemma** (instruction-tuned, sometimes prone to rambling), it dynamically appends instructions to be extremely concise and to the point.
