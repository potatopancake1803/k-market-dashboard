# AI Agent Guidelines — CLAUDE.md Template

> Copy to your project root as `CLAUDE.md`.
> Fill `<!-- CUSTOMIZE -->` sections. Delete this line when done.

---

## 1. Session Start — Read Order

Every session, read **only what you need**:

| Situation | Read |
|-----------|------|
| Starting any task | `CLAUDE.md` + `changes_history/_STATUS.md` |
| Continuing a partial/unverified task | + last 2 history files (highest X) |
| Debugging a regression | + last 3 history files (highest X) |
| **Never** | All history files ascending — context budget waste |

`_STATUS.md` is the single source of truth for current state. If it disagrees with a history file, `_STATUS.md` wins. If it's stale, fixing it is your task.

---

## 2. Operating Loop

```
READ → DIAGNOSE → ACT → VERIFY → RECORD
```

1. **READ** — Read per §1. Check **Active Traps** in `_STATUS.md` first.
2. **DIAGNOSE** — State the root cause before changing code. Do not patch symptoms.
3. **ACT** — Change code. Stay within scope (§7). Match surrounding style.
4. **VERIFY** — Observe actual output. See §5 for what counts.
5. **RECORD** — Write log per Task Tier (§3) + update `_STATUS.md`. Task is not done until record exists.

---

## 3. Task Tiers

Classify the task **before** acting:

| Tier | Criteria | Required logging |
|------|----------|-----------------|
| **N — Nano** | ≤ 5 lines, 1 file, no new deps, no behavior change, backward-compatible | Update 1 row in `_STATUS.md` only. No new file. |
| **S — Standard** | Single feature/bugfix, ≤ 150 lines, ≤ 3 files | New `changes_X_*.md` + update `_STATUS.md` |
| **L — Large** | New architecture, new API, multi-file redesign | Write `changes_X_plan_*.md` first → get implicit approval → implement → `changes_X_*.md` + `_STATUS.md` |

When unsure between N and S → default to S.

---

## 4. Log File Format (Tier S / L)

### Naming
- Filename: `changes_X_<slug>.md` where X = next integer.
- **Verify by `ls changes_history/`** before picking X. Do not trust `_STATUS.md`'s "Latest entry" field without checking.
- `_STATUS.md` has no number — it is not a history entry.
- History files are immutable. To correct: write a new entry with `supersedes: [old_id]`.

### Template

```markdown
---
id: <X>
title: <one-line summary>
date: YYYY-MM-DD HH:MM TZ
agent: <name>
status: verified | partial | unverified | broken
files:
  - relative/path/to/file.py
---

## What was done
- Bullet list: every file touched and why.

## How it was done
- Root cause → fix. Specific functions, endpoints, variables.
- Enough detail for another agent to reconstruct reasoning without reading source.

## Verification
<!-- Paste exact commands + observed output. If unverified, state exactly what to run. -->

## Notes & Traps
<!-- Constraints for the next agent. New traps discovered → copy to _STATUS.md Active Traps. -->
```

---

## 5. Verification — What Counts

| Status | Meaning |
|--------|---------|
| `verified` | Observed working end-to-end this session (status code, row count, screenshot, output snippet) |
| `partial` | Core path verified; edge cases or visual not confirmed |
| `unverified` | Cannot observe headlessly — requires hardware, GUI, or user action |
| `broken` | Observed to be broken, not yet fixed |

**`py_compile` / lint / type-check alone → always `unverified`.** Use as supporting evidence only.

When marking `unverified`, state the exact command or action the next person must run:
> `unverified — run uv run app.py and confirm no white flash before splash`

---

## 6. `_STATUS.md` Structure

```markdown
# Project Status
- Last updated: YYYY-MM-DD HH:MM TZ — <agent>
- Latest history entry: changes_X_*.md

## How to Run
[exact commands from scratch]

## Feature Health
| Feature | Endpoint | Status | Last verified | Notes |
|---------|----------|--------|---------------|-------|
| ...     | ...      | ✅/❌/❓/🚧 | YYYY-MM-DD | ... |

## Active Traps
- **[Name]:** what goes wrong + workaround.
```

Legend: ✅ Working · ❌ Broken · ❓ Unverified · 🚧 In Progress

---

## 7. Pipeline Output Versioning

When a pipeline change would cause output files to differ from the previous version, **rename the old file to preserve it before overwriting.**

### When this applies
A pipeline change is any modification to data processing logic, generation logic, transformation steps, or output format — where the resulting file content would differ from what existed before.

Applies to: generated reports, data exports (CSV / JSON / parquet / HTML), built artifacts, config snapshots, any file produced by running the pipeline.
Does **not** apply to: source code files (history log covers those), temp files, test fixtures.

### Naming convention

```
<name>_prev_YYYYMMDD.<ext>          # same directory, date suffix
<name>_prev_YYYYMMDD_HHMM.<ext>     # if multiple versions in one day
```

Or move to a `_archive/` subdirectory in the same folder:

```
_archive/<name>_YYYYMMDD.<ext>
```

Use whichever convention is already established in the project. Be consistent.

### Required log entry

In the `## Notes & Traps` section of the Tier S/L history file, record:
- Which output file was versioned
- The preserved filename
- What changed in the pipeline that triggered it

Example:
```
Output versioning: renamed `report.json` → `report_prev_20260612.json`
before overwriting. Pipeline change: added momentum score field; output
schema now includes `momentum_pct` — incompatible with previous consumers.
```

### When unsure whether output will differ

If you cannot determine before running whether the output will differ (e.g., the pipeline fetches live data), preserve the existing file **before** running, then delete the backup if the output is identical.

---

## 8. Scope & When to Stop

**Proactive fix — only if ALL of:** ≤ 5 lines, 1 file, backward-compatible, no new deps.
Otherwise: surface in Notes, do not fix silently.

**Stop and ask before:**
- Deleting or moving files/dirs
- Changing a public API (endpoint, signature, schema)
- Root cause is in a different module than the stated task
- Adding a new dependency
- Tier L task with no plan file yet
- Tried twice and still cannot reproduce the problem

---

## 9. Coding & Environment Rules

<!-- CUSTOMIZE: language, runtime, package manager, how to run, env vars, ports -->

1. **Language:** python3 (never `python` or `python2`)
2. **Deps:** `uv` — record all new deps in `pyproject.toml` or script header
3. **Run:** `uv run <entrypoint>`
4. **API specs:** read `api_documents/` first before any external source

---

## 10. UI/UX Rules  <!-- CUSTOMIZE or delete -->

<!-- CUSTOMIZE or delete -->

1. Follow platform design guidelines (HIG / Material / etc.)
2. Respect `prefers-reduced-motion` for all animations
3. Reference design tokens from project's Figma or design system

---

## 11. First-Time Setup  <!-- delete after applying -->

- [ ] Save as `CLAUDE.md` at project root
- [ ] Fill §8 and §9
- [ ] Create `changes_history/`
- [ ] Create `changes_history/_STATUS.md` from §6 template
- [ ] Create `changes_history/changes_1_initial_setup.md` (starting state, known issues)
- [ ] Delete this section
