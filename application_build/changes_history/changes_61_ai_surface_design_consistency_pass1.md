---
id: 61
title: AI-surface design consistency (pass 1) — unify reasoning-box accent + answer markdown across all AI features toward the ask-widget / domestic standard
date: 2026-06-16 07:45 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done (작업3, pass 1 — AI surfaces)
Audit found the same concepts implemented multiple ways: **reasoning/think boxes** (`kmkt-ai-reason` / inline
`#ai-think` / `.rk` — 4 variants), **answers** (markdown vs raw), **loaders** (`ai-loader` bounce vs `ai-typing`
pulse). Unified the two with the clearest, lowest-risk visual divergence toward the polished ask-widget standard:
- **Reasoning-box accent.** Canonical `.kmkt-ai-reason` uses a **blue** left border `rgba(10,132,255,.4)`, but the
  stock & overseas AI modals (inline `#ai-think`) and the report "AI 요약" (`.rp-sum .rk`) used a **gray**
  `var(--line)` border. Aligned all to the blue accent → consistent across every AI surface (4 spots now match).
- **Answer markdown** (from changes_60): all AI answers render via `.kmkt-md` (`window.kmktMd`), including the
  report summary that previously showed raw `**`/`#`. So answer typography is now uniform app-wide.

## Verification
- `python3 -m py_compile` → PY OK. `node --check` on the research page's summarize/render script → OK.
- `grep` confirms 4 blue-accent reasoning borders and **0** remaining gray-accent reasoning borders. 0 tracebacks.
- **Visual = unverified** (needs GUI) — confirm reasoning boxes look identical across 종목/해외/리포트/채팅 and
  answers render as markdown everywhere.

## Notes & Traps
- **Remaining for a later pass:** the two inline "AI 생각 중" loaders still differ (`.ai-loader`/`.ai-dot`
  bouncing in stock/overseas vs `.ai-typing`/`<i>` pulsing in macro/backtest) — both are 3-dot indicators, minor;
  unifying needs markup changes across pages. AI buttons (`rp-btn sum` / `btn-glass g-ai` / `tab-btn`) also vary.
  Broader page-level (non-AI) design unification (작업3 full scope) intentionally deferred — needs GUI to avoid
  blind-CSS regressions.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
