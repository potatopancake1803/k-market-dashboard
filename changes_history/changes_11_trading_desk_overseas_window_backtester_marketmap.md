---
id: 11
title: Trading desk bugfixes + overseas readability/tooltip + window drag/zoom + backtester UI + market treemap
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/app.py
---

## What was done
Five user-requested items (작업1~5):

1. **Real-time trading desk** (`_REALTIME_HTML`, `_rt_stream_payload`): fixed broken hero/order book.
2. **Overseas page** (`_OVERSEAS_HTML`): down-stock hero text white; candle chart hover tooltip.
3. **Window UX** (`_LANDING_HTML` + `app.py`): search field no longer drags the window; titlebar double-click zooms.
4. **Backtester** (`_BACKTEST_HTML`): fixed misaligned param fields; larger fonts.
5. **Market overview** (`_MARKET_HTML` + new endpoints): added a sector/stock treemap ("마켓맵").

## How it was done

### 작업1 — trading desk
Root cause of `一원`/`0원`/`+32,449,900%`: `_rt_stream_payload` never set `last`/`base`/`name`. When the market is
closed (no WS trade), `last` stayed 0 → hero showed em-dash + "원" ("一원"); order book `base` fell back to `1`
→ `(px/1-1)*100` = millions of %. Also `diff`/`rate` were never computed (hero change always 0).
- Added `_rt_stock_name(code)` (DART corp list + ETF snapshot fallback, per-code cache `_RT_NAME_CACHE`).
- `_rt_stream_payload` now calls `_kis_price(code)` (cached 0.8s open / 60s closed) to seed `base = price - change`,
  `last` (when WS dry), and computes `diff`/`rate`. Payload gains `name`, `base`, `diff`, `rate`, `market_open`, `phase`.
- JS: `es.onmessage` sets `#hNm` from `d.name`, badge reflects `market_open`/live; `updateHero(px,diff,rate,dir,mktOpen,live)`.
- `renderOB`: when total depth `tq===0` (closed), shows close + "장 마감 · 실시간 호가는 장중에만" instead of empty rows.

### 작업2 — overseas
- **Down-stock text invisible**: global `.dn{color:var(--dn)}` (blue) has equal specificity to `.hero{color:#fff}`
  but comes later → wins when hero has class `dn`. Fixed with `.hero,.hero *{color:#fff}` (higher specificity than `.dn`).
  Same latent bug fixed in the trading-desk hero too.
- **Chart hover tooltip**: `draw()` stores `chartGeo`; canvas `mousemove`→`showTip()` maps x→bar index, redraws with a
  crosshair + marker, and positions an HTML `.cv-tip` div showing 날짜/시/고/저/종/거래량. `mouseleave`→`hideTip()`.

### 작업3 — window drag / zoom
- pywebview drag (`webview/js/customize.js` `onBodyMouseDown`) walks ancestors; clicking the search input (child of
  `.topbar.pywebview-drag-region`) matched the topbar → window dragged. Fix: `.topbar` `mousedown` listener calls
  `e.stopPropagation()` when the target is interactive (`input,button,select,textarea,a,[role],.searchwrap,.kospi-ticker,
  .theme-toggle,.mkt-seg,.brand`) — stops the event before it bubbles to pywebview's `document.body` listener.
- Double-click empty titlebar → `window.pywebview.api._web_zoom_window()`. In `app.py`, `_web_zoom_window()` calls
  `NSWindow.zoom_(None)` on the main thread (AppHelper.callAfter); registered via `window.expose(_web_zoom_window)`.

### 작업4 — backtester
- Misalignment root cause: dynamic strategy params (단기/장기 SMA) were rendered inside `<span id="prm">` (inline) wrapping
  `.fld` block divs → they weren't flex items of `.form`. Fix: `#prm{display:contents;}`.
