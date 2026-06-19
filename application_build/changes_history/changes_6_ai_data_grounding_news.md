---
id: 6
title: Local AI commentary — real-data grounding (quant metrics) + KIS [141] stock news
date: 2026-06-11 16:40 KST
agent: Claude (Opus 4.8)
area: [local-llm]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  End-to-end POST /api/llm_commentary {"code":"005930"} and {"code":"000660"} (model qwen3-4b-2507):
    005930 -> cites real momentum (5d -14.9% / 20d +7.2% / 60d +62.9%), VaR, 52w pos,
              AND real KIS news headlines ("중동·아프리카 갤럭시 27% 점유율", "외국계 순매수"),
              ends with "※ 데이터 요약이며 투자조언이 아닙니다." first token 2.0s / total 5.0s.
    000660 -> real numbers + real news, disclaimer. first 1.3s / total 4.1s.
  52w-range robustness (standalone numpy proof): bad-tick low -> old min/max "저점대비 +435%"
    vs new percentile(1/99)+clamp "+1.5%"; on clean data near-identical (+18.6% vs +17.8%).
---

# Local AI commentary — real-data grounding + stock news

## 🛠️ What was done
Turned the AI commentary from **hallucinated** prose into a **data-grounded** analyst
note (user-approved scope **P1 + P2**, news source = **KIS 종합시황·공시 [141]**).

Before: the frontend sent only `종목코드 005930에 대해 코멘트해줘` — the model had **no
data** and fabricated every number (e.g. "10일 기준 15.2% 상승" was invented). For a
finance tool that is worse than nothing.

After: the backend assembles a **data sheet** of real numbers + real news for the code and
instructs the model to use *only* those, with a non-advice disclaimer.

## ⚙️ How it was done (Technical Details)
- **Architecture flip:** prompt is now built **server-side** (it owns the data), not in the
  browser. Frontend `startAI(code)` now POSTs `{code}` (was a pre-baked `{prompt}`); the
  endpoint reads `code` and constructs the messages. Legacy `{prompt}` still works (fallback).
- **`_build_ai_context(code) -> (name, sheet|None)`** (90s RAM cache). Reuses existing,
  already-correct pipeline pieces:
  - realtime/last price + change via `_kis_price(code)`;
  - `_clean_closes(asyncio.run(_afetch(code, 400)))` → momentum (5/20/60d), 52-week
    position, and `_risk_stats()` (ann return/vol, Sharpe, Sortino, MDD, VaR95, CVaR95);
  - stock news/disclosures via new `_kis_stock_news()`.
  Each section is independently `try/except`-guarded so a partial sheet still renders.
- **`_kis_stock_news(code, n)`** = KIS 종합시황·공시 **[141]** (`news-title`, tr_id
  `FHKST01011800`) with **`FID_INPUT_ISCD = code`** (spec: blank=all, code=that stock's
  news). 180s per-code cache; reuses the existing `_KIS_LOCK` rate-limit and token.
- **Grounded prompt:** system msg = "아래 [데이터]의 수치·뉴스만 근거로, 없는 것은 절대
  지어내지 말 것 … 3~4문장 … 마지막 줄 '※ 데이터 요약이며 투자조언이 아닙니다.'"; user
  msg = the data sheet + ask. Keeps `changes_5` model pick (`qwen3-4b-2507`), `max_tokens`,
  300s timeout, request-context-safe body read.
- **52-week range robustness:** compute low/high with `np.percentile(win, 1/99)` and clamp
  band to [0,100], instead of raw `min/max`. A single bad tick in the cached series was
  putting the 52w-low at an absurd value ("저점대비 +433%"); percentiles fix it with
  negligible effect on clean data.

## ✅ Verification (commands + observed output)
- End-to-end via Flask (`/api/llm_commentary` with `{code}`), keepalive `/__ping` loop:
  005930 and 000660 both returned commentary citing **real** momentum/risk numbers **and
  real KIS news headlines** (which the model cannot invent), plus the disclaimer. Latency
  first token 1.3–2.0s, total 4.1–5.0s (data gather + 4B generation). See `verified_by`.
- 52w percentile fix proven with a standalone numpy outlier test (numbers in `verified_by`).

## ⚠️ Notes & Pending Issues
- **Depends on LM Studio** running with `qwen3-4b-2507` (or any non-thinking model) loaded.
- **Headless test gotcha** still applies: the 15s `_PING_TIMEOUT` watchdog kills the server
  mid-stream without a `/__ping` keepalive (see `_STATUS.md` trap #8). Also the local shell
  `_safe_eval` hook is flaky on piped/network commands — run test clients via
  `run_in_background` writing to a file.
- **Data quality:** the commentary inherits the cached series' quirks (same data the M4
  quant tab uses). The 52w percentile guard mitigates single bad ticks; momentum at exact
  5/20/60d lags could still be skewed by a bad tick at that lag (rare).
- **Not included (was out of P1+P2 scope):** consensus/target-price, sector/KOSPI relative
  strength, CAPM beta, ETF-specific sheet (HHI/holdings). Natural next step = P4.
- **Naver news** was considered but the user chose KIS [141] only. `fetch_news` remains
  available if broader sentiment coverage is wanted later.
