#!/usr/bin/env python3
"""Regenerate docs/CODEMAP.md — a navigation index for the 13k-line backend.

Why: scripts/market_dashboard3_realtime.py is a single ~736 KB file (~50% of which is
inline HTML/CSS/JS template strings). An AI coding agent cannot read it in one context
window. CODEMAP.md lists every route, inline template and `_inject_*` hook **with line
numbers** so an agent can Read(offset=…, limit=…) / grep straight to the right region
instead of scanning the whole file — saving tokens and dodging the context limit.

Run:  python3 scripts/gen_codemap.py
Line numbers drift as the file is edited; regenerate after large changes.
"""
from __future__ import annotations

import ast
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "market_dashboard3_realtime.py"
OUT = ROOT / "docs" / "CODEMAP.md"

TEMPLATE_DESC = {
    "_LANDING_HTML": "랜딩(홈) 페이지 — 검색·탭·테마토글·카드",
    "_OVERSEAS_HTML": "해외주식 페이지(히어로·KPI·차트·M4퀀트)",
    "_ASK_WIDGET_HTML": "플로팅 AI 채팅 위젯(Gemini형 입력바·모델팝업·중지)",
    "_REALTIME_HTML": "실시간 트레이딩 데스크(호가·체결·페이퍼)",
    "_BACKTEST_HTML": "백테스터(다크 콕핏·캔들·성과패널)",
    "_WORLD_HTML": "세계 시장 3뷰(국내/미국/글로벌)",
    "_INDEX_HTML": "지수 상세 페이지",
    "_MACRO_HTML": "경제지표(ECOS·FRED·글로벌)",
    "_MARKET_HTML": "시장 현황(시총상위·상하한가·시황)",
    "_RESEARCH_HTML": "증권사 리포트 뷰어",
    "_WORLD_DETAIL_HTML": "세계 지수 상세/차트",
    "_FX_STYLE": "리포트 비파괴 주입 CSS(글라스·카운트업)",
    "_FX_JS": "리포트 비파괴 주입 JS(카운트업·틸트·테마)",
    "_PDF_VIEW_HTML": "PDF 줌 뷰어",
    "_M4_STYLE": "M4 퀀트 다크 콕핏 CSS",
    "_M4_WIRE": "M4 3D 자동회전 JS(rAF)",
}
INJECT_ANCHOR = {
    "_inject_fx": "`</head>`/`</body>`",
    "_inject_m4_tab": '`</nav>`/`<footer` + `class="tab-btn"` 카운팅',
    "_inject_ask": "마지막 `</body>`",
    "_inject_floating_ai": "`</body>`",
    "_inject_realtime": "swap",
    "_inject_loader": "`<head>`/swap",
    "_inject_profile": "카드 주입",
    "_ask_setter": "KMKT_ASK 스크립트",
}


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    lines = src.split("\n")

    routes = []
    for i, ln in enumerate(lines):
        m = re.match(r'\s*@app\.(get|post|put|delete)\(\s*["\']([^"\']+)', ln)
        if not m:
            continue
        handler = ""
        for j in range(i + 1, min(i + 6, len(lines))):
            dm = re.match(r"\s*def\s+(\w+)", lines[j])
            if dm:
                handler = dm.group(1)
                break
        routes.append((i + 1, m.group(1).upper(), m.group(2), handler))

    # Inline templates were extracted to scripts/ui_templates.py (changes_77); scan there.
    ui_path = SRC.parent / "ui_templates.py"
    ui_src = ui_path.read_text(encoding="utf-8") if ui_path.exists() else ""
    tmpls = []
    for blob, where in ((ui_src, "ui_templates.py"), (src, "main")):
        for m in re.finditer(r'^(_?[A-Za-z0-9_]+)\s*=\s*([rf]?""".*?""")', blob, re.S | re.M):
            name = m.group(1)
            ln = blob[: m.start()].count("\n") + 1
            try:
                sz = len(ast.literal_eval(m.group(2)))
            except Exception:  # noqa: BLE001
                sz = 0
            tmpls.append((ln, name, sz, where))

    funcs = [i + 1 for i, ln in enumerate(lines) if re.match(r"def\s+\w+", ln)]
    injects = [
        (i + 1, re.search(r"def (_inject_\w+|_ask_setter)", ln).group(1))
        for i, ln in enumerate(lines)
        if re.search(r"def (_inject_\w+|_ask_setter)", ln)
    ]

    groups: "OrderedDict[str, list]" = OrderedDict()
    for r in routes:
        path = r[2]
        seg = path.strip("/").split("/")
        if path.startswith("/api/"):
            g = "/api/" + (seg[1] if len(seg) > 1 else "")
        else:
            g = "/" + (seg[0] if seg and seg[0] else "(root)")
        groups.setdefault(g, []).append(r)

    tmpl_chars = sum(t[2] for t in tmpls)
    o = []
    o.append("# CODEMAP — `scripts/market_dashboard3_realtime.py` 내비게이션 인덱스")
    o.append("")
    o.append("> 자동 생성(라인 번호 포함). **목적:** 13k줄·736KB 단일 백엔드 파일을 *통째로 읽지 않고*")
    o.append("> 필요한 지점으로 바로 점프하기 위한 인덱스. AI 코딩 에이전트는 이 표에서 라인 번호를 보고")
    o.append("> `Read(offset=…, limit=…)` 또는 grep 으로 해당 구역만 열어 **토큰을 아끼고 컨텍스트 한계를 회피**한다.")
    o.append("> 재생성: `python3 scripts/gen_codemap.py`. 라인 번호는 편집하면 바뀌니 큰 변경 후 재생성할 것.")
    o.append("")
    o.append(
        f"- 총 라인: **{len(lines):,}** · 바이트: **{len(src.encode()):,}** · 라우트: **{len(routes)}** "
        f"· top-level 함수: **{len(funcs)}** · 인라인 템플릿: **{len(tmpls)}**"
    )
    o.append(
        f"- 📦 페이지/위젯 템플릿 **{len(tmpls)}개({tmpl_chars:,}자)** 는 `scripts/ui_templates.py` 로 분리됨"
        "(changes_77). 마크업 수정은 거기서, 조립/주입/로직은 main 에서."
    )
    o.append("")
    o.append("## 1. 인라인 템플릿 (HTML/CSS/JS 문자열) → `scripts/ui_templates.py`")
    o.append("")
    o.append("| 파일 | 라인 | 이름 | 크기(자) | 용도(추정) |")
    o.append("|---|---:|---|---:|---|")
    for ln, name, sz, where in sorted(tmpls, key=lambda t: (t[3] != "ui_templates.py", t[0])):
        o.append(f"| {where} | {ln} | `{name}` | {sz:,} | {TEMPLATE_DESC.get(name, '')} |")
    o.append("")
    o.append("## 2. 라우트 (그룹별) — `@app.get/post`")
    o.append("")
    for g, rs in groups.items():
        o.append(f"### `{g}`  ({len(rs)})")
        o.append("| 라인 | 메서드 | 경로 | 핸들러 |")
        o.append("|---:|:--|--|--|")
        for ln, meth, path, h in rs:
            o.append(f"| {ln} | {meth} | `{path}` | `{h}` |")
        o.append("")
    o.append("## 3. `_inject_*` 비파괴 주입 — 순서/앵커 (취약 지점)")
    o.append("")
    o.append("| 라인 | 함수 | 앵커(문자열 수술) |")
    o.append("|---:|--|--|")
    for ln, name in injects:
        o.append(f"| {ln} | `{name}` | {INJECT_ANCHOR.get(name, '')} |")
    o.append("")
    o.append("> ⚠️ 이 함수들은 원본 빌더 HTML 을 문자열 `.replace()`/카운팅으로 사후 수술한다. 앵커가 바뀌면")
    o.append("> **조용히 실패**(에러 없이 주입 누락)할 수 있다. changes_72 가 앵커 미발견 시 `logger.warning` 추가.")
    o.append("")
    o.append("## 4. 재생성")
    o.append("")
    o.append("`python3 scripts/gen_codemap.py` 로 재생성(라인 번호 최신화). 큰 편집/이동 후 갱신 권장.")
    o.append("")
    body = "\n".join(o)
    OUT.write_text(body, encoding="utf-8")
    print(f"WROTE {OUT.relative_to(ROOT)} — {len(body):,} chars, {len(routes)} routes, {len(tmpls)} templates")


if __name__ == "__main__":
    main()
