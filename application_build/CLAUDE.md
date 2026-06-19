# AI Agent Guidelines — K-Market Dashboard (application_build)

Multi-agent project (Claude, Antigravity, etc.). Every agent reads this file first, every session.

---

## 1. Session Start — Read Order

| Situation | Read |
|-----------|------|
| Starting any task | `CLAUDE.md` + `changes_history/_STATUS.md` |
| Continuing a partial/unverified task | + last 2 history files (highest X) |
| Debugging a regression | + last 3 history files (highest X) |
| **Never** | All history files ascending — context budget waste |

`_STATUS.md` is the single source of truth. If it disagrees with a history file, `_STATUS.md` wins. If stale, fixing it is your task.

---

## 2. Operating Loop

```
READ → DIAGNOSE → ACT → VERIFY → RECORD
```

0. **CLEAR DEBT** — At session start, check the **미검증 소거 대기열** in `_STATUS.md` and verify **at least one** item you can (run the app, look, mark ✅/❌). Skip only if no item is checkable in this session.
1. **READ** — Per §1. Check **Active Traps** in `_STATUS.md` before anything else.
2. **DIAGNOSE** — State root cause before changing code. Do not patch symptoms.
3. **ACT** — Change code. Stay within scope (§7). Match surrounding style.
4. **VERIFY** — Observe actual output. See §5. **If you touched imports / file structure / routes /
   `_inject_*` / templates (`scripts/ui_templates.py`), you MUST run the regression gate
   `uv run scripts/smoke_check.py` and see `SMOKE PASS ✓` before claiming verified.**
   `py_compile` alone is NOT verification (changes_73 shipped an app-down bug that py_compile passed).
   After an *intentional* markup change that fails the golden compare, re-baseline with
   `uv run scripts/smoke_check.py --golden write` and note it in the changes log.
5. **RECORD** — Write log per Task Tier (§3) + update `_STATUS.md`. **If you burned ≥1 cycle on an
   error or it was non-obvious, append a `### SYMPTOM:` entry to `docs/DEBUG_JOURNAL.md`** (symptom→
   cause→fix→guard) so it's never re-debugged. **If you changed project structure (files/dirs/entry/
   routes/major templates), sync the guideline files in the SAME session — see §12.** Not done until
   record + (if applicable) journal + guideline-sync exist.

> ⚠️ **Anti-"claimed-fixed" rule:** never mark `verified` unless you observed it working this session. `unverified` is honest and acceptable. Logging from intent instead of observed result is the single worst failure mode in this project — it already happened once.

---

## 3. Task Tiers

Classify **before** acting:

| Tier | Criteria | Required logging |
|------|----------|-----------------|
| **N — Nano** | ≤ 5 lines, 1 file, no new deps, no behavior change, backward-compatible | Update 1 row in `_STATUS.md` only. No new file. |
| **S — Standard** | Single feature/bugfix, ≤ 150 lines, ≤ 3 files | New `changes_X_*.md` + update `_STATUS.md` |
| **L — Large** | New architecture, new API surface, multi-file redesign | Write `changes_X_plan_*.md` first → implement → `changes_X_*.md` + `_STATUS.md` |

When unsure between N and S → default to S.

---

## 4. Log File Format (Tier S / L)

**Location:** `application_build/changes_history/`
**All content MUST be in English.**

### Naming

`changes_X_<slug>.md` where X = next integer after highest existing file.
**Verify with `ls changes_history/`** — do not trust `_STATUS.md`'s "Latest entry" field without checking.
`_STATUS.md` has no number and is not a history entry.
History files are **immutable**. To correct: write a new entry with `supersedes: [old_id]`.

### Template

```markdown
---
id: <X>
title: <one-line summary>
date: YYYY-MM-DD HH:MM KST
agent: <Claude (model) | Antigravity | User>
status: verified | partial | unverified | broken
files:
  - application_build/app.py
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Bullet list: every file touched and why.

## How it was done
- Root cause → fix. Specific functions, endpoints, variables, libraries.
- Enough detail for another agent to reconstruct without reading source.

## Verification
<!-- Paste exact commands + observed output. -->
<!-- If unverified: state exactly what command/action to run to verify. -->

## Notes & Traps
<!-- Constraints for next agent. New traps → copy to _STATUS.md Active Traps. -->
```

---

## 5. Verification — What Counts

| Status | Meaning |
|--------|---------|
| `verified` | Observed working end-to-end this session |
| `partial` | Core path verified; edge cases or visual unconfirmed |
| `unverified` | Requires hardware / GUI / user action — cannot observe headlessly |
| `broken` | Observed broken, not yet fixed |

