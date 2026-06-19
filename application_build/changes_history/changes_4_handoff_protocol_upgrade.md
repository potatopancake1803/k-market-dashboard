---
id: 4
title: Handoff protocol upgrade — mandatory Operating Loop, living _STATUS.md, frontmatter + verification
date: 2026-06-11 15:05 KST
agent: Claude (Opus 4.8)
area: [process, docs]
status: verified
files:
  - application_build/CLAUDE.md
  - application_build/changes_history/_STATUS.md
  - application_build/changes_history/changes_0_add_screener_spotlight_dock.md
  - application_build/changes_history/changes_1_add_local_llm_and_snapshot.md
  - application_build/changes_history/changes_2_bugfixes.md
supersedes: []
verified_by: |
  All referenced files exist and are internally consistent (read order, frontmatter
  schema, and feature-health table cross-reference the same change ids).
  changes_0/1/2 now carry retrofitted frontmatter; changes_2 carries a correction notice.
---

# Handoff protocol upgrade

## 🛠️ What was done
Reworked how LLM agents coordinate on `application_build/`, so the next agent
**reads context before acting and logs/verifies automatically** instead of relying on
the user to prompt either. Motivated by a concrete failure: `changes_2` logged the
screener and local-AI as "fixed" while both were still 100% broken (see `changes_3`).

Changes:
- **`application_build/CLAUDE.md`**: added a top-level **"🔁 The Operating Loop —
  MANDATORY, EVERY TASK"** section (READ → DIAGNOSE → ACT → VERIFY → RECORD), framed to
  make the agent proactive, root-cause-driven, and honest about verification. Kept the
  earlier "Read Order", frontmatter schema, mandatory `✅ Verification` section, and the
  "update `_STATUS.md` in the same session" rule.
- **`changes_history/_STATUS.md`** (created earlier this session): the living source of
  truth — run commands, feature-health table, active traps, correction log. Read first,
  updated every session.
- **Retrofitted** `changes_0/1/2` with YAML frontmatter; added a **correction notice** to
  `changes_2` pointing to the real root causes and to `changes_3`.

## ⚙️ How it was done (Technical Details)
The format is optimized for machine consumption: greppable YAML frontmatter
(`id/title/date/agent/area/status/files/supersedes/verified_by`) lets an agent assess
state without reading prose; the feature-health table in `_STATUS.md` gives a one-glance
✅/⚠️/❌/❓ view keyed to change ids; the correction log breaks the "trust a stale
'fixed' claim" failure chain. History entries (`changes_X_*.md`) are immutable; a wrong
past entry is corrected by a *new* entry via `supersedes:` plus a `_STATUS.md` correction
line, never by silent rewrite. The Operating Loop makes step 4 (VERIFY, with observed
output) and step 5 (RECORD, automatically) preconditions for calling a task "done".

## ✅ Verification (commands + observed output)
This is a documentation/process change (no code), so verification = artifact existence
and internal consistency:
- `_STATUS.md`, `changes_3`, `changes_4` exist; `changes_0/1/2` now begin with frontmatter.
- Cross-references resolve: `_STATUS.md` correction log ↔ `changes_2` notice ↔ `changes_3`
  fixes all name the same root causes (request-context 500, white-on-white iframe, duckdb
  missing in runtime).
- Backend code unchanged by this entry; `python3 -m py_compile market_dashboard3_realtime.py`
  still passes (from `changes_3`).

## ⚠️ Notes & Pending Issues
- This protocol governs `application_build/`. The repo-root `CLAUDE.md`/`HANDOFF.md`
  cover the broader project and were intentionally left untouched; if cross-agent routing
  needs it, add a one-line pointer there to this Operating Loop.
- Local-AI follow-up work is **paused** at the user's request (the `changes_3` fixes
  stand; optional boot-time model warmup is not implemented).
