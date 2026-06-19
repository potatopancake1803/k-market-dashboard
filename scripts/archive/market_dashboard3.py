# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "flask>=3.0",
#   "httpx>=0.27",
#   "polars>=1.0",
#   "pandas>=2.0",
#   "numpy>=1.26",
#   "pyarrow>=15.0",
#   "lxml>=5.0",
#   "plotly>=5.20",
#   "python-dotenv>=1.0",
#   "scipy>=1.11",
# ]
# ///
"""K-Market Dashboard 2 — M4 Pro Accelerated · Pro Quant Edition (market_dashboard2.py).

Claude_M4_Market_dashboard.py 를 계승·확장한 버전.

  uv run market_dashboard2.py
    → http://127.0.0.1:8770/

이 버전에서 추가/강화된 것
  ① 리포트 기본 탭(주식 종목개요·재무제표, ETF 개요)에도 3D 카드 틸트·등장
     애니메이션·숫자 카운트업·헤더 패럴럭스 FX 레이어를 주입.
  ② 주식 M4 퀀트 탭에 증권가 현업 전문 툴 추가:
     리스크 지표(Sharpe/Sortino/VaR/CVaR), 3D 변동성 표면(Volatility Surface),
     수익률 분포·팻테일(왜도/첨도), CAPM 베타/알파(vs KODEX 200).
  ③ ETF M4 퀀트 탭에 전문 툴 추가:
     리스크·집중도 지표(HHI/유효종목수/평균상관), 롤링 변동성,
     3D 편입종목 상관관계 행렬(분산효과).
  ④ 전반 UI/UX 고도화 — 다크 콕핏, 3D 자동회전, 실시간 진행률(SSE), 카운트업,
     카드 등장/틸트, 캐싱(SSD parquet + RAM + 프리워밍).

M4 Pro(12-core CPU · 16-core GPU · 24GB · 512GB SSD) 활용
  · 벡터화 NumPy(Apple Accelerate BLAS 멀티스레드) 몬테카를로/롤링 통계
  · asyncio 병렬 I/O로 시장지수·편입종목 시계열 동시 수집
  · Plotly Surface/Scatter3d 의 WebGL GPU 렌더링 + 자동회전 카메라
  · SSD parquet 캐시 + RAM 결과 캐시로 재조회 즉시 응답
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from datetime import date
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from flask import Flask, Response, jsonify, request

from archive import company_report_ver2 as company
from archive import etf_dashboard_ver2 as etf


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from market_intel.analyze import etf as E
from market_intel.collectors import dart as dart_c
from market_intel.collectors import naver
from market_intel.httpx_client import Fetcher

PORT = int(os.environ.get("MARKET_PORT", "8780"))
app = Flask(__name__)

MARKET_PROXY = "069500"   # KODEX 200 — CAPM/베타 시장 대용치

# 색상
C_UP = "#c0392b"
C_DOWN = "#2e75b6"
C_NAVY = "#1F3864"
C_INK = "#cdd6f4"
C_VIOLET = "#9b6bff"
C_CYAN = "#36c6ff"
C_GREEN = "#7dfac0"


# ════════════════ 캐싱 (SSD + RAM) ════════════════
_CACHE_DIR = Path.home() / ".cache" / "kmkt_m4"


def _cpath(code: str, days: int) -> Path:
    return _CACHE_DIR / f"chart_{code}_{days}.parquet"


def _fresh_today(p: Path) -> bool:
    try:
        return p.exists() and date.fromtimestamp(p.stat().st_mtime) == date.today()
    except Exception:  # noqa: BLE001
        return False


def _disk_read(code: str, days: int) -> list[dict] | None:
    p = _cpath(code, days)
    if _fresh_today(p):
        try:
            return pd.read_parquet(p).to_dict("records")
        except Exception:  # noqa: BLE001
            return None
    return None


def _disk_write(code: str, days: int, rows: list[dict]) -> None:
    if not rows:
        return
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(_cpath(code, days))
    except Exception:  # noqa: BLE001
        pass


async def _achart(f: Fetcher, code: str, days: int) -> list[dict]:
    rows = _disk_read(code, days)
    if rows is not None:
        return rows
    rows = await naver.fetch_price_chart(f, code, days=days)
    _disk_write(code, days, rows)
    return rows


async def _afetch(code: str, days: int) -> list[dict]:
    # parquet 캐시 히트 시 Fetcher(=httpx.AsyncClient) 생성 생략
    cached = _disk_read(code, days)
    if cached is not None:
        return cached
    async with Fetcher() as f:
        return await _achart(f, code, days)


async def _afetch_multi(*args: tuple[str, int]) -> list[list[dict]]:
    """여러 (code, days) 쌍을 Fetcher 1개로 병렬 수집."""
    # 캐시 히트 항목은 네트워크 없이 즉시 반환
    need_fetch = [(i, c, d) for i, (c, d) in enumerate(args) if _disk_read(c, d) is None]
    results: list[list[dict] | None] = [_disk_read(c, d) for c, d in args]
    if need_fetch:
        async with Fetcher() as f:
            fetched = await asyncio.gather(*[_achart(f, c, d) for _, c, d in need_fetch])
            for (i, _, _), rows in zip(need_fetch, fetched):
                results[i] = rows
    return [r or [] for r in results]


async def _fetch_etf_bundle(code: str):
    async with Fetcher() as f:
        chart, an = await asyncio.gather(
            _achart(f, code, 3600),
            naver.fetch_etf_analysis(f, code))
        codes = [str(it.get("종목코드")) for it in (an.get("top10") or [])
                 if str(it.get("종목코드") or "").isdigit() and len(str(it.get("종목코드"))) == 6]
        cons = await asyncio.gather(*[_achart(f, cc, 320) for cc in codes]) if codes else []
        return chart, an, codes, cons


_RESULT: dict[tuple, tuple[str, float]] = {}
_RLOCK = threading.Lock()
_RESULT_TTL = 1800.0


def _rget(key: tuple) -> str | None:
    with _RLOCK:
        v = _RESULT.get(key)
        if v and (time.time() - v[1]) < _RESULT_TTL:
            return v[0]
    return None


def _rput(key: tuple, html: str) -> None:
    with _RLOCK:
        _RESULT[key] = (html, time.time())


# ════════════════ 주식 / ETF 판별 · 코드 해석 ════════════════
def _get_etf_snap():
    """get_market() 결과를 호출부에서 공유하기 위한 헬퍼."""
    try:
        _df, snap, _ld = etf.get_market()
        return snap
    except Exception:  # noqa: BLE001
        return None


def detect_type(query: str, snap=None) -> str:
    q = query.strip()
    if snap is None:
        snap = _get_etf_snap()
    etf_codes = (set(snap["코드"].astype(str)) if (snap is not None and not snap.empty) else set())
    if q.isdigit() and len(q) == 6:
        return "etf" if q in etf_codes else "stock"
    if snap is not None and not snap.empty and (snap["종목명"].astype(str).str.strip() == q).any():
        return "etf"
    try:
        corps = company.get_corps()
        if any(c.get("corp_name") == q and c.get("stock_code") for c in corps):
            return "stock"
    except Exception:  # noqa: BLE001
        pass
    if snap is not None and not snap.empty:
        try:
            if E.find_etf(snap, q) is not None:
                return "etf"
        except Exception:  # noqa: BLE001
            pass
    return "stock"


def _resolve_stock_code(q: str) -> str | None:
    q = q.strip()
    if q.isdigit() and len(q) == 6:
        return q
    try:
        for c in dart_c.search_corp(q, company.get_corps()):
            if c.get("stock_code"):
                return str(c["stock_code"])
    except Exception:  # noqa: BLE001
        pass
    return None


def _resolve_etf_code(q: str, snap=None) -> str | None:
    try:
        if snap is None:
            snap = _get_etf_snap()
        row = E.find_etf(snap, q)
        if row is not None:
            return str(row["코드"])
    except Exception:  # noqa: BLE001
        pass
    return None


# ════════════════ 공용 분석 헬퍼 ════════════════
def _clean_closes(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    df = pd.DataFrame(rows)
    if df.empty or "종가" not in df.columns:
        return np.array([]), np.array([])
    df["일자"] = pd.to_datetime(df["일자"], errors="coerce")
    df = df.dropna(subset=["일자"]).sort_values("일자")
    cl = pd.to_numeric(df["종가"].astype(str).str.replace(",", ""), errors="coerce").ffill().bfill()
    mask = cl.notna() & (cl > 0)
    return df["일자"].values[mask.values], cl.values[mask.values].astype(float)


def _risk_stats(closes: np.ndarray) -> dict:
    logr = np.diff(np.log(closes))
    logr = logr[np.isfinite(logr)]
    mu, sd = float(logr.mean()), float(logr.std())
    if not np.isfinite(sd) or sd <= 0:
        sd = 1e-6
    ann_ret = (np.exp(mu * 252) - 1) * 100
    ann_vol = sd * np.sqrt(252) * 100
    sharpe = mu / sd * np.sqrt(252)
    dn = logr[logr < 0]
    dsd = float(dn.std()) if dn.size > 1 else sd
    sortino = mu / (dsd if dsd > 0 else sd) * np.sqrt(252)
    peak = np.maximum.accumulate(closes)
    mdd = float((closes / peak - 1).min() * 100)
    q5 = float(np.percentile(logr, 5))
    var95 = q5 * 100
    tail = logr[logr <= q5]
    cvar95 = float(tail.mean() * 100) if tail.size else var95
    return dict(logr=logr, mu=mu, sd=sd, ann_ret=ann_ret, ann_vol=ann_vol,
                sharpe=sharpe, sortino=sortino, mdd=mdd, var95=var95, cvar95=cvar95)


# ════════════════ Plotly 다크 레이아웃 ════════════════
_FONT = "-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif"
_PLOT_CFG = {"displayModeBar": False, "responsive": True}


def _layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, size=12, color=C_INK),
        margin=dict(l=52, r=30, t=22, b=44),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1))
    fig.update_xaxes(gridcolor="rgba(160,180,255,.10)", zerolinecolor="rgba(160,180,255,.20)")
    fig.update_yaxes(gridcolor="rgba(160,180,255,.10)", zerolinecolor="rgba(160,180,255,.20)")
    return fig


def _scene3d(fig: go.Figure, height: int, scene: dict) -> go.Figure:
    ax = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(160,180,255,.14)",
              showbackground=True, zerolinecolor="rgba(160,180,255,.25)")
    sc = {}
    for k, v in scene.items():
        if k in ("xaxis", "yaxis", "zaxis") and isinstance(v, dict):
            sc[k] = {**ax, **v}
        else:
            sc[k] = v
            
    fig.update_layout(template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=_FONT, size=11, color=C_INK),
                      margin=dict(l=0, r=0, t=8, b=0), scene=sc)
    return fig


def _card(title: str, inner_html: str, cls: str = "") -> str:
    return f'<section class="card {cls}"><h3 class="card-title">{title}</h3>{inner_html}</section>'


def _frag(fig: go.Figure, title: str, cls: str = "") -> str:
    return _card(title, fig.to_html(full_html=False, include_plotlyjs=False, config=_PLOT_CFG), cls)


def _frag3d(fig: go.Figure, title: str) -> str:
    return _card(title, fig.to_html(full_html=False, include_plotlyjs=False, config=_PLOT_CFG),
                 "m4-card-3d")


def _cu(v, dec: int = 0, sign: bool = False) -> str:
    return (f'<b class="cu" data-to="{float(v):.6f}" data-dec="{dec}" '
            f'data-sign="{1 if sign else 0}">0</b>')


def _metric_grid(items: list[tuple]) -> str:
    cells = "".join(
        f'<div class="m4-met"><div class="m4-met-l">{l}</div>'
        f'<div class="m4-met-v">{v}</div><div class="m4-met-s">{s}</div></div>'
        for l, v, s in items)
    return f'<div class="m4-met-grid">{cells}</div>'


# ════════════════ M4 탭 스타일 (다크 콕핏) ════════════════
_M4_STYLE = """<style id="m4-style">
.pane.active{animation:m4PaneIn .34s cubic-bezier(.22,.61,.36,1);}
@keyframes m4PaneIn{from{opacity:0;}to{opacity:1;}}
.tab-btn{transition:color .18s,border-color .18s,background .18s;}
.tab-btn.m4-tab-btn{position:relative;color:#7a3df0;font-weight:700;}
.tab-btn.m4-tab-btn:hover{color:#5b1fd0;background:rgba(123,61,240,.06);}
.tab-btn.m4-tab-btn.active{color:#5b1fd0;border-bottom-color:#7a3df0;}

.m4-wrap{display:flex;flex-direction:column;gap:16px;color:#dfe6ff;
 background:radial-gradient(1200px 520px at 18% -12%,#1b2350,#0b0f20 62%);
 border:1px solid #232c54;border-radius:20px;padding:18px;
 box-shadow:0 24px 70px rgba(5,8,22,.45);overflow:hidden;}
.m4-wrap .m4-hero{background:linear-gradient(120deg,#231a5e,#3a1d6e,#16407a);
 background-size:240% 240%;animation:m4grad 12s ease infinite;color:#fff;
 border:1px solid rgba(155,107,255,.3);border-radius:16px;padding:20px 24px;
 box-shadow:inset 0 0 40px rgba(120,90,255,.15);}
@keyframes m4grad{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.m4-wrap .m4-hero h2{margin:8px 0 6px;font-size:21px;font-weight:800;}
.m4-wrap .m4-hero p{margin:0;font-size:13.5px;line-height:1.6;opacity:.92;}
.m4-chip{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:700;
 background:rgba(255,255,255,.12);border:1px solid rgba(155,107,255,.45);
 padding:5px 12px;border-radius:999px;letter-spacing:.02em;box-shadow:0 0 18px rgba(155,107,255,.35);}
.m4-grid{display:flex;flex-direction:column;gap:16px;}
.m4-wrap .card{background:rgba(255,255,255,.035);border:1px solid rgba(120,140,255,.16);
 border-radius:14px;box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 10px 30px rgba(5,8,22,.35);
 backdrop-filter:blur(6px);transition:transform .2s ease,box-shadow .2s ease;will-change:transform;}
.m4-wrap .card:hover{box-shadow:0 14px 40px rgba(40,30,90,.5),0 0 0 1px rgba(155,107,255,.25);}
.m4-wrap .card-title{color:#e8ecff;border-left:3px solid #9b6bff;padding-left:10px;
 text-shadow:0 0 12px rgba(155,107,255,.25);}
.m4-note{background:rgba(123,61,240,.13);border-left:3px solid #9b6bff;border-radius:8px;
 padding:14px 18px;color:#d9d2ff;font-size:13.5px;line-height:1.65;}
.m4-note b{color:#c8b4ff;font-variant-numeric:tabular-nums;}
.m4-note .cu{color:#7dfac0;}

/* 리스크 지표 타일 그리드 */
.m4-met-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;}
.m4-met{background:rgba(255,255,255,.045);border:1px solid rgba(120,140,255,.16);border-radius:12px;
 padding:14px 16px;transition:transform .18s ease,box-shadow .18s ease;}
.m4-met:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(40,30,90,.45);
 border-color:rgba(155,107,255,.4);}
.m4-met-l{font-size:12px;color:#9fb0e8;font-weight:600;}
.m4-met-v{font-size:23px;font-weight:800;color:#e8ecff;margin:5px 0 2px;
 font-variant-numeric:tabular-nums;}
.m4-met-v .cu{color:#7dfac0;}
.m4-met-s{font-size:11px;color:#8f9cd0;}

.m4-stage{min-height:460px;}
.m4-loader{min-height:460px;display:flex;flex-direction:column;align-items:center;
 justify-content:center;gap:14px;background:rgba(255,255,255,.03);
 border:1px solid rgba(120,140,255,.16);border-radius:16px;padding:40px;text-align:center;}
.m4-loader h3{margin:0;color:#e8ecff;font-size:18px;}
.m4-loader p{margin:0;color:#9fb0e8;font-size:13px;line-height:1.6;max-width:560px;}
.m4-orb{width:58px;height:58px;border-radius:50%;position:relative;
 background:conic-gradient(from 0deg,#9b6bff,#36c6ff,#c0392b,#9b6bff);
 animation:m4spin 1.1s linear infinite;filter:drop-shadow(0 0 12px rgba(155,107,255,.5));
 -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 7px),#000 0);
         mask:radial-gradient(farthest-side,transparent calc(100% - 7px),#000 0);}
@keyframes m4spin{to{transform:rotate(360deg);}}
.m4-prog{width:min(460px,84%);height:9px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden;}
.m4-prog-fill{height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,#9b6bff,#36c6ff);
 transition:width .45s cubic-bezier(.22,.61,.36,1);box-shadow:0 0 14px rgba(123,61,240,.7);}
.m4-prog-row{display:flex;justify-content:space-between;align-items:center;width:min(460px,84%);
 font-size:12px;color:#9fb0e8;font-weight:600;font-variant-numeric:tabular-nums;}
@media (prefers-reduced-motion:reduce){.pane.active,.m4-hero,.m4-orb{animation:none!important;}}
</style>"""


def _lazy_pane(kind: str, code: str) -> str:
    api = "/api/quant/" + ("etf" if kind == "etf" else "stock")
    cid = "m4q-" + code
    if kind == "etf":
        desc = ("전 기간 시계열로 리스크·집중도 지표, 계절성, 언더워터, 롤링 변동성, 적립식 "
                "백테스트를 계산하고, 편입 상위 종목을 비동기 병렬 수집해 상관관계 행렬과 "
                "리스크-리턴 지형을 3D로 렌더링합니다.")
        loadtxt = "리스크 지표 · 백테스트 · 편입종목 병렬 수집 · 3D 상관/지형"
    else:
        desc = ("리스크 지표(Sharpe·VaR·CVaR), 몬테카를로 적정주가, 3D 변동성 표면, "
                "수익률 분포·팻테일, CAPM 베타/알파, 프랙탈 패턴 매칭을 한 번에 계산합니다.")
        loadtxt = "리스크 지표 · 몬테카를로 · 3D 변동성 표면 · CAPM · 프랙탈"
    tmpl = """
<div class="m4-wrap">
  <div class="m4-hero">
    <span class="m4-chip">🚀 Apple M4 Pro · On-device Quant Desk</span>
    <h2>로컬 코프로세서 정밀 분석</h2>
    <p>__DESC__</p>
  </div>
  <div id="__CID__" class="m4-stage">
    <div class="m4-loader">
      <div class="m4-orb"></div>
      <h3>M4 Pro 연산 대기 중…</h3>
      <div class="m4-prog"><div class="m4-prog-fill" id="__CID__-bar"></div></div>
      <div class="m4-prog-row"><span id="__CID__-lbl">탭을 열면 연산을 시작합니다</span>
        <span id="__CID__-pct">0%</span></div>
      <p>__LOADTXT__</p>
    </div>
  </div>
</div>
<script>
(function(){
 var loaded=false;
 function exec(c){Array.prototype.forEach.call(c.querySelectorAll('script'),function(o){
   var s=document.createElement('script');
   Array.prototype.forEach.call(o.attributes,function(a){s.setAttribute(a.name,a.value);});
   s.appendChild(document.createTextNode(o.innerHTML));o.parentNode.replaceChild(s,o);});}
 function load(){
   if(loaded)return; loaded=true;
   var c=document.getElementById('__CID__'),bar=document.getElementById('__CID__-bar'),
       lbl=document.getElementById('__CID__-lbl'),pct=document.getElementById('__CID__-pct');
   var es=new EventSource('__API__?code=__CODE__');
   es.addEventListener('progress',function(e){try{var d=JSON.parse(e.data);
     if(bar)bar.style.width=d.pct+'%';if(pct)pct.textContent=d.pct+'%';if(lbl)lbl.textContent=d.label;}catch(x){}});
   es.addEventListener('done',function(e){es.close();
     try{var d=JSON.parse(e.data);if(bar)bar.style.width='100%';if(pct)pct.textContent='100%';
       setTimeout(function(){c.classList.remove('m4-stage');c.innerHTML=d.html;exec(c);
         setTimeout(function(){window.dispatchEvent(new Event('resize'));},90);},200);
     }catch(x){c.innerHTML='<div class="m4-note">결과 파싱 실패: '+x+'</div>';}});
   es.addEventListener('failed',function(e){es.close();try{var d=JSON.parse(e.data);
     c.innerHTML='<div class="m4-note" style="border-color:#c0392b;color:#ffb4b4"><b>⚠️ 연산 실패</b>'+
       '<br><pre style="white-space:pre-wrap;font-size:11px;margin:8px 0 0">'+d.msg+'</pre></div>';}catch(x){}});
   es.onerror=function(){};
 }
 var btn=document.getElementById('m4-tab-btn');
 if(btn)btn.addEventListener('click',function(){setTimeout(load,60);});
})();
</script>"""
    return (tmpl.replace("__CID__", cid).replace("__API__", api).replace("__CODE__", code)
            .replace("__DESC__", desc).replace("__LOADTXT__", loadtxt))


def _inject_m4_tab(html_doc: str, kind: str, code: str | None) -> str:
    if not code or "</nav>" not in html_doc or "<footer" not in html_doc:
        return html_doc
    n = html_doc.count('class="tab-btn')
    btn = (f'<button class="tab-btn m4-tab-btn" id="m4-tab-btn" '
           f'onclick="miTab({n})">🚀 M4 퀀트 분석</button>')
    html_doc = html_doc.replace("</nav>", btn + "</nav>", 1)
    pane = f'<div class="pane" id="pane{n}">{_lazy_pane(kind, code)}</div>'
    html_doc = html_doc.replace("<footer", pane + "<footer", 1)
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _M4_STYLE + "</head>", 1)
    return html_doc


# ════════════════ 기본 리포트 탭 FX 레이어 (작업1·4) ════════════════
_FX_STYLE = """<style id="m4-fx">
.pane .card{transition:box-shadow .22s ease,transform .18s ease;will-change:transform;}
.pane .card:hover{box-shadow:0 16px 40px rgba(31,56,100,.16);}
header{perspective:900px;}
header h1{transition:transform .2s ease;transform-style:preserve-3d;}
nav .tab-btn{transition:color .16s,border-color .16s,background .16s,transform .16s;}
nav .tab-btn:hover{transform:translateY(-1px);}
@media (prefers-reduced-motion:reduce){.pane .card,header h1{transition:none!important;transform:none!important;}}
</style>"""

_FX_JS = """<script>
(function(){
 var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 function animNum(el){
   if(el.__cu)return; var txt=el.textContent; var m=txt.match(/-?\\d[\\d,]*(\\.\\d+)?/);
   if(!m){el.__cu=1;return;} el.__cu=1;
   var numStr=m[0],target=parseFloat(numStr.replace(/,/g,'')); if(!isFinite(target))return;
   if(RM)return;
   var dec=(numStr.split('.')[1]||'').length,hasC=numStr.indexOf(',')>=0;
   var pre=txt.slice(0,m.index),suf=txt.slice(m.index+numStr.length),t0=null;
   function fmt(v){var s=hasC?v.toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec}):v.toFixed(dec);return pre+s+suf;}
   function step(t){if(!t0)t0=t;var k=Math.min((t-t0)/850,1),e=1-Math.pow(1-k,3);
     el.textContent=fmt(target*e);if(k<1)requestAnimationFrame(step);else el.textContent=txt;}
   requestAnimationFrame(step);
 }
 function isChart(c){return !!c.querySelector('.plotly-graph-div,.fc-plot,.donut-fig,svg.main-svg');}
 var io=new IntersectionObserver(function(es){es.forEach(function(en){
   if(!en.isIntersecting)return; var c=en.target; io.unobserve(c);
   if(!RM){c.style.transition='opacity .55s cubic-bezier(.22,.61,.36,1),transform .55s cubic-bezier(.22,.61,.36,1)';
     requestAnimationFrame(function(){c.style.opacity=1;c.style.transform='none';});
     setTimeout(function(){window.dispatchEvent(new Event('resize'));},580);}
   c.querySelectorAll('.ph-price,.k-val,.m-value').forEach(animNum);
 });},{threshold:0.05});
 function initCards(){document.querySelectorAll('.pane .card').forEach(function(c){
   if(c.__fx)return;c.__fx=1;
   if(!RM){c.style.opacity=0;c.style.transform='translateY(18px)';}
   io.observe(c);
   if(!RM&&!isChart(c)){
     c.addEventListener('mousemove',function(e){var r=c.getBoundingClientRect();
       var rx=((e.clientY-r.top)/r.height-.5)*-2.4,ry=((e.clientX-r.left)/r.width-.5)*2.4;
       c.style.transform='perspective(1100px) rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg)';});
     c.addEventListener('mouseleave',function(){c.style.transform='';});
   }
 });}
 function boot(){
   initCards();
   var h=document.querySelector('header h1');
   if(h&&!RM)document.addEventListener('mousemove',function(e){
     var ry=(e.clientX/window.innerWidth-.5)*4,rx=(e.clientY/window.innerHeight-.5)*-2;
     h.style.transform='rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg)';});
   // 새 탭(M4 등) 활성화 후 카드가 추가될 수 있으니 한 번 더 스캔
   var nav=document.querySelector('nav');
   if(nav)nav.addEventListener('click',function(){setTimeout(initCards,120);});
 }
 if(document.readyState!=='loading')boot();else document.addEventListener('DOMContentLoaded',boot);
})();
</script>"""


def _inject_fx(html_doc: str) -> str:
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _FX_STYLE + "</head>", 1)
    if "</body>" in html_doc:
        html_doc = html_doc.replace("</body>", _FX_JS + "</body>", 1)
    return html_doc


# 결과 HTML 끝에 붙는 인터랙션 스크립트 (M4 그리드 전용)
_M4_WIRE = """<script>
(function(){
 var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 function fmt(v,dec,sign){return (sign&&v>0?'+':'')+Number(v).toLocaleString('en-US',
   {minimumFractionDigits:dec,maximumFractionDigits:dec});}
 document.querySelectorAll('.m4-grid .cu').forEach(function(el){
   var to=parseFloat(el.getAttribute('data-to'))||0,dec=+(el.getAttribute('data-dec')||0),
       sign=el.getAttribute('data-sign')==='1';
   if(RM){el.textContent=fmt(to,dec,sign);return;}
   var t0=null;function step(t){if(!t0)t0=t;var k=Math.min((t-t0)/950,1),e=1-Math.pow(1-k,3);
     el.textContent=fmt(to*e,dec,sign);if(k<1)requestAnimationFrame(step);else el.textContent=fmt(to,dec,sign);}
   requestAnimationFrame(step);
 });
 var cards=document.querySelectorAll('.m4-grid > .card, .m4-grid > .m4-note');
 cards.forEach(function(c,i){if(RM)return;
   c.style.opacity=0;c.style.transform='translateY(20px)';
   setTimeout(function(){c.style.transition='opacity .6s cubic-bezier(.22,.61,.36,1),transform .6s cubic-bezier(.22,.61,.36,1)';
     c.style.opacity=1;c.style.transform='none';setTimeout(function(){window.dispatchEvent(new Event('resize'));},620);},95*i);
 });
 document.querySelectorAll('.m4-grid .card:not(.m4-card-3d)').forEach(function(c){
   if(RM||c.querySelector('.plotly-graph-div,svg.main-svg'))return;
   c.addEventListener('mousemove',function(e){var r=c.getBoundingClientRect();
     var rx=((e.clientY-r.top)/r.height-.5)*-2.6,ry=((e.clientX-r.left)/r.width-.5)*2.6;
     c.style.transform='perspective(1100px) rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg)';});
   c.addEventListener('mouseleave',function(){c.style.transform='';});
 });
 function autoRotate(gd){
   var R=2.4,Z=1.05,a=Math.atan2(1.5,1.7),paused=false,intro=0;
   gd.addEventListener('mouseenter',function(){paused=true;});
   gd.addEventListener('mouseleave',function(){paused=false;});
   setInterval(function(){
     if(!gd._fullLayout||!gd._fullLayout.scene||paused)return;
     if(intro<1)intro=Math.min(intro+0.018,1);a+=0.006;
     Plotly.relayout(gd,{'scene.camera.eye':{x:R*Math.cos(a),y:R*Math.sin(a),z:Z+(1-intro)*1.3}});
   },40);
 }
 if(!RM&&window.Plotly){document.querySelectorAll('.m4-card-3d .plotly-graph-div').forEach(function(gd){
   var n=0;(function wait(){if(gd._fullLayout&&gd._fullLayout.scene){autoRotate(gd);return;}
     if(n++<50)setTimeout(wait,80);})();});}
})();
</script>"""


# ════════════════ 주식 퀀트 (제너레이터) ════════════════
def _gen_stock_quant(code: str):
    yield ("p", 5, "시계열 데이터 적재 (SSD 캐시)…")
    # 종목 + KODEX 200(CAPM 대용치)을 Fetcher 1개로 병렬 수집
    need_proxy = code != MARKET_PROXY
    if need_proxy:
        stock_rows, proxy_rows = asyncio.run(_afetch_multi((code, 2400), (MARKET_PROXY, 2400)))
    else:
        stock_rows = asyncio.run(_afetch(code, 2400))
        proxy_rows = stock_rows
    dates, closes = _clean_closes(stock_rows)
    if closes.size < 120:
        yield ("done", '<div class="m4-grid"><div class="m4-note">시계열이 부족하여 분석할 수 없습니다.</div></div>')
        return
    cur = float(closes[-1])
    rs = _risk_stats(closes)
    logr, mu, sigma = rs["logr"], rs["mu"], rs["sd"]

    # ① 리스크·수익 지표 + 몬테카를로
    yield ("p", 18, "리스크 지표 · 몬테카를로 25,000 경로…")
    n_sim, horizon = 25_000, 252
    rng = np.random.default_rng()
    draws = rng.normal(mu, sigma, size=(n_sim, horizon)).astype(np.float32)
    paths = cur * np.exp(np.cumsum(draws, axis=1))
    days = np.arange(1, horizon + 1)
    pcts = np.percentile(paths, [5, 25, 50, 75, 95], axis=0)
    term = paths[:, -1]
    med_t, p5_t, p95_t = float(np.median(term)), float(np.percentile(term, 5)), float(np.percentile(term, 95))
    prob_up = float((term > cur).mean() * 100)
    exp_ret = (med_t / cur - 1) * 100
    mc_var = float(np.percentile(term / cur - 1, 5) * 100)

    metric = _metric_grid([
        ("연율 수익률", _cu(rs["ann_ret"], 1, True) + "%", "기하 연환산"),
        ("연율 변동성", _cu(rs["ann_vol"], 1) + "%", "일간 로그수익 기준"),
        ("샤프 지수", _cu(rs["sharpe"], 2), "Rf 0 가정"),
        ("소르티노", _cu(rs["sortino"], 2), "하방위험 기준"),
        ("최대낙폭 MDD", _cu(rs["mdd"], 1, True) + "%", "전 기간"),
        ("VaR 95% (1일)", _cu(rs["var95"], 1, True) + "%", "일간 손실 한계"),
        ("CVaR 95% (1일)", _cu(rs["cvar95"], 1, True) + "%", "조건부 기대손실"),
        ("MC 1년 VaR", _cu(mc_var, 1, True) + "%", "5% 하위 시나리오"),
    ])
    metric_html = _card("📊 리스크·수익 지표 (Risk Analytics)", metric)

    fan = go.Figure()
    for name, lo, hi, fill in [("5~95% 구간", pcts[0], pcts[4], "rgba(155,107,255,.14)"),
                               ("25~75% 구간", pcts[1], pcts[3], "rgba(54,198,255,.22)")]:
        fan.add_trace(go.Scatter(x=days, y=hi, mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        fan.add_trace(go.Scatter(x=days, y=lo, mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor=fill, name=name, hoverinfo="skip"))
    fan.add_trace(go.Scatter(x=days, y=pcts[2], mode="lines", name="중앙값 경로",
                             line=dict(color="#e8ecff", width=2.5)))
    fan.add_hline(y=cur, line_dash="dash", line_color=C_UP,
                  annotation_text=f"현재가 {cur:,.0f}원", annotation_position="top left")
    fan.update_xaxes(title="향후 거래일 (영업일)")
    fan.update_yaxes(title="예상 주가(원)", tickformat=",")
    _layout(fan, 430)

    # 3D 확률 지형
    yield ("p", 36, "확률 지형 (3D · GPU)…")
    surf_html = ""
    try:
        from scipy.stats import gaussian_kde
        slices = np.unique(np.linspace(int(horizon * 0.06), horizon - 1, 26).astype(int))
        grid = np.linspace(np.percentile(paths, 2), np.percentile(paths, 98), 90)
        z = np.empty((slices.size, grid.size))
        for k, d in enumerate(slices):
            z[k] = gaussian_kde(paths[:, d])(grid)
        surf = go.Figure(go.Surface(x=grid, y=slices + 1, z=z, colorscale="Plasma",
                                    showscale=False,
                                    contours={"z": {"show": True, "usecolormap": True, "project_z": True}}))
        _scene3d(surf, 500, dict(xaxis=dict(title="주가(원)", tickformat=","),
                                 yaxis=dict(title="향후 영업일"),
                                 zaxis=dict(title="발생 밀도", showticklabels=False),
                                 camera=dict(eye=dict(x=1.7, y=-1.5, z=1.05))))
        surf_html = _frag3d(surf, "🌄 확률 지형도 — 시간 경과에 따른 가격 분포 (3D · WebGL)")
    except Exception:  # noqa: BLE001
        surf_html = ""

    # ② 3D 변동성 표면 (Volatility Surface)
    yield ("p", 52, "변동성 표면 (3D · 롤링 실현변동성)…")
    vsurf_html = ""
    try:
        windows = [5, 10, 21, 42, 63, 126]
        ser = pd.Series(logr)
        mat = [(ser.rolling(w).std() * np.sqrt(252) * 100).to_numpy() for w in windows]
        M = np.array(mat)[:, max(windows):]
        ncol = M.shape[1]
        if ncol > 8:
            idx = np.linspace(0, ncol - 1, min(ncol, 130)).astype(int)
            M = M[:, idx]
            vsurf = go.Figure(go.Surface(x=np.arange(M.shape[1]), y=windows, z=M,
                                         colorscale="Cividis", showscale=True,
                                         colorbar=dict(title="연율%")))
            _scene3d(vsurf, 500, dict(xaxis=dict(title="기간 경과(영업일·과거→현재)"),
                                      yaxis=dict(title="관측 창(일)"),
                                      zaxis=dict(title="연율 변동성(%)"),
                                      camera=dict(eye=dict(x=1.8, y=-1.5, z=1.0))))
            vsurf_html = _frag3d(vsurf, "🌊 변동성 표면 — 관측창×시간 실현변동성 (3D · 변동성 레짐)")
    except Exception:  # noqa: BLE001
        vsurf_html = ""

    # ③ 수익률 분포 · 팻테일
    yield ("p", 66, "수익률 분포 · 팻테일(왜도/첨도)…")
    dist_html, dist_note = "", ""
    try:
        from scipy.stats import norm, skew, kurtosis
        r_pct = logr * 100
        sk, ku = float(skew(r_pct)), float(kurtosis(r_pct))
        dist = go.Figure()
        dist.add_trace(go.Histogram(x=r_pct, histnorm="probability density", nbinsx=70,
                                    marker_color="rgba(54,198,255,.45)",
                                    marker_line=dict(width=0), name="실현 분포"))
        xx = np.linspace(r_pct.min(), r_pct.max(), 200)
        dist.add_trace(go.Scatter(x=xx, y=norm.pdf(xx, r_pct.mean(), r_pct.std()), mode="lines",
                                  name="정규분포(동일 μ·σ)", line=dict(color="#e8ecff", width=2)))
        dist.add_vline(x=rs["var95"], line_dash="dash", line_color=C_UP,
                       annotation_text="VaR 95%")
        dist.update_xaxes(title="일간 로그수익률 (%)")
        dist.update_yaxes(title="밀도", showticklabels=False)
        _layout(dist, 400)
        dist_html = _frag(dist, "🔔 수익률 분포 · 팻테일 분석")
        tail_word = "정규분포보다 꼬리가 두꺼움(첨도↑)" if ku > 0.5 else "정규분포에 가까움"
        skew_word = "좌측(하락) 꼬리" if sk < -0.1 else ("우측(상승) 꼬리" if sk > 0.1 else "대칭에 가까움")
        dist_note = (f" 왜도(Skew) {_cu(sk, 2, True)} ({skew_word}) · 초과첨도(Kurtosis) "
                     f"{_cu(ku, 2, True)} — {tail_word}.")
    except Exception:  # noqa: BLE001
        dist_html, dist_note = "", ""

    # ④ CAPM 베타/알파 (vs KODEX 200)
    yield ("p", 80, "CAPM 베타/알파 (vs KODEX 200)…")
    capm_html = ""
    try:
        if need_proxy:
            md, mc = _clean_closes(proxy_rows)  # 시작 시 이미 병렬 수집된 데이터 재사용
            if mc.size > 60:
                s = pd.DataFrame({"d": pd.to_datetime(dates), "s": closes})
                m = pd.DataFrame({"d": pd.to_datetime(md), "m": mc})
                j = s.merge(m, on="d").sort_values("d")
                j["rs"] = np.log(j["s"]).diff()
                j["rm"] = np.log(j["m"]).diff()
                j = j.dropna()
                if len(j) > 40:
                    xr, yr = j["rm"].to_numpy() * 100, j["rs"].to_numpy() * 100
                    beta = float(np.cov(yr, xr)[0, 1] / np.var(xr))
                    alpha = float((yr.mean() - beta * xr.mean()) / 100 * 252 * 100)
                    r2 = float(np.corrcoef(yr, xr)[0, 1] ** 2)
                    line_x = np.array([xr.min(), xr.max()])
                    line_y = beta * line_x + (yr.mean() - beta * xr.mean())
                    cap = go.Figure()
                    cap.add_trace(go.Scattergl(x=xr, y=yr, mode="markers", name="일간 수익률",
                                               marker=dict(size=4, color="rgba(155,107,255,.5)")))
                    cap.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines", name="회귀선",
                                             line=dict(color=C_CYAN, width=2.5)))
                    cap.update_xaxes(title="시장(KODEX 200) 일간수익률 %")
                    cap.update_yaxes(title="종목 일간수익률 %")
                    _layout(cap, 420)
                    capm_html = _frag(cap, f"📈 CAPM 베타/알파 (vs KODEX 200) — β {beta:.2f} · "
                                           f"α(연) {alpha:+.1f}% · R² {r2:.2f}")
    except Exception:  # noqa: BLE001
        capm_html = ""

    # ⑤ 프랙탈 패턴 매칭 (벡터화)
    yield ("p", 90, "프랙탈 패턴 매칭 (멀티코어 벡터화)…")
    frac_html, frac_note = "", ""
    try:
        from numpy.lib.stride_tricks import sliding_window_view
        L = 20
        tgt = closes[-L:]
        tn = (tgt - tgt.mean()) / (tgt.std() + 1e-9)
        limit = closes.size - 2 * L
        if limit > 5:
            W = sliding_window_view(closes, L)[:limit]
            Wn = (W - W.mean(1, keepdims=True)) / (W.std(1, keepdims=True) + 1e-9)
            mse = ((Wn - tn) ** 2).mean(1)
            order = np.argsort(mse)
            top, used = [], []
            for i in order:
                i = int(i)
                if any(abs(i - u) < L for u in used):
                    continue
                used.append(i)
                top.append(i)
                if len(top) >= 5:
                    break
            colors = [C_CYAN, "#E08E3C", "#9b6bff", "#27AE60", "#F39C12"]
            fwd = []
            frac = go.Figure()
            frac.add_trace(go.Scatter(x=np.arange(L), y=tn, mode="lines", name="현재 (최근 20일)",
                                      line=dict(color=C_UP, width=4)))
            for rank, i in enumerate(top):
                seg = closes[i:i + 2 * L]
                base = seg[:L]
                sn = (seg - base.mean()) / (base.std() + 1e-9)
                ds = pd.Timestamp(dates[i]).strftime("%Y-%m") if i < dates.size else ""
                frac.add_trace(go.Scatter(x=np.arange(seg.size), y=sn, mode="lines",
                                          name=f"매칭 {rank + 1} · {ds}",
                                          line=dict(color=colors[rank], width=1.6, dash="dot")))
                if seg.size == 2 * L:
                    fwd.append((seg[-1] / seg[L - 1] - 1) * 100)
            frac.add_vline(x=L - 1, line_dash="dot", line_color="#9aa3b2", annotation_text="현재 시점")
            frac.update_xaxes(title="경과일 (0~19 과거구간 · 20~39 이후 궤적)")
            frac.update_yaxes(title="정규화 가격(z-score)")
            _layout(frac, 440)
            if fwd:
                up_ratio = sum(1 for r in fwd if r > 0) / len(fwd) * 100
                frac_note = (f" 과거 닮은꼴 {len(fwd)}건의 이후 20일 수익률 중앙값 "
                             f"{_cu(np.median(fwd), 1, True)}% · 상승 비율 {_cu(up_ratio, 0)}%.")
            frac_html = _frag(frac, "🧬 프랙탈 패턴 매칭 — 과거 닮은꼴 흐름의 이후 20일 궤적")
    except Exception:  # noqa: BLE001
        frac_html, frac_note = "", ""

    yield ("p", 95, "차트 렌더링…")
    note = (
        '<div class="m4-note"><b>💡 M4 퀀트 데스크 브리핑.</b> 25,000개의 가격 경로를 벡터화 '
        "NumPy로 생성했습니다 (Apple Accelerate BLAS · 성능 코어 멀티스레드). 1년 뒤 분포 "
        f"중앙값 {_cu(med_t)}원(현재가 대비 {_cu(exp_ret, 1, True)}%), 90% 구간 "
        f"<b>{p5_t:,.0f}~{p95_t:,.0f}원</b>, 현재가 상회 확률 {_cu(prob_up, 0)}%."
        + dist_note + frac_note +
        "<br><span style='font-size:12px;color:#8f9cd0'>※ 과거 통계 기반 추정치로 미래 수익을 "
        "보장하지 않습니다. 투자 판단의 참고 자료로만 활용하세요.</span></div>")

    html = ('<div class="m4-grid">' + note + metric_html
            + _frag(fan, "🎲 몬테카를로 미래주가 시뮬레이션 — 25,000 경로 · 1년 분포")
            + surf_html + vsurf_html + dist_html + capm_html + frac_html
            + "</div>" + _M4_WIRE)
    yield ("done", html)


# ════════════════ ETF 퀀트 (제너레이터) ════════════════
def _gen_etf_quant(code: str):
    yield ("p", 6, "전 기간 시계열 적재 · 편입종목 병렬 수집…")
    chart_rows, an, ccodes, cons = asyncio.run(_fetch_etf_bundle(code))
    dates, closes = _clean_closes(chart_rows)
    if closes.size < 120:
        yield ("done", '<div class="m4-grid"><div class="m4-note">시계열이 부족하여 분석할 수 없습니다.</div></div>')
        return
    df = pd.DataFrame({"일자": pd.to_datetime(dates), "종가": closes})
    df["ret"] = df["종가"].pct_change()
    df["연도"], df["월"] = df["일자"].dt.year, df["일자"].dt.month
    ret = df["ret"].fillna(0.0)
    rs = _risk_stats(closes)

    # 편입종목 시계열 정렬 + 상관행렬
    top10 = {str(it.get("종목코드")): it for it in (an.get("top10") or [])}
    series = {}
    for cc, rows in zip(ccodes, cons):
        d, cl = _clean_closes(rows)
        if cl.size < 40:
            continue
        nm = str(top10.get(cc, {}).get("종목명") or cc)
        series[nm] = pd.Series(cl, index=pd.to_datetime(d))
    corr, labels, avg_corr = None, [], None
    if len(series) >= 2:
        cdf = pd.DataFrame(series).sort_index()
        rdf = np.log(cdf).diff().dropna(how="all")
        cm = rdf.corr()
        labels = list(cm.columns)
        corr = cm.to_numpy()
        off = corr[~np.eye(corr.shape[0], dtype=bool)]
        avg_corr = float(np.nanmean(off)) if off.size else None

    # 집중도(HHI) · 유효 종목수
    ws = [float(it["비중(%)"]) for it in top10.values() if isinstance(it.get("비중(%)"), (int, float))]
    hhi = float(sum(w * w for w in ws)) if ws else 0.0
    fr = [w / 100 for w in ws]
    eff = float(1 / sum(f * f for f in fr)) if fr and sum(f * f for f in fr) else 0.0

    # ① 리스크·집중도 지표
    yield ("p", 26, "리스크·집중도 지표…")
    metric = _metric_grid([
        ("연율 수익률", _cu(rs["ann_ret"], 1, True) + "%", "기하 연환산"),
        ("연율 변동성", _cu(rs["ann_vol"], 1) + "%", "일간 기준"),
        ("샤프 지수", _cu(rs["sharpe"], 2), "Rf 0 가정"),
        ("최대낙폭 MDD", _cu(rs["mdd"], 1, True) + "%", "전 기간"),
        ("VaR 95% (1일)", _cu(rs["var95"], 1, True) + "%", "일간 손실 한계"),
        ("집중도 HHI", _cu(hhi, 0), "Top10 비중² 합"),
        ("유효 종목수", _cu(eff, 1), "1/Σw² (분산도)"),
        ("평균 상관계수", (_cu(avg_corr, 2, True) if avg_corr is not None else "—"),
         "편입종목 분산효과"),
    ])
    metric_html = _card("📊 리스크·집중도 지표 (Risk & Concentration)", metric)

    # ② 계절성 히트맵
    yield ("p", 40, "계절성 히트맵 · 언더워터(MDD)…")
    mret = (df.dropna(subset=["ret"]).groupby(["연도", "월"])["ret"]
            .apply(lambda x: (1 + x).prod() - 1))
    pivot = mret.unstack("월").reindex(columns=range(1, 13))
    heat = go.Figure(go.Heatmap(z=pivot.values * 100, x=[f"{m}월" for m in pivot.columns],
                                y=[str(y) for y in pivot.index], colorscale="RdBu",
                                reversescale=True, zmid=0, text=np.round(pivot.values * 100, 1),
                                texttemplate="%{text}", textfont=dict(size=10, color="#0b0f20"),
                                colorbar=dict(title="%")))
    _layout(heat, max(320, 70 + 26 * len(pivot.index)))

    cum = (1 + ret).cumprod()
    dd = cum / cum.cummax() - 1
    mdd = float(dd.min() * 100)
    uw = go.Figure()
    uw.add_trace(go.Scatter(x=df["일자"], y=cum, mode="lines", name="누적 수익(배수)",
                            line=dict(color=C_UP, width=2)))
    uw.add_trace(go.Scatter(x=df["일자"], y=dd, mode="lines", name="낙폭(MDD)", fill="tozeroy",
                            line=dict(color=C_CYAN, width=1.2),
                            fillcolor="rgba(54,198,255,.25)", yaxis="y2"))
    uw.update_layout(yaxis=dict(title="누적 수익(배수)"),
                     yaxis2=dict(title="낙폭", overlaying="y", side="right", tickformat=".0%"))
    _layout(uw, 380)

    # ③ 롤링 변동성 (레짐)
    yield ("p", 54, "롤링 변동성 · 적립식 백테스트…")
    rv = (pd.Series(ret).rolling(63).std() * np.sqrt(252) * 100)
    roll = go.Figure()
    roll.add_trace(go.Scatter(x=df["일자"], y=rv, mode="lines", name="63일 연율 변동성",
                              line=dict(color="#E08E3C", width=1.8),
                              fill="tozeroy", fillcolor="rgba(224,142,60,.15)"))
    roll.add_hline(y=rs["ann_vol"], line_dash="dot", line_color="#9aa3b2",
                   annotation_text=f"전기간 평균 {rs['ann_vol']:.1f}%")
    roll.update_yaxes(title="연율 변동성(%)")
    _layout(roll, 350)

    # 적립식 백테스트
    dca_html, dca_note = "", ""
    try:
        first_idx = set(df.groupby([df["연도"], df["월"]]).head(1).index)
        monthly = 1_000_000.0
        units = invested = 0.0
        inv_s, val_s = [], []
        for idx, row in df.iterrows():
            px = row["종가"]
            if idx in first_idx and px > 0:
                units += monthly / px
                invested += monthly
            inv_s.append(invested)
            val_s.append(units * px)
        df["_inv"], df["_val"] = inv_s, val_s
        sub = df[df["_inv"] > 0]
        fi, fv = float(sub["_inv"].iloc[-1]), float(sub["_val"].iloc[-1])
        dca_ret = (fv / fi - 1) * 100 if fi else 0.0
        lump_ret = (closes[-1] / closes[0] - 1) * 100
        dca = go.Figure()
        dca.add_trace(go.Scatter(x=sub["일자"], y=sub["_val"], mode="lines", name="평가금액",
                                 line=dict(color="#9b6bff", width=2.2), fill="tozeroy",
                                 fillcolor="rgba(155,107,255,.16)"))
        dca.add_trace(go.Scatter(x=sub["일자"], y=sub["_inv"], mode="lines", name="누적 투자원금",
                                 line=dict(color="#9aa3b2", width=1.6, dash="dot")))
        dca.update_yaxes(title="금액(원)", tickformat=",")
        _layout(dca, 380)
        dca_note = (f" 매월 100만원 적립 시 누적원금 <b>{fi:,.0f}원</b> → 평가금액 "
                    f"{_cu(fv)}원({_cu(dca_ret, 1, True)}%). 일시불 보유 수익률 "
                    f"{_cu(lump_ret, 1, True)}%.")
        dca_html = _frag(dca, "💰 적립식 백테스트 — 매월 100만원 매수 시 평가금액 추이")
    except Exception:  # noqa: BLE001
        dca_html, dca_note = "", ""

    # ④ 3D 편입종목 상관관계 행렬
    yield ("p", 74, "편입종목 상관관계 행렬 (3D)…")
    corr_html = ""
    if corr is not None and len(labels) >= 2:
        idx = np.arange(len(labels))
        csurf = go.Figure(go.Surface(z=corr, x=idx, y=idx, colorscale="RdBu", cmid=0,
                                     cmin=-1, cmax=1, showscale=True, colorbar=dict(title="ρ")))
        _scene3d(csurf, 540, dict(
            xaxis=dict(title="", tickmode="array", tickvals=idx, ticktext=labels),
            yaxis=dict(title="", tickmode="array", tickvals=idx, ticktext=labels),
            zaxis=dict(title="상관계수 ρ", range=[-1, 1]),
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.1))))
        corr_html = _frag3d(csurf, "🧩 편입종목 상관관계 행렬 (3D · 분산효과)")

    # ⑤ 3D 리스크-리턴-비중 지형
    yield ("p", 86, "편입종목 리스크-리턴 지형 (3D)…")
    bubble_html = ""
    try:
        names, vols, rets6, weights = [], [], [], []
        for cc, rows in zip(ccodes, cons):
            _d, cl = _clean_closes(rows)
            if cl.size < 30:
                continue
            lr = np.diff(np.log(cl))
            lr = lr[np.isfinite(lr)]
            if lr.size < 20:
                continue
            it = top10.get(cc, {})
            w = it.get("비중(%)")
            w = float(w) if isinstance(w, (int, float)) else 1.0
            names.append(str(it.get("종목명") or cc))
            vols.append(float(np.std(lr) * np.sqrt(252) * 100))
            n6 = min(126, cl.size - 1)
            rets6.append(float((cl[-1] / cl[-1 - n6] - 1) * 100))
            weights.append(max(w, 0.3))
        if names:
            sizes = np.array(weights)
            bub = go.Figure(go.Scatter3d(
                x=vols, y=rets6, z=weights, mode="markers+text", text=names,
                textposition="top center", textfont=dict(size=10, color=C_INK),
                marker=dict(size=sizes, sizemode="area", sizeref=2.0 * sizes.max() / (32 ** 2),
                            sizemin=4, color=rets6, colorscale="RdBu", cmid=0,
                            line=dict(width=0.5, color="#0b0f20"), colorbar=dict(title="6M%")),
                hovertemplate="%{text}<br>변동성 %{x:.1f}%<br>6개월 %{y:.1f}%<br>비중 %{z:.2f}%<extra></extra>"))
            _scene3d(bub, 540, dict(xaxis=dict(title="리스크 (연율 변동성 %)"),
                                    yaxis=dict(title="리턴 (최근 6개월 %)"),
                                    zaxis=dict(title="ETF 내 비중 (%)"),
                                    camera=dict(eye=dict(x=1.7, y=1.6, z=1.0))))
            bubble_html = _frag3d(bub, "🎯 편입 상위 종목 리스크-리턴-비중 지형 (3D · 실데이터)")
    except Exception:  # noqa: BLE001
        bubble_html = ""

    yield ("p", 94, "차트 렌더링…")
    corr_word = ""
    if avg_corr is not None:
        corr_word = (f" 편입종목 평균 상관계수 <b>{avg_corr:.2f}</b> — "
                     + ("분산효과가 큰 편" if avg_corr < 0.4 else
                        ("보통" if avg_corr < 0.7 else "동조화가 높아 분산효과 제한")) + ".")
    note = (
        '<div class="m4-note"><b>💡 M4 백테스팅·리스크 데스크.</b> 전 상장 기간 시계열로 '
        f"리스크·집중도·계절성·적립식 성과를 한 번에 계산했습니다. 최대낙폭(MDD) "
        f"{_cu(mdd, 1, True)}% · 집중도(HHI) {_cu(hhi, 0)} · 유효 종목수 {_cu(eff, 1)}."
        + dca_note + corr_word +
        (f" 편입 상위 {len(ccodes)}개 종목 시계열을 비동기 병렬 수집했습니다." if ccodes else "")
        + "</div>")

    html = ('<div class="m4-grid">' + note + metric_html
            + _frag(heat, "🗓️ 월별 수익률 히트맵 — 계절성 (전 기간 · %)")
            + _frag(uw, f"📉 누적 수익 & 언더워터 리스크 — 최대낙폭(MDD) {mdd:.1f}%")
            + _frag(roll, "🌡️ 롤링 변동성 (63일) — 변동성 레짐")
            + dca_html + corr_html + bubble_html + "</div>" + _M4_WIRE)
    yield ("done", html)


# ════════════════ SSE 스트리밍 ════════════════
def _sse_progress(pct: int, label: str) -> str:
    return f"event: progress\ndata: {json.dumps({'pct': pct, 'label': label}, ensure_ascii=False)}\n\n"


def _sse_done(html: str) -> str:
    return f"event: done\ndata: {json.dumps({'html': html}, ensure_ascii=False)}\n\n"


def _sse_failed(msg: str) -> str:
    return f"event: failed\ndata: {json.dumps({'msg': msg}, ensure_ascii=False)}\n\n"


def _stream(kind: str, code: str):
    key = (kind, code)
    gen_fn = _gen_stock_quant if kind == "stock" else _gen_etf_quant

    def gen():
        cached = _rget(key)
        if cached:
            yield _sse_progress(100, "캐시된 결과 불러오기 (RAM)")
            yield _sse_done(cached)
            return
        try:
            for ev in gen_fn(code):
                if ev[0] == "p":
                    yield _sse_progress(ev[1], ev[2])
                elif ev[0] == "done":
                    _rput(key, ev[1])
                    yield _sse_done(ev[1])
        except Exception:  # noqa: BLE001
            yield _sse_failed(traceback.format_exc())
    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


def _precompute(kind: str, code: str) -> None:
    try:
        gen_fn = _gen_stock_quant if kind == "stock" else _gen_etf_quant
        for ev in gen_fn(code):
            if ev[0] == "done":
                _rput((kind, code), ev[1])
    except Exception:  # noqa: BLE001
        pass


@app.get("/api/quant/stock")
def api_quant_stock() -> Response:
    code = (request.args.get("code") or "").strip()
    if not code:
        return Response("Error: no code", status=400)
    return _stream("stock", code)


@app.get("/api/quant/etf")
def api_quant_etf() -> Response:
    code = (request.args.get("code") or "").strip()
    if not code:
        return Response("Error: no code", status=400)
    return _stream("etf", code)


# ════════════════ 라우트 ════════════════
@app.get("/")
def index() -> Response:
    return Response(_LANDING_HTML, mimetype="text/html")


@app.get("/suggest")
def suggest():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    out: list[dict] = []
    try:
        corps = company.get_corps()
        listed = [c for c in corps if c.get("stock_code")]
        if q.isdigit():
            shits = [c for c in listed if c["stock_code"].startswith(q)]
        else:
            qn = q.lower().replace(" ", "")

            def _norm(s):
                return (s or "").lower().replace(" ", "")
            exact = [c for c in listed if _norm(c["corp_name"]) == qn]
            partial = [c for c in listed if qn in _norm(c["corp_name"]) and c not in exact]
            shits = exact + partial
        for c in shits[:8]:
            out.append({"code": c["stock_code"], "name": c["corp_name"], "type": "주식", "extra": ""})
    except Exception:  # noqa: BLE001
        pass
    try:
        _df, snap, _ld = etf.get_market()
        if snap is not None and not snap.empty:
            codes = snap["코드"].astype(str)
            mask = (snap["종목명"].str.contains(q, case=False, na=False, regex=False)
                    | codes.str.upper().str.contains(q.upper(), regex=False))
            for _, r in snap[mask].sort_values("거래대금(억)", ascending=False).head(6).iterrows():
                out.append({"code": str(r["코드"]), "name": str(r["종목명"]), "type": "ETF",
                            "extra": str(r.get("운용사", "") or "")})
    except Exception:  # noqa: BLE001
        pass
    return jsonify(out[:14])


@app.get("/dashboard")
def dashboard() -> Response:
    q = (request.args.get("q") or "").strip()
    if not q:
        return Response(_error_html("검색어를 입력하세요."), mimetype="text/html")
    try:
        snap = _get_etf_snap()  # get_market() 1회만 호출
        kind = detect_type(q, snap=snap)
        if kind == "etf":
            html, err = etf.build_dashboard_html(q)
            code = _resolve_etf_code(q, snap=snap)
        else:
            html, err = company.build_company_html(q)
            code = _resolve_stock_code(q)
    except Exception as e:  # noqa: BLE001
        return Response(_error_html(f"오류가 발생했습니다: {e}"), mimetype="text/html")
    if err:
        return Response(_error_html(err), mimetype="text/html")
    try:
        html = _inject_fx(html)            # 작업1·4: 기본 탭 FX 레이어
        html = _inject_m4_tab(html, kind, code)
    except Exception:  # noqa: BLE001
        pass
    return Response(html, mimetype="text/html")


@app.get("/report_pdf")
def report_pdf() -> Response:
    nid = (request.args.get("nid") or "").strip()
    code = (request.args.get("code") or "").strip()
    if not nid.isdigit():
        return Response("잘못된 요청", status=400)
    try:
        with httpx.Client(timeout=20, follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = c.get(f"https://finance.naver.com/research/company_read.naver?nid={nid}")
            page = r.content.decode("euc-kr", errors="replace")
            m = re.search(r'https://stock\.pstatic\.net/stock-research/[^"\' ]+\.pdf', page)
            if not m:
                return Response(
                    "<div style='font-family:-apple-system,sans-serif;padding:48px;text-align:center;"
                    "color:#6b7689'>이 리포트는 첨부 PDF가 없습니다.<br><br>"
                    f"<a href='https://stock.naver.com/domestic/stock/{code}/research/{nid}' "
                    "target='_blank' style='color:#2E75B6;font-weight:700'>네이버에서 원문 보기 ↗</a></div>",
                    mimetype="text/html")
            pdf = c.get(m.group(0), headers={"Referer": "https://finance.naver.com/"})
            return Response(pdf.content, mimetype="application/pdf",
                            headers={"Content-Disposition": "inline; filename=report.pdf"})
    except Exception as e:  # noqa: BLE001
        return Response(f"PDF를 불러오지 못했습니다: {e}", status=502)


# ════════════════ 자동 종료 ════════════════
_last_ping = {"t": 0.0, "seen": False}
_bye = {"t": 0.0}
_PING_TIMEOUT = 15.0


@app.get("/__ping")
def __ping() -> Response:
    _last_ping["t"] = time.time()
    _last_ping["seen"] = True
    _bye["t"] = 0.0
    return Response("ok", mimetype="text/plain")


@app.post("/__bye")
@app.get("/__bye")
def __bye() -> Response:
    _bye["t"] = time.time()
    return Response("bye", mimetype="text/plain")


def _close_terminal() -> None:
    if sys.platform != "darwin":
        return
    tty = ""
    for fd in (sys.stdin, sys.stdout, sys.stderr):
        try:
            tty = os.ttyname(fd.fileno())
            break
        except Exception:  # noqa: BLE001
            continue
    if not tty:
        return
    scpt = ('tell application "Terminal"\n repeat with w in windows\n  repeat with t in tabs of w\n'
            f'   if tty of t is "{tty}" then close w saving no\n  end repeat\n end repeat\nend tell')
    try:
        subprocess.Popen(["osascript", "-e", scpt])
        time.sleep(0.4)
    except Exception:  # noqa: BLE001
        pass


def _monitor_heartbeat() -> None:
    while True:
        time.sleep(1)
        now = time.time()
        bye = _bye["t"] and (now - _bye["t"]) > 3 and (now - _last_ping["t"]) > 3
        stale = _last_ping["seen"] and (now - _last_ping["t"]) > _PING_TIMEOUT
        if bye or stale:
            print("\n  브라우저 종료 감지 — 서버를 종료합니다.")
            _close_terminal()
            os._exit(0)


def _error_html(msg: str) -> str:
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<style>body{{margin:0;font-family:-apple-system,'Apple SD Gothic Neo',sans-serif;
background:#f4f6fb;color:#1a1a2e;display:flex;align-items:center;justify-content:center;height:100vh;}}
.box{{background:#fff;border:1px solid #e3e8f0;border-radius:14px;padding:40px 48px;text-align:center;
box-shadow:0 4px 20px rgba(20,40,80,.06);max-width:520px;}}
.box .ic{{font-size:42px;margin-bottom:10px;}}
.box h2{{margin:0 0 8px;color:#1F3864;font-size:19px;}}
.box p{{margin:0;color:#6b7689;font-size:14.5px;line-height:1.6;}}</style></head>
<body><div class="box"><div class="ic">🔍</div><h2>결과를 표시할 수 없습니다</h2><p>{msg}</p></div></body></html>"""


# ════════════════ 랜딩 페이지 ════════════════
_LANDING_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>K-Market Dashboard 2 · M4 Pro</title>
<style>
:root{--navy:#1F3864;--blue:#2E75B6;--violet:#7a3df0;--bg:#f4f6fb;--line:#e3e8f0;}
*{box-sizing:border-box;}
html,body{margin:0;height:100%;}
body{display:flex;flex-direction:column;background:var(--bg);
 font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','Apple SD Gothic Neo',sans-serif;color:#1a1a2e;}
.topbar{background:linear-gradient(120deg,#15233f,#1F3864,#3a1d6e,#2E75B6);background-size:300% 300%;
 animation:bargrad 16s ease infinite;color:#fff;padding:16px 24px;display:flex;align-items:center;gap:18px;
 box-shadow:0 2px 12px rgba(20,40,80,.18);z-index:20;}
@keyframes bargrad{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.topbar .brand{font-size:18px;font-weight:800;white-space:nowrap;display:flex;align-items:center;gap:8px;}
.topbar .brand small{font-weight:500;opacity:.82;font-size:12px;margin-left:4px;}
.m4-badge{font-size:11px;font-weight:800;background:rgba(255,255,255,.16);
 border:1px solid rgba(255,255,255,.32);padding:3px 9px;border-radius:999px;
 animation:m4pulse 2.6s ease-in-out infinite;}
@keyframes m4pulse{0%,100%{box-shadow:0 0 0 0 rgba(170,120,255,.45);}50%{box-shadow:0 0 14px 3px rgba(170,120,255,0);}}
.searchwrap{position:relative;flex:1;max-width:620px;}
#q{width:100%;padding:12px 16px;font-size:15px;border:0;border-radius:10px;
 box-shadow:0 1px 3px rgba(0,0,0,.15);outline:none;transition:box-shadow .2s;}
#q:focus{box-shadow:0 0 0 3px rgba(123,61,240,.35),0 1px 3px rgba(0,0,0,.15);}
#q::placeholder{color:#9aa3b2;}
.sg{position:absolute;top:48px;left:0;right:0;background:#fff;border:1px solid var(--line);
 border-radius:10px;box-shadow:0 8px 24px rgba(20,40,80,.14);overflow:hidden;display:none;z-index:30;max-height:420px;overflow-y:auto;
 transform-origin:top center;animation:sgIn .16s ease;}
@keyframes sgIn{from{opacity:0;transform:translateY(-6px);}to{opacity:1;transform:none;}}
.sg.show{display:block;}
.sg-item{padding:11px 16px;cursor:pointer;border-bottom:1px solid #f0f3f8;display:flex;align-items:center;gap:10px;}
.sg-item:last-child{border-bottom:0;}
.sg-item:hover,.sg-item.active{background:#eef5ff;}
.sg-badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 7px;flex:none;}
.sg-badge.etf{background:#e7f0fb;color:#2E75B6;}
.sg-badge.stk{background:#fdeef0;color:#c0392b;}
.sg-code{font-weight:700;color:var(--blue);font-size:13px;font-variant-numeric:tabular-nums;min-width:60px;}
.sg-name{font-weight:700;color:#15233f;font-size:14.5px;}
.sg-extra{margin-left:auto;color:#9aa3b2;font-size:12px;white-space:nowrap;}
.btn{background:#fff;color:var(--navy);border:0;border-radius:10px;padding:12px 22px;
 font-size:15px;font-weight:700;cursor:pointer;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.15);
 transition:transform .12s,background .15s;}
.btn:hover{background:#f0f4fb;transform:translateY(-1px);}
.btn:active{transform:translateY(0);}
.tabstrip{display:none;align-items:flex-end;gap:5px;background:#d7deea;padding:8px 10px 0;overflow-x:auto;}
.tab{display:flex;align-items:center;gap:7px;background:#eaeef4;border:1px solid var(--line);border-bottom:0;
 border-radius:11px 11px 0 0;padding:9px 11px;max-width:240px;cursor:pointer;color:#5b6b86;font-size:13px;font-weight:600;
 white-space:nowrap;user-select:none;transition:background .16s,transform .16s,box-shadow .16s;animation:tabPop .22s ease;}
@keyframes tabPop{from{opacity:0;transform:translateY(8px) scale(.96);}to{opacity:1;transform:none;}}
.tab:hover{background:#f1f4f9;transform:translateY(-1px);}
.tab.active{background:#fff;color:#15233f;box-shadow:0 -1px 4px rgba(20,40,80,.06);transform:translateY(-1px);}
.tab-ic{font-size:13px;flex:none;}
.tab-label{overflow:hidden;text-overflow:ellipsis;max-width:165px;}
.tab-close{border-radius:50%;width:18px;height:18px;line-height:17px;text-align:center;color:#9aa3b2;font-size:15px;flex:none;transition:background .12s,color .12s;}
.tab-close:hover{background:#d4dbe6;color:#33415c;}
.tab.dragging{opacity:.55;}
.stage{flex:1;position:relative;background:#fff;perspective:1400px;overflow:hidden;}
.stage::before{content:"";position:absolute;inset:-30%;z-index:0;pointer-events:none;
 background:conic-gradient(from 0deg at 30% 30%,rgba(123,61,240,.06),rgba(46,117,182,.05),rgba(123,61,240,.06));
 animation:bgspin 40s linear infinite;}
@keyframes bgspin{to{transform:rotate(360deg);}}
.framewrap{position:absolute;inset:0;opacity:0;transform:translateY(12px) scale(.992);
 transition:opacity .34s cubic-bezier(.22,.61,.36,1),transform .34s cubic-bezier(.22,.61,.36,1);
 pointer-events:none;z-index:1;}
.framewrap.show{opacity:1;transform:none;pointer-events:auto;z-index:2;}
.framewrap .frame{width:100%;height:100%;border:0;background:#fff;}
.framewrap .overlay{position:absolute;inset:0;background:rgba(244,246,251,.92);display:none;
 align-items:center;justify-content:center;flex-direction:column;gap:14px;z-index:5;}
.framewrap .overlay.show{display:flex;}
.spinner{width:42px;height:42px;border:4px solid #d4ddec;border-top-color:var(--violet);
 border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.framewrap .overlay p{color:#5b6b86;font-weight:600;font-size:14px;}
.empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 color:#8a93a6;text-align:center;padding:24px;z-index:3;}
.hero3d{transform-style:preserve-3d;transition:transform .25s ease;will-change:transform;
 background:rgba(255,255,255,.96);border:1px solid var(--line);border-radius:22px;padding:40px 52px;
 box-shadow:0 18px 50px rgba(31,56,100,.12);backdrop-filter:blur(4px);}
.empty .big{font-size:54px;margin-bottom:14px;transform:translateZ(46px);}
.empty h2{margin:0 0 8px;color:#1F3864;font-size:22px;font-weight:800;transform:translateZ(30px);}
.empty p{margin:2px 0;font-size:14.5px;transform:translateZ(16px);}
.empty .tagline{margin-top:10px;font-weight:700;
 background:linear-gradient(90deg,#7a3df0,#2E75B6);-webkit-background-clip:text;background-clip:text;color:transparent;}
.empty .ex{margin-top:18px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;transform:translateZ(10px);}
.empty .ex span{background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 14px;
 font-size:13px;color:#33415c;cursor:pointer;font-weight:600;transition:all .15s;}
.empty .ex span:hover{border-color:var(--violet);color:var(--violet);transform:translateY(-2px);}
@media (prefers-reduced-motion:reduce){
 .topbar,.m4-badge,.stage::before,.tab{animation:none!important;}
 .framewrap{transition:none!important;} .hero3d{transform:none!important;}
}
</style></head>
<body>
<div class="topbar">
  <div class="brand">📈 K-Market Dashboard 2<small>KOSPI·KOSDAQ</small><span class="m4-badge">🚀 M4 PRO · PRO QUANT</span></div>
  <form class="searchwrap" id="form" autocomplete="off">
    <input id="q" type="text" placeholder="주식·ETF 종목명 또는 6자리 코드 입력 (예: 삼성전자, 005930, KODEX 200)">
    <div class="sg" id="sg"></div>
  </form>
  <button class="btn" type="button" id="searchBtn">검색</button>
</div>
<div class="tabstrip" id="tabstrip"></div>
<div class="stage" id="stage">
  <div class="empty" id="empty">
    <div class="hero3d" id="hero3d">
      <div class="big">🔍</div>
      <h2>종목을 검색해 보세요</h2>
      <p>개별주식·ETF 종목명 또는 6자리 코드를 입력하면 새 탭으로 리포트가 열립니다.</p>
      <p class="tagline">🚀 "M4 퀀트 분석" 탭 — 리스크 지표·몬테카를로·3D 변동성/상관·CAPM·백테스트</p>
      <div class="ex">
        <span data-code="005930">삼성전자</span>
        <span data-code="000660">SK하이닉스</span>
        <span data-code="005380">현대차</span>
        <span data-code="069500">KODEX 200</span>
        <span data-code="133690">TIGER 미국나스닥100</span>
      </div>
    </div>
  </div>
</div>
<script>
var q=document.getElementById('q'),sg=document.getElementById('sg'),
    tabstrip=document.getElementById('tabstrip'),stage=document.getElementById('stage'),
    empty=document.getElementById('empty');
var tabs=[],active=null,seq=0,sgItems=[],sgActive=-1,tmr=null,dragId=null;
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
q.addEventListener('input',function(){clearTimeout(tmr);sgActive=-1;var v=q.value.trim();
  if(!v){hideSg();return;}tmr=setTimeout(function(){fetchSg(v);},180);});
q.addEventListener('keydown',function(e){
  if(!sg.classList.contains('show')){if(e.key==='Enter'){e.preventDefault();doSearch();}return;}
  var rows=sg.querySelectorAll('.sg-item');
  if(e.key==='ArrowDown'){e.preventDefault();sgActive=Math.min(sgActive+1,rows.length-1);paintSg(rows);}
  else if(e.key==='ArrowUp'){e.preventDefault();sgActive=Math.max(sgActive-1,0);paintSg(rows);}
  else if(e.key==='Enter'){e.preventDefault();if(sgActive>=0&&sgItems[sgActive])pick(sgItems[sgActive].code);else doSearch();}
  else if(e.key==='Escape'){hideSg();}});
document.addEventListener('click',function(e){if(!sg.contains(e.target)&&e.target!==q)hideSg();});
q.addEventListener('blur',function(){setTimeout(hideSg,150);});
q.addEventListener('focus',function(){var v=q.value.trim();if(v)fetchSg(v);});
document.getElementById('form').addEventListener('submit',function(e){e.preventDefault();doSearch();});
document.getElementById('searchBtn').addEventListener('click',doSearch);
function paintSg(rows){rows.forEach(function(r,i){r.classList.toggle('active',i===sgActive);});}
function hideSg(){sg.classList.remove('show');sg.innerHTML='';}
function fetchSg(v){fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
  sgItems=d||[];if(!sgItems.length){hideSg();return;}
  sg.innerHTML=sgItems.map(function(it){var cls=it.type==='ETF'?'etf':'stk';
    return '<div class="sg-item" data-code="'+esc(it.code)+'"><span class="sg-badge '+cls+'">'+it.type+'</span>'+
      '<span class="sg-code">'+esc(it.code)+'</span><span class="sg-name">'+esc(it.name)+'</span>'+
      '<span class="sg-extra">'+esc(it.extra||'')+'</span></div>';}).join('');
  sg.classList.add('show');}).catch(function(){hideSg();});}
sg.addEventListener('click',function(e){var it=e.target.closest('.sg-item');if(it)pick(it.dataset.code);});
function pick(code){q.value=code;hideSg();doSearch();}
function doSearch(){var v=q.value.trim();if(!v)return;hideSg();openTab(v);}
window.MI_TABS=true;
window.miOpenStockTab=function(code){if(code)openTab(String(code));};
function miPing(){fetch('/__ping').catch(function(){});}
miPing();setInterval(miPing,3000);
document.addEventListener('visibilitychange',function(){if(!document.hidden)miPing();});
window.addEventListener('pagehide',function(){try{navigator.sendBeacon('/__bye');}catch(e){}});
empty.querySelectorAll('.ex span').forEach(function(s){s.addEventListener('click',function(){pick(s.dataset.code);});});
var hero=document.getElementById('hero3d');
stage.addEventListener('mousemove',function(e){if(tabs.length)return;var r=stage.getBoundingClientRect();
  var rx=((e.clientY-r.top)/r.height-0.5)*-9,ry=((e.clientX-r.left)/r.width-0.5)*11;
  hero.style.transform='rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg)';});
stage.addEventListener('mouseleave',function(){hero.style.transform='';});
function openTab(query){var ex=tabs.find(function(t){return t.query===query;});
  if(ex){activate(ex.id);return;}var id='t'+(++seq);
  var wrap=document.createElement('div');wrap.className='framewrap';wrap.dataset.id=id;
  var ov=document.createElement('div');ov.className='overlay show';
  ov.innerHTML='<div class="spinner"></div><p>리포트를 생성하는 중…</p>';
  var f=document.createElement('iframe');f.className='frame';
  f.addEventListener('load',function(){ov.classList.remove('show');updateMeta(id,f);});
  f.src='/dashboard?q='+encodeURIComponent(query);
  wrap.appendChild(ov);wrap.appendChild(f);stage.appendChild(wrap);
  tabs.push({id:id,query:query,title:query,icon:'⏳'});activate(id);}
function updateMeta(id,f){var t=tabs.find(function(x){return x.id===id;});if(!t)return;
  var title='',kind='';
  try{title=(f.contentDocument&&f.contentDocument.title)||'';
    kind=(f.contentDocument&&f.contentDocument.documentElement.getAttribute('data-kind'))||'';}catch(e){}
  if(title)t.title=title;t.icon=(kind==='etf')?'📊':'📈';renderTabs();}
function activate(id){active=id;
  document.querySelectorAll('.framewrap').forEach(function(w){w.classList.toggle('show',w.dataset.id===id);});
  empty.style.display=tabs.length?'none':'flex';renderTabs();}
function closeTab(id){var i=tabs.findIndex(function(t){return t.id===id;});if(i<0)return;
  tabs.splice(i,1);var w=stage.querySelector('.framewrap[data-id="'+id+'"]');if(w)w.remove();
  if(active===id){active=tabs.length?tabs[Math.min(i,tabs.length-1)].id:null;}
  if(active)activate(active);else{empty.style.display='flex';renderTabs();}}
function renderTabs(){tabstrip.innerHTML=tabs.map(function(t){
  return '<div class="tab'+(t.id===active?' active':'')+(t.id===dragId?' dragging':'')+'" data-id="'+t.id+'">'+
    '<span class="tab-ic">'+(t.icon||'📈')+'</span><span class="tab-label" title="'+esc(t.title)+'">'+esc(t.title)+'</span>'+
    '<span class="tab-close" data-id="'+t.id+'">×</span></div>';}).join('');
  tabstrip.style.display=tabs.length?'flex':'none';}
tabstrip.addEventListener('click',function(e){var close=e.target.closest('.tab-close');
  if(close){e.stopPropagation();closeTab(close.dataset.id);}});
var dragMoved=false,startX=0;
tabstrip.addEventListener('mousedown',function(e){if(e.target.closest('.tab-close'))return;
  var tab=e.target.closest('.tab');if(!tab)return;dragId=tab.dataset.id;dragMoved=false;startX=e.clientX;
  e.preventDefault();document.addEventListener('mousemove',onTabMove);document.addEventListener('mouseup',onTabUp);});
function onTabMove(e){if(dragId===null)return;
  if(!dragMoved){if(Math.abs(e.clientX-startX)<5)return;dragMoved=true;
    var d=tabstrip.querySelector('.tab[data-id="'+dragId+'"]');if(d)d.classList.add('dragging');}
  var els=tabstrip.querySelectorAll('.tab'),over=null;
  for(var i=0;i<els.length;i++){var r=els[i].getBoundingClientRect();
    if(e.clientX>=r.left&&e.clientX<=r.right){over=els[i];break;}}
  if(!over||over.dataset.id===dragId)return;
  var from=tabs.findIndex(function(x){return x.id===dragId;}),to=tabs.findIndex(function(x){return x.id===over.dataset.id;});
  if(from<0||to<0)return;var m=tabs.splice(from,1)[0];tabs.splice(to,0,m);renderTabs();}
function onTabUp(){document.removeEventListener('mousemove',onTabMove);document.removeEventListener('mouseup',onTabUp);
  if(!dragMoved&&dragId!==null)activate(dragId);dragId=null;dragMoved=false;renderTabs();}
</script>
</body></html>
"""


def _open_browser():
    time.sleep(1.0)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception:  # noqa: BLE001
        pass


def _prewarm():
    if os.environ.get("MI_NO_PREWARM"):
        return
    time.sleep(6.0)
    for kind, code in (("stock", "005930"), ("etf", "069500")):
        _precompute(kind, code)


def main() -> None:
    print("=" * 60)
    print("  한국 증시·ETF 통합 대시보드 2 — M4 Pro · Pro Quant Edition")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 기본 탭 3D FX + M4 퀀트 데스크(리스크/3D 변동성·상관/CAPM)")
    print("  · 캐시: SSD parquet + RAM + 프리워밍 | 종료: 탭 닫기 / Ctrl+C")
    print("=" * 60)
    if not os.environ.get("MI_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    threading.Thread(target=_monitor_heartbeat, daemon=True).start()
    threading.Thread(target=_prewarm, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
