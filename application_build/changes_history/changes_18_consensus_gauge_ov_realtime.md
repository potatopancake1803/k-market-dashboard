---
id: 18
title: Consensus gauge distribution-arc fix + overseas real-time price polling
date: 2026-06-12 KST
agent: Claude (Sonnet 4.6)
area: [ui, overseas, realtime]
status: partial
files:
  - market_intel/report/dashboard.py
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  python3 -m py_compile on both files -> OK.
  Visual verification (gauge arc color change, overseas polling) requires a live browser session.
  The consensus gauge logic is deterministic: dist={매수:23,중립:0,매도:0} → steps=[{range:[1,5],color:"#d6ebd6"}]
  (all-green arc). Visual and polling not headlessly verifiable.
---

# Consensus gauge distribution-arc fix + overseas real-time price polling

## 🛠️ What was done

### 피드백1 — Consensus gauge arc now matches analyst distribution
**Root cause**: `consensus_gauge()` in `dashboard.py` used hard-coded score-range zones
(pink 1–2.5 / yellow 2.5–3.5 / green 3.5–5) regardless of the actual opinion distribution.
So when all 23 analysts said BUY, the arc still showed a large pink (sell) zone and yellow
(neutral) zone on the left, visually contradicting "매수 23 · 중립 0 · 매도 0".

**Fix**: `consensus_gauge(recomm_mean, dist=None)` now accepts the same `dist` dict that
`consensus_panel_html` already had. When `dist` is provided:
- Arc zones are sized proportionally to `n_sell / n_hold / n_buy` fractions of the 1–5 range
- Zero-fraction ranges are filtered out (empty Plotly step ranges cause no visual artifact)
- With dist={매수:23,중립:0,매도:0} → entire arc (range [1,5]) is green
- With dist={매수:15,중립:3,매도:5} → arc is proportionally red | yellow | green

`consensus_panel_html` already received `dist`; changed the one `pio.to_html` call to pass
`dist=dist` to `consensus_gauge`.

Files changed:
- `market_intel/report/dashboard.py`: `consensus_gauge` signature + arc step logic
- `market_intel/report/dashboard.py`: `consensus_panel_html` → `consensus_gauge(recomm_mean, dist=dist)`

### 피드백2 — Overseas page real-time price polling (10s interval)
**Root cause**: The `/overseas` page had no polling at all. Price was fetched once via
`_ov_detail` (HHDFS76200200) on page load and never refreshed.

**Fix**:
1. New endpoint `/api/ov/price` using the lightweight `_ov_price()` (HHDFS00000300) —
   returns only `{ok, last, diff, rate, dir, ccy}`. Much faster than the full detail call.
2. In `_OVERSEAS_HTML` JS:
   - Added `lastFx` variable (populated from `d.fx` in `render(d)`) and `pollTid`
   - `render(d)` saves `lastFx` and starts `setInterval(pollPrice, 10000)`
   - `pollPrice()` calls `/api/ov/price`, updates `#px`, `#ch`, `#krw` with current price
     and the cached FX rate for KRW conversion, and shows "실시간 · HH:MM:SS 갱신" in `#rt-meta`
   - Added `<div id="rt-meta">` below `#krw` in hero section

## ⚙️ How it was done (Technical Details)
- Distribution-proportional arc: `sell_end = 1 + (n_sell/total)*4`, `hold_end = sell_end + (n_hold/total)*4`.
  Arc is always anchored from 1 (min) to 5 (max). Steps with `range[0] == range[1]` are filtered out.
- The FX rate for KRW conversion is set once from the initial full `_ov_detail` call (which returns
  `t_rate`). Subsequent polls only update price/change and reuse the cached FX rate; this avoids an
  extra FX API call on every tick.
- Polling interval 10s: appropriate for overseas markets (lower tick frequency than domestic, and
  KIS overseas REST has no per-symbol WebSocket subscription available without account auth).

## ✅ Verification
- `python3 -m py_compile` on both files → OK (no syntax errors)
- Logic verification: with `dist={"매수":23,"중립":0,"매도":0}`, `total=23`, `sell_end=1.0`,
  `hold_end=1.0`, `raw_steps` has two zero-length entries filtered out, leaving only
  `{"range":[1.0,5],"color":"#d6ebd6"}` → entire arc is green. Correct.
- **Visual**: unverified headlessly. Needs live browser run to confirm gauge color and price ticker.

## ⚠️ Notes & Pending Issues
- KIS overseas REST polling has a rate limit; 10s interval is conservative and well within limits.
- The `lastFx` approach means if the KRW exchange rate changes significantly during a session, the
  KRW display will drift. Acceptable for a session (rate changes < 1% intraday typically). A full
  refresh reloads the correct rate.
- Consensus gauge fix requires a fresh page load (existing cached HTML pages are unaffected until
  the next server restart clears the RAM result cache).
