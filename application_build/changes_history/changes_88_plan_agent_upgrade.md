---
id: 88
title: PLAN — Agent self-improvement & verification automation (Hooks + reflect, gated)
date: 2026-06-19 KST
agent: Claude (Opus 4.8)
status: plan (awaiting user approval — NO code/settings changed yet)
files:
  # To be created/changed only AFTER approval. Listed here as the intended surface.
  - .claude/settings.json                         # NEW (Tier 1-A hooks). Do NOT touch .claude/launch.json.
  - scripts/hooks/gate_dispatch.py                # NEW (1-A) PostToolUse sentinel + Stop-time smoke gate
  - scripts/hooks/session_brief.py                # NEW (1-A, optional) SessionStart trap/health digest
  - scripts/reflect/capture.py                    # NEW (1-B) correction capture → queue
  - scripts/reflect/apply.py                      # NEW (1-B) guarded apply (backup→append→gate→log / else dev_notes)
  - application_build/changes_history/_autoreflect_log.md         # NEW (1-B) provenance log
  - application_build/changes_history/_autoreflect/               # NEW (1-B) backups + queue
---

## 0. Scope of THIS plan

Implement **TIER 1 only** (1-A Hooks gate, 1-B guarded reflect). **TIER 2 / TIER 3 are
proposal/PoC/deferred** — described for the user's decision, not built. Order is strict:
**1-A → verify → 1-B → verify**, one at a time, each behind `smoke_check`.

This is a **Tier-L** task (new automation surface, multi-file). Per `application_build/CLAUDE.md`
§3 this plan file comes first and **nothing is built until the user approves**.

