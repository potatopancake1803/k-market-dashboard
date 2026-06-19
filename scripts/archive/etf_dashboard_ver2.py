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
# ]
# ///
"""한국 ETF 리포트 (웹 버전) — 브라우저에서 ETF를 검색해 대시보드를 본다.

  uv run etf_dashboard_ver2.py
    → 로컬 서버가 뜨고 브라우저가 자동으로 열린다.
    → 상단 검색창에 ETF 종목명/코드를 입력(자동완성 지원)하면
       하단에 인터랙티브 대시보드(개요·차트·투자자 매매동향·섹터 비중 등)가 뜬다.

CLI 버전(etf_dashboard.py)의 데이터 수집·렌더링 로직을 그대로 재사용한다.
KRX ETF 스냅샷은 메모리에 캐시(기본 1시간)해 검색마다 재다운로드하지 않는다.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import time
import webbrowser
from datetime import date

import pandas as pd
from flask import Flask, Response, jsonify, request

# ── CLI 버전과 공용 모듈 재사용 ────────────────────────────────────
import etf_dashboard as base  # add_detail_tab, ETF_LOOKBACK 등 재사용

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from market_intel.analyze import etf as E
from market_intel.collectors import kis
from market_intel.collectors import naver
from market_intel.collectors.krx import KRXCollector
from market_intel.config import business_days, load_settings
from market_intel.httpx_client import Fetcher
from market_intel.report import dashboard as D

PORT = int(os.environ.get("ETF_PORT", "8765"))
app = Flask(__name__)

# ── KRX ETF 스냅샷 메모리 캐시 (검색마다 재수집 방지) ─────────────────
_mkt: dict = {"snap": None, "df": None, "last_date": "", "ts": 0.0}
_mkt_lock = threading.Lock()


async def _async_market(settings):
    """KRX ETF 일별매매정보 → 최신 스냅샷(snap)·원본 프레임(df)·기준일."""
    async with Fetcher() as f:
        krx = KRXCollector(f, settings.krx_key)
        df = await krx.fetch_market_frame("etf", business_days(date.today(), base.ETF_LOOKBACK))
        if df.is_empty():
            return df, pd.DataFrame(), ""
        snap, last_date = E.latest_snapshot(df)
        return df, snap, last_date


def get_market(max_age: float = 3600.0):
    """캐시된 (df, snap, last_date) 반환. 만료 시 1회 재수집(스레드 직렬화)."""
    settings = load_settings()
    with _mkt_lock:
        if _mkt["snap"] is not None and (time.time() - _mkt["ts"]) < max_age:
            return _mkt["df"], _mkt["snap"], _mkt["last_date"]
        df, snap, last_date = asyncio.run(_async_market(settings))
        _mkt.update(df=df, snap=snap, last_date=last_date, ts=time.time())
        return df, snap, last_date


async def _async_etf(code: str):
    """네이버 실시간 시세·ETF 분석·차트·투자자 매매동향·구성종목 시세를 병렬 수집.

    KIS NAV(작업1)·KIS 매매동향(작업4)도 병렬 수집 — rt["kis_nav"] 로 전달,
    매매동향은 KIS 우선(시간제한·실패 시 네이버 폴백).
    """
    async with Fetcher() as f:
        rt, an, chart_rows, trend, kis_nav, kis_trend = await asyncio.gather(
            naver.fetch_realtime_price(f, code),
            naver.fetch_etf_analysis(f, code),
            naver.fetch_price_chart(f, code, days=1900),
            naver.fetch_investor_trend(f, code, days=30),
            kis.fetch_etf_nav(code),
            kis.fetch_investor_trend(code, days=30))
        if kis_nav:
            (rt := rt or {})["kis_nav"] = kis_nav
        if kis_trend:
            trend = kis_trend
        con_codes = [str(it.get("종목코드")) for it in (an.get("top10") or []) if it.get("종목코드")]
        quotes = await naver.fetch_realtime_quotes(f, con_codes) if con_codes else {}
        return rt, an, chart_rows, quotes, trend


def _dash_to_html(dash: D.Dashboard) -> str:
    """Dashboard 를 HTML 문자열로 렌더(임시 파일 경유)."""
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        dash.render(path)
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def build_dashboard_html(query: str) -> tuple[str | None, str | None]:
    """검색어로 ETF 대시보드 HTML 생성. 반환: (html, error_message)."""
    df, snap, last_date = get_market()
    if snap is None or snap.empty:
        return None, "KRX ETF 데이터를 불러오지 못했습니다. (KRX_KEY/네트워크 확인)"
    row = E.find_etf(snap, query)
    if row is None:
        return None, f"'{query}' 에 해당하는 ETF를 찾지 못했습니다. (종목명 또는 6자리 코드로 입력)"

    code = str(row["코드"])
    rt, an, chart_rows, quotes, trend = asyncio.run(_async_etf(code))
    chart = pd.DataFrame(chart_rows)
    ds = E.detail_series(df, code)

    # ── 가격 기준일 보정: KRX(지연) 대신 더 최신인 네이버 차트 최종일로 표시값 갱신
    price_date = last_date
    if not chart.empty and "일자" in chart.columns:
        naver_date = str(chart["일자"].iloc[-1])
        if naver_date > (last_date or ""):
            price_date = naver_date
            row = row.copy()
            last_bar = chart.iloc[-1]
            cur_c = pd.to_numeric(last_bar.get("종가"), errors="coerce")
            if pd.notna(cur_c):
                row["종가"] = float(cur_c)
            if "거래량" in chart.columns and pd.notna(last_bar.get("거래량")):
                row["거래량"] = float(last_bar["거래량"])
            if len(chart) >= 2:
                prev_c = pd.to_numeric(chart["종가"].iloc[-2], errors="coerce")
                if pd.notna(prev_c) and prev_c and pd.notna(cur_c):
                    row["등락률(%)"] = round((cur_c - prev_c) / prev_c * 100, 2)

    dash = D.Dashboard(f"{row['종목명']} ({code})",
                       f"기준일 {price_date} · {row.get('운용사', '')}", kind="etf")
    base.add_detail_tab(dash, row, rt, an, quotes, chart, ds, last_date, trend, price_date)
    return _dash_to_html(dash), None


# ═══════════════════════════════════════════════════════════
# 라우트
# ═══════════════════════════════════════════════════════════
@app.get("/")
def index() -> Response:
    return Response(_LANDING_HTML, mimetype="text/html")


@app.get("/suggest")
def suggest():
    """검색 자동완성 — 종목명/코드 부분일치 상위 12건(거래대금 순)."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    try:
        _df, snap, _ld = get_market()
    except Exception:  # noqa: BLE001
        return jsonify([])
    if snap is None or snap.empty:
        return jsonify([])
    codes = snap["코드"].astype(str)
    mask = (snap["종목명"].str.contains(q, case=False, na=False, regex=False)
            | codes.str.upper().str.contains(q.upper(), regex=False))
    hit = snap[mask].sort_values("거래대금(억)", ascending=False).head(12)
    out = [{"code": str(r["코드"]), "name": str(r["종목명"]),
            "extra": f"{r.get('운용사', '')} · {r.get('기초지수', '') or '-'}"}
           for _, r in hit.iterrows()]
    return jsonify(out)


