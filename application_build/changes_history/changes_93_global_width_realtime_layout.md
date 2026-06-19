---
id: 93
title: Global page-width consistency (1200 centered) + realtime layout (Task6) + empty-space guideline
date: 2026-06-19 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/ui_templates.py
  - application_build/CLAUDE.md
  - memory/ui-design-standard.md
---

## What was done
Follow-up to session2 (changes_92), per user request: match every page's width/interface to the
domestic stock page, finish the realtime layout (Task6), and codify an empty-space check.

1. **Canonical page width on all main pages.** The domestic report `/dashboard` constrains content
   to `.pane{max-width:1200px;margin:0 auto}` (full-bleed page bg behind). Applied the same to:
   `_INDEX_HTML` (`#body{max-width:1200px;margin:0 auto}`) and — via a wrapper-free body rule —
   `_RESEARCH_HTML`, `_MACRO_HTML`, `_BACKTEST_HTML`, `_OVERSEAS_HTML`, `_WORLD_HTML`,
   `_REALTIME_HTML`: `body{padding-left/right:max(14px,calc((100% - 1200px)/2))}`. This centers the
   content at 1200 with side margins while the page background stays full-bleed (no wrapper div
   needed, works regardless of each page's internal structure).
2. **Task6 — realtime layout.** The 호가창|페이퍼 right group was horizontal and short, leaving a
   blank below. Changed `.right-group` to a **vertical stack** (`flex-direction:column;
   align-items:stretch`) with `.col-paper{flex:1 1 auto}` so the right column fills the left's
   height (no dead space). Widened the existing drag-resizer range (330–660 → **300–760**) and
   lowered `.col-left{min-width 240→200}` so the chart/체결/투자자 column can be dragged narrower.
3. **Guideline.** Added to `application_build/CLAUDE.md §10.2`: the canonical-width rule (every page
   = 1200 centered, full-bleed bg, never full-bleed content, match `/dashboard`) and a **mandatory
   no-dead-zone check** after any layout change (the realtime 호가창/페이퍼 case). Mirrored into
   memory `ui-design-standard.md`.

## How it was done
- Pure CSS in `scripts/ui_templates.py`. The 5 body-padding insertions were placed at each page's
  `</style>` by line (the macro/backtest CSS is byte-identical so string-matching was unsafe);
  realtime's rule + index's `#body` rule were edited by unique anchor.

## Verification
- `python3 -m py_compile scripts/ui_templates.py` OK; realtime `<script>` `node --check` OK.
- Asserted the width rule is present in all of `_RESEARCH/_MACRO/_BACKTEST/_OVERSEAS/_WORLD/_REALTIME`
  and `#body{max-width:1200px}` in `_INDEX`; realtime right-group is column-stacked, drag clamp 760.
- `uv run scripts/smoke_check.py --golden write` then plain → `SMOKE PASS ✓` (research/index/macro/
  backtest/realtime golden re-baselined — intentional).

## Notes & Traps
- **status: partial — visual confirmation pending (mandated by the new §10.2 check).** Headless can't
  see: the 1200 centering on each page, the realtime stacked/filled layout + drag feel. Run
  `uv run application_build/app.py` (or KMKT_DEV preview) to eyeball each page for dead zones/overflow.
- Width mechanism = body horizontal padding via `max(14px, calc((100%-1200px)/2))` — content centers,
  bg stays full-bleed (constraining `<body>`'s own max-width would have shown the iframe's white in
  dark mode — trap #12 — so padding, not max-width-on-body, is the correct tool).
- Not yet done (visual/broad follow-ups): embedded table sub-iframes (`/sector`,`/market`,`/screener`,
  `/world_detail`) width; making the index 지수 현재가 card pixel-match the domestic stock hero.
- `.app` rebuild needed to ship; live `uv run application_build/app.py` picks it up on restart.
