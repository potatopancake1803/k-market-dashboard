---
id: 32
title: 작업2 — richer company profile (DART domestic + Yahoo overseas) injected into stock reports
date: 2026-06-15 KST
agent: Claude (Opus 4.8)
status: verified
files:
  - scripts/market_dashboard3_realtime.py
---

## What was done
- Added a "🏢 기업 개요" card to both domestic and overseas stock reports with company facts/description
  (the SPCX/Yahoo example was the target richness).

## How it was done
- **Collectors** (normalized to `{desc, facts:[(label,value)], officers, src}`):
  - `_dart_company_profile(code)` — DART `company.json` (corp_code via `company.get_corps()`): 대표이사,
    설립일, 본사 주소, 홈페이지(링크), 전화, 표준산업분류. DART key via `_dart_key()` (env → API.env).
  - `_yahoo_profile(symbol)` — Yahoo `quoteSummary?modules=assetProfile` with cookie+crumb session
    (`_yahoo_session()`, crumb cached ~50min): sector, industry, employees, longBusinessSummary,
    website, HQ, top officers. **Fallback** when quoteSummary is unauthorized/rate-limited (401/429):
    the no-auth `v1/finance/search` endpoint (sector/industry/exchange) so the card is never blank.
  - `_profile_card_html(prof)` — self-contained card (inline styles, `min-width:0`/`break-word`, only
    depends on `.card`/`.card-title` which both pages have).
  - 6h cache (`_PROFILE_CACHE`).
- **Domestic wiring:** `_inject_profile(html, code)` inserts the card right after the price-hero card
  (anchor: first `</section>` after `id="pane0">`); called from `/dashboard` for non-ETF.
- **Overseas wiring:** `/api/ov/detail` adds `profile_html`; `_OVERSEAS_HTML` has a `<div id="ovProfile">`
  (right column, under 핵심 지표) filled in `render(d)`.

## Verification
- `python3 -m py_compile` clean.
- Live server: `GET /dashboard?q=005930` → contains `id="kmkt-profile"` with 대표이사·설립일·본사·홈페이지
  (DART, fully verified).
- Live server: `GET /api/ov/detail?excd=NAS&symb=AAPL` → `profile_html` len 811, card present with 섹터·산업
  (via search fallback — Yahoo quoteSummary was IP-throttled 429 during this session from repeated probing).
- Yahoo `assetProfile` shape confirmed earlier this session before throttling (sector/industry/employees/
  longBusinessSummary/companyOfficers) — the parse matches; the rich path populates when not throttled
  (real usage is infrequent + 6h-cached, so throttling is unlikely).

## Notes & Traps
- **Yahoo quoteSummary now requires cookie+crumb** (bare v10 returns 401); rapid repeated hits get 429 IP
  cooldown. The crumb-session + 6h cache + search-fallback make this resilient.
- Domestic DART gives structured facts but no prose description; overseas Yahoo gives a real description.
- Next: 작업3 (overseas AI commentary) + 작업4 (app-wide Ask-AI). This profile data feeds both.
- Web-level (live via `_live_source()`); `.app` rebuild deferred (user).
