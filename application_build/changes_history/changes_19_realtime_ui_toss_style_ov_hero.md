---
id: 19
title: Realtime trading UI (Toss-style) + overseas hero rolling animation
date: 2026-06-12 KST
agent: Claude (Sonnet 4.6)
area: [ui, realtime, overseas]
status: partial
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  python3 -m py_compile scripts/market_dashboard3_realtime.py -> OK (no syntax errors)
  Visual verification requires live browser run (server not started this session).
---

# Realtime trading UI (Toss-style) + overseas hero rolling animation

## 🛠️ What was done

### 작업1 — Realtime trading page full rewrite (Toss Securities style)

**Root cause**: The old `_REALTIME_HTML` had a flat 2-column layout (orderbook left,
heatmap right) with a plain input bar, no price hero, no chart, and no real-time price
display in the header. The user showed a Toss Securities screenshot as the target UX.

**New layout** (`_REALTIME_HTML` fully replaced):

- **Price hero bar** (top, full-width, colored): red background when up / blue when down,
  rolling digit animation via `rollPrice()` matching the CLAUDE.md section 12 spec
  (changed digits slide vertically with `cubic-bezier(.16,1,.3,1)` / 0.62s / 26ms stagger),
  shows current price, change amount+%, and live timestamp.
- **3-column main grid**: (chart+ticker+flow) | orderbook | paper trading
  - Left column: daily candlestick chart (from `/api/rt/history`, canvas 2D), period
    selector (1M/3M/6M), real-time current price dashed line overlaid, volume bars.
    Below the chart: 체결 시세 ticker (SSE trades list) and 투자자 동향 flow bars.
  - Center column: 5-level ask + current price + 5-level bid orderbook, colored
    quantity bars (right-anchored), % vs previous close, imbalance bar.
  - Right column: paper trading — portfolio tiles (equity/cash/market value/total PnL),
    quantity input + buy/sell buttons, reset, positions table.
- **Bottom**: full-width screener card (volume / amount / growth-rate tabs, 5s auto-refresh).
- **Dark mode**: inherits CSS vars (--bg, --card, --up, --dn, etc.) with dark theme toggle
  via `window.message` postMessage from the PyWebView wrapper.

Technical changes in `_REALTIME_HTML`:
- Added `rollPrice()`, `rollCell()`, `staticCell()` — identical pattern to domestic stock
  hero in `_REALTIME_HTML`.
- `subscribe()` calls `loadHistory()` on each new subscription to load fresh chart data.
- `updateHero(px, diff, rate, dir, src)` sets hero background class and calls `rollPrice`.
- `drawChart()` draws candlestick + volume bars + current price dashed line on a canvas.
- Chart period buttons (`$('#chartSeg')`) reload history from `/api/rt/history?days=N`.
- `renderTicker(trades)` renders SSE trade list (up to 18 rows) with price, volume, % change.
- `loadFlow()` shows investor flow as labeled bar rows (외국인/기관/개인).
- Orderbook `renderOB(d)` uses 5 ask + 5 bid levels (was 10+10 in old version).

### 작업2 — Overseas stock page hero redesign + rolling digit animation

**Root cause**: The old overseas hero was a plain flex layout (`<div class="hero">`
inside a card) with static `textContent` price update — no color, no animation.
The user asked for the same UX as the domestic stock price hero.

**New overseas hero** (`_OVERSEAS_HTML` fully replaced):

- `<div class="hero-block">`: full-width colored block (no card border), transitions
  red ↔ blue via `background` CSS transition on `--hero-bg-up` / `--hero-bg-dn`.
  Radial white gradient overlay for depth (matches domestic hero style).
- Symbol row: company name + ticker symbol + exchange badge + sector badge +
  `● 실시간` badge (visible after first data load, blinks with `heroBlink` keyframe).
- Price: `<span class="h-ccy">` (currency symbol) + `<span class="h-px">` (rolling digits).
  Font size 38px. `rollPrice()` / `rollCell()` / `staticCell()` same pattern.
- Change: `▲ +1.23 (2.45%)` in `<div class="h-chg">`.
- Sub-line: KRW estimate + "실시간 · HH:MM:SS 갱신" timestamp.
- 52-week range rendered inside the hero block (white bar gradient + white dot).
- `updateHero(ccy, last, diff, rate, dir, meta)` is called from both `render(d)` (initial
  load) and `pollPrice()` (10s polling). Rolling animation only triggers when `newStr ≠ lastPxStr`.
- Layout below hero: `.wrap{padding:0 14px 20px}` wraps 핵심지표 / 기간수익률 / 차트 / 뉴스 cards.
- Dark mode: `--hero-bg-up:#c0241a` / `--hero-bg-dn:#144fa0` (slightly darker for dark bg).

Also fixed in `_OVERSEAS_HTML`:
- Old `.up` / `.down` CSS classes conflicted — renamed `.dn` for fall direction in new version.
- `fmtI` used `en-US` locale for overseas numbers (intentional — these are foreign market prices).
- Chart canvas height reduced from 380 → 360 (fits better with new hero taking space at top).

## ⚙️ How it was done (Technical Details)

**Rolling digit implementation** (per CLAUDE.md §12):
- `rollCell(h, oldCh, newCh, up, delay)`: creates a 2-entry flex column (old+new or new+old),
  translates to show oldCh, then animates to newCh position.
- Direction: `up=true` → column starts at top (old), animates down → new appears from below.
  `up=false` → column starts at bottom (new), old slides out downward.
- Stagger: rightmost digit at delay=0, each more-significant digit +26ms.
- `staticCell(h, ch)` for digits unchanged between old/new string.
- `rollPrice(pe, oldStr, newStr, up)`: aligns by right side (least significant digit).

**Hero background transition**: CSS `transition: background .45s cubic-bezier(.4,0,.2,1)`
with two theme variables `--hero-bg-up` and `--hero-bg-dn`. Toggled by adding/removing
`.dn` class on `.hero-block`. Smooth enough at ~0.45s.

**Canvas chart (realtime page)**: uses same pattern as overseas chart — `devicePixelRatio`
scaling, candlestick + wick + volume bars, 3-label date axis, current-price dashed overlay.
`drawChart()` is called both by `loadHistory()` and `window.resize`.

**Syntax check**: `python3 -m py_compile` passed after both rewrites.

## ✅ Verification (commands + observed output)
```
python3 -m py_compile /path/to/scripts/market_dashboard3_realtime.py
→ (no output) = OK
```
Visual verification (hero color change, rolling animation, Toss-style layout) requires
a live browser. Marked `status: partial` accordingly.

## ⚠️ Notes & Pending Issues
- The rolling animation font-size (`parseInt(getComputedStyle(pe).fontSize)`) on the
  overseas hero returns 38 (matching `.h-px { font-size: 38px }`). Verify this matches
  actual layout in a live browser session.
- `lastPxStr` is initialized to `''` — the very first render call always sets text without
  animation (correct behavior; `rollPrice` skips animation when `oldStr` is empty).
- Orderbook display is 5+5 levels (was 10+10 in old page). This matches Toss Securities
  UX; change to 10+10 if the user prefers more depth.
- Paper trading `/api/paper/order` body includes `name: code` (code used as fallback name);
  the backend already handles this.
