---
id: 14
title: World Market tab — global indices + FX (🌍 세계)
date: 2026-06-12 02:10 KST
agent: Claude (Opus 4.8)
area: [ui, world-market, fx, indices]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  Backend :8795/:8796 (MI_NO_OPEN MI_NO_PREWARM uv run) + /__ping keepalive (trap#8).
  GET /world_page -> 200, 4180 bytes.
  GET /api/world  -> ok:true, 12 indices + 4 FX, asof "06.12 01:51".
    KOSPI 7,763.95 (+0.43%), KOSDAQ 996.93 (+4.76%), S&P500 7,290.16 (+0.32%),
    나스닥 25,301.06 (+0.52%), 다우 50,255.29 (+0.67%), 니케이225 64,217.27 (+0.06%) ...
    FX: USD 1,531.60 (+0.47%), JPY(100) 953.93, EUR 1,762.45, CNY 225.87 — all live.
---

# World Market tab (작업2)

A new dedicated **🌍 세계** iframe tab (launcher next to 📡 실시간) showing global
indices + FX at a glance. Added entirely to `scripts/market_dashboard3_realtime.py`.

## 🛠️ What was done
- Backend `_world_snapshot()` (20s cache) fetches ~14 quotes in parallel
  (`ThreadPoolExecutor`, M4) and returns `{indices, fx, asof}`.
- Routes `GET /api/world` (JSON) and `GET /world_page` (themed iframe UI).
- Landing: `🌍 세계` button + handler opening `/world_page` as a tab.

## ⚙️ How it was done (Technical Details)
- **Data source = Naver market (auth-free)**, consistent with the app's existing
  `polling.finance.naver` usage and far more reliable than guessing KIS overseas index
  symbol codes:
  - Indices: `https://api.stock.naver.com/index/{reutersCode}/basic` — fields
    `indexName`, `closePrice`, `compareToPreviousClosePrice` (change),
    `fluctuationsRatio` (%), `compareToPreviousPrice.code` (2 up / 5 down → dir).
    Codes verified live: `.INX .IXIC .DJI .N225 .HSI .SSEC .TWII .GDAXI .FTSE .STOXX50E`.
  - FX: `https://api.stock.naver.com/marketindex/exchange/{FX_USDKRW|FX_JPYKRW|FX_EURKRW|FX_CNYKRW}`
    — `exchangeInfo.closePrice/fluctuations/fluctuationsRatio`.
  - **KOSPI/KOSDAQ reuse the app's `_kis_index("0001"/"1001")`** (KIS) for consistency;
    its payload key is `value` (not `price`) — initial mapping used `price` → 0.00, fixed
    to `value` (KOSPI 7,763.95 ✓, matches the simulated-dataset magnitude, trap #11).
  - Browser `User-Agent` header sent (Naver blocks default httpx UA).
- **UI** (`_WORLD_HTML`): iframe page, explicit colors + own body bg + theme sync
  (traps #1/#12); responsive auto-fill grid of glass cards grouped 주요 지수 / 환율;
  up=red / down=blue (Korean convention); 20s auto-refresh; "기준 MM.DD HH:MM".

## ✅ Verification (commands + observed output)
See `verified_by`. `/world_page` 200; `/api/world` returns 12 live indices + 4 live FX
with correct prices/%/direction; KOSPI price fix confirmed (7,763.95).

## ⚠️ Notes & Pending Issues
- Naver index values for foreign markets are real-world (e.g. S&P 7,290); KOSPI/KOSDAQ come
  from KIS and reflect the app's simulated/future dataset (trap #11) — mixed magnitudes are
  expected, not a bug.
- FX direction falls back to the sign of `fluctuations` when `compareToPreviousPrice` is null.
- If Naver endpoints ever rate-limit, add a short retry/snapshot cache; currently 20s TTL.
- This is 작업2 of the 5-task batch. Remaining: 작업1 overseas stocks (US+JP detail, others
  index-only — index part already covered here), 작업3 backtesting (deferred — plugin/Docker
  server not set up), 작업5 launch flicker (changes_13, awaiting user visual confirm).
