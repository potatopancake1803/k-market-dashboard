---
id: 73
title: File/folder structure cleanup — move legacy/test/icon residue to archives, rename confusing files
date: 2026-06-17 16:00 KST
agent: Claude (Opus 4.8)
area: [ops, housekeeping]
status: verified
files:
  - (no source code changed — file moves/renames only)
  - tests/legacy/ (new)
  - docs/legacy/ (new)
  - application_build/_archive/icon_attempts/ (new)
  - scripts/archive/ (added 4 legacy entry files)
---

## What was done

Pure file/folder housekeeping — **no code logic changed, no `rm` used (mv only)**.
Moved test/temp/legacy/icon-residue files into dedicated archives, renamed Korean /
whitespace / meaningless filenames to stable English names. Live build/runtime inputs
were identified in PHASE 1 and deliberately left in place.

### PHASE 1 key findings (analysis-first, before any move)
- The **live report builders** imported by the running backend are `company_report_ver2` /
  `etf_dashboard_ver2`, already in `scripts/archive/`. The four root-level `scripts/*.py`
  (`market_dashboard.py`, `market_dashboard3.py`, `company_report.py`, `etf_dashboard.py`)
  are **not imported** anywhere → safe to archive.
- **Live icon build chain:** `build.sh → make_app_icon.py → icon_normalize.py`, reading
  `application_build/app_icon_final/squircle_fixed.png` and writing `icon.png` / `icon.icns`.
  `.spec` bundles `icon.png`/`icon.icns`; `realtime.py::_logo_path()` reads `icon.png`.
  → `app_icon_final/`, `icon.png`, `icon.icns`, `squircle_fixed.png`, `make_app_icon.py`,
  `icon_normalize.py`, `make_icon.sh` are **LIVE — NOT moved**.
- The other icon generator scripts (`apple_icon_generator.py`, `background_remover.py`,
  `build_macos26_icon.py`, `fix_icon.py`, `generate_final_icon.py`, `generate_framed_icon.py`)
  are **not** invoked by the build chain → archived.
- **`--apple`** is actually a **PNG image** (binary, misnamed). **`아이콘복원.txt`** = an LLM's
  icon-restore reasoning notes. **`예시_SPCX.md`** = a scraped Yahoo Finance SPCX page.

### Moves (원래 경로 → 새 경로)
**To `tests/legacy/`** (none imported by app/build):
- `test_market_dashboard3_realtime.py`, `test_ov_api.py`, `test_ov_api_keys.py`,
  `test_ov_price.py`, `test_ps_import.py`, `test_rt_kis_get.py`,
  `_sheet_test.py`, `scratch_test_psutil.py`, `ov.html`, `test_html.html`

**To `docs/legacy/`**:
- `claude_agent_guidelines_template.md`, `claude_guidelines_template_v2.md`
- `application_build/titlebar_transparency_fix.md` (unreferenced code note)

**To `application_build/_archive/icon_attempts/scripts/`**:
- `apple_icon_generator.py`, `background_remover.py`, `build_macos26_icon.py`,
  `fix_icon.py`, `generate_final_icon.py`, `generate_framed_icon.py`

**To `application_build/_archive/icon_attempts/`** (dirs):
- `application_build/application_icon_0/` (build uses `application_icon/` (absent) + icon.png fallback — `_0` unused)
- `icon_maker/` (root) → `application_build/_archive/icon_attempts/icon_maker/`

**To `scripts/archive/`**:
- `scripts/market_dashboard.py`, `scripts/market_dashboard3.py`,
  `scripts/company_report.py`, `scripts/etf_dashboard.py`