@app.get("/dashboard")
def dashboard() -> Response:
    q = (request.args.get("q") or "").strip()
    if not q:
        return Response(_error_html("검색어를 입력하세요."), mimetype="text/html")
    try:
        html, err = build_dashboard_html(q)
    except Exception as e:  # noqa: BLE001
        return Response(_error_html(f"오류가 발생했습니다: {e}"), mimetype="text/html")
    if err:
        return Response(_error_html(err), mimetype="text/html")
    return Response(html, mimetype="text/html")


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


# ═══════════════════════════════════════════════════════════
# 랜딩 페이지 (검색창 + 결과 iframe)
# ═══════════════════════════════════════════════════════════
_LANDING_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>한국 ETF 리포트</title>
<style>
:root{--navy:#1F3864;--blue:#2E75B6;--bg:#f4f6fb;--line:#e3e8f0;}
*{box-sizing:border-box;}
html,body{margin:0;height:100%;}
body{display:flex;flex-direction:column;background:var(--bg);
 font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','Apple SD Gothic Neo',sans-serif;color:#1a1a2e;}
.topbar{background:linear-gradient(135deg,var(--navy),var(--blue));color:#fff;
 padding:16px 24px;display:flex;align-items:center;gap:18px;box-shadow:0 2px 8px rgba(20,40,80,.12);z-index:20;}
.topbar .brand{font-size:18px;font-weight:800;white-space:nowrap;}
.topbar .brand small{font-weight:500;opacity:.8;font-size:12px;margin-left:6px;}
.searchwrap{position:relative;flex:1;max-width:620px;}
#q{width:100%;padding:12px 16px;font-size:15px;border:0;border-radius:10px;
 box-shadow:0 1px 3px rgba(0,0,0,.15);outline:none;}
#q::placeholder{color:#9aa3b2;}
.sg{position:absolute;top:48px;left:0;right:0;background:#fff;border:1px solid var(--line);
 border-radius:10px;box-shadow:0 8px 24px rgba(20,40,80,.14);overflow:hidden;display:none;z-index:30;max-height:380px;overflow-y:auto;}
.sg.show{display:block;}
.sg-item{padding:11px 16px;cursor:pointer;border-bottom:1px solid #f0f3f8;display:flex;align-items:baseline;gap:10px;}
.sg-item:last-child{border-bottom:0;}
.sg-item:hover,.sg-item.active{background:#eef5ff;}
.sg-code{font-weight:700;color:var(--blue);font-size:13px;font-variant-numeric:tabular-nums;min-width:64px;}
.sg-name{font-weight:700;color:#15233f;font-size:14.5px;}
.sg-extra{margin-left:auto;color:#9aa3b2;font-size:12px;white-space:nowrap;}
.btn{background:#fff;color:var(--navy);border:0;border-radius:10px;padding:12px 22px;
 font-size:15px;font-weight:700;cursor:pointer;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.btn:hover{background:#f0f4fb;}
.stage{flex:1;position:relative;}
#frame{width:100%;height:100%;border:0;background:#fff;display:none;}
.empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 color:#8a93a6;text-align:center;padding:24px;}
.empty .big{font-size:54px;margin-bottom:14px;}
.empty h2{margin:0 0 8px;color:#1F3864;font-size:22px;font-weight:800;}
.empty p{margin:2px 0;font-size:14.5px;}
.empty .ex{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;}
.empty .ex span{background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 14px;
 font-size:13px;color:#33415c;cursor:pointer;font-weight:600;}
.empty .ex span:hover{border-color:var(--blue);color:var(--blue);}
.overlay{position:absolute;inset:0;background:rgba(244,246,251,.86);display:none;
 align-items:center;justify-content:center;flex-direction:column;gap:16px;z-index:10;}
.overlay.show{display:flex;}
.spinner{width:42px;height:42px;border:4px solid #d4ddec;border-top-color:var(--blue);
 border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.overlay p{color:#5b6b86;font-weight:600;font-size:14px;}
</style></head>
<body>
<div class="topbar">
  <div class="brand">📊 한국 ETF 리포트<small>KRX · 네이버 금융</small></div>
  <form class="searchwrap" id="form" autocomplete="off" onsubmit="return doSearch();">
    <input id="q" type="text" placeholder="ETF 종목명 또는 6자리 코드 입력 (예: KODEX 200, 069500, TIGER 미국나스닥100)">
    <div class="sg" id="sg"></div>
  </form>
  <button class="btn" type="button" onclick="doSearch()">검색</button>
</div>
<div class="stage">
  <iframe id="frame" title="ETF 대시보드"></iframe>
  <div class="empty" id="empty">
    <div class="big">🔍</div>
    <h2>ETF를 검색해 보세요</h2>
    <p>종목명 또는 6자리 코드를 입력하면 상세 리포트가 아래에 표시됩니다.</p>
    <p>개요 · 캔들차트 · 투자자별 매매 동향 · 섹터/자산 비중</p>
    <div class="ex">
      <span onclick="pick('069500')">KODEX 200</span>
      <span onclick="pick('360750')">TIGER 미국S&amp;P500</span>
      <span onclick="pick('133690')">TIGER 미국나스닥100</span>
      <span onclick="pick('396500')">TIGER 2차전지</span>
    </div>
  </div>
  <div class="overlay" id="overlay"><div class="spinner"></div><p>데이터를 수집하고 리포트를 생성하는 중…</p></div>
</div>
<script>
var q=document.getElementById('q'),sg=document.getElementById('sg'),
    frame=document.getElementById('frame'),overlay=document.getElementById('overlay'),
    empty=document.getElementById('empty');
var tmr=null,items=[],active=-1;

q.addEventListener('input',function(){
  clearTimeout(tmr); active=-1;
  var v=q.value.trim();
  if(!v){hideSg();return;}
  tmr=setTimeout(function(){fetchSg(v);},180);
});
q.addEventListener('keydown',function(e){
  if(!sg.classList.contains('show'))return;
  var rows=sg.querySelectorAll('.sg-item');
  if(e.key==='ArrowDown'){e.preventDefault();active=Math.min(active+1,rows.length-1);paint(rows);}
  else if(e.key==='ArrowUp'){e.preventDefault();active=Math.max(active-1,0);paint(rows);}
  else if(e.key==='Enter'){if(active>=0&&items[active]){e.preventDefault();pick(items[active].code);}}
  else if(e.key==='Escape'){hideSg();}
});
document.addEventListener('click',function(e){if(!sg.contains(e.target)&&e.target!==q)hideSg();});

function paint(rows){rows.forEach(function(r,i){r.classList.toggle('active',i===active);});}
function hideSg(){sg.classList.remove('show');sg.innerHTML='';}
function fetchSg(v){
  fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
    items=d||[];
    if(!items.length){hideSg();return;}
    sg.innerHTML=items.map(function(it){
      return '<div class="sg-item" onclick="pick(\\''+it.code+'\\')">'+
        '<span class="sg-code">'+it.code+'</span>'+
        '<span class="sg-name">'+it.name+'</span>'+
        '<span class="sg-extra">'+(it.extra||'')+'</span></div>';
    }).join('');
    sg.classList.add('show');
  }).catch(function(){hideSg();});
}
function pick(code){q.value=code;hideSg();doSearch();}
function doSearch(){
  var v=q.value.trim();
  if(!v)return false;
  hideSg();
  empty.style.display='none';
  frame.style.display='block';
  overlay.classList.add('show');
  frame.src='/dashboard?q='+encodeURIComponent(v);
  return false;
}
frame.addEventListener('load',function(){
  if(frame.src)overlay.classList.remove('show');
});
</script>
</body></html>
"""


def _open_browser():
    time.sleep(1.0)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    print("=" * 60)
    print("  한국 ETF 리포트 (웹 버전)")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 종료: Ctrl + C")
    print("=" * 60)
    if not os.environ.get("ETF_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
