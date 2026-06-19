"""Developer Mode — capture (location + source + memo) for the coding agent in one shot.

Purpose: when the user spots something to fix in the running app, Dev Mode lets them click the
element and capture EXACTLY where it lives in the source (file:line of the template + the JS/Python
that drives it) plus a memo. Items can be batched into a **session** and saved as one LLM-readable
markdown TODO file in `dev_notes/` — the agent reads it and goes straight to the spots (no token-
wasting hunt, no "fix one / break another" because the whole session is one planned change).

Gated by env `KMKT_DEV=1` (overlay injected + endpoints active only then). Off ⇒ zero effect, so the
render golden baseline is unchanged. Toggle the overlay in-app with ⌘⇧D (Ctrl+Shift+D).

This module holds the overlay template + the grep/locate + note/session writers. The main backend
imports these and wires the routes + an `after_request` injector + the in-process session store.
"""
from __future__ import annotations

import datetime as _dt
import json as _json
import re as _re
from pathlib import Path

# Source files searched to map a DOM element → its source location.
_DEV_SOURCE_REL = [
    "scripts/ui_templates.py",
    "scripts/market_dashboard3_realtime.py",
    "scripts/dev_overlay.py",
    "scripts/archive/company_report_ver2.py",
    "scripts/archive/etf_dashboard_ver2.py",
    "market_intel/report/dashboard.py",
]

# Route (pathname) → best-guess page template constant (a hint for the agent).
_DEV_ROUTE_TEMPLATE = {
    "/": "_LANDING_HTML",
    "/overseas": "_OVERSEAS_HTML",
    "/realtime_page": "_REALTIME_HTML",
    "/backtest_page": "_BACKTEST_HTML",
    "/world_page": "_WORLD_HTML",
    "/world_detail": "_WORLD_DETAIL_HTML",
    "/index_page": "_INDEX_HTML",
    "/macro_page": "_MACRO_HTML",
    "/market": "_MARKET_HTML",
    "/sector": "_SECTOR_HTML",
    "/research_page": "_RESEARCH_HTML",
    "/pdf_view": "_PDF_VIEW_HTML",
    "/dashboard": "company_report_ver2 / etf_dashboard_ver2 (+ _inject_fx/_inject_m4_tab)",
}

# Class names too generic to be useful grep anchors.
_DEV_STOP_CLASSES = {
    "card", "pane", "row", "col", "active", "on", "off", "btn", "box", "wrap", "inner",
    "show", "hide", "open", "sel", "tab", "kmkt-md", "mdh", "mdul", "dn", "up",
}


def dev_template_guess(route: str) -> str:
    path = (route or "").split("?")[0]
    return _DEV_ROUTE_TEMPLATE.get(path, "(unknown — grep the anchors below)")


def _dev_terms(info: dict) -> list[tuple[str, str]]:
    """Ordered (kind, term) search terms, most-unique first. Falls back to ANCESTOR id/class
    (방안1-2) so elements with no own id/class (bare span/div) are still locatable via their
    nearest identifiable container."""
    terms: list[tuple[str, str]] = []
    el_id = (info.get("id") or "").strip()
    if el_id:
        terms.append(("id", el_id))
    for c in (info.get("classes") or "").split():
        c = c.strip()
        if len(c) >= 4 and c not in _DEV_STOP_CLASSES:
            terms.append(("class", c))
    txt = (info.get("text") or "").strip().replace("\n", " ")
    if len(txt) >= 4 and not txt.replace(".", "").replace(",", "").replace("%", "").isdigit():
        terms.append(("text", txt[:24]))
    # ancestor fallbacks (lower priority)
    a_id = (info.get("ancestor_id") or "").strip()
    if a_id:
        terms.append(("ancestor", a_id))
    a_cls = (info.get("ancestor_classes") or "").strip()
    if a_cls and a_cls not in _DEV_STOP_CLASSES:
        terms.append(("ancestor", a_cls))
    return terms[:10]


def dev_locate(root: Path, info: dict) -> list[dict]:
    """Grep the source files for the element's id / classes / text / ancestor → file:line list."""
    terms = _dev_terms(info)
    if not terms:
        return []
    out: list[dict] = []
    seen: set[tuple[str, int]] = set()
    per_term: dict[str, int] = {}
    for rel in _DEV_SOURCE_REL:
        f = root / rel
        if not f.exists():
            continue
        try:
            lines = f.read_text(encoding="utf-8").split("\n")
        except Exception:  # noqa: BLE001
            continue
        for kind, term in terms:
            if per_term.get(term, 0) >= 3:
                continue
            for i, ln in enumerate(lines):
                if term in ln:
                    key = (rel, i)
                    if key in seen:
                        continue
                    seen.add(key)
                    per_term[term] = per_term.get(term, 0) + 1
                    out.append({"file": rel, "line": i + 1, "kind": kind, "term": term,
                                "snippet": ln.strip()[:160]})
                    if per_term[term] >= 3:
                        break
        if len(out) >= 18:
            break
    pri = {"id": 0, "class": 1, "text": 2, "ancestor": 3}
    out.sort(key=lambda o: (pri.get(o["kind"], 4), o["file"], o["line"]))
    return out[:18]


def _slug(s: str, n: int = 28) -> str:
    s = _re.sub(r"[^0-9A-Za-z가-힣]+", "-", (s or "").strip()).strip("-")
    return (s[:n] or "note").lower()


def _el_lines(el: dict) -> list[str]:
    out = [f"- tag: `{el.get('tag','')}`"]
    if el.get("id"):
        out.append(f"- id: `{el.get('id')}`")
    if el.get("classes"):
        out.append(f"- classes: `{el.get('classes')}`")
    if el.get("ancestor_id") or el.get("ancestor_classes"):
        out.append(f"- ancestor: `{el.get('ancestor_id','')}` `{el.get('ancestor_classes','')}`")
    if el.get("role"):
        out.append(f"- role/aria: `{el.get('role')}`")
    if el.get("text"):
        out.append(f"- text: `{str(el.get('text')).replace('|', ' ')[:200]}`")
    out.append(f"- selector: `{el.get('selector','')}`")
    if el.get("chart"):
        out.append(
            f"- **📊 차트 요소({el.get('chart')})** — 마크업이 아니라 *차트 설정 코드*를 고쳐라: "
            "프론트 Plotly `Plotly.react(...)`의 `layout`/`xaxis`, canvas `lineChart(...)`, "
            "또는 백엔드 `go.Figure`/`go.Treemap`(`scripts/market_dashboard3_realtime.py` 의 `_*_fig`). "
            "grep: `go.Treemap`/`go.Figure`/`Plotly.react`/`lineChart`."
        )
    st = el.get("styles") or {}
    if st:
        out.append("- 현재 스타일: " + ", ".join(f"`{k}:{v}`" for k, v in st.items()))
    return out


