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
"""K-Market Dashboard 3 test realtime replay.

기존 파일을 수정하지 않고 `scripts/market_dashboard3_realtime.py`를 베이스로
가져온 뒤, 현재가 갱신만 "최근 거래일 장중 리플레이"로 바꾼 독립 실행 파일.

실행:
  uv run test_market_dashboard3_realtime.py
  MARKET_PORT=8782 uv run test_market_dashboard3_realtime.py

동작:
  - 검색/리포트/M4 퀀트 탭은 기존 대시보드 엔진을 그대로 사용한다.
  - `/api/replay?code=005930&offset=4500`이 최근 거래일의 09:00 기준
    offset 초 시점 가격을 반환한다.
  - 과거 분봉/틱이 아니라 최근 거래일 일봉 OHLC를 이용해 결정적으로 만든
    시연용 장중 경로다. 장마감/휴장일에도 같은 날짜의 장중처럼 움직인다.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from flask import Response, jsonify, request


ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import market_dashboard3_realtime as base  # noqa: E402


PORT = int(os.environ.get("MARKET_PORT", os.environ.get("REPLAY_MARKET_PORT", "8781")))
base.PORT = PORT
app = base.app

SESSION_START_HOUR = 9
SESSION_START_MINUTE = 0
SESSION_MINUTES = 390  # 09:00-15:30
SESSION_SECONDS = SESSION_MINUTES * 60
DEFAULT_START_MINUTE = max(0, min(int(os.environ.get("REPLAY_START_MINUTE", "75")), SESSION_MINUTES))  # 10:15
DEFAULT_SPEED = float(os.environ.get("REPLAY_SPEED", "45"))

_REPLAY_CACHE: dict[str, tuple[dict[str, Any], float]] = {}
_REPLAY_TTL = 60.0


def _num(v: Any, fallback: float | None = None) -> float | None:
    try:
        if v is None or v == "":
            return fallback
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return fallback


def _fmt_clock(offset_sec: float) -> str:
    offset_sec = max(0.0, min(float(offset_sec), float(SESSION_SECONDS)))
    total_min = int(offset_sec // 60)
    sec = int(offset_sec % 60)
    hour = SESSION_START_HOUR + (SESSION_START_MINUTE + total_min) // 60
    minute = (SESSION_START_MINUTE + total_min) % 60
    return f"{hour:02d}:{minute:02d}:{sec:02d}"


def _direction(change: float) -> str:
    if change > 0:
        return "▲"
    if change < 0:
        return "▼"
    return "-"


def _seed(code: str, session_date: str) -> int:
    h = hashlib.blake2s(f"{code}:{session_date}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big") & 0xFFFF_FFFF


def _smooth(a: float, b: float, x: np.ndarray) -> np.ndarray:
    z = x * x * (3 - 2 * x)
    return a + (b - a) * z


def _make_intraday_path(
    code: str,
    session_date: str,
    open_px: float,
    high_px: float,
    low_px: float,
    close_px: float,
) -> np.ndarray:
    """Build a deterministic 1-minute intraday path from a daily OHLC bar."""
    n = SESSION_MINUTES + 1
    rng = np.random.default_rng(_seed(code, session_date))

    high_px = max(high_px, open_px, close_px)
    low_px = min(low_px, open_px, close_px)
    spread = max(high_px - low_px, max(open_px, close_px) * 0.006, 1.0)

    if close_px >= open_px:
        t_low = int(rng.integers(18, 150))
        t_high = int(rng.integers(max(t_low + 25, 180), 374))
        anchors = [(0, open_px), (t_low, low_px), (t_high, high_px), (SESSION_MINUTES, close_px)]
    else:
        t_high = int(rng.integers(18, 150))
        t_low = int(rng.integers(max(t_high + 25, 180), 374))
        anchors = [(0, open_px), (t_high, high_px), (t_low, low_px), (SESSION_MINUTES, close_px)]

    path = np.zeros(n, dtype=float)
    for (t0, p0), (t1, p1) in zip(anchors, anchors[1:]):
        xs = np.linspace(0, 1, t1 - t0 + 1)
        path[t0:t1 + 1] = _smooth(p0, p1, xs)

    # Add small market-looking wiggle while preserving anchors and OHLC bounds.
    noise = rng.normal(0, 1, n).cumsum()
    bridge = noise - np.linspace(0, 1, n) * noise[-1]
    denom = max(float(np.nanstd(bridge)), 1e-9)
    bridge = bridge / denom * spread * 0.025
    wave = np.sin(np.linspace(0, 8.5 * np.pi, n) + rng.random() * np.pi) * spread * 0.018
    wiggle = bridge + wave

    anchor_idx = {t for t, _ in anchors}
    for i in range(n):
        if i not in anchor_idx:
            path[i] += wiggle[i]

    path = np.clip(path, low_px, high_px)
    path[0] = open_px
    path[-1] = close_px
    for t, p in anchors:
        path[t] = p
    return path


def _interp_path(path: np.ndarray, offset_sec: float) -> float:
    minute = max(0.0, min(float(offset_sec) / 60.0, float(SESSION_MINUTES)))
    lo = int(np.floor(minute))
    hi = min(lo + 1, SESSION_MINUTES)
    frac = minute - lo
    return float(path[lo] * (1 - frac) + path[hi] * frac)


async def _chart_rows(code: str, days: int = 45) -> list[dict]:
    return await base._afetch(code, days)


def _session_for_code(code: str) -> dict[str, Any]:
    """Return recent trading-day OHLC + generated path for a code."""
    now = time.time()
    cached = _REPLAY_CACHE.get(code)
    if cached and now - cached[1] < _REPLAY_TTL:
        return cached[0]

    rows = asyncio.run(_chart_rows(code))
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("차트 데이터를 찾을 수 없습니다.")
    df["일자"] = pd.to_datetime(df["일자"], errors="coerce")
    df = df.dropna(subset=["일자"]).sort_values("일자").reset_index(drop=True)
    if df.empty:
        raise RuntimeError("유효한 거래일이 없습니다.")

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last
    session_date = last["일자"].strftime("%Y-%m-%d")
    prev_close = _num(prev.get("종가"), _num(last.get("시가"), 0.0)) or 0.0
    close_px = _num(last.get("종가"), prev_close) or prev_close
    open_px = _num(last.get("시가"), prev_close) or prev_close
    high_px = _num(last.get("고가"), max(open_px, close_px)) or max(open_px, close_px)
    low_px = _num(last.get("저가"), min(open_px, close_px)) or min(open_px, close_px)
    volume = _num(last.get("거래량"), 0.0) or 0.0

    path = _make_intraday_path(code, session_date, open_px, high_px, low_px, close_px)
    data = {
        "code": code,
        "session_date": session_date,
        "prev_close": prev_close,
        "open": open_px,
        "high": high_px,
        "low": low_px,
        "close": close_px,
        "volume": volume,
        "path": path,
    }
    _REPLAY_CACHE[code] = (data, now)
    return data


def _replay_payload(code: str, offset_sec: float) -> dict[str, Any]:
    if not (code and code.isdigit() and len(code) == 6):
        return {"ok": False, "msg": "invalid code"}
    try:
        s = _session_for_code(code)
        price = _interp_path(s["path"], offset_sec)
        change = price - float(s["prev_close"])
        pct = (change / float(s["prev_close"]) * 100.0) if s["prev_close"] else 0.0
        return {
            "ok": True,
            "mode": "replay",
            "code": code,
            "price": round(price, 0),
            "change": round(change, 0),
            "change_pct": round(pct, 2),
            "direction": _direction(change),
            "session_date": s["session_date"],
            "clock": _fmt_clock(offset_sec),
            "offset": max(0, min(float(offset_sec), float(SESSION_SECONDS))),
            "open": s["open"],
            "high": s["high"],
            "low": s["low"],
            "close": s["close"],
            "prev_close": s["prev_close"],
            "source": "Naver daily OHLC replay",
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "msg": str(e)}


_REPLAY_STYLE = """<style>
.rp-panel{position:fixed;right:18px;bottom:18px;z-index:9999;width:min(390px,calc(100vw - 32px));
 background:rgba(11,15,32,.92);color:#e9eefb;border:1px solid rgba(154,169,205,.26);
 border-radius:12px;box-shadow:0 18px 44px rgba(0,0,0,.28);backdrop-filter:blur(10px);
 padding:12px 13px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;}
