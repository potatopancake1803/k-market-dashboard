---
id: 57
title: AI popover — local/Gemini provider toggle + Gemini model picker + custom system-prompt textarea; route AI 요약·해석·코멘터리 to Gemini; AI button label Local/Gemini
date: 2026-06-16 05:10 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
Previously the "AI 요약 / AI 해석 / 코멘터리" features were **local-LLM only**. Now they can run on Gemini,
selected from the ✨ AI popover (`#aiPop`).
- **Provider toggle (top of popover):** macOS segmented control `로컬 LLM | Gemini` (`.aip-seg`, `#aipProv`).
- **Gemini model picker:** when Gemini is active, a `<select>` (`#aipGModel`) with the free-tier catalog
  (3.5 Flash / 2.5 Flash / 2.5 Flash-Lite / 3.1 Flash-Lite), same set as the chat widget.
- **Custom system-prompt textarea (bottom):** `#aipGsys` — user writes extra instructions appended to the
  system prompt for every Gemini run ("[사용자 추가 지시]").
- **Shared state:** popover persists to localStorage `kmkt-ai-prov`/`kmkt-ai-gmodel`/`kmkt-ai-gsys` — the SAME
  keys the floating chat widget uses, so the provider choice is unified across ALL AI surfaces. Exposed a
  global `window.kmktAiProv()` (in `_ASK_WIDGET_HTML`) returning `{provider,gemini_model,gsys}`.
- **Backend routing:** `/api/llm_commentary` and `/api/research_summary` now accept `provider`/`gemini_model`/
  `gsys`; when `provider=gemini` they build `sys_msg + "[사용자 추가 지시]\n"+gsys` and stream via
  `_gemini_stream(use_search=False)` (grounded in the injected data; no quota burn). `research_summary` uses a new
  inner `_synth()` helper covering both its market-brief and report-summary streams.
- **Call sites wired:** stock-report `startAI`, overseas `startAI`, macro/backtest `streamLLM` (both copies),
  research `summarize` all merge `window.kmktAiProv()` into their request (POST body or GET query).
- **AI button label:** `✨ <span id="aiLbl">` now reads **"Local"** when a local model is loaded, **"Gemini"**
  when Gemini is the selected provider, else "AI". Driven by the dot-poll IIFE (`window.__kmktAiBtnSync`), which
  the popover calls on every provider switch.

## Design / Figma (§10.7 gate)
- Figma dev-mode MCP **confirmed connected** (whoami → user MJ, team "정민준의 팀"). The macOS 15 UI Kit
  (fileKey `a6AegNuDiPrlC5qdbXbn9R`) opens but only exposes a "Cover" frame via the API and
  `search_design_system` returns empty for it, so the canonical macOS tokens used are those already extracted
  from this kit (memory `macos26-theme.md`) + the app's existing Figma-aligned chat-widget controls. New CSS
  uses systemBlue `#007AFF`, segmented control matching `.kmkt-ai-seg`, radii 9/10/16, ease
  `cubic-bezier(.32,.72,0,1)`, focus ring `rgba(0,122,255,.2)`.

## Verification
- `python3 -m py_compile` → PY OK. Landing biggest inline `<script>` (33,578 chars) → `node --check` **OK**.
- Headless (MARKET_PORT 8796, /__ping keepalive, single invocation):
  - `GET /` contains `aipProv`, `aip-seg`, `geminiPanel`, `aipGsys`, `id="aiLbl"`, `__kmktAiBtnSync`,
    `window.kmktAiProv` — all present. ✅
  - `POST /api/llm_commentary {code:005930, provider:gemini, gemini_model:gemini-2.5-flash, gsys:"한 문장으로만
    답해줘"}` → **one-sentence Gemini answer** ("강한 상승 모멘텀을 지속하는 삼성전자는…") → custom system
    prompt honored. ✅
  - `GET /api/research_summary?...&provider=gemini&gemini_model=gemini-2.5-flash&gsys=두 줄로 요약` → real
    Gemini report summary (①결론 구조). ✅
  - Server tracebacks: 0.
- **Visual (popover toggle look, dropdown, textarea, button label swap, dark mode) = unverified** — needs GUI.
  Verify via `uv run application_build/app.py`: open ✨ AI popover → toggle 로컬/Gemini (model select + system-prompt
  box appear under Gemini), type a system prompt, run an AI 요약/코멘터리 and confirm Gemini answers per the prompt;
  confirm button reads "Local" (model loaded) / "Gemini" (Gemini selected).

## Notes & Traps
- Provider choice is now **global** across chat widget + popover (same localStorage keys) — intentional unification.
- Commentary/summary Gemini path uses `use_search=False` (data already injected) → no grounding 429 risk.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