**`python3 -m py_compile` alone → always `unverified`.** Valid as supporting evidence only.

**Regression gate = the cheap path to `verified` for structural/backend changes.**
`uv run scripts/smoke_check.py` → `SMOKE PASS ✓` is real, observed evidence (it imports + boots +
renders + golden-compares). Run it; quote the result in the changes log. It will not catch
visual/GUI behavior (still needs preview/app), but it catches import/route/injection/render breakage.

When marking `unverified`, state exactly what to run:
> `unverified — run uv run application_build/app.py and confirm no white flash before splash`

---

## 6. `_STATUS.md` — Living Document

Update in the **same session** as any Tier S/L change, or any Nano that affects a feature row.

Required sections: **How to run** · **Feature health table** · **Active Traps**

Legend: ✅ Working · ❌ Broken · ❓ Unverified · 🚧 In Progress

---

## 7. Pipeline Output Versioning

When a pipeline change would cause output files to differ from the previous version, **rename the old file to preserve it before overwriting.**

### When this applies
Any modification to data processing, generation logic, transformation steps, or output format where the resulting file content would differ from what existed before.

Applies to: generated reports, data exports (CSV / JSON / parquet / HTML), built artifacts, config snapshots.
Does **not** apply to: source code (history log covers those), temp files, test fixtures.

### Naming convention

```
<name>_prev_YYYYMMDD.<ext>           # same directory, date suffix
<name>_prev_YYYYMMDD_HHMM.<ext>      # if multiple versions in one day
_archive/<name>_YYYYMMDD.<ext>       # alternatively, move to _archive/ subdir
```

### Required log entry

In the `## Notes & Traps` section of the history file:
- Which output file was versioned
- The preserved filename
- What pipeline change triggered it

Example:
```
Output versioning: renamed `screener_output.json` → `screener_output_prev_20260612.json`
Pipeline change: added momentum_pct field — output schema change, incompatible with old consumers.
```

### When unsure whether output will differ

Preserve the existing file **before** running. Delete the backup afterward if output is identical.

---

## 8. Scope & When to Stop

**Proactive fix inline — only if ALL of:** ≤ 5 lines, 1 file, backward-compatible, no new deps.
Otherwise: surface it in Notes, do not fix silently.

**Stop and ask before:**
- Deleting or moving files/dirs
- Changing a public API (endpoint, function signature, schema)
- Root cause is in a different module than the stated task
- Adding a new dependency
- Tier L task with no plan file yet
- Two failed attempts to reproduce or fix

---

## 9. Coding & Environment Rules

1. **Python:** always `python3` — never `python` or `python2`
2. **Deps:** `uv` — record all new deps in `pyproject.toml` or PEP 723 script header
3. **API specs:** read `api_documents/` first before any external source
4. **Ports:** never kill PID on 8770 — macOS `sharingd` (AirDrop/Handoff). Use 8780 (`MARKET_PORT` to override).
5. **Env flags:** `MI_NO_OPEN=1` (no browser auto-open), `MI_NO_PREWARM=1` (skip prewarm)

### How to run

| What | Command |
|------|---------|
| Native app (dev) | `uv run application_build/app.py` |
| Backend only (debug) | `MI_NO_OPEN=1 MI_NO_PREWARM=1 MARKET_PORT=8793 uv run scripts/market_dashboard3_realtime.py` |
| Build `.app` | `cd application_build && ./build.sh` |

Backend source of truth: `scripts/market_dashboard3_realtime.py`. `app.py` loads it live via `_live_source()` — edit + restart applies without rebuild.

---

## 10. UI/UX Rules

1. **Canonical design source = Apple macOS official Figma** (macOS 26 UI Kit, fileKey `a6AegNuDiPrlC5qdbXbn9R`).
   ALL interfaces must match its tokens. Use the Figma MCP (`figma-dev-mode-mcp-server`) to read tokens/components
   when possible; otherwise use the extracted official tokens recorded in memory `macos26-theme.md`:
   ease `cubic-bezier(.32,.72,0,1)`, systemBlue `#007AFF`/button `#0088ff`, systemRed `#FF3B30`,
   semantic 상승=red `#FF3B30` (dark `#FF453A`) · 하락=blue `#2E75B6` (dark `#64B5FF`),
   radii pill=100 / glass=26 / lg=16 / md=11, blur 50px (saturate 180%), SF Pro type scale.
