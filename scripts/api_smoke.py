#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "flask>=3.0", "httpx>=0.27", "polars>=1.0", "pandas>=2.0", "numpy>=1.26",
#   "pyarrow>=15.0", "lxml>=5.0", "plotly>=5.20", "python-dotenv>=1.0",
#   "scipy>=1.11", "websockets>=12.0",
# ]
# ///
"""API-level smoke test — exercises the data-source COLLECTORS (which do network I/O),
to catch the one class of regression the render gate (`smoke_check.py`) cannot:
a **call-time NameError / AttributeError / ImportError** introduced by moving a function
to another module (the move compiles + imports fine, but a referenced name is now missing).

KEY IDEA — separate CODE failure from ENVIRONMENT failure:
  Each probe calls a collector. If it raises NameError/AttributeError/ImportError/
  UnboundLocalError  → **FAIL** (a real code/wiring bug, e.g. a bad extraction).
  Any other exception (network/timeout/HTTP error/empty data/missing key/market closed)
  → **SKIP** (the function body executed far enough to make the call — wiring is fine).
  A clean return → **OK**.

So a green run here means "no broken name references", even offline or out of market hours.

USAGE
  uv run scripts/api_smoke.py            # run all probes
  exit 0 = no CODE failures (OK/SKIP only); 1 = at least one CODE failure.

Run this (in addition to `smoke_check.py`) after moving/refactoring any collector.
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# Exceptions that mean the WIRING is broken (a move/refactor bug) — these FAIL.
# (TypeError excluded on purpose: a wrong probe-arg would false-FAIL; extractions don't change
#  signatures. The real move-bug signature is a missing NAME/attr/import at call time.)
CODE_ERRORS = (NameError, AttributeError, ImportError, UnboundLocalError)


def load_backend():
    os.environ.setdefault("MI_NO_OPEN", "1")
    os.environ.setdefault("MI_NO_PREWARM", "1")
    os.environ.setdefault("MARKET_PORT", "8797")
    for p in (str(SCRIPTS), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return importlib.import_module("market_dashboard3_realtime")


def main() -> int:
    try:
        m = load_backend()
    except Exception as e:  # noqa: BLE001
        print(f"API-SMOKE FAIL ✗  import backend: {e!r}")
        return 1

    def call(name, *args, **kw):
        fn = getattr(m, name, None)
        if fn is None:
            return ("FAIL", name, "function not found on module (renamed/removed?)")
        try:
            fn(*args, **kw)
            return ("OK", name, "")
        except CODE_ERRORS as e:
            return ("FAIL", name, f"{type(e).__name__}: {e}")
        except Exception as e:  # noqa: BLE001  (env/network — not a code bug)
            return ("SKIP", name, f"{type(e).__name__} (env/network, body executed)")

    # Probes: the overseas/global data-source closure (changes_80) + a few core collectors.
    # Args chosen to drive the function into its real body (a real symbol / code).
    probes = [
        ("_kis_keys",),
        ("_fnum", "1,234.5"),
        ("_global_macro_snapshot",),
        ("_fred_one", "DGS10"),
        ("_finnhub_quote", "AAPL"),
        ("_fmp_get", "quote/AAPL"),
        ("_get_overseas_financials", "AAPL"),
        ("_get_analyst_view", "AAPL"),
        ("_get_valuation_peers", "AAPL"),
        ("_get_price_technicals", "AAPL"),
        ("_polygon_grouped_one",),
    ]
    results = []
    for p in probes:
        try:
            results.append(call(*p))
        except Exception as e:  # noqa: BLE001  (call() shouldn't raise, but be safe)
            results.append(("FAIL", p[0], f"probe harness error: {e!r}"))

    # also a couple of network /api routes via test client (tolerant)
    try:
        c = m.app.test_client()
        for route in ["/api/global_macro", "/api/us_list?filter=turnover"]:
            try:
                r = c.get(route)
                tag = "OK" if r.status_code == 200 else "SKIP"
                results.append((tag, route, "" if tag == "OK" else f"HTTP {r.status_code}"))
            except CODE_ERRORS as e:
                results.append(("FAIL", route, f"{type(e).__name__}: {e}"))
            except Exception as e:  # noqa: BLE001
                results.append(("SKIP", route, f"{type(e).__name__} (env)"))
    except Exception as e:  # noqa: BLE001
        results.append(("SKIP", "test_client", repr(e)))

    fails = [r for r in results if r[0] == "FAIL"]
    for tag, name, note in results:
        mark = {"OK": "✓", "SKIP": "·", "FAIL": "✗"}[tag]
        print(f"  {mark} {tag:4} {name}  {note}")
    print()
    if fails:
        print(f"API-SMOKE FAIL ✗  ({len(fails)} code failure(s) — broken name references)")
        return 1
    ok = sum(1 for r in results if r[0] == "OK")
    skip = sum(1 for r in results if r[0] == "SKIP")
    print(f"API-SMOKE PASS ✓  (no code failures; {ok} OK, {skip} skipped on env/network)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
