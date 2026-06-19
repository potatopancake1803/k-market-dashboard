---
id: 7
title: AI commentary news fix — [141] iscd filter (stop cross-stock misattribution)
date: 2026-06-11 17:30 KST
agent: Claude (Opus 4.8)
area: [local-llm]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: [6]
verified_by: |
  Diagnosis (urllib-only client reusing cached KIS token, [141] for 009150):
    40 rows returned, but FID_INPUT_ISCD=009150 did NOT filter — rows were tagged
    iscd=005930 / 000660 / KOSPI market news; only 1 row actually tagged 009150.
    => model was attributing Samsung Electronics / market news to Samsung Electro-Mechanics
       ("삼전닉스" hallucinated link).
  After-fix filter applied to the same live [141] response (no LLM):
    009150 now yields REAL 삼성전기 news only —
    "삼성전기, 5%대 약세…차익실현 매물", "삼성전기(009150) -5.82%",
    "ABF·MLCC 기술 경쟁력 갖춘 유일한 삼성전기", "삼성전기 목표주가 240만원".
  End-to-end: server up + /api/llm_commentary 009150 -> commentary now grounded in
    real 삼성전기 headlines; 삼성전자/시장 뉴스 오귀속 제거.
  This session: re-confirmed the iscd filter (lines 2997-3003) is present and the
    backend compiles (python3 -m py_compile -> OK).
---

# AI commentary news fix — [141] iscd filter

> **Recording a task completed in a separate conversation** (the originating session
> ran the diagnostics and end-to-end check below). This entry corrects/continues
> `changes_6`, where `_kis_stock_news()` was introduced believing `FID_INPUT_ISCD=code`
> would return only that stock's news. It does not.

## 🛠️ What was done
Fixed `_kis_stock_news()` so AI commentary for a given stock cites **only that stock's**
news, instead of leaking large-cap / market-wide headlines. Trigger: 삼성전기(009150)
commentary was weakly news-grounded and pulled in Samsung Electronics ("삼전닉스") and
KOSPI market news that the model then misattributed to 삼성전기.

## ⚙️ How it was done (Technical Details)
- **Root cause:** KIS 종합시황·공시 **[141]** (`news-title`, tr_id `FHKST01011800`) does
  **not** honor `FID_INPUT_ISCD` as a hard per-stock filter — it returns market / large-cap
  news regardless. `changes_6` assumed it filtered by code, so for 009150 the first ~12 of
  40 rows were 005930 / 000660 / KOSPI items. 005930·000660 commentary *looked* correct only
  because those large-cap headlines happened to be genuinely theirs (coincidence).
- **Fix** (`scripts/market_dashboard3_realtime.py`, `_kis_stock_news`, lines ~2997–3003):
  after the title check, build `row_codes = {str(o.get(f"iscd{i}")) for i in range(1,11)}`
  from each row's `iscd1..iscd10` tag fields and **keep the row only if the target `code`
  is in that set** (`if code not in row_codes: continue`). No tag match → row dropped. If a
  stock genuinely has no [141] news, the news section is simply omitted (honest, no
  fabrication) rather than padded with someone else's headlines.
- Also widened the scan to all 40 returned rows (then `break` at `n` kept matches), since
  the real 009150 items were buried *after* the first 12 market rows.
- **Non-fix (deliberately left alone):** "60일 모멘텀 +350%" looked like a bad tick but is
  **correct for this dataset** — the app runs on a **simulated/future** dataset (KOSPI
  ~7,721; 삼성전기 ~1.8M KRW), and [141] itself mentions "목표주가 240만원", consistent with
  ~1.8M. So the momentum magnitude is dataset-real, not a bug. No change to the series.

## ✅ Verification (commands + observed output)
- **Diagnostic** (originating session): a urllib-only client reusing the cached KIS token
  hit [141] for 009150 → 40 rows, almost all tagged 005930 / 000660 / market; only 1 row
  tagged 009150. Confirmed the filter was effectively a no-op.
- **After-fix, same live response, no LLM:** 009150 now yields real 삼성전기 headlines only
  (list in `verified_by`); 005930 still retains its (real) news.
- **End-to-end:** server up, `/api/llm_commentary` for 009150 → commentary grounded in the
  real 삼성전기 headlines; the 삼성전자/시장 misattribution ("삼전닉스") is gone.
- **This session:** re-confirmed the iscd filter block is present in the source and the
  backend compiles (`python3 -m py_compile … → COMPILE_OK`). Behavioral evidence above is
  from the originating session, not re-run here (LM Studio not exercised this session).

## ⚠️ Notes & Pending Issues
- Still **LM Studio-dependent** for live commentary (same precondition as `changes_6`).
- [141]'s loose filtering is a **KIS API behavior**, not ours — any future use of that
  endpoint per-stock must apply the same `iscd1..10` row filter, or it will leak market news.
- The dataset is **simulated/future**; do not "fix" large momentum/price magnitudes as if
  they were bad ticks. The 52-week percentile guard from `changes_6` still handles genuine
  single bad ticks.
- Headless-test gotchas from `changes_6`/traps #7,#8 still apply (shell `_safe_eval` flaky;
  15s `/__ping` watchdog kills unkept-alive test servers).