.rp-head{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:800;letter-spacing:.01em;}
.rp-dot{width:8px;height:8px;border-radius:50%;background:#36c6ff;box-shadow:0 0 0 0 rgba(54,198,255,.65);
 animation:rpPulse 1.8s ease-in-out infinite;flex:none;}
@keyframes rpPulse{0%,100%{box-shadow:0 0 0 0 rgba(54,198,255,.55)}50%{box-shadow:0 0 14px 4px rgba(54,198,255,0)}}
.rp-date{margin-left:auto;color:#9fb4ff;font-variant-numeric:tabular-nums;}
.rp-sub{margin-top:4px;color:#aeb9d5;font-size:11.5px;line-height:1.4;}
.rp-row{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;margin-top:10px;}
.rp-btn{height:30px;min-width:64px;border:1px solid rgba(255,255,255,.18);border-radius:8px;
 background:rgba(255,255,255,.08);color:#fff;font-weight:800;cursor:pointer;}
.rp-btn:hover{background:rgba(255,255,255,.14);}
.rp-range{width:100%;accent-color:#36c6ff;}
.rp-clock{font-size:18px;font-weight:900;color:#fff;font-variant-numeric:tabular-nums;min-width:78px;text-align:right;}
.rp-speed{height:30px;border:1px solid rgba(255,255,255,.18);border-radius:8px;background:#151b34;color:#fff;font-weight:700;}
.rp-mini{display:flex;align-items:center;justify-content:space-between;margin-top:8px;color:#8490ad;font-size:11px;}
.price-hero .rt-live.rp-live{background:rgba(54,198,255,.12);border-color:rgba(54,198,255,.35);color:#36c6ff;}
.ph-price .rt-ch,.ph-chg .rt-ch{display:inline-block;vertical-align:top;font-variant-numeric:tabular-nums;}
.ph-price .rt-col,.ph-chg .rt-col{display:block;will-change:transform;}
@media (max-width:720px){.rp-panel{left:12px;right:12px;bottom:12px;width:auto;}.rp-sub{display:none;}}
@media (prefers-reduced-motion:reduce){.rp-dot{animation:none!important;}}
</style>"""


_REPLAY_JS = """<script>
(function(){
 var CODE='__CODE__';
 if(!CODE)return;
 var SESSION_SECONDS=__SESSION_SECONDS__, START_MINUTE=__START_MINUTE__, DEFAULT_SPEED=__DEFAULT_SPEED__;
 var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 var EASE='cubic-bezier(.16,1,.3,1)',DUR=0.62;
 var lastPrice=null,lastText=null,lastChgText=null,lastTick=Date.now();
 var offset=START_MINUTE*60, speed=DEFAULT_SPEED, playing=true;
 function fmt(n){return Number(n).toLocaleString('en-US',{maximumFractionDigits:0});}
 function priceEl(){return document.querySelector('.price-hero .ph-price');}
 function etfKpiVal(){
   var ks=document.querySelectorAll('.etf-head .eh-kpi'),i;
   for(i=0;i<ks.length;i++){var l=ks[i].querySelector('.k-label');
     if(l&&/현재가/.test(l.textContent)){return ks[i].querySelector('.k-val');}}
   return null;}
 function staticCell(h,ch){var c=document.createElement('span');c.className='rt-ch';
   c.style.height=h+'px';c.style.lineHeight=h+'px';c.textContent=ch;return c;}
 function rollCell(h,oldCh,newCh,up,delay){
   var cell=document.createElement('span');cell.className='rt-ch';cell.style.height=h+'px';cell.style.overflow='hidden';
   var col=document.createElement('span');col.className='rt-col';
   function d(t){var s=document.createElement('span');s.style.display='block';s.style.height=h+'px';s.style.lineHeight=h+'px';s.textContent=t;return s;}
   if(up){col.appendChild(d(oldCh));col.appendChild(d(newCh));col.style.transform='translateY(0)';}
   else{col.appendChild(d(newCh));col.appendChild(d(oldCh));col.style.transform='translateY(-'+h+'px)';}
   cell.appendChild(col);
   requestAnimationFrame(function(){requestAnimationFrame(function(){
     col.style.transition='transform '+DUR+'s '+EASE+' '+delay+'ms';
     col.style.transform=up?'translateY(-'+h+'px)':'translateY(0)';});});
   return cell;}
 function rollPrice(pe,oldStr,newStr,up){
   if(RM||!oldStr||oldStr===newStr){pe.textContent=newStr;return;}
   var h=pe.offsetHeight||42,nL=newStr.length,oL=oldStr.length,frag=document.createDocumentFragment(),p,r,nc,oc;
   for(p=0;p<nL;p++){
     r=nL-1-p;nc=newStr.charAt(p);oc=(r<oL)?oldStr.charAt(oL-1-r):'';
     if(oc===nc)frag.appendChild(staticCell(h,nc));else frag.appendChild(rollCell(h,oc,nc,up,Math.min(r,8)*26));
   }
   pe.textContent='';pe.appendChild(frag);}
 function ensurePanel(){
   if(document.getElementById('rpPanel'))return;
   var p=document.createElement('div');p.className='rp-panel';p.id='rpPanel';
   p.innerHTML='<div class="rp-head"><span class="rp-dot"></span><span>장중 리플레이</span><span class="rp-date" id="rpDate">최근 거래일</span></div>'+
     '<div class="rp-sub">최근 거래일 일봉 OHLC 기반 시연 경로입니다. 장마감 후에도 장중 움직임을 보여줍니다.</div>'+
     '<div class="rp-row"><button class="rp-btn" id="rpPlay">일시정지</button><input class="rp-range" id="rpRange" type="range" min="0" max="'+SESSION_SECONDS+'" step="30"><span class="rp-clock" id="rpClock">10:15:00</span></div>'+
     '<div class="rp-mini"><span>09:00</span><select class="rp-speed" id="rpSpeed"><option value="15">15x</option><option value="45" selected>45x</option><option value="120">120x</option><option value="300">300x</option></select><span>15:30</span></div>';
   document.body.appendChild(p);
   document.getElementById('rpRange').value=String(offset);
   document.getElementById('rpPlay').addEventListener('click',function(){
     playing=!playing;this.textContent=playing?'일시정지':'재생';lastTick=Date.now();});
   document.getElementById('rpRange').addEventListener('input',function(){offset=Number(this.value)||0;playing=false;document.getElementById('rpPlay').textContent='재생';poll(true);});
   document.getElementById('rpSpeed').addEventListener('change',function(){speed=Number(this.value)||DEFAULT_SPEED;lastTick=Date.now();});
 }
 function tag(){
   var top=document.querySelector('.price-hero .ph-top');
   if(top&&!top.querySelector('.rt-live')){
     var s=document.createElement('span');s.className='rt-live rp-live';s.innerHTML='<span class="rt-dot"></span>리플레이';top.appendChild(s);}
 }
 function setHero(d){
   var pe=priceEl();if(!pe)return;
   var txt=fmt(d.price)+'원';
   var prev=(lastText!==null)?lastText:(pe.textContent||'').trim();
   var up=(lastPrice!==null)?(d.price>lastPrice):(d.direction==='▲');
   if(prev!==txt){rollPrice(pe,prev,txt,up);}
   lastPrice=d.price;lastText=txt;pe.__cu=1;
   var box=document.querySelector('.price-hero');
   if(box){box.classList.remove('up','down','flat');box.classList.add(d.direction==='▲'?'up':(d.direction==='▼'?'down':'flat'));}
   var chg=document.querySelector('.price-hero .ph-chg');
   if(chg){var sign=d.change>0?'+':'';var newChgTxt=d.direction+' '+sign+fmt(d.change)+'원 ('+(d.change_pct>0?'+':'')+Number(d.change_pct).toFixed(2)+'%)';
     if(newChgTxt!==lastChgText){rollPrice(chg,lastChgText||'',newChgTxt,up);}lastChgText=newChgTxt;}
   var meta=document.querySelector('.price-hero .ph-meta');
   if(meta){meta.textContent='장중 리플레이 · '+d.session_date+' '+d.clock+' · OHLC 기반 시연';}
   var kv=etfKpiVal();
   if(kv){var unit=kv.querySelector('.k-unit');kv.textContent=fmt(d.price);if(unit)kv.appendChild(unit);else kv.insertAdjacentHTML('beforeend','<span class="k-unit">원</span>');kv.__cu=1;}
   var rd=document.getElementById('rpDate'),rc=document.getElementById('rpClock'),rr=document.getElementById('rpRange');
   if(rd)rd.textContent=d.session_date;if(rc)rc.textContent=d.clock;if(rr&&!rr.matches(':focus'))rr.value=String(Math.round(d.offset||offset));
 }
 function advance(){
   var now=Date.now(),dt=(now-lastTick)/1000;lastTick=now;
   if(playing){offset+=dt*speed;if(offset>SESSION_SECONDS)offset=0;}
 }
 var busy=false;
 function poll(force){
   if(busy||(!force&&document.hidden))return;
   advance();busy=true;
   fetch('/api/replay?code='+encodeURIComponent(CODE)+'&offset='+encodeURIComponent(offset),{cache:'no-store'})
     .then(function(r){return r.json();})
     .then(function(d){if(d&&d.ok){tag();setHero(d);}})
     .catch(function(){})
     .finally(function(){busy=false;});
 }
 ensurePanel();
 setTimeout(function(){poll(true);setInterval(function(){poll(false);},900);},1050);
})();</script>"""


def _inject_replay(html_doc: str, code: str | None) -> str:
    if not code or "</body>" not in html_doc:
        return html_doc
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _REPLAY_STYLE + "</head>", 1)
    js = (_REPLAY_JS
          .replace("__CODE__", code)
          .replace("__SESSION_SECONDS__", str(SESSION_SECONDS))
          .replace("__START_MINUTE__", str(DEFAULT_START_MINUTE))
          .replace("__DEFAULT_SPEED__", str(DEFAULT_SPEED)))
    return html_doc.replace("</body>", js + "</body>", 1)


@app.get("/api/replay")
def api_replay() -> Response:
    code = (request.args.get("code") or "").strip()
    offset = _num(request.args.get("offset"), DEFAULT_START_MINUTE * 60) or 0.0
    return jsonify(_replay_payload(code, offset))


def api_index_replay() -> Response:
    """Landing ticker replay. Uses KODEX 200 as a market proxy and scales it."""
    offset = (DEFAULT_START_MINUTE * 60 + time.time() * DEFAULT_SPEED) % SESSION_SECONDS
    d = _replay_payload("069500", offset)
    if not d.get("ok"):
        t = time.time()
        value = 2800 + np.sin(t / 9.0) * 7 + np.sin(t / 23.0) * 4
        change = value - 2800
        return jsonify({
            "ok": True, "code": "0001", "name": "KOSPI", "value": round(value, 2),
            "change": round(change, 2), "change_pct": round(change / 2800 * 100, 2),
            "direction": _direction(change), "mode": "replay",
        })
    # KODEX 200 price -> KOSPI-looking display value. It is only a topbar demo ticker.
    value = float(d["price"]) / 13.0
    prev = float(d["prev_close"]) / 13.0
    change = value - prev
    return jsonify({
        "ok": True,
        "code": "0001",
        "name": "KOSPI",
        "value": round(value, 2),
        "change": round(change, 2),
        "change_pct": round((change / prev * 100.0) if prev else 0.0, 2),
        "direction": _direction(change),
        "mode": "replay",
        "session_date": d.get("session_date"),
        "clock": d.get("clock"),
    })


def index_replay() -> Response:
    html = base._LANDING_HTML
    html = html.replace("K-Market Dashboard 2", "K-Market Dashboard 3 Replay")
    html = html.replace("실시간 지수 · 한국투자증권 KIS", "장중 리플레이 지수")
    html = html.replace("KOSPI 실시간 지수", "KOSPI 장중 리플레이")
    html = html.replace("KOSPI·KOSDAQ", "Replay Demo")
    return Response(html, mimetype="text/html")


def _patch_base_app() -> None:
    # Existing /dashboard calls base._inject_realtime. Repoint that hook to replay.
    base._inject_realtime = _inject_replay
    # Override existing landing and index endpoint view functions without re-registering routes.
    app.view_functions["index"] = index_replay
    app.view_functions["api_index"] = api_index_replay


def _open_browser() -> None:
    time.sleep(1.0)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception:  # noqa: BLE001
        pass


def _prewarm_replay() -> None:
    if os.environ.get("MI_NO_PREWARM"):
        return
    time.sleep(4.0)
    for code in ("005930", "069500"):
        try:
            _session_for_code(code)
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    _patch_base_app()
    print("=" * 68)
    print("  한국 증시·ETF 통합 대시보드 3 — 장중 리플레이 테스트")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 기존 파일 불변: scripts/market_dashboard3_realtime.py 엔진을 import만 합니다.")
    print("  · 현재가: 최근 거래일 OHLC 기반 09:00-15:30 리플레이")
    print("  · 리포트 안 패널: 재생/일시정지 · 시각 슬라이더 · 속도 선택")
    print("=" * 68)
    if not os.environ.get("MI_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    threading.Thread(target=base._monitor_heartbeat, daemon=True).start()
    threading.Thread(target=_prewarm_replay, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
