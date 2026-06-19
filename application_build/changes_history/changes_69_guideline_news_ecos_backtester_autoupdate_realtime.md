---
id: 14
title: UI guideline + per-stock news (Finnhub) + ECOS market-impact + backtester light/dark/pro/resizable + in-app auto-update + realtime density
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/app.py
  - application_build/CLAUDE.md
---

> **이전 위치:** `changes_history/changes_14_guideline_news_ecos_backtester_autoupdate_realtime.md` (루트 디렉터리)  
> **통합일:** 2026-06-17 (재넘버링: changes_14 → changes_69)


## What was done (7 items)
1. **Guideline §10** — codified "all UI matches Apple macOS official Figma" + "no empty space / no overflow" rules.
2. **Per-stock news** — overseas via Finnhub company-news; index/market via Naver market-wide search.
3. **AI news focus** — (prev batch) already recent-news-led; this batch added the market-wide source.
4. **Backtester** — light+dark theme, fixed trades overflow (full-width), resizable stats panel, pro metrics, +2 strategies.
5. **In-app auto-update** — overlay + background watcher auto-applies live-source changes (app.py).
6. **Realtime desk** — taller chart fills dead space, more ticker rows, bigger seg fonts.
7. **ECOS market-impact** — rule-based "증시 영향 종합 해석" card.
8. **.dmg portability** — investigated + reported (no code change; signing needs a cert).

## How it was done

### 작업1 — guideline (application_build/CLAUDE.md §10)
Rewrote UI rules: canonical source = macOS 26 Figma (fileKey a6AegNuDiPrlC5qdbXbn9R) with the extracted tokens
(systemRed #FF3B30, 상승 red/하락 blue #2E75B6, systemBlue #007AFF, ease cubic-bezier(.32,.72,0,1), radii); explicit
"no empty space / content must never overflow" rule (min-width:0 / ellipsis / table-layout:fixed; verify rightmost
column not clipped); light+dark required. Saved memory `ui-design-standard.md` (feedback).

### 작업5 — per-stock & market-wide news
- `_ov_news` rewritten: **Finnhub** `/company-news?symbol=` (US=ticker, JP=ticker+".T") — genuinely per-symbol;
  KIS market-news kept only as fallback. `_FINNHUB_NEWS_CACHE` 5m. Verified AAPL≠NVDA headlines.
- `_market_wide_news()` (new) merges Naver search `증시`/`코스피`/`코스닥` (dedup, recency) → `/api/market_news`
  now returns market-wide news (was KIS [141] random per-company). Index detail + 시장현황 both use it.

### 작업7 — ECOS market-impact commentary
`_macro_snapshot` now computes a rule-based `commentary` (overall stance good/neutral/bad + per-factor points for
기준금리 추세·장단기 스프레드·CPI·환율, scored). Rendered as a "📌 증시 영향 종합 해석" card on `/macro_page`.
(Deterministic — no LM Studio dependency.) Fixed a missing `esc()` helper on the macro page that had also blocked
the rate chart.

### 작업4 — backtester light/dark + overflow + resizable + pro
- Theme: `:root` now LIGHT (Apple tokens) + `html.dark` cockpit; head FOUC script; message listener toggles `.dark`
  and redraws; `drawCandle`/`drawEquity` read colors from CSS vars (`--cand-up/dn`, `--maf/mas`, `--buy/sell`, `--grid-ln`).
- **Overflow fix**: moved 거래 내역 out of the 250px right column into a **full-width** panel below the grid (5 cols,
  no clipping). Verified table width 1155/1240px.
- **Resizable**: grid is `minmax(0,1fr) 7px var(--statw,256px)` with a `#rsz` drag handle → `setupResizer()` adjusts
  `--statw` (200–440px), toss-style.
- **Pro metrics** (`_bt_run.pro`): Calmar, Profit Factor, Payoff(손익비), 평균 이익/손실, 최대 연속손실, best/worst.
- **+2 strategies** (`_bt_signal`): `macd` (EMA12/26 + signal9 cross), `boll` (Bollinger 20/2σ mean-reversion). Now
  6 strategies. Legend conditional (MA chips only for sma). Verified macd +419.86%/PF3.16, boll +56.25%/PF5.17.

### 작업2 — in-app auto-update (app.py — rebuild required)
- `_UPDATE_OVERLAY_JS` (web overlay: "새 버전 적용 중…" + progress bar), `_apply_update_ui()` (inject overlay →
  `threading.Timer(2.0, _restart)`), `_watch_updates()` daemon polls live-source hash every 12s vs `_LOADED_HASH`;
  on change → auto-apply. Started on `window.events.loaded`. Menu "업데이트 확인" now uses the overlay (no NSAlert
  for the apply path). Disabled when no live source (distributed .dmg = fixed bundle).

### 작업6 — realtime desk density
`canvas.chart` 200→280px AND drawChart now uses `cv.clientHeight` (was fixed H=180 → dead space). `.ticker-list`
max-height 172→248px. seg buttons 11→12.5px. Hero/panel fonts already bumped prior batch.

### 작업3 — .dmg portability (report only)
Bundled & self-contained (source, market_intel, archive, .env keys, icon) → runs on another Mac, BUT: arm64-only +
macOS 12+; **unsigned/un-notarized** → Gatekeeper requires right-click→Open on first launch (notarize needs an Apple
Developer cert); live-update disabled there (DEFAULT_LIVE_ROOT hardcoded → bundle fallback); `.env` API keys shipped
in plaintext inside the DMG (fine for personal use, risky to distribute).

## Verification
Server :8793 + Claude_Preview iframe (top-nav fires `/__bye`).
- 작업5: `/api/ov/news?symb=AAPL` vs `NVDA` → different per-symbol headlines; `/api/market_news` → 증시 전반 (코스피 급등·외국인 이탈…). ✓
- 작업7: `/api/macro` commentary {overall:중립적, 4 points}; macro page screenshot shows the card + rate chart. ✓
- 작업4: light screenshot (candles+MA+markers on light), dark via postMessage (bodyBg rgb(10,14,23)); 12 stat rows;
  trades full-width 1155px; macd/boll APIs OK. ✓
- 작업6: iframe `/realtime_page` → chart clientHeight 280, 삼성전자 hero, 10 ob rows; screenshot shows taller chart filling space. ✓
- 작업2: `py_compile app.py` OK; native overlay/restart **not** observable headlessly — needs rebuild + manual test. (unverified)
- `py_compile` clean for both files; `node --check` clean for backtester/macro JS.

## Notes & Traps
- **Rebuild required for 작업2** (app.py is the frozen launcher). After `./build.sh`: edit `scripts/market_dashboard3_realtime.py`
  while the app runs → within ~12s an "새 버전 적용 중…" overlay should appear and the app auto-restart. Verify manually.
- All `scripts/...realtime.py` changes are live-loaded (restart / 업데이트 확인, no rebuild).
- Per-stock overseas news = Finnhub (FINNHUB_KEY in .env); market news = Naver (NAVER_CLIENT_ID/SECRET).
- New rule (now in §10 + memory `ui-design-standard.md`): never let content overflow; verify rightmost column at target width.
- Backtester is theme-aware now (was always-dark); MA/RSI overlays only for sma/rsi, macd/boll show candles+markers only.