def _cand_table(cands: list) -> list[str]:
    if not cands:
        return ["_(자동 후보 없음 — 위 앵커로 grep)_"]
    rows = ["| file | line | 매칭 | snippet |", "|---|---:|---|---|"]
    for c in cands:
        snip = str(c.get("snippet", "")).replace("|", "\\|")
        rows.append(f"| `{c.get('file','')}` | {c.get('line','')} | {c.get('kind','')}:`{c.get('term','')}` | `{snip}` |")
    return rows


def dev_write_note(root: Path, payload: dict) -> str:
    """Write a single LLM-readable markdown note to dev_notes/. Returns the relative path."""
    notes = root / "dev_notes"
    notes.mkdir(exist_ok=True)
    el = payload.get("element", {}) or {}
    route = payload.get("route", "") or ""
    memo = (payload.get("memo", "") or "").strip()
    ts = _dt.datetime.now()
    fname = f"{ts:%Y%m%d_%H%M%S}_{_slug(memo or el.get('id') or el.get('tag') or 'note')}.md"
    o = [f"# Dev note — {ts:%Y-%m-%d %H:%M:%S}", "",
         "> 앱 Dev Mode 캡처. 에이전트는 이 파일로 위치·소스·요청을 파악해 바로 작업하라.", "",
         "## ✏️ 요청 (메모)", memo or "_(메모 없음)_", "",
         "## 📍 위치", f"- **Route**: `{route}`",
         f"- **Page template (추정)**: `{dev_template_guess(route)}`", "",
         "## 🔖 요소", *_el_lines(el), "",
         "## 🧩 소스 후보 (grep — 파일:라인)", *_cand_table(payload.get("candidates") or []), "",
         "## 🛠 힌트", "1. 위 소스 후보 file:line 을 먼저 부분 Read. 없으면 앵커로 grep.",
         "2. 마크업=`scripts/ui_templates.py`, 동작/라우트=`scripts/market_dashboard3_realtime.py`.",
         "3. 변경 후 `uv run scripts/smoke_check.py`(+수집기면 `api_smoke.py`) 통과.", "",
         "```json", _json.dumps(payload, ensure_ascii=False, indent=2), "```"]
    (notes / fname).write_text("\n".join(o), encoding="utf-8")
    return f"dev_notes/{fname}"


def dev_write_session(root: Path, session: dict, fname: str | None = None) -> str:
    """Write a batched SESSION as one LLM-ready TODO markdown. Returns the relative path.

    If ``fname`` is given (continuing an existing session — 요청1), overwrite that file in
    place instead of creating a new timestamped one, so re-saving an in-progress session keeps
    the same file (the agent's queue stays one entry, not a duplicate)."""
    notes = root / "dev_notes"
    notes.mkdir(exist_ok=True)
    title = (session.get("title") or "세션").strip()
    items = session.get("items") or []
    ts = _dt.datetime.now()
    if fname:
        fname = Path(fname).name
        if not fname.endswith(".md"):
            fname += ".md"
    else:
        fname = f"session_{ts:%Y%m%d_%H%M}_{_slug(title)}.md"

    routes = sorted({(it.get("route") or "") for it in items})
    o = [f"# 🛠️ Debugging Session: {title}", "",
         f"- **생성**: {ts:%Y-%m-%d %H:%M} (KST)",
         f"- **항목 수**: {len(items)}",
         f"- **대상 화면(Route)**: {', '.join('`'+r+'`' for r in routes) if routes else '(없음)'}",
         "",
         "> 🤖 **에이전트 처리 프로토콜** (이 순서대로):",
         "> 1. 아래 TODO 를 **한 계획으로 일괄** 처리(항목별 산발 수정 X). 각 수정 후 `uv run scripts/smoke_check.py` 통과.",
         ">    마크업=`scripts/ui_templates.py`, 동작/라우트=`scripts/market_dashboard3_realtime.py`.",
         "> 2. 끝낸 항목은 체크박스 `[ ]`→`[x]`. 못 끝낸 항목은 `[ ]` 유지 + 한 줄 사유.",
         "> 3. **맨 아래 `## ✅ 처리 결과` 를 채워라** — 바꾼 file:line, `changes_X_*.md` 로그 id, smoke 결과.",
         "> 4. 전부 끝나면 이 파일을 `dev_notes/done/` 로 **이동**(완료 큐 분리 → 다음 세션이 미처리만 봄).",
         ">    일부만 끝냈으면 파일은 `dev_notes/` 에 그대로 두고 `[x]`/결과만 갱신.",
         "", "## 📋 수정 요청 (TODO)", ""]
    for i, it in enumerate(items, 1):
        el = it.get("element", {}) or {}
        memo = (it.get("memo", "") or "").strip() or "(메모 없음)"
        cands = it.get("candidates") or []
        top = cands[0] if cands else None
        loc = f"`{top['file']}:{top['line']}`" if top else "(앵커로 grep)"
        anchors = " · ".join(f"`{a}`" for a in (it.get("anchors") or [])[:4])
        o.append(f"- [ ] **Task {i}** — {memo.splitlines()[0][:60]}")
        o.append(f"  - route: `{it.get('route','')}` · template: `{dev_template_guess(it.get('route',''))}`")
        o.append(f"  - 요소: `{el.get('selector','')}` ({el.get('tag','')}{('#'+el.get('id')) if el.get('id') else ''})")
        o.append(f"  - 소스: {loc}" + (f" · 앵커: {anchors}" if anchors else ""))
        o.append(f"  - 요청: {memo}")
        o.append("")
    o += ["## 🔎 소스 후보 (전체)", ""]
    o.append("| # | file | line | 매칭 | snippet |")
    o.append("|---:|---|---:|---|---|")
    for i, it in enumerate(items, 1):
        for c in (it.get("candidates") or [])[:3]:
            snip = str(c.get("snippet", "")).replace("|", "\\|")
            o.append(f"| {i} | `{c.get('file','')}` | {c.get('line','')} | {c.get('kind','')}:`{c.get('term','')}` | `{snip}` |")
    o += ["", "## ✅ 처리 결과",
          "<!-- 처리 전엔 비어 있음. 에이전트가 완료 후 아래를 채우고, 다 끝났으면 이 파일을 dev_notes/done/ 로 옮긴다. -->",
          "- 상태: ⬜ 미처리",
          "- 바꾼 곳: (예: `scripts/ui_templates.py:1518` …)",
          "- 변경 로그: (예: `changes_83_*.md`)",
          "- 검증: (예: `smoke_check` PASS / `api_smoke` PASS)",
          ""]
    o += ["```json", _json.dumps({"title": title, "items": items}, ensure_ascii=False, indent=2), "```"]
    (notes / fname).write_text("\n".join(o), encoding="utf-8")
    return f"dev_notes/{fname}"


def _extract_session_json(txt: str) -> dict | None:
    """Pull the trailing ```json {title, items} ``` block back out of a saved session file."""
    blocks = list(_re.finditer(r"```json\s*(.*?)```", txt, _re.S))
    if not blocks:
        return None
    try:
        return _json.loads(blocks[-1].group(1).strip())
    except Exception:  # noqa: BLE001
        return None