2. **No empty space / no overflow (공간 효율).** Layouts must fill their space without awkward gaps AND content
   must NEVER overflow or get clipped by its container. Concretely:
   - Tables/cards in fixed/grid columns: the column must be wide enough OR the cell content must wrap/ellipsis/shrink
     (`min-width:0`, `overflow:hidden`, `text-overflow:ellipsis`, or `table-layout:fixed`). Verify the rightmost
     column is not cut off at the target width.
   - Prefer responsive `flex`/`grid` that adapts; avoid fixed widths that overflow narrow windows.
   - **Graphics/elements must NEVER spill outside their container or the viewport (right edge especially).**
     The #1 cause is the CSS default `min-width:auto` on flex/grid children: a long unbreakable value (price,
     cash, quantity) refuses to shrink and pushes the child past its parent. Mandatory defaults for any flex/grid
     holding data: parent `min-width:0`; grid tracks `minmax(0,1fr)` (not bare `1fr`); numeric cells
     `white-space:nowrap;overflow:hidden;text-overflow:ellipsis`; container `max-width:100%` and `overflow:hidden`
     where clipping is acceptable. (realtime page fixed this way — changes_31.)
   - After any layout change, verify nothing is clipped and there are no large dead zones (preview if available,
     else reason through the narrowest target width).
3. **Apple HIG:** follow https://developer.apple.com/design/human-interface-guidelines strictly.
4. **Motion:** respect `prefers-reduced-motion` for all animations.
5. **Light + dark:** every screen must support both themes (sync via the `kmkt` postMessage); never ship a
   screen that only works in one theme unless it is an intentional always-dark "cockpit" (document the exception).
6. **Toss Securities-style density** is the reference for data terminals (trading desk, backtester): compact but
   legible rows, resizable panels where useful, no wasted whitespace.
7. **Figma MCP gate (mandatory).** When a task needs Figma work — reading design tokens/components, generating a
   design, or syncing code↔design — **first confirm the Figma MCP is connected** (the `figma-dev-mode-mcp-server` /
   `use_figma` tools must be callable). If it is **not** connected, **pause the task immediately, ask the user to
   connect the Figma MCP, and resume only after they confirm.** Do not silently fall back to guessing layout/tokens
   from memory when the task explicitly calls for Figma — the canonical source (§10.1) must come from Figma when
   reachable. (The extracted `macos26-theme.md` tokens are a fallback only for incidental token lookups, never a
   substitute for required Figma design work.)
