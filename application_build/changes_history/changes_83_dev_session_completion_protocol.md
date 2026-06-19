---
id: 83
title: Dev session — embed a completion protocol (checkbox + 처리 결과 + move to done/) so processed sessions are reflected, not re-hunted
date: 2026-06-17 20:05 KST
agent: Claude (Opus 4.8)
area: [dx, docs]
status: verified
files:
  - scripts/dev_overlay.py
  - dev_notes/README.md
  - CLAUDE.md (root)
---

## Why
User asked: after the agent finishes a saved session, how is the session file handled — is the
result reflected back? **It wasn't, beyond a loose convention.** The session md only said "flip [x]",
with no record of what was changed and no archive step → the next session would re-ask "is this done?"
(the exact token-waste this feature exists to prevent).

## What was done
Made the completion behavior **explicit and self-describing inside every session file** (the agent
reads the file, so the protocol lives there — no server logic needed; the agent does the edits/move
with its file tools).

- `dev_write_session()` agent-instructions block rewritten into a **4-step processing protocol**:
  1. process the whole TODO as one plan; `smoke_check` after each fix.
  2. flip `[ ]`→`[x]` for done items (leave `[ ]` + reason for undone).
  3. **fill the new `## ✅ 처리 결과` section** — changed file:line, `changes_X_*.md` id, smoke result.
  4. when fully done, **move the file to `dev_notes/done/`** (separates the done queue); if partial,
     leave it in `dev_notes/` and just update `[x]`/result.
- Added a `## ✅ 처리 결과` placeholder section (상태/바꾼 곳/변경 로그/검증) before the JSON appendix.
- `dev_notes/README.md` agent-usage rewritten to match (process → reflect in file → move to `done/`).
- Root `CLAUDE.md` doc-map: added `dev_notes/*.md` row ("세션 시작 시 미처리 확인; 처리 후 [x]+결과+done/").

## Verification
```
$ python3 -m py_compile scripts/dev_overlay.py → OK
$ uv run scripts/smoke_check.py (DEV OFF) → SMOKE PASS ✓ (golden unchanged — output format change is
  dev-only, not in any rendered page)
# headless: session save → md now contains the 4-step protocol + an empty `## ✅ 처리 결과` section. ✔
```

## Notes & Traps
- This only changes the **session markdown content** (dev-only); no rendered page changed → golden safe.
- `dev_notes/done/` is created lazily by the agent on first completion (not pre-created).
- The protocol is convention enforced by the file text + README + CLAUDE.md, not code — appropriate,
  since the agent (not the server) is what completes a session.
