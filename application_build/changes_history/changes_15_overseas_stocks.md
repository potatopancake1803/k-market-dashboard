---
id: 15
title: Overseas stocks (US+JP) with 국내/해외 toggle, + relocate 세계 to a landing card
date: 2026-06-12 02:40 KST
agent: Claude (Opus 4.8)
area: [overseas, kis, ui, world-market]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Backend :8797 (MI_NO_OPEN MI_NO_PREWARM uv run) + /__ping keepalive (trap#8).
  GET / -> landing has mktSeg toggle (2) + worldCard (3); worldBtn removed (0).
  GET /overseas?symb=AAPL -> 200, 6821 bytes.
  GET /api/ov/resolve?symb=AAPL -> NASDAQ $293.37 +0.61% up (base 291.58, diff 1.79, vol 12,071,183) LIVE.
  GET /api/ov/resolve?symb=7203 -> TSE 도쿄 ¥2747.5 -2.36% down LIVE (Japan resolves).
  GET /api/ov/chart?excd=NAS&symb=AAPL -> 100 daily rows, chronological 20260120→20260611, OHLCV valid.
---

# Overseas stocks (작업1) + 세계 landing card (피드백2)

## 🛠️ What was done
- **작업1 — Overseas (US + Japan):** new 국내/해외 toggle in the brand bar (where
  "KOSPI·KOSDAQ" was), overseas ticker search, and a polished `/overseas` detail page
  (price hero + candlestick chart 일/주/월 + 1M/3M/1Y return tiles).
- **피드백2 — 세계 placement:** moved the World tab from a top-bar button to a **landing
  card** directly under "시장 현황" (same `.sector-card` box format). Removed `🌍 세계` topbar
  button + its handler.
- All added to `scripts/market_dashboard3_realtime.py`; existing domestic flow untouched.

## ⚙️ How it was done (Technical Details)
- **Backend (KIS overseas, keys present):**
  - `_ov_price(excd,symb)` → `/uapi/overseas-price/v1/quotations/price` `HHDFS00000300`
    (AUTH/EXCD/SYMB) → last/base/diff/rate/tvol.
  - `_ov_resolve(symb)` tries exchanges `NAS→NYS→AMS→TSE` until a live price returns
    (covers US + Japan), 30s cache; returns `{excd, last, rate, dir, ccy($/¥), exname}`.
  - `_ov_chart(excd,symb,gubn)` → `dailyprice` `HHDFS76240000` (output2 OHLCV), reversed to
    chronological. Reuses `_rt_kis_get`/`_rtf`.
  - Routes `/api/ov/resolve`, `/api/ov/chart`, page `/overseas`.
- **Overseas page** (`_OVERSEAS_HTML`): iframe, theme-synced (traps #1/#12); fetches resolve
  then chart; **canvas candlestick** (last ~120 bars, up=red/down=blue), period-return tiles;
  currency symbol per exchange. KIS `diff` is magnitude → hero applies dir-sign to
  `Math.abs(diff/rate)` so down-moves show `−`.
- **Toggle:** `#mktSeg` segmented 국내/해외; `mktMode` gates `doSearch` (해외 → opens
  `/overseas?symb=` tab) and disables domestic autocomplete + swaps the search placeholder.
- **세계 card:** added `#worldCard` `.sector-card` after `#marketCard` with click + Enter/Space
  keyboard handler; opens `/world_page` tab (changes_14).

## ✅ Verification (commands + observed output)
See `verified_by`. AAPL (US) and 7203/Toyota (JP) both resolve live with correct
price/currency/direction; 100-row chronological daily chart; landing toggle + 세계 card present.

## ⚠️ Notes & Pending Issues
- **Reduced feature set for overseas (by design):** no DART financials / Naver consensus /
  realtime WS desk — overseas = price hero + chart + returns. Other countries are covered
  index-only via the 세계 tab (changes_14).
- Ticker resolution is first-hit across NAS/NYS/AMS/TSE; an ambiguous symbol listed on
  multiple boards picks the first. A KIS `inquire_search` autocomplete could be added later.
- Overseas REST prices are real-world magnitudes (AAPL $293) vs the domestic simulated
  dataset (trap #11) — expected.
- Remaining in this 5-task batch: 작업3 internal backtester (user chose no-Docker internal
  build), 작업6 world index/FX click→graph tab (user OK to defer). 피드백1 flicker → changes_16.
