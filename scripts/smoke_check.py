#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "flask>=3.0",
#   "httpx>=0.27",
#   "polars>=1.0",
#   "pandas>=2.0",
#   "numpy>=1.26",
#   "pyarrow>=15.0",
#   "lxml>=5.0",
#   "plotly>=5.20",
#   "python-dotenv>=1.0",
#   "scipy>=1.11",
#   "websockets>=12.0",
# ]
# ///
"""Fast, network-free regression gate for the K-Market backend.

WHY THIS EXISTS
  The #1 recurring failure in this project is "fixed it → broke something else" and
  "py_compile passed so I called it verified" (see _STATUS.md Correction log; changes_73
  shipped an app-down `ModuleNotFoundError` that py_compile + stubbed unit tests missed).
  This script is the objective gate that catches that class of regression in seconds:

    1. IMPORT the live backend module      → catches import/sys.path/archive breakage
    2. BOOT a Flask test client            → catches app-construction errors
    3. GET critical static routes (200)    → catches dead/renamed routes
    4. Assert render INVARIANTS            → catches silent _inject_* anchor failures
    5. Compare rendered output to a GOLDEN  → catches *unintended* output changes
       hash baseline                         (perfect for verifying refactors are byte-identical)

  No network, no GUI, no KIS/DART keys needed (only static shells are rendered).

USAGE
  python3 scripts/smoke_check.py                # run the gate (compare to golden if present)
  python3 scripts/smoke_check.py --golden write # snapshot current render hashes as the baseline
                                                #   → do this BEFORE a refactor, then re-run plain
                                                #     AFTER to prove rendering is unchanged.
  exit code 0 = PASS, 1 = FAIL (use in scripts/CI).

WHEN TO RUN (mandated by CLAUDE.md operating loop)
  - After ANY change to imports, file structure, routes, or the `_inject_*` / template wiring.
  - Before marking such a change "verified".
  - After an INTENTIONAL template/UI change, re-baseline with `--golden write` (and say so in
    the changes log), so the next agent's golden compare stays meaningful.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
GOLDEN = ROOT / "tests" / "golden_render.json"

# Static shells that render WITHOUT network/keys (handlers return a template constant or a
# local asset). These cover the largest inline templates, so the golden hash strongly pins
# any template extraction/refactor to byte-identical output.
STATIC_ROUTES = [
    "/",
    "/research_page",
    "/index_page",
    "/macro_page",
    "/backtest_page",
    "/realtime_page",
    "/logo.png",
    "/favicon.ico",
    "/plotly.js",
]
ALIVE_ROUTES = ["/__ping"]

# (route, [substrings that MUST be present]) — guards silent injection failures.
INVARIANTS = [
    ("/", ["kmktAI", "kmkt-ai-bar"]),  # floating AI widget + Gemini-style input bar injected
]


def load_backend():
    os.environ.setdefault("MI_NO_OPEN", "1")
    os.environ.setdefault("MI_NO_PREWARM", "1")
    os.environ.setdefault("MARKET_PORT", "8799")
    for p in (str(SCRIPTS), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return importlib.import_module("market_dashboard3_realtime")


def main(argv: list[str]) -> int:
    mode = "check"
    if "--golden" in argv:
        i = argv.index("--golden")
        mode = argv[i + 1] if i + 1 < len(argv) else "write"

    fails: list[str] = []
    notes: list[str] = []

    # 1) import (the changes_73-class check)
    try:
        m = load_backend()
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE FAIL ✗  could not import backend: {e!r}")
        return 1
    notes.append("import backend OK")

    # 2) boot test client
    try:
        client = m.app.test_client()
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE FAIL ✗  could not build test client: {e!r}")
        return 1
    notes.append("Flask test client OK")

    # 3) routes 200 + collect hashes
    hashes: dict[str, str] = {}
    for route in STATIC_ROUTES + ALIVE_ROUTES:
        try:
            r = client.get(route)
        except Exception as e:  # noqa: BLE001
            fails.append(f"{route} raised {e!r}")
            continue
        if r.status_code != 200:
            fails.append(f"{route} -> HTTP {r.status_code}")
            continue
        if route in STATIC_ROUTES:
            hashes[route] = hashlib.sha256(r.data).hexdigest()
    notes.append(f"{len(STATIC_ROUTES) + len(ALIVE_ROUTES)} routes returned 200")

    # 4) invariants
    for route, subs in INVARIANTS:
        try:
            body = client.get(route).get_data(as_text=True)
        except Exception as e:  # noqa: BLE001
            fails.append(f"invariant {route} raised {e!r}")
            continue
        for s in subs:
            if s not in body:
                fails.append(f"{route} missing required marker {s!r}")

    # 5) golden compare / write
    if mode == "write":
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
        notes.append(f"golden baseline written ({len(hashes)} routes) → {GOLDEN.relative_to(ROOT)}")
    elif GOLDEN.exists():
        old = json.loads(GOLDEN.read_text(encoding="utf-8"))
        compared = 0
        for route, h in hashes.items():
            if route in old:
                compared += 1
                if old[route] != h:
                    fails.append(
                        f"GOLDEN MISMATCH {route} — rendered output changed "
                        f"(if intentional, re-run with --golden write)"
                    )
        notes.append(f"golden compared ({compared} routes)")
    else:
        notes.append("no golden baseline yet (run: smoke_check.py --golden write)")

    # report
    for n in notes:
        print(f"  · {n}")
    if fails:
        print("\nSMOKE FAIL ✗")
        for f in fails:
            print(f"  ✗ {f}")
        return 1
    print("\nSMOKE PASS ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
