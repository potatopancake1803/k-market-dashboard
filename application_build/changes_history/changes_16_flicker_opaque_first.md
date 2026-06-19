---
id: 16
title: Launch flicker — real fix (reveal opaque-dark first, defer glass transparency)
date: 2026-06-12 02:45 KST
agent: Claude (Opus 4.8)
area: [ui, build, launch]
status: unverified
files:
  - application_build/app.py
supersedes: [13]
verified_by: |
  py_compile app.py -> OK. Visual confirmation still required (sub-second flash, not
  observable headlessly): run `uv run application_build/app.py` and confirm no blink.
---

# Launch flicker — real fix

## 🛠️ What was done
changes_13's 80ms reveal delay did **not** remove the blink (user confirmed it persists).
Found the actual cause and fixed it in `application_build/app.py`.

## ⚙️ How it was done (Technical Details)
- **Root cause (corrected from changes_13):** `_style_native_window()` applied the glass
  effect — ④ `webview.setValue_forKey_(False,"drawsBackground")` + ⑤ `win.setOpaque_(False)`
  + `setBackgroundColor_(clearColor)` — **before** the window was shown. So the window was
  already *transparent* at `show()`; before the dark splash painted its first frame, the
  transparent window briefly revealed the **desktop** behind it → that's the "blink" (it
  wasn't a white WKWebView frame, and the 80ms delay didn't help because the window was
  transparent regardless of when it was shown).
- **Fix:** split the transparency out into a new `_apply_glass_transparency()` and run it
  **0.3s after the window is revealed**. The structural titlebar steps (FullSizeContentView,
  transparent titlebar, hide title, remove toolbar/separator) still run before show — they
  don't cause bleed because the window stays **opaque with its dark `background_color`
  (#0b0f20)**. So the first visible frame is solid dark (matching the dark splash) → no
  desktop bleed, no blink. The later opaque→transparent switch is dark→dark, imperceptible.
- Kept `_reveal_window()` (changes_13) as the single gated reveal path; added the deferred
  `AppHelper.callLater(0.3, _apply_glass_transparency)` right after reveal.

## ✅ Verification (commands + observed output)
- `python3 -m py_compile application_build/app.py` → OK.
- **Visual: UNVERIFIED** — needs the user to relaunch and confirm the blink is gone.

## ⚠️ Notes & Pending Issues
- If a blink still remains, next levers: increase the 0.3s defer; or keep the window
  permanently opaque-dark (drop the clearColor transparency) and achieve rounded corners via
  a different route. But opaque-dark-first is the principled fix for the observed
  desktop-bleed mechanism.
- The rounded-titlebar glass look now appears ~0.3s after launch instead of instantly; this
  is during the dark splash, so it should be unnoticeable.
