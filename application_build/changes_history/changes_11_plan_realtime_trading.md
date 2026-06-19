---
id: 11
title: Implementation Plan — Real-time Trading Desk (orderbook/heatmap, live screener, supply-demand flows, paper trading)
date: 2026-06-12 00:00 KST
agent: Claude (Opus 4.8)
area: [plan, realtime, kis, websocket, paper-trading, ui]
status: unverified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  (plan only — no code verified yet)
---

# Real-time Trading Desk — Implementation Plan

Adds four new features requested by the user, all built on the **KIS Open API**
(open-trading-api repo at `api_documents/KIS_github/open-trading-api`) and local
(M4 Pro) compute. Delivered as a dedicated **"📡 실시간 트레이딩"** iframe page
opened from the landing, plus new Flask routes. **Non-destructive**: all code is
*added* to `scripts/market_dashboard3_realtime.py`; existing report/quant/screener
features are untouched.

## Why NOT the MCP server at runtime (design decision)
The repo ships two MCPs: **Kis Trading MCP** (FastMCP; per-call it downloads
`kis_auth.py`+API code from GitHub and runs a subprocess — see `MCP/Kis Trading
MCP/tools/base.py::ApiExecutor`) and **KIS Code Assistant MCP** (dev-time API
search/codegen). Neither belongs in the app's hot path: wiring the Trading MCP into
a 2s-polling Flask app would add Docker + MCP protocol + per-call GitHub download +
subprocess, i.e. *more* latency/complexity, not less. So we use the repo as the
**authoritative spec source** (correct endpoints/tr_ids/field layouts) and talk to
KIS directly via the app's existing `httpx` + token infra. The Code Assistant MCP is
the right tool only at *development* time.

## Reused existing infra (no reinvention)
- `_kis_token()`, `_kis_keys()`, `_KIS_LOCK`, `_KIS_LAST_CALL` (REST token + throttle).
- `_kis_ws_approval()` (websocket approval key, 12h cache) and the frame-parse pattern
  in `_ws_nav_once()` (`msg.split("|")[3].split("^")`, `0|`=plaintext, PINGPONG echo).
- `_kis_price()` → `{ok, price, change, change_pct, direction, market_open, ...}` (paper mark-to-market).
- `_market_state()` (open/closed/holiday gating).
- Flask SSE pattern (`Response(gen(), mimetype="text/event-stream")`) + iframe-page
  pattern (`/screener_page`) with theme sync (`localStorage('kmkt-theme')` + `postMessage`).
- Landing `openTab({url,title,icon,loading})` to surface the page; launcher button next to `#screenerBtn`.

## Confirmed KIS specs (from repo examples_llm/domestic_stock)
| Feature | Transport | Endpoint / TR_ID | Key fields |
|---|---|---|---|
| 1 호가창 (snapshot) | REST | `/uapi/.../inquire-asking-price-exp-ccn` `FHKST01010200` | output1: `askp1..10`,`bidp1..10`,`askp_rsqn1..10`,`bidp_rsqn1..10`,`total_askp_rsqn`,`total_bidp_rsqn` |
| 1 호가 (live) | WS | `H0STASP0` | cols: MKSC_SHRN_ISCD,BSOP_HOUR,HOUR_CLS_CODE, ASKP1..10, BIDP1..10, ASKP_RSQN1..10, BIDP_RSQN1..10, TOTAL_ASKP_RSQN, TOTAL_BIDP_RSQN |
| 1 체결 히트맵 (live) | WS | `H0STCNT0` | idx2 STCK_PRPR, idx12 CNTG_VOL, idx18 CTTR(체결강도), idx21 CCLD_DVSN(1매수/5매도) |
| 2 실시간 스크리너 | REST poll | `/uapi/.../volume-rank` `FHPST01710000` | screen `20171`; output: hts_kor_isnm, mksc_shrn_iscd, data_rank, stck_prpr, prdy_ctrt, acml_vol, acml_tr_pbmn |
| 3 수급 (종목) | REST | `/uapi/.../inquire-investor` `FHKST01010900` | output: stck_bsop_date, frgn_ntby_qty, orgn_ntby_qty, prsn_ntby_qty (당일은 장 종료 후) |
| 3 수급 (프로그램) | REST | `/uapi/.../investor-program-trade-today` `HHPPG046600C1` | MRKT_DIV_CLS_CODE 1코스피/4코스닥; output1 |

## WS→SSE bridge architecture (hardware-efficient)
- One background **asyncio thread per active code** opens `ws://ops.koreainvestment.com:21000/tryitout/{H0STASP0|H0STCNT0}`
  (the pattern already proven by `_ws_nav_once`), subscribes via approval_key, parses
  multi-record frames, and writes latest state into `_RT_STATE[code]` under a lock.
- Browser consumes via **SSE** `/api/rt/stream?code=` (the app already speaks SSE),
  which reads `_RT_STATE[code]` at ~4 Hz — decouples ws-thread from Flask, no
  approval key in the browser, respects KIS limits (≤41 regs, few connections).
- ws thread **auto-expires** ~30s after the last SSE poll (no idle sockets).
- **M4 compute**: numpy for 체결 히트맵 price×time binning, 체결강도 EMA, rolling buys/sells imbalance.
- REST snapshot is the always-available fallback (and the only path verifiable outside KRX hours).

## Feature 4 — Paper trading (LOCAL simulation, user-chosen)
- SQLite ledger `~/.cache/kmkt_m4/paper.db`: `cash`, `positions(code,qty,avg_px,name)`, `trades(...)`.
- Fills **virtually** at the app's live price (`_kis_price(code)["price"]`); marks-to-market the same way.
- **No real broker order is ever submitted** (honors the financial-action guardrail). 모의투자 keys NOT used.
- Routes: `GET /api/paper/state`, `POST /api/paper/order {code,side,qty,name}`, `POST /api/paper/reset`.
- Verifiable end-to-end with NO KIS keys (uses whatever price source is live, incl. snapshot fallback).

## New routes
`/realtime_page` (iframe UI) · `/api/rt/orderbook?code=` · `/api/rt/stream?code=` (SSE) ·
`/api/rt/screener?mkt=&blng=` · `/api/rt/flows?code=&mkt=` · `/api/paper/state|order|reset`.

## Phasing & verification
- **A** 호가 ladder + 체결 히트맵 (REST snapshot now; WS live when keys present + KRX open).
- **B** 실시간 스크리너 (volume-rank poll).
- **C** 수급 플로우 (investor + program-trade).
- **D** 페이퍼 트레이딩 (local sim) — fully verifiable now.
- Each KIS-live path is `unverified (needs KIS_APP_KEY)` until real keys are dropped at
  `scripts/한국투자증권/API_Key_한국투자증권.env` (appkey line1, secret line2) or env vars.
- Implementation log will be `changes_12_*`; `_STATUS.md` updated same session.

## Known constraints / traps to respect
- Trap #1/#12: iframe gets no parent CSS vars → explicit colors + own body bg + theme sync.
- Trap #2: read `request.*` OUTSIDE SSE generators.
- Trap #8: headless tests need a `/__ping` keepalive loop (watchdog `os._exit(0)` at 15s).
- Trap #11: app's parquet/screener data is a simulated/future dataset; KIS REST is real — paper marks against `_kis_price` (real/snapshot), which is the price the user actually sees.
- No working KIS keys currently on disk (`kis_devlp.yaml` holds placeholders) → live verification pending user keys.
