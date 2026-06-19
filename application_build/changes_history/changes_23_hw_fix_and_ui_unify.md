---
id: 23
title: Fix HW Stats 0.0 Bug & Unify UI to Mac Style
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
1. **HW Stats Bug Fix**: Fixed an issue where the RAM/CPU usage always showed 0.0. The `uv` environment lacked the `psutil` package that was installed globally. Implemented a rock-solid, zero-dependency native macOS fallback using `subprocess.check_output` and `ps -ax` to reliably fetch process stats without dependency issues.
2. **Mac Style UI Unification**: Adjusted the Combo Box and Hardware Badges to match the larger, chunkier Mac-like style of the `Unload` button. Unified `border-radius`, `font-size`, padding, and container margins so everything aligns perfectly on the left and right edges.
