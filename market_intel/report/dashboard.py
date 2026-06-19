"""단일 자기완결 인터랙티브 HTML 대시보드 빌더.

- 상단 탭 네비게이션 (시장 스캔 / 섹터 로테이션 / 종목 / 뉴스·공시 등)
- plotly 차트 inline 삽입 (오프라인 동작)
- 모든 표는 클라이언트측 정렬·검색 가능 (경량 vanilla JS)
- Claude 분석 본문은 마크다운 → HTML 렌더
"""
from __future__ import annotations

import html
import json
import re
import uuid
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

# ── 마크다운(경량) → HTML ──────────────────────────────────────
def markdown_to_html(md: str) -> str:
    if not md:
        return ""
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def inline(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_ul()
            continue
        if line.startswith("### "):
            close_ul(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            close_ul(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            close_ul(); out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.lstrip().startswith(("- ", "* ")):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(line.lstrip()[2:])}</li>")
        else:
            close_ul(); out.append(f"<p>{inline(line)}</p>")
    close_ul()
    return "\n".join(out)


# ── 값 포맷 ────────────────────────────────────────────────────
def _fmt_cell(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, bool):
        return "Y" if v else "N"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        if v == int(v) and abs(v) >= 1000:
            return f"{int(v):,}"
        return f"{v:,.2f}" if abs(v) >= 1 else f"{v:.4f}"
    return html.escape(str(v))


def df_to_table_html(df: pd.DataFrame, max_rows: int | None = None,
                     search: bool = True, scroll_rows: int | None = None,
                     bold_first: bool = False) -> str:
    """표 HTML. search=False 면 검색창 제거, scroll_rows 지정 시 그 행수만 보이고 세로 스크롤,
    bold_first=True 면 첫 열(항목명)을 굵게·크게 강조."""
    if df is None or df.empty:
        return '<p class="empty">데이터 없음</p>'
    d = df.head(max_rows) if max_rows else df
    tid = "t" + uuid.uuid4().hex[:8]
    cls = "mi-table" + (" bold-first" if bold_first else "")
    head = "".join(f"<th onclick=\"miSort('{tid}',{i})\">{html.escape(str(c))}</th>"
                   for i, c in enumerate(d.columns))
    body_rows = []
    for _, row in d.iterrows():
        cells = "".join(f"<td>{_fmt_cell(v)}</td>" for v in row)
        body_rows.append(f"<tr>{cells}</tr>")
    body = "\n".join(body_rows)
    search_html = (f'<input class="mi-search" placeholder="🔍 검색…" '
                   f'oninput="miFilter(\'{tid}\',this.value)">' if search else "")
    if scroll_rows:
        max_h = 46 + scroll_rows * 42
        wrap = (f'<div class="mi-table-wrap tbl-scroll" style="max-height:{max_h}px">'
                f'<table id="{tid}" class="{cls}"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>')
    else:
        wrap = (f'<div class="mi-table-wrap"><table id="{tid}" class="{cls}">'
                f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
    return search_html + wrap


# ── 그룹(구분) 재무제표 렌더 ───────────────────────────────────
def grouped_table_html(df: pd.DataFrame, group_col: str = "구분",
                       acct_col: str = "계정과목") -> str:
    """'구분'으로 묶은 재무제표 HTML. 섹션 헤더 행을 끼워 가독성을 높인다."""
    if df is None or df.empty:
        return '<p class="empty">데이터 없음</p>'
    value_cols = [c for c in df.columns if c not in (group_col, acct_col)]
    tid = "t" + uuid.uuid4().hex[:8]
    ncol = 1 + len(value_cols)
    head = f"<th onclick=\"miSort('{tid}',0)\">{html.escape(acct_col)}</th>" + "".join(
        f"<th onclick=\"miSort('{tid}',{i+1})\">{html.escape(str(c))}</th>"
        for i, c in enumerate(value_cols))
    body, cur = [], None
    for _, row in df.iterrows():
        sec = str(row.get(group_col, ""))
        if sec != cur:
            cur = sec
            body.append(f'<tr class="sec-row"><td colspan="{ncol}">{html.escape(sec)}</td></tr>')
        acct = str(row.get(acct_col, ""))
        is_total = "총계" in acct or "합계" in acct or acct.endswith("현금흐름")
        cls = "acct total" if is_total else "acct"
        cells = f'<td class="{cls}">{html.escape(acct)}</td>'
        cells += "".join(f"<td>{_fmt_cell(row.get(c))}</td>" for c in value_cols)
        body.append(f"<tr>{cells}</tr>")
    return (
        f'<input class="mi-search" placeholder="🔍 계정 검색…" '
        f'oninput="miFilter(\'{tid}\',this.value)">'
        f'<div class="mi-table-wrap"><table id="{tid}" class="mi-table fin-table">'
        f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    )


def metric_cards_html(items: list[tuple]) -> str:
    """[(label, value, sub), ...] → 큰 숫자 지표 카드 그리드."""
    if not items:
        return '<p class="empty">데이터 없음</p>'
    cards = []
    for label, value, sub in items:
        sub_html = f'<div class="m-sub">{html.escape(str(sub))}</div>' if sub else ""
        cards.append(
            f'<div class="metric-card"><div class="m-label">{html.escape(str(label))}</div>'
            f'<div class="m-value">{html.escape(str(value))}</div>{sub_html}</div>')
    return f'<div class="metric-grid">{"".join(cards)}</div>'


_PF_COLORS = ["#5cb85c", "#5b9bd5", "#f0c419", "#9b59b6", "#e08e3c"]  # 상위 5색


def portfolio_html(items: list[dict], color_top: int = 5) -> str:
    """ETF 포트폴리오(구성종목) — 상단 누적비중 막대 + 색상점·시세·전일대비 표.

    items: [{종목명, 주식수, 비중, 시세, 전일대비, 등락률, 방향}] (비중 내림차순 가정).
    네이버 포트폴리오 화면과 유사한 형태.
    """
    if not items:
        return '<p class="empty">구성종목 정보 없음</p>'

    def color(i):
        return _PF_COLORS[i] if i < color_top and i < len(_PF_COLORS) else "#c7cdd6"

    # 상단 누적 비중 막대
    segs, acc = [], 0.0
    for i, it in enumerate(items):
        w = it.get("비중")
        if not w:
            continue
        acc += float(w)
        segs.append(f'<div class="pf-seg" style="width:{float(w):.4f}%;background:{color(i)}" '
                    f'title="{html.escape(str(it.get("종목명","")))} {w}%"></div>')
    if acc < 100:
        segs.append(f'<div class="pf-seg" style="width:{100-acc:.4f}%;background:#e3e8f0" title="기타 {100-acc:.2f}%"></div>')
    bar = f'<div class="pf-bar">{"".join(segs)}</div>'

    head = ("<tr><th>항목</th><th>주식수(계약수)</th><th>비중</th>"
            "<th>시세</th><th>전일대비</th></tr>")
    body = []
    for i, it in enumerate(items):
        name = html.escape(str(it.get("종목명", "")))
        code = str(it.get("코드") or "").strip()
        if code:  # 종목명 클릭 → 통합 대시보드의 개별종목 리포트 새 탭(폴백: 네이버 증권)
            name = (f'<a class="pf-link" target="_blank" rel="noopener" '
                    f'onclick="return miOpenStock(event,\'{html.escape(code)}\')" '
                    f'href="https://stock.naver.com/domestic/stock/{html.escape(code)}/price">{name}</a>')
        dot = f'<span class="pf-dot" style="background:{color(i)}"></span>'
        shares = f'{it["주식수"]:,.0f}주' if it.get("주식수") is not None else "-"
        wt = f'{it["비중"]:.2f}%' if it.get("비중") is not None else "-"
        px = f'{it["시세"]:,.0f}' if it.get("시세") is not None else "-"
        diff, rate, arrow = it.get("전일대비"), it.get("등락률"), it.get("방향", "-")
        if diff is None:
            chg = "-"
            cls = ""
        else:
            cls = "pf-up" if arrow == "▲" else ("pf-down" if arrow == "▼" else "")
            rate_s = f"({rate:+.2f}%)" if rate is not None else ""
            chg = f"{arrow} {abs(diff):,.0f}{rate_s}"
        body.append(f'<tr><td class="pf-name">{dot}{name}</td><td>{shares}</td>'
                    f'<td>{wt}</td><td>{px}</td><td class="{cls}">{chg}</td></tr>')
    return (f'{bar}<div class="mi-table-wrap"><table class="mi-table pf-table">'
            f'<thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>')


def etf_header_html(code: str, name: str, asof: str, tags: list[str],
                    kpis: list[dict], info: list[tuple]) -> str:
    """네이버 ETF 헤더 스타일 — 코드·종목명 + KPI 4카드 + 상품정보 그리드.

    kpis: [{label, value, unit, sub, dir, val_dir}], info: [(label, value)].
    dir/val_dir 은 '▲'(상승·빨강)/'▼'(하락·파랑) 색상용.
    """
    cmap = {"▲": "k-up", "▼": "k-down"}
    tag_html = "".join(f'<span class="eh-tag">{html.escape(str(t))}</span>' for t in (tags or []))
    kpi_html = ""
    for k in kpis:
        unit = f'<span class="k-unit">{html.escape(str(k.get("unit","")))}</span>' if k.get("unit") else ""
        vcls = cmap.get(k.get("val_dir"), "")
        scls = cmap.get(k.get("dir"), "")
        sub = html.escape(str(k.get("sub") or ""))
        kpi_html += (f'<div class="eh-kpi"><div class="k-label">{html.escape(str(k["label"]))}</div>'
                     f'<div class="k-val {vcls}">{html.escape(str(k["value"]))}{unit}</div>'
                     f'<div class="k-sub {scls}">{sub}</div></div>')
    info_html = ""
    for label, val in info:
        v = "-" if val in (None, "", "-") else str(val)
        info_html += (f'<div class="ei"><span class="ei-l">{html.escape(str(label))}</span>'
                      f'<span class="ei-v">{html.escape(v)}</span></div>')
    return (f'<section class="card etf-head">'
            f'<div class="eh-top"><span class="eh-code">{html.escape(str(code))}</span>{tag_html}'
            f'<span class="eh-asof">{html.escape(str(asof))}</span></div>'
            f'<h2 class="eh-name">{html.escape(str(name))}</h2>'
            f'<div class="eh-kpis">{kpi_html}</div>'
            f'<div class="eh-info">{info_html}</div></section>')


def info_grid_html(items: list[tuple]) -> str:
    """[(label, value), ...] → 라벨·값이 가까운 반응형 정보 그리드(큰 글씨)."""
    items = [(k, v) for k, v in items if v not in (None, "", "-")]
    if not items:
        return '<p class="empty">정보 없음</p>'
    cells = "".join(
        f'<div class="info-cell"><div class="ig-label">{html.escape(str(k))}</div>'
        f'<div class="ig-value">{html.escape(str(v))}</div></div>' for k, v in items)
    return f'<div class="info-grid">{cells}</div>'


def price_hero_html(name: str, price_str: str, chg_str: str, direction: str,
                    meta: str) -> str:
    # 박스 전체를 등락 방향 색으로 채움: 상승 빨강 / 하락 파랑 / 보합 회색 (그라데이션)
    box = "up" if direction == "▲" else ("down" if direction == "▼" else "flat")
    return (
        f'<div class="price-hero {box}">'
        f'<div class="ph-top"><span class="ph-name">{html.escape(name)} 현재가</span>'
        f'<span class="ph-chg">{html.escape(direction)} {html.escape(chg_str)}</span></div>'
        f'<div class="ph-price">{html.escape(price_str)}</div>'
        f'<div class="ph-meta">{html.escape(meta)}</div></div>')


# ── 차트 헬퍼 ──────────────────────────────────────────────────
_PALETTE = ["#2E75B6", "#C00000", "#548235", "#BF8F00", "#7030A0",
            "#1F3864", "#C55A11", "#2E8B8B", "#843C0C", "#385723"]


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
               title: str = "") -> go.Figure:
    fig = go.Figure()
    if color and color in df.columns:
        for i, (key, grp) in enumerate(df.groupby(color)):
            fig.add_trace(go.Scatter(x=grp[x], y=grp[y], mode="lines",
                                     name=str(key),
                                     line=dict(color=_PALETTE[i % len(_PALETTE)], width=2)))
    else:
        fig.add_trace(go.Scatter(x=df[x], y=df[y], mode="lines",
                                 line=dict(color=_PALETTE[0], width=2)))
    _style(fig, title)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "",
              color_by_sign: bool = False, horizontal: bool = False) -> go.Figure:
    colors = _PALETTE[0]
    if color_by_sign:
        colors = ["#C00000" if v < 0 else "#2E75B6" for v in df[y].fillna(0)]
    if horizontal:
        fig = go.Figure(go.Bar(y=df[x], x=df[y], orientation="h", marker_color=colors))
    else:
        fig = go.Figure(go.Bar(x=df[x], y=df[y], marker_color=colors))
    _style(fig, title)
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str = "",
              hole: float = 0.45) -> go.Figure:
    """비중(%) 도넛 차트. 큰 비중부터 시계방향 정렬, 조각별 라벨+퍼센트 표시."""
    d = df.copy()
    d[values] = pd.to_numeric(d[values], errors="coerce")
    d = d[d[values] > 0].sort_values(values, ascending=False)
    fig = go.Figure(go.Pie(
        labels=d[names], values=d[values], hole=hole, sort=False,
        direction="clockwise", rotation=0,
        marker=dict(colors=[_PALETTE[i % len(_PALETTE)] for i in range(len(d))],
                    line=dict(color="#ffffff", width=1.5)),
        textposition="outside", textinfo="label+percent",
        texttemplate="%{label}<br>%{percent}",
        hovertemplate="%{label}: %{value:.2f}%<extra></extra>",
        insidetextorientation="radial",
    ))
    _style(fig, title)
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=20),
                      showlegend=True,
                      legend=dict(orientation="v", yanchor="middle", y=0.5,
                                  xanchor="left", x=1.02, font=dict(size=12)))
    return fig


