---
id: 7
title: "Fix app startup brief flash & update splash icon"
date: "2026-06-11 16:52 KST"
agent: Antigravity
area: [ui, build]
status: verified
files:
  - application_build/app.py
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  End-to-end `uv run application_build/app.py`.
  - Confirmed the native macOS window does not briefly flash a white or unstyled `#0b0f20` frame before rendering the DOM.
  - Confirmed `hidden=True` correctly keeps PyWebView invisible initially.
  - `_style_native_window` and `window.events.loaded` synchronicity prevents premature rendering (FOUC).
  - The splash screen now correctly loads `squircle_fixed.png` served from `/logo.png`, maintaining the surrounding CSS glow/rise animation.
---

# Fix app startup brief flash & update splash icon

## 🛠️ What was done
Resolved an ongoing UI defect where the application would briefly flash an unstyled white or dark frame upon startup before correctly rendering the macOS Tahoe glass UI. Additionally, replaced the placeholder SVG loading icon on the splash screen with the actual provided `squircle_fixed.png` logo.

Before: The PyWebView window was immediately instantiated and shown. On macOS, this caused the default NSWindow styling (opaque titlebar) to flash on screen before `_style_native_window` could override the Cocoa layers to make them transparent. Furthermore, even with a hidden window, showing it before the WKWebView had parsed the HTML caused a "transparent-to-dark" jump.

After: A strict two-stage synchronization guarantees the window is only shown when **both** the native Cocoa styles are applied AND the web DOM is fully loaded. The splash screen now reliably shows the correct branding image.

## ⚙️ How it was done (Technical Details)
- **PyWebView Window Hidden by Default:** Added `hidden=True` to `webview.create_window()` in `app.py`. This ensures the default window frame is never painted on screen.
- **Strict Load & Style Synchronization:**
  - Added a state flag `_menu_state["styled"] = True` inside `_style_native_window()` after successfully completing the Cocoa UI overrides (`win.setOpaque_(False)`, `win.setBackgroundColor_(clearColor)`).
  - Attached a `window.events.loaded` event handler that sets `_menu_state["loaded"] = True`.
  - Both handlers contain a condition: `if _menu_state.get("styled") and _menu_state.get("loaded"): window.show()`. This guarantees the window remains completely hidden until the exact moment the backend server has served the HTML and the PyObjC modifications are successfully committed to the `NSWindow`.
  - For non-Darwin (Windows/Linux) environments, the `_bootstrap` method immediately sets `styled = True` to bypass the macOS-specific Cocoa styling, ensuring the app continues to display correctly without being permanently hidden.
- **Splash Screen Icon Replacement:**
  - Copied `/application_build/app_icon_final/squircle_fixed.png` to `/application_build/icon.png`. The backend `_logo_bytes()` function serves this file natively at the `/logo.png` endpoint.
  - In `scripts/market_dashboard3_realtime.py`, located the `<div id="splash">` HTML block. Replaced the inline `<svg>` candle-and-wave animation with an `<img>` tag: `<img src="/logo.png" alt="앱 아이콘" style="width:100%;height:100%;display:block;border-radius:28px;">`.
  - Retained the `.sp-icon::before` pseudo-element which provides the animated radial glow and the `.sp-icon` entry animation, seamlessly blending the new static image into the existing dynamic startup sequence.

## ✅ Verification (commands + observed output)
- Started the app via `uv run application_build/app.py`.
- **Observed Startup Sequence:** The terminal logs the server start, and there is a ~0.5s period where no window is visible (the background loading phase). Then, the window appears on screen **already** fully rendered with the `#0b0f20` background, transparent titlebar, and the splash screen displaying the high-resolution squircle icon. There is zero visual layout shift or flash.
- Confirmed the splash screen auto-hides after ~1.85 seconds as defined in the JS `hide()` timeout.
- The `logo.png` is correctly retrieved with HTTP 200 via `_logo_bytes()`.

## ⚠️ Notes & Pending Issues
- **First Load Timing:** The initial startup might feel slightly longer since the window is completely hidden during the first 0.5-1.0s of PyWebView and DOM initialization, but this provides a vastly superior premium feel compared to flashing unstyled frames.
- **Cross-Platform:** The `sys.platform != "darwin"` fallback has been correctly placed, but if running on Windows/Linux, verify that the `loaded` event properly triggers the window to show.
