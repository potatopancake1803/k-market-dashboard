---
id: 29
title: Fix LLM "no response" (reasoning token exhaustion) + double model load + universal loading animations
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: verified
supersedes: [28]
files:
  - scripts/market_dashboard3_realtime.py
  - application_build/CLAUDE.md
---

## What was done
- **★ PRIMARY cause of macro/backtest "응답 없음": broken SSE line-split in raw-string pages.**
  `_MACRO_HTML` and `_BACKTEST_HTML` are `r"""…"""` (raw). Their `streamLLM` used
  `buf.split('\\n')` / `replace(/\\n/g,…)` / `lines.join('\\n')`. In a **raw** string `\\n`
  stays two backslashes → the browser JS string `'\\n'` is backslash+n, **not** LF. SSE frames
  are separated by real LF, so `split` returned the whole buffer as 1 element → **no `data:` line
  was ever parsed → nothing rendered**, for ANY model. (The stock modal `_AI_SCRIPT` is a
  *non-raw* `"""` string, so its identical-looking `'\\n'` collapsed to `'\n'`=LF and worked —
  which is why only 경제지표·백테스팅 were dead.) Fixed to single-backslash `'\n'`.
- **LLM commentary "응답 없음" (secondary, all surfaces) fixed (작업1/4).** Reasoning models
  (qwen3.5-9b) put the whole response into `delta.reasoning_content` and hit
  `finish_reason=length`, emitting **0 answer `content`**. changes_28's "깊이 있는 추론(Thinking)"
  suffix made this worse. Replaced with model-class-aware handling.
- **Double model load fixed (작업1).** The picker always chose `qwen3-4b-2507` from
  `/v1/models` (which lists ALL downloaded models), so POSTing it JIT-loaded a 2nd model
  beside whatever the user had loaded. Now picks the **already-loaded** model first.
- **Per-model prompt/param tuning (작업4).** New `_llm_model_profile()` sets max_tokens,
  temperature, and a system suffix per model family (reasoning / gemma / instruct).
- **Universal smooth loading animation (작업3).** All static "…불러오는 중 / 계산 중 /
  스캔 중" text loaders replaced with a shared spinner component across every page.
- **Guidelines updated.** `application_build/CLAUDE.md` §10.8 (loaders) + new §11 (Local LLM).

## How it was done
### Backend (`scripts/market_dashboard3_realtime.py`)
- `_is_reasoning_model(id)` — regex on `qwen3.5|qwq|thinking|reasoning|deepseek-r1|magistral|gpt-oss`,
  with `*2507*`/`instruct` excluded (those are non-reasoning).
- `_llm_model_profile(id)` → `{kind, max_tokens, temperature, sys_suffix}`:
  reasoning = 2000 tok / temp 0.6 / "추론은 짧게, 끝나면 반드시 본문 답변"; gemma = 1000 / 0.3 /
  "간결"; instruct = 1200 / 0.3 / "".
- `_llm_chat_models_with_state()` reads `/api/v0/models` (has `state:"loaded"`); falls back to
  `/v1/models` (no state) on older LM Studio.
- `_pick_llm_model_ex(models)` — order: env `KMKT_LLM_MODEL` → loaded non-reasoning → any loaded →
  preferred `qwen3-4b-2507` (JIT) → any non-reasoning → first. Legacy `_pick_llm_model(ids)` kept.
- `/api/llm_commentary`: removed the "think deeply" suffix; applies the profile; the stream loop now
  tags chunks — `{"text":…}` for `content`, `{"text":…,"kind":"reasoning"}` for `reasoning_content`;
  tracks whether any `content` arrived and, for a reasoning model that produced none, yields a final
  "💡 use an Instruct model" note so the answer pane is never blank.
- Frontends: `startAI` modal (stock) + both `streamLLM` (macro, backtest) render `kind==="reasoning"`
  into a dim, collapsible "💭 추론" block and answer text prominently.

### Loading animations
- Added `_LOADER_CSS` (spinner ring + pulsing label, `.kmkt-load` / `.kmkt-load.sm`,
  `prefers-reduced-motion` guard, `--sys-blue`/`#007AFF` fallback for theme-less iframes) and
  `_loader_html(text, sm)` / `_inject_loader(html, swaps)` / `_state_loader(...)` helpers.
- A batch block near `def main()` injects the CSS + swaps the text loaders for the module-level page
  constants (sector, market, index, macro, overseas, world_detail, world, realtime, backtest).
  Screener (function-local HTML) and the backtest "계산 중" JS string were edited in place.

## Verification
- Direct LM Studio probes (`/v1/chat/completions`, port 1234):
  - `qwen/qwen3-4b-2507` → 517 answer chars, first 4.2 s (works).
  - `gemma-4-12b-it-qat` → 433 answer chars, finish=stop (works).
  - `qwen3.5-9b` → **0 content / 3778–10360 reasoning / finish=length** at 1200–3600 tokens (the bug).
- Picker validated against live `/api/v0/models`: only-9b-loaded→9b; 9b+gemma→gemma; none→4b-2507;
  reasoning detection correct.
- **Raw-string newline bug:** `node -e` proved `"a\n\nb".split("\\n")` → 1 part (broken) vs
  `split("\n")` → 5 parts. After fix, `curl /macro_page` and `/backtest_page` serve
  `buf.split('\n')` + `lines.join('\n')` + literal `💭` (verified).
- **Live end-to-end SSE** (`MARKET_PORT=8795 uv run scripts/market_dashboard3_realtime.py`, with a
  2 s `/__ping` keepalive in the same invocation — trap #18), `POST /api/llm_commentary` mode=macro,
  9b loaded:
  `first=2.2s answer_chars=120 reason_chars=7108 endnote=True total=65.0s` →
  reasoning streams immediately (no blank), Instruct end-note shown, no 2nd model JIT-loaded.
- **Loaders:** `curl` each page → `kmkt-loader-css` present and `class="kmkt-load"` markup count:
  macro 1, sector 1, market 4, world_page 1, screener_page 1, overseas 1, backtest_page 1,
  realtime_page 2. ✅
- `python3 -m py_compile` clean.

## Notes & Traps
- New traps added to `_STATUS.md`: #19 (reasoning models emit no content / handling),
  #20 (`/v1/models` lists all downloaded, use `/api/v0/models` for state).
- This is a **web-level** change — `app.py` loads the backend live (`_live_source()`); restart the
  app to apply. **A `.app` rebuild is still required per CLAUDE.md §23/§9** before shipping
  (`cd application_build && ./build.sh`) — not done in this session (no LM Studio in headless CI;
  visual confirm of the dim 추론 block + spinners pending in the real app).
- For best UX the user should keep an **Instruct** model (qwen3-4b-2507 / gemma) loaded in the AI
  popover; a reasoning-only model will show thinking + the steering note rather than a clean answer.
