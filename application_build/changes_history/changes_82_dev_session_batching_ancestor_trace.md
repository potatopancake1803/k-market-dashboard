---
id: 82
title: Dev Mode — session batching (badge counter + dropdown, one TODO .md) + ancestor-trace locate
date: 2026-06-17 19:30 KST
agent: Claude (Opus 4.8)
area: [feature, dx]
status: verified
files:
  - scripts/dev_overlay.py
  - scripts/market_dashboard3_realtime.py
  - docs/CODEMAP.md (regenerated)
---

## What was done
Two enhancements to Developer Mode (changes_81), from the user's reviewed proposals
(방안2 session batching, 방안1-2 ancestor trace):

### 1) Session batching — collect many captures → ONE LLM-ready TODO file
- **UI (phase-1, intentionally NOT a full sidebar — user agreed):** the inspector popover gains
  **`➕ 세션 추가`** (alongside `💾 즉시 저장`). The DEV badge gains a **counter chip `📌 N`**; clicking
  it opens a compact **dropdown session panel** (title input + item list with ✕ remove + `➕ 새 세션`
  / `💾 세션 저장`). Dark, matches the inspector. No left sidebar.
- **Backend (in-process store, single-user local):** `_DEV_SESSION = {"title","items"}` + routes
  `/api/dev/session/{state(GET),add,remove,new,save}` (all `KMKT_DEV`-gated). `save` writes
  `dev_notes/session_<date>_<slug>.md` via `dev_write_session()` and clears the store.
- **Output format:** a checklist — session header (route(s)/count/agent-instructions) + per-item
  `- [ ] Task N` (route·template·selector·source file:line·anchors·memo) + a full candidate table +
  raw JSON. The agent processes the whole session as one planned change → fewer "fix-one-break-
  another" regressions, deduped common info (one header vs N files).

### 2) Ancestor trace (방안1-2) — locate elements with no own id/class
- The overlay JS now climbs up to 6 ancestors to find the nearest `id`/distinctive class and sends
  `ancestor_id`/`ancestor_classes`. `_dev_terms()` adds them as lowest-priority `ancestor` grep terms,
  so a bare `<span>`/`<div>` is still mapped to source via its container. Anchors/markdown include it.

## Verification
```
# render gate (DEV OFF) → golden unchanged:
$ uv run scripts/smoke_check.py → SMOKE PASS ✓
# node --check on overlay JS → OK ; py_compile → OK
# backend (DEV ON, headless test_client):
  session state(init) empty → add×2 → remove(0) → add → save("랜딩 다듬기") = 200 {path: session_…md}
    → state empty after save ; save-empty → 400.  session .md = correct TODO checklist (2 routes).
  ancestor locate (only ancestor_id=kmktAiSend) → 2 candidates, kind="ancestor" ✔
# visual (preview, markup injected): DEV badge shows 📌 2 blue chip; dropdown session panel renders
#   (title "랜딩 페이지 다듬기" + 2 items with selector+memo + 새 세션/세션 저장). Screenshot confirmed.
```

## Notes & Traps
- Session store is an in-process global → resets if the server restarts (acceptable for local
  single-user; the user saves before restarting). Not persisted to disk by design (low overhead).
- `dev_write_session` and `dev_write_note` coexist: `➕ 세션 추가` batches, `💾 즉시 저장` writes one-off.
- Routes: 73 → **78** (5 session endpoints). CODEMAP regenerated.
- The full macOS source-list sidebar was prototyped then dropped per the user's call ("사이드바는
  과함; 배지 카운터로 충분") — phase-1 is the lighter badge-chip dropdown. A sidebar can return later.
- Next (optional, from 방안1): console/network error snapshot (3), dynamic source scan (5).
