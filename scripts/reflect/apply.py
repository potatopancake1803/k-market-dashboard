#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Reflect — guarded apply stage (TIER 1-B, changes_88).

Claude Code Stop hook (also runnable by hand). Drains the capture queue written by
`capture.py` and routes each item under STRICT safety guards. Never blocks the Stop
(a doc note is not a reason to halt) — silent exit 0.

ROUTING (two-tier confidence gating)
  MODE 'propose' (DEFAULT, per plan — earn trust first):
      EVERY item -> a dev_notes/ review note. No canonical doc is ever auto-edited.
  MODE 'auto' (flip KMKT_REFLECT_MODE=auto, or DEFAULT_MODE below, once trusted):
      confidence >= AUTO_THRESHOLD (0.90) -> guarded append to _STATUS.md
      confidence  < AUTO_THRESHOLD        -> dev_notes/ review note

THE 3 MANDATORY GUARDS (only on a canonical-doc write)
  1. BACKUP   : copy _STATUS.md -> _autoreflect/_STATUS_bak_YYYYMMDD_HHMM.md  (only rollback path; no git)
  2. INTEGRITY: after writing, run a STRUCTURAL validator (required sections present, file did not
                shrink, still UTF-8) AND `scripts/smoke_check.py`. NOTE: _STATUS.md is NOT imported
                by the backend, so smoke_check alone cannot catch a corrupted doc — the structural
                validator is the real doc check; smoke_check guards that we didn't disturb code.
                If EITHER fails -> auto-rollback from the backup.
  3. PROVENANCE: append who/what/why/confidence/result to _autoreflect_log.md.

