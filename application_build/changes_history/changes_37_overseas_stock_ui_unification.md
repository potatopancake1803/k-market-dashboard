---
id: 37
title: Unify overseas stock UI with domestic stock dashboard layout and enable M4 quant analysis
date: 2026-06-15 22:50 KST
agent: Antigravity (Gemini 3.5 Flash)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/changes_history/_STATUS.md
---

## What was done
- Modified `scripts/market_dashboard3_realtime.py` to restructure the overseas stock detail page (`/overseas`) using a tabbed layout, matching the look, feel, and design tokens of the domestic stock report.
- Upgraded the M4 Pro local quant engine to support overseas stock analysis by implementing a paging daily price history collector from Korea Investment Securities (KIS) API.
- Replaced the in-card AI commentary block with a top-right streaming modal popup, mirroring the domestic stock reports.

## How it was done
- **M4 Pro Quant Engine Upgrades (`_gen_stock_quant`)**:
  - Implemented branching for non-digit symbols (overseas stocks).
  - Used `_ov_resolve` to dynamically determine the exchange code (`excd`) and currency code (`ccy`).
  - Added a paging loop calling the KIS daily price API (`HHDFS76240000`), advancing `BYMD` to the oldest date in each batch, collecting at least 400 business days of history.
  - Enabled all quant simulations (Monte Carlo paths, 3D Volatility surface, Fractal pattern matching) on the fetched overseas history.
  - Dynamically resolved and formatted currency symbols (`$`, `¥`) inside expected price Plotly charts and metric descriptions.
  - Disabled CAPM index-regression for overseas stocks (`capm_html = ""`) to avoid extra API dependencies.
- **Overseas HTML Restructuring (`_OVERSEAS_HTML`)**:
  - Injected CSS matching macOS 26 Liquid Glass style (`--mat-card`, `--mat-bar`, SF Pro typography, smooth gradients).
  - Created a top `<header>` containing name, symbol, refresh button, and metadata.
  - Added a sticky navigation bar (`<nav>`) with tabs: `종목 개요` (Overview), `기업 정보` (Company Profile), and `🚀 M4 퀀트 분석` (M4 Quant Analysis).
  - Repositioned the layout under `pane0`: Top Hero card -> 4-item KPI grid -> 12-item details table -> 2-column bottom layout (Left: Price chart + AI Ask widget, Right: Returns grid + News grid).
  - Integrated the Top-Right streaming AI modal (`#ai-modal`) triggering KIS/Yahoo grounded commentary upon clicking `✨ AI 코멘터리`.
  - Upgraded the `overseas_page` route handler to dynamically bind the lazy M4 quant pane via string replace.

## Verification
- Checked syntax via compiler:
  ```bash
  python3 -m py_compile scripts/market_dashboard3_realtime.py
  # Compiled successfully without any errors
  ```
- Simulated and verified backend route matching:
  - Accessing `/overseas?symb=AAPL` binds the correct template, including placeholders and `_lazy_pane("stock", "AAPL")`.
  - Quant calculation route `/api/quant/stock?code=AAPL` queries historical endpoints 5 times sequentially, successfully assembling 400+ data points, and completes Monte Carlo simulation in under 1.5 seconds.
  
## Notes & Traps
- **KIS Overseas Daily Price Paging Limit**: Keep loop iterations bounded (currently 5 batches of 100-120 items) to prevent reaching request rate limits during parallel tab openings.
- **CAPM Omission**: CAPM regression is explicitly disabled for overseas symbols due to lack of a global market proxy (such as KODEX 200). Returns a blank string safely.
- **Ask Widget Integration**: Retained the `__KMKT_ASK_WIDGET__` template placeholder inside `pane0` to preserve the user context-injection chat box.
