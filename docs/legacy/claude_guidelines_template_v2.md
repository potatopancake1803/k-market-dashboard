# AI Agent Collaboration Guidelines — CLAUDE.md (v2)

> **Template for multi-agent, multi-session projects.**
> Copy this file to your project root as `CLAUDE.md`.
> Fill in the `<!-- ✏️ -->` sections. Delete placeholder text when done.

---

## 🧭 First Things First — Read Order (every session)

Before touching a single line of code:

1. **`CLAUDE.md`** (this file) — the rules.
2. **`changes_history/_STATUS.md`** — feature-health table, active traps, how to run.
   This is sufficient for 95% of sessions. Stop here unless you need history.
3. **`changes_history/changes_X_*.md`** — only the **last 3 files** (highest X), only if:
   - You're debugging a regression and need the recent change narrative, OR
   - You are explicitly continuing a partial/unverified task.

> ⚠️ **Do NOT read all history files ascending.** With a mature project (20+ entries)
> this consumes significant context with diminishing returns. `_STATUS.md` is the
> living summary — trust it. If it's stale, fixing it is your task.

---

## 🔁 The Operating Loop

Every task — no matter how small — runs through these five steps.
The only variable is *how much* to log (see Task Tiers below).

```
READ → DIAGNOSE → ACT → VERIFY → RECORD
```

1. **READ.** Read in the order above. Check Active Traps in `_STATUS.md` first —
   most failures are repeats of a known trap.

2. **DIAGNOSE.** State the root cause before changing code. If you cannot reproduce
   the problem, say so. Do not patch symptoms.

3. **ACT.** Make the change. Match surrounding code style. Stay within scope
   (see §Scope Discipline).

4. **VERIFY.** Run it and observe actual output. See §Verification Tiers.
   `py_compile` alone is **not** verification — it is a syntax check.

5. **RECORD.** Update `_STATUS.md` and write a history file (if required by Task Tier).
   Logging is part of "done." A task without a record is not done.

> ⚠️ **The anti-"claimed-fixed" rule:** never write `status: verified` for something
> you observed to work, and `status: unverified` for everything you did not.
> "Unverified" is honest and acceptable. "Verified" that was not actually observed
> is the single worst failure mode in multi-agent projects.

---

## 📏 Task Tiers — Match Logging to Task Size

Determine the tier **before** acting. It governs what logging is required.

| Tier | When to use | Record requirement |
|------|-------------|-------------------|
| **N — Nano** | ≤ 5 lines changed, single file, isolated, no new deps, no new behavior | Update one row in `_STATUS.md` feature table. No new file. |
| **S — Standard** | Single feature or bugfix, up to ~150 lines, ≤ 3 files | New `changes_X_*.md` file + update `_STATUS.md`. |
| **L — Large** | New architecture, new API surface, multi-file redesign | Write `changes_X_plan_*.md` **before** acting. Then `changes_X_*.md` after. Update `_STATUS.md`. |

**Classifying edge cases:**
- A bugfix that touches only CSS/template string → usually N.
- A bugfix that requires understanding data flow across 2+ files → at least S.
- Any change that adds a new endpoint, dependency, or removes existing behavior → at least S.
- If unsure between N and S, default to S.

---

## ✅ Verification Tiers

Match verification effort to task tier. Be honest about what you actually observed.

| Level | Meaning | Example evidence |
|-------|---------|-----------------|
| `verified` | You observed the working result end-to-end this session | `GET /api/foo → 200 {"status":"ok"}`, screenshot, row count |
| `partial` | Core path verified; edge cases or visual elements not confirmed | `API returns 200 and correct shape; visual layout unconfirmed` |
| `unverified` | Cannot run it headlessly (requires hardware, GUI, credentials, user) | `py_compile OK; launch flash requires user to run app.py and confirm` |
| `broken` | Observed to be broken; not yet fixed | Used in `_STATUS.md` to flag known issues |

**`py_compile` / type-check / lint alone → always `unverified`**, not `verified`.
Use it as supporting evidence alongside other checks, never alone.

When marking `unverified`, state exactly what the next person needs to do to verify:
```
Visual only — run `uv run app.py` and confirm no white blink before splash.
```

---

## 📝 History Log Format — Standard (Tier S/L)

### Naming (CRITICAL)
```
changes_X_<short-slug>.md
```
- `X` = next sequential integer. **Verify by running `ls changes_history/`** before choosing X.
  Do NOT trust `_STATUS.md`'s "Latest history entry" for numbering without checking files.
- `_STATUS.md` is not a history entry — it has no number prefix.
- History files are **immutable once written.** To correct: write a new entry with
  `supersedes: [old_id]`; add a note in `_STATUS.md` correction log.

### Frontmatter + Body

