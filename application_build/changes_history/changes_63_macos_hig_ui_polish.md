---
id: 8
title: macOS Tahoe HIG consistency polish (screener glass card, system colors, radii, easing)
date: 2026-06-11 18:35 KST
agent: Claude (Opus 4.8)
area: [ui, screener]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/.claude/launch.json
supersedes: []
verified_by: |
  Audited app UI vs official Figma "macOS Tahoe UI Kit" (fileKey a6AegNuDiPrlC5qdbXbn9R,
  via Figma MCP get_metadata/get_screenshot — duplicate holds only the Cover; exact tokens
  already in memory macos26-theme.md) + Apple HIG.
  Ran server on :8793 (uv) + Claude_Preview headless browser; observed:
    /screener_page (light): 41 rows, th textTransform=none (uppercase removed),
       up color rgb(255,59,48)=#FF3B30, table wrapped in glass .card (radius 16, blur 30).
    /screener_page (dark): document.body bg resolved to rgb(13,17,23)=#0d1117 (was the
       latent bug: transparent body over the iframe's white backing -> light text on white).
       Card rgba(28,30,38,.74), text #eef3ff — readable. Screenshot confirms.
    /sector (light): 23 rows, .list border-radius=16px (was 20px), up rgb(255,59,48),
       down rgb(46,117,182)=#2E75B6. Screenshot confirms grouped-list glass.
    /dashboard?q=005930 (report): builds OK, 26 cards, getComputedStyle(--ease)=
       cubic-bezier(.32,.72,0,1) in report context, glass theme intact. Screenshot confirms.
  py_compile -> COMPILE_OK.
---

> **이전 위치:** `changes_history/changes_8_macos_hig_ui_polish.md` (루트 디렉터리)  
> **통합일:** 2026-06-17 (재넘버링: changes_8 → changes_63)


# macOS Tahoe HIG consistency polish

## 🛠️ What was done
User asked to audit the whole app UI against the macOS UI guide (the Figma "macOS Tahoe
UI Kit") via the connected Figma MCP and refine the parts that don't match. Scope chosen by
the user = **targeted HIG-correctness polish** (fix genuine errors, preserve each page's
character) — *not* a full restyle of the Toss-style data pages.

The **landing page** was found already faithful to the kit (blur 50px/saturate 180%, system
blue #007AFF, radii pill100/glass26/lg16/md11, ease cubic-bezier(.32,.72,0,1), SF Pro scale,
Liquid Glass bevel) — left unchanged, used as the reference surface.

Four concrete deviations were corrected (all in `scripts/market_dashboard3_realtime.py`):

1. **Unified semantic up/down colors** to the system palette across the data pages. There
   were three different red/blue pairs. Now everywhere: up = `#FF3B30` (light) / `#FF453A`
   (dark), down = `#2E75B6` (light) / `#64B5FF` (dark) — matching the landing reference.
   - Screener `:root`/`html.dark` `--up/--down`; sector/market `--up/--dn`, the live-pulse
     dot (`#ff5470`→`#FF3B30` + pulse rgba), and `.obadge.buy/.sell` tints.
2. **Screener page** (the biggest fix):
   - Removed `text-transform:uppercase` + `letter-spacing` on `<th>` (HIG doesn't uppercase
     table headers).
   - Wrapped the previously bare table in a **macOS glass `.card`** (saturate180%/blur30px,
     .5px border, radius 16, grouped-list look) to match the sector/market surfaces.
   - Gave `<body>` an explicit themed `--bg` (`#f4f5f9`/`#0d1117`) instead of `transparent`.
     This also fixes a **latent dark-mode bug**: a transparent body sat over the iframe's
     hardcoded white backing (`.framewrap .frame{background:#fff}`), so dark mode rendered
     light text (#eef3ff) on white. Now the body paints its own dark surface.
   - JS: reveal the new `#tblCard` wrapper instead of the raw `#tbl`.
3. **Off-grid radii** on the sector/market pages: `.list` and `.ovcard` `20px`→`16px` (kit
   has 16 (lg) / 26 (glass); 20 was off-grid).
4. **Report glass easing**: `_FX_STYLE` used `cubic-bezier(.16,1,.3,1)` for card-hover /
   `header h1` / `nav .tab-btn` transitions. Added the kit `--ease:cubic-bezier(.32,.72,0,1)`
   to the injected `html{}` block and pointed those three transitions at `var(--ease)`.

Also added `application_build/.claude/launch.json` (preview MCP requires it in the cwd) so
the dashboard can be launched for headless visual verification on port 8793.

## ⚙️ How it was done (Technical Details)
- Figma MCP (`get_metadata`/`get_screenshot`) confirmed the duplicate file `a6AegNuDiPrlC5qdbXbn9R`
  contains only the "macOS Tahoe UI Kit — Apple Design Resources" Cover; the kit's component
  pages are not in the duplicate (community files are read-restricted until duplicated, per
  HANDOFF). The authoritative exact tokens were already extracted (Anima) into memory
  `macos26-theme.md`; those + Apple HIG were the audit yardstick.
- Verification used a Flask server (`MI_NO_OPEN=1 MI_NO_PREWARM=1 MARKET_PORT=8793 uv run`)
  + the Claude_Preview headless browser. A background `/__ping` loop every 2s kept the 15s
  auto-shutdown watchdog from killing the server during off-landing navigation (trap #8).
  Theme was toggled by setting `localStorage['kmkt-theme']` + the `.dark` class and reading
  back `getComputedStyle` values (the 0.4s bg transition means the first read can catch an
  interpolated value — re-read after it settles).

## ✅ Verification (commands + observed output)
See `verified_by`. Screenshots captured for: landing (light, reference), screener (light +
dark), sector (light), and the 005930 report (glass theme + `--ease` resolved). All four
edits observed in the live DOM (computed colors, radii, textTransform, body bg) and visually.
`py_compile` clean.

## ⚠️ Notes & Pending Issues
- **Scope was deliberately limited** (user choice): the sector/market/screener pages keep
  their heavier "Toss" type weights (800) and 14px body — those are character, not errors,
  and were explicitly out of scope. A full Tahoe conversion of those pages remains available
  as a follow-up (the "둘 다 / 전환" option the user did not pick).
- The screener `<th>` is no longer `position:sticky` (it conflicted with the new card's
  `overflow:hidden`). Fine for the ~40-row momentum list; revisit if the list grows long.
- Report up/down red/blue still come from the dashboard.py builder (`#c0392b`/`#2e75b6`,
  per root CLAUDE.md §11) — intentionally not touched (non-destructive injection boundary).
- Dataset is still the simulated/future one (삼성전자 301,000원, 1y +497%) — see changes_7;
  not a bug.
- `application_build/.claude/launch.json` was added for the preview workflow (port 8793).