- Readability: bumped fonts (labels 11→12.5, inputs 13→14.5, tiles value 17→21, table 12.5→14, h3 13→15), `min-height:40px`
  on inputs/run button so all controls align.

### 작업5 — market treemap (마켓맵)
- `_afetch_marketmap(pairs)`: parallel (sem 5) market-cap ranking [FHPST01740000] per sector, top 14 stocks each
  (mcap 억 + change% ). `_marketmap_fig(mkt)`: builds `go.Treemap` (ids/labels/parents/values, `branchvalues="total"`,
  squarify), colors by change via colorscale blue(−3) → gray(0) → red(+3), white text. Returns figure JSON, 120s cache.
- Routes: `/api/marketmap?mkt=` (figure JSON), `/plotly.js` (bundled `get_plotlyjs()`, 1-day cache, offline-safe).
- `_MARKET_HTML`: loads `/plotly.js`, adds 마켓맵 section under the KOSPI/KOSDAQ toggle; `loadMap()` does `Plotly.react`,
  re-renders on toggle/theme/120s.

## Verification
Server `MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py`; visual checks via Claude_Preview iframe
(top-document nav fires landing `/__bye` auto-shutdown, so standalone pages loaded as iframes instead).
- 작업1: `/api/rt/stream?code=005930` → `name=삼성전자, last=342500, base=322500, diff=20000, rate=6.2, market_open=True`
  (previously name=005930, last=0). Order book % now relative to real base. RT page JS `node --check` OK.
- 작업2: iframe `/overseas?symb=BA` (down) → `#hPx`/`#hChg` computed color `rgb(255,255,255)` on blue hero; mousemove on
  canvas → `#cvTip` display=block, text "2026.04.13 시가$216.25 고가$222.21 저가$215.46 종가$222.14 거래량4,136,876".
  Screenshot confirmed white text + tooltip. JS `node --check` OK.
- 작업3: `window.expose` verified in pywebview 6.2.1 (`window.py:548`, registers under `func.__name__`). Landing JS
  `node --check` OK, contains drag-stop + `_web_zoom_window` call. **Native drag/zoom NOT observed this session**
  (requires the packaged NSWindow) — see Notes.
- 작업4: iframe `/backtest_page` → all 6 `.fld` at `top:110` (aligned), `#prm` computed `display:contents`. Screenshot
  confirmed single aligned row + larger fonts.
- 작업5: `/plotly.js` HTTP 200 (4.84 MB); `/api/marketmap?mkt=kospi` → treemap, 267 nodes, 19 sectors. iframe `/market` →
  Plotly loaded, trace rendered; screenshot shows sector/stock treemap matching the reference layout. (All cells 0.00%/gray
  today because the closed-market ranking API returns 0 change — colors are data-dependent.)
- `py_compile` clean for both files; `node --check` clean for landing/overseas/realtime/market JS.

## Notes & Traps
- **Rebuild required for 작업3 zoom**: `application_build/app.py` is the frozen launcher (NOT live-loaded) — the
  `_web_zoom_window` expose only takes effect after `cd application_build && ./build.sh`. The drag-stop and all other
  changes are in `scripts/market_dashboard3_realtime.py` (live-loaded → app restart, no rebuild).
- **Status `partial`**: native window drag/zoom (작업3) needs manual confirmation in the packaged app — run the built
  `.app`, click+drag the search field (window must stay put), and double-click an empty titlebar area (window should
  zoom/restore).
- Marketmap colors only show during sessions with non-zero `prdy_ctrt`; closed/pre-open ranking data is 0 → all gray.
- `/__bye`: landing `beforeunload` shuts the server down on top-document navigation — verify standalone pages
  (`/overseas`, `/market`, `/backtest_page`, `/realtime_page`) by loading them as iframes inside the root page in preview.
- Trap reused: pywebview drag is on `document.body` (bubble) — child `stopPropagation()` (bubble) is the correct,
  version-independent way to exclude interactive elements (no `-webkit-app-region` in pywebview).
