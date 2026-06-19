---
id: 12
title: Real-time Trading Desk — orderbook+heatmap, live screener, supply-demand flows, local paper trading
date: 2026-06-12 01:30 KST
agent: Claude (Opus 4.8)
area: [realtime, kis, websocket, sse, paper-trading, ui, screener, flows]
status: partial
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Backend on :8793/:8794 (MI_NO_OPEN MI_NO_PREWARM uv run), /__ping keepalive loop (trap#8).
  GET /realtime_page                -> 200, 14925 bytes, 4 marker hits (실시간/페이퍼/체결 히트맵)
  GET /api/rt/orderbook?code=005930 -> 200 live REST: 10 asks/bids (ask1 299500 q46149 ... bid1 299000 q90620)
  GET /api/rt/screener?mkt=J&blng=0 -> 200 ok:true, live volume-rank rows (252670/114800/0193T0 ...)
  GET /api/rt/flows?code=005930     -> 200 investor live: 20260611 frgn +549645 orgn -5437840 prsn +4721925
  POST /api/paper/reset -> ok; state cash=100,000,000 equity=100,000,000
  POST /api/paper/order BUY 005930 x10 -> ok fill_px=299000 (== live bid1)
  GET /api/paper/state -> cash 97,010,000 (=1e8-10*299000 EXACT), pos avg/mark 299000 pnl 0, trade logged
  GET /api/rt/stream?code=005930 (SSE) -> 2048 bytes, frame: data:{ok:true,book:{asks/bids...}} REST-seeded
  UNVERIFIED: live WS H0STASP0/H0STCNT0 ticks (체결 히트맵 trades + 체결강도) — only flow during KRX 09:00–15:30.
---

# Real-time Trading Desk

Implements the four user-requested features as a dedicated **📡 실시간 트레이딩**
iframe page (launcher button next to 🔍 스크리너 on the landing). Plan = `changes_11`.
All code is **added** to `scripts/market_dashboard3_realtime.py`; nothing existing changed.

## 🛠️ What was done
1. **Real-time orderbook + 체결 히트맵** — REST snapshot (`inquire-asking-price-exp-ccn`
   `FHKST01010200`, 10-level) + **WS→SSE bridge** streaming live 호가(`H0STASP0`) and
   체결(`H0STCNT0`). UI: 10-level ladder with qty bars; canvas heatmap (x=time, y=price,
   color=buy/sell, radius=√vol); 체결강도 + buy/sell imbalance bar.
2. **Live screener** — `volume-rank` (`FHPST01710000`) poll, 거래량/거래대금/거래증가율
   toggle (blng 0/3/1), click row → re-subscribe symbol.
3. **Supply-demand flows** — `inquire-investor` (`FHKST01010900`, 외국인/기관/개인 net buy)
   + program trade (`investor-program-trade-today` `HHPPG046600C1`).
4. **Paper trading (LOCAL simulation)** — SQLite ledger `~/.cache/kmkt_m4/paper.db`
   (cash/pos/trades), virtual fills at the live price `_kis_price(code)["price"]`,
   mark-to-market P&L. **No real broker order is ever submitted.**

## ⚙️ How it was done (Technical Details)
- **Reused infra:** `_kis_token/_kis_keys/_KIS_LOCK/_KIS_LAST_CALL` (REST+throttle),
  `_kis_ws_approval()` (ws approval key), `_kis_price()` (paper mark), Flask SSE + iframe
  page pattern + `openTab()`. New helper `_rt_kis_get()` centralizes REST GET.
- **WS→SSE bridge:** `_rt_ws_thread(code)` runs `asyncio.run()` in a daemon thread,
  `asyncio.gather`-ing two subscribers to `ws://ops.koreainvestment.com:21000/tryitout/{H0STASP0|H0STCNT0}`
  (same endpoint pattern proven by `_ws_nav_once`). Parses multi-record frames
  (`p=msg.split("|"); n=int(p[2]); f=p[3].split("^")`; per-record slice by column count;
  `0|`=plaintext, `1|` skipped, `{...PINGPONG...}` echoed). State in `_RT_STATE[code]`
  under `_RT_LOCK`. `_rt_ensure_ws()` lazily starts the thread; it auto-expires
  `_RT_IDLE_STOP=30s` after the last SSE poll. SSE generator `/api/rt/stream` reads
  state at 4 Hz, **REST-seeds the book** when no WS data yet (closed market), computes
  buy/sell imbalance with **numpy** (M4). Column maps from repo examples: `_ASP_COLS`
  (3 header + ASKP1..10 + BIDP1..10 + AR1..10 + BR1..10 + TAR/TBR), H0STCNT0 idx
  2 price / 12 vol / 18 체결강도 / 21 체결구분(1 buy,5 sell).
- **Routes:** `/realtime_page`, `/api/rt/orderbook`, `/api/rt/stream` (SSE),
  `/api/rt/screener`, `/api/rt/flows`, `/api/paper/state|order|reset`. All read
  `request.*` in the view fn (trap#2). Paper SQLite tables auto-created in `_paper_conn()`.
- **UI** (`_REALTIME_HTML`): iframe page, explicit colors + own body bg + theme sync
  (`localStorage('kmkt-theme')` + `postMessage`) per traps #1/#12; pure HTML/CSS/canvas
  (no Plotly dependency). EventSource for orderbook/heatmap; fetch polling for
  screener(5s)/flows(15s)/paper(4s).

## ✅ Verification (commands + observed output)
See `verified_by` frontmatter. Highlights:
- Paper math exact: `100,000,000 − 10×299,000 = 97,010,000`; fill at live bid1 299,000.
- Orderbook/screener/flows return **live KIS data** (keys load in-process — startup prints
  "KIS 키 로드: OK").
- SSE streams the REST-seeded book (2048 bytes captured, valid `data:` frames).
- **Not yet observed:** live WS 체결/호가 ticks (market closed at test time 01:26 KST).
  The bridge + REST fallback are verified; live ticks need a run during KRX hours.

## ⚠️ Notes & Pending Issues
- **Live WS unverified until KRX open (09:00–15:30 KST).** During closed market the desk
  shows REST orderbook snapshot + "장중에 실시간 체결이 흐릅니다" note; heatmap/체결강도 stay
  empty (correct). Re-verify intraday: open 📡 실시간, confirm `book.src=="ws"`, live dots.
- **`tryitout` WS endpoint assumption:** reused the exact URL pattern that the existing
  ETF-NAV feature uses (`_ws_nav_once`). If KIS rejects continuous streaming on `/tryitout/`,
  switch to the production realtime endpoint; REST polling remains as fallback.
- **Paper is intentionally local-sim** (user-chosen): never routes a real/모의 broker order.
  Marks against `_kis_price` (real when keys present, else snapshot) — the same price the
  user sees, consistent with trap#11 (app dataset is simulated/future).
- **Program-trade content** (`HHPPG046600C1`) wired + returns 200; field-level rendering is
  passthrough and not yet content-verified (investor block is the verified part).
- Keys: startup loads them in-process despite no `scripts/한국투자증권/...env` file present
  (a root `.env`/`API.env` autoload). `_kis_keys()` truthy in-process → `needs_key=false`.
