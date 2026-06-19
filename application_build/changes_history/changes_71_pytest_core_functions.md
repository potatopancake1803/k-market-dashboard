---
id: 71
title: Core pure-function regression tests (pytest) + changes_history consolidation + .gitignore key hardening
date: 2026-06-17 14:00 KST
agent: Claude (Opus 4.8)
area: [testing, ops, security]
status: verified
files:
  - tests/test_core_functions.py
  - .gitignore
  - application_build/CLAUDE.md
  - application_build/changes_history/_STATUS.md
  - changes_history/MOVED.md
  - application_build/changes_history/changes_62..70_*.md (consolidated copies)
---

## What was done

Implemented the first three actionable items from the external technical review
(`TECH_REVIEW_2026-06-17.md`), all low-risk / no production-logic change:

1. **Core pure-function regression tests** — `tests/test_core_functions.py` (new),
   26 tests, network-free, all passing.
2. **`.gitignore` API-key hardening** (review #5) — broadened env/key ignore rules.
3. **`미검증(❓) 소거 대기열`** (review #2) — new tracking section in `_STATUS.md`
   + one line added to the Operating Loop in `CLAUDE.md`.
4. **`changes_history` fork consolidation** (review #7) — root dir `changes_7..15`
   copied + renumbered into the canonical dir as `changes_62..70`; root left a
   `MOVED.md` redirect; originals preserved (copy, not move).

(The `_inject_*` failure-logging item from the review is logged separately in
`changes_72_inject_failure_logging.md`.)

## How it was done

### 1. tests/test_core_functions.py
- Targets 6 deterministic helpers in `scripts/market_dashboard3_realtime.py`:
  - `_krx_won(v)` — 억/조 scale formatter (the **scale-bug guard**). NOTE: the review
    named `fmtMcap`, but `fmtMcap` is a **JavaScript** function inside an HTML string
    (~line 10471) with **no Python equivalent** — `_krx_won` is the Python analogue and
    is tested instead. Documented in the test file header.
  - `_cu(v, dec, sign)` — count-up `<b class="cu" data-to=… data-dec=… data-sign=…>` span.
  - `_risk_stats(closes)` — Sharpe/Sortino/VaR/CVaR/MDD. Verified by (a) re-deriving
    `sharpe = mu/sd*sqrt(252)` from the same series and asserting equality, (b) a known
    -50% drawdown → MDD ≈ -50, (c) CVaR ≤ VaR tail property, (d) short-series safety.
  - `_clean_closes(rows)` — extracts/sorts 종가 from `[{일자,종가}]`; tests sort,
    comma-numbers, empty list, missing column, non-positive drop.
  - `_is_open_day(d)` — weekend fallback + holiday-map override (monkeypatch
    `_load_holidays` to `{}` / `{"20260615":"N"}` so the test is network-free & deterministic).
  - `_sse_progress/_sse_done/_sse_failed` — SSE frame format. NOTE: the review assumed
    output "starts with `data:`"; the real frame is `event: X\ndata: {json}\n\n`, so the
    tests assert the **actual** format (starts with `event:`, parseable `data:` JSON line,
    `ensure_ascii=False` Korean not escaped).
- **Import isolation (trap #35):** importing the backend eagerly runs
  `from archive import company_report_ver2/etf_dashboard_ver2`, which pull in
  `market_intel/report/dashboard.py:692` — a **Python 3.12-only** backslash-in-f-string
  that fails to compile on 3.10/3.11. Since the 6 target functions are pure and don't
  depend on those legacy modules, the test pre-seeds `sys.modules` with lightweight
  `archive*` stubs **before** importing the backend. On real 3.12+ runtimes the genuine
  modules import normally and the stubs are unused.
- PEP723 header lists pytest+numpy+pandas+pyarrow **and** the backend's import-time
  deps (httpx/flask/plotly/scipy/dotenv/lxml/polars/websockets) so
  `uv run tests/test_core_functions.py` is self-contained.

### 2. .gitignore
- Added an "API Keys" block: `*.env`, `**/*.env`, `**/API.env`, `api_documents/API.env`,
  `**/API_Key_*.env`, `**/한국투자증권/`. Previously only bare `.env` was ignored, leaving
  `api_documents/API.env`, root `API.env`, and the KIS key env exposed to an accidental
  `git add .`.

### 3 & 4. _STATUS.md / CLAUDE.md / consolidation
- `_STATUS.md`: header (last-updated, latest-entry), drift warning flipped to RESOLVED,
  4 new feature-health rows (tests/inject-logging/gitignore/consolidation), new
  "미검증 소거 대기열" section (24 ❓ items), Active Trap #35.
- `CLAUDE.md` §2: added step 0 "CLEAR DEBT" — verify ≥1 queue item at session start.
- Consolidation done by a Python script (read each root `changes_7..15`, inject an
  "이전 위치 / 통합일 / 재넘버링" provenance block after frontmatter, write as
  `changes_62..70`). Internal `id:` left as historical 7–15 by design; filename = new number.

## Verification

```
$ uv run --python 3.10 --with pytest --with numpy --with pandas --with pyarrow \
    --with httpx --with flask --with plotly --with scipy --with python-dotenv \
    --with lxml --with polars --with websockets \
    python -m pytest tests/test_core_functions.py -v
...
26 passed in 0.23s
```
- All 26 tests pass on Python 3.10 (sandbox). Re-ran after the changes_72 edits to the
  backend — still 26 passed (no regression).
- Consolidation: `ls application_build/changes_history/ | grep -E 'changes_(6[2-9]|70)_'`
  → 9 files present; root `changes_history/` still has its 9 originals + new `MOVED.md`.

## Notes & Traps

- **NEW TRAP #35 (added to _STATUS.md):** codebase uses Python 3.12-only f-string syntax
  (`dashboard.py:692`); importing the backend on 3.10/3.11 is a hard SyntaxError. Real app
  runtime is 3.12+ so it's harmless there, but any headless 3.10 tooling must isolate it
  (the test does, via sys.modules stubs).
- `.gitignore` rules are correct but could **not** be confirmed with `git check-ignore`
  here — the sandbox mount is not a git work-tree (`fatal: not a git repository`). No env/key
  files are currently tracked. Recommend the user run `git check-ignore -v .env
  api_documents/API.env` on the real machine once.
- **Out-of-scope finding (not fixed — recorded per §8):** `fmtMcap` scale logic lives only
  in JS and has no Python test path; if that JS formatter ever regresses (it already did once,
  trap #27), Python tests won't catch it. A future JS test harness (node) would be needed.
- Numbering: review suggested `changes_62/63` for these logs, but 62–70 were taken by the
  consolidation, so this is `changes_71` and the inject-logging log is `changes_72`.
