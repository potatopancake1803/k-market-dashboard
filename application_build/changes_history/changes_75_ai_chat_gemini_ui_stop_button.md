---
id: 75
title: AI chat — Gemini-style input bar (model popup, +, mic) + send→stop streaming control
date: 2026-06-17 18:50 KST
agent: Claude (Opus 4.8)
area: [ui, ai]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
Redesigned the floating AI chat widget (`_ASK_WIDGET_HTML`) input area to match the
provided Gemini desktop-app reference, and made the send button double as a **stop**
button while a reply is streaming. Both changes are live-source → **no rebuild needed**.

### 1) Send → Stop toggle (user request 1)
- `ask()` now creates an `AbortController` and passes `signal` to the `/api/llm_ask` fetch.
- New `setSending(on)`: while streaming the send button gets `.stop` (dark circle, `■`,
  `aria-label="중지"`) and stays **clickable** (no longer `disabled`). Click handler is now
  `if(busy)stopGen();else ask();`.
- `stopGen()` aborts the controller. The reader's `read()` rejects `AbortError` →
  caught and finalized gracefully: the **partial answer is preserved** + a small
  `⏹ 중지됨` marker is appended; convo memory keeps the partial turn.
- Closing the window mid-stream (`closeWin`) now also calls `stopGen()`.

### 2) Gemini-style input bar (user request 2 — greeting intentionally omitted per user)
- Replaced the old 3-row footer (ctx `<details>` + provider segmented control + Gemini
  `<select>` + think label + input row) with a single rounded **capsule bar** (`.kmkt-ai-bar`):
  `[ + ]  textarea  [ model chip ▾ ]  [ 🎤 ]  [ ↑/■ ]`.
- **Model chip** (`#kmktAiModel`, shows e.g. "로컬" / "3.5 Flash") opens a **popup menu**
  (`#kmktAiMenu`, Gemini-style: title + subtitle + ✓ per row): 로컬 LLM · 3.5/2.5/2.5-Lite/
  3.1-Lite Flash, a divider, then **심층 추론** toggle (the old `#kmktAiThink` checkbox, now
  living inside the menu). Outside-click closes via `mousedown` (trap #4).
- **`+` button** toggles the "참고 데이터 / 지시사항" textarea panel (replaces the old
  `<details>`); rotates 45° + turns blue when open.
- **🎤 mic**: Web Speech (`webkitSpeechRecognition`, ko-KR) dictation into the input;
  **hidden when unsupported** so there is never a dead button.
- Provider/model state still persists in the SAME localStorage keys
  (`kmkt-ai-prov`/`kmkt-ai-gmodel`) → the landing AI control button and all other AI
  features (`window.kmktAiProv()`) stay in sync. `setModel()` also calls
  `window.__kmktAiBtnSync()` so the landing ✨AI label updates immediately.
- Removed now-dead ids/classes: `#kmktAiProv` (seg), `#kmktAiGModel` (select),
  `#kmktAiCtxD`, `.kmkt-ai-inrow`, `.kmkt-ai-seg`, `.kmkt-ai-opts`, `.kmkt-ai-gmodel`.
  Confirmed none are referenced elsewhere (other code reads localStorage, not the DOM).
- Light + dark both styled (`.kmkt-ai-dark` overrides for bar/menu/chip/mic).

## Verification (Preview MCP, live backend on :8781, landing widget)
- Markup: `kmktAiPlus/kmktAiModel/kmktAiMic/kmktAiMenu/kmktAiThink/kmktAiSend` each ×1;
  old `kmktAiProv`/`kmktAiGModel`/`kmkt-ai-inrow` = 0. `node --check` on extracted script OK.
- **Visual (screenshots):** capsule bar renders (`+ | input | 로컬 ▾ | 🎤 | ↑`); model popup
  renders Gemini-style with ✓ on 로컬 LLM and 심층 추론 toggle; **dark mode** popup + window
  render correctly (light text, blue ✓).
- **Stop flow (stubbed slow stream + AbortError):** during stream send shows `■`
  (`class="kmkt-ai-send stop"`, `aria-label="중지"`); clicking it → reverts to `↑`, partial
  text kept, `⏹ 중지됨` marker shown (`stoppedMarker:true, partialKept:true, sendReverted:true`).
- Console: no errors.

## Notes & Traps
- Mic uses Web Speech; in WKWebView (the packaged app) `webkitSpeechRecognition` may be
  absent → the mic button auto-hides (graceful). It worked in the Chromium preview.
- The think/reasoning toggle id `#kmktAiThink` was intentionally preserved (just relocated
  into the menu) so the `think` request param still flows to `_llm_stream` unchanged.
- Visual verified in browser preview (Chromium). The packaged `.app` (WKWebView) visual is
  the same live source but not separately screenshotted this session.
