---
id: 58
title: Report viewer AI reads the PDF directly — send original PDF bytes to Gemini as multimodal inline_data (native text + table + OCR), not just the Naver text scrape
date: 2026-06-16 05:50 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **Problem the user raised:** in the report PDF viewer, the AI was reading the **Naver research page HTML text**
  (`_research_read`), not the PDF. That misses content that lives only in the PDF (full body, **earnings tables,
  charts**) and fails entirely on **scanned/image PDFs**.
- **Fix (Gemini multimodal direct read):** when the report viewer chat (`/api/llm_ask`, `scope=research`,
  `id="cat:nid"`) runs on **Gemini**, the server now fetches the report's original PDF bytes and sends them to
  Gemini as an `inline_data` document part (`mime_type: application/pdf`). Gemini reads the PDF natively —
  embedded text, tables, layout, and **scanned pages via built-in OCR**. The list-page "✨ AI 요약"
  (`/api/research_summary`) does the same when provider=gemini.
- New helper **`_research_pdf_bytes(cat, nid, max_mb=18)`** — fetches the raw PDF (Naver research → stock.pstatic
  PDF, or 한국은행), validates `%PDF` magic + size cap, returns bytes or None. (Reuses the proxy logic of
  `research_pdf2`.)
- **`_gemini_stream(..., pdf_bytes=None)`** — prepends a base64 `inline_data` PDF part to the current user turn.
- **`llm_ask` Gemini branch** — for research scope, fetch `_research_pdf_bytes`; if present, emit a
  "📑 PDF 원문(NkB)을 Gemini 에 직접 전달…" note and prepend "첨부된 PDF가 이 리포트의 원문입니다…" to the user
  message so the PDF is the primary source. Falls back to the text scrape when there's no PDF (e.g. daily 마감시황).
- **Local LLM unchanged** (text-only): still uses the Naver text scrape. PDF-direct is Gemini-only by design (chosen
  approach: no new dependency, handles scanned PDFs).

## Verification
- `python3 -m py_compile` → PY OK.
- Headless (MARKET_PORT 8797/8798, /__ping keepalive, single invocation):
  - **daily:36408** (no attached PDF) → `_research_pdf_bytes`=None → gracefully fell back to text scrape; Gemini
    answered 981 chars from the page text. ✅ (no-PDF path safe)
  - **company:93565** (749KB broker PDF) → `📑 PDF 원문(749KB)을 Gemini 에 직접 전달` note fired → Gemini read the
    **PDF's earnings table** and returned precise figures absent from any text scrape: 코스메카코리아 · **투자의견
    Buy / 목표주가 120,000원 / 현재가 70,800원 / 상승여력 69.5% / 매출 7,930억 / 영업이익 1,070억 / EPS 6,891원 /
    PER 10.3배**. ✅ End-to-end "직접 PDF 인식" confirmed.
  - Server tracebacks: 0.

## Notes & Traps
- Inline PDF cap = 18MB (Gemini inline limit ~20MB); broker reports are ~0.5–1.5MB. Larger → falls back to text.
- PDF pages are billed as tokens on Gemini, but reports are 1–10 pages → small; free-tier flash supports document
  input. `use_search` stays as-is (grounding gating from changes_54).
- Minor: news-search intent can still trigger on a research-scope question (harmless — finds nothing, PDF drives the
  answer); not worth tightening now.
- `.app` not rebuilt (live-source); `./build.sh` is the §23 follow-up.
