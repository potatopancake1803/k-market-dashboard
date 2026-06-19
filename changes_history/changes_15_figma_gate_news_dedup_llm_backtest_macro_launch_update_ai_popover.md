---
id: 15
title: Figma-MCP gate guideline + near-dup news removal + local-LLM explain (backtester/ECOS) + launch-only auto-update + topbar AI popover (LM Studio control)
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - application_build/CLAUDE.md
  - scripts/market_dashboard3_realtime.py
  - application_build/app.py
  - memory/ui-design-standard.md
---

## What was done (6 user tasks)
1. **Figma MCP gate** — added §10.7 rule: when a task needs Figma work, confirm the Figma MCP is connected; if not, pause and ask the user to connect before resuming (no guessing from memory).
2. **Near-duplicate news removal** — replaced exact-prefix dedup with token-Jaccard + sequence-similarity + Korean josa-stripping; applied across market-wide, per-stock (LLM grounding) and overseas (Finnhub) news.
3. **Record-keeping efficiency review** — see Notes. (review-only; one safe fix to `_STATUS.md` proposed separately.)
4. **Local-LLM explanation for backtester + ECOS** — reuse `/api/llm_commentary` with a new `mode` param (`backtest`/`macro`) selecting beginner-friendly system prompts; added "🤖 AI 해석" button + SSE streaming panel on both pages.
5. **Launch-only auto-update** — removed the 12s polling daemon (`_watch_updates`); replaced with one-shot `_check_update_at_launch` (py_compile + marker guards against restart loops). Manual menu check retained.
6. **Topbar AI popover** — moved brand left (is-app pad-left 94→78px), shrank 스크리너/실시간 (`btn-sm`, 28px), added ✨ AI button + glass popover controlling LM Studio: install detect, model info (Model/Format/Quantization/Size on disk), Load/Unload toggle.

## How it was done

### 작업1 — Figma gate (application_build/CLAUDE.md §10.7 + memory)
New mandatory rule in §10; mirrored into memory `ui-design-standard.md`. Canonical design source must come from Figma MCP when reachable; pause-and-ask if disconnected.

### 작업2 — near-dup news (scripts/...realtime.py)
New `_news_norm` (strip [말머리]/<태그>/(부제), punctuation), `_news_tokens` (len≥2 + Korean josa-strip via `_JOSA`: 순매수에→순매수, 2700선→2700), `_news_similar` (token-Jaccard≥0.5 OR containment≥0.8 OR SequenceMatcher≥0.72), `_dedup_news` (order-preserving). Applied in `_market_wide_news`, per-stock news in `_build_ai_context` (Naver+KIS merged then deduped once), and `_ov_news` (Finnhub stock + KIS market fallback).

### 작업4 — local-LLM explain (backtester + ECOS)
`/api/llm_commentary` body now reads `mode`. `mode=="backtest"` → 금융 교육 전문가 system prompt (전문용어 풀이 + 3단 구성 + 면책); `mode=="macro"` → 경제 해설가 prompt (금리/스프레드/CPI/환율→증시 영향). Backtester `renderRes()` adds `#aiPanel` (button `#aiBtn` → `aiExplain()` builds prompt from `res`); macro page adds `#aiCard` (`aiExplainMacro()` builds prompt from `D.kpi`+rule-based commentary). Shared `streamLLM(body,outId,onDone)` consumes the SSE stream. CSS `.aibtn/.aiout/.ai-cur/.ai-typing` added to both pages (theme-aware, reduced-motion guarded).

### 작업5 — launch-only update (application_build/app.py)
`_LIVE_LOADED` flag set on successful live-source import. `_BUNDLED_HASH` = frozen bundle copy hash. `_watch_updates` (while-True 12s poll) deleted → `_check_update_at_launch`: returns if live loaded (already newest) or no live source; only when running the bundle fallback AND live source differs AND py_compile passes AND not already attempted (temp marker `kmkt_update_attempt.txt`) does it apply the overlay+restart. `_on_loaded` now fires `threading.Timer(0.5, _check_update_at_launch)` once (no daemon). `import tempfile` added.