WHERE auto content lands in _STATUS.md
  A dedicated, clearly-fenced section "## ▶ Auto-reflect log" at the end — NOT inside the
  human-curated numbered Active-Traps list (auto-numbering that list would risk corrupting the
  project's highest-value index). A reviewer promotes good entries to a numbered trap later.
  This keeps machine writes structurally isolated and trivially reversible.

CLI
  apply.py            # hook/run mode: drain queue
  apply.py --list     # show pending queue
  apply.py --undo     # restore _STATUS.md from the newest backup (\"방금 자동수정 되돌려\")
  apply.py --mode auto|propose
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CH = ROOT / "application_build" / "changes_history"
QDIR = CH / "_autoreflect"
QUEUE = QDIR / "queue.jsonl"
LOG = CH / "_autoreflect_log.md"
STATUS = CH / "_STATUS.md"
DEVNOTES = ROOT / "dev_notes"

DEFAULT_MODE = "auto"             # auto: conf>=AUTO_THRESHOLD auto-writes canonical docs (backup+gate+rollback guarded); set KMKT_REFLECT_MODE=propose to revert
AUTO_THRESHOLD = 0.90             # only >= this is eligible for canonical auto-write
REQUIRED_STATUS_SECTIONS = ["## ▶ How to run", "## ▶ Feature health", "## ▶ Active traps"]
AUTO_SECTION = "## ▶ Auto-reflect log (machine-captured — review & promote to a numbered trap)"


# ---------- helpers ----------
def _mode() -> str:
    m = os.environ.get("KMKT_REFLECT_MODE", "").strip().lower()
    if m in ("auto", "propose"):
        return m
    return DEFAULT_MODE


def _read_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    items = []
    for ln in QUEUE.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            items.append(json.loads(ln))
        except Exception:
            pass
    return items


def _clear_queue() -> None:
    try:
        QUEUE.unlink(missing_ok=True)
    except Exception:
        pass


def _log(line: str) -> None:
    try:
        QDIR.mkdir(parents=True, exist_ok=True)
        new = not LOG.exists()
        with LOG.open("a", encoding="utf-8") as f:
            if new:
                f.write("# Auto-reflect provenance log (changes_88)\n\n"
                        "Every machine-captured correction and what was done with it. "
                        "Columns: time · result · confidence · pattern · target · excerpt.\n\n")
            f.write(line + "\n")
    except Exception:
        pass


def _slug(text: str, n: int = 40) -> str:
    s = re.sub(r"\s+", "-", text.strip())
    s = re.sub(r"[^0-9A-Za-z가-힣\-]", "", s)
    return (s[:n] or "note").strip("-")


# ---------- dev_notes routing (low-conf / propose) ----------
def _to_devnotes(item: dict, reason: str) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    fn = DEVNOTES / f"{ts}_autoreflect_{_slug(item.get('excerpt',''))}.md"
    DEVNOTES.mkdir(parents=True, exist_ok=True)
    body = f"""# 🪞 Auto-reflect 후보 (사람 검토용)

- **생성**: {item.get('ts','')}  (route via reflect/apply.py)
- **사유**: {reason}
- **확신도**: {item.get('confidence')}  · **패턴**: {item.get('pattern')}  · **세션**: {item.get('session','')[:12]}

> 🤖 이 노트는 세션 중 사용자 교정으로 추정되는 발화를 자동 포착한 것이다(확신도 임계 미만이거나 propose 모드).
> 검토 후: 진짜 영구 규칙이면 `_STATUS.md`의 적절한 섹션(Active Traps 등)에 **사람이** 정식 등재하고,
> 아니면 이 파일을 지워라. (정본 자동수정은 KMKT_REFLECT_MODE=auto + 확신도 ≥ {AUTO_THRESHOLD} 에서만.)

## 📋 포착된 교정 발화

- [ ] 검토: 아래 발화가 영구 규칙으로 승격할 가치가 있는가?

```
{item.get('excerpt','')}
```

## ✅ 처리 결과
- 상태: ⬜ 미처리
- 승격 여부: (예: _STATUS.md Active Traps #42 로 등재 / 폐기)
"""
    fn.write_text(body, encoding="utf-8")
    return fn.name


# ---------- canonical auto-write (auto mode, high-conf) ----------
def _structural_ok() -> tuple[bool, str]:
    try:
        txt = STATUS.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"unreadable: {e}"
    for sec in REQUIRED_STATUS_SECTIONS:
        if sec not in txt:
            return False, f"missing required section: {sec}"
    return True, "ok"


def _smoke_ok() -> tuple[bool, str]:
    try:
        p = subprocess.run(["uv", "run", "scripts/smoke_check.py"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return p.returncode == 0, (p.stdout or "")[-200:]
    except Exception as e:
        return False, f"smoke run error: {e}"


def _append_auto_section(item: dict) -> None:
    txt = STATUS.read_text(encoding="utf-8")
    entry = (f"- {item.get('ts','')} · conf={item.get('confidence')} · "
             f"pattern={item.get('pattern')} · session={item.get('session','')[:12]}\n"
             f"  > {item.get('excerpt','').strip()}\n")
    if AUTO_SECTION in txt:
        txt = txt.rstrip() + "\n" + entry
    else:
        txt = (txt.rstrip() + "\n\n---\n\n" + AUTO_SECTION + "\n\n"
               "> Machine-captured corrections (KMKT_REFLECT_MODE=auto, conf≥threshold). "
               "Each is a *captured user correction*, not a vetted rule — a human promotes "
               "good ones into the numbered Active-Traps list, then may delete the line here.\n\n"
               + entry)
    STATUS.write_text(txt, encoding="utf-8")


def _auto_write(item: dict) -> str:
    """Guarded write of one high-conf item to _STATUS.md. Returns result string for the log."""
    QDIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M")
    backup = QDIR / f"_STATUS_bak_{stamp}.md"
    pre_size = STATUS.stat().st_size
    shutil.copy2(STATUS, backup)  # GUARD 1: backup

    try:
        _append_auto_section(item)
    except Exception as e:
        shutil.copy2(backup, STATUS)
        return f"ROLLED-BACK (write error: {e}; restored {backup.name})"

    # GUARD 2: integrity = structural validator AND smoke_check, + non-shrink.
    struct_ok, struct_msg = _structural_ok()
    not_shrunk = STATUS.stat().st_size >= pre_size
    smoke_ok, smoke_msg = _smoke_ok()
    if struct_ok and not_shrunk and smoke_ok:
        return f"APPLIED -> _STATUS.md (backup {backup.name})"
    # rollback
    shutil.copy2(backup, STATUS)
    why = []
    if not struct_ok:
        why.append(f"struct:{struct_msg}")
    if not not_shrunk:
        why.append("file-shrank")
    if not smoke_ok:
        why.append(f"smoke-fail:{smoke_msg.strip()}")
    return f"ROLLED-BACK ({'; '.join(why)}; restored from {backup.name})"


# ---------- orchestration ----------
def run_drain() -> int:
    items = _read_queue()
    if not items:
        return 0
    mode = _mode()
    for it in items:
        conf = float(it.get("confidence", 0) or 0)
        excerpt = (it.get("excerpt", "") or "").replace("\n", " ")[:80]
        if mode == "auto" and conf >= AUTO_THRESHOLD:
            result = _auto_write(it)
        else:
            reason = ("propose-mode (auto-write disabled)" if mode != "auto"
                      else f"below auto threshold {AUTO_THRESHOLD}")
            fn = _to_devnotes(it, reason)
            result = f"-> dev_notes/{fn}"
        _log(f"- {it.get('ts','')} · **{result}** · conf={conf} · "
             f"pattern={it.get('pattern')} · mode={mode} · \"{excerpt}\"")
    _clear_queue()
    return 0


def cmd_list() -> int:
    items = _read_queue()
    if not items:
        print("[reflect] queue empty")
        return 0
    print(f"[reflect] {len(items)} pending (mode={_mode()}, auto_threshold={AUTO_THRESHOLD}):")
    for it in items:
        print(f"  conf={it.get('confidence')} {it.get('pattern')}: {it.get('excerpt','')[:90]!r}")
    return 0


def cmd_undo() -> int:
    baks = sorted(QDIR.glob("_STATUS_bak_*.md"))
    if not baks:
        print("[reflect] no _STATUS backup to restore")
        return 1
    newest = baks[-1]
    shutil.copy2(newest, STATUS)
    print(f"[reflect] restored _STATUS.md from {newest.name}")
    _log(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} · **UNDO restore** from {newest.name}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--list" in args:
        return cmd_list()
    if "--undo" in args:
        return cmd_undo()
    if "--mode" in args:
        i = args.index("--mode")
        if i + 1 < len(args):
            os.environ["KMKT_REFLECT_MODE"] = args[i + 1]
    try:
        return run_drain()
    except Exception:
        return 0  # fail-open: never block Stop


if __name__ == "__main__":
    sys.exit(main())
