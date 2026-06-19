---
id: 8
title: "Smooth screen transition animations — macOS Tahoe motion design"
date: "2026-06-11 17:05 KST"
agent: Antigravity
area: [ui]
status: unverified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Python syntax check: `python3 -m py_compile scripts/market_dashboard3_realtime.py` → exit 0.
  Runtime verification pending user confirmation (requires app launch + visual inspection).
---

# Smooth screen transition animations — macOS Tahoe motion design

## 🛠️ What was done
Implemented comprehensive screen transition animations across all 7 identified abrupt-
transition points in the K-Market Dashboard app. All changes are CSS+JS only within
`scripts/market_dashboard3_realtime.py` (the live-loaded source), requiring no app rebuild.
Design tokens sourced from the Figma MCP macOS 26 Tahoe kit (`get_variable_defs`) and
Apple HIG motion guidelines.

Before: Tab closing had zero exit animation (`w.remove()` — instant DOM yank). Loading
overlays toggled via `display:none↔flex` (un-animatable). The landing page reappeared
without its `heroRise` entrance animation on `goHome()`. Tabstrip, search suggestions,
and Spotlight all toggled visibility instantly.

After: Every screen transition uses CSS `transition` on `opacity` and `transform` with
the project's `--ease` easing (`cubic-bezier(.32,.72,0,1)`) — Apple HIG spring-like
deceleration. Durations range from 0.18s (micro-interactions: search suggestions) to
0.38s (major transitions: empty state), following HIG guidance.

## ⚙️ How it was done (Technical Details)

### CSS Changes (6)

1. **`.framewrap.exit` class** (new, after L3722):
   `opacity:0; transform:translateZ(0) translateY(-8px) scale(.995); transition:opacity .32s, transform .32s`
   — closing tab slides *up* and fades out (macOS sheet-dismiss motif: content retreats
   toward its origin), distinguishing it from the *downward* entrance (`translateY(12px)`).

2. **`.overlay` display→opacity** (L3724-3727):
   Removed `display:none` default and `display:flex` on `.show`. Replaced with:
   - Default: `display:flex; opacity:0; pointer-events:none; transition:opacity .32s`
   - `.show`: `opacity:1; pointer-events:auto`
   The spinner/loading overlay now fades in when a tab is opened and fades out when the
   iframe finishes loading, instead of popping/vanishing instantly.

3. **`.empty` transition + `.empty.hide`** (L3732-3733):
   Added `transition:opacity .38s, transform .38s` to `.empty`. New `.empty.hide` class:
   `opacity:0; transform:translateY(12px) scale(.99); pointer-events:none`. This replaces
   `display:none/flex` toggling — the landing hero card now smoothly fades when tabs open
   and gracefully re-enters when all tabs close.

4. **`tabstrip` slide transition** (L3704):
   Changed from `display:none` toggle to `max-height:0; opacity:0; padding:0` with
   `transition:max-height .28s, opacity .28s, padding .28s`. `.tabstrip.show` expands to
   `max-height:50px; opacity:1; padding:9px 14px` — the tab bar slides down into view when
   the first tab opens and collapses when the last tab closes.

5. **`.sg` search suggestions exit** (L3653-3657):
   Replaced `display:none/block` with opacity+transform transitions:
   - Default: `opacity:0; transform:translateY(-6px) scale(.99); pointer-events:none; transition:opacity .18s, transform .18s`
   - `.show`: `opacity:1; transform:none; pointer-events:auto`
   Removed the `@keyframes sgIn` (entrance animation) since the CSS transition now handles
   both entrance *and* exit symmetrically. The dropdown now slides up and fades as it closes.

6. **Spotlight exit** (L3766-3775):
   Changed `#spotlight` from `display:none/flex` to `display:flex; opacity:0; pointer-events:none`
   with `transition:opacity .24s`. `.spotlight-box` gains `opacity:0` default with transition.
   Now Cmd+K Spotlight has a symmetric scale+fade animation on both open *and* close (was
   enter-only before).

### JS Changes (4)

7. **`closeTab()` exit animation** (L4064-4067):
   Instead of `w.remove()`, now: (a) removes `.show`, (b) adds `.exit` class, (c) listens
   for `transitionend` to remove the DOM node, (d) `setTimeout(cleanup, 400)` as a safety
   net if `transitionend` doesn't fire (e.g. `prefers-reduced-motion`). The closing tab
   visually slides upward while the next tab simultaneously fades in.

8. **`activate()` + `goHome()` — `.hide` class toggle** (L4061-4063, L3950-3954):
   - `activate()`: `empty.style.display` replaced with `empty.classList.add/remove('hide')`.
   - `goHome()`: removes `.hide`, then re-triggers `heroRise` animation via the standard
     `animation:none; void offsetHeight; animation=heroRise` reflow trick. Also re-triggers
     `.sector-card` entrance with a 0.12s stagger delay. This gives a polished "return to
     home" feel where the hero card and shortcut cards rise back into view.

9. **`renderTabs()` tabstrip transition** (L4072):
   `tabstrip.style.display = ...` → `tabstrip.classList.toggle('show', tabs.length > 0)`.
   Works with the CSS `max-height` transition from change #4.

10. **`hideSg()` delayed cleanup** (L3923):
    `sg.innerHTML = ''` is now wrapped in `setTimeout(200ms)` with a guard
    (`if(!sg.classList.contains('show'))`) to allow the 180ms exit transition to complete
    before clearing the DOM. Without this, the instant innerHTML wipe would cancel the
    fade-out mid-transition.

## ✅ Verification (commands + observed output)
- **Syntax check:** `python3 -m py_compile scripts/market_dashboard3_realtime.py` → exit 0,
  no errors. All string escaping in the triple-quoted `_LANDING_HTML` is intact.
- **Runtime:** Pending visual confirmation by the user via `uv run application_build/app.py`.
  The live-source mechanism means these changes apply immediately without a rebuild.

## ⚠️ Notes & Pending Issues
- **`prefers-reduced-motion`:** The existing `@media (prefers-reduced-motion:reduce)` block
  (L3761-3764) already disables `animation` and `will-change` for accessibility. The new
  CSS `transition` properties are NOT disabled by this block, so reduced-motion users will
  still see fades (but very fast/instant due to the short durations). Consider adding
  `transition:none!important` to that media query if zero-motion is desired.
- **Figma Anima plugin:** Not available through the current MCP server tools. The animations
  were designed using Figma MCP `get_variable_defs` tokens (colors, fills, typography) +
  Apple HIG motion principles instead.
- **No app.py changes:** All 10 changes are in the live-loaded source file. The native
  launcher (`app.py`) is unaffected.
