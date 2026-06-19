#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Claude Code SessionStart hook — inject a small, capped project digest.

WHY (TIER 1-A, changes_88)
  Re-reading the 444-line `_STATUS.md` every session is token-expensive. This emits a
  TIGHT digest (target <= ~20 lines) of the two things most likely to be missed and
  most actionable at session start:
    1. Health WARNs (doc/code drift, oversize, dev_notes backlog) from health_check.py
    2. A pointer to Active Traps + the newest few headlines (full text stays in _STATUS.md)

  Output goes to stdout; Claude Code adds a SessionStart hook's stdout to the session
  context. Kept deliberately small so it SAVES tokens vs. reading the whole file, not
  adds to them. Fail-open: any error prints nothing and exits 0.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "application_build" / "changes_history" / "_STATUS.md"

MAX_TRAP_HEADLINES = 5
HEALTH_TIMEOUT_S = 8


def _health_warns() -> list[str]:
    try:
        proc = subprocess.run(
            ["uv", "run", "scripts/health_check.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=HEALTH_TIMEOUT_S,
        )
    except Exception:
        return []
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = []
    for ln in out.splitlines():
        s = ln.strip()
        if not s:
            continue
        # WARN lines and the dev_notes-backlog info line are the actionable ones.
        if "⚠️" in s or "미처리" in s:
            lines.append(s)
    return lines


def _trap_headlines() -> tuple[int, list[str]]:
    if not STATUS.exists():
        return 0, []
    txt = STATUS.read_text(encoding="utf-8", errors="replace")
    # Isolate the Active traps section.
    m = re.search(r"## ▶ Active traps(.*?)(?:\n## |\Z)", txt, re.S)
    body = m.group(1) if m else txt
    pat = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*", re.M)
    found = []  # (num, headline)
    for mm in pat.finditer(body):
        num = int(mm.group(1))
        head = mm.group(2).strip()
        if len(head) > 78:
            head = head[:75] + "…"
        found.append((num, head))
    total = len(found)
    # Newest = highest numbers; show those.
    newest = sorted(found, key=lambda t: t[0], reverse=True)[:MAX_TRAP_HEADLINES]
    return total, [f"  #{n} {h}" for n, h in newest]


def main() -> int:
    try:
        out = ["[session-brief] K-Market — read _STATUS.md ▶ for full state (changes_88 / hooks active)"]

        warns = _health_warns()
        if warns:
            out.append("Health:")
            out.extend("  " + w for w in warns)
        else:
            out.append("Health: ✅ no WARN (or health_check unavailable)")

        total, heads = _trap_headlines()
        if total:
            out.append(f"Active traps: {total} total — full text in _STATUS.md. Newest:")
            out.extend(heads)

        sys.stdout.write("\n".join(out) + "\n")
    except Exception:
        pass  # fail-open: never disrupt session start
    return 0


if __name__ == "__main__":
    sys.exit(main())
