---
id: 13
title: Fix residual launch flicker — paint-gated window reveal (white frame before dark splash)
date: 2026-06-12 02:00 KST
agent: Claude (Opus 4.8)
area: [ui, build, launch]
status: unverified
files:
  - application_build/app.py
supersedes: []
verified_by: |
  py_compile app.py -> OK. Visual (sub-second flash) NOT verifiable headlessly — needs the
  user to launch `uv run application_build/app.py` and confirm no white blink before splash.
---

# Fix residual launch flicker

## 🛠️ What was done
User still saw a brief blink on launch despite changes_7's `hidden=True` + styled/loaded
gate. Root-caused and changed the **reveal timing** so the window is shown only *after*
WKWebView composites its first frame. Single file: `application_build/app.py`.

## ⚙️ How it was done (Technical Details)
- **Root cause:** `window.events.loaded` fires at navigation-complete, which is *before*
  WKWebView paints/composites the first frame. The previous code called `window.show()`
  directly in the `loaded` handler (and in `_style_native_window`). On macOS WKWebView's
  default surface is white, so the window was revealed for ~1 frame as **white** before the
  **dark** splash (`#splash` is a `#1a2450→#0b0f20→#06080f` radial; window
  `background_color="#0b0f20"`) composited → the "한 번 짧게 깜빡" blink. (Not a theme
  mismatch — splash and window bg are both dark; it's a paint-timing gap.)
- **Fix:** Added one `_reveal_window()` helper (after `_menu_state`) that all reveal paths
  now route through. It (a) guards single execution via `_menu_state["shown"]`, (b) requires
  both `loaded` and `styled`, and (c) on darwin defers the actual `show()` by one main
  runloop tick — `AppHelper.callLater(0.08, w.show)` — so the dark splash is composited
  before the window becomes visible. Replaced the direct `window.show()` calls in
  `_on_loaded`, `_style_native_window`, and both `_bootstrap` fallback paths with
  `_reveal_window()`.
- ~80ms later reveal is imperceptible and removes the white first-frame.

## ✅ Verification (commands + observed output)
- `python3 -m py_compile application_build/app.py` → OK.
- **Visual: UNVERIFIED.** A <0.5s launch flash can't be observed via headless tooling. Needs
  user to run `uv run application_build/app.py` and confirm the window now appears already
  showing the dark splash with **no white blink**.

## ⚠️ Notes & Pending Issues
- If a blink still remains at +80ms, the next step is to stop WKWebView painting white at all:
  set the WKWebView's background (e.g. `inst.webview.setValue_forKey_(False, "drawsBackground")`
  or an opaque dark layer) — but that interacts with the transparent-titlebar styling in
  `_style_native_window` (`setOpaque_(False)` + `clearColor`), so it was avoided as the
  first, lowest-risk fix. Increase the `0.08` delay slightly if needed.
- Mirrors trap #15 (splash is session-gated + faster than tooling) — same reason the flash
  itself is hard to capture programmatically.
