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
"""K-Market Dashboard (ver6) (market_dashboard.py).

  uv run market_dashboard.py
    → 로컬 서버가 뜨고 브라우저가 자동으로 열린다.
    → 상단 검색창에 개별주식/ETF 종목명·코드를 입력(자동완성)하면
       · 개별주식  → company_report_ver2 의 종목 리포트
       · ETF       → etf_dashboard_ver2 의 ETF 리포트
       로 판별·렌더된다.
    → 각 검색 결과는 크롬 스타일 '탭'으로 열린다(검색창 바로 아래).
       탭은 닫을 수 있고, 드래그로 순서를 바꿀 수 있다.

기존 두 대시보드(company_report_ver2 / etf_dashboard_ver2)의 빌드·캐시 로직을
그대로 재사용하고, 라우팅·탭 UI만 새로 얹은 통합 진입점이다.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import webbrowser

import httpx
from flask import Flask, Response, jsonify, request

# 기존 두 대시보드 모듈 재사용 (각자의 빌드 함수·메모리 캐시 그대로 활용)
from archive import company_report_ver2 as company   # build_company_html, get_corps, dart_c
from archive import etf_dashboard_ver2 as etf         # build_dashboard_html, get_market, E

PORT = int(os.environ.get("MARKET_PORT", "8770"))
app = Flask(__name__)


# ════════════════ 주식 / ETF 판별 ════════════════
def detect_type(query: str) -> str:
    """검색어가 ETF인지 개별주식인지 판별. 'etf' 또는 'stock'."""
    q = query.strip()
    try:
        _df, snap, _ld = etf.get_market()
    except Exception:  # noqa: BLE001
        snap = None
    etf_codes = (set(snap["코드"].astype(str)) if (snap is not None and not snap.empty) else set())

    if q.isdigit() and len(q) == 6:
        return "etf" if q in etf_codes else "stock"
    # 이름 정확일치: ETF 우선 → 주식
    if snap is not None and not snap.empty and (snap["종목명"].astype(str).str.strip() == q).any():
        return "etf"
    try:
        corps = company.get_corps()
        if any(c.get("corp_name") == q and c.get("stock_code") for c in corps):
            return "stock"
    except Exception:  # noqa: BLE001
        pass
    # 부분일치 보조 판정 (ETF 스냅샷에서 매칭되면 ETF)
    if snap is not None and not snap.empty:
        try:
            if etf.E.find_etf(snap, q) is not None:
                return "etf"
        except Exception:  # noqa: BLE001
            pass
    return "stock"


# ════════════════ 라우트 ════════════════
@app.get("/")
def index() -> Response:
    return Response(_LANDING_HTML, mimetype="text/html")


@app.get("/suggest")
def suggest():
    """주식 + ETF 통합 자동완성 — 각 항목에 type 표시."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    out: list[dict] = []

    # 1) 개별주식 (DART 기업목록)
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

    # 2) ETF (KRX 스냅샷)
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
        kind = detect_type(q)
        if kind == "etf":
            html, err = etf.build_dashboard_html(q)
        else:
            html, err = company.build_company_html(q)
    except Exception as e:  # noqa: BLE001
        return Response(_error_html(f"오류가 발생했습니다: {e}"), mimetype="text/html")
    if err:
        return Response(_error_html(err), mimetype="text/html")
    return Response(html, mimetype="text/html")


@app.get("/report_pdf")
def report_pdf() -> Response:
    """네이버 리서치 리포트 PDF를 프록시해 대시보드 내 팝업(iframe)에서 표시."""
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


# ════════════════ 브라우저 종료 시 자동 종료 ════════════════
#  - pagehide(탭 닫힘/이동) 시 beacon(/__bye) → 3초 내 새 핑 없으면 종료(새로고침은 재핑되어 유지)
#  - 폴백: 핑이 _PING_TIMEOUT 동안 끊기면 종료
_last_ping = {"t": 0.0, "seen": False}
_bye = {"t": 0.0}
_PING_TIMEOUT = 15.0


@app.get("/__ping")
def __ping() -> Response:
    _last_ping["t"] = time.time()
    _last_ping["seen"] = True
    _bye["t"] = 0.0   # 살아있음 → 종료 예약 취소
    return Response("ok", mimetype="text/plain")


@app.post("/__bye")
@app.get("/__bye")
def __bye() -> Response:
    _bye["t"] = time.time()
    return Response("bye", mimetype="text/plain")