8. **Loading states must use the shared smooth loader — never a bare line of text.** Any "…불러오는 중 / 계산 중 /
   스캔 중" placeholder must render the spinner component, not plain text. Use the canonical helper in
   `scripts/market_dashboard3_realtime.py`: `_loader_html(text, sm=False)` (markup) + `_LOADER_CSS` (inject once
   per page `<head>`; `_inject_loader(html, swaps)` does both). `.kmkt-load` = ring spinner + pulsing label;
   `.kmkt-load.sm` = compact inline variant for list slots. It respects `prefers-reduced-motion` (§10.4) and uses
   `--sys-blue` with a `#007AFF` fallback so it works inside theme-less iframes (trap #1). **Every new page/panel
   that shows a loading placeholder must use this** — add one `_inject_loader(...)` line in the batch block near
   `def main()`. Verify with `curl <page> | grep kmkt-load` after adding.

## 11. Local LLM (LM Studio bridge) Rules

1. **Pick the LOADED model first.** `/api/llm_commentary` selects via `_pick_llm_model_ex()` against
   `_llm_chat_models_with_state()` (reads `/api/v0/models` → `state`). It prefers an already-**loaded** model so it
   never JIT-loads a *second* model alongside the user's choice (that double-load was a real bug). Only when nothing
   is loaded does it JIT-load the preferred `qwen3-4b-2507`. `KMKT_LLM_MODEL` env still force-overrides.
2. **Reasoning vs Instruct models need different handling (`_llm_model_profile`).** Detect with
   `_is_reasoning_model()` (qwen3.5 / qwq / *thinking* / deepseek-r1 / …; `*2507*`/Instruct are NOT reasoning).
   - **Reasoning models (qwen3.5) have NO working off-switch** (`/no_think`, `enable_thinking:false`,
     `chat_template_kwargs` are all dropped by LM Studio's fast path — measured) and otherwise dump everything into
     `delta.reasoning_content`, hitting `finish_reason=length` with `content`=0 (0 answer chars even at 3600 tok /
     119 s). **THE FIX = Assistant Prefilling:** append a trailing `{"role":"assistant","content":"<think>\n\n</think>"}`
     message. The engine treats reasoning as already done → `reasoning_tokens=0`, `finish_reason=stop`, immediate
     clean answer (qwen3.5-9b: first 1.7 s, 754 chars, finish=stop — measured). The profile carries `prefill`;
     the endpoint appends it. Normal `max_tokens` (1200) is then fine. Strip the leading `\n`/`</think>` off the
     first content chunk.
   - **Instruct models** (qwen3-4b-2507, gemma): concise system suffix, ~1000–1200 tokens, temp 0.3, no prefill.
   - Safety net retained: `reasoning_content` still streams to a dim "💭 추론" block and a "use an Instruct model"
     end-note fires if a reasoning model *still* yields no `content` (e.g. prefill ignored).
3. **Stream protocol:** the SSE yields `{"text":…}` for answer content and `{"text":…,"kind":"reasoning"}` for
   thinking. All three frontends (`startAI` modal, macro/backtest `streamLLM`) render `kind==="reasoning"` dimmed
   and answer text prominently.
4. **Popover (`#aiPop`) outside-click close uses `mousedown`, not `click`.** A `click` close handler fires *after*
   the Load/combo handler re-rendered `pop.innerHTML`, so `e.target` is detached and `!pop.contains` wrongly closed
   the popover. `mousedown` evaluates containment before the re-render.
5. **Context is recognized per model (`_llm_status`).** `/api/v0/models` gives `max_context_length` (all models)
   and `loaded_context_length` (loaded). The popover derives per-model `kind`, default **Max Tokens** (`def_tokens`,
   from effective context ÷4 clamped 512–4096) and a recommended context range (`rec_ctx_lo/hi`). Switching the
   model in the combo re-applies its default (`aipTokModel` guard preserves a manual edit until the model changes).
6. **One streaming core: `_llm_stream(sys_msg, user_msg, max_tokens=None)`** (model-pick → profile → prefill →
   stream → endnote). Reused by `/api/llm_ask` (and the place to evolve LLM behavior). `/api/llm_commentary`
   still has an inline copy — unify if you touch it.
7. **Two AI features beyond commentary:** `/api/llm_commentary {ov_excd,ov_symb}` = overseas commentary
   (`_build_ov_ai_context`); `/api/llm_ask {scope,id,excd,question}` = app-wide chat (`_ask_context` routes
   stock/etf/ov/macro/index). The reusable widget is `_ASK_WIDGET_HTML` — every page exposes `window.KMKT_ASK()`
   returning `{scope,id,excd}` (read at send-time so dynamic ids work). Inject via `_inject_ask` (reports) or a
   page-local setter (overseas/macro/index).
8. **FRESHNESS / anti-stale (mandatory for every AI prompt).** The local model's weights are ~1.5yr stale, but
   stocks need *today's* facts. Solution = **data grounding**: fetch live data, inject it + today's date, and
   command the model "신선 데이터만 인용, 사전 학습 지식은 신뢰하지 말 것, 없으면 모른다고 하라." Never let an AI
   feature answer from the model's own memory. (Verified: a stock Q correctly answered "제공된 화면 정보로는 알 수
   없습니다" instead of hallucinating.) `app.py`'s data is a *simulated future* dataset (trap #11) — grounding also
   keeps the AI consistent with it.
9. **AI 답변 텍스트는 반드시 마크다운 렌더링(기본).** 모든 AI 기능의 *답변 본문*은 raw 마크다운(`**`,`#`,`- `,`*`)이
   그대로 보이면 안 된다. 답변 컨테이너에 `class="kmkt-md"`를 주고, 누적 버퍼를 `window.kmktMd(buf)`(없으면 동등
   fallback)로 `innerHTML` 갱신한다. **추론(`kind==="reasoning"`) 박스는 dim plain(`e2`/`<br>`)으로 둬도 됨** —
   마크다운 렌더는 *답변*에만. 새 AI 출력은 `streamLLM`/`startAI`/ask 위젯의 `md(ansBuf)` 패턴을 복제. `window.kmktMd`와
   `.kmkt-md` CSS 는 `_ASK_WIDGET_HTML` 이 페이지에 주입(위젯 없는 페이지면 위젯/CSS부터 주입). (리포트 'AI 요약'이
   raw 로 흘리던 것 changes_60 에서 수정.)

## 12. Structure changes → guideline sync + regression gate (mandatory)

The single biggest source of wasted cycles here is **docs drifting from code** (a stale CLAUDE.md
sends the next agent down the wrong path) and **structural edits that silently break the app**
(changes_73 moved files and the app stopped booting, yet was logged "verified"). Two hard rules:

1. **Regression gate before "verified" (ties into §2.4 / §5).** Any change to imports, file layout,
   routes, the `_inject_*` wiring, or `scripts/ui_templates.py`/`pure_helpers.py` MUST pass
   `uv run scripts/smoke_check.py` (`SMOKE PASS ✓`). It imports the live backend, boots a test
   client, hits critical static routes, asserts injection invariants, and compares rendered output
   to a golden hash baseline (`tests/golden_render.json`). `py_compile` + stubbed unit tests do **not**
   exercise the real import — they will not catch this class of break. For an *intentional* markup
   change, re-baseline: `uv run scripts/smoke_check.py --golden write` (and say so in the changes log).
   **If you moved/refactored a data collector, ALSO run `uv run scripts/api_smoke.py`** (`API-SMOKE
   PASS ✓`) — it calls collectors and fails ONLY on code-level NameError/Attr/Import (network/env →
   SKIP), so it catches a broken name reference the render gate can't.
   **If you added/renamed a module under `scripts/` that the dynamically-loaded backend imports, add it
   to `application_build/market_dashboard.spec` `hiddenimports`** (PyInstaller can't trace dynamic
   imports → the frozen .app would miss it). Currently: `market_dashboard3_realtime`, `ui_templates`,
   `pure_helpers`. (See _STATUS trap #40.)

   > 🪝 **The gate is now ALSO auto-enforced by Claude Code Hooks (changes_88).** `.claude/settings.json`
   > runs `scripts/hooks/gate_dispatch.py`: a `PostToolUse` mark drops a sentinel when a gated
   > `scripts/*.py` file is edited, and the `Stop` hook runs `smoke_check` once per turn — FAIL exits 2
   > and blocks the turn-end. This is a safety net, **not a substitute for the protocol**: still run the
   > gate yourself and quote it in the log (the hook only fires inside Claude Code sessions; other agents/
   > CI don't get it). `scripts/hooks/` and `scripts/reflect/` are hook entrypoints, NOT imported by the
   > backend → they do **not** go in `hiddenimports` or `CODEMAP`. See also `_STATUS.md` trap #42
   > (guarded auto-reflect: corrections → `dev_notes/`, or `_STATUS.md` only when `KMKT_REFLECT_MODE=auto`
   > + conf ≥ 0.90 with backup/integrity-gate/provenance + auto-rollback). Default mode = `propose`
   > (no canonical auto-edit until a human flips it).

2. **When project structure changes, update the guideline files in the SAME session.** "Structure"
   = adding/moving/deleting files or dirs, changing the entry point, adding/removing/renaming routes,
   or relocating major constants/templates. Then, before the session ends:
   - Regenerate the line index: `python3 scripts/gen_codemap.py` (→ `docs/CODEMAP.md`).
   - Update root `CLAUDE.md` §0 (file structure / entry point) **and** `_STATUS.md` (feature table /
     Active Traps). New gotcha → also `docs/DEBUG_JOURNAL.md` + a `_STATUS.md` trap.
   - If the *working method itself* changed, update this file (`application_build/CLAUDE.md`).
   - **Never end a session with the guideline files contradicting the code.** A doc-vs-code mismatch
     is a future cycle-waster; treat fixing it as part of the task, not optional cleanup.
   - **작동 방식(프로토콜·게이트·도구)이 바뀌면 root `CLAUDE.md` + this file 둘 다** 같은 세션에 갱신.

3. **Proactive structural health — notice inefficiency before it bites, and propose redesign.**
   Run `python3 scripts/health_check.py` at session start and after structural changes. It measures
   creep metrics (main file size, biggest function, route density, `_STATUS` ❓ backlog, CODEMAP/
   `_STATUS` doc-drift, `dev_notes` backlog) against thresholds. **On any ⚠️ WARN, surface it to the
   user and propose the improvement/redesign** — do not silently ignore it, and do not silently
   refactor (redesign is Tier-L → user approval + plan file + gates). This is the mechanism by which
   the agent, over many sessions, *actively* moves the project toward an efficient structure instead
   of only preserving the current one. (The health check is advisory; the agent + user decide.)

> Rationale: this turns "the agent keeps re-learning the project and re-debugging the same errors"
> into a *cumulative* system — every solved error lands in the journal, every structural change keeps
> the map current, and every risky edit is gated. Read `docs/DEBUG_JOURNAL.md` + `docs/CODEMAP.md`
> first and you inherit all prior learning instead of rediscovering it.
