---
id: 77
title: Split inline templates → ui_templates.py (-40% main) + smoke_check regression gate + DEBUG_JOURNAL + guideline overhaul
date: 2026-06-17 20:30 KST
agent: Claude (Opus 4.8)
area: [refactor, tooling, process, docs]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - scripts/ui_templates.py (new)
  - scripts/smoke_check.py (new)
  - scripts/gen_codemap.py
  - tests/golden_render.json (new)
  - docs/DEBUG_JOURNAL.md (new)
  - docs/CODEMAP.md (regenerated)
  - CLAUDE.md (root) + application_build/CLAUDE.md
---

## What was done
A four-part change to make the project **safe to refactor** and to make AI-agent work
**cumulative** (stop re-debugging the same errors / breaking things on fixes).

### 1) Regression gate — `scripts/smoke_check.py` (built FIRST, before touching code)
Network-free gate: imports the live backend (catches changes_73-class import breaks), boots a
Flask test client, GETs 10 critical static routes (200), asserts injection invariants
(`kmktAI`/`kmkt-ai-bar` present), and compares rendered output of 9 static pages to a golden
hash baseline `tests/golden_render.json`. Has PEP723 deps header so `uv run` provisions the env.
`--golden write` snapshots a new baseline. Exit 0/1 for CI.

### 2) File split — inline templates → `scripts/ui_templates.py`
- The backend was 13,166 lines / 736 KB, **~50% of it inline HTML/CSS/JS template strings** →
  too big for one agent context window (root cause behind several silent regressions).
- Extracted all **20 template constants** (`_LANDING_HTML`, `_OVERSEAS_HTML`, `_ASK_WIDGET_HTML`,
  `_REALTIME_HTML`, … `_FX_STYLE`, `_M4_WIRE`, …) into `scripts/ui_templates.py`.
- **Safe because** all 20 are plain/raw string CONSTANTS (no f-string interpolation — verified via
  ast), extracted **byte-exact** by source slicing (preserves `r` prefix), and the main file still
  holds all the `.replace(...)` / `_inject_*` ASSEMBLY which runs after `from ui_templates import …`.
- Extraction done by a throwaway ast script (now deleted) + a pre-edit backup (now deleted after
  verification). Main file: **13,166 → 7,946 lines (−40%)**; `ui_templates.py` = 5,270 lines.
- Edit a page's markup in `ui_templates.py`; edit wiring/logic in the main file.

### 3) Learning system — `docs/DEBUG_JOURNAL.md`
Append-only, **symptom-first** error→fix log so agents grep a symptom instead of re-diagnosing.
Seeded with 9 recurring issues (import regression, dark-mode white page, SSE-500, local-LLM
no-tools, reasoning-model 0-chars, Gemini-429, raw-string `\n`, watchdog-kills-headless, 3.12 syntax).
Protocol: grep it first; append after any ≥1-cycle/non-obvious error; promote durable rules to traps.

### 4) Guideline overhaul (the user's "rewrite the working method")
- Root `CLAUDE.md`: new **"작업 운영 체계 — 지능형 학습·오류 구조"** section (loop + smoke gate +
  debug journal + **structure→guideline-sync rule** + a doc-map table); §0 updated for the split.
- `application_build/CLAUDE.md`: §2.4 VERIFY now mandates `smoke_check`; §2.5 RECORD mandates
  journal append + guideline sync; §5 documents the gate as real evidence; **new §12** "Structure
  changes → guideline sync + regression gate (mandatory)".
- `gen_codemap.py` now scans `ui_templates.py` for templates; `docs/CODEMAP.md` regenerated.

## Verification
```
$ python3 -m py_compile scripts/ui_templates.py scripts/market_dashboard3_realtime.py   # OK
$ uv run scripts/smoke_check.py
  · import backend OK
  · Flask test client OK
  · 10 routes returned 200
  · golden compared (9 routes)        ← rendered output BYTE-IDENTICAL after the split
  SMOKE PASS ✓
# extra: /overseas /world_page /sector /market /screener_page /world_detail → all 200
# live: preview boot OK; landing + AI Gemini bar + model menu (6 items) + 6 cards render
$ python3 scripts/gen_codemap.py    # WROTE docs/CODEMAP.md — 71 routes, 20 templates
```
Golden baseline was written from the CURRENT (post-changes_75 AI-widget) state, then the split was
proven to leave all 9 hashed pages identical. Main line count 13,166 → 7,946.

## Notes & Traps
- **`scripts/ui_templates.py` holds ONLY template constants — no logic.** Assembly/injection stays
  in the main file. Both run with `scripts/` on `sys.path` (script dir / app.py / smoke_check all add it).
- After any intentional markup edit, the golden compare will fail by design → re-baseline with
  `uv run scripts/smoke_check.py --golden write` and note it (else next agent sees a false failure).
- `docs/CODEMAP.md` line numbers shifted (main shrank); regenerate after big edits.
- Did NOT split routes into Blueprints or extract logic modules — that's the next Tier-L step
  (see `docs/MAINTAINABILITY_AUDIT_2026-06-17.md` §5). The template split was the highest-reward,
  lowest-risk slice and is fully gated now.
