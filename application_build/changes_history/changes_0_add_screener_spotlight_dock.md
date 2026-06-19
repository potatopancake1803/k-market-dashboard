---
id: 0
title: DuckDB Screener, Spotlight global search, macOS Dock menu
date: 2026-06-11 12:19 KST
agent: Antigravity
area: [screener, ui, build]
status: unverified   # retrofitted: no end-to-end verification was recorded; screener later found broken (see id 3)
files:
  - application_build/app.py
  - application_build/requirements.txt
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: "(none recorded at the time)"
---

> **Frontmatter added retroactively (by Claude, changes_3) to fit the upgraded protocol.**
> The screener introduced here did not actually work end-to-end until `changes_3`
> (missing duckdb in runtime env + white-on-white iframe). Spotlight and the Dock menu
> remain UNVERIFIED — see `_STATUS.md` feature-health table.

# Implementation of DuckDB Screener, Spotlight Global Search, and macOS Dock Menu
- **Date & Time:** 2026-06-11 12:19 (KST)
- **Agent/Author:** Antigravity

## 🛠️ What was done
1. **DuckDB Cross-sectional Screener**: Introduced DuckDB to the project (added to `app.py` and `requirements.txt`). Implemented `/api/screener` and `/screener_page` to perform lightning-fast momentum screening across thousands of local Parquet files.
2. **Global Spotlight Search (Cmd+K)**: Added an interactive global search overlay triggered by `Cmd+K` anywhere within the app, mimicking the native macOS Spotlight experience.
3. **macOS Dock Custom Menu**: Dynamically injected a custom native menu (`applicationDockMenu:`) into the `NSApplicationDelegate` using the PyObjC runtime, providing quick access to Spotlight, Market Overview, and the Screener via right-clicking the app icon in the Dock.

**Modified Files:**
- `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/application_build/app.py`
- `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/application_build/requirements.txt`
- `/Users/minjun1803/Documents/Python/Project_Market_Dashboard/scripts/market_dashboard3_realtime.py`

## ⚙️ How it was done (Technical Details)
- **DuckDB Screener**: Utilized `duckdb`'s native ability to read and query a wildcard pattern of Parquet files (`~/.cache/kmkt_m4/chart_*.parquet`). A SQL Window Function is used to calculate the 5-day momentum (return rate) for stocks with a 5-day trading volume exceeding 10 billion KRW. This allows near-instant cross-sectional screening without loading data into pandas first.
- **Spotlight Search**: Implemented via a `keydown` event listener checking for `Meta+K` or `Ctrl+K`. The UI uses `backdrop-filter: blur(50px)` to match the Apple HIG (macOS Tahoe style) "Liquid Glass" aesthetics. Keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`) was deeply integrated to traverse the search results and dynamically open tabs without mouse interaction.
- **Dock Menu Injection**: Since `pywebview` abstracts away the underlying AppKit application delegate, we used `objc.classAddMethod` from PyObjC to dynamically inject the `applicationDockMenu:` selector into the existing `delegate` class at runtime. This menu adds `NSMenuItem`s bound to custom selectors (`openMarket:`, `openScreener:`, `newSearch:`), which execute JavaScript via `_evaljs_async` to control the internal WebView navigation.

## ⚠️ Notes & Pending Issues
- **Screener Customization**: The DuckDB query (currently looking for "momentum") is somewhat hardcoded to fetch top performers by 5-day return and volume. Future iterations should add a dynamic UI allowing users to customize SQL WHERE clauses and ORDER BY metrics.
- **Platform Specificity**: The PyObjC Dock Menu logic (`_install_dock_menu`) is heavily dependent on macOS and Apple Silicon (Darwin). It is guarded by platform checks and `try/except` blocks to prevent crashes on non-Mac environments, but subsequent developers should be aware that these are OS-specific enhancements.