### 작업6 — topbar AI popover + LM Studio control
Backend: `_lms_bin()` (~/.lmstudio/bin/lms or PATH), `_llm_installed()`, `_lms_run()` (subprocess), `_llm_status()` (/api/v0/models for state/compatibility_type/quantization + `lms ls --json` for sizeBytes; `lms ps` fallback for loaded), endpoints `GET /api/llm/status`, `POST /api/llm/load` (`lms load <key> -y`), `POST /api/llm/unload` (`lms unload --all`). Frontend (landing): brand pad-left 78px, `.btn-sm` on screener/realtime, `.btn-glass.g-ai` ✨ AI button + `.ai-pop` glass popover (light+dark, macos26 tokens), IIFE rendering status → not-installed message / model-missing message / info rows + Load↔Unload toggle. `.ai-wrap`/`.ai-pop` added to topbar drag-exclusion selector.

## Verification
Server: `MARKET_PORT=8781 uv run scripts/market_dashboard3_realtime.py` via Claude_Preview (port 8781). ⚠ headless: do NOT hit `/__ping` — it arms the heartbeat watchdog (`_PING_TIMEOUT=15s`) and the server self-terminates with no browser pinging; probe `/api/llm/status` instead.
- 작업2: `/api/market_news` → 15 deduped rows; offline heuristic test collapsed 3 Samsung + 2 코스피 near-dupes (6→4) with distinct stories preserved. ✓
- 작업4: `POST /api/llm_commentary {mode:backtest}` streamed a plain-language Korean explanation ("이 전략은 삼성전자의 가격이 5일과 20일 이동…"). ✓ (model loaded for the test, then unloaded)
- 작업5: `py_compile app.py` OK; no stale `_watch_updates` refs. Native overlay/restart not observable headlessly → see app rebuild.
- 작업6: preview eval — AI btn "✨ AI", screener/realtime height 28px, is-app pad-left 78px. Click → popover shows Load toggle + Model qwen/qwen3-4b-2507 / Format MLX / Quantization 4bit / Size on disk 2.28 GB. Toggle load → `loaded:true` + "● 로드됨"/"Unload"; unload → `loaded:false`. Light + dark screenshots both correct. ✓
- `py_compile` clean for both Python files.

## Notes & Traps
- **App rebuild** required for 작업5 (app.py is the frozen launcher): ran `application_build/build.sh` this session (installs /Applications + DMG). Verify the launch-only update manually by editing `scripts/...realtime.py` and relaunching the app.
- **LM Studio dependency**: 작업6 needs `~/.lmstudio/bin/lms`. Size on disk comes from `lms ls --json` (sizeBytes), state/format/quant from `/api/v0/models` (note: `/v1/models` lists ALL models here, not just loaded — use `/api/v0` `state`).
- **Heartbeat watchdog trap** (new): headless verification must avoid `/__ping` and `/__bye`.
- **작업3 — record-keeping review (token efficiency):** the logging *format* (tier system in §3, `_STATUS.md` as cheap index, read-order table in §1) is well-designed and NOT wasteful. The real waste is structural: (a) TWO `changes_history/` dirs — repo-root (Claude lineage 7–15, this file) and `application_build/` (sequence 0–20 with `_STATUS.md`) — with COLLIDING numbers but different content, so an agent following §1 read-order silently misses the other dir's latest; (b) `_STATUS.md` (last updated 2026-06-12, tracks only `application_build/`) does not know about root changes_13/14/15; (c) ~7 overlapping governance docs (AGENTS.md, ANTIGRAVITY.md, 2 template files, 2 CLAUDE.md, HANDOFF.md). **Recommendation:** consolidate to ONE `changes_history/` (the §4 canonical `application_build/changes_history/`), keep `_STATUS.md` as the single index, archive redundant template docs. File moves were NOT done (needs user approval per §8).
