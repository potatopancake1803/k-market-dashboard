---
id: 60
title: Render report AI-summary as markdown (+ guideline §11.9); heat reduction — pause full-screen wallpaper animation when idle + adaptive KOSPI polling
date: 2026-06-16 07:20 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/CLAUDE.md
---

## 작업1 — AI 답변 마크다운 렌더 (raw 잔존 제거 + 기본 지침화)
- Audited every AI output renderer. All already render the answer via `md()`/`window.kmktMd` (`.kmkt-md`)
  **except the report list "✨ AI 요약"** (`/research_page` `summarize`), which used `e2()` (escape+`<br>`) for the
  answer → raw `**`/`#`/`*` shown. Fixed: answer now accumulates `ansBuf` and renders `st.innerHTML=md(ansBuf)`
  with `st.className='kmkt-md'`. (Reasoning box stays dim plain — correct.) The research page already injects
  `_ASK_WIDGET_HTML` (provides `window.kmktMd` + `.kmkt-md` CSS), so it renders properly.
- **Guideline:** added `application_build/CLAUDE.md` §11.9 — all AI *answer* text MUST render through the shared
  markdown renderer (`.kmkt-md` + `window.kmktMd`); reasoning boxes may stay plain; copy the `md(ansBuf)` pattern.

## 작업2 — 발열/연산 낭비 점검 + 수정
- **Full-screen wallpaper animation ran 24/7 (biggest idle-heat driver).** `body::before` AND `body::after` are
  fixed full-viewport layers with `animation: wpdrift 42s …, wphue 72s linear infinite` + permanent
  `will-change:transform,filter,opacity` → continuous **hue-rotate compositing** on two GPU layers regardless of
  activity, and it had **no `prefers-reduced-motion` guard**. Fixes:
  - `body.kmkt-bg-off::before/::after{animation-play-state:paused!important}` + a top-frame JS sync
    (`visibilitychange` + 3s poll of `MI_APP_ACTIVE`) → animation **pauses when the app is hidden/inactive**.
  - `@media (prefers-reduced-motion:reduce){body::before,body::after{animation:none;will-change:auto}}`.
- **KOSPI ticker polled `/api/index` every 2s forever on the always-present top bar, unguarded.** It hammered the
  API every 2s even when the tab was hidden/app inactive and even when the market was **closed** (static "종가"
  data most of the day). Replaced `setInterval(pollKospi,2000)` with an **adaptive self-scheduling loop**: skip
  when `document.hidden||MI_APP_ACTIVE===false` (re-poll 20s), **30s when market closed**, 2s only when open;
  immediate re-poll on `visibilitychange`. (`window.__ktClosed` set from the phase in the poll response.)
- Reviewed other loops: report-tab `poll`/`pollNav` (`/api/realtime`,`/api/etf_nav`) already guard
  `document.hidden`+`MI_APP_ACTIVE`+`MI_TAB_ACTIVE` (active tab only) → left as-is. Other infinite CSS animations
  are on transient elements (loaders, splash, streaming cursors) → no idle cost.

## Verification
- `python3 -m py_compile` → PY OK. Landing biggest inline `<script>` (34,196 chars) → `node --check` OK.
- Headless (MARKET_PORT 8788): `/` contains `kmkt-bg-off`, `ktTick`, `bgSync`, `prefers-reduced-motion`;
  `/research_page` has `.kmkt-md` + `window.kmktMd` (markdown fix renders). 0 server tracebacks.
- **Visual/thermal (wallpaper actually pauses on blur, markdown layout) = unverified** — needs GUI/app run.

## Notes & Traps
- `MI_APP_ACTIVE` is set by the native wrapper (`app.py`), read-only in the page; the bg pause also keys off
  `document.hidden` so it works even in pure-browser use.
- 작업3 (앱 전역 디자인 일관성 통합) is NOT in this entry — it's a larger dedicated pass (see session notes).
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
