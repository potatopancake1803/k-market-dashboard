---
id: 85
title: Dev Mode richer capture (computed styles + chart hint) + proactive structural health monitor + auto doc-sync rule
date: 2026-06-17 21:30 KST
agent: Claude (Opus 4.8)
area: [dx, process, tooling]
status: verified
files:
  - scripts/dev_overlay.py
  - scripts/health_check.py (new)
  - CLAUDE.md (root) + application_build/CLAUDE.md
  - application_build/changes_history/_STATUS.md
---

## Why (retrospective on processing session #1, changes_84)
Retracing the 4-task session showed *where* tokens still went after the dev note:
- For id'd elements (Task 1 `#hChg`, Task 4 `#rcv`) the note's file:line was enough → near-zero locate.
- For **chart-internal SVG** (Task 2 Plotly `<rect>`, Task 3 treemap `<path>`) the note gave weak/empty
  candidates → cold-grep for the chart config (`_marketmap_fig`, Plotly `layout`).
- For visual tweaks I had to **guess current CSS values** (letter-spacing/padding) — no current-state info.

## What was done
### 1) Dev Mode — richer capture (작업1)
- **Computed styles**: `pickStyles(el)` captures the key CSS (color/font-size/weight/letter-spacing/
  padding/margin/radius/opacity/…, skipping defaults) → shown in the popover + saved in the note
  (`현재 스타일:` line). The agent now edits from the *actual* values, no guessing.
- **Chart detection**: `chartKind(el)` flags Plotly/canvas/SVG elements. The popover shows a `📊 chart`
  row ("설정 코드를 고쳐라"), the note adds a hint pointing to chart config
  (`Plotly.react` layout / `lineChart` / backend `go.Figure`·`go.Treemap` in `_*_fig`), and an anchor
  is added for id-less chart elements. Kills the cold-grep for Task 2/3-type captures.

### 2) Proactive structural health monitor — `scripts/health_check.py` (작업2)
The self-learning docs (`_STATUS`/`DEBUG_JOURNAL`/`CODEMAP`/gates) *preserve* learning and *catch
regressions* (reactive). Missing: a layer that notices the structure drifting back toward inefficiency
and **prompts a redesign**. `health_check.py` (stdlib, instant) measures creep + drift metrics vs
thresholds and emits ⚠️ WARN + a concrete suggestion:
- main backend size (>9000L → extract), biggest top-level function (>420L → split), route density
  (>90 → Blueprint), `_STATUS` ❓ backlog (>30), **CODEMAP route-count drift**, **`_STATUS` latest-entry
  drift vs actual max changes_X**, `dev_notes` backlog, Dev-Mode source-list existence, golden present.
- Protocol: run at session start / after structural change; **on WARN, surface to user + propose
  redesign** (Tier-L → approval + plan + gates; never silent refactor). This is the agent's *proactive*
  path to an efficient structure, not just preserving the current one.

### 3) Auto doc-sync rule (작업3)
- Root `CLAUDE.md` 운영체계: device #4 now explicitly says **구조 OR 작동방식 변경 시 root `CLAUDE.md`
  + `application_build/CLAUDE.md` 둘 다 갱신**; added **device #5 (능동 구조 점검)**.
- `application_build/CLAUDE.md` §12 gained rule 3 (health_check + proactive proposal) + the both-files
  doc-sync line. `_STATUS` How-to-run + root doc-map list `health_check.py`.

## Verification
```
$ python3 -m py_compile scripts/dev_overlay.py scripts/health_check.py → OK
$ node --check (overlay JS) → OK
$ uv run scripts/smoke_check.py → SMOKE PASS ✓ (dev changes are KMKT_DEV-gated → golden unchanged)
$ python3 scripts/health_check.py → all ✅ (main 7,959L · largest fn _gen_stock_quant 304L · 78 routes ·
  ❓=28/30 (near threshold — surfaced) · CODEMAP & _STATUS in sync · dev_notes 0 · golden present)
```

## Notes & Traps
- health_check is **advisory** (exit 0); it does not block. The agent reads it and proposes — the user
  decides. Tune thresholds at the top of the file as the project grows.
- ❓ unverified is at 28/30 — the monitor is already near-warning; the 미검증 소거 대기열 should be worked down.
- Token-savings review for Dev Mode: see this session's chat summary (locate phase eliminated for id'd
  elements; chart hint + computed styles close the remaining gaps).
