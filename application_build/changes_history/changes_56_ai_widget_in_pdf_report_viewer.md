---
id: 56
title: AI 질문하기 widget inside the research-report PDF viewer (/pdf_view) — reads the specific open report (cat:nid)
date: 2026-06-16 04:20 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- The securities-report viewer (`/pdf_view`, the tab opened from 증권사 리포트 → 원문) had **no floating AI
  widget** — it was the one content surface missing it. Added it, and made the AI read **the report currently
  open**, not a generic list.
- `_PDF_VIEW_HTML`: before `</body>`, added a per-request `window.KMKT_ASK` setter
  (`{scope:__ASK_SCOPE__, id:__ASK_ID__}`) + a `__KMKT_ASK_WIDGET__` placeholder.
- `pdf_view()`: parses `cat`/`nid` from the embedded `src` (`/research_pdf2?cat=&nid=`). If it's a real research
  report (`cat∈_RESEARCH_CATS`, `nid` digit) → `ask_scope="research", ask_id="cat:nid"`; otherwise falls back to
  `scope="market"` (non-research PDFs still get a working widget). Fills `__ASK_SCOPE__`/`__ASK_ID__`.
- Module-load: `_PDF_VIEW_HTML.replace("__KMKT_ASK_WIDGET__", _ASK_WIDGET_HTML)` (not `_inject_floating_ai`, to
  avoid a duplicate static setter/FAB — the page sets its own dynamic `KMKT_ASK`).
- `_ask_context(scope="research", ident)`: new branch — if `ident` is `"cat:nid"`, read **that** report's text
  (`_research_read(cat,nid)`, or `_market_brief_text()` for the market cat) and return it as
  "[지금 보고 있는 증권사 리포트 …]". Image-only PDFs (no extractable text) → a graceful hint to paste content
  into 참고 데이터. The old list-based behavior (ident = bare category) is unchanged.

## How it was done
- Theme: the widget auto-syncs dark mode via its existing `MutationObserver` on `documentElement.class`; the
  pdf_view already toggles `html.dark` on the `kmkt` postMessage, so no extra wiring needed.
- The intent gate (changes_55) means "이 리포트 요약해줘" does NOT trigger a web search — it just reads the report.

## Verification
- `python3 -m py_compile` → PY OK.
- Headless (MARKET_PORT 8793–8795, /__ping keepalive, single invocation):
  - `GET /pdf_view?src=%2Fresearch_pdf2%3Fcat%3Ddaily%26nid%3D…` → contains `kmktAiFab`; setter renders as
    `{scope:"research",id:"daily:99999"}`. Largest inline `<script>` → `node --check` **NODE OK**.
  - Real nid: `/api/research?cat=daily` → nid 36408 → `POST /api/llm_ask {scope:research,id:"daily:36408",
    question:"이 리포트 핵심만 3줄로 요약해줘",provider:gemini,gemini-2.5-flash}` → `chitchat=False,
    news-search=False` (no reflexive search) → **287-char answer citing the report's own content**
    ("KOSPI는 중동 긴장 완화와 미국 기술주 강세에 힘입어 1.2% 상승한 8,644.6p…"). ✅ End-to-end verified.
  - Server tracebacks: 0.
- Transient Google 503 hit `gemini-3.5-flash` on one attempt (graceful fallback); 2.5-flash returned the answer.

## Notes & Traps
- Non-research PDFs (한국은행 `/fileSrc/…`, image-only broker PDFs) get the widget at `scope:"market"`; for
  image PDFs there's no extractable text, so the research branch returns a "paste into 참고 데이터" hint.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
