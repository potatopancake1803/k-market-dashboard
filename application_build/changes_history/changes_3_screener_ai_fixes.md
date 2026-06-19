---
id: 3
title: Screener blank-screen fix + Local AI 500/timeout fix
date: 2026-06-11 14:25 KST
agent: Claude (Opus 4.8)
area: [screener, local-llm]
status: verified            # verified | partial | unverified | broken
files:
  - scripts/market_dashboard3_realtime.py
supersedes: [2]             # corrects the unverified "fixes" claimed in changes_2
verified_by: |
  GET /api/screener?q=momentum    -> 200 {"status":"ok"} 41 unique rows (uv env, pyarrow fallback path)
  duckdb dedup query (system py)  -> 41 rows, 41 unique codes (no duplicates)
  GET /screener_page              -> 200, no 'var(--label' present, has theme bootstrap
  POST /api/llm_commentary {}     -> 200 SSE "No prompt provided." (proves request-context bug gone)
  POST .../chat/completions warm  -> streamed reply OK (first token ~7.7s, model qwen3.5-9b)
---

# Screener blank-screen fix + Local AI 500/timeout fix

## 🛠️ What was done
Two user-reported "doesn't work" features were diagnosed to root cause and fixed in
`scripts/market_dashboard3_realtime.py` (the live backend the `.app` loads):

1. **Screener showed a blank white tab.** Three compounding causes, all fixed.
2. **Local AI commentary never worked** (always failed silently). Two bugs, both fixed.

No new dependencies added (duckdb/mlx were already in `requirements.txt`; pyarrow,
used by the new fallback, was already present everywhere).

## ⚙️ How it was done (Technical Details)

### Screener (`/api/screener`, `/screener_page`)
- **Cause A — runtime had no `duckdb`.** changes_2 installed duckdb into *system*
  python via `pip --break-system-packages`, but the app runs under uv / the frozen
  `.app` env, where `import duckdb` raised `No module named 'duckdb'`.
  - Fix: split the query into `_screener_rows_duckdb()` (fast path) and
    `_screener_rows_pandas()` (pyarrow/pandas fallback, always available). The
    endpoint tries duckdb, falls back on any exception. Both return identical
    `{code, current_price, ret_5d, volume_money}` dicts.
- **Cause B — duplicate rows.** A code can have several parquet files
  (`chart_005380_160.parquet`, `chart_005380_2400.parquet`). The old query joined
  `ranked t1 JOIN ranked t5 ON t1.code=t5.code`, producing a cartesian product across
  files → the same stock listed 4× (066570 appeared 4 times).
  - Fix: per code, select only the file with the most rows (longest history) before
    computing 5-day momentum. duckdb path uses `arg_max(filename, nrows)`; pandas
    path keeps `max(len(df))` per code. Result deduped to 41 unique codes.
- **Cause C — white-on-white iframe.** `/screener_page` is loaded as an `<iframe>`.
  Its CSS used `color: var(--label, #fff)`; `--label` is only defined in the *parent*
  document and does not cascade into the iframe → text fell back to `#fff` white on a
  `transparent` (white parent) background. Even the `Error: ...` fallback was white.
  - Fix: rewrote the page with **explicit** light/dark colors (`--ink`, `--sub`, …),
    a proper loading/empty/error state element, sticky header, tabular-nums, and the
    project-standard theme sync (`localStorage('kmkt-theme')` bootstrap +
    `window.message {kmkt}` listener — same-origin, identical to `/sector`,`/market`).
    Row click now uses `window.parent.miOpenStockTab(code)` (a guaranteed-on-`window`
    bridge) instead of `window.parent.pick` (a bare top-level fn, not always exposed).

### Local AI commentary (`POST /api/llm_commentary`)
- **Cause A — HTTP 500 on every call.** `req_data = request.json` was read *inside*
  the SSE generator `generate()`. Generators run lazily during response streaming,
  *after* the Flask request context is gone → `RuntimeError: Working outside of
  request context`. This made the feature 500 on every request — it never worked,
  despite changes_2 marking it fixed.
  - Fix: read `prompt = (request.get_json(silent=True) or {}).get("prompt","")` in the
    **view function body** (context alive) and close over it in `generate()`.
- **Cause B — `UnboundLocalError: json`.** `import json` sat inside the `try`; when the
  context error above fired on the first line, `json` was never bound, so the `except`
  handler's `json.dumps(...)` raised a *second* error that masked the first.
  - Fix: moved `import json` / `import urllib.request` to the top of the view function.
- **Cause C — `timeout=5.0` too short.** LM Studio JIT-loads the model on first
  request; first token measured at ~7.7s (9B) and can be far longer cold. 5s aborted
  mid-load.
  - Fix: chat-completions socket timeout `5.0 → 300.0`; models-list `2.0 → 5.0`.
  - Also: distinct, actionable Korean error messages for "server off" (connection
    refused / models-list fail → tells user to start LM Studio Local Server) vs.
    "timed out" (tells user to preload the model), vs. generic.

## ✅ Verification (commands + observed output)
Ran the backend under uv (`MARKET_PORT=8793`), which has **no duckdb** — deliberately
exercising the fallback path that the frozen `.app` would hit:

```
GET  /api/screener?q=momentum  -> {"status":"ok"}, 41 rows, e.g. LG전자/066570/+45.45%
duckdb dedup query (system py) -> 41 rows, 41 unique codes (dup 066570 gone)
pandas fallback (system py)    -> identical 41 rows, same top-8
GET  /screener_page            -> 200; 'var(--label' absent; 'kmkt-theme' + 'miOpenStockTab' present
POST /api/llm_commentary {}    -> 200 text/event-stream: data: {"text":"No prompt provided."}
   (this previously 500'd — proves the request-context bug is fixed)
POST 127.0.0.1:1234 warm chat  -> streamed a full Korean sentence (model qwen3.5-9b)
```

## ⚠️ Notes & Pending Issues
- **Local AI requires LM Studio running** with a model loaded; this is a precondition,
  not a bug. Recommend a small model (3–4B) + "keep model loaded" for snappy first
  response. Optional future work: warm the model on app boot (mirror `_prewarm`).
- **`.venv-build` still lacks duckdb/mlx.** Runtime is safe via the pyarrow fallback,
  but a clean `./build.sh` should pip-install `requirements.txt` so the fast duckdb
  path is bundled. Verify post-build with `GET /api/screener`.
- **Unverified by this session:** Spotlight, Dock menu, KIS snapshot fallback — left
  as-is; see `_STATUS.md` feature-health table.
