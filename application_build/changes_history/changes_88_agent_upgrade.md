---
id: 88
title: Agent self-improvement automation TIER 1 — Hooks regression gate + guarded reflect
date: 2026-06-19 KST
agent: Claude (Opus 4.8)
status: verified
supersedes: []
files:
  - .claude/settings.json
  - scripts/hooks/gate_dispatch.py
  - scripts/hooks/session_brief.py
  - scripts/reflect/capture.py
  - scripts/reflect/apply.py
  - application_build/changes_history/changes_88_plan_agent_upgrade.md
  - application_build/changes_history/_STATUS.md
  - CLAUDE.md
  - application_build/CLAUDE.md
---

## What was done
Implemented **TIER 1 only** of the agent-upgrade plan (`changes_88_plan_agent_upgrade.md`).
TIER 2/3 remain proposal/deferred (see the plan). Two automations, each gated by `smoke_check`:

- **1-A — Claude Code Hooks auto-enforce the regression gate.**
  - `.claude/settings.json` (NEW; `launch.json` untouched) wires three hook events.
  - `scripts/hooks/gate_dispatch.py` (NEW): `PostToolUse(Edit|Write|MultiEdit)` → `mark`
    drops a sentinel only when a backend-graph file changes; `Stop` → `gate` runs
    `smoke_check` at most once per turn and exits 2 (blocks turn-end) on FAIL.
  - `scripts/hooks/session_brief.py` (NEW): `SessionStart` injects a capped ~9-line digest
    (health WARNs + dev_notes backlog + 5 newest trap headlines) instead of re-reading the
    444-line `_STATUS.md`.
- **1-B — Guarded auto-reflect (custom wrapper, NOT the claude-reflect plugin).**
  - `scripts/reflect/capture.py` (NEW): `UserPromptSubmit` hook; deterministic multilingual
    regex scores user corrections (floor 0.75) → appends to `_autoreflect/queue.jsonl`. Never
    edits docs, never blocks.
  - `scripts/reflect/apply.py` (NEW): `Stop` hook; drains the queue with the 3 mandatory guards
    + 2-tier confidence gating. Default `DEFAULT_MODE="propose"` (everything → `dev_notes/`);
    `KMKT_REFLECT_MODE=auto` enables canonical writes for conf ≥ 0.90.
  - `_STATUS.md` / root `CLAUDE.md` / `application_build/CLAUDE.md` updated (this change alters
    the working method → §12 doc-sync).

