---
id: 12
title: Smooth zoom anim + live market cards/marketmap + trading-desk resize/fonts + index detail page + world status + pre-open zero
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/app.py
---

> **이전 위치:** `changes_history/changes_12_zoom_market_realtime_marketmap_tradingdesk_indexpage_world.md` (루트 디렉터리)  
> **통합일:** 2026-06-17 (재넘버링: changes_12 → changes_67)


## What was done
Six user items (this batch's 작업1~6):

1. **Window zoom animation** (`app.py`): double-click titlebar now expands smoothly instead of jumping to top-left.
2. **Market overview** (`_MARKET_HTML`): live rolling index cards w/ pulsing red dot; marketmap made static (query-time only) with reference timestamp; treemap text now scales by cell size.
3. **Trading desk** (`_REALTIME_HTML`): fixed right-panel cutoff (flex layout), added drag resizer, enlarged fonts.
4. **Index detail page** (new `_INDEX_HTML` + endpoints): Naver-style KOSPI/KOSDAQ page — candle chart, sidebar, market news.
5. **World market** (`_world_*`): localized open/pre/closed/holiday status with colored dot.
6. **KOSPI ticker** (`api_index`/`_market_overview`): pre-open shows 0 change.

## How it was done

### 작업1 — zoom animation (app.py, rebuild required)
`_web_zoom_window` previously called `NSWindow.zoom_(None)` (jumps to standard frame). Now toggles between current
frame and `screen.visibleFrame()` via `setFrame_display_animate_(frame, True, True)` (single smooth Cocoa resize),
storing the pre-max frame in `_menu_state["_prevframe"]` for restore.

### 작업6 + 작업2a — index live / pre-open zero
- `_zero_if_pre(d, phase)`: when phase=="pre", copies dict and sets change/change_pct=0, direction="-".
  Applied in `api_index` (ticker) and `_market_overview` (cards). Fixes "pre-open shows prev-day change".
- Market cards rebuilt once (`buildOv`) then updated in place: `ovRoll()` digit-rolling (same as top KOSPI ticker),
  per-card pulsing `.dot.live` when phase=="open", clickable (`data-idx` → `openIndex` → parent `miOpenIndexTab`).
  Overview poll 30s → 3s (document.hidden-guarded) for a live feel.

### 작업2b/2c — marketmap static + variable font
- Removed the 120s `loadMap` interval; map loads only on init + KOSPI/KOSDAQ toggle. Added `#mapAsof` "기준 MM.DD HH:MM:SS".
- `_marketmap_fig`: removed fixed `textfont.size` → Plotly auto-sizes text per tile (big cells big text, tiny cells omit).
- **Bug fixed**: '제조'(0027/1009) is an umbrella sector overlapping 전기·전자/화학 etc. → 삼성전자 appeared twice.
  Now excludes the '제조' pair and dedups stocks by code across sectors (first/largest sector wins).

### 작업4 — index detail page (new)
- `_index_chart(iscd, period)`: KIS `inquire-daily-indexchartprice` (FHKUP03500100, market U, D/W/M/Y). Returns
  rows[{d,o,h,l,c,v}] + prev_close/amount/hi52/lo52. 60s cache. Uses KIS (not Naver) so values match the app's ticker.
- `_INDEX_HTML` + `/index_page?code=&name=`: hero (value/change, live dot, phase badge, 3s poll of /api/index),
  candle chart with MA5/20/60/120 + volume + hover crosshair tooltip (same engine as overseas page), 시세정보 grid,
  등락 종목수 bars, 시장 뉴스 (reuses /api/market_news). Route `/api/index_chart`.
- Landing: `window.miOpenIndexTab(code,name)` opens it; KOSPI top-ticker and market overview cards are now clickable.

### 작업3 — trading desk layout/resize/fonts
- `.main` grid (`minmax(0,1fr) 220px 210px` + `overflow-x:hidden` on body) clipped the 3rd column. Rebuilt as flex:
  `.col-left{flex:1 1 0}` + `.rsz` 6px drag handle + `.right-group{flex:0 0 var(--rgw,430px); min 330 / max 660}`
  wrapping `.col-ob` + `.col-paper` (both `flex:1 1 0`). Nothing clips now (verified rightGroupRight 1251 < body 1265).
- Drag resizer JS: mousedown on `#rsz` → mousemove adjusts `--rgw` (clamped 330–660) → redraw chart on mouseup.
- Removed a duplicate `.col-left` rule that overrode the flex. Bumped fonts (h3 12.5→13.5, ob-px 12.5→14,
  ob-cur 13→15, ob-q 11.5→12.5, t-row/flow 12→13, scr-table 12.5→13.5, ptile 14.5→16, pos-table 11.5→12.5, chart 180→200).

### 작업5 — world market status
- `_world_status_kr(raw)` maps Naver `marketStatus` (OPEN/CLOSE/PREOPEN/…) → (한글, phase). `_world_index_one`
  returns localized `status` + `phase`. `_world_domestic_one` derives phase from `_index_phase()` and `_zero_if_pre`.
- World page: status tag now has a phase-colored `.sdot` (green pulse=open, amber=pre, gray=closed) + Korean label.

## Verification
Server `MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py`; visuals via Claude_Preview iframe.
- 작업6: `/api/index?code=0001` returns phase + change (today phase=open in this env, so non-zero; pre-open branch
  zeroes — code path verified by logic). `_zero_if_pre` applied in both ticker + cards.
- 작업2: iframe `/market` → `#val_kospi` rolls (8,579.44), `#dot_kospi`="dot ov-dot live", `#mapAsof`="기준 06.15 09:30:18",
  ovcard role=button. Screenshot: treemap shows variable text (삼성전자/SK하이닉스 large, small cells tiny/omitted),
  red/blue by change. `/api/marketmap?mkt=kospi`: 삼성전자 once, 제조 excluded, 21 sectors.
- 작업4: `/api/index_chart?code=0001` → 코스피, 50 rows, prev 8123.62, last 8582.83. iframe `/index_page` screenshot:
  코스피 장중 8,579.84 ▲+456.22, candle+MA+volume+일/주/월/년, 시세정보, 등락 종목수, 시장 뉴스. JS `node --check` OK.
- 작업3: iframe `/realtime_page` (1280px) → rightGroupRight 1251 ≤ body 1265 (no cutoff), `#rsz` present. Screenshot:
  호가창 percentages sane (+5.58%/+4.96%…), 삼성전자 338,000 ▲+15,500, bigger fonts. JS `node --check` OK.
- 작업5: `/api/world` → 코스피/코스닥 장중, S&P/나스닥/다우 장마감, 니케이 장중 (correct). World JS `node --check` OK.
- `py_compile` clean for both files.

## Notes & Traps
- **Rebuild required for 작업1** (app.py is the frozen launcher, not live-loaded). `cd application_build && ./build.sh`,
  then double-click an empty titlebar → window should smoothly expand to full and double-click again to restore.
  All other changes are in the live-loaded `scripts/market_dashboard3_realtime.py` (app restart / 업데이트 확인, no rebuild).
- Index detail uses KIS index chart (not Naver) on purpose — Naver returns real-world values (~4214) that mismatch this
  environment's simulated KIS data (~8580). Keep both header and chart on the same source.
- Marketmap is intentionally NOT real-time (per request) — reloads on tab open + KOSPI/KOSDAQ toggle only, with 기준시점.
- `/__bye`: landing beforeunload shuts the server on top-document nav — verify standalone pages (`/index_page`,
  `/market`, `/realtime_page`, `/world_page`) as iframes inside the root page in preview.
- Trap: pywebview drag listener is on document.body (bubble); the trading-desk resizer is inside an iframe so no conflict.
