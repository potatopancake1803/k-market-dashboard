---
id: 5
title: Local AI — deterministic model selection (qwen3-4b-2507) + bounded fast commentary
date: 2026-06-11 15:40 KST
agent: Claude (Opus 4.8)
area: [local-llm]
status: verified
files:
  - scripts/market_dashboard3_realtime.py
supersedes: []
verified_by: |
  _pick_llm_model unit test (real LM Studio list of 5):
    real list           -> qwen/qwen3-4b-2507
    embedding-model-first-> qwen/qwen3-4b-2507  (embedding never chosen)
    no-2507 / 9b first  -> qwen/qwen3.5-9b
    only thinking+vl    -> falls back (last resort)
    KMKT_LLM_MODEL=...   -> override honored
  End-to-end POST /api/llm_commentary (warm, model qwen3-4b-2507):
    call#1 first token 0.5s, total 1.5s, 129 chars, clean 3-sentence Korean
    call#2 first token 0.2s, total 1.2s, 135 chars
---

# Local AI — deterministic model selection + bounded fast commentary

## 🛠️ What was done
Made the local AI commentary (`POST /api/llm_commentary`) **deterministically use the
fast 4B model** (`qwen/qwen3-4b-2507`, non-thinking MLX 4bit, which the user downloaded)
instead of blindly taking `/v1/models` `data[0]`, and bounded the response length for
snappy output. This resolves the latency concern from `changes_3`'s notes.

## ⚙️ How it was done (Technical Details)
- **Root issue:** the endpoint picked `models_res["data"][0]["id"]`. LM Studio's
  `/v1/models` order is **not stable** and includes heavyweight (9B/12B) and
  **embedding** models — `data[0]` could be a 12B (slow) or `text-embedding-...`
  (would break chat entirely). With several models loaded, "which model answers" was
  effectively random.
- **Fix — new `_pick_llm_model(ids)` helper** (module scope, just above the route):
  1. `KMKT_LLM_MODEL` env → exact/substring match, else forced (LM Studio JIT-loads it).
  2. Drop any id containing `embed` (never use an embedding model for chat).
  3. Prefer `_LLM_PREFERRED = "qwen3-4b-2507"` (substring).
  4. Else first `4b` id that is **not** `thinking` / `vl` (token-split match so we don't
     false-match substrings).
  5. Else first non-thinking/non-vl id; else `pool[0]`.
  Rationale: for a 3-sentence commentary, a **non-thinking Instruct** model is ideal —
  `thinking` models emit long hidden reasoning (the suspected cause of the old ~45s
  latency) and `vl` (vision) models are heavier with no benefit for text-only quant stats.
- Endpoint now: `ids = [m["id"] ...]; model_id = _pick_llm_model(ids)`, with a new guard
  that yields a clear "no model loaded" SSE message if selection returns `None`.
- **`max_tokens: _LLM_MAX_TOKENS` (400)** added to the payload → bounded generation time.
- System prompt tightened ("핵심만 3문장 이내") to match the bound.
- Kept the `changes_3` fixes intact (prompt read outside generator; module-level
  `json`/`urllib`; `timeout=300.0`; tiered error messages).

## ✅ Verification (commands + observed output)
- **Unit test** of the picker against the real LM Studio list
  `[qwen3-4b-2507, qwen3.5-9b, gemma-4-12b-it-qat-..., gemma-4-12b-qat, text-embedding-...]`
  and adversarial orderings — results above in `verified_by`. Embedding model is never
  selected; `qwen3-4b-2507` wins whenever present; env override works.
- **End-to-end** via Flask (`MARKET_PORT=8795`), keeping the server alive with a 2s
  `/__ping` keepalive (see gotcha below): two real commentary calls returned full,
  coherent 3-sentence Korean quant commentary; **warm first token 0.2–0.5s, total
  1.2–1.5s**. Cold first request (model JIT-load) was ~6s, then warm.

## ⚠️ Notes & Pending Issues
- **Headless test gotcha (NOT a code bug):** the server's auto-shutdown watchdog
  (`_monitor_heartbeat`, `_PING_TIMEOUT = 15s`) calls `os._exit(0)` if no `/__ping`
  arrives for 15s. The real app pings every ~2s from the browser (`miPing`), but a
  `curl`/script test without keepalive will get the server killed mid-stream (looks like
  a truncated reply / empty response). When testing endpoints headless, run a background
  `/__ping` loop. First attempt this session hit exactly this and cut a reply at 27 chars.
- **For best UX, enable "keep model loaded" in LM Studio** so the first request isn't a
  cold JIT-load (~6s). Backend timeout (300s) covers cold loads regardless.
- **Model override:** set `KMKT_LLM_MODEL` (env) to force a specific model without code
  changes.
- Still **not implemented** (optional): boot-time model warmup mirroring `_prewarm`.
- Screener code unchanged this session (verified in `changes_3`; still ✅).