def _close_terminal() -> None:
    """(macOS) 이 프로세스를 실행 중인 터미널 창을 닫는다. 베스트에포트."""
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
    scpt = ('tell application "Terminal"\n'
            ' repeat with w in windows\n'
            '  repeat with t in tabs of w\n'
            f'   if tty of t is "{tty}" then close w saving no\n'
            '  end repeat\n'
            ' end repeat\n'
            'end tell')
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


# ════════════════ 랜딩 페이지 (검색창 + 탭 + iframe) ════════════════
_LANDING_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>K-Market Dashboard</title>
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
 border-radius:10px;box-shadow:0 8px 24px rgba(20,40,80,.14);overflow:hidden;display:none;z-index:30;max-height:420px;overflow-y:auto;}
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
 font-size:15px;font-weight:700;cursor:pointer;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.btn:hover{background:#f0f4fb;}
/* 크롬 스타일 탭바 (검색창 바로 아래) */
.tabstrip{display:none;align-items:flex-end;gap:5px;background:#d7deea;padding:8px 10px 0;overflow-x:auto;}
.tab{display:flex;align-items:center;gap:7px;background:#eaeef4;border:1px solid var(--line);border-bottom:0;
 border-radius:11px 11px 0 0;padding:9px 11px;max-width:240px;cursor:pointer;color:#5b6b86;font-size:13px;font-weight:600;
 white-space:nowrap;user-select:none;transition:background .12s;}
.tab:hover{background:#f1f4f9;}
.tab.active{background:#fff;color:#15233f;box-shadow:0 -1px 3px rgba(20,40,80,.05);}
.tab-ic{font-size:13px;flex:none;}
.tab-label{overflow:hidden;text-overflow:ellipsis;max-width:165px;}
.tab-close{border-radius:50%;width:18px;height:18px;line-height:17px;text-align:center;color:#9aa3b2;font-size:15px;flex:none;}
.tab-close:hover{background:#d4dbe6;color:#33415c;}
.tab.dragging{opacity:.55;}
.stage{flex:1;position:relative;background:#fff;}
.framewrap{position:absolute;inset:0;display:none;}
.framewrap.show{display:block;}
.framewrap .frame{width:100%;height:100%;border:0;background:#fff;}
.framewrap .overlay{position:absolute;inset:0;background:rgba(244,246,251,.92);display:none;
 align-items:center;justify-content:center;flex-direction:column;gap:14px;z-index:5;}
.framewrap .overlay.show{display:flex;}
.spinner{width:42px;height:42px;border:4px solid #d4ddec;border-top-color:var(--blue);
 border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.framewrap .overlay p{color:#5b6b86;font-weight:600;font-size:14px;}
.empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 color:#8a93a6;text-align:center;padding:24px;}
.empty .big{font-size:54px;margin-bottom:14px;}
.empty h2{margin:0 0 8px;color:#1F3864;font-size:22px;font-weight:800;}
.empty p{margin:2px 0;font-size:14.5px;}
.empty .ex{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;}
.empty .ex span{background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 14px;
 font-size:13px;color:#33415c;cursor:pointer;font-weight:600;}
.empty .ex span:hover{border-color:var(--blue);color:var(--blue);}
</style></head>
<body>
<div class="topbar">
  <div class="brand">📈 K-Market Dashboard<small>KOSPI·KOSDAQ</small></div>
  <form class="searchwrap" id="form" autocomplete="off">
    <input id="q" type="text" placeholder="주식·ETF 종목명 또는 6자리 코드 입력 (예: 삼성전자, 005930, KODEX 200)">
    <div class="sg" id="sg"></div>
  </form>
  <button class="btn" type="button" id="searchBtn">검색</button>
</div>
<div class="tabstrip" id="tabstrip"></div>
<div class="stage" id="stage">
  <div class="empty" id="empty">
    <div class="big">🔍</div>
    <h2>종목을 검색해 보세요</h2>
    <p>개별주식·ETF 종목명 또는 6자리 코드를 입력하면 새 탭으로 리포트가 열립니다.</p>
    <p>탭은 닫거나 드래그해 순서를 바꿀 수 있습니다.</p>
    <div class="ex">
      <span data-code="005930">삼성전자</span>
      <span data-code="000660">SK하이닉스</span>
      <span data-code="005380">현대차</span>
      <span data-code="069500">KODEX 200</span>
      <span data-code="133690">TIGER 미국나스닥100</span>
    </div>
  </div>
</div>
<script>
var q=document.getElementById('q'),sg=document.getElementById('sg'),
    tabstrip=document.getElementById('tabstrip'),stage=document.getElementById('stage'),
    empty=document.getElementById('empty');
var tabs=[],active=null,seq=0,sgItems=[],sgActive=-1,tmr=null,dragId=null;

function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

// ── 자동완성 ──
q.addEventListener('input',function(){
  clearTimeout(tmr); sgActive=-1;
  var v=q.value.trim();
  if(!v){hideSg();return;}
  tmr=setTimeout(function(){fetchSg(v);},180);
});
q.addEventListener('keydown',function(e){
  if(!sg.classList.contains('show')){ if(e.key==='Enter'){e.preventDefault();doSearch();} return; }
  var rows=sg.querySelectorAll('.sg-item');
  if(e.key==='ArrowDown'){e.preventDefault();sgActive=Math.min(sgActive+1,rows.length-1);paintSg(rows);}
  else if(e.key==='ArrowUp'){e.preventDefault();sgActive=Math.max(sgActive-1,0);paintSg(rows);}
  else if(e.key==='Enter'){e.preventDefault(); if(sgActive>=0&&sgItems[sgActive]) pick(sgItems[sgActive].code); else doSearch();}
  else if(e.key==='Escape'){hideSg();}
});
document.addEventListener('click',function(e){if(!sg.contains(e.target)&&e.target!==q)hideSg();});
// 드롭다운은 검색창이 활성(focus)일 때만 — 포커스 해제 시 닫기(클릭 선택은 지연으로 허용)
q.addEventListener('blur',function(){setTimeout(hideSg,150);});
q.addEventListener('focus',function(){var v=q.value.trim(); if(v)fetchSg(v);});
document.getElementById('form').addEventListener('submit',function(e){e.preventDefault();doSearch();});
document.getElementById('searchBtn').addEventListener('click',doSearch);
function paintSg(rows){rows.forEach(function(r,i){r.classList.toggle('active',i===sgActive);});}
function hideSg(){sg.classList.remove('show');sg.innerHTML='';}
function fetchSg(v){
  fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
    sgItems=d||[];
    if(!sgItems.length){hideSg();return;}
    sg.innerHTML=sgItems.map(function(it){
      var cls=it.type==='ETF'?'etf':'stk';
      return '<div class="sg-item" data-code="'+esc(it.code)+'">'+
        '<span class="sg-badge '+cls+'">'+it.type+'</span>'+
        '<span class="sg-code">'+esc(it.code)+'</span>'+
        '<span class="sg-name">'+esc(it.name)+'</span>'+
        '<span class="sg-extra">'+esc(it.extra||'')+'</span></div>';
    }).join('');
    sg.classList.add('show');
  }).catch(function(){hideSg();});
}
sg.addEventListener('click',function(e){var it=e.target.closest('.sg-item'); if(it) pick(it.dataset.code);});
function pick(code){q.value=code;hideSg();doSearch();}
function doSearch(){var v=q.value.trim(); if(!v)return; hideSg(); openTab(v);}

// iframe(ETF 구성종목 등) → 부모에서 개별종목 리포트를 새 탭으로 열기
window.MI_TABS=true;
window.miOpenStockTab=function(code){ if(code) openTab(String(code)); };

// 하트비트: 이 페이지(브라우저 탭)가 살아있는 동안 주기적으로 핑 → 닫히면 서버 자동 종료
function miPing(){ fetch('/__ping').catch(function(){}); }
miPing(); setInterval(miPing, 3000);
document.addEventListener('visibilitychange',function(){ if(!document.hidden) miPing(); });
// 탭 닫힘/이동 시 즉시 종료 신호(새로고침이면 새 페이지가 다시 핑하여 취소됨)
window.addEventListener('pagehide',function(){ try{navigator.sendBeacon('/__bye');}catch(e){} });

// 예시 칩
empty.querySelectorAll('.ex span').forEach(function(s){
  s.addEventListener('click',function(){pick(s.dataset.code);});
});

// ── 탭 관리 ──
function openTab(query){
  var ex=tabs.find(function(t){return t.query===query;});
  if(ex){activate(ex.id);return;}
  var id='t'+(++seq);
  var wrap=document.createElement('div'); wrap.className='framewrap'; wrap.dataset.id=id;
  var ov=document.createElement('div'); ov.className='overlay show';
  ov.innerHTML='<div class="spinner"></div><p>리포트를 생성하는 중…</p>';
  var f=document.createElement('iframe'); f.className='frame';
  f.addEventListener('load',function(){ov.classList.remove('show');updateMeta(id,f);});
  f.src='/dashboard?q='+encodeURIComponent(query);
  wrap.appendChild(ov); wrap.appendChild(f); stage.appendChild(wrap);
  tabs.push({id:id,query:query,title:query,icon:'⏳'});
  activate(id);
}
function updateMeta(id,f){
  var t=tabs.find(function(x){return x.id===id;}); if(!t)return;
  var title='';
  var kind='';
  try{
    title=(f.contentDocument&&f.contentDocument.title)||'';
    kind=(f.contentDocument&&f.contentDocument.documentElement.getAttribute('data-kind'))||'';
  }catch(e){}
  if(title)t.title=title;
  t.icon = (kind==='etf') ? '📊' : '📈';
  renderTabs();
}
function activate(id){
  active=id;
  document.querySelectorAll('.framewrap').forEach(function(w){w.classList.toggle('show',w.dataset.id===id);});
  empty.style.display=tabs.length?'none':'flex';
  renderTabs();
}
function closeTab(id){
  var i=tabs.findIndex(function(t){return t.id===id;}); if(i<0)return;
  tabs.splice(i,1);
  var w=stage.querySelector('.framewrap[data-id="'+id+'"]'); if(w)w.remove();
  if(active===id){active=tabs.length?tabs[Math.min(i,tabs.length-1)].id:null;}
  if(active)activate(active); else{empty.style.display='flex';renderTabs();}
}
function renderTabs(){
  tabstrip.innerHTML=tabs.map(function(t){
    return '<div class="tab'+(t.id===active?' active':'')+(t.id===dragId?' dragging':'')+'" data-id="'+t.id+'">'+
      '<span class="tab-ic">'+(t.icon||'📈')+'</span>'+
      '<span class="tab-label" title="'+esc(t.title)+'">'+esc(t.title)+'</span>'+
      '<span class="tab-close" data-id="'+t.id+'">×</span></div>';
  }).join('');
  tabstrip.style.display=tabs.length?'flex':'none';
}
// 닫기 버튼만 click 으로 처리
tabstrip.addEventListener('click',function(e){
  var close=e.target.closest('.tab-close');
  if(close){e.stopPropagation();closeTab(close.dataset.id);}
});
// 탭: 눌러서 클릭=활성화 / 끌어서 순서변경 (포인터 기반 — 네이티브 DnD보다 안정적)
var dragMoved=false,startX=0;
tabstrip.addEventListener('mousedown',function(e){
  if(e.target.closest('.tab-close'))return;        // 닫기 버튼 제외
  var tab=e.target.closest('.tab'); if(!tab)return;
  dragId=tab.dataset.id; dragMoved=false; startX=e.clientX;
  e.preventDefault();
  document.addEventListener('mousemove',onTabMove);
  document.addEventListener('mouseup',onTabUp);
});
function onTabMove(e){
  if(dragId===null)return;
  if(!dragMoved){
    if(Math.abs(e.clientX-startX)<5)return;
    dragMoved=true;
    var d=tabstrip.querySelector('.tab[data-id="'+dragId+'"]'); if(d)d.classList.add('dragging');
  }
  var els=tabstrip.querySelectorAll('.tab'),over=null;
  for(var i=0;i<els.length;i++){
    var r=els[i].getBoundingClientRect();
    if(e.clientX>=r.left&&e.clientX<=r.right){over=els[i];break;}
  }
  if(!over||over.dataset.id===dragId)return;
  var from=tabs.findIndex(function(x){return x.id===dragId;}),
      to=tabs.findIndex(function(x){return x.id===over.dataset.id;});
  if(from<0||to<0)return;
  var m=tabs.splice(from,1)[0]; tabs.splice(to,0,m); renderTabs();
}
function onTabUp(){
  document.removeEventListener('mousemove',onTabMove);
  document.removeEventListener('mouseup',onTabUp);
  if(!dragMoved&&dragId!==null)activate(dragId);   // 이동 없었으면 클릭=활성화
  dragId=null; dragMoved=false; renderTabs();
}
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
    print("  한국 증시·ETF 통합 대시보드")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 종료: 브라우저 탭을 닫거나 Ctrl + C")
    print("=" * 60)
    if not os.environ.get("MI_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    threading.Thread(target=_monitor_heartbeat, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
