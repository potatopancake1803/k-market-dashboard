#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Claude Code hook dispatcher — auto-enforce the smoke_check regression gate.

WHY (TIER 1-A, changes_88)
  The project's #1 failure is "edited backend → broke import/route/render → logged
  'verified' anyway" (changes_73). This makes `scripts/smoke_check.py` run WITHOUT
  the agent having to remember to, by wiring two Claude Code hooks (see
  `.claude/settings.json`):

    PostToolUse(Edit|Write|MultiEdit) -> `gate_dispatch.py mark`
        Cheap & silent. If the edited file is in the GATED set (backend import graph),
        drop a sentinel file. Otherwise do nothing. NEVER blocks editing.

    Stop                              -> `gate_dispatch.py gate`
        If the sentinel exists, run smoke_check ONCE for the whole turn, clear the
        sentinel, and on FAIL exit 2 with the output on stderr so Claude Code feeds
        it back and the agent must fix the break before the turn ends.

  Design rationale (token efficiency): smoke_check is ~1.1s but per-edit running would
  redundantly re-run on multi-edit turns. Sentinel+Stop runs it at most once per turn
  and costs ~0 on turns that touch no backend file. (changes_88 plan, option C.)

GATED SET
  *.py directly under scripts/ (the backend: market_dashboard3_realtime, ui_templates,
  pure_helpers, smoke_check, etc.) and scripts/archive/*.py (the live report builders
  imported via the sys.path shim, trap #38). Subdirs like scripts/hooks/ and
  scripts/reflect/ are intentionally EXCLUDED — they are not imported by the backend,
  so editing them cannot break the render gate.

FAIL-OPEN
  Any parsing/IO error in `mark` exits 0 silently (a hook must never block normal work).
  `gate` only ever blocks on an actual smoke_check FAIL.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
ARCHIVE = SCRIPTS / "archive"

# Sentinel lives in the project's existing cache dir (created if missing).
SENTINEL_DIR = Path.home() / ".cache" / "kmkt_m4"
SENTINEL = SENTINEL_DIR / ".smoke_dirty"


def _read_hook_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _is_gated(file_path: str) -> bool:
    """True iff the edited file is part of the backend import graph smoke_check covers."""
    if not file_path:
        return False
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = (ROOT / p).resolve()
        else:
            p = p.resolve()
    except Exception:
        return False
    if p.suffix != ".py":
        return False
    # Directly under scripts/ (backend + gates) OR under scripts/archive/ (live builders).
    return p.parent == SCRIPTS or p.parent == ARCHIVE


def _mark() -> int:
    """PostToolUse: drop a sentinel if a gated file was edited. Always silent, always exit 0."""
    data = _read_hook_input()
    tool_input = data.get("tool_input") or {}
    # Edit / Write / MultiEdit all carry file_path in tool_input.
    file_path = tool_input.get("file_path") or ""
    if _is_gated(file_path):
        try:
            SENTINEL_DIR.mkdir(parents=True, exist_ok=True)
            SENTINEL.write_text(file_path, encoding="utf-8")
        except Exception:
            pass  # fail-open: never block editing
    return 0


def _gate() -> int:
    """Stop: if dirty, run smoke_check once. Exit 2 on FAIL (blocks turn-end with output)."""
    data = _read_hook_input()
    # Guard against a wedge: if we are already inside a Stop-hook continuation, don't
    # block again (the agent is presumably trying to fix it).
    stop_active = bool(data.get("stop_hook_active"))

    if not SENTINEL.exists():
        return 0
    try:
        SENTINEL.unlink()
    except Exception:
        pass

    try:
        proc = subprocess.run(
            ["uv", "run", "scripts/smoke_check.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as e:
        # Could not run the gate (e.g. uv missing). Inform but do not hard-block.
        sys.stderr.write(f"[gate] could not run smoke_check: {e}\n")
        return 0

    if proc.returncode == 0:
        # Quiet success — one short line, no token bloat.
        print("[gate] SMOKE PASS ✓")
        return 0

    # FAIL: surface the smoke output to the agent.
    out = (proc.stdout or "") + (proc.stderr or "")
    msg = (
        "[gate] smoke_check FAILED after a backend/template edit. Fix before finishing:\n"
        + out.strip()
    )
    if stop_active:
        # Avoid an infinite Stop loop; report but allow stop.
        sys.stderr.write(msg + "\n[gate] (already in stop continuation; not re-blocking)\n")
        return 0
    sys.stderr.write(msg + "\n")
    return 2  # exit 2 → Claude Code blocks the Stop and feeds stderr back


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "mark":
        return _mark()
    if mode == "gate":
        return _gate()
    sys.stderr.write("usage: gate_dispatch.py [mark|gate]\n")
    return 0  # unknown mode: fail-open


if __name__ == "__main__":
    sys.exit(main())
