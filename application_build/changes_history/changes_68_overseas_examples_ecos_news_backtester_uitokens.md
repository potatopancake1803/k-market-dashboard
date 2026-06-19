---
id: 13
title: Overseas search examples + ECOS macro page + recent-news AI commentary + backtester terminal redesign + UI color unification
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

> **이전 위치:** `changes_history/changes_13_overseas_examples_ecos_news_backtester_uitokens.md` (루트 디렉터리)  
> **통합일:** 2026-06-17 (재넘버링: changes_13 → changes_68)


## What was done
Five user items (this batch 작업1~5):

1. **Overseas search examples** (`_LANDING_HTML`): example chips now switch to overseas tickers when the 해외 toggle is on.
2. **ECOS macro page** (new): a "한국 경제 지표" page (BOK rates/bonds/CPI/FX) from a landing card.
3. **AI commentary** (`_build_ai_context`): foregrounds recent news (Naver News Search) over past price action.
4. **Backtester** (`_BACKTEST_HTML` + `_bt_run`): redesigned into a dark trading-terminal (candles + MA + buy/sell markers + RSI subpanel + stats panel + equity curve).
5. **UI consistency**: unified the divergent up/down (red/blue) palette across standalone pages to the Apple-aligned macOS-26 values.

## How it was done

### 작업1 — overseas search examples
The 국내/해외 토글 changed only the placeholder; the `.empty .ex` example chips stayed domestic (삼성전자 등).
Added `EX_KR`/`EX_OV` arrays + `renderExamples()` that rebuilds the chips per `mktMode` (해외 → 애플/AAPL·NAS,
엔비디아, 테슬라, MSFT, 토요타/7203·TSE) and binds click → `openOvTab` (overseas) / `pick` (domestic). Called on
init and in the toggle handler. Verified: toggling 해외 swaps chips + placeholder; chips carry correct code/excd.

### 작업2 — ECOS macro page (한국은행 ECOS)
- `_ecos_rows(stat,period,item,start,end)` + `_macro_snapshot()` (1h cache): 기준금리(722Y001 M), 국고채 3·10년
  (817Y002 — **daily only**, resampled to month-end via `_to_monthly`), CPI(901Y009 M, YoY computed), 원/달러(731Y001 D).
  Item codes corrected via StatisticItemList: 국고채3년=010200000, 10년=010210000.
- Routes `/api/macro` + `/macro_page` (`_MACRO_HTML`): 6 KPI tiles (기준금리·국고3y·국고10y·장단기 스프레드·원달러·
  CPI YoY) + 금리 추이 line chart (기준금리·3y·10y) + CPI YoY chart. Landing card `#macroCard` (🏦) → `/macro_page`.
- ECOS lags ~1 month → asof(기준시점) shown on each tile/chart.

### 작업3 — recent-news AI commentary
- New `_naver_news(query,n)` — Naver News Search API (`sort=date`, returns title+description+pubDate), 5m cache.
- `_build_ai_context` restructured: price/risk block condensed to ONE "시세 흐름(보조)" line (was 4 verbose lines of
  Sharpe/Sortino/VaR/CVaR); a prominent "[최근 뉴스 — 분석의 핵심 근거]" section merges Naver news (with summaries) +
  KIS [141], deduped, up to 10 items.
- System prompt rewritten: "★ 최근 뉴스를 분석 중심에 두고, 과거 주가 흐름은 보조 배경으로만 한 번 언급."
- Verified: LM Studio stream for 005930 led with recent news ("삼성전자는 최근 구글이 차세대 TPU…").

### 작업4 — backtester dark trading-terminal
- `_bt_run` now emits chart data: `_clean_ohlc()` for OHLC; downsamples to ~300 OHLC buckets (`bars` with o/h/l/c +
  per-bucket MA `mf`/`ms` for sma or `rsi` for rsi), records buy/sell `markers` (bucket index + price + side), and `ind`
  metadata. Added `name` to the response.
- `_BACKTEST_HTML` fully rewritten as a dark cockpit (always dark, like the M4 quant tab): compact form bar → status
  strip (종목·전략 태그·기간·거래·승률 + big 총수익률) → grid [candle chart w/ MA lines + ▲buy(teal)/▼sell(amber)
  markers + RSI subpanel(70/30 dashed) | right 전략 성과 stat panel] → equity curve → recent trades table.
  Canvas `drawCandle()` + `drawEquity()`.
- Verified: SK하이닉스 SMA backtest renders candles + MA20/MA60 + buy/sell markers + equity curve + 7 stat rows.

### 작업5 — UI color unification (Apple/macOS-26 aligned)
Audit found two divergent semantic red/blue palettes across standalone pages: Apple-aligned `#FF3B30/#2E75B6`
(landing, market, world, suggest) vs vivid `#E8291C/#1A65C0` (overseas, index, macro, trading-desk, marketmap).
The macOS-26 landing (Figma-kit-aligned, tokens in memory `macos26-theme.md`) and Apple systemRed both use `#FF3B30`.
Unified everything to **light `--up:#FF3B30` / `--dn:#2E75B6`, dark `--up:#FF453A` / `--dn:#64B5FF`** — incl. hero
backgrounds, order-book pct tints, marketmap treemap colorscale + legend, and macro chart line colors. The backtester
keeps its intentional dark-cockpit palette (like M4 quant). The report builder (dashboard.py, `#c0392b/#2e75b6`) is a
separate non-destructive subsystem and was left untouched (noted).

## Verification
Server `MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py`; visuals via Claude_Preview iframe.
- 작업1: eval — 해외 토글 → chips [애플,엔비디아,테슬라,MSFT,토요타] w/ code/excd, placeholder overseas. ✓
- 작업2: `/api/macro` → 기준금리 2.5, 국고3y 3.808, 국고10y 4.195, spread +0.387, CPI YoY 3.14, 30-mo series.
  Screenshot: 6 tiles + 금리/CPI charts. ✓
- 작업3: POST `/api/llm_commentary {code:005930}` streamed, news-led. No server errors. ✓
- 작업4: iframe ran SK하이닉스 SMA → total +1,083.82%, candle+MA+markers+equity, 7 stat rows. Screenshot. ✓
- 작업5: grep → 0 remaining `#E8291C/#1A65C0`; all 8 pages HTTP 200; marketmap screenshot reads red(up)/blue(down). ✓
- `py_compile` clean; `node --check` clean for landing/macro/backtester/market/index JS.

## Notes & Traps
- All changes are in `scripts/market_dashboard3_realtime.py` (live-loaded) → app restart / 업데이트 확인, **no rebuild**.
- ECOS free data lags ~1 month; 817Y002 (국고채) is daily-only (no monthly cycle) → resample to month-end.
- AI commentary requires LM Studio (port 1234); recent-news quality depends on Naver News Search (NAVER_CLIENT_ID/SECRET in .env).
- Figma MCP `get_variable_defs` needs live desktop selection (remote nodeId unsupported) — used the official tokens
  already extracted into memory `macos26-theme.md` (ease cubic-bezier(.32,.72,0,1), systemBlue #007AFF, systemRed #FF3B30,
  radii pill100/glass26/lg16/md11) as the consistency reference.
- Report builder (`market_intel/report/dashboard.py`) keeps `#c0392b/#2e75b6` by design — not unified (separate subsystem).
