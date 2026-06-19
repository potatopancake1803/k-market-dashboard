#!/usr/bin/env python3
"""Project structural-health monitor — the PROACTIVE layer of the agent's self-learning system.

WHY: `_STATUS.md` / `DEBUG_JOURNAL.md` / `CODEMAP.md` / the smoke gates *preserve* learning and
*catch regressions* (reactive). But nothing watches the project's structure drifting back toward
inefficiency over many sessions. This script measures a handful of structural-health metrics, compares
them to thresholds, and emits ⚠️ WARN + a concrete suggestion when a line is crossed — so the agent
**proactively notices** "this is getting inefficient" and surfaces a redesign proposal to the user
(redesign itself is Tier-L → needs approval; this only flags + suggests).

It also catches **doc↔code drift** (the #1 cycle-waster): stale CODEMAP, stale `_STATUS.md` latest-entry,
moved files that Dev Mode greps. Stdlib-only, instant: `python3 scripts/health_check.py`.

RUN IT: at session start, and after structural changes. If it prints any ⚠️, tell the user what it
found and propose the fix/redesign — don't silently ignore or silently refactor.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "scripts" / "market_dashboard3_realtime.py"
UI = ROOT / "scripts" / "ui_templates.py"
STATUS = ROOT / "application_build" / "changes_history" / "_STATUS.md"
CODEMAP = ROOT / "docs" / "CODEMAP.md"
CHANGES = ROOT / "application_build" / "changes_history"
DEVNOTES = ROOT / "dev_notes"

# Thresholds (tune as the project grows). Crossing → ⚠️ WARN + suggestion.
T_MAIN_LINES = 9000          # main backend file; over this → extract more (templates/logic already split)
T_FUNC_LINES = 420           # any single top-level function; over → split for readability
T_UNVERIFIED = 30            # ❓ rows in _STATUS feature table; over → run the 미검증 소거 대기열
T_DEVNOTES_BACKLOG = 8       # unprocessed dev_notes sessions; over → process them
T_ROUTES_ONE_FILE = 90       # routes in a single module; over → Blueprint split candidate


def _lines(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0


def main() -> int:
    findings: list[tuple[str, str]] = []  # (level, message); level ∈ {WARN, INFO, OK}

    def warn(m): findings.append(("WARN", m))
    def info(m): findings.append(("INFO", m))
    def ok(m): findings.append(("OK", m))

    src = MAIN.read_text(encoding="utf-8") if MAIN.exists() else ""
    main_lines = _lines(MAIN)

    # 1) main backend size (creep detection)
    if main_lines > T_MAIN_LINES:
        warn(f"main backend {main_lines:,} lines > {T_MAIN_LINES:,} → 다음 추출 후보(수집기→data_sources, "
             f"라우트→Blueprint; plan: changes_80_plan). 사용자에게 재설계 제안.")
    else:
        ok(f"main backend {main_lines:,} lines (≤ {T_MAIN_LINES:,})")

    # 2) biggest top-level function (readability)
    try:
        tree = ast.parse(src)
        funcs = [(n.end_lineno - n.lineno + 1, n.name) for n in tree.body
                 if isinstance(n, ast.FunctionDef) and n.end_lineno]
        if funcs:
            big = max(funcs)
            if big[0] > T_FUNC_LINES:
                warn(f"가장 큰 함수 `{big[1]}` {big[0]} lines > {T_FUNC_LINES} → 분할 고려(읽기/수정 비용↑).")
            else:
                ok(f"largest function `{big[1]}` {big[0]} lines (≤ {T_FUNC_LINES})")
    except Exception as e:  # noqa: BLE001
        info(f"function-size check skipped (ast parse: {e})")

    # 3) routes in one file (Blueprint candidate)
    routes = len(re.findall(r"@app\.(get|post|put|delete)\(", src))
    if routes > T_ROUTES_ONE_FILE:
        warn(f"{routes} routes in one module > {T_ROUTES_ONE_FILE} → Blueprint 분할 후보.")
    else:
        ok(f"{routes} routes in main (≤ {T_ROUTES_ONE_FILE})")

    # 4) ❓ unverified backlog in _STATUS
    if STATUS.exists():
        st = STATUS.read_text(encoding="utf-8")
        unv = st.count("❓")
        if unv > T_UNVERIFIED:
            warn(f"_STATUS 에 ❓(미검증) {unv}개 > {T_UNVERIFIED} → '미검증 소거 대기열'을 세션마다 1~2개 소거.")
        else:
            ok(f"_STATUS ❓ unverified = {unv} (≤ {T_UNVERIFIED})")
        # 6) _STATUS latest-entry drift vs actual max changes_X
        m = re.search(r"changes_(\d+)_[\w-]+\.md", st)
        latest_claimed = int(m.group(1)) if m else -1
        nums = [int(x.group(1)) for x in (re.match(r"changes_(\d+)_", f) for f in os.listdir(CHANGES)) if x]
        max_file = max(nums) if nums else -1
        if max_file > latest_claimed:
            warn(f"_STATUS 'Latest history entry'(changes_{latest_claimed})가 실제 최신(changes_{max_file})보다 뒤짐 "
                 f"→ _STATUS 갱신 누락(doc-code drift).")
        else:
            ok(f"_STATUS latest-entry in sync (changes_{max_file})")
    else:
        warn("_STATUS.md 없음")

    # 5) dev_notes backlog (unprocessed sessions)
    if DEVNOTES.exists():
        pend = [f for f in os.listdir(DEVNOTES) if f.endswith(".md") and f != "README.md"]
        if len(pend) > T_DEVNOTES_BACKLOG:
            warn(f"dev_notes 미처리 {len(pend)}개 > {T_DEVNOTES_BACKLOG} → 세션으로 묶어 일괄 처리.")
        elif pend:
            info(f"dev_notes 미처리 {len(pend)}개 — 처리 대기: {', '.join(pend[:5])}")
        else:
            ok("dev_notes 미처리 없음")

    # 7) CODEMAP staleness (route count drift)
    if CODEMAP.exists():
        cm = CODEMAP.read_text(encoding="utf-8")
        m = re.search(r"라우트:\s*\*\*(\d+)\*\*", cm)
        cm_routes = int(m.group(1)) if m else -1
        if cm_routes != routes:
            warn(f"CODEMAP 라우트 수({cm_routes}) ≠ 실제({routes}) → `python3 scripts/gen_codemap.py` 재생성.")
        else:
            ok(f"CODEMAP in sync ({routes} routes)")

    # 8) Dev-Mode source list health (moved files break locate silently)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dev_overlay", ROOT / "scripts" / "dev_overlay.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
        missing = [r for r in mod._DEV_SOURCE_REL if not (ROOT / r).exists()]
        if missing:
            warn(f"dev_overlay._DEV_SOURCE_REL 에 없는 파일: {missing} → Dev Mode locate 가 조용히 누락. 목록 갱신.")
        else:
            ok(f"Dev-Mode source list OK ({len(mod._DEV_SOURCE_REL)} files)")
    except Exception as e:  # noqa: BLE001
        info(f"dev_overlay check skipped ({e})")

    # 9) golden baseline present
    if (ROOT / "tests" / "golden_render.json").exists():
        ok("golden_render.json present (render gate baselined)")
    else:
        warn("tests/golden_render.json 없음 → `uv run scripts/smoke_check.py --golden write`.")

    # ── report ──
    warns = [m for lvl, m in findings if lvl == "WARN"]
    for lvl, m in findings:
        mark = {"WARN": "⚠️ ", "INFO": "ℹ️ ", "OK": "✅"}[lvl]
        print(f"  {mark} {m}")
    print()
    if warns:
        print(f"HEALTH: ⚠️  {len(warns)} warning(s) — 사용자에게 알리고 개선/재설계를 제안하라.")
    else:
        print("HEALTH: ✅ 모든 지표 정상.")
    print(f"(summary: main {main_lines:,}L · ui_templates {_lines(UI):,}L · {routes} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
