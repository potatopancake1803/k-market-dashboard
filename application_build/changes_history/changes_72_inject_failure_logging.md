---
id: 72
title: Surface silent _inject_* anchor failures via logger.warning (no logic change)
date: 2026-06-17 14:20 KST
agent: Claude (Opus 4.8)
area: [observability, html-injection]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done

Implemented external-review item #4: the string-anchor HTML injection helpers used to
**fail silently** — if a build's markup changed and an anchor (`</nav>`, `<footer`,
`</head>`, `</body>`, or a loader swap target) disappeared, the injection was simply
skipped with no signal, and neither `py_compile` nor `test_client` would catch it. Now
each such miss emits a `logger.warning`. **No existing behavior was changed** — only
warnings were added on the skip paths.

Touched functions:
- `_inject_m4_tab` (~L2162) — split the combined guard so a missing `</nav>` vs `<footer`
  each log distinctly; the `not code` early-return stays silent (normal, not an anchor failure).
- `_inject_fx` (~L2502) — warn when `</head>` or `</body>` absent.
- `_inject_realtime` (~L3108) — warn on missing `</body>` (skip) and missing `</head>`
  (style skip); `not code` stays silent.
- `_inject_loader` (~L12916) — warn when `</head>` absent, and warn+`continue` per `swaps`
  entry whose `old` target isn't present.
- `_inject_floating_ai` (~L12985) — warn when `</body>` not found (widget appended at EOF).

## How it was done

- Added `import logging` to the stdlib import block (~L55).
- Added a module logger right after `app = Flask(__name__)` (~L91):
  `logging.basicConfig(level=logging.WARNING)` + `logger = logging.getLogger("kmkt")`.
- Each helper: kept the original `if "anchor" not in html: return html` control flow,
  inserting a `logger.warning(...)` immediately before the early `return`, or converting a
  silent `else`/`rfind == -1` branch into a warned branch. Logic and outputs are identical
  on the happy path.

Root cause being surfaced (not changed): the injectors are coupled to the exact markup
strings produced by the report builders (`dashboard.py`, `company_report_ver2`,
`etf_dashboard_ver2`); an upstream markup tweak can break injection with zero error.
Warnings make that observable in the app log.

## Verification

```
$ python3 -m py_compile scripts/market_dashboard3_realtime.py   # → exit 0 (COMPILE OK)
$ grep -nE 'logger\.warning' scripts/market_dashboard3_realtime.py   # → 9 warning sites across the 5 helpers
$ uv run ... python -m pytest tests/test_core_functions.py -q   # → 26 passed (no regression)
```

- `py_compile` passes (supporting evidence only).
- 26 core-function tests still green after the edit (no import/compile regression).
- **Warning path exercised at runtime** (3.10 + archive stubs, anchorless input):
  ```
  >>> md._inject_fx("<p>no anchors here</p>")
  WARNING:kmkt:_inject_fx: </head> anchor not found — FX head/style injection skipped
  WARNING:kmkt:_inject_fx: </body> anchor not found — FX JS injection skipped
  # return value == input (unchanged)  → True
  ```
  Confirmed the warning fires AND the function returns its input unchanged (happy path intact).
- Marked `verified` on this basis. (Full happy-path visual rendering is covered by the
  existing per-page feature rows / 미검증 대기열.)

## Notes & Traps

- Logging is configured with `logging.basicConfig(level=logging.WARNING)`. If a future
  change adds its own `basicConfig`/handler, ensure it doesn't suppress the `kmkt` logger.
- Scope kept minimal per review/§8: only the 5 named `_inject_*` helpers; no behavior change,
  no new deps, no refactor of the underlying string-anchor approach (that's a larger task —
  the durable fix would be dedicated comment anchors like `<!--KMKT_M4_SLOT-->` in the builders).
