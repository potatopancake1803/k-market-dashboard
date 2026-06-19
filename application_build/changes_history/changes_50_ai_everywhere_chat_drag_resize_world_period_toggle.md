---
id: 50
title: AI ask on every screen + typing/markdown for all AI outputs; chat window drag+resize; world-card chart overflow fix + per-card period toggle
date: 2026-06-16 22:30 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **작업1 — AI 질문하기 on ALL screens + unified typing & markdown.**
  - Injected the floating "AI 질문하기" widget into the **landing/home screen** (`_LANDING_HTML`),
    scope `market`. It is auto-hidden whenever a tab iframe is open (`.framewrap.show` present) so
    the home FAB never doubles with the iframe's own FAB (MutationObserver on `document.body` class).
  - Made **every AI text output render markdown** (headers/bold/italic/lists/code) like the ask widget,
    and keep the **typing cursor** like backtest "AI 해석 보기":
    - Exposed the widget's markdown renderer globally as `window.kmktMd`.
    - Added a global `.kmkt-md` CSS block (unscoped, ships with the widget on every page) so AI output
      outside the chat bubble is styled too.
    - `streamLLM()` (macro + backtest, 2 copies) now accumulates the answer and re-renders
      `tc.innerHTML = md(ans)` with `class="kmkt-md"`; the existing `.ai-cur` cursor stays during stream.
    - Stock-report AI modal (`_AI_SCRIPT.startAI`) and overseas AI modal (`startAI` in `_OVERSEAS_HTML`)
      now accumulate `ansBuf` and render `textContainer.innerHTML = md(ansBuf)` (block display) with the
      blinking `#ai-cursor` retained.
    - Floating ask widget answer now appends a blinking `.kmkt-ai-cur` while streaming, removed on done.
- **작업2 — chat window drag + edge-resize.** In `_ASK_WIDGET_HTML` script:
  - Drag the window by its header (`.kmkt-ai-head`, `cursor:move`) to reposition.
  - Hover near any edge/corner → resize cursor (ns/ew/nwse/nesw) → drag to resize (8 directions),
    min 300×360, clamped to viewport. Manual move/resize sets `userPlaced` so window-resize and reopen
    no longer snap the window back to the FAB anchor.
- **작업3 — world (세계 시장) card charts.**
  - **Overflow fix:** `render()` now shows `#body` *before* `redrawSparks()` (previously charts were
    drawn while the container was `display:none` → 0-width → Plotly fell back to ~700px and spilled out
    of the card). Added `.icard{min-width:0;overflow:hidden}`, `.ispark{max-width:100%;overflow:hidden}`,
    Plotly `.plot-container/.svg-container{max-width:100%}`, and grid `minmax(min(420px,100%),1fr)`.
  - **Per-card period toggle:** each index card now has a 일/주/월 segmented control (`.csg`) in its header.
    New `loadCardSpark(i,period)` fetches `/api/world/spark?kind=&code=&period=` and redraws only that card;
    `bindSparkSegs()` wires the buttons. `kind=dom` for KR view (→ `_index_chart` D/W/M), else `index`
    (→ `_world_chart` day/week/month). New endpoint `GET /api/world/spark` returns last-60-bar OHLC arrays.

## How it was done
- Root cause of world overflow: draw-order bug — sparks rendered into hidden (0-width) containers.
- `window.kmktMd` is assigned inside the widget IIFE (`try{window.kmktMd=mdToHtml;}`); all other renderers
  fall back to a plain escaper if it's absent. The fallback avoids `\n` literals (uses
  `String.fromCharCode(10)`) so the same shared edit is valid in both raw (`r"""`) and non-raw page strings
  (trap #21/#25).
- Drag/resize uses pointer events with `setPointerCapture`; edge detection via `getBoundingClientRect`.

## Verification
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` → OK.
- Headless server (MARKET_PORT 8793/8794, with /__ping keepalive loop per trap #8):
  - `/world_page`, `/`, `/macro_page`, `/backtest_page`, `/overseas` all serve; `kmktAiFab` present on each
    (landing included); `kmkt-md` CSS present (11 refs/page).
  - `node --check` on every large inline `<script>` of world/landing/macro/backtest/overseas → 0 failures
    (validates widget drag/resize + markdown edits + world period-toggle JS).
  - `GET /api/world/spark?kind=dom&code=0001&period=week` → 60 weekly KOSPI closes.
  - `GET /api/world/spark?kind=index&code=.DJI&period=day` → 60 daily DJI closes.
- **Visual (drag/resize feel, typing cursor, markdown layout, world card chart fit) = unverified** — needs
  GUI. To verify: `uv run application_build/app.py`, open 세계 시장 (resize window narrow, confirm charts
  stay inside cards; toggle 일/주/월 per card), open AI 질문하기 (drag header, resize edges), ask a question
  (confirm markdown + blinking cursor), and check stock/overseas/macro/backtest AI outputs render markdown.

## Notes & Traps
- `.app` not rebuilt (token budget). Backend is loaded live via `app.py::_live_source()`, so a restart of
  the dev app reflects these changes without PyInstaller. A `cd application_build && ./build.sh` is still the
  protocol §23 follow-up before shipping a frozen bundle.
- Duplicate `.ai-cur` rule now exists (page-level `aiBlink` + widget-level `kmktAiBlink`); harmless — widget
  rule only overrides `animation`, width/height/colour still come from the page rule.
