---
id: 17
title: Overnight batch — overseas autocomplete+full report, built-in backtester, world detail charts, UI glass polish, .app rebuild
date: 2026-06-12 06:45 KST
agent: Claude (Fable 5)
area: [overseas, backtest, world-market, ui, build, launch]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/dist/K-Market Dashboard.app (rebuilt)
supersedes: []
verified_by: |
  Integrated run on :8803 (MI_NO_OPEN MI_NO_PREWARM uv run) + /__ping keepalive (trap#8).
  [피드백3] /api/ov/suggest?q=엔비디아 -> NVDA NAS 🇺🇸; q=toyota -> TM NYS + 7203 TSE 🇯🇵 (한글 OK).
    /api/ov/detail?excd=NAS&symb=AAPL -> PER 35.77 PBR 40.73 EPS 8.27 52주 317.4/194.3
    시총 4.343조$ 섹터 '컴퓨터전자장비/기기' 원화 452,913 환율 1531.7 — all LIVE.
    detail 7203 -> ¥2747.5 PER 9.3 원화 26,214. /overseas page HTTP 200 (URL-encoded Korean OK;
    bare-curl 400 was just unencoded test bytes). News: AAPL -> scope market US 10 rows;
    7203 -> JP empty -> global fallback 10 rows.
  [작업3] /api/backtest 005930 SMA(20/60,5y): strat total +337.79% MDD -28.22 Sharpe 1.45 vs
    bench +391.35% MDD -43.17; 7 trades, expo 63%. RSI/MOM run; bh: strategy==bench EXACT
    (engine math sanity). Bad code rejected. /backtest_page 200.
  [작업6] /api/world/chart index .DJI day/month 110 rows; .N225 week 110; fx USDKRW/JPYKRW 300
    rows (~14mo). /world_detail 200. world_page has 5 click-cell hooks.
  [작업7/피드백2] GET / -> mkt-seg(6) present, m4-badge usage 0, btn-glass(8), 4 landing cards,
    miOpenUrlTab + fetchSgOv wired.
  [피드백1] ./build.sh -> exit 0, dist/.app + .dmg rebuilt 06-12 06:38, installed to /Applications.
  [비파괴] /api/screener, /api/world, /api/paper/state, /realtime_page, /backtest_page all 200.
---

# Overnight batch (user asleep — full trust run)

Five work items, priority 피드백3 > 작업3 > 작업6 per user. All in
`scripts/market_dashboard3_realtime.py` (additive; no existing feature touched) + .app rebuild.

## 🛠️ What was done

### 피드백3 — Overseas search & domestic-grade report (top priority)
- **Autocomplete**: `/api/ov/suggest` proxies `ac.stock.naver.com/ac` (Korean-name search!),
  filters to US+JP, maps typeCode→KIS EXCD (NASDAQ→NAS, NYSE→NYS, AMEX→AMS, TOKYO→TSE).
  Landing search in 해외 mode now shows the same dropdown (flag badge + exchange), arrow-key +
  Enter + click all route through `pick()` → `openOvTab()` (no more Enter-only).
- **Full report page** (`/overseas` rewritten): price hero (KRW-converted price + FX rate),
  52-week range bar with marker, 핵심 지표 grid (시/고/저/전일종가, PER/PBR/EPS/BPS, 시총,
  상장주수, 거래량/대금, 액면가, 매매단위, 섹터 badge), candle+volume canvas (일/주/월),
  period-return tiles, overseas news. Quant/LLM excluded per user. Data: `price-detail`
  HHDFS76200200 + `dailyprice` HHDFS76240000 + news HHPSTH60100C1.
- **News fallback chain**: SYMB-filtered → nation (US) → global (KIS has no JP NATION_CD;
  spec lists only 공백/CN/HK/US) — page labels the scope honestly.

### 작업3 — Built-in backtester (no Docker/account)
- `_bt_signal`/`_bt_run`: SMA cross, N-day momentum, RSI mean-reversion (stateful), buy&hold.
  No look-ahead (signal on close t → position from t+1), per-side cost in bp, NumPy vectorized.
  Metrics: total/CAGR/MDD/Sharpe/vol + benchmark, per-trade list & win rate, exposure,
  equity curve (downsampled). Data via existing `_clean_closes(asyncio.run(_afetch(code,days)))`
  (SSD parquet cache + Naver daily).
- `/backtest_page`: 종목 autocomplete (reuses `/suggest`), strategy picker with dynamic params,
  기간/비용 controls, result tiles (전략 vs 매수보유), 2-line equity canvas, trade table.
  Landing card 🧪 백테스터 added (5th `.sector-card`).

### 작업6 — World index/FX click → detail chart tabs
- `_world_chart`: index candles via `api.stock.naver.com/chart/foreign/index/{code}?periodType=
  {day|week|month}Candle` (110 bars); FX via `marketindex/exchange/{pair}/prices` paginated
  (pageSize max 60 → 5 pages ≈ 14 months).
- `/world_detail` page: index = candle canvas + 일/주/월 seg; FX = area-line + 최근 15일 table
  (매매기준율/현찰 살·팔 때). Hero + period-return tiles.
- `world_page` cells: foreign indices (code starts with '.') + all FX now clickable
  (KR rows excluded — domestic index detail returns empty from that API; 업종/시장 tabs cover
  domestic already). Landing exposes generic `window.miOpenUrlTab(id,opts)`.

### 작업7 + 피드백2 — UI (macOS official look)
- 스크리너/실시간 buttons → **liquid glass** `.btn-glass` (same material recipe as the old
  m4-badge: tint + `--chip-blur` + .5px hairline + `--glass-soft`; indigo / red tints, dark-mode
  text variants). **m4-badge removed** from the brand bar → search field gains space.
- 국내/해외 toggle → **macOS HIG segmented control**: recessed track (`--cap-fill` + inset
  shadow, same material as the theme toggle) + raised white thumb (dark: #5a5a5f), 🇰🇷/🌎 icons,
  `role=tablist` + `aria-selected`. **Figma MCP was queried per project rule** — file
  `a6AegNuDiPrlC5qdbXbn9R` still holds only the Cover page (trap #13 confirmed), so the
  documented Tahoe kit tokens + HIG were used.

### 피드백1 — .app double-click flicker
- Root cause of "terminal fine / .app flickers": the bundle froze the **pre-changes_16**
  `app.py` (transparent-before-show desktop bleed). Ran `./build.sh` → rebuilt + auto-installed
  to /Applications + new DMG (06-12 06:38). Code fix itself was changes_16; this ships it.

## ✅ Verification
See `verified_by` frontmatter — every endpoint observed live this session, including engine
sanity (bh strategy ≡ benchmark) and non-destructive checks on all prior features.

## ⚠️ Notes & Pending Issues
- **.app flicker needs the user's eyes** (sub-second, not headless-verifiable): double-click
  the rebuilt app. If it STILL blinks, next lever = increase the 0.3s glass-transparency defer
  in `app.py::_style_native_window`, or keep the window permanently opaque-dark.
- Overseas suggest covers US+JP by design; other nations remain index-only (세계 탭).
- KIS overseas news rarely has per-symbol rows → market-news fallback is the common path.
- FX detail history is capped ~14 months by Naver's pageSize≤60 (5 pages fetched).
- Backtest uses the simulated/future dataset (trap #11) — relative comparisons (전략 vs 매수보유)
  are the point, not absolute returns.
- Landing `/suggest` (domestic) is reused by the backtest page — if its shape changes, update
  both consumers.