### Renames (원래 이름 → 새 이름; all moved into `application_build/_archive/icon_attempts/`)
| old | new |
|-----|-----|
| 레알진짜끝.png | icon_attempt_final.png |
| 아이콘복원.txt | icon_restore_notes.txt |
| 예시_SPCX.md | example_SPCX.md |
| --apple (PNG) | icon_attempt_apple.png |
| Pasted Graphic.icns | icon_attempt_pasted.icns |
| "app_icon_final 123.png" | icon_attempt_final_v2.png |
| app_icon_gpt.png / gpt2 / gpt3 | icon_attempt_gpt_v1 / v2 / v3.png |
| app_icon_gpt2_bgrmd.png / bgrmd2 | icon_attempt_gpt_v2_nobg.png / nobg2.png |
| app_real_final.png / app_real_final_1.png | icon_attempt_real_v1.png / v2.png |
| app_icon_final.png | icon_attempt_final_master.png |
| app_icon_final-removebg-preview.png | icon_attempt_final_nobg.png |
| icon_final.png | icon_attempt_final_alt.png |
| icon_icon.png | icon_attempt_icon_icon.png |
| krx_app.png / krx_app_appicon.png / krx_app_transparent_backup.png | icon_attempt_krx_app.png / _appicon.png / _nobg.png |
| ver2.png / ver2_appicon.png | icon_attempt_ver2.png / _appicon.png |
| figma_export_720-25.png | icon_attempt_figma_export.png |
| AppIcon_Squircle.icns (application_build root) | icon_attempt_squircle.icns |
| apple_icon_spec.md | apple_icon_spec.md (moved, name kept) |

## Files NOT moved (and why)
- **root `API.env`** — HELD. Content **differs** from `API_documents/API.env` (12 vs 17 keys),
  AND it is **actively loaded**: `app.py:158` (`_r/"API.env"`) and `realtime.py:5412,5891`
  read `"API.env"` / `"../API.env"`. Moving it would break env loading. (Spec step 5 assumed a
  duplicate; PHASE 1 proved it is live + different → hold, per spec's "다르면 보류".)
- **AGENTS.md / ANTIGRAVITY.md** — kept at root **per user decision** (asked explicitly). They are
  other agents' (Codex / Antigravity) entry-convention files; moving them risks breaking auto-discovery.
- **app_icon_final/, icon.png, icon.icns, squircle_fixed.png, make_app_icon.py,
  icon_normalize.py, make_icon.sh** — live build chain (see PHASE 1).
- **scripts/archive/*_ver2.py** — live imports.
- **tests/test_core_functions.py** — untouched (explicit no-move).
- **application_build/test_squircle.py** — left in place (icon test paired with build; not residue).

## Verification

```
$ python3 -m py_compile scripts/market_dashboard3_realtime.py   # COMPILE OK
$ python3 -m py_compile application_build/app.py                # COMPILE OK
# all LIVE paths resolve after moves:
  icon.png, icon.icns, squircle_fixed.png, app_icon_final/squircle_fixed.png,
  make_app_icon.py, icon_normalize.py, API.env, API_documents/API.env,
  scripts/archive/{company_report_ver2,etf_dashboard_ver2}.py  → all OK
$ uv run ... pytest tests/test_core_functions.py -q            # 26 passed
```
- Root now contains only: CLAUDE.md, HANDOFF.md, README.md, TECH_REVIEW, AGENTS.md,
  ANTIGRAVITY.md, .env, API.env, API_documents/, application_build/, changes_history/,
  data/, docs/, market_intel/, output/, scripts/, tests/ (+ dotfiles). No loose
  test_/scratch/ov.html/template files remain.

## Notes & Traps
- **NEW TRAP candidate:** root `API.env` is **live + distinct** from `API_documents/API.env`
  (subset of keys). Don't "dedupe" by deleting it — both are loaded. (Added to _STATUS.md traps.)
- The icon build source is `app_icon_final/squircle_fixed.png` (NOT the now-archived
  `icon_attempt_*` images). If a future agent regenerates the icon, point `make_app_icon.py`
  at the file under `app_icon_final/`, not the archive.
- `make_icon.sh` expects a dir named `application_icon/` (singular, no `_0`) — that dir does
  **not** exist; the script falls back to `icon.png`. The archived `application_icon_0/` was
  never the one it reads. (Recorded so nobody "restores" `_0` expecting the build to use it.)
- Output-versioning rule (CLAUDE.md §7) not applicable — no pipeline output files changed,
  only source/asset relocation.
- Numbering: this is `changes_73` (prev `changes_72`; `changes_62–70` are the consolidated
  fork from changes_71).