def dev_list_sessions(root: Path) -> list[dict]:
    """In-progress sessions (dev_notes/session_*.md, excluding done/) — for 이어쓰기 (요청1)."""
    notes = root / "dev_notes"
    out: list[dict] = []
    if not notes.exists():
        return out
    for f in notes.glob("session_*.md"):     # glob is non-recursive → done/ already excluded
        try:
            data = _extract_session_json(f.read_text(encoding="utf-8"))
            out.append({"file": f.name,
                        "title": (data.get("title") if data else None) or f.stem,
                        "count": len(data.get("items", [])) if data else 0,
                        "mtime": f.stat().st_mtime})
        except Exception:  # noqa: BLE001
            continue
    out.sort(key=lambda d: d["mtime"], reverse=True)
    return out


def dev_load_session(root: Path, fname: str) -> dict | None:
    """Re-load a saved session file into memory so more items can be appended (요청1)."""
    f = root / "dev_notes" / Path(fname).name
    if not f.exists():
        return None
    return _extract_session_json(f.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Overlay (HTML + CSS + JS) — injected before </body> on every HTML page when KMKT_DEV=1.
# No single-backslash regex (Python-string pitfall); uses split(' ') + template literals.
# Phase-1 session UI = popover "➕ 세션 추가" + a badge counter (📌 N) that opens a compact
# session panel (title + item list + 새 세션 / 세션 저장). No full sidebar. Talks to
# /api/dev/{locate,note,session/*}.
# ---------------------------------------------------------------------------
_DEV_OVERLAY_HTML = """
<div id="kmktDev" class="kmkt-dev" data-on="0" data-pick="1" aria-hidden="true">
  <div class="kdv-frame"></div>
  <div class="kdv-badge">
    <span class="kdv-dot"></span><b>DEV</b>
    <button type="button" id="kdvPick" class="kdv-btn on" title="검사 모드(요소 선택). 끄면 앱을 평소처럼 조작">🖱 검사</button>
    <button type="button" id="kdvCount" class="kdv-chip" title="세션 목록 (클릭하여 저장/관리)">📌 0</button>
    <span class="kdv-hint">클릭=캡처 · ⌘+클릭=다중추가 · ⌘⇧C=복사 · ⌘⇧D=종료</span>
    <button type="button" id="kdvOff" class="kdv-btn" title="개발자 모드 끄기">✕</button>
  </div>
  <div class="kdv-hl" id="kdvHl"></div>

  <!-- 세션 패널 (배지 카운터에서 드롭다운) -->
  <div class="kdv-sess" id="kdvSess">
    <div class="kdv-sess-h">
      <span class="kdv-sess-ic">🗂</span>
      <input id="kdvSessTitle" class="kdv-sess-title" value="새 세션" spellcheck="false" placeholder="세션 이름">
    </div>
    <div class="kdv-sess-cont">
      <select id="kdvSessPick" class="kdv-sess-pick" title="저장됐던 미완료 세션을 이어서 편집"><option value="">⤴︎ 미완료 세션 이어가기…</option></select>
      <button type="button" id="kdvLoadSess" class="kdv-fbtn" title="선택한 세션 불러오기">📂</button>
    </div>
    <div class="kdv-sess-list" id="kdvList"><div class="kdv-empty">요소를 클릭 → 메모 → <b>➕ 세션 추가</b><br>모은 뒤 <b>💾 세션 저장</b></div></div>
    <div class="kdv-sess-foot">
      <button type="button" id="kdvNewSess" class="kdv-fbtn">➕ 새 세션</button>
      <button type="button" id="kdvSaveSess" class="kdv-fbtn prim">💾 세션 저장</button>
    </div>
    <div class="kdv-sess-msg" id="kdvSideMsg"></div>
  </div>

  <!-- 요소 인스펙터 팝오버 -->
  <div class="kdv-pop" id="kdvPop" role="dialog" aria-label="요소 정보">
    <div class="kdv-pop-h"><b>🛠 요소 정보</b><button type="button" id="kdvPopX" class="kdv-btn">✕</button></div>
    <div class="kdv-info" id="kdvInfo"></div>
    <div class="kdv-src" id="kdvSrc"><div class="kdv-src-load">소스 위치 찾는 중…</div></div>
    <textarea id="kdvMemo" placeholder="이 부분 메모 / 수정 요청 — 에이전트에게 그대로 전달됩니다…"></textarea>
    <div class="kdv-act">
      <span class="kdv-saved" id="kdvSaved"></span>
      <button type="button" id="kdvCopy" class="kdv-add" title="요소+소스 정보 클립보드 복사 (⌘⇧C)">📋 복사</button>
      <button type="button" id="kdvAddSess" class="kdv-add">➕ 세션 추가</button>
      <button type="button" id="kdvSave" class="kdv-save">💾 즉시 저장</button>
    </div>
  </div>
</div>
<style>
.kmkt-dev{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Apple SD Gothic Neo",sans-serif;}
.kmkt-dev[data-on="0"]{display:none;}
.kmkt-dev *{box-sizing:border-box;}
.kdv-frame{position:fixed;inset:0;z-index:2147482000;pointer-events:none;
  border:2.5px solid rgba(10,200,255,.9);box-shadow:inset 0 0 0 1px rgba(0,0,0,.25),inset 0 0 40px rgba(10,200,255,.12);}
.kdv-badge{position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:2147483600;pointer-events:auto;
  display:flex;align-items:center;gap:8px;height:34px;padding:0 8px 0 12px;border-radius:100px;
  background:rgba(18,20,28,.92);color:#e8f6ff;backdrop-filter:blur(20px);box-shadow:0 6px 20px rgba(0,0,0,.4);
  font-size:12.5px;font-weight:700;letter-spacing:.3px;}
.kdv-badge b{color:#26c6ff;}
.kdv-dot{width:8px;height:8px;border-radius:50%;background:#26c6ff;box-shadow:0 0 8px #26c6ff;animation:kdvPulse 1.4s infinite;}
@keyframes kdvPulse{50%{opacity:.35;}}
.kdv-hint{font-weight:500;opacity:.6;font-size:11px;}
.kdv-btn{border:0;background:rgba(255,255,255,.1);color:#cfe9f5;font:inherit;font-size:11.5px;font-weight:700;
  height:24px;padding:0 9px;border-radius:100px;cursor:pointer;}
.kdv-btn:hover{background:rgba(255,255,255,.2);}
.kdv-btn.on{background:#0a84ff;color:#fff;}
.kdv-chip{border:0;background:rgba(10,132,255,.22);color:#9fd2ff;font:inherit;font-size:11.5px;font-weight:800;
  height:24px;padding:0 11px;border-radius:100px;cursor:pointer;}
.kdv-chip:hover{background:rgba(10,132,255,.36);}
.kdv-chip.has{background:#0a84ff;color:#fff;}
html.kdv-cursor,html.kdv-cursor *{cursor:crosshair !important;}
/* z-index 를 떠있는 AI 채팅창(#kmktAiWin, 2147483001) 위로 올려 그 안의 요소도 하이라이트가 보이게(요청5) */
.kdv-hl{position:fixed;z-index:2147483300;pointer-events:none;border:2px solid #0a84ff;border-radius:3px;
  background:rgba(10,132,255,.14);box-shadow:0 0 0 1px rgba(10,132,255,.5);display:none;}
/* ── 세션 패널 (배지에서 드롭다운, 다크) ── */
.kdv-sess{position:fixed;top:52px;left:50%;transform:translateX(-50%) translateY(-8px);z-index:2147483620;
  width:320px;max-width:calc(100vw - 24px);display:none;flex-direction:column;pointer-events:auto;
  border-radius:14px;overflow:hidden;background:rgba(22,24,32,.97);color:#dfeaf2;
  border:1px solid rgba(120,200,255,.25);box-shadow:0 24px 64px rgba(0,0,0,.6);opacity:0;
  transition:opacity .18s,transform .18s cubic-bezier(.32,.72,0,1);}
.kmkt-dev.sess-open .kdv-sess{display:flex;opacity:1;transform:translateX(-50%) translateY(0);}
.kdv-sess-h{display:flex;align-items:center;gap:8px;padding:11px 12px;border-bottom:1px solid rgba(255,255,255,.08);}
.kdv-sess-ic{font-size:15px;}
.kdv-sess-title{flex:1;min-width:0;border:0;background:rgba(255,255,255,.06);border-radius:8px;padding:6px 9px;
  color:#eaf4fb;font:inherit;font-size:13px;font-weight:700;outline:none;}
.kdv-sess-title:focus{box-shadow:0 0 0 2px rgba(10,132,255,.5);}
.kdv-sess-list{max-height:320px;overflow-y:auto;padding:6px;}
.kdv-empty{color:#8fa0ac;font-size:11.5px;text-align:center;padding:20px 10px;line-height:1.7;}
.kdv-item{display:flex;align-items:flex-start;gap:8px;padding:8px;border-radius:8px;}
.kdv-item:hover{background:rgba(255,255,255,.05);}
.kdv-item .kdv-ic{margin-top:1px;font-size:12px;color:#7fc4ff;}
.kdv-item-t{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.3;}
.kdv-item-t b{font-size:12px;font-weight:700;color:#dfeaf2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:ui-monospace,monospace;}
.kdv-item-t span{font-size:11px;color:#9fb0bc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kdv-item-x{flex:0 0 18px;border:0;background:transparent;color:#7a8a96;cursor:pointer;font-size:12px;border-radius:5px;}
.kdv-item-x:hover{background:rgba(255,59,48,.2);color:#ff6b60;}
.kdv-sess-foot{display:flex;gap:8px;padding:10px 12px;border-top:1px solid rgba(255,255,255,.08);}
.kdv-fbtn{flex:1;border:0;border-radius:8px;height:30px;font:inherit;font-size:12px;font-weight:700;cursor:pointer;
  background:rgba(255,255,255,.1);color:#dfeaf2;}
.kdv-fbtn:hover{background:rgba(255,255,255,.18);}
.kdv-fbtn.prim{background:#0a84ff;color:#fff;}
.kdv-fbtn.prim:hover{background:#0073ea;}
.kdv-sess-msg{font-size:11px;color:#7ee0a0;padding:0 12px;}
.kdv-sess-msg:not(:empty){padding:0 12px 10px;}
/* ── 인스펙터 팝오버 ── */
.kdv-pop{position:fixed;z-index:2147483640;width:420px;max-width:calc(100vw - 24px);max-height:calc(100vh - 24px);
  display:none;flex-direction:column;overflow:hidden;border-radius:14px;background:rgba(22,24,32,.97);
  color:#dfeaf2;border:1px solid rgba(120,200,255,.25);box-shadow:0 24px 64px rgba(0,0,0,.6);font-size:12.5px;}
.kdv-pop.show{display:flex;}
.kdv-pop-h{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.08);font-size:13px;color:#bfe6ff;}
.kdv-info{padding:10px 12px;line-height:1.6;border-bottom:1px solid rgba(255,255,255,.06);max-height:160px;overflow:auto;}
.kdv-info .kdv-k{color:#8fb6c8;}
.kdv-info code{background:rgba(120,180,255,.16);color:#d9ecff;padding:1px 5px;border-radius:5px;font-family:ui-monospace,monospace;font-size:11.5px;word-break:break-all;}
.kdv-src{padding:8px 12px;max-height:170px;overflow:auto;border-bottom:1px solid rgba(255,255,255,.06);font-family:ui-monospace,monospace;font-size:11px;line-height:1.55;}
.kdv-src-load{opacity:.6;font-family:inherit;}
.kdv-src .kdv-cand{padding:2px 0;}
.kdv-src .kdv-cand b{color:#7ee0a0;}
.kdv-src .kdv-cand span{opacity:.7;}
.kdv-pop textarea{margin:10px 12px 0;width:calc(100% - 24px);height:70px;resize:vertical;border-radius:9px;
  border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.05);color:#eaf4fb;font:inherit;font-size:12.5px;padding:8px 10px;outline:none;}
.kdv-pop textarea:focus{border-color:#0a84ff;}
.kdv-act{display:flex;align-items:center;gap:8px;padding:9px 12px 12px;}
.kdv-saved{margin-right:auto;font-size:11.5px;color:#7ee0a0;}
.kdv-add{border:0;background:rgba(10,132,255,.18);color:#7fc4ff;font:inherit;font-size:12px;font-weight:700;height:30px;padding:0 12px;border-radius:9px;cursor:pointer;}
.kdv-add:hover{background:rgba(10,132,255,.32);}
.kdv-save{border:0;background:#0a84ff;color:#fff;font:inherit;font-size:12px;font-weight:700;height:30px;padding:0 12px;border-radius:9px;cursor:pointer;}
.kdv-save:hover{background:#0073ea;}
/* ── 요청4: 우리 UI(팝오버·세션·배지) 위에서는 크로스헤어(+) 대신 자연스러운 커서 ── */
html.kdv-cursor #kmktDev,html.kdv-cursor #kmktDev *{cursor:auto !important;}
html.kdv-cursor #kmktDev button,html.kdv-cursor #kmktDev .kdv-chip,html.kdv-cursor #kmktDev .kdv-item-x,
html.kdv-cursor #kmktDev select{cursor:pointer !important;}
html.kdv-cursor #kmktDev textarea,html.kdv-cursor #kmktDev input{cursor:text !important;}
html.kdv-cursor #kmktDev .kdv-pop-h{cursor:move !important;}
/* ── 요청4: 팝오버/세션 스크롤바를 어두운 테마로 ── */
#kmktDev .kdv-info,#kmktDev .kdv-src,#kmktDev .kdv-sess-list{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.24) transparent;}
#kmktDev ::-webkit-scrollbar{width:10px;height:10px;}
#kmktDev ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);border-radius:7px;border:2px solid transparent;background-clip:padding-box;}
#kmktDev ::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.36);background-clip:padding-box;}
#kmktDev ::-webkit-scrollbar-track{background:transparent;}
/* ── 요청4: 팝오버 상단 드래그 핸들 ── */
.kdv-pop-h{cursor:move;user-select:none;-webkit-user-select:none;}
.kdv-pop-h button{cursor:pointer;}
/* ── 요청1: 미완료 세션 이어가기 행 ── */
.kdv-sess-cont{display:flex;gap:6px;padding:8px 12px 0;}
.kdv-sess-pick{flex:1;min-width:0;border:0;border-radius:8px;height:30px;padding:0 8px;font:inherit;font-size:11.5px;font-weight:600;
  background:rgba(255,255,255,.06);color:#cfe1ee;outline:none;}
.kdv-sess-pick:focus{box-shadow:0 0 0 2px rgba(10,132,255,.5);}
.kdv-sess-cont .kdv-fbtn{flex:0 0 38px;}
/* ── 작업1: 세션 항목 메모 인라인 편집 ── */
.kdv-item-memo{font-size:11px;color:#9fb0bc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:text;border-radius:4px;padding:1px 3px;}
.kdv-item-memo:hover{background:rgba(120,180,255,.14);color:#cfe1ee;}
.kdv-memo-edit{width:100%;margin-top:2px;border:1px solid #0a84ff;border-radius:6px;background:rgba(10,20,32,.9);
  color:#eaf4fb;font:inherit;font-size:11.5px;padding:5px 7px;resize:vertical;outline:none;}
/* ── 요청3(피드백): ⌘ 다중선택 — 팝오버 목록 + 페이지 위 번호 박스 ── */
.kdv-multi-h{font-size:12px;font-weight:700;color:#ffd089;margin-bottom:6px;}
.kdv-msel{display:flex;align-items:center;gap:7px;padding:3px 0;}
.kdv-msel code{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.kdv-mn{flex:0 0 16px;height:16px;border-radius:50%;background:#ffb02e;color:#1a1a1a;font:800 10px/16px ui-monospace,monospace;text-align:center;}
#kdvMultiBox .kdv-mbox{position:fixed;z-index:2147483290;pointer-events:none;border:2px solid #ffb02e;border-radius:3px;
  background:rgba(255,176,46,.13);box-shadow:0 0 0 1px rgba(255,176,46,.55);}
#kdvMultiBox .kdv-mbox-n{position:absolute;top:-9px;left:-9px;width:17px;height:17px;border-radius:50%;
  background:#ffb02e;color:#1a1a1a;font:800 10px/17px ui-monospace,monospace;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.4);}
@media (prefers-reduced-motion:reduce){.kdv-dot{animation:none;}.kdv-sess{transition:none;}}
</style>
<script>(function(){
  var root=document.getElementById('kmktDev');if(!root||root._w)return;root._w=1;
  var hl=document.getElementById('kdvHl'),pop=document.getElementById('kdvPop'),
      info=document.getElementById('kdvInfo'),srcBox=document.getElementById('kdvSrc'),
      memo=document.getElementById('kdvMemo'),saved=document.getElementById('kdvSaved'),
      pickBtn=document.getElementById('kdvPick'),
      listEl=document.getElementById('kdvList'),countEl=document.getElementById('kdvCount'),
      titleEl=document.getElementById('kdvSessTitle'),sideMsg=document.getElementById('kdvSideMsg'),
      copyBtn=document.getElementById('kdvCopy'),sessPick=document.getElementById('kdvSessPick'),
      loadBtn=document.getElementById('kdvLoadSess');
  var on=false,pick=true,sel=null,cx=0,cy=0,cands=[],anchors=[],multi=[];
  function isOurs(el){return el&&el.closest&&el.closest('#kmktDev');}
  function setOn(v){on=v;root.setAttribute('data-on',v?'1':'0');root.setAttribute('aria-hidden',v?'false':'true');
    document.documentElement.classList.toggle('kdv-cursor',v&&pick);
    if(!v){hideHl();closePop();root.classList.remove('sess-open');}else{loadSession();}}
  function setPick(v){pick=v;pickBtn.classList.toggle('on',v);pickBtn.textContent=v?'🖱 검사':'🖱 검사 꺼짐';
    document.documentElement.classList.toggle('kdv-cursor',on&&v);if(!v)hideHl();}
  function hideHl(){hl.style.display='none';}
  function showHl(el){var r=el.getBoundingClientRect();hl.style.display='block';
    hl.style.left=r.left+'px';hl.style.top=r.top+'px';hl.style.width=r.width+'px';hl.style.height=r.height+'px';}
  function closePop(){pop.classList.remove('show');sel=null;clearMulti();}
  function flash(t){sideMsg.textContent=t;setTimeout(function(){if(sideMsg.textContent===t)sideMsg.textContent='';},2600);}
  // ── element info (no regex except \\s; split(' ')) + ancestor trace (방안1-2) ──
  function classList(el){var c=(el.className&&typeof el.className==='string')?el.className:'';
    return c.split(' ').filter(function(x){return x;});}
  function cssPath(el){
    if(!el||el.nodeType!==1)return '';
    if(el.id)return '#'+el.id;
    var parts=[],cur=el,depth=0;
    while(cur&&cur.nodeType===1&&depth<4){
      var s=cur.tagName.toLowerCase();
      if(cur.id){parts.unshift('#'+cur.id);break;}
      var cls=classList(cur).slice(0,2);if(cls.length)s+='.'+cls.join('.');
      var par=cur.parentElement;
      if(par){var same=Array.prototype.filter.call(par.children,function(c){return c.tagName===cur.tagName;});
        if(same.length>1)s+=':nth-of-type('+(Array.prototype.indexOf.call(par.children,cur)+1)+')';}
      parts.unshift(s);cur=par;depth++;
    }
    return parts.join(' > ');
  }
  function ancestor(el){
    var p=el.parentElement,hop=0,aId='',aCls='';
    while(p&&hop<6){
      if(!aId&&p.id)aId=p.id;
      if(!aCls){var pc=classList(p).filter(function(c){return c.length>=5;});if(pc.length)aCls=pc[0];}
      if(aId)break;p=p.parentElement;hop++;
    }
    return {id:aId,cls:aCls};
  }
  // 현재 computed 스타일(핵심 속성만) — 에이전트가 현재값을 알고 정확히 수정(추측 제거)
  function pickStyles(el){
    try{var cs=getComputedStyle(el);}catch(e){return {};}
    var want=['color','background-color','font-size','font-weight','letter-spacing','line-height',
      'padding','margin','border-radius','opacity','text-align','display'],o={};
    want.forEach(function(k){var v=cs.getPropertyValue(k);
      if(v&&v!=='normal'&&v!=='auto'&&v!=='none'&&v!=='0px'&&v!=='rgba(0, 0, 0, 0)'&&v!=='0px 0px')o[k]=v;});
    return o;
  }
  // 차트 요소 감지 — Plotly/canvas/SVG 내부면 설정 코드로 안내(마크업이 아니라 차트 config 가 진짜 소스)
  function chartKind(el){
    try{
      if(el.closest('.js-plotly-plot')||el.closest('#plotlyChart'))return 'plotly';
      if(el.tagName==='CANVAS'||(el.closest&&el.closest('canvas')))return 'canvas';
      if(el.closest('svg'))return 'svg';
    }catch(e){}
    return '';
  }
  function elInfo(el){
    var cls=classList(el);
    var role=el.getAttribute&&(el.getAttribute('aria-label')||el.getAttribute('role')||el.getAttribute('title')||'');
    var txt=(el.innerText||el.textContent||'').trim().replace(/\\s+/g,' ');
    var anc=ancestor(el);
    anchors=[];
    if(el.id)anchors.push('id="'+el.id+'"');
    cls.forEach(function(c){if(c.length>=4)anchors.push('.'+c);});
    if(txt&&txt.length>=4)anchors.push('"'+txt.slice(0,24)+'"');
    if(!el.id&&anc.id)anchors.push('(부모)#'+anc.id);
    var ck=chartKind(el);
    if(ck&&!el.id&&!anc.id)anchors.push('(차트:'+ck+') go.Figure/go.Treemap/Plotly.react/lineChart');
    return {tag:el.tagName.toLowerCase(),id:el.id||'',classes:cls.join(' '),role:role||'',
            text:txt.slice(0,160),selector:cssPath(el),dompath:cssPath(el),
            ancestor_id:anc.id,ancestor_classes:anc.cls,
            styles:pickStyles(el),chart:chartKind(el)};
  }
  function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
  function renderInfo(d){
    var rows=[['route',location.pathname+location.search],['tag',d.tag]];
    if(d.id)rows.push(['id',d.id]);
    if(d.classes)rows.push(['class',d.classes]);
    if(!d.id&&d.ancestor_id)rows.push(['ancestor','#'+d.ancestor_id]);
    if(d.chart)rows.push(['📊 chart',d.chart+' — 설정 코드를 고쳐라(마크업 X)']);
    if(d.role)rows.push(['role/aria',d.role]);
    if(d.text)rows.push(['text',d.text]);
    rows.push(['selector',d.selector]);
    var html=rows.map(function(r){return '<div><span class="kdv-k">'+r[0]+':</span> <code>'+esc(r[1])+'</code></div>';}).join('');
    var st=d.styles||{},ks=Object.keys(st);
    if(ks.length)html+='<div style="margin-top:5px;"><span class="kdv-k">현재 스타일:</span> '
      +ks.map(function(k){return '<code>'+esc(k)+':'+esc(st[k])+'</code>';}).join(' ')+'</div>';
    info.innerHTML=html;
  }
  function renderSrc(){
    if(!cands.length){srcBox.innerHTML='<div class="kdv-src-load">자동 후보 없음 — 앵커로 grep: '+esc(anchors.join('  '))+'</div>';return;}
    srcBox.innerHTML=cands.map(function(c){
      return '<div class="kdv-cand"><b>'+esc(c.file)+':'+c.line+'</b> <span>['+c.kind+']</span><br>'+esc(c.snippet)+'</div>';
    }).join('');
  }
  function openPop(el){
    clearMulti();   // 일반 클릭이면 ⌘ 다중선택 초기화
    sel=elInfo(el);renderInfo(sel);cands=[];srcBox.innerHTML='<div class="kdv-src-load">소스 위치 찾는 중…</div>';
    saved.textContent='';memo.value='';root.classList.remove('sess-open');
    pop.classList.add('show');
    var pw=pop.offsetWidth||420,ph=pop.offsetHeight||360;
    var x=Math.min(cx+12,window.innerWidth-pw-10),y=Math.min(cy+12,window.innerHeight-ph-10);
    pop.style.left=Math.max(10,x)+'px';pop.style.top=Math.max(50,y)+'px';
    setTimeout(function(){memo.focus();},60);
    fetch('/api/dev/locate',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({route:location.pathname+location.search,id:sel.id,classes:sel.classes,text:sel.text,
        tag:sel.tag,ancestor_id:sel.ancestor_id,ancestor_classes:sel.ancestor_classes})})
      .then(function(r){return r.json();}).then(function(j){cands=(j&&j.candidates)||[];renderSrc();})
      .catch(function(){cands=[];renderSrc();});
  }
  function payload(){return {route:location.pathname+location.search,element:sel,anchors:anchors,
    candidates:cands,memo:memo.value};}
  function save(){
    if(isMulti()){multiAddAll(function(){saveSession();closePop();});return;}   // 다중: 추가 후 세션 저장
    if(!sel)return;saved.textContent='저장 중…';
    fetch('/api/dev/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())})
      .then(function(r){return r.json();}).then(function(j){
        saved.textContent=j&&j.ok?('✓ 저장됨: '+j.path):('실패: '+((j&&j.error)||'?'));
        if(j&&j.ok)setTimeout(closePop,900);})
      .catch(function(e){saved.textContent='실패: '+e.message;});
  }
  function addToSession(){
    if(isMulti()){multiAddAll(function(){closePop();});return;}   // 다중: 모두 세션에 추가
    if(!sel)return;saved.textContent='추가 중…';
    fetch('/api/dev/session/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())})
      .then(function(r){return r.json();}).then(function(j){
        if(j&&j.ok){renderList(j.items||[]);closePop();flash('세션에 추가됨 ('+(j.items?j.items.length:0)+')');}
        else saved.textContent='실패: '+((j&&j.error)||'?');})
      .catch(function(e){saved.textContent='실패: '+e.message;});
  }
  // ── 요청2: 요소+소스 정보 클립보드 복사 (⌘⇧C 또는 📋 버튼) ──
  function copyText(){
    if(!sel)return '';
    var L=['route: '+location.pathname+location.search,
           'selector: '+(sel.selector||''),
           'tag/id/classes: '+sel.tag+' / '+(sel.id||'-')+' / '+(sel.classes||'-')];
    if(sel.ancestor_id||sel.ancestor_classes)L.push('ancestor: #'+(sel.ancestor_id||'')+' .'+(sel.ancestor_classes||''));
    if(sel.text)L.push('text: '+sel.text);
    if(sel.chart)L.push('chart: '+sel.chart+' (마크업 아님 — 차트 설정 코드를 고칠 것)');
    if(anchors&&anchors.length)L.push('anchors: '+anchors.join('  '));
    if(cands&&cands.length){L.push('source candidates (file:line):');
      cands.forEach(function(c){L.push('  '+c.file+':'+c.line+' ['+c.kind+'] '+c.snippet);});}
    if(memo.value.trim())L.push('memo: '+memo.value.trim());
    return L.join('\\n');
  }
  function multiText(){
    var blocks=multi.map(function(m,i){
      var L=['['+(i+1)+'] selector: '+(m.info.selector||''),
             '    tag/id/classes: '+m.info.tag+' / '+(m.info.id||'-')+' / '+(m.info.classes||'-')];
      if(m.info.text)L.push('    text: '+m.info.text);
      if(m.cands&&m.cands.length)m.cands.forEach(function(c){L.push('    '+c.file+':'+c.line+' ['+c.kind+'] '+c.snippet);});
      return L.join('\\n');});
    return 'route: '+location.pathname+location.search+'\\n'+blocks.join('\\n')
      +(memo.value.trim()?'\\nmemo(공통): '+memo.value.trim():'');
  }
  function doCopy(t){
    function ok(){saved.textContent='✓ 클립보드 복사됨';}
    function fb(){try{var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';
      document.body.appendChild(ta);ta.focus();ta.select();document.execCommand('copy');document.body.removeChild(ta);ok();}
      catch(e){saved.textContent='복사 실패';}}
    try{if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(ok,fb);else fb();}catch(e){fb();}
  }
  function copyInfo(){
    if(isMulti()){doCopy(multiText());return;}
    if(!sel){flash('복사할 요소가 없습니다');return;}
    doCopy(copyText());
  }
  // ── 요청3(피드백): ⌘+클릭 = 여러 요소를 누적 선택 → 팝오버에 한 번에 반영, 공통 메모로 일괄 추가 ──
  function isMulti(){return multi.length>0;}
  function clearMulti(){multi=[];var c=document.getElementById('kdvMultiBox');if(c&&c.parentNode)c.parentNode.removeChild(c);}
  function multiBoxes(){
    var c=document.getElementById('kdvMultiBox');
    if(!c){c=document.createElement('div');c.id='kdvMultiBox';root.appendChild(c);}
    c.innerHTML=multi.map(function(m,i){var r=m.el.getBoundingClientRect();
      return '<div class="kdv-mbox" style="left:'+r.left+'px;top:'+r.top+'px;width:'+r.width+'px;height:'+r.height+'px;">'
        +'<span class="kdv-mbox-n">'+(i+1)+'</span></div>';}).join('');
  }
  function multiAdd(el){
    var info=elInfo(el),anc=anchors.slice();   // elInfo 가 전역 anchors 를 채운다
    if(multi.some(function(m){return m.info.selector===info.selector;})){flash('이미 선택됨 ('+multi.length+')');return;}
    var entry={el:el,info:info,anchors:anc,cands:[]};multi.push(entry);
    multiBoxes();openMulti();
    fetch('/api/dev/locate',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({route:location.pathname+location.search,id:info.id,classes:info.classes,text:info.text,
        tag:info.tag,ancestor_id:info.ancestor_id,ancestor_classes:info.ancestor_classes})})
      .then(function(r){return r.json();}).then(function(j){entry.cands=(j&&j.candidates)||[];if(isMulti())renderMulti();})
      .catch(function(){});
  }
  function openMulti(){
    sel=null;root.classList.remove('sess-open');saved.textContent='';
    if(!pop.classList.contains('show')){
      pop.classList.add('show');
      var pw=pop.offsetWidth||420,ph=pop.offsetHeight||360;
      pop.style.left=Math.max(10,Math.min(cx+12,window.innerWidth-pw-10))+'px';
      pop.style.top=Math.max(50,Math.min(cy+12,window.innerHeight-ph-10))+'px';
    }
    renderMulti();setTimeout(function(){memo.focus();},40);
  }
  function renderMulti(){
    info.innerHTML='<div class="kdv-multi-h">⌘ 다중선택 <b>'+multi.length+'</b>개 · 공통 메모로 일괄 추가</div>'
      +multi.map(function(m,i){return '<div class="kdv-msel"><span class="kdv-mn">'+(i+1)+'</span>'
        +'<code>'+esc(m.info.selector||m.info.tag||'?')+'</code>'
        +'<button class="kdv-item-x" data-mi="'+i+'" title="선택 해제">✕</button></div>';}).join('');
    Array.prototype.forEach.call(info.querySelectorAll('.kdv-item-x'),function(b){
      b.addEventListener('click',function(){multi.splice(parseInt(b.dataset.mi,10),1);
        if(isMulti()){multiBoxes();renderMulti();}else{clearMulti();closePop();}});});
    var nc=multi.reduce(function(a,m){return a+(m.cands?m.cands.length:0);},0);
    srcBox.innerHTML='<div class="kdv-src-load">소스 후보 '+nc+'개 · ➕ 세션 추가 = 각 요소를 항목으로(공통 메모) · 💾 = 추가 후 세션 저장</div>';
  }
  function multiAddAll(then){
    if(!isMulti())return;var items=multi.slice(),mm=memo.value;saved.textContent='추가 중…';
    (function next(i){
      if(i>=items.length){flash('세션에 '+items.length+'개 추가됨');if(then)then();return;}
      var m=items[i];
      fetch('/api/dev/session/add',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({route:location.pathname+location.search,element:m.info,anchors:m.anchors,candidates:m.cands,memo:mm})})
        .then(function(r){return r.json();}).then(function(j){if(j&&j.ok)renderList(j.items||[]);next(i+1);})
        .catch(function(){next(i+1);});
    })(0);
  }
  // ── session (badge counter + dropdown panel) ──
  function renderList(items){
    var n=items.length;countEl.textContent='📌 '+n;countEl.classList.toggle('has',n>0);
    if(!n){listEl.innerHTML='<div class="kdv-empty">요소를 클릭 → 메모 → <b>➕ 세션 추가</b><br>모은 뒤 <b>💾 세션 저장</b></div>';return;}
    listEl.innerHTML=items.map(function(it,i){var el=it.element||{};
      return '<div class="kdv-item"><span class="kdv-ic">📍</span><span class="kdv-item-t">'
        +'<b>'+esc(el.selector||el.tag||'?')+'</b>'
        +'<span class="kdv-item-memo" data-i="'+i+'" title="클릭하여 메모 수정">'+esc(it.memo||'(메모 없음 — 클릭해 입력)')+'</span></span>'
        +'<button class="kdv-item-x" data-i="'+i+'" title="제거">✕</button></div>';}).join('');
    Array.prototype.forEach.call(listEl.querySelectorAll('.kdv-item-x'),function(b){
      b.addEventListener('click',function(){removeItem(parseInt(b.dataset.i,10));});});
    Array.prototype.forEach.call(listEl.querySelectorAll('.kdv-item-memo'),function(s){   // 작업1: 메모 인라인 수정
      s.addEventListener('click',function(){editMemo(parseInt(s.dataset.i,10),s,items);});});
  }
  function editMemo(i,spanEl,items){
    var cur=(items[i]&&items[i].memo)||'';
    var ta=document.createElement('textarea');ta.className='kdv-memo-edit';ta.value=cur;ta.rows=2;
    spanEl.parentNode.replaceChild(ta,spanEl);ta.focus();ta.select();
    var doneFlag=false;
    function commit(){if(doneFlag)return;doneFlag=true;
      fetch('/api/dev/session/update',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({index:i,memo:ta.value})}).then(function(r){return r.json();})
        .then(function(j){renderList((j&&j.items)||items);flash('✓ 메모 수정됨');})
        .catch(function(){renderList(items);});}
    ta.addEventListener('keydown',function(e){
      if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();ta.blur();}      // ⌘/Ctrl+Enter = 저장
      else if(e.key==='Escape'){e.stopPropagation();doneFlag=true;renderList(items);} // 취소
    });
    ta.addEventListener('blur',commit);
  }
  function loadSession(){
    listSessions();
    fetch('/api/dev/session/state').then(function(r){return r.json();}).then(function(j){
      if(j){if(j.title&&document.activeElement!==titleEl)titleEl.value=j.title;renderList(j.items||[]);}})
      .catch(function(){});
  }
  // ── 요청1: 미완료 세션 목록 + 이어가기 ──
  function listSessions(){
    if(!sessPick)return;
    fetch('/api/dev/session/list').then(function(r){return r.json();}).then(function(j){
      var ss=(j&&j.sessions)||[];
      sessPick.innerHTML='<option value="">⤴︎ 미완료 세션 이어가기…</option>'+
        ss.map(function(s){return '<option value="'+esc(s.file)+'">'+esc(s.title)+' ('+s.count+')</option>';}).join('');
      if(j&&j.current_file)sessPick.value=j.current_file;
    }).catch(function(){});
  }
  function loadExisting(){
    var f=sessPick&&sessPick.value;if(!f){flash('이어갈 세션을 먼저 선택하세요');return;}
    fetch('/api/dev/session/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file:f})})
      .then(function(r){return r.json();}).then(function(j){
        if(j&&j.ok){if(j.title)titleEl.value=j.title;renderList(j.items||[]);
          flash('✓ 이어가기: '+f+' ('+(j.items?j.items.length:0)+'개) — 추가 후 저장하면 이 파일을 갱신');}
        else flash('불러오기 실패: '+((j&&j.error)||'?'));})
      .catch(function(e){flash('실패: '+e.message);});
  }
  function removeItem(i){
    fetch('/api/dev/session/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:i})})
      .then(function(r){return r.json();}).then(function(j){if(j&&j.ok)renderList(j.items||[]);}).catch(function(){});
  }
  function newSession(){
    fetch('/api/dev/session/new',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({title:(titleEl.value||'새 세션')})})
      .then(function(r){return r.json();}).then(function(){renderList([]);flash('새 세션 시작');}).catch(function(){});
  }
  function saveSession(){
    fetch('/api/dev/session/save',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({title:(titleEl.value||'세션')})})
      .then(function(r){return r.json();}).then(function(j){
        if(j&&j.ok){renderList([]);titleEl.value='새 세션';flash('✓ 저장: '+j.path);}
        else flash('실패: '+((j&&j.error)||'비어있음'));}).catch(function(e){flash('실패: '+e.message);});
  }
  // ── events ──
  document.addEventListener('keydown',function(e){
    var k=(e.key||'').toLowerCase();
    if((e.metaKey||e.ctrlKey)&&e.shiftKey&&k==='d'){e.preventDefault();setOn(!on);return;}
    if(on&&(e.metaKey||e.ctrlKey)&&e.shiftKey&&k==='c'&&pop.classList.contains('show')){e.preventDefault();copyInfo();return;}  // 요청2
    var ae=document.activeElement,inEdit=ae&&ae.classList&&ae.classList.contains('kdv-memo-edit');  // 작업1: 인라인 메모 편집 중엔 Esc=취소(필드가 처리)
    if(on&&e.key==='Escape'){if(inEdit)return;if(pop.classList.contains('show'))closePop();
      else if(root.classList.contains('sess-open'))root.classList.remove('sess-open');else setOn(false);}
  },true);
  document.addEventListener('mousemove',function(e){
    if(!on||!pick||pop.classList.contains('show'))return;
    if(isOurs(e.target)){hideHl();return;}
    showHl(e.target);
  },true);
  function capture(e){
    if(!on||!pick)return;
    if(isOurs(e.target))return;
    // AI 질문 FAB 는 가로채지 않는다 → dev 모드에서도 챗을 열어 그 내부를 검사할 수 있게(요청5).
    if(e.target.closest&&e.target.closest('#kmktAiFab'))return;
    e.preventDefault();e.stopPropagation();
    cx=e.clientX;cy=e.clientY;hideHl();
    if(e.metaKey){multiAdd(e.target);return;}   // 요청3: ⌘+클릭 = 누적 다중선택 → 팝오버에 한 번에 반영
    openPop(e.target);
  }
  document.addEventListener('click',capture,true);
  document.addEventListener('contextmenu',function(e){if(on&&pick&&!isOurs(e.target))capture(e);},true);
  document.addEventListener('scroll',function(){if(on){hideHl();if(multi.length)multiBoxes();}},true);
  window.addEventListener('resize',function(){if(on&&multi.length)multiBoxes();});
  document.getElementById('kdvOff').addEventListener('click',function(){setOn(false);});
  document.getElementById('kdvPopX').addEventListener('click',closePop);
  document.getElementById('kdvSave').addEventListener('click',save);
  document.getElementById('kdvAddSess').addEventListener('click',addToSession);
  document.getElementById('kdvNewSess').addEventListener('click',newSession);
  document.getElementById('kdvSaveSess').addEventListener('click',saveSession);
  countEl.addEventListener('click',function(){root.classList.toggle('sess-open');if(root.classList.contains('sess-open'))loadSession();});
  pickBtn.addEventListener('click',function(){setPick(!pick);});
  // 요청2: 복사 버튼 · 요청1: 세션 이어가기 불러오기
  if(copyBtn)copyBtn.addEventListener('click',copyInfo);
  if(loadBtn)loadBtn.addEventListener('click',loadExisting);
  // 요청4: 팝오버 상단(헤더) 드래그로 이동
  (function(){var h=pop.querySelector('.kdv-pop-h'),drag=false,sx,sy,ox,oy;if(!h)return;
    h.addEventListener('pointerdown',function(e){if(e.target.closest('button'))return;
      drag=true;var r=pop.getBoundingClientRect();ox=r.left;oy=r.top;sx=e.clientX;sy=e.clientY;
      try{h.setPointerCapture(e.pointerId);}catch(_){}e.preventDefault();});
    h.addEventListener('pointermove',function(e){if(!drag)return;
      var nx=ox+(e.clientX-sx),ny=oy+(e.clientY-sy);
      nx=Math.max(6,Math.min(nx,window.innerWidth-pop.offsetWidth-6));
      ny=Math.max(46,Math.min(ny,window.innerHeight-44));
      pop.style.left=nx+'px';pop.style.top=ny+'px';});
    function end(e){drag=false;try{h.releasePointerCapture(e.pointerId);}catch(_){}}
    h.addEventListener('pointerup',end);h.addEventListener('pointercancel',end);
  })();
})();</script>
"""
