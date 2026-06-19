---
id: 21
title: AI Popover Combo Box & Realtime Layout Fix
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Added a Combo Box (`<select>`) to the AI Popover to list and switch between locally installed LM Studio models.
- Fixed an overflow/layout issue in the Realtime Trading page where the right-side interface (Paper Trading) was getting clipped.

## How it was done
- **Backend `_llm_status` & `api_llm_load`**: 
  - Modified `_llm_status` to scan all available models using `lms ls --json` and return them as a `models` array along with the currently loaded state.
  - Modified `api_llm_load` to parse JSON payload `modelKey` to selectively load a user-chosen model via LM Studio instead of unconditionally using `_LLM_PREFERRED`.
- **Frontend `aiPop` render**:
  - Dynamically generate `<select id="aipCombo">` inside the popover from the `models` array.
  - Listen to `change` event on combo box to immediately reflect the selected model's Format/Quantization/Size info locally.
  - Ensure the "Load" toggle hits the new `/api/llm/load` with the explicitly chosen `modelKey`.
- **Realtime CSS Layout**:
  - `table-layout: fixed` and `white-space: nowrap; text-overflow: ellipsis; overflow: hidden;` applied to `.pos-table` and `.scr-table` first columns. This prevents unusually long stock names from ballooning their flex containers and causing page overflow.
  - `min-width: 0;` applied to `.main`, `.right-group`, `.col-left`, `.col-ob`, and `.col-paper` to ensure flex items correctly shrink below their content size instead of escaping viewport boundaries.

## Verification
- Verified `.main` and `.right-group` CSS changes visually resolve the bounding box clipping via syntax testing.
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` completed with no errors.

## Notes & Traps
- **Flexbox Minimum Width Trap**: Standard CSS flex items default to `min-width: auto;` meaning they will not shrink below the width of their content. When combined with tables using `white-space: nowrap`, this systematically guarantees layout clipping on narrow viewports. Always explicitly set `min-width: 0;` on flex children and `table-layout: fixed` on tables to restrict growth.