def donut_breakdown_html(df: pd.DataFrame, names: str, values: str,
                         unit: str = "%", gray_labels=None, center=None) -> str:
    """좌측 도넛 + 우측 항목별 비중 리스트 (네이버 '자산비중 및 구성' 스타일).

    gray_labels: 회색으로 칠할 라벨 집합(예: '기타 주주(유통)').
    center: 중앙에 표시할 (이름, 값) 튜플. None이면 최상위 항목.
    """
    gray_labels = set(gray_labels or [])
    GRAY = "#c7cdd6"
    d = df.copy()
    d[values] = pd.to_numeric(d[values], errors="coerce")
    d = d[d[values] > 0].sort_values(values, ascending=False).reset_index(drop=True)
    if d.empty:
        return '<p class="empty">데이터 없음</p>'
    colors, list_colors, pi = [], [], 0
    for nm in d[names]:
        if str(nm) in gray_labels:
            colors.append(GRAY)               # 파이 슬라이스(Plotly)는 hex 필요
            list_colors.append("var(--dl-gray,#c7cdd6)")  # HTML 막대/점은 테마 변수
        else:
            c = _PALETTE[pi % len(_PALETTE)]
            colors.append(c)
            list_colors.append(c)
            pi += 1
    if center is not None:
        top_name, top_val = str(center[0]), float(center[1])
    else:
        top_name, top_val = str(d[names].iloc[0]), float(d[values].iloc[0])

    fig = go.Figure(go.Pie(
        labels=d[names], values=d[values], hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textinfo="none", hovertemplate="%{label}: %{value:.2f}" + unit + "<extra></extra>"))
    fig.update_layout(
        template="plotly_white", height=300, showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family="-apple-system, 'Helvetica Neue', sans-serif"),
        annotations=[dict(
            text=f"<b style='font-size:30px'>{top_val:.1f}{unit}</b><br>"
                 f"<span style='font-size:14px;color:#8a93a6'>{html.escape(top_name)}</span>",
            x=0.5, y=0.5, font=dict(color="#15233f"), showarrow=False)])
    div = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                      default_width="100%", config={"displaylogo": False})

    total = float(d[values].sum())
    rows = ""
    for i in range(len(d)):
        nm, vv = str(d[names].iloc[i]), float(d[values].iloc[i])
        share = vv / total * 100 if total else 0
        rows += (f'<div class="dl-row"><span class="dl-dot" style="background:{list_colors[i]}"></span>'
                 f'<span class="dl-name">{html.escape(nm)}</span>'
                 f'<span class="dl-bar"><span class="dl-barfill" '
                 f'style="width:{share:.1f}%;background:{list_colors[i]}"></span></span>'
                 f'<span class="dl-val">{vv:.1f} {unit}</span></div>')
    return (f'<div class="donut-wrap"><div class="donut-fig">{div}</div>'
            f'<div class="donut-list"><div class="dl-head">비중</div>{rows}</div></div>')


def _itr_sign_span(s: str) -> str:
    """순매수/등락 문자열에 색상 적용 (+ 빨강, - 파랑). 한국 관행."""
    s = (s or "").strip()
    cls = "t-up" if s.startswith("+") else ("t-down" if s.startswith("-") else "")
    return f'<span class="{cls}">{html.escape(s)}</span>' if cls else html.escape(s)


def _itr_chg_span(s: str) -> str:
    """'상승 180' → '▲ 180'(빨강), '하락 610' → '▼ 610'(파랑)."""
    s = (s or "").strip()
    if s.startswith("상승"):
        return f'<span class="t-up">▲ {html.escape(s[2:].strip())}</span>'
    if s.startswith("하락"):
        return f'<span class="t-down">▼ {html.escape(s[2:].strip())}</span>'
    return html.escape(s)