## How it was done
**1-A frequency design (token efficiency).** `smoke_check` measured at 1.13s, network-free,
~5-line PASS output. Chose **sentinel + Stop** over per-edit: `mark` is silent/instant and only
sets `~/.cache/kmkt_m4/.smoke_dirty` when the edited path is `scripts/*.py` directly under
`scripts/` or `scripts/archive/*.py` (the backend import graph + live builders, trap #38).
Subdirs `scripts/hooks/` and `scripts/reflect/` are intentionally NOT gated (not imported by the
backend). `gate` runs the check once per turn, clears the sentinel, and on FAIL writes the smoke
output to stderr + exit 2 so Claude Code feeds it back and blocks the Stop. A `stop_hook_active`
guard prevents an infinite Stop loop (reports but does not re-block). All hooks fail **open**.

**1-B build-vs-adopt.** Researched `BayramAnnakov/claude-reflect`: it is a plugin whose apply is
*manual* (`/reflect`), whose sync globs `./**/CLAUDE.md` (would hit BOTH root and
`application_build` CLAUDE.md + AGENTS.md → the dual-source drift this project forbids), and 2 of
its 4 hooks are git-dependent (inert here — no `.git`). Per the plan's fallback clause, built a
stdlib custom wrapper instead. The 3 guards on a canonical write:
1. **Backup** `_STATUS.md` → `_autoreflect/_STATUS_bak_YYYYMMDD_HHMM.md` (only rollback path; no git).
2. **Integrity gate = structural validator AND `smoke_check`** + non-shrink check. Key nuance the
   plan corrected: `_STATUS.md` is not imported by the backend, so `smoke_check` alone cannot
   detect a corrupted doc — the structural validator (required sections present, file did not
   shrink, UTF-8 parses) is the real doc check. If EITHER fails → auto-restore from the backup.
3. **Provenance** → `_autoreflect_log.md` (who/what/why/confidence/result).
Auto content lands in a dedicated end-of-file `## ▶ Auto-reflect log` section, NOT inside the
human-curated numbered Active-Traps list (auto-numbering that list would risk corrupting the
project's highest-value index); a reviewer promotes good entries later. Low-conf / propose-mode
items become `dev_notes/*_autoreflect_*.md` review notes in the existing capture format (unified
with the dev_notes queue — no parallel system). `apply.py --undo` restores the newest backup
("방금 자동수정 되돌려"); `apply.py --list` shows the queue.

## Verification
All observed this session (commands via `uv run` / `python3`, hook inputs simulated by piping the
exact JSON Claude Code sends):

1-A:
- `python3 -m py_compile` both hook scripts; `.claude/settings.json` + `launch.json` valid JSON.
- `mark` with gated file `scripts/ui_templates.py` → sentinel created; with `_STATUS.md` (doc) and
  with `scripts/hooks/gate_dispatch.py` (subdir) → NO sentinel (correctly excluded).
- `gate` with sentinel + intact golden → `rc=0`, prints `[gate] SMOKE PASS ✓`, sentinel cleared.
- `gate` with a real induced break (one golden hash flipped) → `rc=2` with smoke output on stderr.
- `gate` with `stop_hook_active=true` while failing → `rc=0` + "not re-blocking" (no wedge).
- `session_brief.py` → 9-line digest: the live health WARN (`_STATUS` latest-entry drift), the
  dev_notes backlog line, and the 5 newest trap headlines (#41–#37). Golden restored after tests.

1-B (with a sha256 snapshot of `_STATUS.md` asserted byte-identical before/after):
- capture: `아니 그거 말고…`→0.92, `don't…instead`→0.80, `instead of…`→0.80, `그게 아니야`→0.78;
  a plain feature request → not queued. (4 queued, 1 skipped.)
- apply propose (default) → all 4 routed to `dev_notes/*_autoreflect_*.md`, queue cleared, log written.
- apply auto + high-conf → guarded append to `_STATUS.md` (auto-section added, required sections
  intact), log `APPLIED`; `--undo` restored `_STATUS.md` to the original hash.
- **apply auto + induced smoke failure (corrupted golden) → `_STATUS.md` auto-rolled-back to the
  original hash, log `ROLLED-BACK` with the real `GOLDEN MISMATCH` reason.** (The most important guard.)
- Cleanup verified: `_STATUS.md` final sha256 == original; queue/log/backups + test dev_notes removed.

Final gate: `uv run scripts/smoke_check.py` → `SMOKE PASS ✓` (golden 9 routes, 10 routes 200).

## Notes & Traps
- **New trap (added to `_STATUS.md` Active Traps #42):** reflect auto-doc-edit policy — high-conf
  (≥0.90) + `KMKT_REFLECT_MODE=auto` appends to a fenced `## ▶ Auto-reflect log` section of
  `_STATUS.md` ONLY (never the numbered trap list, never both CLAUDE.md files); low-conf/propose →
  `dev_notes/`. Every auto write = backup → structure-preserving append → (structural validator AND
  smoke_check, + non-shrink) → provenance log, with auto-rollback on gate failure. **smoke_check
  alone does NOT validate a doc edit** (docs aren't imported) — the structural validator is the doc check.
- **Default is `propose` mode** — no canonical doc is auto-edited until a human flips
  `DEFAULT_MODE` (scripts/reflect/apply.py) or sets `KMKT_REFLECT_MODE=auto`. Flip only after the
  captured-correction quality is observed to be good.
- **No `market_dashboard.spec` hiddenimports change** and **no CODEMAP regen**: `scripts/hooks/` and
  `scripts/reflect/` are hook entrypoints invoked by Claude Code, NOT imported by the dynamically
  loaded backend, so they do not enter the frozen-app import graph and do not affect the line index.
- Hooks run arbitrary local commands by design; the command set here is fixed and reviewed, stdlib-only.
- TIER 2 (claude-mem PoC, self-improve skills) and TIER 3 (wshobson patterns, GitHub PR review —
  blocked: no `.git`) remain **not built**; see the plan file for the proposals.
- Unrelated pre-existing item surfaced by the session digest: one unprocessed dev_note
  `dev_notes/session_20260618_1441_새-세션.md` (투자의견 수치 on `/dashboard?q=402340`) — out of scope here.
