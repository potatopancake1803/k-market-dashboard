---
id: 81
title: Developer Mode — click an element in the running app → capture location+source+memo as an LLM-readable note
date: 2026-06-17 23:40 KST
agent: Claude (Opus 4.8)
area: [feature, tooling, dx]
status: verified
files:
  - scripts/dev_overlay.py (new)
  - scripts/market_dashboard3_realtime.py
  - application_build/market_dashboard.spec
  - dev_notes/README.md (new)
---

## What was done — purpose
A **Developer Mode** so the user can flag "fix this" spots in the running app and hand the coding
agent the **exact location + source (file:line) + the driving function + a memo** in ONE markdown
file — so the agent goes straight to the spot instead of token-wastefully hunting. This pairs with
the changes_77/78 modularization: a clicked element's id/class is greped against `ui_templates.py` /
the backend → precise `file:line`.

## How it works
- **Gated by env `KMKT_DEV=1`.** Off (default) ⇒ overlay not injected, `/api/dev/*` return 403,
  render golden baseline unchanged. On ⇒ overlay auto-injected into every HTML page via
  `@app.after_request` (covers iframes/reports too — no per-page edits).
- **In-app:** toggle with **⌘⇧D** (Ctrl+Shift+D). Shows a cyan DEV frame + badge + crosshair cursor.
  Hover highlights elements; **click / right-click** an element opens an inspector popover with:
  route, tag/id/classes/role/text, CSS selector, **grep anchors**, and **source candidates
  (file:line + snippet)** fetched from `/api/dev/locate`. A memo textarea + **Save** writes the note.
  The badge's `🖱 검사` toggle lets the user navigate the app normally, then re-arm to capture.
- **Endpoints (KMKT_DEV only):**
  - `POST /api/dev/locate` → `dev_locate()` greps `scripts/ui_templates.py`,
    `scripts/market_dashboard3_realtime.py`, the archive builders, and `dashboard.py` for the
    element's id / distinctive classes / text → ranked `{file,line,kind,term,snippet}` candidates.
  - `POST /api/dev/note` → `dev_write_note()` writes `dev_notes/<ts>_<slug>.md` (human sections +
    a raw JSON block) and returns the path.
- **Module:** all logic + the overlay template live in `scripts/dev_overlay.py` (imported by main);
  main only wires the 2 routes + the after_request + the env gate. Added `dev_overlay` to the build
  spec `hiddenimports` (trap #40). `dev_notes/README.md` documents the queue + agent usage.

## Verification
```
# render gate (DEV OFF) — golden unchanged → zero impact on normal app:
$ uv run scripts/smoke_check.py → SMOKE PASS ✓ (golden 9 routes)

# backend (DEV ON, headless test_client):
  overlay injected on / : True ; on /backtest_page : True ; on /__ping (JSON) : False
  /api/dev/locate kmktAiSend → 200, 5 candidates incl.
      scripts/ui_templates.py:1518 [id]  <button id="kmktAiSend" class="kmkt-ai-send" …>
      scripts/ui_templates.py:1690 [id]  …getElementById('kmktAiSend')…   (the JS handler)
      scripts/ui_templates.py:1604 [class] .kmkt-ai-send{…}                (the CSS)
  /api/dev/note → 200 {ok:true, path:"dev_notes/…md"} ; file content = full LLM-readable note ✔

# visual (preview, overlay injected + toggled on): screenshot shows cyan DEV frame, DEV badge
#   (●DEV | 🖱검사 | hint | ✕), and the inspector popover (route/tag/id/text + source candidate
#   ui_templates.py:142 + memo textarea + 💾저장). node --check on the overlay JS: OK.
```

## Notes & Traps
- **Gate:** `_DEV_ENABLED = os.environ.get("KMKT_DEV")=="1"`. Both the injector and the endpoints
  check it; smoke_check (no KMKT_DEV) sees the unchanged app → golden stays valid.
- Overlay JS deliberately avoids regex/backslash escapes that bite in Python strings (uses
  `split(' ')`, template literals); the one `replace(/\\s+/g,' ')` is written `\\s` (→ JS `\s`).
- Run dev mode: `KMKT_DEV=1 uv run application_build/app.py` then ⌘⇧D. Notes land in `dev_notes/`.
- `application_build/.claude/launch.json` has a `dashboard-dev` config (KMKT_DEV=1) for preview.
- Next idea (optional): a `/api/dev/notes` list + an in-app "처리됨" move-to-done; AST-based source
  mapping for even tighter file:line (current grep is already accurate for id/class).