def investor_trend_html(rows: list[dict], visible: int = 8) -> str:
    """투자자별 매매 동향 — 상승/하락 기호·색상 적용 + 세로 스크롤(기본 8행 노출)."""
    if not rows:
        return '<p class="empty">데이터 없음</p>'
    cols = ["날짜", "종가", "전일대비", "등락률", "거래량", "외국인", "기관", "개인"]
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in rows:
        body += (
            "<tr>"
            f'<td class="t-date">{html.escape(str(r.get("날짜","")))}</td>'
            f'<td>{html.escape(str(r.get("종가","")))}</td>'
            f'<td>{_itr_chg_span(str(r.get("전일대비","")))}</td>'
            f'<td>{_itr_sign_span(str(r.get("등락률","")))}</td>'
            f'<td>{html.escape(str(r.get("거래량","")))}</td>'
            f'<td>{_itr_sign_span(str(r.get("외국인","")))}</td>'
            f'<td>{_itr_sign_span(str(r.get("기관","")))}</td>'
            f'<td>{_itr_sign_span(str(r.get("개인","")))}</td>'
            "</tr>")
    # 행 높이 ≈ 42px, 헤더 ≈ 46px → visible행 기준 최대 높이
    max_h = 46 + visible * 42
    return (f'<div class="itr-wrap" style="max-height:{max_h}px">'
            f'<table class="mi-table itr-table"><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def candle_chart(df: pd.DataFrame, x: str, o: str, h: str, l: str, c: str,
                 ma_windows: tuple = (5, 20, 60, 120), title: str = "") -> go.Figure:
    """종가 캔들차트 + 이동평균선(MA). 국내 관행: 상승=빨강, 하락=파랑."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df[x], open=df[o], high=df[h], low=df[l], close=df[c], name="가격",
        increasing_line_color="#C0392B", increasing_fillcolor="#C0392B",
        decreasing_line_color="#2E75B6", decreasing_fillcolor="#2E75B6",
        showlegend=False))
    ma_color = {5: "#2E8B57", 20: "#C0392B", 60: "#E08E3C", 120: "#7030A0"}
    close = pd.to_numeric(df[c], errors="coerce")
    for w in ma_windows:
        if len(df) >= w:
            fig.add_trace(go.Scatter(
                x=df[x], y=close.rolling(w).mean(), mode="lines", name=f"MA{w}",
                line=dict(color=ma_color.get(w, "#888"), width=1.3)))
    _style(fig, title)
    fig.update_layout(height=460, xaxis_rangeslider_visible=False)
    # Y축을 55k 가 아닌 전체 숫자(콤마)로 — 이미지처럼 10,000 / 20,000 …
    fig.update_yaxes(tickformat=",.0f", separatethousands=True)
    return fig


_RANGE_PERIODS = ("1주", "1개월", "3개월", "연초후", "1년", "3년", "5년")


def _init_xrange(dates: list[str], period: str) -> tuple[str, str] | None:
    """default 기간에 해당하는 [시작, 끝] 날짜 문자열. 데이터 범위를 벗어나면 보정."""
    from datetime import datetime, timedelta
    ds = [d for d in dates if d]
    if not ds:
        return None
    try:
        last = datetime.strptime(ds[-1][:10], "%Y-%m-%d")
        first = datetime.strptime(ds[0][:10], "%Y-%m-%d")
    except ValueError:
        return None
    if period == "1주":
        s = last - timedelta(days=7)
    elif period == "1개월":
        s = last - timedelta(days=31)
    elif period == "3개월":
        s = last - timedelta(days=92)
    elif period == "연초후":
        s = datetime(last.year, 1, 1)
    elif period == "1년":
        s = last - timedelta(days=365)
    elif period == "3년":
        s = last - timedelta(days=365 * 3)
    elif period == "5년":
        s = last - timedelta(days=365 * 5)
    else:
        s = first
    if s < first:
        s = first
    pad = timedelta(days=max((last - s).days * 0.012, 1))
    return (s - pad).strftime("%Y-%m-%d"), (last + pad).strftime("%Y-%m-%d")


def _range_toggle_html(uid: str, cdl_id: str, vol_id: str, dates: list[str],
                       highs: list, lows: list, vols: list, default: str) -> str:
    """캔들차트 기간 토글(1주~전체). x축 범위와 y축(가격·거래량)을 클라이언트에서 재조정."""
    btns = "".join(
        f'<button class="{"active" if p == default else ""}" '
        f"onclick=\"miRange_{uid}(this,'{p}')\">{p}</button>"
        for p in _RANGE_PERIODS)
    payload = json.dumps({"dates": dates, "highs": highs, "lows": lows, "vols": vols},
                         ensure_ascii=False, separators=(",", ":"))
    script = """<script>(function(){
var ID=%(uid)r,CDL=%(cdl)r,VOL=%(vol)r,D=%(data)s;
function bounds(p){var n=D.dates.length;if(!n)return null;
 var last=Date.parse(D.dates[n-1]),first=Date.parse(D.dates[0]),s=new Date(last);
 if(p==='1주')s.setDate(s.getDate()-7);
 else if(p==='1개월')s.setMonth(s.getMonth()-1);
 else if(p==='3개월')s.setMonth(s.getMonth()-3);
 else if(p==='연초후')s=new Date(new Date(last).getFullYear(),0,1);
 else if(p==='1년')s.setFullYear(s.getFullYear()-1);
 else if(p==='3년')s.setFullYear(s.getFullYear()-3);
 else if(p==='5년')s.setFullYear(s.getFullYear()-5);
 else s=new Date(first);
 var st=s.getTime();if(st<first)st=first;return [st,last];}
function apply(p){var b=bounds(p);if(!b)return;var s=b[0],e=b[1];
 var lo=Infinity,hi=-Infinity,vmax=0;
 for(var i=0;i<D.dates.length;i++){var t=Date.parse(D.dates[i]);
  if(t>=s&&t<=e){var L=D.lows[i],H=D.highs[i];
   if(L!=null&&L<lo)lo=L;if(H!=null&&H>hi)hi=H;
   if(D.vols&&D.vols[i]!=null&&D.vols[i]>vmax)vmax=D.vols[i];}}
 var padX=(e-s)*0.012||86400000;
 function f(ms){var d=new Date(ms);return d.toISOString().slice(0,10);}
 var xr=[f(s-padX),f(e+padX)];
 var cg=document.getElementById(CDL);
 if(cg&&cg.data&&window.Plotly){var lay={'xaxis.range':xr};
  if(isFinite(lo)&&isFinite(hi)){var py=(hi-lo)*0.08||hi*0.05;lay['yaxis.range']=[lo-py,hi+py];}
  Plotly.relayout(cg,lay);}
 if(VOL){var vg=document.getElementById(VOL);
  if(vg&&vg.data&&window.Plotly){var vl={'xaxis.range':xr};
   if(vmax>0)vl['yaxis.range']=[0,vmax*1.12];Plotly.relayout(vg,vl);}}}
window['miRange_'+ID]=function(btn,p){var bs=btn.parentNode.getElementsByTagName('button');
 for(var i=0;i<bs.length;i++)bs[i].className='';btn.className='active';apply(p);};
function init(){var cg=document.getElementById(CDL);
 if(cg&&cg.data&&window.Plotly)apply(%(default)r);else setTimeout(init,120);}
init();})();</script>""" % {"uid": uid, "cdl": cdl_id, "vol": vol_id,
                           "data": payload, "default": default}
    return f'<div class="range-toggle">{btns}</div>{script}'


def grouped_bar(df: pd.DataFrame, x: str, ys: list[str], title: str = "") -> go.Figure:
    fig = go.Figure()
    for i, y in enumerate(ys):
        if y in df.columns:
            fig.add_trace(go.Bar(x=df[x], y=df[y], name=y,
                                 marker_color=_PALETTE[i % len(_PALETTE)]))
    fig.update_layout(barmode="group")
    _style(fig, title)
    return fig


def grouped_line(df: pd.DataFrame, x: str, ys: list[str], title: str = "") -> go.Figure:
    """다계열 꺾은선 그래프 — 연도별 추이를 부드럽게 표현."""
    fig = go.Figure()
    for i, y in enumerate(ys):
        if y in df.columns:
            fig.add_trace(go.Scatter(
                x=df[x], y=df[y], mode="lines+markers", name=y,
                line=dict(color=_PALETTE[i % len(_PALETTE)], width=2.6),
                marker=dict(size=7)))
    _style(fig, title)
    return fig


def opinion_label(v: float) -> str:
    """평균 투자의견 점수(1~5) → 한글 라벨."""
    return ("적극매수" if v >= 4.5 else "매수" if v >= 3.5 else "중립"
            if v >= 2.5 else "매도" if v >= 1.5 else "적극매도")


def consensus_gauge(recomm_mean: float, dist: dict | None = None) -> go.Figure:
    """평균 투자의견(1 매도 ~ 5 매수) 게이지.

    dist 가 주어지면 아크 색상을 실제 분포 비율로 그린다 (전원 매수 → 아크 전체 초록).
    dist 없으면 고정 구간(매도 1-2.5 / 중립 2.5-3.5 / 매수 3.5-5)으로 표시.
    """
    v = float(recomm_mean)

    if dist:
        n_sell = int(dist.get("매도", 0) or 0)
        n_hold = int(dist.get("중립", 0) or 0)
        n_buy  = int(dist.get("매수", 0) or 0)
        total  = n_sell + n_hold + n_buy
    else:
        total = 0

    if total > 0:
        sell_end = 1 + (n_sell / total) * 4
        hold_end = sell_end + (n_hold / total) * 4
        raw_steps = [
            {"range": [1, sell_end], "color": "#f7d5d5"},
            {"range": [sell_end, hold_end], "color": "#fdeecf"},
            {"range": [hold_end, 5], "color": "#d6ebd6"},
        ]
        steps = [s for s in raw_steps if s["range"][1] > s["range"][0]]
    else:
        steps = [
            {"range": [1, 2.5], "color": "#f7d5d5"},
            {"range": [2.5, 3.5], "color": "#fdeecf"},
            {"range": [3.5, 5], "color": "#d6ebd6"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge", value=round(v, 2),
        title={"text": f"<b style='color:#1F3864;font-size:19px'>{opinion_label(v)} {v:.2f}점</b>"
                       f"<br><span style='font-size:10.5px;color:#8a93a6'>"
                       f"점수 기준 1=적극매도 · 2=매도 · 3=중립 · 4=매수 · 5=적극매수</span>",
               "font": {"size": 15}},
        gauge={
            "axis": {"range": [1, 5], "tickvals": [1, 2, 3, 4, 5], "tickfont": {"size": 10}},
            "bar": {"color": "#1F3864", "thickness": 0.25},
            "steps": steps,
            "threshold": {"line": {"color": "#E31837", "width": 4}, "thickness": 0.9, "value": v},
        }))
    fig.update_layout(template="plotly_white", height=280, margin=dict(l=30, r=30, t=64, b=14),
                      font=dict(family="-apple-system, 'Helvetica Neue', sans-serif"),
                      annotations=[dict(text=f"<b>{v:.2f}</b>", x=0.5, y=0.12, xref="paper",
                                        yref="paper", showarrow=False,
                                        font=dict(size=44, color="#15233f"))])
    return fig


def target_price_indicator(target: float, current: float) -> go.Figure:
    """평균 목표주가 + 현재가 대비 상승여력(델타) 인디케이터."""
    fig = go.Figure(go.Indicator(
        mode="number+delta", value=float(target),
        number={"prefix": "₩", "valueformat": ",.0f", "font": {"size": 40, "color": "#15233f"}},
        delta={"reference": float(current), "relative": True, "valueformat": ".1%",
               "increasing": {"color": "#c0392b"}, "decreasing": {"color": "#2e75b6"},
               "font": {"size": 20}},
        title={"text": "<b style='color:#1F3864'>평균 목표주가</b>"
                       f"<br><span style='font-size:11px;color:#8a93a6'>현재가(₩{float(current):,.0f}) 대비 상승여력</span>",
               "font": {"size": 15}}))
    fig.update_layout(template="plotly_white", height=280, margin=dict(l=30, r=30, t=64, b=14),
                      font=dict(family="-apple-system, 'Helvetica Neue', sans-serif"))
    return fig


def _dist_html(dist: dict) -> str:
    """투자의견 분포(매수/중립/매도) 미니 막대."""
    if not dist:
        return ""
    order = [("매수", "#c0392b", "buy"), ("중립", "#e0a93c", "hold"), ("매도", "#2e75b6", "sell")]
    total = sum(int(dist.get(k, 0)) for k, _, _ in order)
    if total <= 0:
        return ""
    seg = ""
    for lbl, col, _ in order:
        n = int(dist.get(lbl, 0))
        if n > 0:
            seg += f'<span style="width:{n / total * 100:.1f}%;background:{col}" title="{lbl} {n}"></span>'
    leg = " · ".join(f'<span class="cd-{cls}">{lbl} {int(dist.get(lbl, 0))}</span>'
                     for lbl, _, cls in order)
    return (f'<div class="cons-dist"><div class="cd-label">최근 3개월 의견 분포 ({total}건)</div>'
            f'<div class="cd-bar">{seg}</div><div class="cd-leg">{leg}</div></div>')


def consensus_panel_html(recomm_mean, target, current, create_date: str = "",
                         dist: dict | None = None) -> str:
    """좌측 투자의견 게이지(+의견 분포) + 우측 평균 목표주가(굵게)·상승여력 패널."""
    cells = []
    if recomm_mean:
        gdiv = pio.to_html(consensus_gauge(recomm_mean, dist=dist), include_plotlyjs=False,
                           full_html=False, default_width="100%", config={"displaylogo": False})
        cells.append(f'<div class="cons-col">{gdiv}{_dist_html(dist)}</div>')
    if target:
        up = ((float(target) / float(current) - 1) * 100) if current else None
        upcls = "up" if (up is not None and up > 0) else ("down" if (up is not None and up < 0) else "")
        arrow = "▲" if upcls == "up" else ("▼" if upcls == "down" else "")
        upside = (f'<div class="ct-upside {upcls}">{arrow} {abs(up):.1f}%'
                  f'<span class="ct-uplabel">상승여력</span></div>') if up is not None else ""
        sub = (f"현재가 ₩{float(current):,.0f}" if current else "") + \
              (f" · {create_date} 기준" if create_date else "")
        cells.append(
            '<div class="cons-col cons-target">'
            '<div class="ct-label">평균 목표주가</div>'
            f'<div class="ct-price">₩{float(target):,.0f}</div>'
            f'{upside}'
            f'<div class="ct-sub">{html.escape(sub)}</div></div>')
    if not cells:
        return ""
    return f'<div class="cons-wrap">{"".join(cells)}</div>'


_FIN_COLORS = {"매출": "#2E75B6", "영업이익": "#27AE60", "순이익": "#7030A0",
               "부채비율": "#E08E3C", "당좌비율": "#2E8B57"}


def fin_charts_html(charts: list[dict]) -> str:
    """실적/안정성/재무 등 토글형 인터랙티브 차트 3개를 가로로 배치한 카드 행.

    charts 각 항목: {title, mode("toggle"|"group"), type("bar"|"line"),
                     keys[지표...], data{annual/quarter}, period}
    """
    import json as _json
    cells = []
    for ch in charts:
        uid = uuid.uuid4().hex[:8]
        keys = ch["keys"]
        period_btn = ('<div class="fc-seg fc-period">'
                      '<button data-p="annual" class="active">연간</button>'
                      '<button data-p="quarter">분기</button></div>')
        metric_btn = ""
        if ch["mode"] == "toggle":
            metric_btn = '<div class="fc-seg fc-metric">' + "".join(
                f'<button data-m="{html.escape(k)}"{" class=\"active\"" if i == 0 else ""}>{html.escape(k)}</button>'
                for i, k in enumerate(keys)) + "</div>"
        cfg = {"div": f"fc_{uid}", "mode": ch["mode"], "type": ch["type"], "keys": keys,
               "colors": {k: _FIN_COLORS.get(k, "#2E75B6") for k in keys},
               "data": ch["data"], "period": ch.get("period", "annual"),
               "metric": keys[0] if keys else ""}
        cfg_json = _json.dumps(cfg, ensure_ascii=False)
        # miFinChart 는 페이지 하단 _JS 에서 정의되므로, 정의될 때까지 대기 후 호출
        cells.append(
            f'<section class="card finchart">'
            f'<div class="fc-head"><h3 class="card-title">{html.escape(ch["title"])}</h3>{period_btn}</div>'
            f'{metric_btn}<div id="fc_{uid}" class="fc-plot"></div>'
            f'<script>(function(){{var c={cfg_json};'
            f'function go(){{if(window.miFinChart){{miFinChart(c);}}else{{setTimeout(go,30);}}}}go();}})();'
            f'</script></section>')
    return f'<div class="card-row cols-3">{"".join(cells)}</div>'


def research_table_html(reports: list[dict], code: str = "") -> str:
    """애널리스트 리포트 표 — 제목 클릭 시 대시보드 내 팝업(PDF)으로 표시."""
    if not reports:
        return '<p class="empty">최근 리포트 없음</p>'
    head = "<tr><th>증권사</th><th>제목</th><th>투자의견</th><th>작성일</th></tr>"
    body = ""
    for r in reports:
        op = r.get("투자의견", "") or "-"
        opcls = ("op-buy" if any(k in op for k in ("매수", "Buy", "적극"))
                 else "op-sell" if ("매도" in op or "Sell" in op)
                 else "op-hold" if ("중립" in op or "보유" in op or "Hold" in op) else "")
        tit = html.escape(r.get("제목", ""))
        link = r.get("link", "")
        nid = str(r.get("nid", "")).strip()
        if nid:  # 제목 클릭 → 대시보드 내 모달(PDF). 폴백 href=네이버.
            titcell = (f'<a class="res-link" href="{html.escape(link)}" target="_blank" rel="noopener" '
                       f"onclick=\"return miOpenReport('{nid}', this.textContent, '{html.escape(code)}')\">"
                       f"{tit}</a>")
        elif link:
            titcell = f'<a class="res-link" href="{html.escape(link)}" target="_blank" rel="noopener">{tit}</a>'
        else:
            titcell = tit
        body += (f'<tr><td class="res-broker">{html.escape(r.get("증권사", ""))}</td>'
                 f'<td class="res-title">{titcell}</td>'
                 f'<td class="{opcls}">{html.escape(op)}</td>'
                 f'<td>{html.escape(r.get("작성일", ""))}</td></tr>')
    return (f'<div class="mi-table-wrap"><table class="mi-table res-table">'
            f'<thead>{head}</thead><tbody>{body}</tbody></table></div>')


def metric_header_html(title: str, kpis: list[dict], info: list[tuple]) -> str:
    """ETF 헤더와 동일한 UI(상단 KPI 박스 + 하단 정보 그리드)의 일반 카드.

    회사명/코드 헤더 없이 'title' 만 붙인다 — 투자지표 패널 등에 사용.
    """
    cmap = {"▲": "k-up", "▼": "k-down"}
    kpi_html = ""
    for k in kpis:
        unit = (f'<span class="k-unit">{html.escape(str(k.get("unit","")))}</span>'
                if k.get("unit") else "")
        vcls = cmap.get(k.get("val_dir"), "")
        scls = cmap.get(k.get("dir"), "")
        kpi_html += (f'<div class="eh-kpi"><div class="k-label">{html.escape(str(k["label"]))}</div>'
                     f'<div class="k-val {vcls}">{html.escape(str(k["value"]))}{unit}</div>'
                     f'<div class="k-sub {scls}">{html.escape(str(k.get("sub") or ""))}</div></div>')
    info_html = ""
    for label, val in info:
        v = "-" if val in (None, "", "-") else str(val)
        info_html += (f'<div class="ei"><span class="ei-l">{html.escape(str(label))}</span>'
                      f'<span class="ei-v">{html.escape(v)}</span></div>')
    info_block = (f'<div class="eh-info" style="margin-top:8px">{info_html}</div>'
                  if info_html else "")
    return (f'<section class="card etf-head" style="padding:20px 22px">'
            f'<h3 class="card-title">{html.escape(title)}</h3>'
            f'<div class="eh-kpis">{kpi_html}</div>{info_block}</section>')


def _style(fig: go.Figure, title: str) -> None:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#1F3864")),
        template="plotly_white",
        margin=dict(l=50, r=20, t=50, b=40),
        height=380,
        font=dict(family="-apple-system, 'Helvetica Neue', sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )


# ── 대시보드 구성 ──────────────────────────────────────────────
@dataclass
class Section:
    kind: str          # "html" | "table" | "figure" | "callout"
    title: str = ""
    html: str = ""


@dataclass
class Tab:
    label: str
    sections: list[Section] = field(default_factory=list)

    def add_markdown(self, md: str) -> "Tab":
        self.sections.append(Section("html", html=markdown_to_html(md)))
        return self

    def add_html(self, raw: str) -> "Tab":
        self.sections.append(Section("html", html=raw))
        return self

    def add_table(self, title: str, df: pd.DataFrame, max_rows: int | None = None,
                  search: bool = True, scroll_rows: int | None = None,
                  bold_first: bool = False) -> "Tab":
        self.sections.append(Section("table", title=title,
            html=df_to_table_html(df, max_rows, search, scroll_rows, bold_first)))
        return self

    def add_figure_grid(self, items: list[tuple], cols: int = 3, restyle: bool = True) -> "Tab":
        """(제목, figure) 목록을 각각 별도 카드로 가로 N열 그리드 배치.

        restyle=False 면 각 figure의 height/margin을 건드리지 않는다(인디케이터 등).
        """
        cells = []
        for title, fig in items:
            if restyle:
                fig.update_layout(height=300, margin=dict(l=46, r=16, t=14, b=34))
            div = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                              default_width="100%", config={"displaylogo": False, "responsive": True})
            cells.append(f'<section class="card fig-card">'
                         f'<h3 class="card-title">{html.escape(title)}</h3>{div}</section>')
        self.sections.append(Section("callout",
            html=f'<div class="card-row cols-{cols}">{"".join(cells)}</div>'))
        return self

    def add_grouped_table(self, title: str, df: pd.DataFrame, note: str = "") -> "Tab":
        body = (f'<p class="empty" style="color:#6b7689;font-size:13px;margin:0 0 8px">{html.escape(note)}</p>'
                if note else "") + grouped_table_html(df)
        self.sections.append(Section("table", title=title, html=body))
        return self

    def add_metrics(self, title: str, items: list[tuple]) -> "Tab":
        self.sections.append(Section("table", title=title, html=metric_cards_html(items)))
        return self

    def add_info_grid(self, title: str, items: list[tuple]) -> "Tab":
        self.sections.append(Section("table", title=title, html=info_grid_html(items)))
        return self

    def add_portfolio(self, title: str, items: list[dict]) -> "Tab":
        self.sections.append(Section("table", title=title, html=portfolio_html(items)))
        return self

    def add_html_raw_card(self, raw: str) -> "Tab":
        """카드 래핑 없이 원시 HTML(예: 현재가 히어로)을 그대로 삽입."""
        self.sections.append(Section("callout", html=raw))
        return self

    def add_figure(self, title: str, fig: go.Figure) -> "Tab":
        div = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                          default_width="100%", config={"displaylogo": False})
        self.sections.append(Section("figure", title=title, html=div))
        return self

    def add_candle_chart(self, title: str, df: pd.DataFrame, x: str, o: str,
                         h: str, l: str, c: str, ma_windows: tuple = (5, 20, 60, 120),
                         volume_col: str | None = None, volume_title: str = "거래량",
                         default: str = "1년") -> "Tab":
        """기간 토글(1주~전체)이 달린 캔들차트. volume_col 지정 시 거래량 차트도 함께 동기화.

        초기 표시 범위(default 기간)를 서버측에서 미리 적용해, JS 로딩 전에도
        최근 구간만 보이도록 한다(전체 5년 데이터가 화면을 잠식하는 문제 방지).
        """
        uid = uuid.uuid4().hex[:8]
        cdl_id = f"cdl_{uid}"

        def _num(v):
            n = pd.to_numeric(v, errors="coerce")
            return None if pd.isna(n) else float(n)

        dates = [str(v)[:10] for v in df[x].tolist()]
        highs = [_num(v) for v in df[h].tolist()]
        lows = [_num(v) for v in df[l].tolist()]
        has_vol = bool(volume_col) and volume_col in df.columns and df[volume_col].notna().any()
        vols = [_num(v) for v in df[volume_col].tolist()] if has_vol else []

        # ── 초기(default 기간) x축 범위·y축 맞춤을 서버측 계산
        init_xr = _init_xrange(dates, default)
        cdl_yr = vol_yr = None
        if init_xr:
            s_str, e_str = init_xr
            cy_lo, cy_hi, vy_max = float("inf"), float("-inf"), 0.0
            for i, dt in enumerate(dates):
                if s_str <= dt <= e_str:
                    if lows[i] is not None:
                        cy_lo = min(cy_lo, lows[i])
                    if highs[i] is not None:
                        cy_hi = max(cy_hi, highs[i])
                    if has_vol and vols[i] is not None:
                        vy_max = max(vy_max, vols[i])
            if cy_lo < cy_hi:
                pad = (cy_hi - cy_lo) * 0.08 or cy_hi * 0.05
                cdl_yr = [cy_lo - pad, cy_hi + pad]
            if vy_max > 0:
                vol_yr = [0, vy_max * 1.12]

        fig = candle_chart(df, x, o, h, l, c, ma_windows)
        if init_xr:
            fig.update_xaxes(range=list(init_xr))
            if cdl_yr:
                fig.update_yaxes(range=cdl_yr)
        cdl_div = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                              div_id=cdl_id, default_width="100%",
                              config={"displaylogo": False})

        vol_id, vol_div = "", ""
        if has_vol:
            vol_id = f"vol_{uid}"
            vfig = bar_chart(df.dropna(subset=[volume_col]), x, volume_col)
            vfig.update_layout(height=220)
            if init_xr:
                vfig.update_xaxes(range=list(init_xr))
                if vol_yr:
                    vfig.update_yaxes(range=vol_yr)
            vol_div = pio.to_html(vfig, include_plotlyjs=False, full_html=False,
                                  div_id=vol_id, default_width="100%",
                                  config={"displaylogo": False})

        toggle = _range_toggle_html(uid, cdl_id, vol_id, dates, highs, lows, vols, default)
        self.sections.append(Section("figure", title=title, html=cdl_div + toggle))
        if has_vol:
            self.sections.append(Section("figure", title=volume_title, html=vol_div))
        return self

    def add_fin_charts(self, charts: list[dict]) -> "Tab":
        """실적/안정성/재무 인터랙티브 차트 3개 가로 배치."""
        self.sections.append(Section("callout", html=fin_charts_html(charts)))
        return self

    def add_research_table(self, title: str, reports: list[dict], code: str = "") -> "Tab":
        """애널리스트 리포트 표(투자의견·팝업)."""
        self.sections.append(Section("table", title=title,
                                     html=research_table_html(reports, code)))
        return self

    def add_consensus_panel(self, title: str, recomm_mean, target, current,
                            create_date: str = "", dist: dict | None = None) -> "Tab":
        """애널리스트 투자의견 게이지(+분포) + 목표주가 패널 카드."""
        body = consensus_panel_html(recomm_mean, target, current, create_date, dist)
        if body:
            self.sections.append(Section("figure", title=title, html=body))
        return self

    def add_donut_breakdown(self, title: str, df: pd.DataFrame, names: str,
                            values: str, unit: str = "%", gray_labels=None,
                            center=None) -> "Tab":
        """좌측 도넛 + 우측 비중 리스트(자산비중 및 구성 스타일)."""
        self.sections.append(Section("figure", title=title,
            html=donut_breakdown_html(df, names, values, unit, gray_labels, center)))
        return self

    def add_investor_trend(self, title: str, rows: list[dict], visible: int = 8) -> "Tab":
        """투자자별 매매 동향(기호·색상 + 스크롤) 표."""
        self.sections.append(Section("table", title=title,
                                     html=investor_trend_html(rows, visible)))
        return self

    def add_callout(self, text: str, kind: str = "info") -> "Tab":
        self.sections.append(Section("callout", html=f'<div class="callout {kind}">{text}</div>'))
        return self


@dataclass
class Dashboard:
    title: str
    subtitle: str = ""
    tabs: list[Tab] = field(default_factory=list)
    kind: str = ""   # "etf" | "stock" — 통합 대시보드 탭 아이콘 판별용

    def add_tab(self, label: str) -> Tab:
        tab = Tab(label)
        self.tabs.append(tab)
        return tab

    def render(self, path) -> None:
        nav, panes = [], []
        for i, tab in enumerate(self.tabs):
            active = " active" if i == 0 else ""
            nav.append(f'<button class="tab-btn{active}" onclick="miTab({i})">'
                       f'{html.escape(tab.label)}</button>')
            blocks = []
            for s in tab.sections:
                if s.kind in ("table", "figure") and s.title:
                    blocks.append(f'<section class="card"><h3 class="card-title">'
                                  f'{html.escape(s.title)}</h3>{s.html}</section>')
                elif s.kind == "callout":
                    blocks.append(s.html)
                else:
                    blocks.append(f'<section class="card prose">{s.html}</section>')
            panes.append(f'<div class="pane{active}" id="pane{i}">{"".join(blocks)}</div>')

        plotly_js = get_plotlyjs()
        doc = _PAGE.format(
            title=html.escape(self.title),
            subtitle=html.escape(self.subtitle),
            kind=html.escape(self.kind),
            nav="".join(nav),
            panes="".join(panes),
            plotly_js=plotly_js,
            css=_CSS,
            js=_JS,
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)


_CSS = """
:root{--navy:#1F3864;--blue:#2E75B6;--bg:#f4f6fb;--card:#fff;--line:#e3e8f0;--text:#1a1a2e;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);
 font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','Apple SD Gothic Neo',sans-serif;}
header{background:linear-gradient(135deg,#eceff4,#dce2ec);color:#1F3864;padding:20px 28px;
 border-bottom:1px solid var(--line);}
header h1{margin:0;font-size:22px;font-weight:800;color:#15233f;display:flex;align-items:center;gap:10px;}
header .sub{margin-top:6px;font-size:13px;color:#6b7689;}
.hdr-refresh{border:0;background:transparent;color:#9aa3b2;border-radius:8px;
 width:30px;height:30px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
 padding:0;transition:background .15s,color .15s,transform .3s;flex:none;}
.hdr-refresh svg{width:17px;height:17px;display:block;}
.hdr-refresh:hover{background:rgba(31,56,100,.09);color:var(--navy);transform:rotate(180deg);}
nav{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);
 padding:0 16px;display:flex;gap:4px;overflow-x:auto;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.tab-btn{border:0;background:none;padding:14px 18px;font-size:14px;font-weight:600;color:#7a8499;
 cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;}
.tab-btn:hover{color:var(--blue);}
.tab-btn.active{color:var(--navy);border-bottom-color:var(--blue);}
.pane{display:none;padding:20px;max-width:1200px;margin:0 auto;}
.pane.active{display:block;}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 3px rgba(20,40,80,.04);}
.card-title{margin:0 0 12px;font-size:15px;color:var(--navy);font-weight:700;}
.range-toggle{display:flex;gap:4px;background:#f1f3f8;border-radius:12px;
 padding:6px;margin:14px auto 2px;max-width:760px;}
.range-toggle button{flex:1;border:1.5px solid transparent;background:none;
 padding:9px 6px;font-size:14px;font-weight:600;color:#7a8499;cursor:pointer;
 border-radius:9px;transition:all .12s;white-space:nowrap;}
.range-toggle button:hover{color:var(--blue);}
.range-toggle button.active{background:#fff;color:var(--blue);
 border-color:var(--blue);box-shadow:0 1px 3px rgba(20,40,80,.07);}
.prose h1{font-size:21px;color:var(--navy);border-bottom:2px solid var(--line);padding-bottom:8px;}
.prose h2{font-size:17px;color:var(--navy);margin-top:22px;}
.prose h3{font-size:14px;color:var(--blue);}
.prose p,.prose li{font-size:14px;line-height:1.75;}
.prose code{background:#eef2f9;padding:1px 5px;border-radius:4px;font-size:12px;}
.mi-search{width:240px;max-width:100%;padding:7px 10px;margin-bottom:10px;border:1px solid var(--line);
 border-radius:8px;font-size:13px;}
.mi-table-wrap{overflow-x:auto;}
table.mi-table{border-collapse:collapse;width:100%;font-size:14.5px;}
table.mi-table th{background:var(--navy);color:#fff;padding:11px 16px;text-align:right;
 cursor:pointer;white-space:nowrap;position:sticky;top:0;font-size:14px;}
table.mi-table th:first-child,table.mi-table td:first-child{text-align:left;}
table.mi-table td{padding:10px 16px;border-bottom:1px solid var(--line);text-align:right;
 white-space:nowrap;font-variant-numeric:tabular-nums;}
/* 숫자(값) 셀은 더 크고 또렷하게 */
table.mi-table td:not(:first-child){font-size:15px;font-weight:600;color:#15233f;}
table.mi-table tbody tr:nth-child(even){background:#f7faff;}
table.mi-table tbody tr:hover{background:#eef5ff;}
.empty{color:#9aa3b2;font-size:13px;padding:8px 0;}
/* 그룹(구분) 재무제표 — 자산/부채/자본 등 섹션 헤더 행 */
table.fin-table .sec-row td{background:#dde6f4;color:var(--navy);font-weight:800;
 font-size:14.5px;text-align:left;letter-spacing:.02em;padding:9px 16px;border-top:2px solid #c3d2ea;}
table.fin-table td.acct{text-align:left;color:#33415c;font-weight:500;font-size:14px;padding-left:26px;}
table.fin-table td.acct.total{font-weight:800;color:var(--navy);}
/* 지표 카드 그리드(밸류에이션) */
.metric-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;}
.metric-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;
 box-shadow:0 1px 3px rgba(20,40,80,.05);}
.metric-card .m-label{font-size:13px;color:#6b7689;font-weight:600;margin-bottom:6px;}
.metric-card .m-value{font-size:26px;font-weight:800;color:var(--navy);line-height:1.1;
 font-variant-numeric:tabular-nums;}
.metric-card .m-sub{font-size:11.5px;color:#9aa3b2;margin-top:6px;}
/* ETF 헤더(네이버 스타일) */
.etf-head{padding:22px 26px;}
.eh-top{display:flex;align-items:center;gap:8px;font-size:13px;color:#8a93a6;margin-bottom:8px;flex-wrap:wrap;}
.eh-code{font-weight:700;color:#6b7689;}
.eh-tag{background:#eef2f9;color:#5b6b86;border-radius:6px;padding:2px 9px;font-size:12px;font-weight:600;}
.eh-asof{margin-left:auto;}
.eh-name{margin:0 0 20px;font-size:30px;font-weight:800;color:#15233f;line-height:1.15;}
.eh-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:20px;}
.eh-kpi{background:#f5f7fb;border-radius:12px;padding:16px 18px;}
.eh-kpi .k-label{font-size:13px;color:#8a93a6;font-weight:600;margin-bottom:12px;}
.eh-kpi .k-val{font-size:27px;font-weight:800;color:#15233f;text-align:right;
 font-variant-numeric:tabular-nums;line-height:1;}
.eh-kpi .k-val.k-up{color:#c0392b;} .eh-kpi .k-val.k-down{color:#2e75b6;}
.eh-kpi .k-unit{font-size:15px;font-weight:600;color:#6b7689;margin-left:3px;}
.eh-kpi .k-sub{font-size:13.5px;font-weight:700;text-align:right;margin-top:9px;color:#8a93a6;min-height:1em;}
.eh-kpi .k-sub.k-up{color:#c0392b;} .eh-kpi .k-sub.k-down{color:#2e75b6;}
.eh-info{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:2px 30px;
 border-top:1px solid var(--line);padding-top:14px;}
.eh-info .ei{display:flex;gap:14px;font-size:14.5px;padding:9px 2px;border-bottom:1px solid #f0f3f8;}
.eh-info .ei-l{color:#8a93a6;min-width:90px;font-weight:600;}
.eh-info .ei-v{color:#1a2238;font-weight:700;overflow-wrap:anywhere;}
/* ETF 포트폴리오(구성종목) */
.pf-bar{display:flex;height:16px;border-radius:8px;overflow:hidden;margin:4px 0 16px;
 background:#e3e8f0;box-shadow:inset 0 0 0 1px rgba(0,0,0,.03);}
.pf-seg{height:100%;}
table.pf-table td.pf-name{text-align:left;font-weight:600;color:#1a2238;}
table.pf-table td.pf-name a.pf-link{color:#1a2238;text-decoration:none;}
table.pf-table td.pf-name a.pf-link:hover{color:var(--blue);text-decoration:underline;}
.pf-dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:9px;vertical-align:middle;}
table.pf-table td.pf-up{color:#c0392b;font-weight:700;}
table.pf-table td.pf-down{color:#2e75b6;font-weight:700;}
/* 정보 그리드(라벨·값이 가까운 큰 글씨) */
.info-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;}
.info-cell{background:#f7faff;border:1px solid var(--line);border-radius:10px;padding:11px 15px;}
.info-cell .ig-label{font-size:13px;color:#6b7689;font-weight:600;margin-bottom:4px;}
.info-cell .ig-value{font-size:18px;font-weight:700;color:var(--navy);
 overflow-wrap:anywhere;line-height:1.3;font-variant-numeric:tabular-nums;}
/* 현재가 히어로 */
.price-hero{border-radius:14px;padding:20px 26px;margin-bottom:18px;color:#fff;
 box-shadow:0 2px 8px rgba(20,40,80,.12);}
.price-hero.up{background:linear-gradient(135deg,#c0392b,#e85c4a);}
.price-hero.down{background:linear-gradient(135deg,#1f5fa8,#3a8ddd);}
.price-hero.flat{background:linear-gradient(135deg,#5b6b86,#8a97ad);}
.price-hero .ph-top{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:6px;}
.price-hero .ph-name{font-size:15px;font-weight:700;opacity:.92;}
.price-hero .ph-chg{font-size:18px;font-weight:800;opacity:.98;}
.price-hero .ph-price{font-size:44px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}
.price-hero .ph-meta{font-size:12px;opacity:.82;margin-top:8px;}
/* 실적/안정성/재무 인터랙티브 차트 */
.finchart .fc-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;}
.finchart .fc-head .card-title{margin:0;}
.fc-seg{display:inline-flex;background:#eef1f6;border-radius:8px;padding:3px;gap:2px;}
.fc-seg button{border:0;background:none;padding:5px 11px;font-size:12.5px;font-weight:700;color:#7a8499;
 cursor:pointer;border-radius:6px;white-space:nowrap;}
.fc-seg button.active{background:#fff;color:var(--navy);box-shadow:0 1px 2px rgba(20,40,80,.1);}
.fc-metric{margin:0 0 8px;}
.finchart .fc-plot{width:100%;height:300px;overflow:hidden;}
.finchart .fc-plot .plotly-graph-div{width:100%!important;}
/* 리포트 PDF 팝업 모달 */
.mi-modal{position:fixed;inset:0;background:rgba(20,30,55,.55);z-index:1000;
 display:none;align-items:center;justify-content:center;padding:28px;}
.mi-modal.show{display:flex;}
.mi-modal-box{position:relative;background:#fff;border-radius:14px;width:min(960px,96vw);height:min(90vh,1000px);
 display:flex;flex-direction:column;overflow:hidden;box-shadow:0 12px 48px rgba(0,0,0,.3);}
/* 리사이즈 핸들 (가장자리·모서리) — 중앙 고정 대칭 리사이즈 */
.mi-rs{position:absolute;z-index:5;}
.mi-rs-n{top:0;left:10px;right:10px;height:7px;cursor:ns-resize;}
.mi-rs-s{bottom:0;left:10px;right:10px;height:7px;cursor:ns-resize;}
.mi-rs-e{right:0;top:10px;bottom:10px;width:7px;cursor:ew-resize;}
.mi-rs-w{left:0;top:10px;bottom:10px;width:7px;cursor:ew-resize;}
.mi-rs-ne{top:0;right:0;width:14px;height:14px;cursor:nesw-resize;}
.mi-rs-sw{bottom:0;left:0;width:14px;height:14px;cursor:nesw-resize;}
.mi-rs-se{bottom:0;right:0;width:14px;height:14px;cursor:nwse-resize;}
.mi-rs-nw{top:0;left:0;width:14px;height:14px;cursor:nwse-resize;}
.mi-modal-head{display:flex;align-items:center;justify-content:space-between;gap:12px;
 padding:13px 18px;background:linear-gradient(135deg,#1F3864,#2E75B6);color:#fff;}
.mi-modal-title{font-size:15px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.mi-modal-actions{display:flex;align-items:center;gap:14px;flex:none;}
.mi-modal-ext{color:#dbe7f7;font-size:13px;font-weight:600;text-decoration:none;white-space:nowrap;}
.mi-modal-ext:hover{color:#fff;text-decoration:underline;}
.mi-modal-x{border:0;background:rgba(255,255,255,.15);color:#fff;width:30px;height:30px;
 border-radius:8px;font-size:20px;line-height:1;cursor:pointer;}
.mi-modal-x:hover{background:rgba(255,255,255,.3);}
.mi-modal-frame{flex:1;width:100%;border:0;background:#525659;}
/* 애널리스트 리포트 표 */
.res-table td.res-broker{text-align:left;font-weight:600;color:#33415c;}
.res-table td.res-title{text-align:left;font-weight:600;}
.res-table th:nth-child(2){text-align:center;}
.res-table a.res-link{color:#15233f;text-decoration:none;}
.res-table a.res-link:hover{color:var(--blue);text-decoration:underline;}
.res-table td.op-buy{color:#c0392b;font-weight:800;}
.res-table td.op-sell{color:#2e75b6;font-weight:800;}
.res-table td.op-hold{color:#a06a00;font-weight:800;}
/* 애널리스트 컨센서스 패널 (게이지 + 목표주가) */
.cons-wrap{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;align-items:center;}
@media(max-width:760px){.cons-wrap{grid-template-columns:1fr;}}
.cons-col{min-width:0;}
.cons-target{text-align:center;padding:8px 0;}
.cons-target .ct-label{font-size:14px;font-weight:700;color:var(--navy);margin-bottom:6px;}
.cons-target .ct-price{font-size:46px;font-weight:800;color:#15233f;line-height:1.05;
 font-variant-numeric:tabular-nums;letter-spacing:-.5px;}
.cons-target .ct-upside{font-size:21px;font-weight:800;margin-top:8px;}
.cons-target .ct-upside.up{color:#c0392b;} .cons-target .ct-upside.down{color:#2e75b6;}
.cons-target .ct-uplabel{font-size:12px;font-weight:600;color:#8a93a6;margin-left:6px;}
.cons-target .ct-sub{font-size:12px;color:#9aa3b2;margin-top:10px;}
.cons-dist{margin:2px 14px 4px;}
.cons-dist .cd-label{font-size:12px;color:#6b7689;font-weight:600;margin-bottom:5px;text-align:center;}
.cons-dist .cd-bar{display:flex;height:12px;border-radius:6px;overflow:hidden;background:#eef2f9;}
.cons-dist .cd-bar span{display:block;height:100%;}
.cons-dist .cd-leg{display:flex;gap:12px;justify-content:center;margin-top:6px;font-size:12.5px;font-weight:700;}
.cons-dist .cd-buy{color:#c0392b;} .cons-dist .cd-hold{color:#c08a1e;} .cons-dist .cd-sell{color:#2e75b6;}
/* 그래프 가로 N열 그리드 (각 카드 독립) */
.card-row{display:grid;gap:16px;margin-bottom:18px;}
.card-row.cols-3{grid-template-columns:repeat(3,minmax(0,1fr));}
.card-row.cols-2{grid-template-columns:repeat(2,minmax(0,1fr));}
@media(max-width:980px){.card-row.cols-3,.card-row.cols-2{grid-template-columns:1fr;}}
.card-row .fig-card{margin-bottom:0;}
/* 첫 열(항목명) 강조 표 */
table.mi-table.bold-first td:first-child{font-weight:800;color:#15233f;font-size:15px;}
/* 세로 스크롤 표 (헤더 고정) */
.tbl-scroll{overflow-y:auto;border:1px solid var(--line);border-radius:10px;}
.tbl-scroll table.mi-table th{position:sticky;top:0;z-index:3;}
/* 투자자별 매매 동향 — 스크롤 + 상승/하락 색상 */
.itr-wrap{overflow-y:auto;overflow-x:auto;border:1px solid var(--line);border-radius:10px;}
.itr-wrap table.mi-table{font-size:14px;}
.itr-wrap table.mi-table th{position:sticky;top:0;z-index:3;}
.itr-table td.t-date{text-align:left;color:#33415c;font-weight:700;}
.t-up{color:#c0392b;font-weight:700;}
.t-down{color:#2e75b6;font-weight:700;}
/* 도넛 + 우측 비중 리스트 (자산비중 및 구성) */
.donut-wrap{display:flex;gap:28px;align-items:center;flex-wrap:wrap;}
.donut-fig{flex:1 1 320px;min-width:280px;max-width:440px;}
.donut-list{flex:1 1 280px;min-width:250px;}
.donut-list .dl-head{font-size:14px;font-weight:700;color:var(--navy);
 border-bottom:1px solid var(--line);padding-bottom:9px;margin-bottom:4px;}
.dl-row{display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid #f0f3f8;font-size:14.5px;}
.dl-dot{width:12px;height:12px;border-radius:3px;flex:none;}
.dl-name{color:#33415c;font-weight:600;min-width:74px;}
.dl-bar{flex:1;height:8px;background:#eef2f9;border-radius:5px;overflow:hidden;min-width:40px;}
.dl-barfill{display:block;height:100%;border-radius:5px;}
.dl-val{margin-left:6px;font-weight:700;color:#15233f;font-variant-numeric:tabular-nums;min-width:58px;text-align:right;}
.callout{padding:14px 18px;border-radius:10px;margin-bottom:18px;font-size:14px;font-weight:600;}
.callout.win{background:#e7f4e4;border:1px solid #a8d49a;color:#2f5e1f;}
.callout.info{background:#e8f0fb;border:1px solid #a9c7ec;color:#1f3864;}
.callout.warn{background:#fdeeee;border:1px solid #e7b3b3;color:#8a1f1f;}
footer{text-align:center;color:#9aa3b2;font-size:12px;padding:24px;}
"""

_JS = """
function miTab(i){
 document.querySelectorAll('.tab-btn').forEach((b,j)=>b.classList.toggle('active',j===i));
 document.querySelectorAll('.pane').forEach((p,j)=>p.classList.toggle('active',j===i));
 window.dispatchEvent(new Event('resize'));
}
function miFilter(id,q){
 q=q.toLowerCase();
 document.querySelectorAll('#'+id+' tbody tr').forEach(tr=>{
  tr.style.display = tr.innerText.toLowerCase().includes(q)?'':'none';
 });
}
function miNum(s){var n=parseFloat(String(s).replace(/[, %]/g,''));return isNaN(n)?null:n;}
function miSort(id,col){
 var t=document.getElementById(id),tb=t.tBodies[0];
 var rows=Array.from(tb.rows);
 var dir=t.getAttribute('data-sc')==col+'a'?'d':'a';
 rows.sort(function(x,y){
  var a=x.cells[col].innerText,b=y.cells[col].innerText;
  var na=miNum(a),nb=miNum(b);
  if(na!==null&&nb!==null)return dir=='a'?na-nb:nb-na;
  return dir=='a'?a.localeCompare(b,'ko'):b.localeCompare(a,'ko');
 });
 rows.forEach(r=>tb.appendChild(r));
 t.setAttribute('data-sc',col+(dir=='a'?'a':'d'));
}
// 실적/안정성/재무 인터랙티브 차트 (연간·분기 토글 + 지표 토글)
function miFinChart(cfg){
 var el=document.getElementById(cfg.div); if(!el||!window.Plotly){setTimeout(function(){miFinChart(cfg);},120);return;}
 var card=el.closest('.finchart'); var state={p:cfg.period,m:cfg.metric};
 function mk(k,d){var color=(cfg.colors&&cfg.colors[k])||'#2E75B6';
  if(cfg.type==='line') return {type:'scatter',mode:'lines+markers',name:k,x:d.periods,y:d.series[k],
    line:{color:color,width:2.6},marker:{size:7},connectgaps:true};
  return {type:'bar',name:k,x:d.periods,y:d.series[k],marker:{color:color}};}
 function draw(){
  // 숨겨진(0폭) 상태에서 그리면 레이아웃이 깨져 넘침 → 보일 때만 렌더
  if(el.offsetParent===null||!el.clientWidth){return;}
  var d=cfg.data[state.p]; if(!d)return; var traces=[];
  if(cfg.mode==='group'){cfg.keys.forEach(function(k){if(d.series[k])traces.push(mk(k,d));});}
  else{traces.push(mk(state.m,d));}
  var lay={template:'plotly_white',height:300,autosize:true,margin:{l:52,r:14,t:8,b:34},barmode:'group',
   showlegend:cfg.mode==='group',legend:{orientation:'h',y:1.12,x:0,font:{size:11}},
   xaxis:{type:'category',tickfont:{size:11}},yaxis:{tickfont:{size:11},separatethousands:true}};
  Plotly.react(cfg.div,traces,lay,{displaylogo:false,responsive:true});}
 if(card){
  card.querySelectorAll('.fc-period button').forEach(function(b){b.addEventListener('click',function(){
    state.p=b.dataset.p; card.querySelectorAll('.fc-period button').forEach(function(x){x.classList.toggle('active',x===b);}); draw();});});
  card.querySelectorAll('.fc-metric button').forEach(function(b){b.addEventListener('click',function(){
    state.m=b.dataset.m; card.querySelectorAll('.fc-metric button').forEach(function(x){x.classList.toggle('active',x===b);}); draw();});});
 }
 draw();
 // 숨겨진 탭(display:none)에서 0폭으로 그려져 비는 문제 방지: 보일 때마다 다시 그림
 if('IntersectionObserver' in window){
  var io=new IntersectionObserver(function(es){for(var i=0;i<es.length;i++){if(es[i].isIntersecting){draw();}}},{threshold:0.01});
  io.observe(el);
 }
}
// 애널리스트 리포트 제목 클릭 → 대시보드 내 팝업(PDF) 표시
function miOpenReport(nid,title,code){
 var m=document.getElementById('mi-modal'); if(!m)return true;
 document.getElementById('mi-modal-title').textContent=title||'리포트';
 document.getElementById('mi-modal-frame').src='/report_pdf?nid='+encodeURIComponent(nid)+'&code='+encodeURIComponent(code||'');
 var ext=document.getElementById('mi-modal-ext');
 ext.href='https://stock.naver.com/domestic/stock/'+(code||'')+'/research/'+nid;
 m.classList.add('show'); document.body.style.overflow='hidden';
 return false;
}
function miCloseReport(){
 var m=document.getElementById('mi-modal'); if(!m)return;
 m.classList.remove('show'); document.getElementById('mi-modal-frame').src=''; document.body.style.overflow='';
}
document.addEventListener('keydown',function(e){if(e.key==='Escape')miCloseReport();});
// 모달 리사이즈 (가장자리 드래그) — flex 중앙정렬이라 크기만 바꾸면 위치는 중앙 고정
(function(){
 var box,dir,sx,sy,sw,sh,fr;
 function mv(e){var dx=e.clientX-sx,dy=e.clientY-sy,w=sw,h=sh;
  if(dir.indexOf('e')>=0)w=sw+dx*2; if(dir.indexOf('w')>=0)w=sw-dx*2;
  if(dir.indexOf('s')>=0)h=sh+dy*2; if(dir.indexOf('n')>=0)h=sh-dy*2;
  w=Math.max(380,Math.min(window.innerWidth-32,w));
  h=Math.max(320,Math.min(window.innerHeight-32,h));
  box.style.width=w+'px'; box.style.height=h+'px';}
 function up(){document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',up);
  document.body.style.userSelect=''; if(fr)fr.style.pointerEvents='';}
 document.addEventListener('mousedown',function(e){var hd=e.target.closest('.mi-rs'); if(!hd)return;
  box=hd.closest('.mi-modal-box'); if(!box)return; dir=hd.dataset.d;
  var r=box.getBoundingClientRect(); sw=r.width; sh=r.height; sx=e.clientX; sy=e.clientY;
  fr=box.querySelector('iframe'); if(fr)fr.style.pointerEvents='none';
  document.body.style.userSelect='none'; e.preventDefault();
  document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);});
})();
// 구성종목 클릭 → 통합 대시보드(부모)에서 개별종목 리포트를 새 탭으로 열기.
// 부모에 탭 시스템이 없으면(단독 실행) href(네이버 증권)로 폴백.
function miOpenStock(ev,code){
 try{
  if(window.parent&&window.parent!==window&&window.parent.MI_TABS&&window.parent.miOpenStockTab){
   window.parent.miOpenStockTab(code);
   if(ev)ev.preventDefault();
   return false;
  }
 }catch(e){}
 return true;
}
"""

_PAGE = """<!DOCTYPE html>
<html lang="ko" data-kind="{kind}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
<script>{plotly_js}</script>
</head><body>
<header><h1>{title}<button class="hdr-refresh" onclick="location.reload()" title="새로고침 — 최신 데이터로 다시 조회"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg></button></h1><div class="sub">{subtitle}</div></header>
<nav>{nav}</nav>
{panes}
<footer>Generated by market_intel · 한국 증시 종합 인텔리전스 툴</footer>
<div id="mi-modal" class="mi-modal" onclick="if(event.target===this)miCloseReport()">
  <div class="mi-modal-box">
    <div class="mi-modal-head">
      <span id="mi-modal-title" class="mi-modal-title">리포트</span>
      <span class="mi-modal-actions">
        <a id="mi-modal-ext" href="#" target="_blank" rel="noopener" class="mi-modal-ext">네이버에서 열기 ↗</a>
        <button class="mi-modal-x" onclick="miCloseReport()" title="닫기">&times;</button>
      </span>
    </div>
    <iframe id="mi-modal-frame" class="mi-modal-frame" title="애널리스트 리포트"></iframe>
    <div class="mi-rs mi-rs-n" data-d="n"></div><div class="mi-rs mi-rs-s" data-d="s"></div>
    <div class="mi-rs mi-rs-e" data-d="e"></div><div class="mi-rs mi-rs-w" data-d="w"></div>
    <div class="mi-rs mi-rs-ne" data-d="ne"></div><div class="mi-rs mi-rs-nw" data-d="nw"></div>
    <div class="mi-rs mi-rs-se" data-d="se"></div><div class="mi-rs mi-rs-sw" data-d="sw"></div>
  </div>
</div>
<script>{js}</script>
</body></html>
"""
