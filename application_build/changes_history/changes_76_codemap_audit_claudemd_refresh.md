---
id: 76
title: Agent-maintainability — CODEMAP line-index + maintainability audit + root CLAUDE.md refresh
date: 2026-06-17 19:20 KST
agent: Claude (Opus 4.8)
area: [docs, maintainability, tooling]
status: verified
files:
  - docs/CODEMAP.md (new)
  - scripts/gen_codemap.py (new)
  - docs/MAINTAINABILITY_AUDIT_2026-06-17.md (new)
  - CLAUDE.md (root — refreshed sections 0/1)
---

## What was done
Addressed the user's request to (a) audit the Python skeleton's efficiency + AI-coding-agent
maintainability (token waste / context-limit risk), and (b) check & refresh the root CLAUDE.md.

### 1) `docs/CODEMAP.md` + `scripts/gen_codemap.py` (new — the high-leverage fix)
- The backend is a single **13,166-line / 736 KB** file; **~50% of it (≈341K chars) is inline
  HTML/CSS/JS template strings**. That's ~180K tokens — it does **not fit in one context window**,
  so an agent must grep/partial-read and risks editing one region while missing a coupled one.
- `CODEMAP.md` is an auto-generated **navigation index**: every route (71, grouped by path
  prefix), inline template (20, with size), and `_inject_*` hook (8) listed **with line numbers**,
  so an agent does `Read(offset=…, limit=…)` instead of reading the whole file → saves tokens,
  dodges the context limit.
- `gen_codemap.py` regenerates it (`python3 scripts/gen_codemap.py`). 3.10-compatible
  (no backslash-in-f-string; avoids trap #35). Verified: emits "71 routes, 20 templates".

### 2) `docs/MAINTAINABILITY_AUDIT_2026-06-17.md` (new)
- Focused companion to `TECH_REVIEW_2026-06-17.md`, specifically on **agent maintainability**.
- Findings: runtime Python efficiency is **fine for a single-user local app** (static pages
  assembled once at import, 155 TTL caches, `threaded=True` for SSE). The real cost is the
  single-file size (3-1), 50%-markup token waste (3-2), no navigation scaffolding (3-3, now
  mitigated by CODEMAP), fragile string-anchor injection (3-4), and weak verification (3-5,
  reinforced by the changes_73→74 regression).
- Recommendations ranked by risk/reward; flags template extraction + Blueprint split as
  **Tier-L (plan-first, do NOT start without user approval + per-page visual verify)**.

### 3) Root `CLAUDE.md` refresh (sections 0 & 1)
- Was dated 2026-06-05 and named `market_dashboard3.py` as the entry file — **stale**. The live
  entry is `scripts/market_dashboard3_realtime.py` (loaded by `app.py`); the old files were
  archived in changes_73.
- Rewrote the banner into a **canonical read-order pointer** (application_build/CLAUDE.md →
  _STATUS.md → CODEMAP → changes/HANDOFF) so the root file is a thin index, not a duplicate
  stale snapshot (duplication was the source of past drift).
- Rewrote section 0 file-structure to post-changes_73 reality (scripts/, scripts/archive/,
  application_build/, docs/, tests/) + added the import-path trap (#38), the 3.12-syntax trap
  (#35), and the dual-`.env` trap (#36). Fixed the stale run command in section 13.
- Decision: did **not** duplicate the new feature catalog (realtime/KIS/AI/overseas/world/…)
  into root CLAUDE.md — those live in `_STATUS.md`/`CODEMAP.md`/`HANDOFF.md`; pointing avoids drift.

## Verification
```
$ python3 -m py_compile scripts/gen_codemap.py            # OK
$ python3 scripts/gen_codemap.py                          # WROTE docs/CODEMAP.md — 71 routes, 20 templates
# root CLAUDE.md: all 5 linked docs exist (application_build/CLAUDE.md, _STATUS.md, CODEMAP.md,
#   MAINTAINABILITY_AUDIT, HANDOFF.md); no remaining bare `market_dashboard3.py` run refs.
```

## Notes & Traps
- `CODEMAP.md` line numbers drift on edit — regenerate with `gen_codemap.py` after large changes.
  Consider wiring it into `build.sh` or a pre-commit later (not done — keep it manual for now).
- The audit's Tier-L recommendations (template extraction, Blueprints, comment anchors) are
  **not** implemented this session by design (need user approval + a plan file + visual verify).
