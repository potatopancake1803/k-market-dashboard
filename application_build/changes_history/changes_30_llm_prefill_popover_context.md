---
id: 30
title: Reasoning LLM fixed via Assistant-Prefill; AI popover stays open on Load + per-model context recognition
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/CLAUDE.md
---

## What was done
- **작업1 — reasoning models now return clean answers (Assistant Prefilling).** Per the user's
  research note (`qwen_thinking.md`), the only reliable way to bypass qwen3.5's forced thinking is
  to **prefill an empty think block**. Reasoning models now produce a fast, clean answer instead of
  burning the whole budget on `reasoning_content`.
- **작업2a — AI popover no longer closes when you click Load** (or pick a model in the combo).
- **작업2b — per-model context recognition.** The popover now actively reads each model's max /
  loaded context and sets the default **Max Tokens** and a recommended context range per model.

## How it was done
### Assistant Prefilling (`scripts/market_dashboard3_realtime.py`)
- `_llm_model_profile()` now returns a `prefill` field. For reasoning models it is
  `"<think>\n\n</think>"`; for instruct/gemma it is `None`. Reasoning `max_tokens` dropped back to the
  normal `_LLM_MAX_TOKENS` (1200) and temp 0.5 (prefill removes the need for a big budget).
- `/api/llm_commentary` builds `_messages` and, when `prof["prefill"]` is set, appends
  `{"role":"assistant","content":prof["prefill"]}` as the last message.
- The stream loop strips a leading `\n`/`</think>` from the **first** content chunk (prefill can leave
  residual whitespace). The dim "💭 추론" stream + Instruct end-note remain as a safety net.

### Popover stays open (`_aiPop` IIFE)
- Root cause: the outside-click-to-close listener was on `document` **click**. Clicking Load/combo
  triggers `render()` which replaces `pop.innerHTML`; by the time the `click` bubbles to `document`,
  `e.target` (the old button) is detached, so `!pop.contains(e.target)` is true → it closed the popover.
- Fix: bind the close detection to **`mousedown`** instead. `mousedown` fires before the re-render, so
  containment is evaluated against the live DOM. Outside clicks still close; Escape still closes.

### Per-model context (`_llm_status` + popover render)
- `_llm_status()`: the `lms ls` pass records `max_ctx` (from `maxContextLength`); the `/api/v0/models`
  pass records `loaded_ctx` (`loaded_context_length`). A final loop adds per-model `kind`
  (via `_llm_model_profile`), `def_tokens` and `rec_ctx_lo/hi`:
  `eff = loaded_ctx or min(max_ctx, 32768)`; `def_tokens = clamp(max(profile_tokens, eff//4), 512, 4096)`;
  `rec = eff//8 ~ eff//4`.
- Popover render: new **Max Context** row (`256K · 로드 8K`), Recommended uses `rec_ctx_lo/hi`, and the
  Max Tokens input defaults to the model's `def_tokens`. An `aipTokModel` guard re-applies the default
  only when the selected model changes (a manual Max Tokens edit is preserved otherwise).

## Verification
- **Prefill, direct LM Studio:** `<think>\n\n</think>` prefill on qwen3.5-9b →
  first 1.7s, **content 754, reason 0, finish=stop**; `</think>` → 591, finish=stop.
- **Prefill, live SSE** (`MARKET_PORT=8797`, ping keepalive, `mode=macro`, 9b loaded):
  `first=2.2s answer_chars=529 reason_chars=0 endnote=False total=9.9s`, answer head cleanly trimmed
  ("현재 기준금리가…"). No more blank / endless-reasoning.
- **Status fields** (`GET /api/llm/status`, live): qwen3.5-9b → `kind=reasoning, max_ctx=262144,
  loaded_ctx=8192, def_tokens=2048, rec=1024–2048`; gemma/4b (unloaded) → `def_tokens=4096, rec=4096–8192`.
- **Landing JS** (`curl /`): `addEventListener('mousedown'` ×3, `aipTokModel` ×2, `Max Context` ×1.
- `python3 -m py_compile` clean.
- **Status = `partial`:** prefill (SSE end-to-end), status fields, and JS presence were *observed*.
  The popover *staying open on Load* and the Max Context display are logic-/served-JS-verified only —
  not yet observed in a real browser session (would require triggering an actual `lms load`).
  To confirm: run `uv run application_build/app.py`, click AI ▸ pick a model ▸ Load, and verify the
  popover stays open and shows "Max Context".

## Notes & Traps
- `_STATUS.md` trap #19 updated to record the prefill solution (supersedes the changes_29 "cap+endnote"
  mitigation, which is now only a safety net).
- The popover model list still includes the embedding model (`text-embedding-…`); selecting it for
  commentary would fail. Out of scope here — could be filtered later (it is harmless for load/unload).
- Web-level change (live via `_live_source()`); **`.app` rebuild still pending** per §23 (user deferred
  in this session). Popover open/close + Max Context display are visual — confirm in the real app.