```markdown
---
id: <X>
title: <one-line summary>
date: YYYY-MM-DD HH:MM <TZ>
agent: <Claude (model) | Antigravity | User | ...>
status: verified | partial | unverified | broken
files:
  - relative/path/to/changed/file.py
supersedes: []   # omit this line if empty; only include when actually superseding
---

# [Task Title]

## 🛠️ What was done
- Bullet list: features / bugfixes / refactors. Every file touched and why.

## ⚙️ How it was done
- Root cause → fix. Specific functions, endpoints, variables, libraries.
- Detailed enough that another agent can reconstruct the reasoning without reading source.

## ✅ Verification
<!-- Match to your verification tier above. Paste exact commands + observed output. -->
<!-- If unverified, state exactly what needs to be done to verify. -->

## ⚠️ Notes & Pending Issues
<!-- Traps, constraints, or unfinished work the next agent must know about. -->
<!-- Add a NEW TRAP entry here if you discovered one — copy to _STATUS.md Active Traps. -->
```

---

## 📋 `_STATUS.md` — Living Document

Updated **in the same session** as any Tier S/L change, or any Nano change that affects
a feature-health row. Required sections:

```markdown
# Project Status

- **Last updated:** YYYY-MM-DD HH:MM TZ by <agent>
- **Latest history entry:** changes_X_*.md

---

## ▶ How to Run

<!-- Step-by-step from scratch. Commands that actually work. -->

---

## ▶ Feature Health

| Feature | Endpoint / entry | Status | Last verified | Notes |
|---------|-----------------|--------|---------------|-------|
| ...     | ...             | ✅/❌/❓/🚧 | YYYY-MM-DD | ... |

Legend: ✅ Working  ❌ Broken  ❓ Unverified  🚧 In Progress

---

## ▶ Active Traps

<!-- Gotchas that have caused failures at least once. Check before debugging. -->

- **[Trap name]:** description and workaround.

---

## ▶ Correction Log *(optional — add only when a prior entry was found wrong)*

| Date | Entry corrected | What was wrong | Fixed by |
|------|----------------|----------------|----------|
```

---

## 🔭 Scope Discipline

> **Do not touch code outside the stated task scope without surfacing it first.**

- **Fix inline (Nano-scope only):** ≤ 5 lines, single file, backward compatible, no new
  behavior, no new deps. If all five conditions are met, fix it and note it as a Nano
  change in `_STATUS.md`.
- **Surface and flag (everything else):** Describe the issue in your reply or in the
  `## ⚠️ Notes & Pending Issues` section. Do not fix it silently and do not fix it
  while mid-task on something else.
- **Never:** rename symbols, move files, or restructure modules unless that is the
  explicit task.

---

## 🛑 When to STOP and ASK

Stop and ask the user before proceeding when:

- The task requires **deleting or moving** files/dirs (cannot auto-undo).
- The task requires **changing a public API** (endpoint, function signature, schema).
- You've found a **root cause that contradicts the stated task** — e.g., the user
  asked you to patch symptom X but root cause is Y in a different module.
- The fix requires **adding a new dependency** not already in the project.
- You are **uncertain about scope**: "should I also fix the related issue in file B?"
- The task is Tier L but **no plan file exists yet** — write the plan and surface it
  before acting.
- You've **tried twice** and still cannot reproduce or fix the problem.

---

## 💻 Coding & Environment Rules

<!-- ✏️ Customize this section per project -->

1. **Language & Runtime:** [e.g., `python3` via `uv` — never bare `python` or `python2`]
2. **Dependency management:** [e.g., `uv` — record all deps in `pyproject.toml`]
3. **How to run:** [e.g., `uv run main.py` → `http://localhost:8780`]
4. **Port/env notes:** [e.g., never kill PID on port 8770 — macOS sharingd]
5. **API specs:** When integrating APIs, read `api_documents/` first.

<!-- End customizable section -->

---

## 🎨 UI/UX Rules

<!-- ✏️ Customize or delete this section -->

1. **Design system:** [e.g., Apple HIG / Material 3 / company tokens]
2. **Accessibility:** Respect `prefers-reduced-motion` for all animations.
3. **Component reference:** [e.g., Figma file link or local design tokens path]

<!-- End customizable section -->

---

## 🚀 First-Time Setup Checklist

When applying this template to a new project:

- [ ] Copy this file to project root as `CLAUDE.md`
- [ ] Fill in `💻 Coding & Environment Rules`
- [ ] Fill in or delete `🎨 UI/UX Rules`
- [ ] Create `changes_history/` directory
- [ ] Create `changes_history/_STATUS.md` from the template above (empty feature table)
- [ ] Create `changes_history/changes_1_initial_setup.md` documenting the project's
      starting state (tech stack, entry point, known issues)
- [ ] Delete this checklist section

---

## ✅ Definition of "Done"

A task is done when:

1. The change works end-to-end, **verified with real observed output** (or honestly marked unverified with clear instructions for the human verifier).
2. `_STATUS.md` is updated: feature-health row(s) reflect the new state.
3. A history file exists if the task was Tier S or L.
4. No previously working features were knowingly broken (cross-check the feature-health table).

---

*Template version: 2 — improvements over v1: task tiers, smart read strategy,
removed frontmatter redundancy (verified_by), removed always-empty supersedes,
added scope discipline, added stop-and-ask triggers, clarified verification theater,
defined "cheap" for proactive fixes.*
