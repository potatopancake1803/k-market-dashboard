---
id: 9
title: App launch splash screen (logo-concept animated SVG, macOS 26 motion)
date: 2026-06-11 19:20 KST
agent: Claude (Opus 4.8)
area: [ui]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Ran server :8793 (uv) + Claude_Preview headless browser.
  - Injected the exact splash markup as a static clone (inserted <script> doesn't execute,
    so no auto-hide) and screenshotted: dark squircle + 3 glowing candlesticks (cyan/violet/
    orange) over neon waves + glow aura + "K-Market Dashboard" wordmark (rgb(234,240,255)) +
    "🚀 M4 PRO · PRO QUANT" badge + gradient progress shimmer. Matches icon.png concept.
  - Real load lifecycle: after a normal page load, sessionStorage['kmkt_splash']==="1" and
    #splash no longer in DOM (readyState complete) -> controller showed then auto-hid+removed
    it. Subsequent same-session loads gate it off immediately.
  - Landing underneath renders intact after splash removal (screenshot, no residue).
  - py_compile -> COMPILE_OK.
---

> **이전 위치:** `changes_history/changes_9_app_launch_splash.md` (루트 디렉터리)  
> **통합일:** 2026-06-17 (재넘버링: changes_9 → changes_64)


# App launch splash screen

## 🛠️ What was done
Added a first-launch **loading/splash screen** themed on the app logo, with smooth macOS-26
motion. It lives entirely in `_LANDING_HTML` (the live source) — the WKWebView's first painted
document — so it appears on the next app launch **with no rebuild**, and there's no white
flash (its dark-navy backdrop continues `app.py`'s `background_color="#0b0f20"`).

## ⚙️ How it was done (Technical Details)
- **Concept = the app icon** (`application_build/icon.png` = `/logo.png`): a dark squircle with
  three glowing candlesticks (cyan/violet/orange) over flowing neon waves. Recreated as an
  **inline animated SVG** (not the raster PNG) so each element animates:
  - candlesticks **grow** from the baseline (`transform:scaleY(0→1)`, `transform-box:fill-box`,
    staggered 0.15/0.30/0.45s), wicks **draw in** (`stroke-dashoffset`, `pathLength="100"`),
    waves **draw** then gently **drift**; the icon **rises+unblurs** in and softly **bobs**,
    with a pulsing radial **glow aura** (`::before`).
  - wordmark + "M4 PRO · PRO QUANT" badge fade up; an indeterminate **gradient shimmer bar**.
  - Whole overlay exits with `opacity→0 + scale(1.045) + blur(9px)` over .7s, then is removed.
- **Grounded in the Figma macOS 26 tokens** (memory `macos26-theme.md`): kit ease
  `--ease:cubic-bezier(.32,.72,0,1)`, M4 palette (cyan #36c6ff, violet #9b6bff, ink #eaf0ff,
  navy #0b0f20). Motion hand-built (the documented project lesson: Anima is a one-way
  Figma→React/Tailwind exporter and there is no Anima MCP endpoint, so it can't port into this
  Flask/CSS app — see `macos26-theme.md`).
- **Controller** (inline script right after `<body>`): shows once per WebView session via
  `sessionStorage['kmkt_splash']`; on `window.load` (or immediately if already complete) waits
  out a **min display** (1850ms; 260ms under reduced-motion) so the entrance animation reads,
  then hides+removes. A 6s safety timer force-removes it no matter what. Full
  `prefers-reduced-motion` guard (no animations, dashoffset 0).
- No `app.py` change needed — the splash is web-level, inside the live-loaded source.

## ✅ Verification (commands + observed output)
See `verified_by`. Screenshot of the splash (settled hero state) + screenshot of the intact
landing after removal; sessionStorage flag + DOM-absence prove the show→hide→remove lifecycle
on a real load; `py_compile` clean. (The headless eval round-trip is slower than the 1.85s
display, so the live splash was captured by re-injecting the exact markup as a non-scripted
clone — the CSS/markup under test is identical to what ships.)

## ⚠️ Notes & Pending Issues
- **Session-gated**: shows on app process launch (fresh WebView session), not on in-session
  Cmd+R / navigation. To replay during testing: `sessionStorage.removeItem('kmkt_splash')`.
- Splash is **always dark** (brand launch screen), independent of light/dark theme — matches
  the window backdrop and the logo. Intentional.
- Not yet observed inside the actual packaged `.app` window this session (verified in the
  WKWebView-equivalent preview browser); behavior should be identical since `app.py` loads the
  same live source and sets the matching `background_color`.
- Optional follow-up the user may want: push this splash into Figma as an artboard via the
  Figma MCP (`use_figma`, code→design) for a design record — not done unless requested.
