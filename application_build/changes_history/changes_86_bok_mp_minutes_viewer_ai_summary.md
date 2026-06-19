---
id: 86
title: Integrate BOK Monetary Policy Committee (bok_mp) minutes viewer and AI summary
date: 2026-06-18 20:30 KST
agent: Antigravity
status: verified
files:
  - scripts/market_dashboard3_realtime.py
  - scripts/ui_templates.py
---

## What was done
- Added `bok_mp` ("🏛️ 금융통화위원회") category to research board.
- Implemented `_bok_mp_list(page)` to scrape and parse the Monetary Policy Committee minutes and decision announcements using `listCont.do` with specific filters (`menuNo=201154`, `depth2=200038`, `depth3=201154`).
- Implemented `_bok_mp_read(nid)` to retrieve and parse content/PDF attachment link of individual MPC items.
- Relaxed digit checks in `_research_pdf_bytes`, `research_pdf2`, `api_research_summary`, and `_ask_context` for custom `boardId_nttId` format of `bok_mp`.
- Appended `['bok_mp', '🏛️ 금융통화위원회']` to the list of categories in the frontend template in `scripts/ui_templates.py`.

## How it was done
- Scraped list data using Bank of Korea dynamic HTML AJAX endpoint `/portal/singl/newsData/listCont.do` with headers and parameters.
- Parsed titles, dates (compounded to `YY.MM.DD` format), and compiled `nid` as `boardId_nttId` since board IDs vary per MPC board type (e.g. `B0000245` for 의사록 and `P0000093` for 의결사항).
- Implemented view scrapper by fetching `/portal/bbs/{board_id}/view.do?nttId={ntt_id}` to locate target PDF attachments (`/fileSrc/...pdf`).
- Registered `bok_mp` in `_RESEARCH_CATS` and updated list routing inside `_research_list` and `_research_read`.
- Re-baselined the golden render test hash due to the template layout change.

## Verification
- Ran regression gate: `uv run scripts/smoke_check.py --golden write` -> `SMOKE PASS ✓`
- Ran API check gate: `uv run scripts/api_smoke.py` -> `API-SMOKE PASS ✓`
- Regenerated line index: `python3 scripts/gen_codemap.py` -> `WROTE docs/CODEMAP.md`

## Notes & Traps
- MPC item `nid` has a custom `boardId_nttId` format (e.g., `B0000245_10098513`) which is not fully numeric. Backend checks of `nid.isdigit()` must explicitly bypass or relax check for `bok_mp` to prevent `400 Bad Request` or context-extraction failure.
