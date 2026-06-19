---
id: 51
title: Gemini model catalog + picker, Google-Search grounding, local→Gemini auto-switch on search, per-message model avatars, local-load hint, provider memory, Mac resize handles
date: 2026-06-16 23:55 KST
agent: Claude (Opus 4.8)
status: partial
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- **작업1 — Gemini model suitability + default.** Read the live pricing page and curated a 4-model catalog
  (`_GEMINI_MODELS`) for this app's "deterministic gather → synthesize (+ optional web search)" shape.
  Default stays/normalised to **`gemini-3.5-flash`** (`_GEMINI_DEFAULT`). Suitability rationale below.
- **작업2 — Gemini works + efficient prompt + model picker + max cloud perf.**
  - New `gemini_model` request field on `/api/llm_ask`, validated against `_GEMINI_MODELS`.
  - Chat footer now has a **Gemini model `<select>`** (`#kmktAiGModel`) shown only when Gemini is active.
  - `_gemini_stream(model=, use_search=, max_tokens=4096)`: enables **Google Search grounding**
    (`tools:[{google_search:{}}]`) and bumps output tokens to 4096. The strict "only injected data" system
    prompt is augmented when searching so it no longer contradicts the search tool (cite only verifiable
    fresh sources; no pretrained guessing).
- **작업3 — Mac-style arrow resize.** Replaced the pointer/edge-detection resize with **8 explicit handle
  divs** (`.kmkt-ai-rs-{n,s,e,w,ne,nw,se,sw}`) using the same `ns/ew/nesw/nwse-resize` cursors as the
  individual-stock report modal (`.mi-rs` in `market_intel/report/dashboard.py`). Header still drags to move.
- **작업4 — local-load hint + provider memory.** On open / provider change, `updatePlaceholder()` pings
  `/api/llm/loaded`; if local is selected but no model is loaded, the input placeholder reads
  **"로컬 LLM 모델을 로드해 주세요."**. Provider (`kmkt-ai-prov`) and Gemini model (`kmkt-ai-gmodel`) are
  persisted to localStorage and restored on reopen.
- **작업5 — auto-switch to a search-capable model.** Server computes `needs_search` (recency/news keywords).
  If provider is **local**, the deterministic agent gathered **nothing** (`tool_used==False`), and a
  `GEMINI_KEY` exists → it transparently switches to Gemini (with Google Search), emitting a reasoning note.
  (Conservative: when local *can* gather, it stays local — verified both branches live.)
- **작업6 — per-message model avatar (KakaoTalk style).** Each assistant message shows a round avatar +
  short model name: **✦ + "Gemini 3.5 Flash"** for cloud, **✨ + "로컬"/model-id** for local. Driven by a new
  SSE **`meta`** event (`{provider,model,name}`) the server emits before the answer, so an auto-switch is
  reflected accurately.

## Gemini model suitability (작업1 deliverable)
- **gemini-3.5-flash — DEFAULT.** $1.50/$9.00, "most intelligent built for speed", Google Search. Best
  intelligence/latency balance for synthesizing gathered evidence + light web boost.
- **gemini-3.1-pro-preview.** $2.00/$12.00, top reasoning + grounding. Deep multi-factor analysis (quality > cost).
- **gemini-2.5-flash.** $0.30/$2.50, fast, grounding, 1M ctx. Cheaper everyday option.
- **gemini-3.1-flash-lite.** $0.25/$1.50, cheapest/high-throughput. Fastest/cheapest.
- Excluded: 2.0-flash(* deprecated 2026-06-01), image/tts/live/audio/embeddings/computer-use/veo/lyria
  (wrong modality), 2.5-flash-lite (superseded by 3.1-flash-lite).

## How it was done
- `_llm_stream` gained `model_id=` so `llm_ask` can pick the local model once (for the avatar meta) and pass
  it in, avoiding a duplicate LM Studio `/api/v0/models` call.
- `_short_model_name()` prettifies the local id for the avatar.
- SSE protocol extension: a leading `data: {"meta":{...}}` frame; the widget's reader sets the avatar via
  `setWho()` and otherwise behaves as before for `text`/`reasoning` frames.

## Verification
- `python3 -m py_compile` → OK.
- Headless (MARKET_PORT 8795–8797, /__ping keepalive per trap #8):
  - Widget markup present on `/overseas`: `kmktAiGModel`, `kmkt-ai-rs-se`, `kmkt-ai-who/av`, `setWho`,
    `updatePlaceholder`, `startResize`, `kmkt-ai-prov`; all big inline `<script>`s pass `node --check` (0 fail).
  - `GET /api/llm/loaded` → `{up:true, loaded:false, id:""}` (LM Studio up, no model) → drives 작업4 hint.
  - `POST /api/llm_ask {provider:gemini,gemini_model:gemini-3.5-flash}` → emits
    `meta{provider:gemini,model:gemini-3.5-flash,name:"Gemini 3.5 Flash"}` then streams; ended in **429**
    (Gemini credits depleted — known, graceful fallback). A 429 (not 400) confirms model id + google_search
    tool are accepted; full answer streaming is **unverified pending credits**.
  - 작업5 both branches: local + search kw + news FOUND → stays `provider:local`; local + search kw +
    empty gather (bogus symbol) → switches to `provider:gemini`. ✅
- **Visual (avatars, resize-handle cursor feel, model dropdown, placeholder hint, persistence) = unverified**
  — needs GUI. Verify via `uv run application_build/app.py`: open AI 질문하기, switch 로컬/Gemini (dropdown
  appears, choice persists across reopen), with no local model loaded confirm the placeholder hint, drag
  edges/corners (Mac arrows), ask a Gemini question and confirm ✦ avatar + model name.

## Notes & Traps
- Gemini still **429s** in this environment (credits depleted, per `_STATUS`); end-to-end answer text is
  unverified until the key has quota. Wiring (model select, google_search, meta) is confirmed.
- `KMKT_GEMINI_MODEL` env still force-overrides when no per-request `gemini_model` is sent.
- Google Search grounding bills after the free 5,000 prompts/month (shared across Gemini 3 models).
  It is enabled on every Gemini answer (use_search=True) for freshness — revisit if cost matters.
- `.app` not rebuilt (live-source via `app.py::_live_source()` reflects on restart); `./build.sh` is the
  protocol §23 follow-up before shipping a frozen bundle.
