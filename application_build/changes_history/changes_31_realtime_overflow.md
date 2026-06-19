---
id: 31
title: Fix realtime page right-edge overflow (paper/grid columns) + overflow guideline
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/CLAUDE.md
---

## What was done
- **작업1:** Realtime page (`/realtime_page`) rightmost card (페이퍼 트레이딩) spilled past the viewport.
- Added an overflow-guard CSS block + strengthened CLAUDE.md §10.2 to mandate the fix pattern.

## How it was done
- Root cause: `.paper-tiles` / `.lower-row` used `grid-template-columns:1fr 1fr`. Grid items default to
  `min-width:auto`, so a long unbreakable number (cash, P&L, qty in `.ptile .pv`) can't shrink below its
  content width → the column (and card) overflow the container → clipped at the viewport right edge.
- Fix (end of `_REALTIME_HTML` `<style>`, wins source order): `min-width:0` on
  `.main/.col-left/.right-group/.col-ob/.col-paper/.ptile`; `minmax(0,1fr)` tracks for
  `.lower-row/.paper-tiles`; `max-width:100%;overflow:hidden` on the cards; `.ptile .pv` nowrap+ellipsis.

## Verification
- `python3 -m py_compile` clean.
- **status=partial:** preview/Chrome MCP not connected this session → no live visual confirm. The fix is the
  canonical flex/grid-overflow remedy (high confidence). To confirm: `uv run application_build/app.py` →
  📡 실시간 → check the 페이퍼 트레이딩 card no longer spills at the right edge (try a large cash value).

## Notes & Traps
- Guideline §10.2 now spells out the `min-width:0` + `minmax(0,1fr)` + ellipsis rule for all data flex/grids.
- Web-level (live via `_live_source()`); `.app` rebuild deferred (user).
