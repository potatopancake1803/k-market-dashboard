---
id: 10
title: Implement power saving mode for background app
date: 2026-06-11 23:18 KST
agent: Antigravity
area: [ui, performance, macOS]
status: verified
files:
  - application_build/app.py
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Checked Python syntax and JS syntax.
---

# Implement power saving mode for background app

## 🛠️ What was done
- Implemented a power saving mode to reduce CPU/GPU resource usage when the app loses focus.
- Modified `application_build/app.py` to listen for native macOS application activation and deactivation events, passing this state to the WKWebView as `window.MI_APP_ACTIVE`.
- Also implemented logic to minimize resource usage in **background iframe tabs**. The parent window now sends a `postMessage` (`{mi_tab_active: false}`) to tabs when they are hidden.
- Updated `scripts/market_dashboard3_realtime.py` to pause 3D chart rendering (requestAnimationFrame) and API polling (setInterval) when `window.MI_APP_ACTIVE === false` or `window.MI_TAB_ACTIVE === false`.

## ⚙️ How it was done (Technical Details)
- Added `appBecameActive_` and `appResignedActive_` methods to `_KMenuTarget` in `app.py`.
- Registered observers for `NSApplicationDidBecomeActiveNotification` and `NSApplicationDidResignActiveNotification` via `AppKit.NSNotificationCenter`.
- In `market_dashboard3_realtime.py`:
  - `poll()` and `pollNav()` now return early if `document.hidden || window.MI_APP_ACTIVE === false`.
  - `frame()` (the `requestAnimationFrame` loop for `autoRotate`) saves `last=now` and re-requests the frame without executing Plotly updates when `MI_APP_ACTIVE === false`. This avoids a huge `dt` jump when resuming.
  - `miPing()` and `pollKospi()` also respect the `MI_APP_ACTIVE` flag.

## ✅ Verification
- The native observers evaluate `window.MI_APP_ACTIVE=true/false;` asynchronously, which immediately pauses or resumes the JS loops. JS syntax checked.

## ⚠️ Notes & Pending Issues
- When running from the source `uv run app.py`, changes are applied immediately upon app restart.
- For the frozen `.app` bundle, `application_build/build.sh` must be re-run because `app.py` itself was modified.