### Environment facts re-confirmed this session (READ phase)
- **No `.git`** (`[ -d .git ]` false) → TIER 3-B (GitHub PR review) is not installable now; conditional memo only.
- **`.claude/` exists but contains only `launch.json`** (used by Preview MCP, trap #14). **`settings.json` is ABSENT** → we create it fresh; we must not disturb `launch.json`.
- Gate scripts present: `scripts/smoke_check.py`, `scripts/api_smoke.py`, `scripts/health_check.py`.
- **`smoke_check.py` measured: `real 1.13s`, network-free, deps already cached, output ~5 lines on PASS** (`SMOKE PASS ✓`). This is the single most important design input for 1-A frequency.
- No `pyproject.toml` → PEP723 script headers (consistent with existing `scripts/`).
- `dev_notes/` has one **unprocessed** capture: `session_20260618_1441_새-세션.md` (out of scope here; flagged to user separately). Its format is the template the 1-B low-confidence queue will reuse.
- Latest history entry = `changes_87`; this plan is `changes_88`.

---

## TIER 1-A — Claude Code Hooks → regression gate auto-enforcement

### Goal
Make `smoke_check.py` run **without depending on the agent remembering to** after any
edit to gated backend/template files. Directly attacks the project's #1 failure
(changes_73 logged "verified" after `py_compile` only and shipped an app-down break).

### Design decision — frequency (token-efficiency, the project's stated goal)
Three candidate shapes were considered against the measured 1.13s / 5-line cost:

| Option | When smoke runs | Runs per multi-edit turn | Token cost | Verdict |
|---|---|---|---|---|
| A. PostToolUse-immediate | after **every** gated Edit/Write | N (once per edit) | N×(~5 lines) on pass | redundant on multi-edit turns |
| B. Stop-only | once when the agent finishes the turn | 1 | ~5 lines on pass, full output on fail | cheap but no per-edit locality |
| **C. Sentinel + Stop (RECOMMENDED)** | PostToolUse just marks "dirty"; **Stop** runs smoke once iff dirty | ≤1 | **~0 on no-structural-change turns**, ~5 lines pass, full output fail | best |

**Recommended = C.** Rationale: PostToolUse fires on *every* Edit/Write but the dispatcher
exits **silently in microseconds** unless the changed file matches the gated set, so non-backend
turns cost nothing. When a gated file is touched it only **touches a sentinel file**
(`.cache`/tmp), deferring the actual 1.13s run to the **Stop** hook, which runs it **at most once
per turn**. On FAIL the Stop hook returns the smoke output as a blocking reason (exit 2), so the
agent is forced to address the break **before the turn ends** — exactly the gate the protocol wants,
but it can never double-run or spam.

### Gated path set (matches §12 of `application_build/CLAUDE.md`)
`scripts/*.py` — with the hard trigger being the live-imported modules:
`market_dashboard3_realtime.py`, `ui_templates.py`, `pure_helpers.py` (and any new
`scripts/` module the dynamic backend imports). Edits elsewhere (docs, dev_notes, tests) do **not** trip it.

### Files
1. **`.claude/settings.json`** (new) — minimal, additive:
   ```jsonc
   {
     "hooks": {
       "PostToolUse": [
         { "matcher": "Edit|Write|MultiEdit",
           "hooks": [ { "type": "command",
             "command": "python3 scripts/hooks/gate_dispatch.py mark" } ] }
       ],
       "Stop": [
         { "hooks": [ { "type": "command",
             "command": "python3 scripts/hooks/gate_dispatch.py gate" } ] }
       ],
       "SessionStart": [
         { "hooks": [ { "type": "command",
             "command": "python3 scripts/hooks/session_brief.py" } ] }
       ]
     }
   }
   ```
   - Does **not** reference `launch.json`; leaves it untouched.
   - Commands are **relative to project root** (Claude Code runs hooks with `cwd` = project dir); `gate_dispatch.py` resolves paths from its own `__file__` to be safe.

2. **`scripts/hooks/gate_dispatch.py`** (new, PEP723, stdlib-only):
   - `mark` mode: read hook JSON from stdin, pull `tool_input.file_path` (handle `Write`/`Edit`/`MultiEdit` shapes); if it matches the gated set → write a sentinel (`~/.cache/kmkt_m4/.smoke_dirty`); **always exit 0 silently** (PostToolUse must never block normal editing).
   - `gate` mode (Stop): if sentinel absent → exit 0 silently. If present → run `uv run scripts/smoke_check.py`, delete sentinel, then:
     - PASS → exit 0 (optionally one line `gate: SMOKE PASS ✓`).
     - FAIL → print smoke output to **stderr** and **exit 2** (Claude Code feeds stderr back and blocks the Stop, so the agent must fix before finishing).
   - Guard against infinite Stop loops: the hook input carries `stop_hook_active`; if true, do **not** re-block (exit 0) — prevents a hard wedge if smoke stays red.

3. **`scripts/hooks/session_brief.py`** (new, optional, stdlib-only) — SessionStart:
   - Emit a **small** digest to stdout (added to session context): the **headline line of each `_STATUS.md` Active Trap** (number + first clause only, not full text) + any `health_check.py` **WARN** lines. Hard cap (~40 lines) so it saves tokens vs. re-reading the 444-line `_STATUS.md`, not adds them. If `health_check.py` is slow (>2s) it is run with a timeout and skipped on timeout.
   - This is the only part that *adds* context; it is opt-in and capped. If the user prefers zero injection, we ship 1-A without it.

### Verification (1-A)
- `uv run scripts/smoke_check.py` → `SMOKE PASS ✓` (settings/hook files don't touch the import graph, so golden is unchanged — no re-baseline expected).
- **Live hook proof:** make a trivial whitespace edit to `scripts/ui_templates.py`, observe the Stop gate actually runs smoke (quote the gate output); then make a deliberately broken edit (e.g. a bad anchor) and confirm the Stop hook **blocks with the failure output**, then revert.
- Boot the app once (`uv run application_build/app.py`, or headless backend) to confirm settings.json presence causes no startup change.

### Rollback (1-A)
Delete `.claude/settings.json` (and `scripts/hooks/`). Hooks vanish; nothing else references them. `launch.json` untouched throughout.

### Tradeoffs / traps (1-A)
- Hooks run **arbitrary local commands**; this is acceptable (local single-user tool) but the command set is fixed and reviewed.
- A Stop hook that always-fails could wedge the turn → mitigated by the `stop_hook_active` guard (block once, not repeatedly).
- PostToolUse JSON shape differs slightly per tool (`Write` vs `Edit` vs `MultiEdit`); dispatcher handles all and fails **open** (never blocks) if it can't parse.

---

## TIER 1-B — Guarded auto-reflect (capture corrections → canonical docs, with the 3 safety guards)

### Finding from researching `BayramAnnakov/claude-reflect` (drives the build-vs-adopt call)
- It is a **Claude Code plugin** (marketplace install). Capture is automatic (regex over every prompt, confidence **0.60–0.95 = max(regex, semantic)**), but **apply is MANUAL** via `/reflect` with per-item human approval — i.e. it is *not* the silent auto-writer the brief assumes.
- Its sync targets are a **glob**: `~/.claude/CLAUDE.md`, `./CLAUDE.md`, **`./**/CLAUDE.md`**, `AGENTS.md`. In **this** repo that glob hits **both** root `CLAUDE.md` **and** `application_build/CLAUDE.md` **and** `AGENTS.md`/`ANTIGRAVITY.md` indiscriminately → it would create the exact **dual-source drift** the project forbids, and it has **no concept of `_STATUS.md` as the single source of truth**.
- Two of its four hooks are **git-dependent** (`post_commit_reminder.py`) → **inert here** (no `.git`).
- It has **no backup, no smoke/integrity gate, no confidence→dev_notes routing**.

**→ Recommendation (matches the brief's own fallback clause): BUILD a lightweight custom wrapper**,
optionally borrowing claude-reflect's regex *patterns* for capture. A custom ~2-file script gives us
the **3 mandatory guards + 2-tier confidence gating + targeted single-source writes** that the plugin
cannot, and stays "얇게 얹기" (no marketplace/plugin footprint, stdlib-only, PEP723).

### The 3 safety guards (mandatory) + 2-tier confidence gating — concrete design

**Capture** — `scripts/reflect/capture.py`, hook = **UserPromptSubmit** (fires per user message, never blocks):
- Scan the user message for correction patterns (multilingual): `아니(요)?\s*X\s*말고\s*Y`, `~말고`, `~로 해`, `틀렸`, `다시`, `not X, use Y`, `don't use`, `instead`, `should be`, etc. Compute a **regex confidence** in 0.60–0.95 (pattern-strength table). No LLM call (stdlib only, deterministic).
- Append a candidate to a queue: `application_build/changes_history/_autoreflect/queue.jsonl`
  `{ts, session, user_excerpt, inferred_rule, target_doc_guess, confidence}`.
- **Capture never writes to canonical docs.** Exit 0 always.

**Apply** — `scripts/reflect/apply.py`, hook = **Stop** (runs after capture, automatic) — for each queued item:
- **Threshold (2-tier).** Recommend a **conservative 0.90** (the brief says be conservative; canonical docs are high-density). Items `≥ 0.90` → auto-apply to canonical docs; items `< 0.90` → **routed to `dev_notes/`** as a single-note md in the existing capture format (unifies with the existing capture→user-confirm→`done/` workflow; **no parallel queue system**). *(0.90 is a proposed default — see "Decision needed".)*
- **Guard 1 — Backup before write:** copy the target file → `application_build/changes_history/_autoreflect/<file>_bak_YYYYMMDD_HHMM.md`. (This is the only rollback path; no git.)
- **Targeted, structure-preserving append (NOT rewrite):**
  - `_STATUS.md` → append as the **next-numbered Active Trap** at the end of that section (preserve numbering/table), or a Correction-log bullet — never rewrite the file.
  - Canonical `CLAUDE.md` (root) → append a one-liner under the relevant existing section only.
  - **Never** write both CLAUDE.md files; pick the single correct target (default: append the *rule* to `_STATUS.md`, since it is the single source of truth). No `./**/CLAUDE.md` glob.
- **Guard 2 — Integrity gate + auto-rollback:** after the write run `uv run scripts/smoke_check.py`. **Important nuance:** `_STATUS.md`/`CLAUDE.md` are **not imported by the backend**, so smoke_check alone cannot detect a *doc* corruption. Therefore the integrity gate is **smoke_check AND a lightweight structural validator** (`apply.py` self-check): target file still parses as UTF-8, **required sections still present** (e.g. `## ▶ Active traps`), file **did not shrink** (byte count ≥ pre-write), table rows intact. If **either** check fails → **restore from the Guard-1 backup**, mark the item failed, and warn. *(This corrects an over-trust in the brief: smoke_check is necessary but not sufficient for doc edits.)*
- **Guard 3 — Provenance log:** append to `application_build/changes_history/_autoreflect_log.md`:
  which tool / what sentence / why (session id + the correction excerpt) / confidence / applied|rolled-back.
- **Stop-loop guard:** respect `stop_hook_active`; apply runs at most once per turn and never blocks the Stop (it is informational — a doc edit is not a reason to halt the agent).

### Rollout safety (recommended)
First ship apply.py in **"propose" mode** (high-confidence items also go to `dev_notes/` instead of
auto-editing canonical docs) for the initial period, then flip a single flag to **"auto"** once the
capture quality is observed to be good. This earns trust before letting it write canonical docs.
*(Flag default is a Decision-needed item below.)*

### Verification (1-B)
- Mock a **high-confidence** correction → confirm: backup created, structure-preserving append to `_STATUS.md`, `_autoreflect_log.md` provenance row, smoke+structural gate PASS.
- Mock a **low-confidence** correction → confirm it lands in `dev_notes/` only (no canonical edit).
- **Most important:** deliberately induce an integrity break (e.g. force apply to remove a required section) → confirm the gate **auto-rolls-back** from the backup and logs the rollback.
- `uv run scripts/smoke_check.py` green throughout.

### Rollback (1-B)
Remove the UserPromptSubmit/Stop entries from `.claude/settings.json` and delete `scripts/reflect/`. Any canonical-doc line it added is reversible via the timestamped backups in `_autoreflect/`. "방금 자동수정 되돌려" = restore newest backup for that file.

### Overlap check with TIER 2-B (self-improvement skills)
1-B already automates the RECORD/journal capture that 2-B proposes. After 1-B ships, **2-B is presumed redundant** unless it adds something 1-B can't — do not build a second parallel self-improvement system.

---

## TIER 2 — proposal / PoC only (NOT built; user decides)

### 2-A. claude-mem / claude-brain (auto session compression)
- Potential: less manual `_STATUS.md`/`HANDOFF.md` upkeep; cross-session context injection → token savings.
- Risks to surface: ① SQLite-locked memory is hard for a human to curate; ② un-reviewed auto-accumulation collides with the high-density canonical docs (duplication/drift); ③ creates a **second source of truth** vs the `_STATUS.md` single-source rule.
- **Proposed action (not now):** read-only PoC in a **separate scratch dir**; compare auto-generated memory vs current `_STATUS.md` quality. Decision is the user's. No install into this repo.

### 2-B. Self-improvement skills (`learnings.md` auto-append)
- Overlaps 1-B. **Defer**; re-evaluate only after 1-B is live and only if it adds unique value. Avoid a parallel self-improvement track.

---

## TIER 3 — reference only (NOT installed)

### 3-A. wshobson/agents + `.agents/skills/` pattern
- **Do not** create `.agents/skills/` (a new doc source = drift). Extract **at most 1–2** ideas (e.g. a frontmatter convention) to fold into existing docs. Proposal only.

### 3-B. anthropics/claude-code-action (GitHub PR review)
- **Not installable: no `.git`/remote.** Conditional memo only: "if the project later adopts Git + GitHub, PR auto-review becomes a strong regression backstop." Do **not** `git init` or wire a remote (user infra decision).

---

## Decisions needed from the user before ACT
1. **1-A SessionStart digest:** include the capped trap/health digest, or ship hooks **without** any context injection? (Default: include, capped ≤40 lines.)
2. **1-B confidence threshold** for auto-writing canonical docs. (Default proposal: **0.90**, conservative.)
3. **1-B initial mode:** start in **"propose"** (high-confidence also routed to `dev_notes/` first) then flip to **"auto"**, or go **"auto"** immediately with the guards? (Default: start "propose".)
4. Confirm: build the **custom lightweight reflect wrapper** (recommended) rather than installing the claude-reflect plugin (which mis-targets both CLAUDE.md files + has inert git hooks here). (Default: custom.)

## RECORD plan (after approval + implementation)
- `changes_88_*.md` (final, English) for each shipped tier; update `_STATUS.md` feature table.
- New **Active Trap** to add to `_STATUS.md`: *"reflect auto-doc-edit: high-conf (≥thr) appends to `_STATUS.md` single-source only; low-conf → `dev_notes/` queue; every auto-edit = backup→append(structure-preserving)→(smoke_check AND structural validator)→provenance log, auto-rollback on gate fail. smoke_check alone does NOT validate doc edits."*
- Hooks change "how the project works" → sync **both** root `CLAUDE.md` and `application_build/CLAUDE.md` (§12). Regenerate `docs/CODEMAP.md` only if backend modules change (they won't here — hooks/reflect live under `scripts/hooks/` & `scripts/reflect/`, not imported by the backend, so **no `market_dashboard.spec` hiddenimports change** needed).
- Append a `docs/DEBUG_JOURNAL.md` entry if any non-obvious issue arises during wiring.
