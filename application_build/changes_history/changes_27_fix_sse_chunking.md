---
id: 27
title: Fix SSE Chunking Data Loss in AI Stream
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **SSE Stream Data Loss Bug Fix**: Fixed a critical bug in the JavaScript `streamLLM` function where the AI's generated text would randomly drop characters, words, or entire phrases, resulting in completely broken grammar (e.g. "한국 경가 조금하고", "앞으로할지", "투들이 장식에"). 
- **Root Cause**: The `fetch` stream reader chunk boundaries do not always align perfectly with the SSE `\n` line boundaries. When a network chunk split a `data: {...}` line in half, `JSON.parse` failed silently and the tokens in that chunk were permanently lost. 
- **Solution**: Implemented a string buffer accumulator (`buf`) in both `streamLLM` definitions to hold incomplete string chunks across `reader.read()` iterations. The incomplete tail of the stream is now popped off and safely carried over to the next loop, ensuring 100% token integrity.
