#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Reflect — capture stage (TIER 1-B, changes_88).

Claude Code UserPromptSubmit hook. Scans each user message for *correction* patterns
(multilingual, deterministic regex — no LLM call) and, if one is found above a floor,
appends a candidate to a queue. It NEVER edits canonical docs and NEVER blocks the prompt
(silent exit 0). The guarded apply stage (`apply.py`, Stop hook) decides what to do with
the queue.

Two-tier gating (per plan):
  confidence >= 0.90  -> (apply.py in 'auto' mode) append to _STATUS.md, fully guarded.
  0.75 <= conf < 0.90 -> always routed to dev_notes/ for human review.
  conf < 0.75         -> not queued at all (bare "no"/negation = too weak).

Storage: application_build/changes_history/_autoreflect/queue.jsonl  (append-only JSONL).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QDIR = ROOT / "application_build" / "changes_history" / "_autoreflect"
QUEUE = QDIR / "queue.jsonl"

CAPTURE_FLOOR = 0.75  # below this, do not queue (weak negations are noise)

# (weight, compiled pattern, label). Highest matched weight wins.
_PATTERNS = [
    # STRONG (0.92): names both the wrong and the right thing.
    (0.92, re.compile(r"(?:아니|아니라|아니야|아니에요|아냐).{0,24}(?:말고|대신|보다)"), "ko_not_X_but_Y"),
    (0.92, re.compile(r"(?:말고|대신)\s*\S+.{0,12}(?:로|으로|를|을)?\s*(?:해|하자|하라|하세요|쓰|써)"), "ko_use_Y"),
    (0.92, re.compile(r"\bnot\b[^.]{0,40}\b(?:but|use|instead|rather)\b", re.I), "en_not_X_use_Y"),
    (0.90, re.compile(r"\bshould\s+(?:be|use|have)\b", re.I), "en_should"),
    (0.90, re.compile(r"틀렸|잘못(?:됐|되|했)"), "ko_wrong"),
    # MEDIUM (0.80): a clear corrective directive, but not naming the replacement.
    (0.80, re.compile(r"(?:하지\s*마|쓰지\s*마|하면\s*안\s*(?:돼|된다))"), "ko_dont"),
    (0.80, re.compile(r"\b(?:don'?t|do not)\b", re.I), "en_dont"),
    (0.80, re.compile(r"\b(?:instead|rather than)\b", re.I), "en_instead"),
    (0.80, re.compile(r"다시\s*(?:해|하|작성|만들)"), "ko_redo"),
    (0.78, re.compile(r"그게?\s*아니|그건\s*아니|이게\s*아니"), "ko_thats_not_it"),
]


def _read_hook_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def score(text: str):
    """Return (confidence, label) for the strongest matched correction pattern, or (None, None)."""
    best_w, best_l = 0.0, None
    for w, pat, label in _PATTERNS:
        if pat.search(text):
            if w > best_w:
                best_w, best_l = w, label
    if best_l is None:
        return None, None
    return best_w, best_l


def main() -> int:
    try:
        data = _read_hook_input()
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return 0
        conf, label = score(prompt)
        if conf is None or conf < CAPTURE_FLOOR:
            return 0  # not a (strong enough) correction
        QDIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session": data.get("session_id", ""),
            "confidence": round(conf, 2),
            "pattern": label,
            "excerpt": prompt[:280],
        }
        with QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # fail-open: never disrupt the user's prompt
    return 0  # UserPromptSubmit: silent, no context injection


if __name__ == "__main__":
    sys.exit(main())
