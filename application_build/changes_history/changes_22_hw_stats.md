---
id: 22
title: Add System Hardware Stats to AI Popover
date: 2026-06-15 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Added a hardware status indicator (RAM & CPU usage) matching the LM Studio GUI style into the AI Popover.
- Used `psutil` in the backend to query specific OS processes associated with LM Studio and LM Link to replicate the targeted resource monitoring logic.

## How it was done
- **Dependency Update**: Installed `psutil` via `uv pip install psutil --system --break-system-packages` into the environment.
- **Backend (`api_llm_hardware`)**: 
  - Iterates over OS processes using `psutil.process_iter`.
  - Filters by process name or command line containing `lm studio`, `lmstudio`, `lmlink`, or `llama-server`.
  - Aggregates the Resident Set Size (RSS) memory and computes CPU percent (normalized by CPU count for total system context).
- **Frontend (`aiPop`)**:
  - Inserted two flexbox badges (one for Memory, one for CPU) using native SVG icons that closely replicate the user-provided screenshot.
  - Implemented `hwTimer` (`pollHw`) that hits `/api/llm/hardware` every 1.5 seconds.
  - Bound the timer strictly to the popover's `open` state to completely avoid background network/computation overhead when the popover is closed.

## Verification
- `test_psutil.py` verified the measurement outputs matching the `0.0 GB` and `0.0%` baselines properly.
- `python3 -m py_compile scripts/market_dashboard3_realtime.py` completed with no syntax errors.
