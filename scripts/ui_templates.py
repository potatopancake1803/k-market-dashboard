# AUTO-EXTRACTED from market_dashboard3_realtime.py (changes_77). DO NOT add logic here —
# this module holds ONLY the inline page/widget template *constants* (HTML/CSS/JS strings).
# The main file imports these, then assembles them (`.replace(...)`, `_inject_*`).
# Edit a page's markup HERE; edit wiring/logic in the main file. After editing, run:
#   uv run scripts/smoke_check.py   (golden compare must pass, or re-baseline if intentional)

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

_FX_STYLE = """<style id="m4-fx">
/* ===== Phase B: macOS 26 Liquid Glass 리포트 테마 (비파괴 오버라이드) ===== */
html{--mat-card:rgba(255,255,255,.72);--mat-bar:rgba(255,255,255,.6);
 --g-blur:saturate(180%) blur(18px);
 --g-edge:inset 0 1px 0 rgba(255,255,255,.6), inset 0 -1px 3px rgba(0,0,0,.04);
 --g-line:rgba(60,60,67,.12);--dl-gray:#c7cdd6;
 --ease:cubic-bezier(.32,.72,0,1);}   /* macOS 26 표준 이징(랜딩과 동일) */
html.dark{--bg:#0d1117;--card:#1b1c22;--line:rgba(255,255,255,.10);--text:rgba(255,255,255,.9);
 --navy:#e8eefc;--blue:#5aa6ff;--mat-card:rgba(40,40,46,.64);--mat-bar:rgba(26,26,31,.55);
 --g-line:rgba(255,255,255,.10);--g-edge:inset 0 1px 0 rgba(255,255,255,.10), inset 0 -1px 3px rgba(0,0,0,.3);
 --dl-gray:#2b2f38;}
body{background:radial-gradient(60% 50% at 10% -2%, rgba(150,190,255,.20), transparent 60%),
 radial-gradient(55% 50% at 95% 2%, rgba(255,180,220,.16), transparent 60%), var(--bg) !important;
 background-attachment:fixed;}
html.dark body{background:radial-gradient(60% 50% at 10% -2%, rgba(60,90,200,.22), transparent 60%),
 radial-gradient(55% 50% at 95% 2%, rgba(140,60,160,.16), transparent 60%), var(--bg) !important;}
header{background:var(--mat-bar) !important;-webkit-backdrop-filter:var(--g-blur);backdrop-filter:var(--g-blur);
 border-bottom:.5px solid var(--g-line) !important;box-shadow:var(--g-edge);}
nav{background:var(--mat-bar) !important;-webkit-backdrop-filter:var(--g-blur);backdrop-filter:var(--g-blur);
 border-bottom:.5px solid var(--g-line) !important;}
/* 내용 카드 = 투명도 있는 리퀴드 글라스 (기본 탭) */
.pane .card,.metric-card,.eh-kpi,.info-cell{background:var(--mat-card) !important;
 -webkit-backdrop-filter:var(--g-blur);backdrop-filter:var(--g-blur);
 border:.5px solid var(--g-line) !important;border-radius:16px !important;
 box-shadow:var(--g-edge), 0 8px 26px rgba(20,30,70,.08) !important;
 transition:box-shadow .22s ease,transform .18s var(--ease),background-color .55s ease;
 will-change:transform;backface-visibility:hidden;}
.pane .card:hover{box-shadow:var(--g-edge),0 16px 40px rgba(31,56,100,.14) !important;}
.range-toggle,.fc-seg{background:rgba(120,120,128,.10) !important;}
/* M4 퀀트 탭 카드는 다크 콕핏 그대로 보호(원본 값 !important 재선언) */
.m4-wrap .card{background:rgba(255,255,255,.035) !important;border:1px solid rgba(120,140,255,.16) !important;
 border-radius:14px !important;box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 10px 30px rgba(5,8,22,.35) !important;
 -webkit-backdrop-filter:blur(6px) !important;backdrop-filter:blur(6px) !important;}
/* 다크: 하드코딩 색 오버라이드 */
html.dark header h1{color:var(--text) !important;}
html.dark header .sub,html.dark .metric-card .m-label,html.dark .metric-card .m-sub,html.dark .empty{color:#9aa6bd !important;}
html.dark .card-title,html.dark .metric-card .m-value{color:#eaf0ff !important;}
html.dark .tab-btn{color:#9aa6bd !important;}
html.dark .tab-btn.active{color:#fff !important;}
html.dark table.mi-table th{background:#28304a !important;color:#eef3ff !important;}
html.dark table.mi-table td{color:#cdd6e8 !important;border-bottom-color:rgba(255,255,255,.08) !important;}
html.dark table.mi-table td:not(:first-child){color:#fff !important;}
html.dark table.mi-table tbody tr:nth-child(even){background:rgba(255,255,255,.04) !important;}
html.dark table.mi-table tbody tr:hover{background:rgba(90,166,255,.14) !important;}
html.dark table.fin-table .sec-row td{background:#28304a !important;color:#dbe6ff !important;border-top-color:#3a4a72 !important;}
html.dark table.fin-table td.acct{color:#c0c9dc !important;}
html.dark .prose code{background:rgba(255,255,255,.08) !important;}
html.dark .mi-search{background:rgba(255,255,255,.06) !important;color:var(--text) !important;border-color:var(--g-line) !important;}
html.dark .range-toggle button.active,html.dark .fc-seg button.active{background:#2c2c30 !important;color:#fff !important;}
/* 개요 정보 그리드·KPI 등 하드코딩 네이비 텍스트 보강 */
html.dark .ei-v{color:#eef3ff !important;}
html.dark .ei-l{color:#9aa6bd !important;}
html.dark .ei{border-bottom-color:rgba(255,255,255,.08) !important;}
html.dark .info-cell{background:rgba(255,255,255,.05) !important;border-color:var(--g-line) !important;}
html.dark .k-val{color:#fff !important;}
html.dark .k-label,html.dark .ph-meta,html.dark .eh-top{color:#9aa6bd !important;}
html.dark .eh-name{color:#eef3ff !important;}
html.dark .eh-code,html.dark .eh-asof{color:#9aa6bd !important;}
/* 다크 기본 텍스트 안전망(빨강/파랑 등 의미색 보존 — !important 미사용) */
html.dark .card,html.dark .pane,html.dark .info-cell,html.dark .prose p,html.dark .prose li{color:#d7e0f0;}
/* 콜아웃 박스(지배구조 출처 등) 다크 — 흰 박스 → 다른 카드와 톤 맞춤 */
html.dark .callout.info{background:rgba(90,140,220,.16) !important;border-color:rgba(130,170,235,.32) !important;color:#d4e0f6 !important;}
html.dark .callout.win{background:rgba(70,170,100,.15) !important;border-color:rgba(110,200,140,.32) !important;color:#c6edd1 !important;}
html.dark .callout.warn{background:rgba(220,90,90,.15) !important;border-color:rgba(235,120,120,.32) !important;color:#f2c9c9 !important;}
/* 도넛 비중 리스트 다크 — 이름/값/빈 막대 트랙 대비 보강 */
html.dark .donut-list .dl-head{color:#e8eefc !important;border-bottom-color:rgba(255,255,255,.12) !important;}
html.dark .donut-list .dl-row{border-bottom-color:rgba(255,255,255,.07) !important;}
html.dark .donut-list .dl-name{color:#cdd6e8 !important;}
html.dark .donut-list .dl-val{color:#fff !important;}
html.dark .donut-list .dl-bar{background:rgba(255,255,255,.08) !important;}
/* 애널리스트 리포트 표 다크 — 제목 링크/증권사/투자의견 대비 보강 */
html.dark .res-table td.res-broker{color:#c0c9dc !important;}
html.dark .res-table a.res-link{color:#eaf0ff !important;}
html.dark .res-table a.res-link:hover{color:#7db8ff !important;}
html.dark .res-table td.op-hold{color:#e0b15a !important;}
/* 작업3: 그 외 하드코딩 네이비/회색 텍스트 다크 보강 */
html.dark .k-unit{color:#9aa6bd !important;}
html.dark .ig-label{color:#9aa6bd !important;}
html.dark table.mi-table.bold-first td:first-child{color:#fff !important;}
html.dark table.mi-table td.t-date{color:#c0c9dc !important;}
/* 컨센서스(애널리스트 투자의견) 패널 다크 */
html.dark .cons-target .ct-price{color:#fff !important;}
html.dark .cons-target .ct-sub{color:#9aa6bd !important;}
html.dark .cons-target .ct-uplabel{color:#9aa6bd !important;}
html.dark .cons-dist .cd-label{color:#9aa6bd !important;}
html.dark .cons-dist .cd-bar{background:rgba(255,255,255,.08) !important;}
/* 부드러운 테마 전환 */
body,.card,.metric-card,header,nav,.tab-btn,table.mi-table th,table.mi-table td,.fin-table .sec-row td{
 transition:background-color .55s ease,color .55s ease,border-color .55s ease;}
html.theme-anim *{transition:background-color .6s ease,color .6s ease,border-color .6s ease,box-shadow .6s ease,fill .6s ease !important;}
/* 기존 FX (유지) */
header{perspective:900px;}
header h1{transition:transform .2s var(--ease);transform-style:preserve-3d;will-change:transform;backface-visibility:hidden;}
nav .tab-btn{transition:color .16s,border-color .16s,background .16s,transform .16s var(--ease),background-color .55s ease;}
nav .tab-btn:hover{transform:translateY(-1px);}
@media (prefers-reduced-motion:reduce){.pane .card,header h1{transition:none!important;transform:none!important;will-change:auto!important;}}
</style>"""

_FX_JS = """<script>
(function(){
 try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}
 window.addEventListener('message',function(ev){try{if(ev.data&&ev.data.kmkt){var rr=document.documentElement,dd=ev.data.kmkt==='dark';rr.classList.add('theme-anim');rr.classList.toggle('dark',dd);clearTimeout(window.__rtm);window.__rtm=setTimeout(function(){rr.classList.remove('theme-anim');},780);try{themeCharts(true);setTimeout(function(){themeCharts(true);},150);}catch(e){}}}catch(e){}});
 function _chC(){var d=document.documentElement.classList.contains('dark');
  return {fg:d?'#cdd6e8':'#33415c',gr:d?'rgba(255,255,255,.09)':'rgba(0,0,0,.07)',ln:d?'rgba(255,255,255,.18)':'rgba(0,0,0,.14)'};}
 function themeCharts(force){ if(!window.Plotly)return; var c=_chC();
  document.querySelectorAll('.js-plotly-plot').forEach(function(gd){
   if(gd.closest&&gd.closest('.m4-wrap'))return;
   var pc;try{pc=gd._fullLayout&&gd._fullLayout.paper_bgcolor;}catch(e){pc=null;}
   if(!force&&pc==='rgba(0, 0, 0, 0)'&&gd.__thm===c.fg)return; gd.__thm=c.fg;
   try{Plotly.relayout(gd,{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
    'font.color':c.fg,'legend.font.color':c.fg,'title.font.color':c.fg,
    'xaxis.gridcolor':c.gr,'yaxis.gridcolor':c.gr,'xaxis.zerolinecolor':c.gr,'yaxis.zerolinecolor':c.gr,
    'xaxis.linecolor':c.ln,'yaxis.linecolor':c.ln,'xaxis.tickcolor':c.ln,'yaxis.tickcolor':c.ln});}catch(e){}
   var dk=document.documentElement.classList.contains('dark'),dat=gd.data&&gd.data[0];
   /* 도넛(파이): 기타주주 회색 슬라이스 + 중앙 퍼센티지 라벨 테마 대응 */
   try{if(dat&&dat.type==='pie'){
     var mc=dat.marker&&dat.marker.colors;
     if(mc&&mc.length){var nc=mc.map(function(x){
       return (x==='#c7cdd6'||x==='#2b2f38')?(dk?'#2b2f38':'#c7cdd6'):x;});
      Plotly.restyle(gd,{'marker.colors':[nc],'marker.line.color':dk?'#1b1c22':'#ffffff'});}
     if(gd.layout&&gd.layout.annotations&&gd.layout.annotations.length)
      Plotly.relayout(gd,{'annotations[0].font.color':dk?'#eaf0ff':'#15233f'});
    }}catch(e){}
   /* 인디케이터(투자의견 게이지): 하드코딩 네이비 제목/중앙 숫자 테마 대응 */
   try{if(dat&&dat.type==='indicator'){
     var up={},tt=gd.layout&&gd.layout.title&&gd.layout.title.text;
     if(tt)up['title.text']=dk?tt.replace(/#1F3864/g,'#eaf0ff'):tt.replace(/#eaf0ff/g,'#1F3864');
     if(gd.layout&&gd.layout.annotations&&gd.layout.annotations.length)
      up['annotations[0].font.color']=dk?'#eaf0ff':'#15233f';
     Plotly.relayout(gd,up);
    }}catch(e){}
  });}
 setInterval(function(){if(!document.hidden)themeCharts(false);},1000);
 setTimeout(function(){themeCharts(false);},400);setTimeout(function(){themeCharts(true);},1300);
 document.addEventListener('click',function(){setTimeout(function(){themeCharts(false);},220);setTimeout(function(){themeCharts(false);},760);});
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

_MKT_CSS = """
:root{
 --bg:#f4f5f9;--card:rgba(255,255,255,.82);--line:rgba(60,60,67,.1);
 --text:rgba(0,0,0,.86);--sub:rgba(60,60,67,.6);--chip:rgba(118,118,128,.08);
 --ico:rgba(118,118,128,.1);--up:#FF3B30;--dn:#2E75B6;--hover:rgba(10,132,255,.06);
 --seg:rgba(247,247,247,.92);--seg-on:#fff;
}
html.dark{
 --bg:#0d1117;--card:rgba(28,30,38,.74);--line:rgba(255,255,255,.09);
 --text:rgba(255,255,255,.92);--sub:rgba(235,235,245,.52);--chip:rgba(255,255,255,.06);
 --ico:rgba(255,255,255,.08);--up:#FF453A;--dn:#64B5FF;--hover:rgba(90,166,255,.1);
 --seg:rgba(48,50,58,.85);--seg-on:#5b5e6a;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);font-size:14px;
 font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Apple SD Gothic Neo',sans-serif;
 padding:22px 24px 48px;transition:background .4s ease;-webkit-font-smoothing:antialiased;}
.bar{display:flex;align-items:center;gap:14px;margin-bottom:6px;flex-wrap:wrap;}
.seg{display:inline-flex;background:var(--seg);border:.5px solid var(--line);
 border-radius:100px;padding:3px;box-shadow:0 8px 30px rgba(0,0,0,.07);}
.seg button{border:0;background:transparent;color:var(--sub);font:inherit;font-size:15px;font-weight:700;
 padding:9px 26px;border-radius:100px;cursor:pointer;transition:all .22s cubic-bezier(.32,.72,0,1);}
.seg button.on{background:var(--seg-on);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.18);}
.asof{margin-left:auto;color:var(--sub);font-size:12.5px;display:flex;align-items:center;gap:7px;}
.dot{width:8px;height:8px;border-radius:50%;background:#9aa0ab;flex:none;}
.dot.live{background:#FF3B30;animation:pulse 1.6s ease-in-out infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,59,48,.6);}70%{box-shadow:0 0 0 7px rgba(255,59,48,0);}100%{box-shadow:0 0 0 0 rgba(255,59,48,0);}}
.lead{color:var(--sub);font-size:12.5px;margin:2px 2px 14px;}
.h2{font-size:17px;font-weight:800;margin:26px 2px 12px;display:flex;align-items:center;gap:9px;letter-spacing:-.01em;}
.h2 .cnt{font-weight:500;color:var(--sub);font-size:13px;}
.list{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(30px);backdrop-filter:saturate(180%) blur(30px);
 border:.5px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.09);}
.row{display:flex;align-items:center;gap:14px;padding:14px 18px;cursor:pointer;
 border-bottom:.5px solid var(--line);transition:background .14s;}
.row:last-child{border-bottom:0;}
.row:hover{background:var(--hover);}
.row.sel{background:var(--hover);}
.rank{width:24px;text-align:center;font-size:15px;font-weight:800;color:var(--sub);flex:none;}
.ico{width:46px;height:46px;flex:none;display:flex;align-items:center;justify-content:center;
 font-size:24px;background:var(--ico);border-radius:14px;}
.rankc{width:34px;height:34px;flex:none;display:flex;align-items:center;justify-content:center;
 font-size:14px;font-weight:800;color:var(--sub);background:var(--ico);border-radius:11px;}
.main{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:3px;}
.nm{font-size:16px;font-weight:700;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.sub{font-size:12.5px;color:var(--sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.right{flex:none;display:flex;flex-direction:column;align-items:flex-end;gap:3px;text-align:right;}
.chg{font-size:16px;font-weight:800;font-variant-numeric:tabular-nums;}
.px{font-size:15px;font-weight:600;font-variant-numeric:tabular-nums;}
.bd{font-size:12.5px;color:var(--sub);}
.up{color:var(--up);} .dn{color:var(--dn);} .fl{color:var(--sub);}
.empty-note{padding:34px;text-align:center;color:var(--sub);font-size:14px;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
@media (max-width:880px){.two{grid-template-columns:1fr;}}
.ovw{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:4px;}
@media (max-width:680px){.ovw{grid-template-columns:1fr;}}
.ovcard{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(30px);backdrop-filter:saturate(180%) blur(30px);
 border:.5px solid var(--line);border-radius:16px;padding:18px 22px;box-shadow:0 18px 50px rgba(0,0,0,.09);}
.ovcard .ovname{font-size:14px;font-weight:700;color:var(--sub);}
.ovcard .ovval{font-size:30px;font-weight:800;letter-spacing:-.02em;margin:4px 0 2px;font-variant-numeric:tabular-nums;}
.ovcard .ovchg{font-size:15px;font-weight:700;font-variant-numeric:tabular-nums;}
.ovcard .ovbd{font-size:12.5px;color:var(--sub);margin-top:8px;}
.ovcard .ovbd b.u{color:var(--up);} .ovcard .ovbd b.d{color:var(--dn);}
.obadge{display:inline-block;font-size:11px;font-weight:800;border-radius:7px;padding:3px 9px;flex:none;}
.obadge.buy{background:rgba(255,59,48,.13);color:var(--up);}
.obadge.hold{background:rgba(120,120,128,.16);color:var(--sub);}
.obadge.sell{background:rgba(46,117,182,.13);color:var(--dn);}
.nrow{display:flex;gap:14px;padding:13px 18px;border-bottom:.5px solid var(--line);align-items:baseline;}
.nrow:last-child{border-bottom:0;}
.nrow.clickable{cursor:pointer;} .nrow.clickable:hover{background:var(--hover);}
.nrow .ntime{font-size:12px;color:var(--sub);flex:none;width:78px;font-variant-numeric:tabular-nums;}
.nrow .ntitle{flex:1;font-size:14.5px;line-height:20px;font-weight:500;}
.nrow .nsrc{font-size:12px;color:var(--sub);flex:none;width:88px;text-align:right;}
@media (max-width:680px){.nrow .nsrc{display:none;}}
#detail{display:none;margin-top:6px;}
#detail.show{display:block;animation:slin .3s cubic-bezier(.32,.72,0,1);}
@keyframes slin{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}
.dico{font-size:20px;}
"""

_SECTOR_HTML = """<!DOCTYPE html>
<html lang="ko" data-kind="sector"><head>
<meta charset="utf-8"><title>업종 지수</title>
<link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>__KMKT_MKT_CSS__</style></head>
<body>
<div class="bar">
  <div class="seg" id="seg">
    <button data-mkt="kospi" class="on">코스피</button>
    <button data-mkt="kosdaq">코스닥</button>
  </div>
  <span class="asof"><span class="dot" id="liveDot"></span><span id="asof">불러오는 중…</span></span>
</div>
<div class="lead">업종을 누르면 시가총액 상위 구성종목 시세가 펼쳐집니다 · 등락률 높은 순</div>
<div class="list" id="list"><div class="empty-note">업종 지수를 불러오는 중…</div></div>
<div id="detail">
  <div class="h2"><span class="dico" id="dIco">📂</span><span id="dName">업종</span><span class="cnt" id="dCnt"></span></div>
  <div class="list" id="dList"></div>
</div>
<script>
(function(){
 var SECT_ICON={"음식료·담배":"🍔","섬유·의류":"👕","종이·목재":"🪵","화학":"🧪","제약":"💊",
  "비금속":"🪨","금속":"🔩","기계·장비":"⚙️","전기·전자":"💡","의료·정밀기기":"🔬",
  "운송장비·부품":"🚗","유통":"🛒","전기·가스":"⚡","건설":"🏗️","운송·창고":"🚚",
  "통신":"📡","금융":"🏦","증권":"📊","보험":"🛡️","일반서비스":"🛎️","제조":"🏭",
  "부동산":"🏢","IT 서비스":"💻","오락·문화":"🎬","출판·매체복제":"📚","기타제조":"📦"};
 function ico(n){return SECT_ICON[n]||"🏷️";}
 var mkt='kospi',selCode=null;
 var fmt=function(n,d){return Number(n).toLocaleString('en-US',{minimumFractionDigits:d===undefined?2:d,maximumFractionDigits:d===undefined?2:d});};
 function cls(v){return v>0?'up':(v<0?'dn':'fl');}
 function sgn(v){return (v>0?'+':(v<0?'-':''))}
 function mc(v){return v>=10000?fmt(v/10000,1)+'조':fmt(v,0)+'억';}
 function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
 function load(){
   if(document.hidden || (window.__APP_LOADED && !document.hasFocus()))return;
   window.__APP_LOADED = true;
   fetch('/api/sectors?mkt='+mkt,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var rows=(d.rows||[]).slice().sort(function(a,b){return b.change_pct-a.change_pct;});
     var el=document.getElementById('list');
     if(!rows.length){el.innerHTML='<div class="empty-note">데이터를 불러오지 못했습니다 (KIS 키/네트워크 확인)</div>';return;}
     el.innerHTML=rows.map(function(r,i){
       var c=cls(r.change_pct);
       var tot=(r.up_cnt||0)+(r.down_cnt||0)+((r.flat_cnt!=null?r.flat_cnt:0));
       var breadth=(tot>0)?(tot+'개 중 '+(r.up_cnt||0)+'개 상승'):('지수 '+fmt(r.value));
       return '<div class="row'+(r.code===selCode?' sel':'')+'" data-code="'+r.code+'" data-name="'+esc(r.name)+'">'+
         '<span class="rank">'+(i+1)+'</span>'+
         '<span class="ico">'+ico(r.name)+'</span>'+
         '<span class="main"><span class="nm">'+esc(r.name)+'</span>'+
           '<span class="sub">지수 '+fmt(r.value)+'</span></span>'+
         '<span class="right"><span class="chg '+c+'">'+sgn(r.change_pct)+fmt(Math.abs(r.change_pct))+'%</span>'+
           '<span class="bd">'+breadth+'</span></span></div>';
     }).join('');
     document.getElementById('asof').textContent=(d.market_open?'실시간':'전일 종가 기준')+' \\u00b7 '+(d.asof||'');
     document.getElementById('liveDot').className='dot'+(d.market_open?' live':'');
     var allZero=rows.every(function(r){return !r.change_pct;});
     document.querySelector('.lead').textContent=(!d.market_open&&allZero)
       ? '장 시작 전입니다 — 업종 등락률은 장 중(09:00~) 실시간 갱신됩니다 · 업종을 누르면 구성종목 시세가 펼쳐집니다'
       : '업종을 누르면 시가총액 상위 구성종목 시세가 펼쳐집니다 · 등락률 높은 순';
   }).catch(function(){});
 }
 function loadDetail(code,name){
   selCode=code;
   document.querySelectorAll('#list .row').forEach(function(x){x.classList.toggle('sel',x.dataset.code===code);});
   fetch('/api/sector_stocks?iscd='+code,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var rows=d.rows||[];
     document.getElementById('dIco').textContent=ico(name);
     document.getElementById('dName').textContent=name;
     document.getElementById('dCnt').textContent='시가총액 상위 '+rows.length+'종목';
     var el=document.getElementById('dList');
     el.innerHTML=rows.length?rows.map(function(r,i){
       var c=cls(r.change_pct);
       return '<div class="row srow" data-scode="'+r.code+'">'+
         '<span class="rank">'+(i+1)+'</span>'+
         '<span class="main"><span class="nm">'+esc(r.name)+'</span>'+
           '<span class="sub">'+mc(r.mcap)+(r.volume>0?' · '+fmt(r.volume,0)+'주':'')+'</span></span>'+
         '<span class="right"><span class="px">'+fmt(r.price,0)+'</span>'+
           '<span class="chg '+c+'">'+sgn(r.change_pct)+fmt(Math.abs(r.change_pct))+'%</span></span></div>';
     }).join(''):'<div class="empty-note">구성종목 정보를 불러오지 못했습니다</div>';
     var det=document.getElementById('detail');det.classList.add('show');
     det.scrollIntoView({behavior:'smooth',block:'nearest'});
   }).catch(function(){});
 }
 document.getElementById('seg').addEventListener('click',function(e){
   var b=e.target.closest('button');if(!b)return;mkt=b.dataset.mkt;
   document.querySelectorAll('#seg button').forEach(function(x){x.classList.toggle('on',x===b);});
   selCode=null;document.getElementById('detail').classList.remove('show');load();
 });
 document.getElementById('list').addEventListener('click',function(e){
   var row=e.target.closest('.row');if(!row||!row.dataset.code)return;
   loadDetail(row.dataset.code,row.dataset.name);
 });
 document.getElementById('dList').addEventListener('click',function(e){
   var row=e.target.closest('.row');if(!row||!row.dataset.scode)return;
   try{if(window.parent&&window.parent.miOpenStockTab)window.parent.miOpenStockTab(row.dataset.scode);}catch(err){}
 });
 window.addEventListener('message',function(e){
   var d=e&&e.data;if(!d||!d.kmkt)return;
   document.documentElement.classList.toggle('dark',d.kmkt==='dark');
 });
 load();setInterval(load,45000);
})();
</script>
</body></html>"""

_MARKET_HTML = """<!DOCTYPE html>
<html lang="ko" data-kind="market"><head>
<meta charset="utf-8"><title>시장 현황</title>
<link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<script src="/plotly.js"></script>
<style>__KMKT_MKT_CSS__
.mapcard{margin:4px 0 14px;}
.maphead{display:flex;align-items:baseline;gap:10px;margin:0 0 8px;font-size:15px;font-weight:700;}
.maphead .note{font-size:11.5px;font-weight:500;color:var(--sub);}
.maplegend{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:11px;color:var(--sub);font-weight:500;}
.maplegend i{display:inline-block;width:42px;height:9px;border-radius:2px;
 background:linear-gradient(90deg,#2E75B6,#4a5160,#FF3B30);}
#marketMap{width:100%;height:560px;border-radius:14px;overflow:hidden;}
.mapempty{color:var(--sub);font-size:13px;padding:60px 0;text-align:center;}
.mapasof{margin-left:8px;font-size:11px;font-weight:500;color:var(--sub);}
/* 지수 카드 — 실시간 점·롤링·클릭 진입 */
.ovcard{cursor:pointer;transition:transform .14s ease,box-shadow .2s ease;}
.ovcard:hover{transform:translateY(-2px);box-shadow:0 16px 40px rgba(0,0,0,.12);}
.ovhead{display:flex;align-items:center;gap:7px;}
.ovhead .ovname{font-size:14px;font-weight:700;color:var(--sub);}
.ovhead .ovarrow{margin-left:auto;color:var(--sub);font-size:18px;font-weight:600;opacity:.5;}
.ovval .rt-ch{display:inline-block;overflow:hidden;vertical-align:bottom;}
</style></head>
<body>
<div class="bar">
  <div class="seg" id="seg">
    <button data-mkt="kospi" class="on">코스피</button>
    <button data-mkt="kosdaq">코스닥</button>
  </div>
  <span class="asof"><span class="dot" id="liveDot"></span><span id="asof">불러오는 중…</span></span>
</div>
<div class="ovw" id="ovw"></div>
<div class="mapcard">
  <div class="maphead">🗺️ 마켓맵 <span class="note">섹터·종목 시가총액 비중(칸 크기) × 등락률(색)</span>
    <span class="mapasof" id="mapAsof"></span>
    <span class="maplegend">하락 <i></i> 상승</span></div>
  <div id="marketMap"><div class="mapempty">마켓맵 불러오는 중…</div></div>
</div>
<div class="h2">👑 시가총액 상위 <span class="cnt" id="topCnt"></span></div>
<div class="list" id="topList"><div class="empty-note">불러오는 중…</div></div>
<div class="two">
  <div><div class="h2">🚀 상한가 <span class="cnt" id="upCnt"></span></div>
    <div class="list" id="upList"><div class="empty-note">—</div></div></div>
  <div><div class="h2">🧊 하한가 <span class="cnt" id="dnCnt"></span></div>
    <div class="list" id="dnList"><div class="empty-note">—</div></div></div>
</div>
<div class="h2">💬 증권사 신규 투자의견 <span class="cnt" id="opnCnt"></span></div>
<div class="list" id="opnList"><div class="empty-note">불러오는 중…</div></div>
<div class="h2">📰 종합 시황 · 공시 <span class="cnt" id="newsCnt"></span></div>
<div class="list" id="newsList"><div class="empty-note">불러오는 중…</div></div>
<script>
(function(){
 var mkt='kospi';
 function fmt(n,d){return Number(n).toLocaleString('en-US',{minimumFractionDigits:d===undefined?0:d,maximumFractionDigits:d===undefined?0:d});}
 function cls(v){return v>0?'up':(v<0?'dn':'fl');}
 function sgn(v){return v>0?'+':(v<0?'-':'');}
 function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
 function mc(v){return v>=10000?fmt(v/10000,1)+'조':fmt(v,0)+'억';}
 function openStock(code){try{if(code&&window.parent&&window.parent.miOpenStockTab)window.parent.miOpenStockTab(code);}catch(e){}}
 function obcls(o){o=(o||'').toUpperCase();
   if(/매수|BUY|OUTPERFORM|OVERWEIGHT|적극|비중확대|STRONG/.test(o))return 'buy';
   if(/매도|SELL|UNDERPERFORM|UNDERWEIGHT|축소|REDUCE/.test(o))return 'sell';
   return 'hold';}
 /* 지수값 자릿수 롤링 (우측 상단 KOSPI 티커와 동일 방식) */
 var RM_M=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 function ovRoll(el,oldStr,newStr,up){
   if(RM_M||!oldStr||oldStr===newStr){el.textContent=newStr;return;}
   var h=el.offsetHeight||34,nL=newStr.length,oL=oldStr.length,frag=document.createDocumentFragment();
   for(var p=0;p<nL;p++){var r=nL-1-p,nc=newStr.charAt(p),oc=(r<oL)?oldStr.charAt(oL-1-r):'';
     var cell=document.createElement('span');cell.className='rt-ch';
     if(oc===nc){cell.style.cssText='height:'+h+'px;line-height:'+h+'px;';cell.textContent=nc;}
     else{cell.style.cssText='height:'+h+'px;overflow:hidden;';
       var col=document.createElement('span');col.style.cssText='display:flex;flex-direction:column;';
       function rw(t){var s=document.createElement('span');s.style.cssText='height:'+h+'px;line-height:'+h+'px;';s.textContent=t;return s;}
       if(up){col.appendChild(rw(oc));col.appendChild(rw(nc));col.style.transform='translateY(0)';}
       else{col.appendChild(rw(nc));col.appendChild(rw(oc));col.style.transform='translateY(-'+h+'px)';}
       cell.appendChild(col);(function(cc,u){requestAnimationFrame(function(){requestAnimationFrame(function(){
         cc.style.transition='transform .62s cubic-bezier(.16,1,.3,1) '+Math.min(r,8)*26+'ms';
         cc.style.transform=u?'translateY(-'+h+'px)':'translateY(0)';});});})(col,up);}
     frag.appendChild(cell);}
   el.innerHTML='';el.appendChild(frag);
 }
 var ovBuilt=false,ovLast={};
 function buildOv(){
   document.getElementById('ovw').innerHTML=['kospi','kosdaq'].map(function(k){
     var label=k==='kospi'?'코스피':'코스닥',idx=k==='kospi'?'0001':'1001';
     return '<div class="ovcard" data-idx="'+idx+'" data-nm="'+label+'" role="button" tabindex="0" title="'+label+' 상세 보기">'+
       '<div class="ovhead"><span class="dot ov-dot" id="dot_'+k+'"></span><span class="ovname">'+label+'</span><span class="ovarrow">›</span></div>'+
       '<div class="ovval" id="val_'+k+'">—</div><div class="ovchg" id="chg_'+k+'"></div>'+
       '<div class="ovbd" id="bd_'+k+'"></div></div>';}).join('');
   ovBuilt=true;
 }
 function setOvCard(k,o,phase){
   var valEl=document.getElementById('val_'+k),chgEl=document.getElementById('chg_'+k),
       dotEl=document.getElementById('dot_'+k),bdEl=document.getElementById('bd_'+k);
   if(!valEl)return;
   if(!o){valEl.textContent='—';chgEl.textContent='';bdEl.innerHTML='';return;}
   var v=fmt(o.value,2),up=(ovLast[k]!=null)?(o.value>ovLast[k]):(o.direction==='▲');
   ovRoll(valEl,ovLast[k+'_s']||'',v,up);ovLast[k]=o.value;ovLast[k+'_s']=v;
   chgEl.className='ovchg '+cls(o.change);
   chgEl.textContent=(o.direction||'')+' '+sgn(o.change)+fmt(Math.abs(o.change),2)+' ('+sgn(o.change_pct)+fmt(Math.abs(o.change_pct),2)+'%)';
   dotEl.className='dot ov-dot'+(phase==='open'?' live':'');
   if(o.up_cnt!=null&&(o.up_cnt+(o.down_cnt||0))>0)
     bdEl.innerHTML='상승 <b class="u">'+fmt(o.up_cnt)+'</b> · 하락 <b class="d">'+fmt(o.down_cnt)+'</b>'+(o.uplm_cnt?' · 상한 '+o.uplm_cnt:'')+(o.lslm_cnt?' · 하한 '+o.lslm_cnt:'');
   else bdEl.innerHTML='';
 }
 function loadOverview(){
   fetch('/api/market_overview',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     if(!ovBuilt)buildOv();
     setOvCard('kospi',d.kospi,d.phase);setOvCard('kosdaq',d.kosdaq,d.phase);
     var open=d.phase==='open';
     document.getElementById('asof').textContent=({open:'실시간',pre:'개장 전 · 전일 종가',closed:'장 마감 · 종가',holiday:'휴장 · 종가'}[d.phase]||'')+
       (open?'':(' · '+(d.last_close||'')));
     document.getElementById('liveDot').className='dot'+(open?' live':'');
   }).catch(function(){});
 }
 function stockRow(r,i){
   var c=cls(r.change_pct);
   return '<div class="row" data-code="'+r.code+'">'+
     '<span class="rankc">'+(i+1)+'</span>'+
     '<span class="main"><span class="nm">'+esc(r.name)+'</span>'+
       '<span class="sub">'+mc(r.mcap)+(r.weight!=null?' · 비중 '+fmt(r.weight,2)+'%':'')+'</span></span>'+
     '<span class="right"><span class="px">'+fmt(r.price)+'</span>'+
       '<span class="chg '+c+'">'+sgn(r.change_pct)+fmt(Math.abs(r.change_pct),2)+'%</span></span></div>';
 }
 function loadTop(){
   fetch('/api/market_top?mkt='+mkt,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var rows=d.rows||[];
     document.getElementById('topCnt').textContent=rows.length?rows.length+'종목':'';
     document.getElementById('topList').innerHTML=rows.length?rows.map(stockRow).join(''):'<div class="empty-note">데이터 없음</div>';
   }).catch(function(){});
 }
 function udRow(r){
   var c=cls(r.change_pct);
   return '<div class="row" data-code="'+r.code+'">'+
     '<span class="main"><span class="nm">'+esc(r.name)+'</span>'+
       '<span class="sub">'+(r.volume>0?fmt(r.volume)+'주':'거래 전')+'</span></span>'+
     '<span class="right"><span class="px">'+fmt(r.price)+'</span>'+
       '<span class="chg '+c+'">'+sgn(r.change_pct)+fmt(Math.abs(r.change_pct),2)+'%</span></span></div>';
 }
 function loadUD(){
   fetch('/api/updown',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var up=d.up||[],dn=d.down||[];
     document.getElementById('upCnt').textContent=up.length+'종목';
     document.getElementById('dnCnt').textContent=dn.length+'종목';
     document.getElementById('upList').innerHTML=up.length?up.map(udRow).join(''):'<div class="empty-note">해당 종목 없음</div>';
     document.getElementById('dnList').innerHTML=dn.length?dn.map(udRow).join(''):'<div class="empty-note">해당 종목 없음</div>';
   }).catch(function(){});
 }
 function loadOpn(){
   fetch('/api/opinions_feed',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var rows=d.rows||[];
     document.getElementById('opnCnt').textContent=rows.length?rows.length+'건 · 최근 2주':'';
     document.getElementById('opnList').innerHTML=rows.length?rows.map(function(r){
       var uc=cls(r.upside);
       return '<div class="row" data-code="'+r.code+'">'+
         '<span class="obadge '+obcls(r.opinion)+'">'+esc(r.opinion)+'</span>'+
         '<span class="main"><span class="nm">'+esc(r.name)+'</span>'+
           '<span class="sub">'+esc(r.broker)+' · '+r.date+'</span></span>'+
         '<span class="right"><span class="px">목표 '+fmt(r.target)+'</span>'+
           '<span class="chg '+uc+'">'+sgn(r.upside)+fmt(Math.abs(r.upside),1)+'%</span></span></div>';
     }).join(''):'<div class="empty-note">최근 신규 투자의견 없음</div>';
   }).catch(function(){});
 }
 function loadNews(){
   fetch('/api/market_news',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     var rows=d.rows||[];
     document.getElementById('newsCnt').textContent=rows.length?rows.length+'건':'';
     document.getElementById('newsList').innerHTML=rows.length?rows.map(function(r){
       return '<div class="nrow'+(r.code?' clickable':'')+'" data-code="'+(r.code||'')+'">'+
         '<span class="ntime">'+esc(r.when)+'</span>'+
         '<span class="ntitle">'+esc(r.title)+'</span>'+
         '<span class="nsrc">'+esc(r.src)+'</span></div>';
     }).join(''):'<div class="empty-note">뉴스 없음</div>';
   }).catch(function(){});
 }
 /* 마켓맵 (트리맵) */
 function isDark(){return document.documentElement.classList.contains('dark');}
 function loadMap(){
   var el=document.getElementById('marketMap');if(!el)return;
   var asof=document.getElementById('mapAsof');if(asof)asof.textContent='조회 중…';
   fetch('/api/marketmap?mkt='+mkt,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     if(!d.ok||!d.fig||!window.Plotly){el.innerHTML='<div class="mapempty">마켓맵 데이터가 없습니다 (장중·종가 시점에 표시).</div>';if(asof)asof.textContent='';return;}
     var fig=d.fig;
     (fig.layout=fig.layout||{}).font={color:isDark()?'#cdd6e8':'#1d1d1f'};
     Plotly.react(el,fig.data,fig.layout,{responsive:true,displayModeBar:false});
     var now=new Date();
     if(asof)asof.textContent='기준 '+now.toLocaleString('ko-KR',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
   }).catch(function(){el.innerHTML='<div class="mapempty">마켓맵을 불러오지 못했습니다.</div>';if(asof)asof.textContent='';});
 }
 document.getElementById('seg').addEventListener('click',function(e){
   var b=e.target.closest('button');if(!b)return;mkt=b.dataset.mkt;
   document.querySelectorAll('#seg button').forEach(function(x){x.classList.toggle('on',x===b);});
   loadTop();loadMap();
 });
 function openIndex(code,name){try{if(window.parent&&window.parent.miOpenIndexTab)window.parent.miOpenIndexTab(code,name);}catch(e){}}
 document.body.addEventListener('click',function(e){
   var ov=e.target.closest('.ovcard');
   if(ov&&ov.dataset.idx){openIndex(ov.dataset.idx,ov.dataset.nm);return;}
   var row=e.target.closest('[data-code]');if(row&&row.dataset.code)openStock(row.dataset.code);
 });
 window.addEventListener('message',function(e){
   var d=e&&e.data;if(!d||!d.kmkt)return;
   document.documentElement.classList.toggle('dark',d.kmkt==='dark');
   loadMap();
 });
 loadOverview();loadTop();loadUD();loadOpn();loadNews();loadMap();
 setInterval(function(){if(!document.hidden)loadOverview();},3000);   // 지수 실시간 느낌
 setInterval(function(){if(!document.hidden)loadTop();},30000);
 setInterval(function(){if(!document.hidden)loadUD();},60000);
 setInterval(function(){if(!document.hidden)loadOpn();},600000);
 setInterval(function(){if(!document.hidden)loadNews();},120000);
 // 마켓맵은 실시간 갱신하지 않음 — 진입·토글 전환 시에만 조회(기준시점 표기)
})();
</script>
</body></html>"""

_RT_STYLE = """<style id="m4-rt">
.price-hero{transition:background .5s ease,box-shadow .5s ease;}
.rt-live{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;
 letter-spacing:.02em;vertical-align:middle;margin-left:8px;opacity:.92;}
.rt-live .rt-dot{width:7px;height:7px;border-radius:50%;background:#ff5470;
 box-shadow:0 0 0 0 rgba(255,84,112,.7);animation:rtPulse 1.6s ease-in-out infinite;}
@keyframes rtPulse{0%{box-shadow:0 0 0 0 rgba(255,84,112,.6);}
 70%{box-shadow:0 0 0 6px rgba(255,84,112,0);}100%{box-shadow:0 0 0 0 rgba(255,84,112,0);}}
/* 폐장·휴장: 회색 점 + 깜빡임 정지 (작업3) */
.rt-live.closed .rt-dot{background:#9aa0ab;animation:none;box-shadow:none;}
/* 가격·등락 롤링(자릿수별 슬라이드) 전환: 상승=위로, 하락=아래로 */
.ph-price .rt-ch,.ph-chg .rt-ch{display:inline-block;vertical-align:top;font-variant-numeric:tabular-nums;}
.ph-price .rt-col,.ph-chg .rt-col{display:block;will-change:transform;}
.ph-chg{display:inline-flex;align-items:center;vertical-align:middle;letter-spacing:.4px;padding:0 2px;}
@media (prefers-reduced-motion:reduce){.rt-live .rt-dot{animation:none!important;}}
</style>"""

_RT_JS = """<script>
(function(){
 var CODE='__CODE__';
 if(!CODE)return;
 var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 var lastPrice=null,lastText=null,lastChgText=null;
 var EASE='cubic-bezier(.16,1,.3,1)',DUR=0.62;
 function fmt(n){return Number(n).toLocaleString('en-US',{maximumFractionDigits:0});}
 function priceEl(){return document.querySelector('.price-hero .ph-price');}
 function etfKpiVal(){ // ETF 헤더의 '현재가' KPI 값
   var ks=document.querySelectorAll('.etf-head .eh-kpi'),i;
   for(i=0;i<ks.length;i++){var l=ks[i].querySelector('.k-label');
     if(l&&/현재가/.test(l.textContent)){return ks[i].querySelector('.k-val');}}
   return null;}
 // 정적(안 바뀐) 자릿수 셀
 function staticCell(h,ch){
   var c=document.createElement('span');c.className='rt-ch';
   c.style.height=h+'px';c.style.lineHeight=h+'px';c.textContent=ch;return c;}
 // 굴러가는(바뀐) 자릿수 셀 — up: 위로 / down: 아래로, delay(ms) 로 살짝 계단식
 function rollCell(h,oldCh,newCh,up,delay){
   var cell=document.createElement('span');cell.className='rt-ch';
   cell.style.height=h+'px';cell.style.overflow='hidden';
   var col=document.createElement('span');col.className='rt-col';
   function d(t){var s=document.createElement('span');s.style.display='block';
     s.style.height=h+'px';s.style.lineHeight=h+'px';s.textContent=t;return s;}
   if(up){col.appendChild(d(oldCh));col.appendChild(d(newCh));col.style.transform='translateY(0)';}
   else  {col.appendChild(d(newCh));col.appendChild(d(oldCh));col.style.transform='translateY(-'+h+'px)';}
   cell.appendChild(col);
   requestAnimationFrame(function(){requestAnimationFrame(function(){
     col.style.transition='transform '+DUR+'s '+EASE+' '+delay+'ms';
     col.style.transform=up?'translateY(-'+h+'px)':'translateY(0)';});});
   return cell;}
 // 변한 자릿수만 굴리는 가격 전환 (오른쪽 자리 기준 정렬)
 function rollPrice(pe,oldStr,newStr,up){
   if(RM||!oldStr||oldStr===newStr){pe.textContent=newStr;return;}
   var h=pe.offsetHeight,nL=newStr.length,oL=oldStr.length;
   var frag=document.createDocumentFragment(),p,r,nc,oc;
   for(p=0;p<nL;p++){
     r=nL-1-p;                              // 오른쪽에서 r번째 (0=최하위)
     nc=newStr.charAt(p);
     oc=(r<oL)?oldStr.charAt(oL-1-r):'';    // 오른쪽 정렬된 이전 글자
     if(oc===nc)frag.appendChild(staticCell(h,nc));
     else frag.appendChild(rollCell(h,oc,nc,up,Math.min(r,8)*26));
   }
   pe.textContent='';pe.appendChild(frag);
 }
 function setHero(d){
   var pe=priceEl();if(!pe)return;
   var txt=fmt(d.price)+'원';
   var prev=(lastText!==null)?lastText:(pe.textContent||'').trim();
   var up=(lastPrice!==null)?(d.price>lastPrice):(d.direction==='\\u25b2');
   if(prev!==txt){rollPrice(pe,prev,txt,up);}
   lastPrice=d.price;lastText=txt;
   pe.__cu=1; // FX 카운트업이 덮어쓰지 않도록 잠금
   // 등락 배지 + 박스색
   var box=document.querySelector('.price-hero');
   if(box){box.classList.remove('up','down','flat');
     box.classList.add(d.direction==='\\u25b2'?'up':(d.direction==='\\u25bc'?'down':'flat'));}
   var chg=document.querySelector('.price-hero .ph-chg');
   if(chg){var sign=d.change>0?'+':'';
     var newChgTxt=d.direction+' '+sign+fmt(d.change)+'원 ('+(d.change_pct>0?'+':'')+d.change_pct.toFixed(2)+'%)';
     if(newChgTxt!==lastChgText){rollPrice(chg,lastChgText||'',newChgTxt,up);}
     lastChgText=newChgTxt;}
   // 메타 + LIVE 점 — 장 단계(개장/개장 전/폐장/휴장) 반영 (작업1·3)
   var ph=d.phase||(d.market_open?'open':'closed');
   var meta=document.querySelector('.price-hero .ph-meta');
   if(meta){
     if(ph==='open'){var now=new Date();
       meta.textContent='실시간 · '+(d.src||'KRX')+' · '+now.toLocaleTimeString('ko-KR',{hour12:false})+' 갱신';}
     else if(ph==='pre'){meta.textContent='개장 전 · 전일 종가 · '+(d.last_close||'')+' · 한국투자증권 KIS';}
     else if(ph==='holiday'){meta.textContent='휴장 · 전일 종가 · '+(d.last_close||'')+' · 한국투자증권 KIS';}
     else{meta.textContent='종가 · '+(d.last_close||'')+' 폐장(NXT) · 한국투자증권 KIS';}}
   var live=document.querySelector('.price-hero .rt-live');
   if(live){live.classList.toggle('closed',ph!=='open');
     var lt=live.childNodes[live.childNodes.length-1];
     var ltxt=(ph==='open')?('실시간('+(d.src||'KIS')+')')
       :(ph==='pre'?'개장 전':(ph==='holiday'?'휴장':'폐장 · 종가'));
     if(lt&&lt.nodeType===3){if(lt.textContent!==ltxt)lt.textContent=ltxt;}
     else{live.insertAdjacentText('beforeend',ltxt);}}
   // ETF 현재가 KPI
   var kv=etfKpiVal();
   if(kv){var unit=kv.querySelector('.k-unit');
     kv.textContent=fmt(d.price);if(unit)kv.appendChild(unit);else kv.insertAdjacentHTML('beforeend','<span class="k-unit">원</span>');
     kv.__cu=1;}
 }
 function tag(){ // 현재가 옆 LIVE 표시
   var top=document.querySelector('.price-hero .ph-top');
   if(top&&!top.querySelector('.rt-live')){
     var s=document.createElement('span');s.className='rt-live';
     s.innerHTML='<span class="rt-dot"></span>';
     top.appendChild(s);}
 }
  window.addEventListener('message', function(e){if(e.data&&e.data.mi_tab_active!==undefined){window.MI_TAB_ACTIVE=e.data.mi_tab_active;}});
 // ETF iNAV KPI — KIS NAV(웹소켓/REST)로 갱신 (작업1)
 function etfNavKpi(){
   var ks=document.querySelectorAll('.etf-head .eh-kpi'),i;
   for(i=0;i<ks.length;i++){var l=ks[i].querySelector('.k-label');
     if(l&&/iNAV|기준가/.test(l.textContent)){return ks[i];}}
   return null;}
 function pollNav(){
   if(document.hidden || window.MI_APP_ACTIVE === false || window.MI_TAB_ACTIVE === false)return;
   var k=etfNavKpi();if(!k)return;
   fetch('/api/etf_nav?code='+encodeURIComponent(CODE),{cache:'no-store'})
     .then(function(r){return r.json();})
     .then(function(d){
       if(!d||!d.ok||!d.nav)return;
       var kv=k.querySelector('.k-val');
       if(kv){var unit=kv.querySelector('.k-unit');
         kv.textContent=Number(d.nav).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
         if(unit)kv.appendChild(unit);else kv.insertAdjacentHTML('beforeend','<span class="k-unit">원</span>');
         kv.__cu=1;}
       var sub=k.querySelector('.k-sub')||k.querySelector('.k-label+*+*');
       if(sub&&d.nav_vrss!==undefined&&d.nav_vrss!==null){
         sub.textContent=(d.dirc||'')+' '+Math.abs(d.nav_vrss).toLocaleString('en-US',{maximumFractionDigits:2})+
           ' ('+Math.abs(d.nav_ctrt||0).toFixed(2)+'%)';}
     }).catch(function(){});
 }
 var alive=true,first=true,closedN=0;
 function poll(){
   if(!alive || window.MI_APP_ACTIVE === false || window.MI_TAB_ACTIVE === false)return;
   if(document.hidden){return;} // 숨은 탭은 건너뜀
   fetch('/api/realtime?code='+encodeURIComponent(CODE),{cache:'no-store'})
     .then(function(r){return r.json();})
     .then(function(d){if(d&&d.ok){if(first){tag();first=false;}
       // 폐장 중엔 16회(32초)에 한 번만 실제 반영해도 충분하지만 표시는 즉시 정합
       setHero(d);}})
     .catch(function(){});
 }
 // FX 카운트업(최초 850ms) 이후 시작
 setTimeout(function(){poll();setInterval(poll,2000);
   pollNav();setInterval(pollNav,20000);},1100);
 window.addEventListener('pagehide',function(){alive=false;});
})();</script>"""

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
 // ProMotion 대응: setInterval(40ms·25fps) 대신 requestAnimationFrame 으로 회전.
 // rAF 는 디스플레이 주사율(ProMotion 120Hz)에 맞춰 호출되므로 회전이 매끄럽다.
 // delta-time 으로 각속도를 환산해 기존과 동일한 속도(0.15 rad/s·intro≈2.2s)를 유지.
 function autoRotate(gd){
   var R=2.4,Z=1.05,a=Math.atan2(1.5,1.7),paused=false,intro=0,last=performance.now(),vis=true;
   var SPEED=0.15,INTRO=0.4545;            // rad/s, intro/s (구 setInterval 값 환산)
   gd.addEventListener('mouseenter',function(){paused=true;});
   gd.addEventListener('mouseleave',function(){paused=false;last=performance.now();});
   // 화면 밖으로 스크롤된 3D 차트는 회전 렌더 생략(WebGL relayout 발열↓)
   try{var io=new IntersectionObserver(function(es){vis=es[0].isIntersecting;if(vis)last=performance.now();},{threshold:0.05});io.observe(gd);}catch(e){}
   function frame(now){
     if(!document.body.contains(gd))return;             // 제거된 차트면 루프 종료
     if(!vis || document.hidden || window.MI_APP_ACTIVE === false){ last=now; requestAnimationFrame(frame); return; } // 화면 밖·백그라운드·절전 → 렌더 생략
     var dt=Math.min((now-last)/1000,0.05);last=now;    // 120Hz면 dt≈8.3ms
     if(gd._fullLayout&&gd._fullLayout.scene&&!paused&&window.Plotly){
       if(intro<1)intro=Math.min(intro+INTRO*dt,1);
       a+=SPEED*dt;
       try{Plotly.relayout(gd,{'scene.camera.eye':{x:R*Math.cos(a),y:R*Math.sin(a),z:Z+(1-intro)*1.3}});}catch(e){}
     }
     requestAnimationFrame(frame);
   }
   requestAnimationFrame(frame);
 }
 if(!RM&&window.Plotly){document.querySelectorAll('.m4-card-3d .plotly-graph-div').forEach(function(gd){
   var n=0;(function wait(){if(gd._fullLayout&&gd._fullLayout.scene){autoRotate(gd);return;}
     if(n++<50)setTimeout(wait,80);})();});}
})();
</script>"""

_PDF_VIEW_HTML = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>__TITLE__</title>
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bar:#f4f5f9;--ink:#1d1d1f;--line:rgba(60,60,67,.14);--btn:rgba(118,118,128,.12);--accent:#0a84ff;}
html.dark{--bar:#15171e;--ink:#eef3ff;--line:rgba(255,255,255,.12);--btn:rgba(120,120,128,.26);}
*{box-sizing:border-box;} html,body{margin:0;height:100%;}
body{display:flex;flex-direction:column;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;background:var(--bar);color:var(--ink);}
.bar{display:flex;align-items:center;gap:8px;padding:9px 14px;border-bottom:.5px solid var(--line);flex:none;
 -webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);}
.ttl{font-size:13.5px;font-weight:700;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;}
.zg{display:inline-flex;align-items:center;gap:2px;background:var(--btn);border-radius:10px;padding:3px;flex:none;}
.zg button{border:0;background:transparent;color:var(--ink);font-size:15px;font-weight:700;width:30px;height:28px;border-radius:8px;cursor:pointer;}
.zg button:hover{background:rgba(127,127,127,.18);}
.zg .zl{font-size:12.5px;font-weight:700;min-width:46px;text-align:center;font-variant-numeric:tabular-nums;}
.act{border:0;background:var(--btn);color:var(--ink);font-size:12.5px;font-weight:600;padding:7px 12px;border-radius:9px;cursor:pointer;flex:none;}
.act.pri{background:var(--accent);color:#fff;}
.wrap{flex:1;min-height:0;background:#525659;}
iframe{width:100%;height:100%;border:0;display:block;background:#525659;}
</style></head><body>
<div class="bar">
  <span class="ttl">__TITLE__</span>
  <div class="zg"><button id="zo" title="축소">−</button><span class="zl" id="zl">맞춤</span><button id="zi" title="확대">+</button></div>
  <button class="act" id="zfit">너비맞춤</button>
  <button class="act pri" id="dl">새 창</button>
</div>
<div class="wrap"><iframe id="pf"></iframe></div>
<script>
var SRC=__SRC__;var pf=document.getElementById('pf'),zl=document.getElementById('zl');
var levels=[50,67,75,85,100,110,125,150,175,200,250,300];var zi=-1; // -1 = page-width(맞춤)
function applyZoom(){
  var frag=(zi<0)?'page-width':String(levels[zi]);
  pf.src=SRC+'#zoom='+frag+'&toolbar=0&navpanes=0';
  zl.textContent=(zi<0)?'맞춤':(levels[zi]+'%');
}
document.getElementById('zi').onclick=function(){ if(zi<0){zi=levels.indexOf(110);} else if(zi<levels.length-1){zi++;} applyZoom();};
document.getElementById('zo').onclick=function(){ if(zi<0){zi=levels.indexOf(85);} else if(zi>0){zi--;} applyZoom();};
document.getElementById('zfit').onclick=function(){zi=-1;applyZoom();};
document.getElementById('dl').onclick=function(){window.open(SRC,'_blank');};
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)document.documentElement.classList.toggle('dark',e.data.kmkt==='dark');});
applyZoom();
</script>
<script>window.KMKT_ASK=function(){return{scope:__ASK_SCOPE__,id:__ASK_ID__};};</script>
__KMKT_ASK_WIDGET__
</body></html>
"""

_RESEARCH_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="research"><head><meta charset="utf-8">
<title>증권사 리포트</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f4f5f9;--card:rgba(255,255,255,.86);--ink:#1d1d1f;--sub:rgba(60,60,67,.6);
 --line:rgba(60,60,67,.12);--row:rgba(10,132,255,.06);--up:#FF3B30;--accent:#0A84FF;--chip:rgba(118,118,128,.12);}
html.dark{--bg:#0b0f1a;--card:rgba(28,30,38,.82);--ink:#eef3ff;--sub:#9aa6bd;--line:rgba(255,255,255,.1);
 --row:rgba(90,166,255,.1);--up:#FF453A;--accent:#0A84FF;--chip:rgba(120,120,128,.22);}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;background:var(--bg);
 color:var(--ink);-webkit-font-smoothing:antialiased;padding:20px 22px 36px;}
.hd{display:flex;align-items:baseline;gap:10px;margin-bottom:4px;}
h2{margin:0;font-size:22px;font-weight:800;letter-spacing:-.02em;}
.lead{color:var(--sub);font-size:13px;margin:2px 0 16px;}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;}
.tab{font-size:13.5px;font-weight:600;padding:8px 15px;border-radius:100px;border:1px solid var(--line);
 background:var(--card);color:var(--ink);cursor:pointer;transition:all .18s cubic-bezier(.32,.72,0,1);}
.tab:hover{transform:translateY(-1px);}
.tab.on{background:var(--accent);color:#fff;border-color:transparent;box-shadow:0 6px 16px rgba(10,132,255,.3);}
.state{color:var(--sub);font-size:14px;padding:36px 2px;text-align:center;}
.list{display:flex;flex-direction:column;gap:10px;}
.rp-item{display:flex;align-items:center;gap:14px;background:var(--card);border:.5px solid var(--line);
 border-radius:14px;padding:14px 16px;box-shadow:0 6px 20px rgba(0,0,0,.05);
 -webkit-backdrop-filter:saturate(180%) blur(24px);backdrop-filter:saturate(180%) blur(24px);}
.rp-main{flex:1;min-width:0;}
.rp-title{font-size:14.5px;font-weight:700;line-height:1.45;color:var(--ink);
 display:flex;align-items:center;gap:7px;}
.rp-title .tt{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.rp-badge{flex:none;font-size:10px;font-weight:800;color:#fff;background:var(--up);border-radius:6px;padding:2px 6px;}
.rp-meta{font-size:12px;color:var(--sub);margin-top:5px;display:flex;flex-wrap:wrap;gap:8px;}
.rp-meta .stk{color:var(--accent);font-weight:600;}
.rp-acts{flex:none;display:flex;gap:7px;}
.rp-btn{font-size:12px;font-weight:600;padding:7px 12px;border-radius:10px;cursor:pointer;border:1px solid var(--line);
 background:var(--chip);color:var(--ink);transition:all .15s;white-space:nowrap;}
.rp-btn:hover{transform:translateY(-1px);}
.rp-btn.sum{background:linear-gradient(135deg,var(--accent),#9b6bff);color:#fff;border-color:transparent;}
.rp-btn:disabled{opacity:.5;cursor:default;transform:none;}
.rp-sum{font-size:13px;line-height:1.7;color:var(--ink);background:var(--row);border:1px solid var(--line);
 border-radius:12px;padding:13px 15px;margin:-2px 0 4px;white-space:normal;}
.rp-sum .rk{font-size:11.5px;opacity:.62;border-left:2px solid rgba(10,132,255,.4);padding:3px 9px;margin:0 0 8px;
 white-space:pre-wrap;max-height:120px;overflow:auto;}
.pager{display:flex;justify-content:center;gap:10px;margin-top:18px;}
.pager button{font-size:13px;font-weight:600;padding:8px 16px;border-radius:100px;border:1px solid var(--line);
 background:var(--card);color:var(--ink);cursor:pointer;}
.pager button:disabled{opacity:.4;cursor:default;}
@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
</style></head>
<body>
<div class="hd"><h2>📑 증권사 리포트</h2></div>
<p class="lead">네이버 금융 리서치 — 카테고리별 최신 리포트. 원문 PDF 보기 + 로컬 AI 요약. (클릭 시 원문 PDF)</p>
<div class="tabs" id="tabs"></div>
<div id="state" class="state">리포트를 불러오는 중…</div>
<div class="list" id="list"></div>
<div class="pager" id="pager" style="display:none;">
  <button id="prev">‹ 이전</button><span id="pgInfo" style="align-self:center;font-size:13px;color:var(--sub);"></span><button id="next">다음 ›</button>
</div>
<script>
var CATS=[['daily','📊 데일리'],['company','🏢 종목분석'],['industry','🏭 산업분석'],['invest','🎯 투자전략'],['economy','🌐 경제분석'],['debenture','💵 채권분석'],['market','📊 종합시황'],['bok','🏦 한국은행'],['bok_mp','🏛️ 금융통화위원회']];
var cat='daily',page=1;
var $=function(s){return document.querySelector(s);};
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt){document.documentElement.classList.toggle('dark',e.data.kmkt==='dark');}});
function today(){var d=new Date();function p(n){return(n<10?'0':'')+n;}return p(d.getFullYear()%100)+'.'+p(d.getMonth()+1)+'.'+p(d.getDate());}
function renderTabs(){
  $('#tabs').innerHTML=CATS.map(function(c){return '<button class="tab'+(c[0]===cat?' on':'')+'" data-c="'+c[0]+'">'+c[1]+'</button>';}).join('');
  document.querySelectorAll('#tabs .tab').forEach(function(b){b.addEventListener('click',function(){cat=b.dataset.c;page=1;load();});});
}
function openPdf(c,nid,title){
  var raw='/research_pdf2?cat='+encodeURIComponent(c)+'&nid='+encodeURIComponent(nid);
  var u='/pdf_view?src='+encodeURIComponent(raw)+'&title='+encodeURIComponent(title||'리포트');
  try{if(window.parent&&window.parent.miOpenUrlTab){window.parent.miOpenUrlTab('rpdf:'+nid,{url:u,title:(title||'리포트').slice(0,16)+' 📄',icon:'📄',loading:'PDF 불러오는 중…'});return;}}catch(e){}
  window.open(u,'_blank');
}
function summarize(c,nid,title,panel,btn){
  if(panel._busy)return;panel._busy=1;btn.disabled=true;btn.textContent='요약 중…';
  panel.style.display='block';
  panel.innerHTML='<div class="rk" id="rk" style="display:none"></div><span id="st">불러오는 중 · · ·</span>';
  var rk=panel.querySelector('#rk'),st=panel.querySelector('#st'),started=false;
  st.className='kmkt-md';   // AI 답변 마크다운 렌더(공용 스타일)
  var ansBuf='',md=window.kmktMd||function(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');};
  var _ap=(window.kmktAiProv?window.kmktAiProv():{}),_aq='&provider='+encodeURIComponent(_ap.provider||'local')+'&gemini_model='+encodeURIComponent(_ap.gemini_model||'')+'&gsys='+encodeURIComponent(_ap.gsys||'');
  fetch('/api/research_summary?cat='+encodeURIComponent(c)+'&nid='+encodeURIComponent(nid)+'&title='+encodeURIComponent(title||'')+_aq)
    .then(async function(r){
      var rd=r.body.getReader(),dec=new TextDecoder('utf-8'),buf='';
      function e2(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');}
      while(true){var rr=await rd.read();if(rr.done)break;
        buf+=dec.decode(rr.value,{stream:true});var ls=buf.split('\n');buf=ls.pop();
        for(var i=0;i<ls.length;i++){var ln=ls[i];if(ln.indexOf('data: ')===0){
          try{var dj=JSON.parse(ln.substring(6));if(dj.text){
            if(dj.kind==='reasoning'){rk.style.display='block';rk.insertAdjacentHTML('beforeend',e2(dj.text));}
            else{if(!started){started=true;st.innerHTML='';}ansBuf+=dj.text;st.innerHTML=md(ansBuf);}
          }}catch(e){}}}
      }
      btn.disabled=false;btn.textContent='✨ AI 요약';panel._busy=0;
    }).catch(function(e){st.innerHTML='<span style="color:var(--up)">요약 실패: '+esc(e.message)+'</span>';btn.disabled=false;btn.textContent='✨ AI 요약';panel._busy=0;});
}
function render(rows){
  if(!rows||!rows.length){$('#list').innerHTML='<div class="state">리포트가 없습니다.</div>';return;}
  var td=today();
  $('#list').innerHTML=rows.map(function(r,i){
    var badge=(r.date===td)?'<span class="rp-badge">TODAY</span>':'';
    var meta=[r.broker?esc(r.broker):''].concat(r.stock?['<span class="stk">'+esc(r.stock)+'</span>']:[]).concat(r.date?[esc(r.date)]:[]).filter(Boolean).join(' · ');
    return '<div class="rp-item"><div class="rp-main">'+
      '<div class="rp-title">'+badge+'<span class="tt">'+esc(r.title)+'</span></div>'+
      '<div class="rp-meta">'+meta+'</div></div>'+
      '<div class="rp-acts">'+(r.pdf?'<button class="rp-btn pdf" data-i="'+i+'">PDF 원문</button>':'')+
      '<button class="rp-btn sum" data-i="'+i+'">✨ AI 요약</button></div></div>'+
      '<div class="rp-sum" id="sum'+i+'" style="display:none"></div>';
  }).join('');
  document.querySelectorAll('#list .rp-btn.pdf').forEach(function(b){b.addEventListener('click',function(){var r=rows[b.dataset.i];openPdf(r.cat,r.nid,r.title);});});
  document.querySelectorAll('#list .rp-btn.sum').forEach(function(b){b.addEventListener('click',function(){var r=rows[b.dataset.i];summarize(r.cat,r.nid,r.title,document.getElementById('sum'+b.dataset.i),b);});});
}
function load(){
  renderTabs();$('#state').style.display='block';$('#state').textContent='리포트를 불러오는 중…';$('#list').innerHTML='';$('#pager').style.display='none';
  fetch('/api/research?cat='+cat+'&page='+page,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    $('#state').style.display='none';render(d.rows||[]);
    $('#pager').style.display='flex';$('#pgInfo').textContent=page+' 페이지';$('#prev').disabled=(page<=1);
  }).catch(function(){$('#state').textContent='네트워크 오류';});
}
$('#prev').addEventListener('click',function(){if(page>1){page--;load();}});
$('#next').addEventListener('click',function(){page++;load();});
load();
</script>
</body></html>
"""

_INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="index"><head><meta charset="utf-8">
<title>지수 상세</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f0f1f5;--card:rgba(255,255,255,.92);--ink:#1d1d1f;--sub:rgba(60,60,67,.56);
 --line:rgba(60,60,67,.11);--row:rgba(10,132,255,.05);--up:#FF3B30;--dn:#2E75B6;--accent:#0A84FF;
 --hero-bg-up:#FF3B30;--hero-bg-dn:#2E75B6;}
html.dark{--bg:#0b0f1a;--card:rgba(24,26,36,.88);--ink:#eef3ff;--sub:#8a97b5;
 --line:rgba(255,255,255,.09);--row:rgba(90,166,255,.08);--up:#FF453A;--dn:#64B5FF;--accent:#0A84FF;
 --hero-bg-up:#c0241a;--hero-bg-dn:#144fa0;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
 background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
.hero{margin:12px 14px;border-radius:16px;padding:16px 20px;background:var(--hero-bg-up);color:#fff;
 transition:background .4s ease;position:relative;overflow:hidden;}
.hero,.hero *{color:#fff;}
.hero.dn{background:var(--hero-bg-dn);}
.hero::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 20% 30%,rgba(255,255,255,.13),transparent 60%);pointer-events:none;}
.h-top{display:flex;align-items:center;gap:9px;flex-wrap:wrap;}
.h-nm{font-size:17px;font-weight:800;letter-spacing:-.01em;}
.badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;background:rgba(255,255,255,.18);}
.badge.open{background:#FFD60A;color:#000 !important;}
.h-rt-badge{font-size:10.5px;background:rgba(255,255,255,.2);border-radius:6px;padding:2px 7px;font-weight:700;
 animation:hb 2s ease-in-out infinite;margin-left:auto;}
@keyframes hb{0%,100%{opacity:1;}50%{opacity:.5;}}
.h-px{font-size:40px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-top:6px;display:inline-block;}
.h-px .rt-ch{display:inline-block;overflow:hidden;vertical-align:bottom;}
.h-chg{font-size:17px;font-weight:700;margin-top:3px;}
.h-sub{font-size:12.5px;opacity:.78;margin-top:5px;}
.main{display:grid;grid-template-columns:1fr 300px;gap:12px;padding:0 14px 22px;align-items:start;}
@media(max-width:820px){.main{grid-template-columns:1fr;}}
.col-left,.col-right{display:flex;flex-direction:column;gap:12px;}
.card{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(28px);backdrop-filter:saturate(180%) blur(28px);
 border:.5px solid var(--line);border-radius:14px;padding:15px 17px;box-shadow:0 8px 28px rgba(0,0,0,.06);}
h3{font-size:13.5px;font-weight:700;margin-bottom:11px;}
.note{font-size:11.5px;color:var(--sub);}
.state{color:var(--sub);font-size:15px;padding:40px 16px;text-align:center;}.err{color:var(--up);}
.seg{display:inline-flex;border:.5px solid var(--line);border-radius:9px;overflow:hidden;margin-left:auto;}
.seg button{background:transparent;border:0;color:var(--sub);font:inherit;font-size:12.5px;padding:6px 14px;cursor:pointer;}
.seg button.on{background:var(--accent);color:#fff;}
.cv-wrap{position:relative;}
canvas{width:100%;height:380px;display:block;}
.cv-tip{position:absolute;pointer-events:none;z-index:5;display:none;min-width:130px;background:rgba(20,22,32,.92);
 color:#fff;border-radius:9px;padding:9px 11px;font-size:12px;line-height:1.55;box-shadow:0 6px 20px rgba(0,0,0,.3);
 -webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);white-space:nowrap;}
.cv-tip .tip-d{font-weight:700;opacity:.8;margin-bottom:3px;}
.cv-tip .tip-r{display:flex;justify-content:space-between;gap:16px;}.cv-tip .tip-r .k{opacity:.65;}
.mgrid{display:grid;grid-template-columns:1fr 1fr;gap:0;}
.mg{padding:11px 12px;border-bottom:.5px solid var(--line);}
.mg .k{font-size:11.5px;color:var(--sub);}.mg .v{font-size:16px;font-weight:700;margin-top:3px;}
.bd-row{display:flex;align-items:center;gap:9px;padding:8px 2px;font-size:13px;}
.bd-row .bk{width:42px;color:var(--sub);font-size:12px;}
.bd-row .bv{width:64px;text-align:right;font-weight:700;}
.bd-bar{flex:1;height:6px;border-radius:3px;background:var(--line);overflow:hidden;}
.bd-bar i{display:block;height:100%;border-radius:3px;}
.news .it{display:flex;gap:10px;align-items:baseline;padding:9px 2px;border-bottom:.5px solid var(--line);font-size:13.5px;}
.news .it:last-child{border-bottom:0;}.news .it.clk{cursor:pointer;}.news .it.clk:hover{color:var(--accent);}
.news .t{font-weight:500;min-width:0;}.news .meta{margin-left:auto;flex:none;font-size:11px;color:var(--sub);}
.up{color:var(--up);}.dn{color:var(--dn);}
</style></head>
<body>
<div id="state" class="state">지수 정보를 불러오는 중…</div>
<div id="body" style="display:none;">
  <div class="hero" id="hero">
    <div class="h-top"><span class="h-nm" id="nm"></span><span class="badge" id="mktBadge"></span>
      <span class="h-rt-badge" id="rtBadge" style="display:none;">● 실시간</span></div>
    <div><span class="h-px" id="hPx">—</span></div>
    <div class="h-chg" id="hChg"></div>
    <div class="h-sub" id="hMeta"></div>
  </div>
  <div class="main">
    <div class="col-left">
      <section class="card">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <h3 style="margin:0;">📈 지수 차트</h3>
          <div class="seg" id="seg"><button data-p="D" class="on">일</button><button data-p="W">주</button><button data-p="M">월</button><button data-p="Y">년</button></div>
        </div>
        <div class="cv-wrap"><canvas id="cv"></canvas><div id="cvTip" class="cv-tip"></div></div>
        <div class="note" style="margin-top:8px;">캔들 상승 <span class="up">●</span> / 하락 <span class="dn">●</span> · MA5·20·60·120 · 하단 거래량 · KIS 지수시세</div>
      </section>
      <section class="card"><h3>📰 시장 뉴스</h3><div class="news" id="news"><div class="note" style="padding:6px 0;">불러오는 중…</div></div></section>
    </div>
    <div class="col-right">
      <section class="card"><h3>📋 시세 정보</h3><div class="mgrid" id="mgrid"></div></section>
      <section class="card"><h3>📊 등락 종목수</h3><div id="breadth"><div class="note" style="padding:4px 0;">—</div></div></section>
    </div>
  </div>
</div>
<script>
var $=function(s){return document.querySelector(s);};
var P=new URLSearchParams(location.search),code=(P.get('code')||'0001').trim(),
    kname=P.get('name')||'',period='D',rows=[],info=null,lastPxStr='',pollTid=null,hoverIdx=-1,geo=null;
var RM=(window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches);
function setTheme(d){document.documentElement.classList.toggle('dark',!!d);draw();}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)setTheme(e.data.kmkt==='dark');});
function fmt(n,d){return (Number(n)||0).toLocaleString('en-US',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function fmtI(n){return (Number(n)||0).toLocaleString('en-US',{maximumFractionDigits:0});}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fail(m){$('#state').className='state err';$('#state').textContent=m;}

/* 롤링 숫자 */
function rollPrice(pe,oldStr,newStr,up){
  if(RM||!oldStr||oldStr===newStr){pe.textContent=newStr;return;}
  var h=parseInt(getComputedStyle(pe).fontSize)||40,nL=newStr.length,oL=oldStr.length,frag=document.createDocumentFragment();
  for(var p=0;p<nL;p++){var r=nL-1-p,nc=newStr.charAt(p),oc=(r<oL)?oldStr.charAt(oL-1-r):'';
    var cell=document.createElement('span');cell.className='rt-ch';
    if(oc===nc){cell.style.cssText='height:'+h+'px;line-height:'+h+'px;';cell.textContent=nc;}
    else{cell.style.cssText='height:'+h+'px;overflow:hidden;';
      var col=document.createElement('span');col.style.cssText='display:flex;flex-direction:column;';
      function rw(t){var s=document.createElement('span');s.style.cssText='height:'+h+'px;line-height:'+h+'px;';s.textContent=t;return s;}
      if(up){col.appendChild(rw(oc));col.appendChild(rw(nc));col.style.transform='translateY(0)';}
      else{col.appendChild(rw(nc));col.appendChild(rw(oc));col.style.transform='translateY(-'+h+'px)';}
      cell.appendChild(col);(function(cc,u,rr){requestAnimationFrame(function(){requestAnimationFrame(function(){
        cc.style.transition='transform .62s cubic-bezier(.16,1,.3,1) '+Math.min(rr,8)*26+'ms';
        cc.style.transform=u?'translateY(-'+h+'px)':'translateY(0)';});});})(col,up,r);}
    frag.appendChild(cell);}
  pe.textContent='';pe.appendChild(frag);}

function updateHero(d){
  var up=d.direction==='▲'||d.change>0,dn=d.direction==='▼'||d.change<0;
  $('#hero').className='hero'+(dn?' dn':'');
  var ns=fmt(d.value);
  if(ns!==lastPxStr){var tu=lastPxStr?(d.value>=parseFloat(lastPxStr.replace(/,/g,'')||'0')):up;rollPrice($('#hPx'),lastPxStr,ns,tu);}
  lastPxStr=ns;
  var s=d.change>0?'+':'';
  $('#hChg').textContent=(up?'▲ ':dn?'▼ ':'')+s+fmt(Math.abs(d.change))+' ('+(d.change_pct>0?'+':'')+fmt(d.change_pct)+'%)';
  var ph=d.phase||'';
  var open=ph==='open';
  $('#mktBadge').className='badge'+(open?' open':'');
  $('#mktBadge').textContent={open:'장중',pre:'개장 전',closed:'장 마감',holiday:'휴장'}[ph]||'';
  $('#rtBadge').style.display=open?'':'none';
  var now=new Date();
  $('#hMeta').textContent=(open?'실시간 · '+now.toLocaleTimeString('ko-KR',{hour12:false})+' 갱신':('전일 종가 기준'+(d.last_close?' · '+d.last_close:'')));
  if(d.up_cnt!=null)renderBreadth(d);
}
function renderBreadth(d){
  var u=d.up_cnt||0,dn=d.down_cnt||0,fl=d.flat_cnt||0,t=u+dn+fl||1;
  $('#breadth').innerHTML=
    '<div class="bd-row"><span class="bk">상승</span><span class="bv up">'+fmtI(u)+'</span><div class="bd-bar"><i style="width:'+(u/t*100)+'%;background:var(--up)"></i></div></div>'+
    '<div class="bd-row"><span class="bk">하락</span><span class="bv dn">'+fmtI(dn)+'</span><div class="bd-bar"><i style="width:'+(dn/t*100)+'%;background:var(--dn)"></i></div></div>'+
    '<div class="bd-row"><span class="bk">보합</span><span class="bv">'+fmtI(fl)+'</span><div class="bd-bar"><i style="width:'+(fl/t*100)+'%;background:var(--sub)"></i></div></div>';
}

function loadHeader(){
  return fetch('/api/index?code='+code,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    if(!d||!d.ok)return;info=d;$('#state').style.display='none';$('#body').style.display='block';
    document.title=(kname||d.name||'지수')+' — 지수 상세';$('#nm').textContent=kname||d.name||'지수';
    updateHero(d);});
}
function loadChart(){
  fetch('/api/index_chart?code='+code+'&period='+period,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    rows=d.rows||[];geo=null;draw();
    if(d.ok&&rows.length){var last=rows[rows.length-1];
      $('#mgrid').innerHTML=
        mg('시가',fmt(last.o))+mg('고가',fmt(last.h))+mg('저가',fmt(last.l))+mg('전일종가',fmt(d.prev_close))+
        mg('거래량',fmtI(last.v)+'천주')+mg('거래대금',fmtI(d.amount)+'백만')+
        mg('기간 최고',fmt(d.hi52))+mg('기간 최저',fmt(d.lo52));}
  });
}
function mg(k,v){return '<div class="mg"><div class="k">'+k+'</div><div class="v">'+v+'</div></div>';}
function loadNews(){
  fetch('/api/market_news',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    var rs=(d&&d.rows)||[];
    $('#news').innerHTML=rs.length?rs.slice(0,12).map(function(n){
      return '<div class="it'+(n.code?' clk':'')+'" data-code="'+(n.code||'')+'"><span class="t">'+esc(n.title)+'</span>'+
        '<span class="meta">'+esc(n.src||'')+' '+esc(n.when||'')+'</span></div>';}).join(''):'<div class="note" style="padding:6px 0;">뉴스 없음</div>';
    $('#news').querySelectorAll('.it.clk').forEach(function(it){it.onclick=function(){
      try{if(window.parent&&window.parent.miOpenStockTab&&it.dataset.code)window.parent.miOpenStockTab(it.dataset.code);}catch(e){}};});
  }).catch(function(){});
}

/* 캔들 + MA + 거래량 + 호버 (해외 종목 차트와 동일 방식) */
function draw(){var cv=$('#cv');if(!cv)return;var dpr=window.devicePixelRatio||1;
  var W=cv.clientWidth,H=380;cv.width=W*dpr;cv.height=H*dpr;var x=cv.getContext('2d');x.scale(dpr,dpr);
  x.clearRect(0,0,W,H);if(!rows.length)return;
  var data=rows.slice(-130),cs=getComputedStyle(document.documentElement);
  var up=cs.getPropertyValue('--up').trim(),dn=cs.getPropertyValue('--dn').trim(),sub=cs.getPropertyValue('--sub').trim(),ln=cs.getPropertyValue('--line').trim();
  var volH=56,gap=10,padT=12,padB=20,padR=64,priceH=H-padT-padB-volH-gap,plotW=W-padR;
  var hi=Math.max.apply(null,data.map(function(r){return r.h;})),lo=Math.min.apply(null,data.map(function(r){return r.l;}));
  if(hi<=lo)hi=lo+1;var vmx=Math.max.apply(null,data.map(function(r){return r.v;}))||1;
  function Y(p){return padT+(hi-p)/(hi-lo)*priceH;}
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.textAlign='left';x.lineWidth=.5;
  for(var g=0;g<=4;g++){var pv=lo+(hi-lo)*g/4,gy=Y(pv);x.beginPath();x.moveTo(0,gy);x.lineTo(plotW,gy);x.stroke();x.fillText(fmt(pv),plotW+6,gy+3);}
  var n=data.length,bw=plotW/n,cw=Math.max(1,bw*0.62),volTop=padT+priceH+gap;
  for(var i=0;i<n;i++){var r=data[i],cx=i*bw+bw/2,rise=r.c>=r.o,col=rise?up:dn;
    x.strokeStyle=col;x.fillStyle=col;x.lineWidth=1;x.beginPath();x.moveTo(cx,Y(r.h));x.lineTo(cx,Y(r.l));x.stroke();
    var y1=Y(Math.max(r.o,r.c)),y2=Y(Math.min(r.o,r.c));x.fillRect(cx-cw/2,y1,cw,Math.max(1,y2-y1));
    var vh=(r.v/vmx)*volH;x.globalAlpha=.5;x.fillRect(cx-cw/2,volTop+volH-vh,cw,vh);x.globalAlpha=1;}
  function sma(a,p){var o=[],s=0;for(var k=0;k<a.length;k++){s+=a[k];if(k>=p)s-=a[k-p];o.push(k>=p-1?s/p:null);}return o;}
  var ca=rows.map(function(r){return r.c;}),off=rows.length-n,md=[[5,'#e67e22'],[20,'#2e86de'],[60,'#8e44ad'],[120,'#16a085']];
  md.forEach(function(m){var ma=sma(ca,m[0]);x.strokeStyle=m[1];x.lineWidth=1.2;x.beginPath();var st=false;
    for(var i=0;i<n;i++){var v=ma[off+i];if(v==null)continue;var px=i*bw+bw/2,py=Y(v);if(!st){x.moveTo(px,py);st=true;}else x.lineTo(px,py);}x.stroke();});
  x.textAlign='left';x.font='10px -apple-system';var lx=4;md.forEach(function(m){x.fillStyle=m[1];x.fillText('MA'+m[0],lx,11);lx+=34;});
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(n/2),n-1].forEach(function(ix){var r=data[ix];if(!r||!r.d)return;
    x.fillText(String(r.d).replace(/(\d{4})(\d{2})(\d{2})/,'$1.$2.$3'),Math.min(plotW-30,Math.max(30,ix*bw+bw/2)),H-6);});
  geo={data:data,n:n,bw:bw,plotW:plotW,W:W};
  if(hoverIdx>=0&&hoverIdx<n){var hr=data[hoverIdx],hx=hoverIdx*bw+bw/2,hy=Y(hr.c);
    x.strokeStyle=sub;x.lineWidth=.7;x.setLineDash([3,3]);x.beginPath();x.moveTo(hx,padT);x.lineTo(hx,padT+priceH);x.stroke();
    x.beginPath();x.moveTo(0,hy);x.lineTo(plotW,hy);x.stroke();x.setLineDash([]);
    x.fillStyle=hr.c>=hr.o?up:dn;x.beginPath();x.arc(hx,hy,3,0,7);x.fill();}
}
function showTip(clientX){var cv=$('#cv'),tip=$('#cvTip');if(!cv||!tip||!geo||!geo.n)return;
  var rect=cv.getBoundingClientRect(),mx=clientX-rect.left,idx=Math.floor(mx/geo.bw);
  if(idx<0)idx=0;if(idx>=geo.n)idx=geo.n-1;if(mx<0||mx>geo.plotW){hideTip();return;}
  hoverIdx=idx;draw();var r=geo.data[idx];if(!r){hideTip();return;}
  var chg=r.c-r.o,cls=chg>=0?'up':'dn';
  tip.innerHTML='<div class="tip-d">'+String(r.d).replace(/(\d{4})(\d{2})(\d{2})/,'$1.$2.$3')+'</div>'+
    '<div class="tip-r"><span class="k">시가</span><span>'+fmt(r.o)+'</span></div>'+
    '<div class="tip-r"><span class="k">고가</span><span>'+fmt(r.h)+'</span></div>'+
    '<div class="tip-r"><span class="k">저가</span><span>'+fmt(r.l)+'</span></div>'+
    '<div class="tip-r"><span class="k">종가</span><span class="'+cls+'">'+fmt(r.c)+'</span></div>'+
    '<div class="tip-r"><span class="k">거래량</span><span>'+fmtI(r.v)+'</span></div>';
  tip.style.display='block';var tw=tip.offsetWidth,hx=idx*geo.bw+geo.bw/2,left=hx+12;
  if(left+tw>geo.W)left=hx-tw-12;if(left<0)left=4;tip.style.left=left+'px';tip.style.top='8px';}
function hideTip(){var tip=$('#cvTip');if(tip)tip.style.display='none';if(hoverIdx!==-1){hoverIdx=-1;draw();}}

$('#seg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
  period=b.dataset.p;this.querySelectorAll('button').forEach(function(z){z.classList.toggle('on',z===b);});loadChart();});
window.addEventListener('resize',draw);
(function(){var cv=$('#cv');if(cv){cv.addEventListener('mousemove',function(e){showTip(e.clientX);});cv.addEventListener('mouseleave',hideTip);}})();

loadHeader().then(function(){loadChart();loadNews();
  if(pollTid)clearInterval(pollTid);
  pollTid=setInterval(function(){if(!document.hidden)loadHeader();},3000);});
</script></body></html>
"""

_MACRO_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="macro"><head><meta charset="utf-8">
<title>한국 경제 지표</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f4f5f9;--card:rgba(255,255,255,.86);--ink:#1d1d1f;--sub:rgba(60,60,67,.6);
 --line:rgba(60,60,67,.12);--row:rgba(10,132,255,.06);--up:#FF3B30;--dn:#2E75B6;--accent:#0A84FF;}
html.dark{--bg:#0b0f1a;--card:rgba(28,30,38,.82);--ink:#eef3ff;--sub:#9aa6bd;--line:rgba(255,255,255,.1);
 --row:rgba(90,166,255,.1);--up:#FF453A;--dn:#64B5FF;--accent:#0A84FF;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;background:var(--bg);
 color:var(--ink);-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;padding:20px 22px 30px;}
.hd{display:flex;align-items:baseline;gap:10px;margin-bottom:4px;}
h2{margin:0;font-size:22px;font-weight:800;letter-spacing:-.02em;}
.lead{color:var(--sub);font-size:13px;margin:2px 0 16px;}
.state{color:var(--sub);font-size:14px;padding:40px 2px;}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:16px;}
.tile{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(28px);backdrop-filter:saturate(180%) blur(28px);
 border:.5px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 8px 26px rgba(0,0,0,.06);}
.tile .k{font-size:12px;color:var(--sub);}
.tile .v{font-size:23px;font-weight:800;margin-top:4px;letter-spacing:-.02em;}
.tile .s{font-size:11.5px;color:var(--sub);margin-top:3px;}
.up{color:var(--up);}.dn{color:var(--dn);}
.card{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(28px);backdrop-filter:saturate(180%) blur(28px);
 border:.5px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 10px 30px rgba(0,0,0,.06);margin-bottom:14px;}
h3{font-size:14.5px;font-weight:700;margin-bottom:4px;}
.sub{font-size:12px;color:var(--sub);margin-bottom:10px;}
.legend{display:flex;gap:16px;font-size:12px;color:var(--sub);margin-bottom:6px;}
.legend i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:5px;}
canvas{width:100%;height:280px;display:block;}
.cmt-overall{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;border-radius:13px;margin-bottom:12px;
 border:1px solid var(--line);}
.cmt-overall.good{background:rgba(255,59,48,.07);border-color:rgba(255,59,48,.25);}
.cmt-overall.bad{background:rgba(46,117,182,.08);border-color:rgba(46,117,182,.28);}
.cmt-overall.neutral{background:var(--row);}
.cmt-overall .badge{font-size:12px;font-weight:800;padding:4px 11px;border-radius:9px;white-space:nowrap;flex:none;}
.cmt-overall.good .badge{background:var(--up);color:#fff;} .cmt-overall.bad .badge{background:var(--dn);color:#fff;}
.cmt-overall.neutral .badge{background:var(--sub);color:#fff;}
.cmt-overall .ot{font-size:13.5px;font-weight:700;margin-bottom:3px;} .cmt-overall .od{font-size:12.5px;color:var(--sub);line-height:1.5;}
.cmt-pt{display:flex;gap:10px;padding:9px 2px;border-bottom:1px solid var(--line);font-size:13px;line-height:1.5;}
.cmt-pt:last-child{border-bottom:0;} .cmt-pt .pk{flex:none;width:86px;font-weight:700;color:var(--sub);}
.cmt-pt .dot{flex:none;width:7px;height:7px;border-radius:50%;margin-top:6px;}
.cmt-pt .dot.good{background:var(--up);} .cmt-pt .dot.bad{background:var(--dn);} .cmt-pt .dot.neutral{background:var(--sub);}
.cmt-dis{font-size:11px;color:var(--sub);margin-top:10px;}
.aibtn{float:right;font:600 12px/1 -apple-system;color:#fff;background:linear-gradient(135deg,var(--accent),#9b6bff);
  border:none;border-radius:100px;padding:7px 14px;cursor:pointer;transition:transform .15s,opacity .15s;}
.aibtn:hover{transform:translateY(-1px);} .aibtn:disabled{opacity:.55;cursor:default;transform:none;}
.aiout{margin-top:12px;font-size:13.5px;line-height:1.74;color:var(--ink);
  background:var(--row);border:1px solid var(--line);border-radius:12px;padding:13px 15px;max-height:360px;overflow:auto;}
.ai-cur{display:inline-block;width:7px;height:15px;margin-left:2px;background:var(--accent);border-radius:1px;vertical-align:-2px;animation:aiBlink 1s steps(2) infinite;}
@keyframes aiBlink{50%{opacity:0;}}
.ai-typing{display:inline-flex;gap:5px;} .ai-typing i{width:7px;height:7px;border-radius:50%;background:var(--accent);opacity:.4;animation:aiPulse 1.2s ease-in-out infinite;}
.ai-typing i:nth-child(2){animation-delay:.18s;} .ai-typing i:nth-child(3){animation-delay:.36s;}
@keyframes aiPulse{0%,100%{opacity:.3;transform:scale(.8);}50%{opacity:1;transform:scale(1);}}
@media (prefers-reduced-motion:reduce){.ai-cur,.ai-typing i{animation:none;}}
</style></head>
<body>
<div class="hd"><h2>🏦 경제 지표 — 한국 · 글로벌</h2></div>
<p class="lead">한국은행 ECOS(기준금리·국고채·물가·환율) + 글로벌 필수 지표(미국 증시·VIX·달러인덱스·금·WTI). (한국 지표는 발표 시차로 최신값이 한두 달 전일 수 있음)</p>
<div id="state" class="state">경제 지표를 불러오는 중…</div>
<div id="body" style="display:none;">
  <div class="tiles" id="tiles"></div>
  <div class="card" id="cmtCard" style="display:none;">
    <h3>📌 증시 영향 종합 해석</h3>
    <div id="cmtOverall"></div>
    <div id="cmtPoints"></div>
    <div class="cmt-dis">※ 거시지표 추세에 근거한 규칙 기반 해석이며, 투자조언이 아닙니다.</div>
  </div>
  <div class="card" id="globalCard" style="display:none;">
    <h3>🌐 글로벌 경제지표 <span class="sub" id="gAsof" style="font-weight:500;font-size:12px;"></span></h3>
    <div class="sub">미국 증시·위험심리(VIX)·달러·원자재 — 한국 증시 해석에 필수적인 글로벌 지표 (출처 네이버)</div>
    <div class="tiles" id="gtiles"></div>
    <div id="gPoints"></div>
    <div class="cmt-dis">※ 글로벌 지표 추세에 근거한 규칙 기반 해석이며, 투자조언이 아닙니다.</div>
  </div>
  <div class="card" id="aiCard">
    <h3>🤖 AI 해석 <span class="sub" style="font-weight:500;font-size:12px;">로컬 LLM이 지금 경제 상황을 쉽게 설명합니다</span>
      <button class="aibtn" id="aiBtn" type="button">AI 해석 보기</button></h3>
    <div id="aiOut" class="aiout" style="display:none;"></div>
  </div>
  <div class="card">
    <h3>📉 금리 추이</h3><div class="sub" id="rateAsof"></div>
    <div class="legend"><span><i style="background:#9b6bff"></i>기준금리</span><span><i style="background:#36c6ff"></i>국고채 3년</span><span><i style="background:#FF3B30"></i>국고채 10년</span><span><i style="background:#e0894e"></i>미국 10년물</span></div>
    <canvas id="rcv"></canvas>
  </div>
  <div class="card">
    <h3>🛒 소비자물가 상승률 (YoY)</h3><div class="sub" id="cpiAsof"></div>
    <canvas id="ccv"></canvas>
  </div>
</div>
<script>
var $=function(s){return document.querySelector(s);};
var D=null;
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt){document.documentElement.classList.toggle('dark',e.data.kmkt==='dark');drawAll();}});
function fmt(n,d){return n==null?'—':(Number(n)).toLocaleString('en-US',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function ym(t){return t&&t.length===6?t.slice(0,4)+'.'+t.slice(4,6):t;}
function tile(k,v,s,cls){return '<div class="tile"><div class="k">'+k+'</div><div class="v '+(cls||'')+'">'+v+'</div>'+(s?'<div class="s">'+s+'</div>':'')+'</div>';}
function render(){
  var k=D.kpi,a=D.asof;
  $('#tiles').innerHTML=
    tile('기준금리',fmt(k.base)+'%','한국은행 · '+ym(a.rate))+
    tile('국고채 3년',fmt(k.g3)+'%',ym(a.bond))+
    tile('국고채 10년',fmt(k.g10)+'%',ym(a.bond))+
    tile('장단기 스프레드',(k.spread>0?'+':'')+fmt(k.spread)+'%p','10년-3년',k.spread>0?'up':'dn')+
    tile('원/달러',fmt(k.usd,1)+'원','매매기준율 · '+ym(a.fx))+
    tile('소비자물가 YoY',(k.cpi_yoy!=null?(k.cpi_yoy>0?'+':'')+fmt(k.cpi_yoy)+'%':'—'),'총지수 '+fmt(k.cpi,1)+' · '+ym(a.cpi),k.cpi_yoy>=2?'up':'');
  $('#rateAsof').textContent='최근 '+(D.rate_series.months.length)+'개월 · 기준 '+ym(a.bond);
  $('#cpiAsof').textContent='전년동월 대비 · 기준 '+ym(a.cpi);
  renderCommentary();
  drawAll();
}
function renderCommentary(){
  var c=D.commentary;if(!c){return;}
  $('#cmtCard').style.display='';
  var o=c.overall;
  $('#cmtOverall').innerHTML='<div class="cmt-overall '+o.tone+'"><span class="badge">'+esc(o.title)+'</span>'+
    '<span><div class="od">'+esc(o.t)+'</div></span></div>';
  $('#cmtPoints').innerHTML=(c.points||[]).map(function(p){
    return '<div class="cmt-pt"><span class="dot '+p.tone+'"></span><span class="pk">'+esc(p.k)+'</span><span>'+esc(p.t)+'</span></div>';}).join('');
  var ab=document.getElementById('aiBtn');if(ab&&!ab._w){ab._w=1;ab.addEventListener('click',aiExplainMacro);}
}
/* ── AI 해석 (로컬 LLM · 작업4) — 거시지표를 초보 투자자용 자연어로 ── */
function aiExplainMacro(){
  if(!D)return;var k=D.kpi||{},a=D.asof||{};
  var lines=[
    '기준금리: '+fmt(k.base)+'% (한국은행 · '+ym(a.rate)+')',
    '국고채 3년: '+fmt(k.g3)+'% / 10년: '+fmt(k.g10)+'%',
    '장단기 스프레드(10년-3년): '+(k.spread>0?'+':'')+fmt(k.spread)+'%p',
    '원/달러 환율: '+fmt(k.usd,1)+'원 ('+ym(a.fx)+')',
    '소비자물가 YoY: '+(k.cpi_yoy!=null?(k.cpi_yoy>0?'+':'')+fmt(k.cpi_yoy)+'%':'—')+' (총지수 '+fmt(k.cpi,1)+' · '+ym(a.cpi)+')'
  ];
  if(D.commentary&&D.commentary.overall)lines.push('규칙기반 종합판단: '+D.commentary.overall.title+' — '+D.commentary.overall.t);
  var g=window._gmac;
  if(g&&g.ok&&g.rows&&g.rows.length){
    lines.push('[글로벌 지표] '+g.rows.map(function(r){return r.key+' '+r.price+(r.unit?r.unit:'')+'('+(r.dir==='up'?'+':'')+r.pct+'%)';}).join(', '));
  }
  var btn=document.getElementById('aiBtn');if(btn){btn.disabled=true;btn.textContent='해석 생성 중…';}
  streamLLM({prompt:lines.join('\n'),mode:'macro'},'aiOut',function(){if(btn){btn.disabled=false;btn.textContent='다시 해석';}});
}
function streamLLM(body,outId,onDone){
  body.max_tokens = window._llmMaxTokens || 1200;
  try{Object.assign(body,(window.kmktAiProv?window.kmktAiProv():{}));}catch(e){}   // 로컬/Gemini 선택 반영
  var out=document.getElementById(outId);if(!out)return;out.style.display='block';
  out.innerHTML='<span class="ai-typing"><i></i><i></i><i></i></span>';
  fetch('/api/llm_commentary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(async function(r){
      out.innerHTML='<div class="ai-think" id="'+outId+'_k" style="display:none;font-size:11.5px;opacity:.62;'
        +'border-left:2px solid var(--line,#d0d4dc);padding:4px 9px;margin:0 0 9px;max-height:150px;overflow:auto;'
        +'white-space:pre-wrap;line-height:1.5;">💭 <b style="opacity:.85;">추론</b><br><span id="'+outId+'_kt"></span></div>'
        +'<span id="'+outId+'_t"></span><span class="ai-cur"></span>';
      var tc=document.getElementById(outId+'_t'),kc=document.getElementById(outId+'_k'),kt=document.getElementById(outId+'_kt');
      var reader=r.body.getReader(),dec=new TextDecoder('utf-8');
      var buf='';function e2(s){return s.replace(/</g,'&lt;').replace(/\n/g,'<br>');}
      var ans='',md=window.kmktMd||function(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');};
      tc.className='kmkt-md';
      while(true){var rr=await reader.read();if(rr.done)break;
        buf+=dec.decode(rr.value,{stream:true});var ls=buf.split('\n');buf=ls.pop();
        for(var i=0;i<ls.length;i++){var ln=ls[i];if(ln.indexOf('data: ')===0){
          try{var dj=JSON.parse(ln.substring(6));if(dj.text){
            if(dj.kind==='reasoning'){kc.style.display='block';kt.insertAdjacentHTML('beforeend',e2(dj.text));}
            else{ans+=dj.text;tc.innerHTML=md(ans);}
            out.scrollTop=out.scrollHeight;}}catch(e){}}}
      }
      var cur=out.querySelector('.ai-cur');if(cur)cur.remove();if(onDone)onDone();
    }).catch(function(e){out.innerHTML='<span style="color:var(--dn,#2E75B6)">AI 연결 실패: '+e.message+'</span>';if(onDone)onDone();});
}
function lineChart(cv,months,seriesList){ // seriesList: [{vals,color}]
  if(!cv)return;var dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=280;
  cv.width=W*dpr;cv.height=H*dpr;var x=cv.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,W,H);
  var cs=getComputedStyle(document.documentElement),sub=cs.getPropertyValue('--sub').trim(),ln=cs.getPropertyValue('--line').trim();
  var padT=12,padB=24,padR=46,padL=8,plotW=W-padR-padL,plotH=H-padT-padB;
  var all=[];seriesList.forEach(function(s){s.vals.forEach(function(v){if(v!=null)all.push(v);});});
  if(!all.length)return;var hi=Math.max.apply(null,all),lo=Math.min.apply(null,all);if(hi<=lo)hi=lo+1;
  var pad=(hi-lo)*0.12;hi+=pad;lo-=pad;
  function X(i){return padL+i/(months.length-1||1)*plotW;}
  function Y(v){return padT+(hi-v)/(hi-lo)*plotH;}
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.lineWidth=.5;x.textAlign='left';
  for(var g=0;g<=4;g++){var pv=lo+(hi-lo)*g/4,gy=Y(pv);x.beginPath();x.moveTo(padL,gy);x.lineTo(padL+plotW,gy);x.stroke();x.fillText(fmt(pv,2),padL+plotW+5,gy+3);}
  seriesList.forEach(function(s){x.strokeStyle=s.color;x.lineWidth=2;x.beginPath();var started=false;
    s.vals.forEach(function(v,i){if(v==null)return;var px=X(i),py=Y(v);if(!started){x.moveTo(px,py);started=true;}else x.lineTo(px,py);});x.stroke();
    // 마지막 점
    for(var i=s.vals.length-1;i>=0;i--){if(s.vals[i]!=null){x.fillStyle=s.color;x.beginPath();x.arc(X(i),Y(s.vals[i]),3,0,7);x.fill();break;}}});
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(months.length/2),months.length-1].forEach(function(i){var t=months[i];if(!t)return;x.fillText(ym(t),Math.min(padL+plotW-20,Math.max(20,X(i))),H-7);});
}
function drawAll(){if(!D)return;
  lineChart($('#rcv'),D.rate_series.months,[{vals:D.rate_series.base,color:'#9b6bff'},{vals:D.rate_series.g3,color:'#36c6ff'},{vals:D.rate_series.g10,color:'#FF3B30'},{vals:(D.rate_series.us10||[]),color:'#e0894e'}]);
  lineChart($('#ccv'),D.cpi_series.months,[{vals:D.cpi_series.yoy,color:'#FF3B30'}]);
}
window.addEventListener('resize',drawAll);
/* ── 글로벌 경제지표 (작업4) — 한국 지표와 독립적으로 로드 ── */
function gtile(r){
  var cls=r.dir==='up'?'up':(r.dir==='down'?'dn':'');var sign=r.dir==='up'?'+':'';
  var pv=esc(r.price)+(r.unit?' <span style="font-size:13px;font-weight:600;color:var(--sub)">'+esc(r.unit)+'</span>':'');
  return '<div class="tile"><div class="k">'+esc(r.key)+'</div><div class="v '+cls+'">'+pv+'</div>'+
    '<div class="s '+cls+'">'+sign+esc(r.pct)+'%</div></div>';
}
function renderGlobal(g){
  if(!g||!g.ok||!g.rows||!g.rows.length)return;
  $('#state').style.display='none';$('#body').style.display='block';
  $('#globalCard').style.display='';
  $('#gAsof').textContent='· 기준 '+esc(g.asof);
  $('#gtiles').innerHTML=g.rows.map(gtile).join('');
  $('#gPoints').innerHTML=(g.points||[]).map(function(p){
    return '<div class="cmt-pt"><span class="dot '+p.tone+'"></span><span class="pk">'+esc(p.k)+'</span><span>'+esc(p.t)+'</span></div>';}).join('');
}
fetch('/api/global_macro',{cache:'no-store'}).then(function(r){return r.json();}).then(function(g){window._gmac=g;renderGlobal(g);}).catch(function(){});
fetch('/api/macro',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
  if(!d.ok){if(!(window._gmac&&window._gmac.ok))$('#state').textContent=d.msg||'경제 지표를 불러올 수 없습니다.';return;}
  D=d;$('#state').style.display='none';$('#body').style.display='block';render();
}).catch(function(){if(!(window._gmac&&window._gmac.ok))$('#state').textContent='네트워크 오류';});
</script></body></html>
"""

_ASK_WIDGET_HTML = """<div id="kmktAI" class="kmkt-ai" data-on="0">
  <button id="kmktAiFab" class="kmkt-ai-fab" type="button" aria-label="AI 질문하기" title="AI 질문하기">
    <span class="kmkt-ai-fab-ic">✨</span><span class="kmkt-ai-fab-lbl">AI 질문하기</span>
  </button>
  <div id="kmktAiWin" class="kmkt-ai-win" role="dialog" aria-label="AI 질문하기" aria-hidden="true">
    <div class="kmkt-ai-head">
      <div class="kmkt-ai-title">✨ AI 질문하기 <span class="kmkt-ai-sub">로컬 LLM</span></div>
      <button id="kmktAiX" class="kmkt-ai-x" type="button" aria-label="닫기">✕</button>
    </div>
    <div id="kmktAiBody" class="kmkt-ai-body">
      <div class="kmkt-ai-empty">이 화면에 대해 무엇이든 물어보세요.<br><span style="opacity:.7;">필요하면 AI가 스스로 뉴스 검색·기사 본문 읽기·계산을 수행합니다.</span></div>
    </div>
    <div class="kmkt-ai-foot">
      <div id="kmktAiCtxWrap" class="kmkt-ai-ctxwrap" hidden>
        <textarea id="kmktAiCtx" placeholder="참고할 뉴스·리포트·지표를 붙여넣거나, 분석 톤(예: '보수적 가치투자자 관점')을 지정하세요."></textarea>
      </div>
      <div id="kmktAiMenu" class="kmkt-ai-menu" role="menu" aria-label="모델 선택" hidden>
        <div class="kmkt-ai-menu-sec">모델</div>
        <button type="button" class="kmkt-ai-menu-it" data-prov="local" role="menuitemradio">
          <span class="mi-ic">💻</span><span class="mi-tx"><b>로컬 LLM</b><span>온디바이스 · 무료</span></span><span class="mi-ck">✓</span></button>
        <button type="button" class="kmkt-ai-menu-it" data-prov="gemini" data-model="gemini-3.5-flash" role="menuitemradio">
          <span class="mi-ic">✦</span><span class="mi-tx"><b>3.5 Flash</b><span>균형 · 기본</span></span><span class="mi-ck">✓</span></button>
        <button type="button" class="kmkt-ai-menu-it" data-prov="gemini" data-model="gemini-2.5-flash" role="menuitemradio">
          <span class="mi-ic">✦</span><span class="mi-tx"><b>2.5 Flash</b><span>웹 검색 ✓</span></span><span class="mi-ck">✓</span></button>
        <button type="button" class="kmkt-ai-menu-it" data-prov="gemini" data-model="gemini-2.5-flash-lite" role="menuitemradio">
          <span class="mi-ic">✦</span><span class="mi-tx"><b>2.5 Flash-Lite</b><span>검색 · 초경량</span></span><span class="mi-ck">✓</span></button>
        <button type="button" class="kmkt-ai-menu-it" data-prov="gemini" data-model="gemini-3.1-flash-lite" role="menuitemradio">
          <span class="mi-ic">✦</span><span class="mi-tx"><b>3.1 Flash-Lite</b><span>초고속</span></span><span class="mi-ck">✓</span></button>
        <div class="kmkt-ai-menu-div"></div>
        <label class="kmkt-ai-menu-it kmkt-ai-menu-tog" title="켜면 모델이 단계적으로 더 깊이 추론합니다(응답이 느려질 수 있음)">
          <span class="mi-ic">🧠</span><span class="mi-tx"><b>심층 추론</b><span>더 깊이 사고 · 느려질 수 있음</span></span>
          <input type="checkbox" id="kmktAiThink"><span class="kmkt-ai-think-tog"></span></label>
      </div>
      <div class="kmkt-ai-bar">
        <button id="kmktAiPlus" class="kmkt-ai-plus" type="button" aria-label="참고 데이터 / 지시사항 주입" title="참고 데이터 / 지시사항 주입">+</button>
        <textarea id="kmktAiIn" class="kmkt-ai-in" rows="1" placeholder="메시지를 입력하세요…"></textarea>
        <button id="kmktAiModel" class="kmkt-ai-modelchip" type="button" aria-haspopup="menu" aria-label="모델 선택"><span id="kmktAiModelLbl">로컬</span><span class="mc-ar">▾</span></button>
        <button id="kmktAiMic" class="kmkt-ai-mic" type="button" aria-label="음성 입력" title="음성 입력" hidden>🎤</button>
        <button id="kmktAiSend" class="kmkt-ai-send" type="button" aria-label="보내기">↑</button>
      </div>
    </div>
    <div class="kmkt-ai-rs kmkt-ai-rs-n" data-d="n"></div><div class="kmkt-ai-rs kmkt-ai-rs-s" data-d="s"></div>
    <div class="kmkt-ai-rs kmkt-ai-rs-e" data-d="e"></div><div class="kmkt-ai-rs kmkt-ai-rs-w" data-d="w"></div>
    <div class="kmkt-ai-rs kmkt-ai-rs-ne" data-d="ne"></div><div class="kmkt-ai-rs kmkt-ai-rs-nw" data-d="nw"></div>
    <div class="kmkt-ai-rs kmkt-ai-rs-se" data-d="se"></div><div class="kmkt-ai-rs kmkt-ai-rs-sw" data-d="sw"></div>
  </div>
</div>
<style>
.kmkt-ai{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Apple SD Gothic Neo",sans-serif;}
.kmkt-ai *{box-sizing:border-box;}
.kmkt-ai-fab{position:fixed;right:22px;bottom:22px;z-index:2147483000;display:flex;align-items:center;gap:0;
  height:56px;width:56px;padding:0;border:0;border-radius:100px;cursor:pointer;overflow:hidden;
  background:linear-gradient(135deg,#0a84ff,#0066e0);color:#fff;
  box-shadow:0 8px 24px rgba(10,132,255,.42),0 2px 6px rgba(0,0,0,.18);
  transition:width .42s cubic-bezier(.32,.72,0,1),transform .2s ease,box-shadow .2s ease;touch-action:none;}
.kmkt-ai-fab:hover{width:152px;transform:translateY(-1px);box-shadow:0 12px 30px rgba(10,132,255,.5),0 3px 8px rgba(0,0,0,.2);}
.kmkt-ai[data-drag="1"] .kmkt-ai-fab{transition:none;width:56px;}
.kmkt-ai-fab-ic{flex:0 0 56px;display:flex;align-items:center;justify-content:center;font-size:23px;line-height:1;}
.kmkt-ai-fab-lbl{white-space:nowrap;font-size:14px;font-weight:700;opacity:0;transition:opacity .2s ease .08s;padding-right:18px;}
.kmkt-ai-fab:hover .kmkt-ai-fab-lbl{opacity:1;}
.kmkt-ai[data-on="1"] .kmkt-ai-fab{transform:scale(.6);opacity:0;pointer-events:none;}
.kmkt-ai-win{position:fixed;right:22px;bottom:22px;z-index:2147483001;width:380px;max-width:calc(100vw - 28px);
  height:560px;max-height:calc(100vh - 40px);display:flex;flex-direction:column;overflow:hidden;
  border-radius:20px;border:1px solid rgba(0,0,0,.08);
  background:rgba(255,255,255,.86);backdrop-filter:blur(50px) saturate(180%);-webkit-backdrop-filter:blur(50px) saturate(180%);
  box-shadow:0 24px 64px rgba(0,0,0,.26),0 4px 14px rgba(0,0,0,.12);
  opacity:0;transform:translateY(16px) scale(.94);transform-origin:bottom right;pointer-events:none;
  transition:opacity .34s cubic-bezier(.32,.72,0,1),transform .34s cubic-bezier(.32,.72,0,1);}
.kmkt-ai[data-on="1"] .kmkt-ai-win{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;}
.kmkt-ai-head{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;
  border-bottom:1px solid rgba(0,0,0,.07);cursor:move;touch-action:none;user-select:none;}
.kmkt-ai-title{font-size:15px;font-weight:700;color:#1d1d1f;}
.kmkt-ai-sub{font-size:11px;font-weight:600;opacity:.5;margin-left:4px;}
.kmkt-ai-x{border:0;background:rgba(0,0,0,.06);color:#444;width:26px;height:26px;border-radius:100px;cursor:pointer;font-size:13px;line-height:1;transition:background .15s;}
.kmkt-ai-x:hover{background:rgba(0,0,0,.12);}
.kmkt-ai-body{flex:1;min-height:0;overflow-y:auto;padding:14px 14px 6px;display:flex;flex-direction:column;gap:12px;}
.kmkt-ai-empty{margin:auto 6px;text-align:center;font-size:13px;line-height:1.7;color:#8a8a8e;}
.kmkt-ai-msg{display:flex;flex-direction:column;max-width:90%;}
.kmkt-ai-msg.u{align-self:flex-end;align-items:flex-end;}
.kmkt-ai-msg.a{align-self:flex-start;align-items:flex-start;max-width:96%;}
.kmkt-ai-bub{font-size:13.5px;line-height:1.68;padding:9px 13px;border-radius:16px;word-break:break-word;white-space:normal;}
.kmkt-ai-msg.u .kmkt-ai-bub{background:linear-gradient(135deg,#0a84ff,#0073ea);color:#fff;border-bottom-right-radius:5px;}
.kmkt-ai-msg.a .kmkt-ai-bub{background:rgba(120,120,128,.12);color:#1d1d1f;border-bottom-left-radius:5px;}
.kmkt-ai-bub .mdh{font-weight:800;margin:9px 0 3px;font-size:13.5px;}
.kmkt-ai-bub .mdh:first-child{margin-top:0;}
.kmkt-ai-bub .mdul{margin:4px 0;padding-left:18px;} .kmkt-ai-bub .mdul li{margin:2px 0;}
.kmkt-ai-bub .mdsp{height:7px;} .kmkt-ai-bub b{font-weight:800;}
.kmkt-ai-bub code{background:rgba(120,120,128,.18);padding:1px 5px;border-radius:5px;font-size:12px;font-family:ui-monospace,monospace;}
.kmkt-ai-reason{font-size:11.5px;line-height:1.6;color:#7a7a7e;border-left:2px solid rgba(10,132,255,.4);
  padding:5px 10px;margin:0 0 7px;max-height:160px;overflow:auto;white-space:pre-wrap;border-radius:0 8px 8px 0;background:rgba(10,132,255,.05);}
.kmkt-ai-reason summary{cursor:pointer;font-weight:700;opacity:.85;outline:none;list-style:none;}
.kmkt-ai-reason[open] summary{margin-bottom:4px;}
.kmkt-ai-foot{padding:8px 12px 12px;border-top:1px solid rgba(0,0,0,.07);position:relative;}
.kmkt-ai-ctxwrap{margin-bottom:8px;}
.kmkt-ai-ctxwrap textarea{width:100%;height:62px;font:inherit;font-size:12px;line-height:1.5;padding:8px 10px;
  border:1px solid rgba(0,0,0,.12);border-radius:12px;background:rgba(255,255,255,.7);color:#1d1d1f;outline:none;resize:vertical;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-ctxwrap textarea{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.14);color:#f5f5f7;}
/* ── Gemini 스타일 입력 캡슐 ── */
.kmkt-ai-bar{display:flex;align-items:flex-end;gap:5px;background:rgba(118,118,128,.1);
  border:1px solid rgba(0,0,0,.06);border-radius:24px;padding:5px;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-bar{background:rgba(118,118,128,.22);border-color:rgba(255,255,255,.08);}
.kmkt-ai-plus{flex:0 0 32px;height:32px;width:32px;border:0;border-radius:50%;cursor:pointer;
  background:rgba(120,120,128,.16);color:#3a3a3e;font-size:21px;font-weight:300;line-height:1;
  display:flex;align-items:center;justify-content:center;transition:background .15s,transform .2s,color .15s;}
.kmkt-ai-plus:hover{background:rgba(120,120,128,.28);}
.kmkt-ai-plus.on{background:#0a84ff;color:#fff;transform:rotate(45deg);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-plus{background:rgba(255,255,255,.12);color:#e5e5ea;}
.kmkt-ai-in{flex:1;min-width:0;border:0;background:transparent;font:inherit;font-size:13.5px;line-height:1.5;color:#1d1d1f;
  outline:none;resize:none;max-height:120px;padding:7px 2px;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-in{color:#f5f5f7;}
.kmkt-ai-modelchip{flex:0 0 auto;display:inline-flex;align-items:center;gap:2px;height:32px;border:0;
  background:transparent;color:#5a5a5e;font:inherit;font-size:12.5px;font-weight:600;cursor:pointer;
  padding:0 5px;border-radius:9px;transition:background .15s,color .15s;max-width:118px;}
.kmkt-ai-modelchip:hover{background:rgba(120,120,128,.16);}
.kmkt-ai-modelchip .mc-ar{font-size:9px;opacity:.55;}
.kmkt-ai-modelchip #kmktAiModelLbl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-modelchip{color:#b0b0b8;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-modelchip:hover{background:rgba(255,255,255,.12);}
.kmkt-ai-mic{flex:0 0 32px;height:32px;width:32px;border:0;border-radius:50%;cursor:pointer;background:transparent;
  font-size:15px;line-height:1;display:flex;align-items:center;justify-content:center;transition:background .15s;}
.kmkt-ai-mic:hover{background:rgba(120,120,128,.16);}
.kmkt-ai-mic.rec{background:#FF3B30;color:#fff;animation:kmktAiMicPulse 1.1s ease-in-out infinite;}
@keyframes kmktAiMicPulse{50%{box-shadow:0 0 0 5px rgba(255,59,48,.25);}}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-mic:hover{background:rgba(255,255,255,.12);}
.kmkt-ai-send{flex:0 0 32px;height:32px;width:32px;border:0;border-radius:50%;cursor:pointer;
  background:#0a84ff;color:#fff;font-size:16px;font-weight:700;line-height:1;transition:background .15s,opacity .15s;
  display:flex;align-items:center;justify-content:center;}
.kmkt-ai-send:disabled{opacity:.35;cursor:default;}
.kmkt-ai-send:hover:not(:disabled){background:#0073ea;}
.kmkt-ai-send.stop{background:#1d1d1f;font-size:13px;}
.kmkt-ai-send.stop:hover{background:#000;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-send.stop{background:#f5f5f7;color:#1d1d1f;}
/* 심층 추론 토글(메뉴 내부) */
.kmkt-ai-think-tog{flex:0 0 30px;width:30px;height:18px;border-radius:100px;background:rgba(120,120,128,.3);position:relative;transition:background .2s;}
.kmkt-ai-think-tog::after{content:"";position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:#fff;transition:transform .2s;box-shadow:0 1px 2px rgba(0,0,0,.25);}
.kmkt-ai-menu-tog input:checked + .kmkt-ai-think-tog{background:#0a84ff;}
.kmkt-ai-menu-tog input:checked + .kmkt-ai-think-tog::after{transform:translateX(12px);}
/* ── 모델 선택 팝업 메뉴 (Gemini 스타일) ── */
.kmkt-ai-menu{position:absolute;left:12px;right:12px;bottom:58px;z-index:8;padding:6px;border-radius:16px;
  background:rgba(252,252,252,.94);backdrop-filter:blur(40px) saturate(180%);-webkit-backdrop-filter:blur(40px) saturate(180%);
  border:1px solid rgba(0,0,0,.08);box-shadow:0 16px 44px rgba(0,0,0,.22),0 3px 10px rgba(0,0,0,.1);
  max-height:330px;overflow:auto;animation:kmktAiMenuIn .18s cubic-bezier(.32,.72,0,1);}
@keyframes kmktAiMenuIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-menu{background:rgba(40,40,43,.95);border-color:rgba(255,255,255,.1);}
.kmkt-ai-menu-sec{font-size:11px;font-weight:700;color:#8a8a8e;padding:6px 10px 4px;}
.kmkt-ai-menu-it{display:flex;align-items:center;gap:10px;width:100%;border:0;background:transparent;
  text-align:left;padding:8px 10px;border-radius:10px;cursor:pointer;font:inherit;color:#1d1d1f;margin:0;}
.kmkt-ai-menu-it:hover{background:rgba(120,120,128,.14);}
.kmkt-ai-menu-it .mi-ic{flex:0 0 22px;font-size:17px;text-align:center;}
.kmkt-ai-menu-it .mi-tx{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.25;}
.kmkt-ai-menu-it .mi-tx b{font-size:13px;font-weight:700;}
.kmkt-ai-menu-it .mi-tx span{font-size:11px;color:#8a8a8e;}
.kmkt-ai-menu-it .mi-ck{flex:0 0 16px;color:#0a84ff;font-weight:800;opacity:0;}
.kmkt-ai-menu-it.sel .mi-ck{opacity:1;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-menu-it{color:#f5f5f7;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-menu-it:hover{background:rgba(255,255,255,.1);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-menu-it .mi-ck{color:#64b5ff;}
.kmkt-ai-menu-div{height:1px;background:rgba(0,0,0,.08);margin:5px 8px;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-menu-div{background:rgba(255,255,255,.1);}
.kmkt-ai-menu-tog{cursor:pointer;user-select:none;}
.kmkt-ai-menu-tog input{position:absolute;opacity:0;width:0;height:0;}
.kmkt-ai-stopped{font-size:11px;color:#8a8a8e;font-weight:600;}
/* 메시지 프로필 아바타·모델명(작업6) — 카카오톡식 */
.kmkt-ai-who{display:flex;align-items:center;gap:7px;margin:0 0 5px 1px;}
.kmkt-ai-av{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;
  font-size:15px;line-height:1;color:#fff;flex:0 0 28px;box-shadow:0 1px 4px rgba(0,0,0,.2);}
.kmkt-ai-av.local{background:linear-gradient(135deg,#0a84ff,#0066e0);}
.kmkt-ai-av.gemini{background:linear-gradient(135deg,#8b5cf6,#d946ef);font-size:19px;
  box-shadow:0 1px 5px rgba(139,92,246,.45),inset 0 0 0 1px rgba(217,70,239,.18);}
.kmkt-ai-nm{font-size:11.5px;font-weight:700;color:#8a8a8e;letter-spacing:-.1px;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-nm{color:#9a9aa0;}
/* 리사이즈 핸들(작업3) — 개별종목 리포트(.mi-rs)와 동일한 Mac 화살표 커서 */
.kmkt-ai-rs{position:absolute;z-index:6;}
.kmkt-ai-rs-n{top:0;left:12px;right:12px;height:7px;cursor:ns-resize;}
.kmkt-ai-rs-s{bottom:0;left:12px;right:12px;height:7px;cursor:ns-resize;}
.kmkt-ai-rs-e{right:0;top:12px;bottom:12px;width:7px;cursor:ew-resize;}
.kmkt-ai-rs-w{left:0;top:12px;bottom:12px;width:7px;cursor:ew-resize;}
.kmkt-ai-rs-ne{top:0;right:0;width:15px;height:15px;cursor:nesw-resize;}
.kmkt-ai-rs-sw{bottom:0;left:0;width:15px;height:15px;cursor:nesw-resize;}
.kmkt-ai-rs-se{bottom:0;right:0;width:15px;height:15px;cursor:nwse-resize;}
.kmkt-ai-rs-nw{top:0;left:0;width:15px;height:15px;cursor:nwse-resize;}
/* ── 다크 ── */
.kmkt-ai.kmkt-ai-dark .kmkt-ai-win{background:rgba(28,28,30,.9);border-color:rgba(255,255,255,.1);box-shadow:0 24px 64px rgba(0,0,0,.6);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-head{border-bottom-color:rgba(255,255,255,.09);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-title{color:#f5f5f7;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-x{background:rgba(255,255,255,.12);color:#ddd;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-x:hover{background:rgba(255,255,255,.2);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-empty{color:#9a9aa0;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-msg.a .kmkt-ai-bub{background:rgba(120,120,128,.26);color:#f5f5f7;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-reason{color:#a9b0bd;background:rgba(100,181,255,.08);border-left-color:rgba(100,181,255,.5);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-foot{border-top-color:rgba(255,255,255,.09);}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-ctx textarea{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.14);color:#f5f5f7;}
.kmkt-ai.kmkt-ai-dark .kmkt-ai-in{color:#f5f5f7;}
/* 타이핑 커서(작업1 — 모든 AI 기능 공통) */
.kmkt-ai-cur{display:inline-block;width:6px;height:13px;background:#0a84ff;margin-left:2px;vertical-align:-2px;border-radius:1px;
  animation:kmktAiBlink 1s step-start infinite;}
.ai-cur{animation:kmktAiBlink 1s step-start infinite;}
@keyframes kmktAiBlink{50%{opacity:0;}}
/* 공통 마크다운 렌더(작업1) — .kmkt-md 컨테이너에 적용(위젯 밖 AI 출력에도 재사용) */
.kmkt-md .mdh{font-weight:800;margin:9px 0 3px;} .kmkt-md .mdh:first-child{margin-top:0;}
.kmkt-md .mdul{margin:4px 0;padding-left:18px;} .kmkt-md .mdul li{margin:2px 0;}
.kmkt-md .mdsp{height:7px;} .kmkt-md b{font-weight:800;} .kmkt-md i{font-style:italic;}
.kmkt-md code{background:rgba(120,120,128,.18);padding:1px 5px;border-radius:5px;font-size:.92em;font-family:ui-monospace,monospace;}
/* 창 리사이즈 가장자리 커서(작업2) */
.kmkt-ai-win{will-change:left,top,width,height;}
@media (prefers-reduced-motion:reduce){.kmkt-ai-fab,.kmkt-ai-win,.kmkt-ai-cur,.ai-cur{transition:none !important;animation:none !important;}}
</style>
<script>(function(){
  var root=document.getElementById('kmktAI');if(!root||root._w)return;root._w=1;
  var fab=document.getElementById('kmktAiFab'),win=document.getElementById('kmktAiWin'),xb=document.getElementById('kmktAiX'),
      body=document.getElementById('kmktAiBody'),inp=document.getElementById('kmktAiIn'),send=document.getElementById('kmktAiSend'),
      ctx=document.getElementById('kmktAiCtx');
  // ── 테마 동기화 ──
  function isDark(){try{return document.documentElement.classList.contains('dark')||localStorage.getItem('kmkt-theme')==='dark';}catch(e){return false;}}
  function applyTheme(){root.classList.toggle('kmkt-ai-dark',isDark());}
  applyTheme();
  try{new MutationObserver(applyTheme).observe(document.documentElement,{attributes:true,attributeFilter:['class']});}catch(e){}
  window.addEventListener('storage',function(e){if(e.key==='kmkt-theme')applyTheme();});
  // ── FAB 위치 복원/드래그 ──
  try{var sp=JSON.parse(localStorage.getItem('kmkt-ai-fab-pos')||'null');
    if(sp&&sp.l!=null){placeFab(sp.l,sp.t);}}catch(e){}
  function placeFab(l,t){l=Math.max(8,Math.min(window.innerWidth-64,l));t=Math.max(8,Math.min(window.innerHeight-64,t));
    fab.style.left=l+'px';fab.style.top=t+'px';fab.style.right='auto';fab.style.bottom='auto';
    var nearR=(l>window.innerWidth/2),nearB=(t>window.innerHeight/2);
    win.style.right='auto';win.style.bottom='auto';
    var wl=nearR?Math.max(8,l+56-380):l, wt=nearB?Math.max(8,t-560-10):t+66;
    wl=Math.min(wl,window.innerWidth-12-Math.min(380,window.innerWidth-28));
    wt=Math.min(wt,window.innerHeight-12-Math.min(560,window.innerHeight-40));
    win.style.left=Math.max(8,wl)+'px';win.style.top=Math.max(8,wt)+'px';
    win.style.transformOrigin=(nearB?'bottom ':'top ')+(nearR?'right':'left');}
  var dragging=false,moved=false,sx=0,sy=0,ox=0,oy=0;
  fab.addEventListener('pointerdown',function(e){dragging=true;moved=false;
    var r=fab.getBoundingClientRect();ox=r.left;oy=r.top;sx=e.clientX;sy=e.clientY;
    root.setAttribute('data-drag','1');fab.setPointerCapture&&fab.setPointerCapture(e.pointerId);});
  fab.addEventListener('pointermove',function(e){if(!dragging)return;
    var dx=e.clientX-sx,dy=e.clientY-sy;if(Math.abs(dx)+Math.abs(dy)>5)moved=true;
    if(moved)placeFab(ox+dx,oy+dy);});
  fab.addEventListener('pointerup',function(e){if(!dragging)return;dragging=false;root.removeAttribute('data-drag');
    if(moved){try{var r=fab.getBoundingClientRect();localStorage.setItem('kmkt-ai-fab-pos',JSON.stringify({l:r.left,t:r.top}));}catch(e2){}}
    else{openWin();}});
  // ── 열기/닫기 (닫으면 대화 내용 휘발) ──
  function openWin(){if(!userPlaced)placeFab(fab.getBoundingClientRect().left,fab.getBoundingClientRect().top);
    root.setAttribute('data-on','1');try{updatePlaceholder();}catch(e){}setTimeout(function(){inp.focus();},120);}
  function closeWin(){root.setAttribute('data-on','0');try{stopGen();convo=[];}catch(e){}   // 닫으면 스트림 중지 + 메모리 휘발
    setTimeout(function(){body.innerHTML='<div class="kmkt-ai-empty">이 화면에 대해 무엇이든 물어보세요.<br><span style=\\"opacity:.7;\\">필요하면 AI가 스스로 뉴스 검색·기사 본문 읽기·계산을 수행합니다.</span></div>';
      if(ctx)ctx.value='';inp.value='';autosz();},340);}
  xb.addEventListener('click',closeWin);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&root.getAttribute('data-on')==='1')closeWin();});
  // ── 입력창 자동 높이 ──
  function autosz(){inp.style.height='auto';inp.style.height=Math.min(120,inp.scrollHeight)+'px';}
  inp.addEventListener('input',autosz);
  // ── 모델 선택 (Gemini 스타일 팝업 메뉴) + 직전 선택 기억 ──
  var menu=document.getElementById('kmktAiMenu'),modelChip=document.getElementById('kmktAiModel'),
      modelLbl=document.getElementById('kmktAiModelLbl'),plusBtn=document.getElementById('kmktAiPlus'),
      ctxWrap=document.getElementById('kmktAiCtxWrap'),micBtn=document.getElementById('kmktAiMic');
  var aiProv='local',aiGModel='gemini-3.5-flash';
  try{aiProv=localStorage.getItem('kmkt-ai-prov')||'local';}catch(e){}
  try{aiGModel=localStorage.getItem('kmkt-ai-gmodel')||'gemini-3.5-flash';}catch(e){}
  var GLABEL={'gemini-3.5-flash':'3.5 Flash','gemini-2.5-flash':'2.5 Flash','gemini-2.5-flash-lite':'2.5 Flash-Lite','gemini-3.1-flash-lite':'3.1 Flash-Lite'};
  // 더 이상 제공하지 않는(무료 티어 미지원) 모델이 저장돼 있으면 기본값으로 보정 — 오류 방지
  if(aiProv==='gemini'&&!GLABEL[aiGModel]){aiGModel='gemini-3.5-flash';try{localStorage.setItem('kmkt-ai-gmodel',aiGModel);}catch(e){}}
  var DEF_PH='메시지를 입력하세요…';
  function updatePlaceholder(){          // 로컬 선택인데 미로드면 입력창에 로드 안내
    if(aiProv!=='local'){inp.placeholder=DEF_PH;return;}
    inp.placeholder=DEF_PH;
    fetch('/api/llm/loaded',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
      if(aiProv==='local')inp.placeholder=(d&&d.loaded)?DEF_PH:'로컬 LLM 모델을 로드해 주세요.';
    }).catch(function(){if(aiProv==='local')inp.placeholder='로컬 LLM 모델을 로드해 주세요.';});}
  var subEl=root.querySelector('.kmkt-ai-sub');
  function applyProvUI(){
    if(modelLbl)modelLbl.textContent=(aiProv==='gemini')?(GLABEL[aiGModel]||'Gemini'):'로컬';
    if(menu)menu.querySelectorAll('.kmkt-ai-menu-it[data-prov]').forEach(function(it){
      var sel=(it.dataset.prov===aiProv)&&(it.dataset.prov!=='gemini'||it.dataset.model===aiGModel);
      it.classList.toggle('sel',sel);});
    if(subEl)subEl.textContent=(aiProv==='gemini')?('Gemini · '+(GLABEL[aiGModel]||'')):'로컬 LLM';
    updatePlaceholder();}
  function setModel(p,m){aiProv=p;if(p==='gemini'&&m)aiGModel=m;
    try{localStorage.setItem('kmkt-ai-prov',p);if(p==='gemini'&&m)localStorage.setItem('kmkt-ai-gmodel',m);}catch(e){}
    try{if(window.__kmktAiBtnSync)window.__kmktAiBtnSync();}catch(e){}   // 랜딩 AI 버튼 라벨 동기화
    applyProvUI();}
  // 메뉴 열기/닫기
  function openMenu(){if(menu){menu.hidden=false;modelChip&&modelChip.setAttribute('aria-expanded','1');}}
  function closeMenu(){if(menu){menu.hidden=true;modelChip&&modelChip.removeAttribute('aria-expanded');}}
  if(modelChip)modelChip.addEventListener('click',function(e){e.stopPropagation();menu&&(menu.hidden?openMenu():closeMenu());});
  if(menu)menu.querySelectorAll('.kmkt-ai-menu-it[data-prov]').forEach(function(it){
    it.addEventListener('click',function(){setModel(it.dataset.prov,it.dataset.model||'');closeMenu();});});
  // 메뉴 바깥 클릭 닫기(트랩#4: mousedown 으로 containment 평가)
  document.addEventListener('mousedown',function(e){
    if(menu&&!menu.hidden&&!menu.contains(e.target)&&e.target!==modelChip&&!(modelChip&&modelChip.contains(e.target)))closeMenu();});
  // + 버튼: 참고 데이터 / 지시사항 패널 토글
  if(plusBtn&&ctxWrap)plusBtn.addEventListener('click',function(){
    var show=ctxWrap.hidden;ctxWrap.hidden=!show;plusBtn.classList.toggle('on',show);if(show&&ctx)ctx.focus();});
  applyProvUI();
  // ── 음성 입력(Web Speech) — 지원될 때만 노출 ──
  (function(){var SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR||!micBtn)return;
    micBtn.hidden=false;var rec=null,recOn=false;
    micBtn.addEventListener('click',function(){
      if(recOn){try{rec&&rec.stop();}catch(e){}return;}
      try{rec=new SR();}catch(e){return;}rec.lang='ko-KR';rec.interimResults=true;rec.continuous=false;
      var base=inp.value;
      rec.onresult=function(ev){var t='';for(var i=ev.resultIndex;i<ev.results.length;i++)t+=ev.results[i][0].transcript;
        inp.value=(base?base+' ':'')+t;autosz();};
      rec.onstart=function(){recOn=true;micBtn.classList.add('rec');};
      rec.onend=function(){recOn=false;micBtn.classList.remove('rec');try{inp.focus();}catch(e){}};
      rec.onerror=function(){recOn=false;micBtn.classList.remove('rec');};
      try{rec.start();}catch(e){}});
  })();
  // ── 전송/스트리밍 ──
  function cfg(){try{var c=window.KMKT_ASK;return (typeof c==='function')?c():(c||{});}catch(e){return {};}}
  function e2(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\\n/g,'<br>');}
  function mdToHtml(t){
    t=String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    t=t.replace(/`([^`]+)`/g,'<code>$1</code>');
    t=t.replace(/\\*\\*([^*]+)\\*\\*/g,'<b>$1</b>');
    t=t.replace(/(^|[^*])\\*([^*\\n]+)\\*(?!\\*)/g,'$1<i>$2</i>');
    var lines=t.split('\\n'),out=[],ul=false;
    function cu(){if(ul){out.push('</ul>');ul=false;}}
    for(var i=0;i<lines.length;i++){var L=lines[i];
      var hm=L.match(/^\\s*#{1,4}\\s+(.*)$/);
      var bm=L.match(/^\\s*(?:[-*•]|\\d+\\.)\\s+(.*)$/);
      if(hm){cu();out.push('<div class="mdh">'+hm[1]+'</div>');}
      else if(bm){if(!ul){out.push('<ul class="mdul">');ul=true;}out.push('<li>'+bm[1]+'</li>');}
      else if(L.trim()===''){cu();out.push('<div class="mdsp"></div>');}
      else{cu();out.push('<div>'+L+'</div>');}}
    cu();return out.join('');}
  try{window.kmktMd=mdToHtml;}catch(e){}   // 다른 AI 출력에서 재사용(작업1)
  // AI 팝오버가 고른 provider/모델/시스템프롬프트를 모든 AI 기능(요약·해석·코멘터리)이 공유(같은 localStorage 키).
  try{window.kmktAiProv=function(){function g(k,d){try{return localStorage.getItem(k)||d;}catch(e){return d;}}
    return {provider:g('kmkt-ai-prov','local'),gemini_model:g('kmkt-ai-gmodel','gemini-3.5-flash'),gsys:g('kmkt-ai-gsys','')};};}catch(e){}
  var busy=false,convo=[],ctrl=null;   // 멀티턴 메모리(Gemini) + 스트리밍 중단 컨트롤러
  function setSending(on){busy=on;
    if(on){send.classList.add('stop');send.innerHTML='■';send.setAttribute('aria-label','중지');send.disabled=false;}
    else{send.classList.remove('stop');send.innerHTML='↑';send.setAttribute('aria-label','보내기');}}
  function stopGen(){if(ctrl){try{ctrl.abort();}catch(e){}}}
  function ask(){
    var q=(inp.value||'').trim();if(!q||busy)return;
    var em=body.querySelector('.kmkt-ai-empty');if(em)em.remove();
    var c=cfg(),ctxVal=(ctx?ctx.value:'').trim();
    var thinkEl=document.getElementById('kmktAiThink'),think=!!(thinkEl&&thinkEl.checked);
    var um=document.createElement('div');um.className='kmkt-ai-msg u';
    um.innerHTML='<div class="kmkt-ai-bub">'+e2(q)+'</div>';body.appendChild(um);
    inp.value='';autosz();
    var am=document.createElement('div');am.className='kmkt-ai-msg a';
    var w0=(aiProv==='gemini');
    am.innerHTML='<div class="kmkt-ai-who"><span class="kmkt-ai-av '+(w0?'gemini':'local')+'">'+(w0?'✦':'✨')+'</span>'
      +'<span class="kmkt-ai-nm">'+(w0?'Gemini':'로컬')+'</span></div>'
      +'<details class="kmkt-ai-reason" style="display:none"><summary>💭 생각 과정</summary><span class="kmkt-ai-rt"></span></details>'
      +'<div class="kmkt-ai-bub">생각 중 · · ·</div>';
    body.appendChild(am);body.scrollTop=body.scrollHeight;
    var rb=am.querySelector('.kmkt-ai-reason'),rt=am.querySelector('.kmkt-ai-rt'),tb=am.querySelector('.kmkt-ai-bub'),
        av=am.querySelector('.kmkt-ai-av'),nm=am.querySelector('.kmkt-ai-nm'),started=false,ansBuf='';
    function setWho(m){if(!m)return;var g=(m.provider==='gemini');
      av.className='kmkt-ai-av '+(g?'gemini':'local');av.textContent=g?'✦':'✨';nm.textContent=m.name||(g?'Gemini':'로컬');}
    tb.classList.add('kmkt-md');
    var CUR='<span class="kmkt-ai-cur"></span>';
    function finish(){setSending(false);ctrl=null;
      if(started&&ansBuf){convo.push({role:'user',text:q});convo.push({role:'model',text:ansBuf});if(convo.length>24)convo=convo.slice(-24);}}
    ctrl=(typeof AbortController!=='undefined')?new AbortController():null;setSending(true);
    fetch('/api/llm_ask',{method:'POST',headers:{'Content-Type':'application/json'},signal:ctrl?ctrl.signal:undefined,
      body:JSON.stringify({scope:c.scope||'',id:c.id||'',excd:c.excd||'',question:q,user_context:ctxVal,think:think,provider:aiProv,gemini_model:aiGModel,history:(aiProv==='gemini')?convo.slice(-12):[]})})
    .then(async function(r){
      var rd=r.body.getReader(),dec=new TextDecoder('utf-8'),buf='';
      while(true){var rr=await rd.read();if(rr.done)break;
        buf+=dec.decode(rr.value,{stream:true});var ls=buf.split('\\n');buf=ls.pop();
        for(var i=0;i<ls.length;i++){var ln=ls[i];if(ln.indexOf('data: ')===0){
          try{var dj=JSON.parse(ln.substring(6));
            if(dj.meta){setWho(dj.meta);}
            else if(dj.text){
            if(dj.kind==='reasoning'){rb.style.display='';rb.setAttribute('open','');rt.insertAdjacentHTML('beforeend',e2(dj.text));}
            else{if(!started){started=true;tb.innerHTML='';}ansBuf+=dj.text;tb.innerHTML=mdToHtml(ansBuf)+CUR;}
            body.scrollTop=body.scrollHeight;}}catch(e){}}}
      }
      if(started)tb.innerHTML=mdToHtml(ansBuf);   // 완료 시 커서 제거
      if(!started&&tb.textContent.indexOf('생각 중')===0)tb.textContent='(응답이 없습니다)';
      finish();
    }).catch(function(e){
      if(e&&e.name==='AbortError'){   // 사용자가 중지 — 받은 만큼 보존
        if(started)tb.innerHTML=mdToHtml(ansBuf)+' <span class="kmkt-ai-stopped">⏹ 중지됨</span>';
        else tb.innerHTML='<span class="kmkt-ai-stopped">⏹ 중지됨</span>';
        finish();return;}
      tb.innerHTML='<span style="color:#FF3B30">AI 연결 실패: '+e2(e.message)+'</span>';finish();});
  }
  send.addEventListener('click',function(){if(busy)stopGen();else ask();});
  inp.addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask();}});
  // ── 창 이동(헤더 드래그) + 리사이즈 핸들(작업2·3) — 개별종목 리포트와 동일한 Mac 핸들 방식 ──
  var head=win.querySelector('.kmkt-ai-head');
  var userPlaced=false,MINW=300,MINH=360,rz=null,mvs=null;
  function wr(){return win.getBoundingClientRect();}
  function startResize(e){var hd=e.target.closest('.kmkt-ai-rs');if(!hd)return;var r=wr();
    rz={dir:hd.dataset.d,sx:e.clientX,sy:e.clientY,l:r.left,t:r.top,w:r.width,h:r.height};
    userPlaced=true;win.style.right='auto';win.style.bottom='auto';win.style.maxWidth='none';win.style.maxHeight='none';
    document.body.style.userSelect='none';e.preventDefault();
    document.addEventListener('mousemove',onResize);document.addEventListener('mouseup',endResize);}
  function onResize(e){if(!rz)return;var dx=e.clientX-rz.sx,dy=e.clientY-rz.sy,l=rz.l,t=rz.t,w=rz.w,h=rz.h,d=rz.dir;
    if(d.indexOf('e')>=0)w=rz.w+dx;if(d.indexOf('s')>=0)h=rz.h+dy;
    if(d.indexOf('w')>=0)w=rz.w-dx;if(d.indexOf('n')>=0)h=rz.h-dy;
    w=Math.max(MINW,Math.min(window.innerWidth-16,w));h=Math.max(MINH,Math.min(window.innerHeight-16,h));
    if(d.indexOf('w')>=0)l=rz.l+(rz.w-w);if(d.indexOf('n')>=0)t=rz.t+(rz.h-h);
    win.style.width=w+'px';win.style.height=h+'px';win.style.left=Math.max(8,l)+'px';win.style.top=Math.max(8,t)+'px';}
  function endResize(){rz=null;document.body.style.userSelect='';
    document.removeEventListener('mousemove',onResize);document.removeEventListener('mouseup',endResize);}
  win.addEventListener('mousedown',startResize);
  function startMove(e){if((e.target.closest&&(e.target.closest('.kmkt-ai-x')||e.target.closest('.kmkt-ai-rs'))))return;
    var r=wr();mvs={sx:e.clientX,sy:e.clientY,l:r.left,t:r.top};userPlaced=true;
    win.style.right='auto';win.style.bottom='auto';document.body.style.userSelect='none';e.preventDefault();
    document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',endMove);}
  function onMove(e){if(!mvs)return;var nl=mvs.l+(e.clientX-mvs.sx),nt=mvs.t+(e.clientY-mvs.sy);
    nl=Math.max(60-wr().width,Math.min(window.innerWidth-60,nl));nt=Math.max(8,Math.min(window.innerHeight-44,nt));
    win.style.left=nl+'px';win.style.top=nt+'px';}
  function endMove(){mvs=null;document.body.style.userSelect='';
    document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',endMove);}
  head.addEventListener('mousedown',startMove);
  window.addEventListener('resize',function(){if(root.getAttribute('data-on')==='1'&&!userPlaced)placeFab(fab.getBoundingClientRect().left,fab.getBoundingClientRect().top);});
})();</script>"""

_LANDING_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" type="image/png" href="/logo.png">
<link rel="apple-touch-icon" href="/logo.png">
<title>K-Market Dashboard 2 · M4 Pro</title>
<script>(function(){try{var k='kmkt-theme',s=localStorage.getItem(k);
if(!s)s=(window.matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches)?'dark':'light';
if(s==='dark')document.documentElement.classList.add('dark');
document.addEventListener('DOMContentLoaded',function(){var t=document.getElementById('themeToggle');if(!t)return;
function sync(){t.setAttribute('aria-checked',document.documentElement.classList.contains('dark')?'true':'false');}sync();
t.addEventListener('click',function(){var r=document.documentElement,d=!r.classList.contains('dark');
r.classList.add('theme-anim');r.classList.toggle('dark',d);localStorage.setItem(k,d?'dark':'light');sync();
try{document.querySelectorAll('iframe.frame').forEach(function(f){try{f.contentWindow.postMessage({kmkt:d?'dark':'light'},'*');}catch(_){}});}catch(_){}
clearTimeout(window.__tmT);window.__tmT=setTimeout(function(){r.classList.remove('theme-anim');},760);});});}catch(e){}})();</script>
<style>
:root{
 --sys-blue:#007AFF; --btn-blue:#0088ff; --sys-red:#FF3B30; --sys-blue-dn:#2E75B6; --sys-indigo:#5856D6;
 --label:#000000d9; --label-2:rgba(60,60,67,.62); --label-3:rgba(60,60,67,.34);
 --fill-1:rgba(120,120,128,.16); --fill-3:rgba(118,118,128,.07); --line:rgba(60,60,67,.13);
 --surface-solid:#fff;
 --mat-medium:rgba(255,255,255,.36); --mat-thick:rgba(246,246,246,.74); --mat-ultrathick:rgba(246,246,246,.92);
 --blur:saturate(180%) blur(50px);
 --glass-edge:inset 0 1px 0 rgba(255,255,255,.5), inset 1px 0 0 rgba(255,255,255,.3), inset 0 -1px 4px rgba(0,0,0,.08), inset -1px 0 4px rgba(0,0,0,.06);
 --shadow-pop:var(--glass-edge), 0 8px 24px rgba(20,30,70,.14);
 --shadow-card:var(--glass-edge), 0 17px 45px rgba(0,0,0,.18), 0 0 1px rgba(0,0,0,.2);
 --r-md:11px; --r-lg:16px; --r-glass:26px; --r-pill:100px; --ease:cubic-bezier(.32,.72,0,1);
 --chip:rgba(255,255,255,.4); --chip-blur:saturate(160%) blur(12px);
 --glass-soft:inset 0 1px 0 rgba(255,255,255,.55), inset 0 -1px 2px rgba(0,0,0,.05);
 /* macOS 26 (Tahoe) 글라스 캡슐 — Figma UI Kit 레시피.
    오프화이트 프로스트 필 + 매우 부드러운 드롭섀도 + 미세 글라스 베벨 */
 --cap-fill:rgba(247,247,247,.72); --cap-fill-solid:rgba(247,247,247,.95);
 --cap-shadow:0 8px 40px rgba(0,0,0,.12);
 --cap-edge:inset 0 .5px 0 rgba(255,255,255,.85), inset 0 -.5px 0 rgba(0,0,0,.05), inset 0 0 0 .5px rgba(0,0,0,.04);
 --cap-blur:saturate(180%) blur(30px);
 --wp-base:#eef1f8;
 --wp-light:radial-gradient(42% 50% at 18% 22%, rgba(150,190,255,.72), transparent 62%),
      radial-gradient(40% 46% at 82% 18%, rgba(255,175,215,.64), transparent 60%),
      radial-gradient(46% 52% at 72% 88%, rgba(160,235,210,.62), transparent 62%),
      radial-gradient(44% 50% at 28% 92%, rgba(205,180,255,.58), transparent 62%),
      linear-gradient(120deg,#eef3ff,#fbeef7,#eefaf6,#f3eeff);
 /* 다크모드: 채도 없는 무채색(검정~짙은회색)만 사용 → wphue(hue-rotate)에도 색이 안 변함 */
 --wp-dark:radial-gradient(42% 50% at 18% 22%, rgba(72,72,78,.55), transparent 62%),
      radial-gradient(40% 46% at 82% 18%, rgba(52,52,56,.5), transparent 60%),
      radial-gradient(46% 52% at 72% 88%, rgba(60,60,64,.46), transparent 62%),
      radial-gradient(44% 50% at 28% 92%, rgba(40,40,44,.46), transparent 62%),
      linear-gradient(120deg,#0b0b0d,#151517,#0e0e10,#090909);
}
:root.dark{
 --sys-blue:#0A84FF; --btn-blue:#0A84FF; --sys-red:#FF453A; --sys-blue-dn:#64B5FF; --sys-indigo:#5E5CE6;
 --label:rgba(255,255,255,.92); --label-2:rgba(235,235,245,.6); --label-3:rgba(235,235,245,.3);
 --fill-1:rgba(120,120,128,.36); --fill-3:rgba(120,120,128,.22); --line:rgba(255,255,255,.12);
 --surface-solid:#2c2c2e;
 --mat-medium:rgba(28,28,32,.42); --mat-thick:rgba(42,42,46,.7); --mat-ultrathick:rgba(46,46,50,.86);
 --glass-edge:inset 0 1px 0 rgba(255,255,255,.12), inset 0 -1px 4px rgba(0,0,0,.3);
 --chip:rgba(255,255,255,.085);
 --glass-soft:inset 0 1px 0 rgba(255,255,255,.14), inset 0 -1px 2px rgba(0,0,0,.22);
 --shadow-pop:var(--glass-edge), 0 8px 24px rgba(0,0,0,.4);
 --shadow-card:var(--glass-edge), 0 17px 45px rgba(0,0,0,.5), 0 0 1px rgba(0,0,0,.4);
 /* macOS 26 글라스 캡슐(다크) — 무채색 다크 그레이 프로스트 */
 --cap-fill:rgba(58,58,62,.55); --cap-fill-solid:rgba(54,54,58,.92);
 --cap-shadow:0 8px 40px rgba(0,0,0,.5);
 --cap-edge:inset 0 .5px 0 rgba(255,255,255,.12), inset 0 -.5px 0 rgba(0,0,0,.35), inset 0 0 0 .5px rgba(255,255,255,.05);
 --wp-base:#0a0a0c;
}
*{box-sizing:border-box;}
html,body{margin:0;height:100%;}
body{display:flex;flex-direction:column;color:var(--label);font-size:13px;background:var(--wp-base);
 transition:background-color .6s ease;
 font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue','Apple SD Gothic Neo',sans-serif;}
/* 흐르는 파스텔 그라데이션 웨이브 — 라이트/다크 두 레이어 opacity 크로스페이드.
   ① wpdrift: 유기적 다중 키프레임으로 부드럽게 출렁이는 웨이브 모션
   ② wphue:   0→360° 연속 색상 회전으로 여러 파스텔 색채가 끊임없이 바뀜
   (라이트/다크 두 레이어 모두 애니메이션 → 다크 모드에도 동일한 웨이브) */
body::before,body::after{content:"";position:fixed;inset:-34%;z-index:-1;pointer-events:none;
 animation:wpdrift 42s ease-in-out infinite, wphue 72s linear infinite;
 will-change:transform,filter,opacity;}
body::before{background:var(--wp-light);}
body::after{background:var(--wp-dark);opacity:0;transition:opacity .6s ease;animation-delay:-8s,-18s;}
:root.dark body::after{opacity:1;}
/* 발열↓: 앱 비활성/숨김이면 전면 그라데이션(hue-rotate) 애니메이션 정지 → GPU 컴포지팅 중단.
   접근성: prefers-reduced-motion 이면 항상 정지. */
body.kmkt-bg-off::before,body.kmkt-bg-off::after{animation-play-state:paused!important;}
@media (prefers-reduced-motion:reduce){body::before,body::after{animation:none!important;will-change:auto!important;}}
/* 테마 전환하는 순간에만 색 트랜지션을 입혀 부드럽게(평소 hover/모션엔 영향 없음) */
:root.theme-anim *{transition:background-color .6s ease, color .6s ease, border-color .6s ease,
 box-shadow .6s ease, fill .6s ease, transform .45s var(--ease) !important;}
@keyframes wpdrift{
 0%{transform:translate3d(-3%,-2%,0) rotate(-4deg) scale(1.14);}
 20%{transform:translate3d(2%,-3.5%,0) rotate(2.5deg) scale(1.20);}
 40%{transform:translate3d(4%,2%,0) rotate(5deg) scale(1.16);}
 60%{transform:translate3d(0%,4%,0) rotate(-1.5deg) scale(1.22);}
 80%{transform:translate3d(-4%,1.5%,0) rotate(-5deg) scale(1.17);}
 100%{transform:translate3d(-3%,-2%,0) rotate(-4deg) scale(1.14);}}
@keyframes wphue{from{filter:hue-rotate(0deg);}to{filter:hue-rotate(360deg);}}
.topbar{display:flex;align-items:center;gap:13px;padding:11px 18px;z-index:20;
 background:var(--mat-medium);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 border-bottom:.5px solid var(--line);box-shadow:var(--glass-edge),0 1px 0 rgba(60,60,80,.07);}
/* 네이티브 앱(pywebview): 불투명 흰 바를 없애고 컨트롤이 월페이퍼 위에 떠 있게(Gemini 식).
   · 상단바 배경/블러/보더 제거(투명) → "흰 바" 사라짐
   · padding-top 으로 콘텐츠를 신호등(닫기·최소화·확대) 높이까지 내려 잘림 방지
   · padding-left 로 좌측 신호등 자리를 비워 브랜드를 그 오른쪽에 배치
   · 빈 영역은 .pywebview-drag-region 으로 창 드래그 핸들 */
.is-app .topbar{padding:20px 18px 11px 78px;background:transparent;
 -webkit-backdrop-filter:none;backdrop-filter:none;border-bottom:0;box-shadow:none;
 -webkit-user-select:none;user-select:none;}
.topbar.pywebview-drag-region :where(.brand,.brand *){-webkit-user-select:none;}
/* 앱 모드: 컨트롤은 cap 글라스 토큰을 그대로 사용 → 월페이퍼가 비쳐 '흰 바'로 안 보임 */
.topbar .brand{font-size:15px;font-weight:600;white-space:nowrap;display:flex;align-items:center;gap:7px;color:var(--label);}
.topbar .brand .brand-logo{width:24px;height:24px;border-radius:6px;flex:none;object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2);}
.topbar .brand small{font-weight:400;color:var(--label-2);font-size:12px;margin-left:2px;}
/* macOS HIG 세그먼트 컨트롤 (피드백2) — 음각 트랙 + 떠 있는 썸. 토큰: cap-fill/blur, r-pill, ease */
.mkt-seg{display:inline-flex;gap:2px;margin-left:10px;padding:2px;vertical-align:middle;
 background:var(--cap-fill);-webkit-backdrop-filter:var(--cap-blur);backdrop-filter:var(--cap-blur);
 border-radius:var(--r-pill);box-shadow:inset 0 .5px 2px rgba(0,0,0,.14),inset 0 0 0 .5px rgba(0,0,0,.04);}
.mkt-seg button{font:inherit;font-size:12px;font-weight:600;padding:4px 14px;border:0;border-radius:var(--r-pill);
 background:transparent;color:var(--label-2);cursor:pointer;line-height:1.5;white-space:nowrap;
 transition:background .22s var(--ease),color .22s var(--ease),box-shadow .22s var(--ease);}
.mkt-seg button.on{background:#fff;color:var(--label);
 box-shadow:0 1px 3px rgba(0,0,0,.18),0 .5px 1px rgba(0,0,0,.08),inset 0 0 0 .5px rgba(0,0,0,.03);}
html.dark .mkt-seg{box-shadow:inset 0 .5px 2px rgba(0,0,0,.5),inset 0 0 0 .5px rgba(255,255,255,.05);}
html.dark .mkt-seg button.on{background:#5a5a5f;color:#fff;box-shadow:0 1px 3px rgba(0,0,0,.4);}
.m4-badge{font-size:11px;font-weight:600;color:var(--sys-indigo);background:rgba(88,86,214,.14);
 -webkit-backdrop-filter:var(--chip-blur);backdrop-filter:var(--chip-blur);
 border:.5px solid rgba(88,86,214,.3);padding:3px 9px;border-radius:var(--r-pill);box-shadow:var(--glass-soft);}
.searchwrap{position:relative;flex:1;min-width:120px;display:flex;align-items:center;}
#q{width:100%;height:34px;padding:0 18px;font-size:13px;color:var(--label);background:var(--cap-fill);font-family:inherit;
 -webkit-backdrop-filter:var(--cap-blur);backdrop-filter:var(--cap-blur);
 border:0;border-radius:var(--r-pill);box-shadow:var(--cap-edge),var(--cap-shadow);
 outline:none;transition:box-shadow .22s var(--ease),background .22s var(--ease);}
#q:focus{background:var(--cap-fill-solid);box-shadow:var(--cap-edge),0 0 0 3.5px rgba(10,132,255,.35);}
#q::placeholder{color:var(--label-3);}
.sg{position:absolute;top:44px;left:0;right:0;border-radius:var(--r-lg);overflow:hidden;z-index:30;max-height:420px;overflow-y:auto;
 background:var(--mat-ultrathick);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 box-shadow:var(--shadow-card);transform-origin:top center;
 opacity:0;transform:translateY(-6px) scale(.99);pointer-events:none;
 transition:opacity .18s var(--ease),transform .18s var(--ease);}
.sg.show{opacity:1;transform:none;pointer-events:auto;}
.sg-item{padding:9px 14px;cursor:pointer;border-bottom:.5px solid var(--line);display:flex;align-items:center;gap:10px;}
.sg-item:last-child{border-bottom:0;}
.sg-item:hover,.sg-item.active{background:rgba(10,132,255,.12);}
.sg-badge{font-size:11px;font-weight:600;border-radius:6px;padding:2px 7px;flex:none;}
.sg-badge.etf{background:rgba(10,132,255,.16);color:var(--sys-blue);}
.sg-badge.stk{background:rgba(255,69,58,.16);color:var(--sys-red);}
.sg-code{font-weight:600;color:var(--sys-blue);font-size:13px;font-variant-numeric:tabular-nums;min-width:60px;}
.sg-name{font-weight:600;color:var(--label);font-size:14px;}
.sg-extra{margin-left:auto;color:var(--label-3);font-size:12px;white-space:nowrap;}
.btn{background:linear-gradient(rgba(255,255,255,.2),rgba(255,255,255,0) 55%),var(--btn-blue);
 color:#fff;border:0;border-radius:var(--r-pill);padding:0 18px;height:34px;
 font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap;
 box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 6px 22px rgba(0,136,255,.3);
 font-family:inherit;transition:transform .12s var(--ease),filter .2s;}
.btn:hover{filter:brightness(1.07);}
.btn:active{transform:scale(.96);}
/* 리퀴드 글라스 캡슐 버튼 (작업7) — m4-badge 와 동일 재질: 틴트 + 블러 + 헤어라인 + 소프트 섀도 */
.btn-glass{background:rgba(88,86,214,.14);color:var(--sys-indigo);
 -webkit-backdrop-filter:var(--chip-blur);backdrop-filter:var(--chip-blur);
 border:.5px solid rgba(88,86,214,.3);box-shadow:var(--glass-soft);font-weight:600;}
.btn-glass:hover{filter:none;background:rgba(88,86,214,.22);}
.btn-glass.g-red{background:rgba(255,59,48,.13);color:#FF3B30;border-color:rgba(255,59,48,.3);}
.btn-glass.g-red:hover{background:rgba(255,59,48,.2);}
html.dark .btn-glass{color:#b9b6ff;}
html.dark .btn-glass.g-red{color:#FF6B61;}
/* 컴팩트 캡슐 — 스크리너·실시간 버튼 크기 축소(작업6) */
.btn.btn-sm{height:28px;padding:0 12px;font-size:12px;}
.btn.btn-sm:not(.searchwrap){box-shadow:var(--glass-soft);}
/* 상단 AI(로컬 LLM 제어) 버튼 + 팝오버 (작업6) */
.btn-glass.g-ai{background:rgba(155,107,255,.16);color:#7a4ddb;border-color:rgba(155,107,255,.34);}
.btn-glass.g-ai:hover{background:rgba(155,107,255,.24);}
html.dark .btn-glass.g-ai{color:#c8b4ff;}
.ai-wrap{position:relative;display:inline-flex;}
.ai-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#c7c7cc;
 margin-right:6px;vertical-align:middle;transition:background .25s,box-shadow .25s;}
.ai-dot.on{background:#34C759;box-shadow:0 0 0 3px rgba(52,199,89,.18);}
html.dark .ai-dot{background:#5a5a5e;} html.dark .ai-dot.on{background:#30D158;box-shadow:0 0 0 3px rgba(48,209,88,.22);}
.ai-pop{position:absolute;top:calc(100% + 9px);right:0;width:266px;z-index:60;
 background:var(--mat-thick,rgba(255,255,255,.86));-webkit-backdrop-filter:saturate(180%) blur(50px);backdrop-filter:saturate(180%) blur(50px);
 border:.5px solid var(--line,rgba(60,60,67,.18));border-radius:16px;padding:14px;
 box-shadow:0 18px 48px rgba(20,30,60,.22),inset 0 1px 0 rgba(255,255,255,.4);
 opacity:0;transform:translateY(-6px) scale(.98);transform-origin:top right;pointer-events:none;
 transition:opacity .2s var(--ease,cubic-bezier(.32,.72,0,1)),transform .2s var(--ease,cubic-bezier(.32,.72,0,1));}
.ai-pop.show{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;}
html.dark .ai-pop{background:rgba(28,30,40,.9);border-color:rgba(255,255,255,.12);box-shadow:0 18px 48px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.06);}
.aip-h{display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:700;color:var(--label,#1d1d1f);margin-bottom:11px;}
.aip-state{font-size:11px;font-weight:600;color:var(--label-2,#8a8a8e);}
.aip-state.on{color:#16a06a;}
/* 로컬/Gemini 세그먼트 토글 + Gemini 모델 select + 시스템 프롬프트 textarea (macOS UI Kit 토큰 기준) */
.aip-seg{display:flex;background:rgba(118,118,128,.12);border-radius:9px;padding:2px;margin-bottom:11px;}
.aip-seg button{flex:1;border:0;background:transparent;font:600 12px/1 inherit;color:var(--label-2,#6a6a6e);
 padding:7px 0;border-radius:7px;cursor:pointer;transition:all .18s var(--ease,cubic-bezier(.32,.72,0,1));}
.aip-seg button.on{background:var(--card,#fff);color:#007AFF;box-shadow:0 1px 3px rgba(0,0,0,.14);}
html.dark .aip-seg{background:rgba(120,120,128,.26);}
html.dark .aip-seg button{color:#9a9aa0;}
html.dark .aip-seg button.on{background:#3a3a3e;color:#64b5ff;}
.aip-select{width:100%;padding:9px 12px;border-radius:10px;background:var(--card,#fff);color:var(--label,#1d1d1f);
 border:1px solid var(--line,rgba(60,60,67,.18));font:600 13px/1.2 inherit;outline:none;
 box-shadow:0 1px 2px rgba(0,0,0,.04);appearance:auto;cursor:pointer;}
.aip-lbl{font-size:12px;font-weight:700;color:var(--label,#1d1d1f);margin-bottom:6px;}
.aip-ta{width:100%;min-height:64px;resize:vertical;padding:9px 11px;border-radius:10px;background:var(--bg,#f4f5f9);
 color:var(--label,#1d1d1f);border:1px solid var(--line,rgba(60,60,67,.18));font:inherit;font-size:12.5px;line-height:1.5;
 outline:none;box-shadow:0 1px 2px rgba(0,0,0,.03);transition:border-color .18s,box-shadow .18s;}
.aip-ta:focus{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,.2);}
html.dark .aip-select,html.dark .aip-ta{background:rgba(120,120,128,.16);}
.aip-msg{font-size:12.5px;line-height:1.6;color:var(--label-2,#6b6b70);padding:6px 2px 4px;}
.aip-toggle{display:flex;align-items:center;gap:9px;width:100%;border:0;cursor:pointer;
 border-radius:11px;padding:9px 12px;font:600 12.5px/1 inherit;color:#fff;margin-bottom:12px;
 background:rgba(120,130,150,.5);transition:background .2s var(--ease,ease);}
.aip-toggle.on{background:linear-gradient(135deg,#16a06a,#0a8f7a);}
.aip-toggle:disabled{opacity:.6;cursor:default;}
.aip-tg-knob{width:16px;height:16px;border-radius:50%;background:#fff;flex:none;box-shadow:0 1px 3px rgba(0,0,0,.3);
 transition:transform .2s var(--ease,ease);} .aip-toggle.on .aip-tg-knob{transform:translateX(2px);}
.aip-info{border-top:.5px solid var(--line,rgba(60,60,67,.14));padding-top:10px;}
.aip-row{display:flex;justify-content:space-between;gap:10px;font-size:12px;padding:4px 0;}
.aip-k{color:var(--label-2,#8a8a8e);flex:none;} .aip-v{color:var(--label,#1d1d1f);font-weight:600;text-align:right;
 word-break:break-all;font-variant-numeric:tabular-nums;}
@media (prefers-reduced-motion:reduce){.ai-pop{transition:none;}.aip-tg-knob,.aip-toggle{transition:none;}}
/* 다크모드 토글 (검색 버튼 ↔ KOSPI 사이) */
.theme-toggle{border:0;background:none;padding:0;margin:0;cursor:pointer;flex:none;display:flex;align-items:center;}
.tt-track{position:relative;width:48px;height:26px;border-radius:999px;display:flex;align-items:center;
 background:var(--cap-fill);-webkit-backdrop-filter:var(--cap-blur);backdrop-filter:var(--cap-blur);
 border:0;box-shadow:var(--cap-edge),var(--cap-shadow);
 transition:background .28s var(--ease);}
.tt-sun,.tt-moon{position:absolute;line-height:1;color:var(--label-2);pointer-events:none;}
.tt-sun{left:6px;font-size:12px;} .tt-moon{right:6px;font-size:11px;}
.tt-knob{position:absolute;left:3px;top:3px;width:20px;height:20px;border-radius:50%;background:#fff;
 box-shadow:0 1px 3px rgba(0,0,0,.3);transition:transform .28s var(--ease),background .28s;}
:root.dark .tt-track{background:rgba(120,120,128,.5);}
:root.dark .tt-knob{transform:translateX(22px);background:#f2f2f4;}
/* KOSPI 티커 — 글래스 캡슐 */
.kospi-ticker{display:flex;align-items:center;gap:9px;white-space:nowrap;color:var(--label);
 background:var(--cap-fill);-webkit-backdrop-filter:var(--cap-blur);backdrop-filter:var(--cap-blur);
 border-radius:var(--r-pill);padding:6px 14px;box-shadow:var(--cap-edge),var(--cap-shadow);}
.kospi-ticker .kt-dot{width:7px;height:7px;border-radius:50%;background:var(--sys-red);flex:none;
 box-shadow:0 0 0 0 rgba(255,59,48,.6);animation:ktpulse 1.8s ease-in-out infinite;}
@keyframes ktpulse{0%,100%{box-shadow:0 0 0 0 rgba(255,59,48,.5);}60%{box-shadow:0 0 0 6px rgba(255,59,48,0);}}
.kospi-ticker .kt-name{font-size:11px;font-weight:600;letter-spacing:.03em;color:var(--label-2);}
.kospi-ticker .kt-val{font-size:16px;font-weight:600;font-variant-numeric:tabular-nums;
 color:var(--label)!important;display:inline-flex;align-items:center;overflow:visible;}
.kospi-ticker .kt-chg{font-size:12px;font-weight:500;font-variant-numeric:tabular-nums;display:inline-flex;align-items:center;}
.kospi-ticker.up .kt-chg{color:var(--sys-red);}
.kospi-ticker.down .kt-chg{color:var(--sys-blue-dn);}
.kospi-ticker.flat .kt-chg{color:var(--label-2);}
.kospi-ticker .kt-val .rt-ch,.kospi-ticker .kt-chg .rt-ch{display:inline-block;vertical-align:top;font-variant-numeric:tabular-nums;}
.kospi-ticker .kt-val .rt-col,.kospi-ticker .kt-chg .rt-col{display:block;will-change:transform;}
@media (max-width:980px){.kospi-ticker{display:none;}}
@media (prefers-reduced-motion:reduce){.kospi-ticker .kt-dot{animation:none!important;}}
.tabstrip{display:flex;align-items:center;gap:6px;padding:0 14px;overflow-x:auto;
 max-height:0;opacity:0;transition:max-height .28s var(--ease),opacity .28s var(--ease),padding .28s var(--ease);}
.tabstrip.show{max-height:50px;opacity:1;padding:9px 14px;}
.tab{display:flex;align-items:center;gap:7px;border-radius:10px;padding:6px 12px;max-width:240px;cursor:pointer;
 color:var(--label-2);font-size:13px;font-weight:500;white-space:nowrap;user-select:none;
 background:var(--mat-thick);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 box-shadow:var(--glass-edge),0 1px 3px rgba(20,30,70,.10);
 transition:background .2s var(--ease),color .2s,transform .12s;animation:tabPop .24s var(--ease);}
@keyframes tabPop{from{opacity:0;transform:translateY(8px) scale(.96);}to{opacity:1;transform:none;}}
.tab:hover{color:var(--label);}
.tab.active{background:var(--surface-solid);color:var(--label);box-shadow:0 1px 4px rgba(20,30,70,.18);}
.tab-ic{font-size:13px;flex:none;}
.tab-label{overflow:hidden;text-overflow:ellipsis;max-width:165px;}
.tab-close{border-radius:50%;width:18px;height:18px;line-height:17px;text-align:center;color:var(--label-3);font-size:15px;flex:none;transition:background .12s,color .12s;}
.tab-close:hover{background:rgba(125,125,130,.25);color:var(--label);}
.tab.dragging{opacity:.55;}
.stage{flex:1;position:relative;overflow:hidden;perspective:1400px;}
.framewrap{position:absolute;inset:0;opacity:0;transform:translateZ(0) translateY(12px) scale(.992);
 transition:opacity .34s var(--ease),transform .34s var(--ease);pointer-events:none;z-index:1;
 will-change:transform;backface-visibility:hidden;}
.framewrap.show{opacity:1;transform:translateZ(0);pointer-events:auto;z-index:2;}
.framewrap.exit{opacity:0;transform:translateZ(0) translateY(-8px) scale(.995);
 pointer-events:none;z-index:1;transition:opacity .32s var(--ease),transform .32s var(--ease);}
.framewrap .frame{width:100%;height:100%;border:0;background:#fff;}
.framewrap .overlay{position:absolute;inset:0;background:var(--mat-ultrathick);
 -webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;z-index:5;
 opacity:0;pointer-events:none;transition:opacity .32s var(--ease);}
.framewrap .overlay.show{opacity:1;pointer-events:auto;}
.spinner{width:40px;height:40px;border:4px solid rgba(125,125,130,.25);border-top-color:var(--sys-blue);
 border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.framewrap .overlay p{color:var(--label-2);font-weight:500;font-size:14px;}
.empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 text-align:center;padding:24px;z-index:3;
 transition:opacity .38s var(--ease),transform .38s var(--ease);}
.empty.hide{opacity:0;transform:translateY(12px) scale(.99);pointer-events:none;}
.hero3d{transform-style:preserve-3d;transition:transform .25s var(--ease);will-change:transform;backface-visibility:hidden;
 background:var(--mat-thick);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 border-radius:var(--r-glass);padding:38px 48px;box-shadow:var(--shadow-card);animation:heroRise .6s var(--ease) both;}
@keyframes heroRise{from{opacity:0;transform:translateY(16px) scale(.985);}to{opacity:1;transform:none;}}
.empty .big{font-size:48px;margin-bottom:14px;transform:translateZ(40px);}
.empty h2{margin:0 0 8px;color:var(--label);font-size:22px;font-weight:600;letter-spacing:-.01em;transform:translateZ(26px);}
.empty p{margin:3px 0;color:var(--label-2);font-size:13px;line-height:18px;transform:translateZ(14px);}
.empty .tagline{margin-top:10px;font-weight:600;color:var(--sys-indigo);}
.empty .ex{margin-top:20px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;transform:translateZ(10px);}
.empty .ex span{background:var(--surface-solid);border:.5px solid var(--line);border-radius:var(--r-pill);padding:7px 14px;
 font-size:13px;color:var(--label);cursor:pointer;font-weight:500;box-shadow:0 1px 2px rgba(20,30,60,.06);
 transition:transform .18s var(--ease),border-color .18s,color .18s,box-shadow .18s;}
.empty .ex span:hover{border-color:var(--sys-blue);color:var(--sys-blue);transform:translateY(-2px);box-shadow:0 4px 12px rgba(10,132,255,.2);}
.empty .ex span:active{transform:translateY(0);}
/* 업종 지수 바로가기 카드 (작업6) — 히어로 아래 글라스 캡슐 */
.sector-card{display:flex;align-items:center;gap:14px;margin-top:18px;cursor:pointer;
 max-width:560px;width:100%;padding:15px 20px;border-radius:var(--r-lg);text-align:left;
 background:var(--mat-thick);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 box-shadow:var(--shadow-pop);user-select:none;
 transition:transform .2s var(--ease),box-shadow .2s var(--ease);animation:heroRise .6s var(--ease) .12s both;}
.sector-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-card);}
.sector-card:active{transform:translateY(0) scale(.99);}
.sector-card .sc-ic{font-size:24px;flex:none;}
.sector-card .sc-body{display:flex;flex-direction:column;gap:2px;min-width:0;}
.sector-card .sc-title{font-size:15px;font-weight:600;color:var(--label);}
.sector-card .sc-sub{font-size:12px;color:var(--label-2);line-height:16px;}
.sector-card .sc-arrow{margin-left:auto;font-size:22px;color:var(--label-3);flex:none;}
@media (prefers-reduced-motion:reduce){
 body::before,body::after,.tab,.hero3d{animation:none!important;}
 .framewrap{transition:none!important;} .hero3d{transform:none!important;}
 .framewrap,.hero3d,.tab,.btn,.empty .ex span,body::before,body::after{will-change:auto!important;}
}
/* Spotlight Overlay */
#spotlight{position:fixed;inset:0;z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding-top:12vh;
 background:rgba(0,0,0,0.2);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
 opacity:0;pointer-events:none;transition:opacity .24s var(--ease);}
#spotlight.show{opacity:1;pointer-events:auto;}
.spotlight-box{width:100%;max-width:680px;background:var(--cap-fill);border-radius:var(--r-glass);
 box-shadow:var(--shadow-card), 0 0 0 1px rgba(255,255,255,0.1) inset;
 transform:scale(0.96) translateY(-10px);transition:transform .24s var(--ease),opacity .24s var(--ease);opacity:0;
 display:flex;flex-direction:column;overflow:hidden;}
#spotlight.show .spotlight-box{transform:none;opacity:1;}
.spotlight-input{width:100%;height:64px;padding:0 24px;font-size:22px;background:transparent;border:0;color:var(--label);outline:none;}
.spotlight-input::placeholder{color:var(--label-3);}
.spotlight-results{max-height:400px;overflow-y:auto;border-top:1px solid var(--line);}
.spotlight-item{padding:12px 24px;display:flex;align-items:center;gap:12px;cursor:pointer;border-bottom:1px solid var(--line);}
.spotlight-item.active{background:var(--sys-blue);color:#fff;}
.spotlight-item.active *{color:#fff !important;}
/* ════ 앱 첫 구동 스플래시 (로고 컨셉 · macOS 26 모션) ════
   logo.png 의 캔들+웨이브 모티프를 애니메이션 SVG로 재현. 다크 네이비 고정
   (창 background_color #0b0f20 와 이어져 흰 플래시 없음). 세션당 1회 표시. */
#splash{position:fixed;inset:0;z-index:99999;display:flex;flex-direction:column;
 align-items:center;justify-content:center;gap:24px;
 background:radial-gradient(125% 92% at 50% 16%, #1a2450 0%, #0b0f20 56%, #06080f 100%);
 transition:opacity .7s ease, transform .7s var(--ease), filter .7s ease;
 will-change:opacity,transform,filter;-webkit-font-smoothing:antialiased;}
#splash.hide{opacity:0;transform:scale(1.045);filter:blur(9px);pointer-events:none;}
.sp-icon{width:132px;height:132px;position:relative;
 animation:spRise .9s var(--ease) both, spBob 4.4s ease-in-out 1s infinite;}
@keyframes spRise{from{opacity:0;transform:translateY(16px) scale(.84);filter:blur(7px);}
 to{opacity:1;transform:none;filter:none;}}
@keyframes spBob{0%,100%{transform:translateY(0);}50%{transform:translateY(-7px);}}
.sp-icon svg{width:100%;height:100%;display:block;overflow:visible;}
.sp-icon::before{content:"";position:absolute;inset:-24%;border-radius:34px;z-index:-1;
 background:radial-gradient(circle at 50% 48%, rgba(123,110,255,.5), rgba(54,198,255,.18) 46%, transparent 70%);
 filter:blur(22px);animation:spGlow 3.4s ease-in-out infinite;}
@keyframes spGlow{0%,100%{opacity:.5;transform:scale(.95);}50%{opacity:1;transform:scale(1.07);}}
.sp-candle{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);
 animation:spGrow .85s cubic-bezier(.16,1,.3,1) both;}
@keyframes spGrow{to{transform:scaleY(1);}}
.sp-wick{stroke-dasharray:100;stroke-dashoffset:100;animation:spWick .65s ease both;}
@keyframes spWick{to{stroke-dashoffset:0;}}
.sp-wave{stroke-dasharray:100;stroke-dashoffset:100;transform-box:fill-box;
 animation:spDraw 1.5s var(--ease) both, spDrift 7s ease-in-out 1.5s infinite;}
@keyframes spDraw{to{stroke-dashoffset:0;}}
@keyframes spDrift{0%,100%{transform:translateX(0);}50%{transform:translateX(-5px);}}
.sp-word{font-size:26px;font-weight:700;letter-spacing:-.01em;color:#eaf0ff;
 font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Apple SD Gothic Neo',sans-serif;
 animation:spFade .7s ease .5s both;}
.sp-sub{margin-top:-12px;font-size:12px;font-weight:600;letter-spacing:.05em;color:#a796ff;
 animation:spFade .7s ease .72s both;}
@keyframes spFade{from{opacity:0;transform:translateY(9px);}to{opacity:1;transform:none;}}
.sp-bar{width:184px;height:3px;border-radius:3px;overflow:hidden;background:rgba(255,255,255,.08);
 animation:spFade .6s ease .95s both;}
.sp-bar span{display:block;height:100%;width:38%;border-radius:3px;
 background:linear-gradient(90deg,#36c6ff,#9b6bff,#ff7a59);animation:spSlide 1.25s ease-in-out infinite;}
@keyframes spSlide{0%{transform:translateX(-130%);}100%{transform:translateX(330%);}}
@media (prefers-reduced-motion:reduce){
 .sp-icon,.sp-icon::before,.sp-candle,.sp-wick,.sp-wave,.sp-word,.sp-sub,.sp-bar,.sp-bar span{animation:none!important;}
 .sp-candle{transform:none!important;}.sp-wick,.sp-wave{stroke-dashoffset:0!important;}}
</style></head>
<body>
<div id="splash" role="status" aria-label="K-Market Dashboard 로딩 중">
  <div class="sp-icon">
    <img src="/logo.png" alt="앱 아이콘" style="width:100%;height:100%;display:block;border-radius:28px;">
  </div>
  <div class="sp-word">K-Market Dashboard</div>
  <div class="sp-sub">🚀 M4 PRO · PRO QUANT</div>
  <div class="sp-bar"><span></span></div>
</div>
<script>(function(){
  var sp=document.getElementById('splash');if(!sp)return;
  var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion:reduce)').matches;
  // 세션당 1회: 앱을 처음 구동했을 때만. 같은 세션 내 새로고침/탐색엔 생략.
  try{if(sessionStorage.getItem('kmkt_splash')){if(sp.parentNode)sp.parentNode.removeChild(sp);return;}}catch(e){}
  var MIN=RM?260:1850,t0=Date.now(),gone=false;
  function hide(){if(gone)return;gone=true;sp.classList.add('hide');
    try{sessionStorage.setItem('kmkt_splash','1');}catch(e){}
    setTimeout(function(){if(sp.parentNode)sp.parentNode.removeChild(sp);},780);}
  function ready(){setTimeout(hide,Math.max(0,MIN-(Date.now()-t0)));}
  if(document.readyState==='complete')ready();else window.addEventListener('load',ready);
  setTimeout(hide,6000);  // 안전망: 무슨 일이 있어도 강제 종료
})();</script>
<script>(function(){function app(){document.documentElement.classList.add('is-app');}
 if(window.pywebview)app();window.addEventListener('pywebviewready',app);
 /* 폴백: pywebview 객체 주입이 한 박자 늦어도(상단바가 프로스트 흰 바로 보이는 원인)
    반드시 is-app 이 붙도록 잠시 폴링 — 네이티브 창에선 상단바가 투명으로 유지된다. */
 var n=0,t=setInterval(function(){if(window.pywebview){app();clearInterval(t);}else if(++n>60)clearInterval(t);},50);})();</script>
<div class="topbar pywebview-drag-region">
  <div class="brand"><img class="brand-logo" src="/logo.png" alt="" onerror="this.replaceWith(document.createTextNode('📈'))">K-Market Dashboard 2<span class="mkt-seg" id="mktSeg" role="tablist" aria-label="시장 전환"><button type="button" data-m="kr" class="on" role="tab" aria-selected="true">🇰🇷 국내</button><button type="button" data-m="ov" role="tab" aria-selected="false">🌎 해외</button></span></div>
  <form class="searchwrap" id="form" autocomplete="off">
    <input id="q" type="text" placeholder="주식·ETF 종목명 또는 6자리 코드 입력 (예: 삼성전자, 005930, KODEX 200)">
    <div class="sg" id="sg"></div>
  </form>
  <button class="btn" type="button" id="searchBtn">검색</button>
  <button class="btn btn-glass btn-sm" type="button" id="screenerBtn">🔍 스크리너</button>
  <button class="btn btn-glass g-red btn-sm" type="button" id="realtimeBtn">📡 실시간</button>
  <span class="ai-wrap">
    <button class="btn btn-glass g-ai btn-sm" type="button" id="aiCtrlBtn" aria-haspopup="dialog" aria-expanded="false" title="AI 모델 제어 (로컬/Gemini)"><span class="ai-dot" id="aiDot" title="모델 미로드"></span>✨ <span id="aiLbl">AI</span></button>
    <div class="ai-pop" id="aiPop" role="dialog" aria-label="로컬 AI 모델"></div>
  </span>
  <button class="theme-toggle" id="themeToggle" type="button" role="switch" aria-checked="false" aria-label="다크 모드 전환" title="라이트/다크 모드">
    <span class="tt-track"><span class="tt-sun">☀</span><span class="tt-moon">☾</span><span class="tt-knob"></span></span>
  </button>
  <div class="kospi-ticker flat" id="kospiTicker" title="KOSPI 실시간 지수 · 한국투자증권 KIS">
    <span class="kt-dot"></span><span class="kt-name">KOSPI</span>
    <span class="kt-val" id="ktVal">—</span><span class="kt-chg" id="ktChg"></span>
  </div>
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
    <div class="sector-card" id="sectorCard" role="button" tabindex="0" title="업종 지수 열기">
      <span class="sc-ic">🏷️</span>
      <span class="sc-body">
        <span class="sc-title">업종 지수</span>
        <span class="sc-sub">코스피·코스닥 업종별 현재지수 — 등락률 순 정렬 · 업종 클릭 시 구성종목 시세</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sector-card" id="marketCard" role="button" tabindex="0" title="시장 현황 열기" style="animation-delay:.2s">
      <span class="sc-ic">📈</span>
      <span class="sc-body">
        <span class="sc-title">시장 현황</span>
        <span class="sc-sub">시가총액 상위 · 상한가/하한가 포착 · 종합 시황과 공시 헤드라인</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sector-card" id="worldCard" role="button" tabindex="0" title="세계 시장 열기" style="animation-delay:.3s">
      <span class="sc-ic">🌍</span>
      <span class="sc-body">
        <span class="sc-title">세계 시장</span>
        <span class="sc-sub">미국·유럽·아시아 주요 지수와 환율(원화 기준) — 20초 자동 갱신</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sector-card" id="btCard" role="button" tabindex="0" title="백테스터 열기" style="animation-delay:.4s">
      <span class="sc-ic">🧪</span>
      <span class="sc-body">
        <span class="sc-title">백테스터</span>
        <span class="sc-sub">SMA 교차·모멘텀·RSI 룰 전략 검증 — 일봉 기반, 매수보유와 비교 · 로컬 연산</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sector-card" id="macroCard" role="button" tabindex="0" title="한국 경제 지표 열기" style="animation-delay:.5s">
      <span class="sc-ic">🏦</span>
      <span class="sc-body">
        <span class="sc-title">한국 · 글로벌 경제 지표</span>
        <span class="sc-sub">ECOS 금리·물가·환율 + 미국증시·VIX·달러·금·WTI 글로벌 지표</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sector-card" id="researchCard" role="button" tabindex="0" title="증권사 리포트 열기" style="animation-delay:.6s">
      <span class="sc-ic">📑</span>
      <span class="sc-body">
        <span class="sc-title">증권사 리포트</span>
        <span class="sc-sub">데일리·종목·산업·투자전략·경제·채권 — 원문 PDF + 로컬 AI 요약</span>
      </span>
      <span class="sc-arrow">›</span>
    </div>
  </div>
</div>
<script>
var q=document.getElementById('q'),sg=document.getElementById('sg'),
    tabstrip=document.getElementById('tabstrip'),stage=document.getElementById('stage'),
    empty=document.getElementById('empty');
var tabs=[],active=null,seq=0,sgItems=[],sgActive=-1,tmr=null,dragId=null;
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
var mktMode='kr';
q.addEventListener('input',function(){clearTimeout(tmr);sgActive=-1;var v=q.value.trim();
  if(!v){hideSg();return;}
  tmr=setTimeout(function(){if(mktMode==='ov')fetchSgOv(v);else fetchSg(v);},180);});
function fetchSgOv(v){fetch('/api/ov/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
  sgItems=(d||[]).map(function(it){it.ov=true;return it;});
  if(!sgItems.length){hideSg();return;}
  sg.innerHTML=sgItems.map(function(it){
    return '<div class="sg-item" data-code="'+esc(it.code)+'"><span class="sg-badge etf">'+esc(it.flag||'🌎')+'</span>'+
      '<span class="sg-code">'+esc(it.code)+'</span><span class="sg-name">'+esc(it.name)+'</span>'+
      '<span class="sg-extra">'+esc(it.exname||'')+'</span></div>';}).join('');
  sg.classList.add('show');}).catch(function(){hideSg();});}
function openOvTab(it){hideSg();q.value='';
  openTab('ov:'+it.code,{url:'/overseas?excd='+encodeURIComponent(it.excd||'')+'&symb='+encodeURIComponent(it.code)+'&name='+encodeURIComponent(it.name||''),
    title:(it.name||it.code),icon:it.flag||'🌎',loading:'해외 종목 불러오는 중…'});}
/* 검색 예시 칩 — 국내/해외 모드에 따라 교체 */
var EX_KR=[['삼성전자','005930'],['SK하이닉스','000660'],['현대차','005380'],['KODEX 200','069500'],['TIGER 미국나스닥100','133690']];
var EX_OV=[['애플','AAPL','NAS'],['엔비디아','NVDA','NAS'],['테슬라','TSLA','NAS'],['마이크로소프트','MSFT','NAS'],['토요타','7203','TSE']];
function renderExamples(){var box=document.querySelector('.empty .ex');if(!box)return;
  box.innerHTML=(mktMode==='ov'
    ?EX_OV.map(function(e){return '<span data-ov="1" data-code="'+e[1]+'" data-excd="'+e[2]+'" data-name="'+esc(e[0])+'">'+esc(e[0])+'</span>';})
    :EX_KR.map(function(e){return '<span data-code="'+e[1]+'">'+esc(e[0])+'</span>';})).join('');
  box.querySelectorAll('span').forEach(function(s){s.addEventListener('click',function(){
    if(s.dataset.ov)openOvTab({code:s.dataset.code,excd:s.dataset.excd,name:s.dataset.name,flag:'🌎'});
    else pick(s.dataset.code);});});}
(function(){var seg=document.getElementById('mktSeg');if(!seg)return;
  seg.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
    mktMode=b.dataset.m;hideSg();
    seg.querySelectorAll('button').forEach(function(z){var on=z===b;z.classList.toggle('on',on);z.setAttribute('aria-selected',on?'true':'false');});
    q.placeholder=mktMode==='ov'
      ?'해외 종목명·티커 검색 (예: 애플, AAPL, 엔비디아, 토요타 — 미국·일본)'
      :'주식·ETF 종목명 또는 6자리 코드 입력 (예: 삼성전자, 005930, KODEX 200)';
    renderExamples();
  });})();
q.addEventListener('keydown',function(e){
  if(!sg.classList.contains('show')){if(e.key==='Enter'){e.preventDefault();doSearch();}return;}
  var rows=sg.querySelectorAll('.sg-item');
  if(e.key==='ArrowDown'){e.preventDefault();sgActive=Math.min(sgActive+1,rows.length-1);paintSg(rows);}
  else if(e.key==='ArrowUp'){e.preventDefault();sgActive=Math.max(sgActive-1,0);paintSg(rows);}
  else if(e.key==='Enter'){e.preventDefault();if(sgActive>=0&&sgItems[sgActive])pick(sgItems[sgActive].code);else doSearch();}
  else if(e.key==='Escape'){hideSg();}});
document.addEventListener('click',function(e){if(!sg.contains(e.target)&&e.target!==q)hideSg();});
q.addEventListener('blur',function(){setTimeout(hideSg,150);});
q.addEventListener('focus',function(){var v=q.value.trim();if(!v)return;if(mktMode==='ov')fetchSgOv(v);else fetchSg(v);});
document.getElementById('form').addEventListener('submit',function(e){e.preventDefault();doSearch();});
document.getElementById('searchBtn').addEventListener('click',doSearch);
function paintSg(rows){rows.forEach(function(r,i){r.classList.toggle('active',i===sgActive);});}
function hideSg(){sg.classList.remove('show');setTimeout(function(){if(!sg.classList.contains('show'))sg.innerHTML='';},200);}
function fetchSg(v){fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
  sgItems=d||[];if(!sgItems.length){hideSg();return;}
  sg.innerHTML=sgItems.map(function(it){var cls=it.type==='ETF'?'etf':'stk';
    return '<div class="sg-item" data-code="'+esc(it.code)+'"><span class="sg-badge '+cls+'">'+it.type+'</span>'+
      '<span class="sg-code">'+esc(it.code)+'</span><span class="sg-name">'+esc(it.name)+'</span>'+
      '<span class="sg-extra">'+esc(it.extra||'')+'</span></div>';}).join('');
  sg.classList.add('show');}).catch(function(){hideSg();});}
sg.addEventListener('click',function(e){var it=e.target.closest('.sg-item');if(it)pick(it.dataset.code);});
function pick(code){
  for(var i=0;i<sgItems.length;i++){var it=sgItems[i];
    if(it.ov&&String(it.code)===String(code)){openOvTab(it);return;}}
  q.value=code;hideSg();doSearch();}
function doSearch(){var v=q.value.trim();if(!v)return;hideSg();
  if(mktMode==='ov'){var s=v.toUpperCase();
    openTab('ov:'+s,{url:'/overseas?symb='+encodeURIComponent(s),title:s+' 🌎',icon:'🌎',loading:'해외 종목 불러오는 중…'});return;}
  openTab(v);}
window.MI_TABS=true;
window.miOpenStockTab=function(code){if(code)openTab(String(code));};
window.miOpenUrlTab=function(id,opts){if(id&&opts&&opts.url)openTab(String(id),opts);};
window.miOpenIndexTab=function(code,name){if(!code)return;
  openTab('idx:'+code,{url:'/index_page?code='+encodeURIComponent(code)+'&name='+encodeURIComponent(name||''),
    title:(name||'지수'),icon:'📈',loading:'지수 상세 불러오는 중…'});};
// ── 네이티브 메뉴바 브리지 (app.py macOS 메뉴 → 웹 UI). 각 함수는 처리 여부(boolean) 반환 ──
function _miActiveFrame(){return stage.querySelector('.framewrap[data-id="'+active+'"] iframe.frame');}
window.MI_FOCUS_SEARCH=function(){try{q.focus();q.select();}catch(e){}return true;};
window.MI_CLOSE_TAB=function(){if(active){closeTab(active);return true;}return false;};
window.MI_NEXT_TAB=function(){if(tabs.length<2)return false;
  var i=tabs.findIndex(function(t){return t.id===active;});activate(tabs[(i+1)%tabs.length].id);return true;};
window.MI_PREV_TAB=function(){if(tabs.length<2)return false;
  var i=tabs.findIndex(function(t){return t.id===active;});activate(tabs[(i-1+tabs.length)%tabs.length].id);return true;};
window.MI_RELOAD=function(){var f=_miActiveFrame();
  if(f){try{f.contentWindow.location.reload();}catch(e){f.src=f.src;}return true;}
  location.reload();return true;};
window.MI_PRINT=function(){var f=_miActiveFrame();
  try{if(f&&f.contentWindow){f.contentWindow.focus();f.contentWindow.print();}else{window.print();}}catch(e){try{window.print();}catch(_){}}
  return true;};
function goHome(){active=null;
  document.querySelectorAll('.framewrap').forEach(function(w){w.classList.remove('show');});
  if(typeof empty!=='undefined'&&empty){
    empty.classList.remove('hide');
    /* heroRise 재트리거 — 랜딩 복귀 시 카드가 다시 떠오르는 모션 */
    var h=document.getElementById('hero3d');
    if(h){h.style.animation='none';void h.offsetHeight;h.style.animation='heroRise .6s var(--ease) both';}
    document.querySelectorAll('.sector-card').forEach(function(c){
      c.style.animation='none';void c.offsetHeight;c.style.animation='heroRise .6s var(--ease) .12s both';});
  }
  renderTabs();
  if(q){q.value='';try{q.focus();}catch(e){}}}
(function(){var b=document.querySelector('.topbar .brand');
  if(b){b.style.cursor='pointer';b.title='랜딩으로 돌아가기';b.addEventListener('click',goHome);}})();
/* AI 버튼 상태 점 + 라벨 (로컬 준비=Local / Gemini 선택=Gemini / 그 외=AI) — 경량 폴링 (작업5) */
(function(){
  var dot=document.getElementById('aiDot'),lbl=document.getElementById('aiLbl');if(!dot)return;
  var loaded=false,lastId='';
  function prov(){try{return localStorage.getItem('kmkt-ai-prov')||'local';}catch(e){return 'local';}}
  function sync(){
    var p=prov(),on=(p==='gemini')||loaded;
    dot.classList.toggle('on',on);
    dot.title=(p==='gemini')?'Gemini(클라우드) 사용 중':(loaded?('로컬 모델 로드됨'+(lastId?': '+lastId:'')):'로컬 모델 미로드');
    if(lbl)lbl.textContent=(p==='gemini')?'Gemini':(loaded?'Local':'AI');
  }
  window.__kmktAiBtnSync=sync;            // 팝오버에서 provider 전환 시 즉시 호출
  function tick(){
    if(document.hidden)return;             // 백그라운드 탭에선 생략(발열↓)
    fetch('/api/llm/loaded',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
      loaded=!!(d&&d.loaded);lastId=(d&&d.id)||'';sync();
    }).catch(function(){loaded=false;sync();});
  }
  tick();setInterval(tick,30000);sync();   // 30초 간격(상시 폴링 최소화)
})();
/* 상단 AI 버튼 → 로컬 LLM(LM Studio) 제어 팝오버 (작업6) */
(function(){
  var btn=document.getElementById('aiCtrlBtn'),pop=document.getElementById('aiPop');
  if(!btn||!pop)return;
  var open=false,busy=false,cur=null,aipTokModel=null;
  function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function row(k,v){return '<div class="aip-row"><span class="aip-k">'+k+'</span><span class="aip-v">'+esc(v)+'</span></div>';}
  // ── 로컬/Gemini provider 선택 + Gemini 모델·시스템프롬프트 (localStorage 공유: 채팅 위젯과 동일 키) ──
  function lsGet(k,d){try{return localStorage.getItem(k)||d;}catch(e){return d;}}
  function lsSet(k,v){try{localStorage.setItem(k,v);}catch(e){}}
  function aiProv(){return lsGet('kmkt-ai-prov','local');}
  var GMODELS=[['gemini-3.5-flash','✦ 3.5 Flash · 균형(기본)'],['gemini-2.5-flash','✦ 2.5 Flash · 웹검색 ✓'],
    ['gemini-2.5-flash-lite','✦ 2.5 Flash-Lite · 검색+초경량'],['gemini-3.1-flash-lite','✦ 3.1 Flash-Lite · 초고속']];
  function provBar(p){return '<div class="aip-seg" id="aipProv">'
    +'<button type="button" data-p="local"'+(p==='local'?' class="on"':'')+'>💻 로컬 LLM</button>'
    +'<button type="button" data-p="gemini"'+(p==='gemini'?' class="on"':'')+'>🌩️ Gemini</button></div>';}
  function geminiPanel(){
    var gm=lsGet('kmkt-ai-gmodel','gemini-3.5-flash'),gs=lsGet('kmkt-ai-gsys','');
    var opts=GMODELS.map(function(o){return '<option value="'+o[0]+'"'+(o[0]===gm?' selected':'')+'>'+esc(o[1])+'</option>';}).join('');
    return '<div style="padding:0 14px;margin-top:2px;"><select id="aipGModel" class="aip-select">'+opts+'</select></div>'
      +'<div style="padding:12px 14px 4px;"><div class="aip-lbl">시스템 프롬프트 <span style="opacity:.55;font-weight:500;">· Gemini 요청사항</span></div>'
      +'<textarea id="aipGsys" class="aip-ta" placeholder="예: 보수적 가치투자자 관점으로, 핵심만 불릿 3개로 요약해줘.">'+esc(gs)+'</textarea></div>'
      +'<div class="aip-info">'+row('구동','Gemini 클라우드 · 무료 티어')+row('웹검색','2.5 계열 모델만')
      +row('적용 범위','AI 요약·해석·코멘터리 전체')+'</div>';
  }
  function bindProv(){
    var box=document.getElementById('aipProv');if(!box)return;
    box.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
      lsSet('kmkt-ai-prov',b.dataset.p);
      try{if(window.__kmktAiBtnSync)window.__kmktAiBtnSync();}catch(e){}
      if(b.dataset.p==='gemini'){render(cur);}else{load();}   // 로컬 전환 시 상태 재조회
    });});
    var sel=document.getElementById('aipGModel');
    if(sel)sel.addEventListener('change',function(){lsSet('kmkt-ai-gmodel',sel.value);});
    var ta=document.getElementById('aipGsys');
    if(ta)ta.addEventListener('input',function(){lsSet('kmkt-ai-gsys',ta.value);});
  }
  function close(){open=false;pop.classList.remove('show');btn.setAttribute('aria-expanded','false');}
  function render(st){
    cur=st;
    // ── Gemini 선택 시: 모델 select + 시스템 프롬프트 textarea (로컬 상태와 무관하게 표시) ──
    if(aiProv()==='gemini'){
      pop.innerHTML='<div class="aip-h"><span>AI 모델</span><span class="aip-state on">☁︎ Gemini</span></div>'
        +provBar('gemini')+geminiPanel();
      bindProv();return;}
    if(!st||!st.installed){
      pop.innerHTML='<div class="aip-h"><span>AI 모델</span></div>'+provBar('local')
        +'<div class="aip-msg">로컬 LLM 환경이 설치되어 있지 않습니다. 상단에서 <b>Gemini</b>로 전환해 사용할 수 있어요.</div>';
      bindProv();return;}
    var m=st.model;
    if(!m && (!st.models || !st.models.length)){
      pop.innerHTML='<div class="aip-h"><span>AI 모델</span></div>'+provBar('local')+
        '<div class="aip-msg">설치된 모델이 없습니다. LM Studio에서 모델을 받거나 <b>Gemini</b>로 전환하세요.</div>';
      bindProv();return;}
    if(!m && st.models && st.models.length>0) m=st.models[0];
    var loaded=!!m.loaded;
    var opts = (st.models||[]).map(function(x){
      var sel=(x.id===m.id)?' selected':'';
      return '<option value="'+esc(x.id)+'"'+sel+'>'+esc(x.id)+'</option>';
    }).join('');
      // 모델별 컨텍스트 능동 인식 (작업2): 모델이 바뀌면 그 모델의 기본 Max Tokens 로 갱신.
      if(m && m.id!==aipTokModel){ if(m.def_tokens) window._llmMaxTokens=m.def_tokens; aipTokModel=m.id; }
      function fmtCtx(n){ if(!n)return '—'; return n>=1024 ? (Math.round(n/1024)+'K') : (''+n); }
      var ctxText = m.max_ctx ? (fmtCtx(m.max_ctx) + (m.loaded_ctx ? (' · 로드 '+fmtCtx(m.loaded_ctx)) : '')) : '—';
      var recText = (m.rec_ctx_lo && m.rec_ctx_hi) ? (m.rec_ctx_lo + ' ~ ' + m.rec_ctx_hi)
        : (m.max_ctx ? (Math.floor(m.max_ctx/8) + ' ~ ' + Math.floor(m.max_ctx/4))
        : (m.id.toLowerCase().includes('qwen') ? '1024 ~ 4096' : '512 ~ 2048'));
      pop.innerHTML=
      '<div class="aip-h"><span>로컬 AI 모델</span><span class="aip-state '+(loaded?'on':'')+'">'+
        (busy?'처리 중…':(loaded?'● 로드됨':'○ 언로드'))+'</span></div>'+
      provBar('local')+
      '<div style="padding:0 14px;margin-top:10px;"><select id="aipCombo" style="width:100%;padding:9px 12px;border-radius:10px;background:var(--card);color:var(--ink);border:1px solid var(--line);font-size:13px;outline:none;box-shadow:0 1px 2px rgba(0,0,0,0.04);appearance:auto;"'+(busy?' disabled':'')+'>'+opts+'</select></div>'+
      '<div style="display:flex;gap:8px;padding:10px 14px 2px;">'+
        '<div style="flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:var(--card);font-size:13px;color:var(--ink);font-family:ui-monospace, monospace;font-weight:500;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'+
          '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M15 14h.01"/><path d="M9 14h.01"/><path d="M12 14h.01"/><path d="M4 11h16"/><path d="M6 18v2"/><path d="M10 18v2"/><path d="M14 18v2"/><path d="M18 18v2"/></svg> '+
          '<span id="hwRamVal">0.0 GB</span>'+
        '</div>'+
        '<div style="flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:var(--card);font-size:13px;color:var(--ink);font-family:ui-monospace, monospace;font-weight:500;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'+
          '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg> '+
          '<span id="hwCpuVal">0.0%</span>'+
        '</div>'+
      '</div>'+
      '<div style="padding:10px 14px 4px;">'+
        '<button class="aip-toggle '+(loaded?'on':'')+'" id="aipTog" style="margin-bottom:0;"'+(busy?' disabled':'')+'>'+
          '<span class="aip-tg-knob"></span><span class="aip-tg-txt">'+
          (busy?'처리 중…':(loaded?'Unload · 메모리 해제':'Load · 메모리 로드'))+'</span></button>'+
      '</div>'+
      '<div class="aip-info">'+
        '<div class="aip-row" style="align-items:center;"><span class="aip-k">Max Tokens</span><span class="aip-v"><input type="number" id="aipTokens" value="'+(window._llmMaxTokens||m.def_tokens||1200)+'" style="width:70px;text-align:right;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font-size:12px;padding:4px 6px;outline:none;" min="100" max="200000" step="100"></span></div>'+
        row('Max Context', ctxText)+
        row('Recommended', recText)+
        row('Format',m.format||'—')+
        row('Quantization',m.quant||'—')+row('Size on disk',(m.size!=null?m.size+' GB':'—'))+'</div>';
    bindProv();
    var tg=document.getElementById('aipTog');if(tg)tg.addEventListener('click',toggle);
    var tk=document.getElementById('aipTokens');if(tk)tk.addEventListener('change',function(e){window._llmMaxTokens=parseInt(e.target.value,10)||1200;});
    var cb=document.getElementById('aipCombo');
    if(cb)cb.addEventListener('change', function(e){
      var selId=e.target.value, selM=st.models.find(function(x){return x.id===selId;});
      if(selM){
        var oldLoaded = st.models.some(function(x){return x.loaded;});
        st.model=selM;
        if(oldLoaded && !selM.loaded){
          busy=true; render(st);
          fetch('/api/llm/unload',{method:'POST'})
            .then(function(r){return r.json();})
            .then(function(newSt){
               busy=false;
               var preserved = (newSt.models||[]).find(function(x){return x.id===selId;});
               if(preserved) newSt.model = preserved;
               else newSt.model = selM;
               render(newSt);
            })
            .catch(function(){busy=false; load();});
        } else {
          render(st);
        }
      }
    });
  }
  function load(){
    pop.innerHTML='<div class="aip-h"><span>로컬 AI</span></div><div class="aip-msg">상태 확인 중…</div>';
    fetch('/api/llm/status',{cache:'no-store'}).then(function(r){return r.json();}).then(render)
      .catch(function(){pop.innerHTML='<div class="aip-msg">상태를 불러올 수 없습니다.</div>';});
  }
  function toggle(){
    if(busy||!cur||!cur.model)return;
    busy=true;var loaded=!!cur.model.loaded;var tk=cur.model.id; render(cur);
    fetch(loaded?'/api/llm/unload':'/api/llm/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelKey:tk})})
      .then(function(r){return r.json();}).then(function(st){busy=false;render(st);})
      .catch(function(){busy=false;load();});
  }
  var hwTimer=null;
  function pollHw(){
    if(!open)return;
    fetch('/api/llm/hardware').then(function(r){return r.json();}).then(function(d){
      var r=document.getElementById('hwRamVal'), c=document.getElementById('hwCpuVal');
      if(r) r.textContent=d.ram_gb.toFixed(1)+' GB';
      if(c) c.textContent=d.cpu_pct.toFixed(1)+'%';
    }).catch(function(){});
  }
  function startHw(){if(hwTimer)clearInterval(hwTimer);hwTimer=setInterval(pollHw,1500);pollHw();}
  function stopHw(){if(hwTimer){clearInterval(hwTimer);hwTimer=null;}}
  
  btn.addEventListener('click',function(e){e.stopPropagation();
    if(open){close();stopHw();return;} open=true;pop.classList.add('show');btn.setAttribute('aria-expanded','true');
    if(aiProv()==='gemini'){render(cur);}else{load();startHw();}});
  // ⚠️ 바깥 클릭 닫기는 'mousedown' 으로 판정한다. Load/모델선택 클릭은 render() 가
  // pop.innerHTML 을 교체하므로, 'click' 시점엔 e.target(교체된 버튼)이 더 이상 pop 안에
  // 없어 !pop.contains 가 참이 되어 팝오버가 잘못 닫혔다. mousedown 은 재렌더 '전'에
  // 발생하므로 클릭 대상이 팝오버 내부인지 정확히 알 수 있다.
  document.addEventListener('mousedown',function(e){if(open&&!pop.contains(e.target)&&e.target!==btn){close();stopHw();}});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&open){close();stopHw();}});
})();
/* 상단바 드래그 제어: 인터랙티브 요소(검색창·버튼 등)에서는 창이 끌려가지 않게 하고,
   빈 영역 더블클릭 시 네이티브 창 zoom(최대화 토글) 호출. */
(function(){
  var bar=document.querySelector('.topbar');if(!bar)return;
  var INTERACTIVE='input,textarea,select,button,a,[role="button"],[role="switch"],[role="tab"],[role="dialog"],'+
    '.searchwrap,.sg,.kospi-ticker,.theme-toggle,.mkt-seg,.brand,.ai-wrap,.ai-pop';
  function isInteractive(t){return t&&t.closest&&t.closest(INTERACTIVE);}
  // pywebview 드래그 리스너는 document.body(버블)에 달림 → 인터랙티브 타깃이면 버블 차단해 드래그 방지
  bar.addEventListener('mousedown',function(e){if(isInteractive(e.target))e.stopPropagation();},false);
  // 빈 영역 더블클릭 → 창 최대화/복원
  bar.addEventListener('dblclick',function(e){
    if(isInteractive(e.target))return;
    try{if(window.pywebview&&window.pywebview.api&&window.pywebview.api._web_zoom_window)
      window.pywebview.api._web_zoom_window();}catch(_){}});
})();
function miPing(){if(window.MI_APP_ACTIVE === false)return; fetch('/__ping').catch(function(){});}
miPing();setInterval(miPing,3000);
// 발열↓: 비활성/숨김이면 전면 그라데이션 애니메이션 정지(class 토글은 무시할 만한 비용).
(function(){var b=document.body;function bgSync(){b.classList.toggle('kmkt-bg-off',document.hidden||window.MI_APP_ACTIVE===false);}
 document.addEventListener('visibilitychange',bgSync);setInterval(bgSync,3000);bgSync();})();
// KOSPI 실시간 지수 티커 (한국투자증권 KIS · /api/index)
// 지수값: 자릿수 롤링 애니메이션(바뀐 자리만 위/아래 슬라이드)
(function(){
 var ktBox=document.getElementById('kospiTicker'),ktValEl=document.getElementById('ktVal'),
     ktChg=document.getElementById('ktChg');
 var lastKtText=null,lastKtNum=null,lastKtChgText=null;
 var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 var KT_EASE='cubic-bezier(.16,1,.3,1)',KT_DUR=0.62;
 function ktFmt(n){return Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}
 function ktStaticCell(h,ch){var c=document.createElement('span');c.className='rt-ch';c.style.cssText='height:'+h+'px;line-height:'+h+'px;';c.textContent=ch;return c;}
 function ktRollCell(h,oldCh,newCh,up,delay){
   var cell=document.createElement('span');cell.className='rt-ch';cell.style.cssText='height:'+h+'px;overflow:hidden;';
   var col=document.createElement('span');col.className='rt-col';
   function row(t){var s=document.createElement('span');s.style.cssText='display:block;height:'+h+'px;line-height:'+h+'px;';s.textContent=t;return s;}
   if(up){col.appendChild(row(oldCh));col.appendChild(row(newCh));col.style.transform='translateY(0)';}
   else  {col.appendChild(row(newCh));col.appendChild(row(oldCh));col.style.transform='translateY(-'+h+'px)';}
   cell.appendChild(col);
   requestAnimationFrame(function(){requestAnimationFrame(function(){
     col.style.transition='transform '+KT_DUR+'s '+KT_EASE+' '+delay+'ms';
     col.style.transform=up?'translateY(-'+h+'px)':'translateY(0)';});});
   return cell;}
 // el 의 자릿수만 굴리는 전환 (지수값·등락 공용)
 function ktRollPrice(el,oldStr,newStr,up){
   if(RM||!oldStr||oldStr===newStr){el.textContent=newStr;return;}
   var h=el.offsetHeight||22;
   var nL=newStr.length,oL=oldStr.length;
   var frag=document.createDocumentFragment(),p,r,nc,oc;
   for(p=0;p<nL;p++){
     r=nL-1-p;
     nc=newStr.charAt(p);
     oc=(r<oL)?oldStr.charAt(oL-1-r):'';
     if(oc===nc)frag.appendChild(ktStaticCell(h,nc));
     else frag.appendChild(ktRollCell(h,oc,nc,up,Math.min(r,8)*26));
   }
   el.innerHTML='';el.appendChild(frag);
 }
 function pollKospi(){
   if(document.hidden || window.MI_APP_ACTIVE === false)return; // 절전 모드
   fetch('/api/index?code=0001',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
     if(!d||!d.ok)return;
     var v=ktFmt(d.value);
     var up=(lastKtNum!==null)?(d.value>lastKtNum):(d.direction==='▲');
     if(v!==lastKtText){ktRollPrice(ktValEl,lastKtText||'',v,up);lastKtText=v;}
     lastKtNum=d.value;
     ktBox.classList.remove('up','down','flat');
     ktBox.classList.add(d.direction==='▲'?'up':(d.direction==='▼'?'down':'flat'));
     var s=d.change>0?'+':'';
     var newKtChgTxt=d.direction+' '+s+ktFmt(d.change)+' ('+(d.change_pct>0?'+':'')+d.change_pct.toFixed(2)+'%)';
     if(newKtChgTxt!==lastKtChgText){ktRollPrice(ktChg,lastKtChgText||'',newKtChgTxt,up);}
     lastKtChgText=newKtChgTxt;
     // 장 단계: KIS 휴장일조회+장운영시간 phase(open/pre/closed/holiday) 반영 (작업1·2)
     var ph=d.phase||((typeof d.market_open!=='undefined')?(d.market_open?'open':'closed'):(d.is_closed?'closed':'open'));
     var closed=ph!=='open';window.__ktClosed=closed;   // 폴링 주기 적응용(장마감이면 느리게)
     var tagTxt={pre:'개장 전',holiday:'휴장',closed:'종가'}[ph];
     var dot=ktBox.querySelector('.kt-dot'),nameEl=ktBox.querySelector('.kt-name');
     if(closed){
       if(dot){dot.style.background='#8a98b8';dot.style.animation='none';dot.style.boxShadow='none';}
       var tag=ktBox.querySelector('.kt-closed-tag');
       if(!tag){tag=document.createElement('span');tag.className='kt-closed-tag';
         tag.style.cssText='font-size:10px;font-weight:700;opacity:.78;margin-left:3px;'+
           'color:#b0bdd8;vertical-align:middle;letter-spacing:.03em;';
         nameEl.insertAdjacentElement('afterend',tag);}
       tag.textContent=tagTxt||'종가';
     }else{
       if(dot){dot.style.background='';dot.style.animation='';dot.style.boxShadow='';}
       var existTag=ktBox.querySelector('.kt-closed-tag');if(existTag)existTag.remove();}
   }).catch(function(){});
 }
 // 적응형 폴링(발열↓): 비활성/숨김이면 폴링 생략, 장마감이면 30s, 장중에만 2s.
 (function ktTick(){
   var idle=(document.hidden||window.MI_APP_ACTIVE===false);
   if(!idle)pollKospi();
   setTimeout(ktTick, idle?20000:(window.__ktClosed?30000:2000));
 })();
 document.addEventListener('visibilitychange',function(){if(!document.hidden)pollKospi();});
 if(ktBox){ktBox.style.cursor='pointer';ktBox.title='코스피 지수 상세 보기';
   ktBox.addEventListener('click',function(){window.miOpenIndexTab('0001','코스피');});}
})();
document.addEventListener('visibilitychange',function(){if(!document.hidden)miPing();});
window.addEventListener('pagehide',function(){try{navigator.sendBeacon('/__bye');}catch(e){}});
renderExamples();   // 초기 예시 칩 바인딩(국내). 토글 시 renderExamples 가 해외로 교체
var hero=document.getElementById('hero3d');
stage.addEventListener('mousemove',function(e){if(tabs.length)return;var r=stage.getBoundingClientRect();
  var rx=((e.clientY-r.top)/r.height-0.5)*-9,ry=((e.clientX-r.left)/r.width-0.5)*11;
  hero.style.transform='rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg)';});
stage.addEventListener('mouseleave',function(){hero.style.transform='';});
function openTab(query,opts){opts=opts||{};
  var ex=tabs.find(function(t){return t.query===query;});
  if(ex){activate(ex.id);return;}var id='t'+(++seq);
  var wrap=document.createElement('div');wrap.className='framewrap';wrap.dataset.id=id;
  var ov=document.createElement('div');ov.className='overlay show';
  ov.innerHTML='<div class="spinner"></div><p>'+(opts.loading||'리포트를 생성하는 중…')+'</p>';
  var f=document.createElement('iframe');f.className='frame';
  f.addEventListener('load',function(){ov.classList.remove('show');updateMeta(id,f);});
  f.src=opts.url||('/dashboard?q='+encodeURIComponent(query));
  wrap.appendChild(ov);wrap.appendChild(f);stage.appendChild(wrap);
  tabs.push({id:id,query:query,title:opts.title||query,icon:opts.icon||'⏳'});activate(id);}
function updateMeta(id,f){var t=tabs.find(function(x){return x.id===id;});if(!t)return;
  var title='',kind='';
  try{title=(f.contentDocument&&f.contentDocument.title)||'';
    kind=(f.contentDocument&&f.contentDocument.documentElement.getAttribute('data-kind'))||'';}catch(e){}
  if(title)t.title=title;
  t.icon=(kind==='etf')?'📊':(kind==='sector'?'🏷️':(kind==='market'?'📈':'📈'));renderTabs();}
document.getElementById('sectorCard').addEventListener('click',function(){
  openTab('__sector__',{url:'/sector',title:'업종 지수',icon:'🏷️',loading:'업종 지수를 불러오는 중…'});});
document.getElementById('marketCard').addEventListener('click',function(){
  openTab('__market__',{url:'/market',title:'시장 현황',icon:'📈',loading:'시장 현황을 불러오는 중…'});});
document.getElementById('worldCard').addEventListener('click',function(){
  openTab('__world__',{url:'/world_page',title:'세계 시장',icon:'🌍',loading:'세계 지수·환율 불러오는 중…'});});
document.getElementById('btCard').addEventListener('click',function(){
  openTab('__backtest__',{url:'/backtest_page',title:'백테스터',icon:'🧪',loading:'백테스터 준비 중…'});});
document.getElementById('macroCard').addEventListener('click',function(){
  openTab('__macro__',{url:'/macro_page',title:'한국 경제 지표',icon:'🏦',loading:'경제 지표 불러오는 중…'});});
document.getElementById('researchCard').addEventListener('click',function(){
  openTab('__research__',{url:'/research_page',title:'증권사 리포트',icon:'📑',loading:'증권사 리포트 불러오는 중…'});});
[document.getElementById('sectorCard'),document.getElementById('marketCard'),document.getElementById('worldCard'),document.getElementById('btCard'),document.getElementById('macroCard'),document.getElementById('researchCard')].forEach(function(card){
  card.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){e.preventDefault();card.click();}});});
function activate(id){active=id;
  document.querySelectorAll('.framewrap').forEach(function(w){
    var show = w.dataset.id===id;
    w.classList.toggle('show',show);
    try { var f = w.querySelector('iframe.frame'); if(f && f.contentWindow) f.contentWindow.postMessage({mi_tab_active: show}, '*'); } catch(e){}
  });
  if(tabs.length){empty.classList.add('hide');}else{empty.classList.remove('hide');}
  renderTabs();}
function closeTab(id){var i=tabs.findIndex(function(t){return t.id===id;});if(i<0)return;
  tabs.splice(i,1);
  var w=stage.querySelector('.framewrap[data-id="'+id+'"]');
  if(w){
    w.classList.remove('show');w.classList.add('exit');
    var cleanup=function(){if(w.parentNode)w.parentNode.removeChild(w);};
    w.addEventListener('transitionend',function _te(e){if(e.target===w){w.removeEventListener('transitionend',_te);cleanup();}});
    setTimeout(cleanup,400); /* 안전망 */
  }
  if(active===id){active=tabs.length?tabs[Math.min(i,tabs.length-1)].id:null;}
  if(active)activate(active);else{empty.classList.remove('hide');
    var h=document.getElementById('hero3d');
    if(h){h.style.animation='none';void h.offsetHeight;h.style.animation='heroRise .6s var(--ease) both';}
    renderTabs();}}
function renderTabs(){tabstrip.innerHTML=tabs.map(function(t){
  return '<div class="tab'+(t.id===active?' active':'')+(t.id===dragId?' dragging':'')+'" data-id="'+t.id+'">'+
    '<span class="tab-ic">'+(t.icon||'📈')+'</span><span class="tab-label" title="'+esc(t.title)+'">'+esc(t.title)+'</span>'+
    '<span class="tab-close" data-id="'+t.id+'">×</span></div>';}).join('');
  tabstrip.classList.toggle('show',tabs.length>0);}
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

// Spotlight
var spot=document.getElementById('spotlight'), spotInput=document.getElementById('spotInput'), spotResults=document.getElementById('spotResults');
var spotData=[]; var spotIndex=-1;
document.addEventListener('keydown',function(e){
  if(e.metaKey&&e.key==='k'){e.preventDefault();spot.classList.add('show');spotInput.focus();}
  if(e.key==='Escape'&&spot.classList.contains('show')){spot.classList.remove('show');}
});
if(spot){
  spot.addEventListener('click',function(e){if(e.target===spot)spot.classList.remove('show');});
  spotInput.addEventListener('input',function(e){
    var q=e.target.value.trim();
    if(!q){spotResults.innerHTML='';spotData=[];return;}
    fetch('/suggest?q='+encodeURIComponent(q)).then(r=>r.json()).then(d=>{
      spotData=d; spotIndex=-1;
      spotResults.innerHTML=d.map((x,i)=>'<div class="spotlight-item" data-index="'+i+'"><span class="sg-badge '+(x.type==='ETF'?'etf':'stk')+'">'+x.type+'</span><span class="sg-code">'+x.code+'</span><span class="sg-name">'+x.name+'</span></div>').join('');
    });
  });
  spotInput.addEventListener('keydown',function(e){
    if(!spotData.length)return;
    var items=spotResults.querySelectorAll('.spotlight-item');
    if(e.key==='ArrowDown'){e.preventDefault();spotIndex=Math.min(spotIndex+1,spotData.length-1);}
    else if(e.key==='ArrowUp'){e.preventDefault();spotIndex=Math.max(spotIndex-1,0);}
    else if(e.key==='Enter'){
      e.preventDefault();
      if(spotIndex<0)spotIndex=0;
      pick(spotData[spotIndex].code);
      spot.classList.remove('show');
      return;
    }
    items.forEach((x,i)=>x.classList.toggle('active',i===spotIndex));
  });
  spotResults.addEventListener('click',function(e){
    var item=e.target.closest('.spotlight-item');
    if(!item)return;
    var idx=parseInt(item.dataset.index,10);
    pick(spotData[idx].code);
    spot.classList.remove('show');
  });
}

// Screener Button
document.getElementById('screenerBtn').addEventListener('click',function(){
  openTab('__screener__', {url: '/screener_page', title: '스크리너 (DuckDB)', icon: '🔍', loading:'전 종목 캐시 스캔 중...'});
});

// Realtime Trading Desk Button
document.getElementById('realtimeBtn').addEventListener('click',function(){
  openTab('__realtime__', {url: '/realtime_page', title: '실시간 트레이딩', icon: '📡', loading:'실시간 데스크 준비 중...'});
});

// App expose
window.showSpotlight = function() {
  spot.classList.add('show');
  spotInput.focus();
};
</script>
<div id="spotlight">
  <div class="spotlight-box">
    <input type="text" id="spotInput" class="spotlight-input" placeholder="Spotlight 검색 (종목명 입력 후 Enter)">
    <div class="spotlight-results" id="spotResults"></div>
  </div>
</div>
</body></html>
"""

_BACKTEST_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="backtest"><head><meta charset="utf-8">
<title>백테스터</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
/* 트레이딩 터미널 — 라이트(기본) + 다크(html.dark). Apple macOS 토큰 정렬. */
:root{--bg:#f4f5f9;--panel:rgba(255,255,255,.9);--panel-b:rgba(60,60,67,.12);
 --ink:#1d1d1f;--sub:rgba(60,60,67,.6);--line:rgba(60,60,67,.1);--row:rgba(10,132,255,.05);
 --up:#FF3B30;--dn:#2E75B6;--accent:#0A84FF;--violet:#9b6bff;--buy:#16a06a;--sell:#e0820a;
 --maf:#e67e22;--mas:#2e86de;--cand-up:#FF3B30;--cand-dn:#2E75B6;--grid-ln:rgba(60,60,67,.09);
 --opt:#141926;--optc:#e6ecff;--sgg-bg:rgba(255,255,255,.98);}
html.dark{--bg:#0a0e17;--panel:rgba(255,255,255,.045);--panel-b:rgba(130,150,255,.14);
 --ink:#e6ecff;--sub:#8a97b5;--line:rgba(255,255,255,.08);--row:rgba(120,150,255,.06);
 --up:#ff5a52;--dn:#5aadff;--accent:#36c6ff;--buy:#2ee6a6;--sell:#ffb020;
 --maf:#f5a623;--mas:#36c6ff;--cand-up:#ff5a52;--cand-dn:#5aadff;--grid-ln:rgba(255,255,255,.07);
 --sgg-bg:#141a28;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:var(--ink);
 -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;
 background:radial-gradient(60% 50% at 12% -4%,rgba(120,160,255,.10),transparent 60%),
   radial-gradient(50% 46% at 96% 0%,rgba(200,150,255,.08),transparent 60%),var(--bg);
 background-attachment:fixed;padding:16px 18px 28px;transition:background .4s ease;}
html.dark body{background:radial-gradient(60% 50% at 12% -4%,rgba(60,90,200,.16),transparent 60%),
   radial-gradient(50% 46% at 96% 0%,rgba(155,107,255,.13),transparent 60%),var(--bg);background-attachment:fixed;}
.panel{background:var(--panel);border:1px solid var(--panel-b);border-radius:14px;
 box-shadow:0 8px 28px rgba(20,30,70,.07);
 -webkit-backdrop-filter:saturate(180%) blur(18px);backdrop-filter:saturate(180%) blur(18px);padding:14px 16px;margin-bottom:12px;}
html.dark .panel{box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 12px 34px rgba(4,8,22,.4);backdrop-filter:blur(8px);}
h2{font-size:18px;font-weight:800;letter-spacing:-.02em;display:flex;align-items:center;gap:8px;}
.sub{color:var(--sub);font-size:12px;}
/* 폼 — 애플 UI 톤·빈공간 없이 채움 (종목 필드가 남는 폭을 흡수) */
#formPanel{position:relative;z-index:30;}   /* 자동완성 드롭다운이 아래 패널에 가려지지 않게 */
.form{display:flex;gap:12px 12px;flex-wrap:wrap;align-items:flex-end;}
#prm{display:contents;}
.fld{display:flex;flex-direction:column;gap:6px;position:relative;}
.fld label{font-size:11.5px;color:var(--sub);font-weight:600;letter-spacing:-.01em;}
.fld input,.fld select{font:inherit;font-size:14px;padding:9px 12px;border:1px solid var(--panel-b);
 border-radius:10px;background:var(--row);color:var(--ink);outline:none;min-height:40px;width:100%;transition:box-shadow .15s,border-color .15s;}
.fld input:focus,.fld select:focus{box-shadow:0 0 0 3px rgba(10,132,255,.22);border-color:var(--accent);}
.fld select option{background:var(--sgg-bg);color:var(--ink);}
.fld.f-code{flex:1 1 240px;min-width:190px;}            /* 종목: 남는 폭 흡수 */
.fld.f-strat{flex:0 1 180px;min-width:150px;}
.fld.f-num{flex:0 0 96px;} .fld.f-num input{width:96px;}
.fld.f-days{flex:0 0 92px;}
.run{font:inherit;font-size:14.5px;font-weight:700;padding:0 26px;min-height:40px;border:0;border-radius:11px;
 background:var(--accent);color:#fff;cursor:pointer;align-self:flex-end;flex:0 0 auto;box-shadow:0 6px 16px rgba(10,132,255,.28);}
.run:hover{filter:brightness(1.04);} html.dark .run{background:linear-gradient(135deg,#36c6ff,#5b8cff);color:#06121f;}
.run:disabled{opacity:.5;}
.sgg{position:absolute;top:100%;left:0;right:0;z-index:1000;background:var(--sgg-bg);border:1px solid var(--panel-b);
 border-radius:10px;margin-top:4px;overflow:hidden;display:none;box-shadow:0 16px 40px rgba(20,30,70,.2);
 -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);}
.sgg.show{display:block;}
.sgg .it{padding:9px 11px;font-size:12.5px;cursor:pointer;display:flex;gap:8px;}
.sgg .it:hover{background:var(--row);}
.sgg .c{color:var(--sub);margin-left:auto;}
/* 상태 스트립 */
.statbar{display:flex;align-items:center;gap:18px;flex-wrap:wrap;}
.statbar .nm{font-size:16px;font-weight:800;}
.statbar .meta{font-size:12px;color:var(--sub);}
.statbar .ret{margin-left:auto;text-align:right;}
.statbar .ret .v{font-size:30px;font-weight:800;letter-spacing:-.02em;line-height:1;}
.statbar .ret .l{font-size:11px;color:var(--sub);}
.statbar .stag{font-size:12px;font-weight:700;color:var(--accent);border:1px solid var(--panel-b);
 border-radius:8px;padding:4px 10px;}
/* 메인 그리드 (우측 성과 패널 너비 사용자 조절 — 토스식 패널 리사이즈) */
.grid{display:grid;grid-template-columns:minmax(0,1fr) 7px var(--statw,256px);gap:0 10px;align-items:start;}
.grid .rsz{align-self:stretch;cursor:col-resize;border-radius:3px;background:var(--line);transition:background .15s;min-height:120px;}
.grid .rsz:hover,.grid .rsz.drag{background:var(--accent);}
@media(max-width:820px){.grid{grid-template-columns:1fr;}.grid .rsz{display:none;}}
h3{font-size:13px;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:8px;}
.chiprow{display:flex;gap:14px;font-size:11.5px;color:var(--sub);margin-bottom:6px;flex-wrap:wrap;}
.chiprow i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:5px;}
.chiprow .tri{font-style:normal;font-weight:800;}
canvas{width:100%;display:block;}
#cvMain{height:420px;} #cvEq{height:200px;}
/* 우측 성과 패널 */
.stats .srow{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
 padding:9px 2px;border-bottom:1px solid var(--line);}
.stats .srow:last-child{border-bottom:0;}
.stats .sk{font-size:12.5px;color:var(--sub);}
.stats .sv{font-size:16px;font-weight:800;letter-spacing:-.01em;}
.stats .sb{font-size:10.5px;color:var(--sub);display:block;text-align:right;margin-top:1px;}
.up{color:var(--up);} .dn{color:var(--dn);}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{padding:8px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left;}
th{color:var(--sub);font-weight:600;font-size:11.5px;}
.state{color:var(--sub);font-size:14px;padding:30px 4px;text-align:center;} .err{color:var(--up);}
.note{font-size:11.5px;color:var(--sub);margin-top:8px;line-height:1.5;}
.aibtn{float:right;font:600 12px/1 -apple-system;color:#fff;background:linear-gradient(135deg,var(--accent),var(--violet));
  border:none;border-radius:100px;padding:7px 14px;cursor:pointer;transition:transform .15s,opacity .15s;}
.aibtn:hover{transform:translateY(-1px);} .aibtn:disabled{opacity:.55;cursor:default;transform:none;}
.aiout{margin-top:12px;font-size:13.5px;line-height:1.72;color:var(--ink);white-space:normal;
  background:var(--row);border:1px solid var(--line);border-radius:12px;padding:13px 15px;max-height:340px;overflow:auto;}
.ai-cur{display:inline-block;width:7px;height:15px;margin-left:2px;background:var(--accent);border-radius:1px;vertical-align:-2px;animation:aiBlink 1s steps(2) infinite;}
@keyframes aiBlink{50%{opacity:0;}}
.ai-typing{display:inline-flex;gap:5px;} .ai-typing i{width:7px;height:7px;border-radius:50%;background:var(--accent);opacity:.4;animation:aiPulse 1.2s ease-in-out infinite;}
.ai-typing i:nth-child(2){animation-delay:.18s;} .ai-typing i:nth-child(3){animation-delay:.36s;}
@keyframes aiPulse{0%,100%{opacity:.3;transform:scale(.8);}50%{opacity:1;transform:scale(1);}}
@media (prefers-reduced-motion:reduce){.ai-cur,.ai-typing i{animation:none;}}
</style></head><body>
<section class="panel" id="formPanel">
  <h2>🧪 백테스터 <span class="sub" style="font-weight:500;">국내 일봉 룰 전략 검증 · 신호=종가, 체결=다음 봉 · 로컬 연산</span></h2>
  <div class="form" style="margin-top:12px;">
    <div class="fld f-code"><label>종목 (이름·코드)</label><input id="code" placeholder="삼성전자" autocomplete="off">
      <div class="sgg" id="sgg"></div></div>
    <div class="fld f-strat"><label>전략</label><select id="strat">
      <option value="sma">SMA 골든크로스</option><option value="mom">N일 모멘텀</option>
      <option value="rsi">RSI 평균회귀</option><option value="macd">MACD 시그널 교차</option>
      <option value="boll">볼린저밴드 평균회귀</option><option value="bh">매수 보유</option></select></div>
    <span id="prm"></span>
    <div class="fld f-days"><label>기간</label><select id="days">
      <option value="500">2년</option><option value="1250" selected>5년</option><option value="2400">10년</option></select></div>
    <div class="fld f-num"><label>편도 비용(bp)</label><input id="cost" type="number" value="25"></div>
    <button class="run" id="run">백테스트 실행</button>
  </div>
</section>
<div id="out"><div class="panel"><div class="state">종목을 선택하고 백테스트를 실행해 보세요.</div></div></div>
<script>
var $=function(s){return document.querySelector(s);};
var selCode='', selName='', res=null;
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt){
  document.documentElement.classList.toggle('dark',e.data.kmkt==='dark');if(res)draw();}});
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fmt(n,d){return (Number(n)||0).toLocaleString('en-US',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function pct(v){return (v>0?'+':'')+fmt(v)+'%';}
/* 종목 자동완성 */
var ci=$('#code'),sgg=$('#sgg'),tmr=null;
ci.addEventListener('input',function(){clearTimeout(tmr);var v=ci.value.trim();selCode='';
  if(!v){sgg.classList.remove('show');return;}
  tmr=setTimeout(function(){fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
    var items=(d||[]).slice(0,7);
    if(!items.length){sgg.classList.remove('show');return;}
    sgg.innerHTML=items.map(function(it){return '<div class="it" data-c="'+esc(it.code)+'" data-n="'+esc(it.name)+'">'+
      '<span>'+esc(it.name)+'</span><span class="c">'+esc(it.code)+'</span></div>';}).join('');
    sgg.classList.add('show');});},160);});
sgg.addEventListener('mousedown',function(e){var it=e.target.closest('.it');if(!it)return;
  selCode=it.dataset.c;selName=it.dataset.n;ci.value=it.dataset.n+' ('+it.dataset.c+')';sgg.classList.remove('show');});
document.addEventListener('click',function(e){if(!sgg.contains(e.target)&&e.target!==ci)sgg.classList.remove('show');});
/* 전략별 파라미터 */
var PRMS={sma:[['fast','단기 SMA',20],['slow','장기 SMA',60]],
          mom:[['lookback','모멘텀 일수',60]],
          rsi:[['period','RSI 기간',14],['buy','매수 임계',30],['sell','청산 임계',70]],
          macd:[['fast','단기 EMA',12],['slow','장기 EMA',26],['signal','시그널',9]],
          boll:[['period','기간',20],['k','표준편차 배수',2]],bh:[]};
function renderPrm(){var s=$('#strat').value;
  $('#prm').innerHTML=PRMS[s].map(function(p){return '<div class="fld f-num"><label>'+p[1]+'</label>'+
    '<input id="p_'+p[0]+'" type="number" value="'+p[2]+'"></div>';}).join('');}
$('#strat').addEventListener('change',renderPrm);renderPrm();
/* 실행 */
$('#run').addEventListener('click',run);
ci.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();run();}});
function run(){
  var code=selCode||(ci.value.match(/\d{6}/)||[''])[0];
  if(!code){$('#out').innerHTML='<div class="panel"><div class="state err">종목을 선택해 주세요 (이름 검색 후 클릭).</div></div>';return;}
  var s=$('#strat').value,qs='code='+code+'&strat='+s+'&days='+$('#days').value+'&cost='+($('#cost').value||25);
  PRMS[s].forEach(function(p){var el=document.getElementById('p_'+p[0]);if(el&&el.value)qs+='&'+p[0]+'='+el.value;});
  $('#run').disabled=true;
  $('#out').innerHTML='<div class="panel"><div class="kmkt-load" role="status" aria-live="polite"><span class="ring" aria-hidden="true"></span><span class="tx">백테스트 계산 중… (일봉 수집 + NumPy 시뮬레이션)</span></div></div>';
  fetch('/api/backtest?'+qs,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    $('#run').disabled=false;
    if(!d.ok){$('#out').innerHTML='<div class="panel"><div class="state err">'+esc(d.msg||'실패')+'</div></div>';return;}
    res=d;renderRes();
  }).catch(function(){$('#run').disabled=false;$('#out').innerHTML='<div class="panel"><div class="state err">네트워크 오류</div></div>';});
}
var STRAT_NM={sma:'SMA 골든크로스',mom:'N일 모멘텀',rsi:'RSI 평균회귀',macd:'MACD 시그널 교차',boll:'볼린저밴드 평균회귀',bh:'매수 보유'};
function srow(k,v,sub,cls){return '<div class="srow"><span class="sk">'+k+'</span><span><span class="sv '+(cls||'')+'">'+v+'</span>'+(sub?'<span class="sb">'+sub+'</span>':'')+'</span></div>';}
function renderRes(){
  var d=res,s=d.strategy,b=d.bench,p2=d.pro||{},rsiOn=(d.ind&&d.ind.type==='rsi');
  var legend='<div class="chiprow">'+
    (d.ind.type==='sma'?('<span><i style="background:var(--maf)"></i>MA'+d.ind.fast+'</span><span><i style="background:var(--mas)"></i>MA'+d.ind.slow+'</span>'):'')+
    '<span><span class="tri" style="color:var(--buy)">▲</span> 매수</span>'+
    '<span><span class="tri" style="color:var(--sell)">▼</span> 매도</span>'+
    (rsiOn?'<span>RSI '+d.ind.period+' (매수&lt;'+d.ind.buy+' · 청산&gt;'+d.ind.sell+')</span>':'')+'</div>';
  var h=
   '<section class="panel"><div class="statbar">'+
     '<div><div class="nm">'+esc(selName||d.name||d.code)+' <span class="stag">'+esc(STRAT_NM[d.ind.type]||'')+'</span></div>'+
       '<div class="meta">'+esc(d.start)+' ~ '+esc(d.end)+' · '+d.n+'봉 · 거래 '+d.trades_n+'회 · 승률 '+fmt(d.winrate,1)+'%</div></div>'+
     '<div class="ret"><div class="l">전략 총수익률</div><div class="v '+(s.total>0?'up':'dn')+'">'+pct(s.total)+'</div>'+
       '<div class="l">매수보유 '+pct(b.total)+'</div></div>'+
   '</div></section>'+
   '<div class="grid">'+
     '<div>'+
       '<section class="panel"><h3>🕯️ 가격 차트 · 전략 신호</h3>'+legend+
         '<canvas id="cvMain"></canvas></section>'+
       '<section class="panel"><h3>📈 자본 곡선 (시작=1.0)</h3>'+
         '<div class="chiprow"><span><i style="background:var(--accent)"></i>전략</span><span><i style="background:var(--sub)"></i>매수보유</span></div>'+
         '<canvas id="cvEq"></canvas></section>'+
     '</div>'+
     '<div class="rsz" id="rsz" title="드래그하여 패널 너비 조절"></div>'+
     '<div>'+
       '<section class="panel stats"><h3>📊 전략 성과</h3>'+
         srow('총수익률',pct(s.total),'매수보유 '+pct(b.total),s.total>0?'up':'dn')+
         srow('CAGR',pct(s.cagr),'매수보유 '+pct(b.cagr),s.cagr>0?'up':'dn')+
         srow('MDD',fmt(s.mdd)+'%','매수보유 '+fmt(b.mdd)+'%','dn')+
         srow('샤프',fmt(s.sharpe),'매수보유 '+fmt(b.sharpe))+
         srow('Calmar',p2.calmar==null?'—':fmt(p2.calmar),'CAGR/MDD')+
         srow('손익비(Payoff)',p2.payoff==null?'—':fmt(p2.payoff),'평균이익/평균손실')+
         srow('Profit Factor',p2.profit_factor==null?'—':fmt(p2.profit_factor),'총이익/총손실')+
         srow('변동성(연)',fmt(s.vol)+'%','매수보유 '+fmt(b.vol)+'%')+
         srow('거래 횟수',d.trades_n+'회','승률 '+fmt(d.winrate,1)+'%')+
         srow('평균손익','<span class="up">'+pct(p2.avg_win)+'</span> / <span class="dn">'+pct(p2.avg_loss)+'</span>','승/패 평균')+
         srow('최대 연속손실',p2.max_consec_loss+'회','최고 '+(p2.best==null?'—':pct(p2.best))+' · 최저 '+(p2.worst==null?'—':pct(p2.worst)),p2.max_consec_loss>=4?'dn':'')+
         srow('시장 노출',fmt(d.exposure,1)+'%','현금 '+fmt(100-d.exposure,1)+'%')+
       '</section>'+
     '</div>'+
   '</div>'+
   '<section class="panel"><h3>🧾 거래 내역 <span class="sub" style="font-weight:500;">('+d.trades.length+'건 · 최근 20건)</span></h3>'+
     (d.trades.length?'<table class="trades"><thead><tr><th>#</th><th>진입일</th><th>청산일</th><th>수익률</th><th>결과</th></tr></thead><tbody>'+
       d.trades.slice().reverse().map(function(t,i){var c=t.ret>0?'up':t.ret<0?'dn':'';
         return '<tr><td>'+(d.trades.length-i)+'</td><td>'+esc(t.in)+'</td><td>'+esc(t.out)+'</td>'+
           '<td class="'+c+'">'+pct(t.ret)+'</td><td class="'+c+'">'+(t.ret>0?'이익':t.ret<0?'손실':'—')+'</td></tr>';}).join('')+
       '</tbody></table>':'<div class="state">완결된 거래가 없습니다 (상시 보유 또는 무거래).</div>')+
   '</section>'+
   '<section class="panel" id="aiPanel"><h3>🤖 AI 해석 <span class="sub" style="font-weight:500;">로컬 LLM이 결과를 쉽게 풀어 설명합니다</span>'+
     '<button class="aibtn" id="aiBtn" type="button">AI 해석 보기</button></h3>'+
     '<div id="aiOut" class="aiout" style="display:none;"></div></section>'+
   '<div class="note">편도 비용 반영 · 신호 종가 → 다음 봉 체결(룩어헤드 방지) · 과거 성과는 미래 수익을 보장하지 않습니다.</div>';
  $('#out').innerHTML=h;draw();setupResizer();
  var ab=document.getElementById('aiBtn');if(ab)ab.addEventListener('click',aiExplain);
}
/* ── AI 해석 (로컬 LLM · 작업4) — 결과 수치를 초보 투자자용 자연어로 ── */
function aiExplain(){
  if(!res)return;
  var d=res,s=d.strategy||{},b=d.bench||{},p2=d.pro||{};
  var lines=[
    '종목: '+(selName||d.name||d.code)+' ('+d.code+')',
    '전략: '+(STRAT_NM[d.ind.type]||d.ind.type),
    '기간: '+d.start+' ~ '+d.end+' ('+d.n+'거래일)',
    '전략 총수익률: '+pct(s.total)+' / 매수보유(벤치마크): '+pct(b.total),
    'CAGR(연복리): '+pct(s.cagr)+' / 벤치 '+pct(b.cagr),
    'MDD(최대낙폭): '+fmt(s.mdd)+'% / 벤치 '+fmt(b.mdd)+'%',
    '샤프지수: '+fmt(s.sharpe)+' / 벤치 '+fmt(b.sharpe),
    '연변동성: '+fmt(s.vol)+'%',
    'Calmar: '+(p2.calmar==null?'—':fmt(p2.calmar))+' / 손익비: '+(p2.payoff==null?'—':fmt(p2.payoff))+' / Profit Factor: '+(p2.profit_factor==null?'—':fmt(p2.profit_factor)),
    '거래 '+d.trades_n+'회 · 승률 '+fmt(d.winrate,1)+'% · 시장노출 '+fmt(d.exposure,1)+'%',
    '최대 연속손실: '+p2.max_consec_loss+'회'
  ].join('\n');
  var btn=document.getElementById('aiBtn');if(btn){btn.disabled=true;btn.textContent='해석 생성 중…';}
  streamLLM({prompt:lines,mode:'backtest'},'aiOut',function(){if(btn){btn.disabled=false;btn.textContent='다시 해석';}});
}
/* SSE 스트리밍 공용 헬퍼 — /api/llm_commentary 결과를 outId div 에 타이핑 */
function streamLLM(body,outId,onDone){
  body.max_tokens = window._llmMaxTokens || 1200;
  try{Object.assign(body,(window.kmktAiProv?window.kmktAiProv():{}));}catch(e){}   // 로컬/Gemini 선택 반영
  var out=document.getElementById(outId);if(!out)return;
  out.style.display='block';
  out.innerHTML='<span class="ai-typing"><i></i><i></i><i></i></span>';
  fetch('/api/llm_commentary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(async function(r){
      out.innerHTML='<div class="ai-think" id="'+outId+'_k" style="display:none;font-size:11.5px;opacity:.62;'
        +'border-left:2px solid var(--line,rgba(255,255,255,.14));padding:4px 9px;margin:0 0 9px;max-height:150px;overflow:auto;'
        +'white-space:pre-wrap;line-height:1.5;">💭 <b style="opacity:.85;">추론</b><br><span id="'+outId+'_kt"></span></div>'
        +'<span id="'+outId+'_t"></span><span class="ai-cur"></span>';
      var tc=document.getElementById(outId+'_t'),kc=document.getElementById(outId+'_k'),kt=document.getElementById(outId+'_kt');
      var reader=r.body.getReader(),dec=new TextDecoder('utf-8');
      var buf='';function e2(s){return s.replace(/</g,'&lt;').replace(/\n/g,'<br>');}
      var ans='',md=window.kmktMd||function(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');};
      tc.className='kmkt-md';
      while(true){var rr=await reader.read();if(rr.done)break;
        buf+=dec.decode(rr.value,{stream:true});var ls=buf.split('\n');buf=ls.pop();
        for(var i=0;i<ls.length;i++){var ln=ls[i];if(ln.indexOf('data: ')===0){
          try{var dj=JSON.parse(ln.substring(6));if(dj.text){
            if(dj.kind==='reasoning'){kc.style.display='block';kt.insertAdjacentHTML('beforeend',e2(dj.text));}
            else{ans+=dj.text;tc.innerHTML=md(ans);}
            out.scrollTop=out.scrollHeight;}}catch(e){}}}
      }
      var cur=out.querySelector('.ai-cur');if(cur)cur.remove();
      if(onDone)onDone();
    }).catch(function(e){out.innerHTML='<span style="color:var(--sell,#FF3B30)">AI 연결 실패: '+e.message+'</span>';if(onDone)onDone();});
}
/* 우측 성과 패널 너비 드래그 조절 (토스식) */
function setupResizer(){var rsz=document.getElementById('rsz'),grid=rsz&&rsz.closest('.grid');if(!rsz||!grid)return;
  var drag=false,sx=0,sw=0;
  function cur(){var v=getComputedStyle(grid).getPropertyValue('--statw').trim();return parseFloat(v)||256;}
  rsz.addEventListener('mousedown',function(e){drag=true;sx=e.clientX;sw=cur();rsz.classList.add('drag');
    document.body.style.cursor='col-resize';document.body.style.userSelect='none';e.preventDefault();});
  window.addEventListener('mousemove',function(e){if(!drag)return;
    var w=Math.max(200,Math.min(440,sw-(e.clientX-sx)));grid.style.setProperty('--statw',w+'px');});
  window.addEventListener('mouseup',function(){if(!drag)return;drag=false;rsz.classList.remove('drag');
    document.body.style.cursor='';document.body.style.userSelect='';try{draw();}catch(e){}});
}
/* ── 가격 캔들 + MA + 매수/매도 마커 (+ RSI 서브패널) ── */
function draw(){drawCandle();drawEquity();}
function drawCandle(){
  var cv=document.getElementById('cvMain');if(!cv||!res||!res.bars)return;
  var dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=420;cv.width=W*dpr;cv.height=H*dpr;
  var x=cv.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,W,H);
  var bars=res.bars,ind=res.ind,rsiOn=(ind.type==='rsi');
  var cs=getComputedStyle(document.documentElement);
  var up=cs.getPropertyValue('--cand-up').trim()||'#ff5a52',dn=cs.getPropertyValue('--cand-dn').trim()||'#5aadff';
  var sub=cs.getPropertyValue('--sub').trim()||'#8a97b5',ln=cs.getPropertyValue('--grid-ln').trim()||'rgba(255,255,255,.07)';
  var maf=cs.getPropertyValue('--maf').trim()||'#f5a623',mas=cs.getPropertyValue('--mas').trim()||'#36c6ff';
  var buyC=cs.getPropertyValue('--buy').trim()||'#2ee6a6',sellC=cs.getPropertyValue('--sell').trim()||'#ffb020';
  var padT=10,padB=22,padR=58,rsiH=rsiOn?96:0,gap=rsiOn?10:0;
  var priceH=H-padT-padB-rsiH-gap,plotW=W-padR;
  var hs=[],ls=[];bars.forEach(function(r){hs.push(r.h);ls.push(r.l);if(r.mf!=null){hs.push(r.mf);ls.push(r.mf);}if(r.ms!=null){hs.push(r.ms);ls.push(r.ms);}});
  var hi=Math.max.apply(null,hs),lo=Math.min.apply(null,ls);if(hi<=lo)hi=lo+1;
  function Y(p){return padT+(hi-p)/(hi-lo)*priceH;}
  var n=bars.length,bw=plotW/n,cw=Math.max(1,bw*0.6);
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.lineWidth=.5;x.textAlign='left';
  for(var g=0;g<=4;g++){var pv=lo+(hi-lo)*g/4,gy=Y(pv);x.beginPath();x.moveTo(0,gy);x.lineTo(plotW,gy);x.stroke();x.fillText(fmt(pv,0),plotW+6,gy+3);}
  for(var i=0;i<n;i++){var r=bars[i],cx=i*bw+bw/2,rise=r.c>=r.o,col=rise?up:dn;
    x.strokeStyle=col;x.fillStyle=col;x.lineWidth=1;
    x.beginPath();x.moveTo(cx,Y(r.h));x.lineTo(cx,Y(r.l));x.stroke();
    var y1=Y(Math.max(r.o,r.c)),y2=Y(Math.min(r.o,r.c));x.fillRect(cx-cw/2,y1,cw,Math.max(1,y2-y1));}
  // MA lines (sma 전략)
  function maLine(key,col){x.strokeStyle=col;x.lineWidth=1.4;x.beginPath();var st=false;
    for(var i=0;i<n;i++){var v=bars[i][key];if(v==null)continue;var px=i*bw+bw/2,py=Y(v);if(!st){x.moveTo(px,py);st=true;}else x.lineTo(px,py);}x.stroke();}
  if(ind.type==='sma'){maLine('mf',maf);maLine('ms',mas);}
  // 매수/매도 마커
  (res.markers||[]).forEach(function(m){var cx=m.b*bw+bw/2;
    if(m.side==='buy'){var py=Y(bars[m.b]?bars[m.b].l:m.px)+12;x.fillStyle=buyC;
      x.beginPath();x.moveTo(cx,py-7);x.lineTo(cx-5,py+2);x.lineTo(cx+5,py+2);x.closePath();x.fill();}
    else{var py=Y(bars[m.b]?bars[m.b].h:m.px)-12;x.fillStyle=sellC;
      x.beginPath();x.moveTo(cx,py+7);x.lineTo(cx-5,py-2);x.lineTo(cx+5,py-2);x.closePath();x.fill();}});
  // RSI 서브패널
  if(rsiOn){var ry=padT+priceH+gap;
    x.strokeStyle=ln;x.beginPath();x.moveTo(0,ry);x.lineTo(plotW,ry);x.stroke();
    function RY(v){return ry+(100-v)/100*rsiH;}
    [ind.sell,ind.buy].forEach(function(lv,k){x.strokeStyle=k?'rgba(90,173,255,.5)':'rgba(255,90,82,.5)';x.setLineDash([4,3]);
      x.beginPath();x.moveTo(0,RY(lv));x.lineTo(plotW,RY(lv));x.stroke();x.setLineDash([]);
      x.fillStyle=sub;x.fillText(lv+'',plotW+6,RY(lv)+3);});
    x.strokeStyle='#9b6bff';x.lineWidth=1.3;x.beginPath();var st=false;
    for(var i=0;i<n;i++){var v=bars[i].rsi;if(v==null)continue;var px=i*bw+bw/2,py=RY(v);if(!st){x.moveTo(px,py);st=true;}else x.lineTo(px,py);}x.stroke();
    x.fillStyle=sub;x.fillText('RSI',4,ry+12);}
  // 날짜 라벨
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(n/2),n-1].forEach(function(ix){var r=bars[ix];if(!r)return;
    x.fillText(r.d,Math.min(plotW-32,Math.max(32,ix*bw+bw/2)),H-6);});
}
function drawEquity(){var cv=document.getElementById('cvEq');if(!cv||!res||!res.curve)return;
  var dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=200;cv.width=W*dpr;cv.height=H*dpr;
  var x=cv.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,W,H);
  var ecs=getComputedStyle(document.documentElement);
  var sub=ecs.getPropertyValue('--sub').trim()||'#8a97b5',ln=ecs.getPropertyValue('--grid-ln').trim()||'rgba(255,255,255,.07)';
  var stratC=ecs.getPropertyValue('--accent').trim()||'#36c6ff';
  var C=res.curve;if(!C.length)return;
  var vs=[];C.forEach(function(p){vs.push(p.s,p.b);});
  var hi=Math.max.apply(null,vs),lo=Math.min.apply(null,vs);if(hi<=lo)hi=lo+1e-6;
  var padT=10,padB=20,padR=52,pw=W-padR,ph=H-padT-padB;
  function X(i){return i/(C.length-1)*pw;}function Y(v){return padT+(hi-v)/(hi-lo)*ph;}
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.lineWidth=.5;x.textAlign='left';
  for(var g=0;g<=4;g++){var v=lo+(hi-lo)*g/4,gy=Y(v);x.beginPath();x.moveTo(0,gy);x.lineTo(pw,gy);x.stroke();x.fillText(v.toFixed(2),pw+6,gy+3);}
  function line(key,col,w){x.strokeStyle=col;x.lineWidth=w;x.beginPath();
    C.forEach(function(p,i){var px=X(i),py=Y(p[key]);if(i)x.lineTo(px,py);else x.moveTo(px,py);});x.stroke();}
  line('b',sub,1.2);line('s',stratC,2);
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(C.length/2),C.length-1].forEach(function(i){var p=C[i];if(p)x.fillText(p.d,Math.min(pw-34,Math.max(34,X(i))),H-5);});
}
window.addEventListener('resize',draw);
</script></body></html>
"""

_OVERSEAS_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="overseas"><head><meta charset="utf-8">
<title>해외주식</title><link rel="icon" href="/favicon.ico">
<script src="/plotly.js"></script>
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{
  --bg:#f0f1f5;
  --card:rgba(255,255,255,.92);
  --ink:#1d1d1f;
  --sub:rgba(60,60,67,.56);
  --line:rgba(60,60,67,.11);
  --row:rgba(10,132,255,.05);
  --up:#FF3B30;
  --dn:#2E75B6;
  --accent:#007AFF;
  --sys-blue:#007AFF;
  --sys-indigo:#5856D6;
  --mat-card:rgba(255,255,255,.72);
  --mat-bar:rgba(255,255,255,.6);
  --g-blur:saturate(180%) blur(20px);
  --g-edge:inset 0 1px 0 rgba(255,255,255,.6), inset 0 -1px 3px rgba(0,0,0,.04);
  --g-line:rgba(60,60,67,.12);
  --hero-bg-up:#FF3B30;
  --hero-bg-dn:#2E75B6;
  --ease:cubic-bezier(.32,.72,0,1);
}
html.dark{
  --bg:#0b0f1a;
  --card:rgba(24,26,36,.88);
  --ink:#eef3ff;
  --sub:#8a97b5;
  --line:rgba(255,255,255,.09);
  --row:rgba(90,166,255,.08);
  --up:#FF453A;
  --dn:#64B5FF;
  --accent:#0A84FF;
  --sys-blue:#0A84FF;
  --sys-indigo:#5E5CE6;
  --mat-card:rgba(40,40,46,.64);
  --mat-bar:rgba(26,26,31,.55);
  --g-line:rgba(255,255,255,.10);
  --g-edge:inset 0 1px 0 rgba(255,255,255,.10), inset 0 -1px 3px rgba(0,0,0,.3);
  --hero-bg-up:#c0241a;
  --hero-bg-dn:#144fa0;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Roboto","Helvetica Neue","Apple SD Gothic Neo",sans-serif;
  background:radial-gradient(60% 50% at 10% -2%, rgba(150,190,255,.20), transparent 60%),
             radial-gradient(55% 50% at 95% 2%, rgba(255,180,220,.16), transparent 60%), var(--bg) !important;
  background-attachment:fixed;
  background-repeat:no-repeat;
  background-size:cover;
  min-height:100vh;
  color:var(--ink);
  -webkit-font-smoothing:antialiased;
  font-variant-numeric:tabular-nums;
}
html.dark body{
  background:radial-gradient(60% 50% at 10% -2%, rgba(60,90,200,.22), transparent 60%),
             radial-gradient(55% 50% at 95% 2%, rgba(140,60,160,.16), transparent 60%), var(--bg) !important;
  background-repeat:no-repeat;
  background-size:cover;
  min-height:100vh;
}

/* ── 헤더 & 네비게이션 ── */
header{
  background:var(--mat-bar) !important;
  -webkit-backdrop-filter:var(--g-blur);
  backdrop-filter:var(--g-blur);
  border-bottom:.5px solid var(--g-line) !important;
  box-shadow:var(--g-edge);
  padding:20px 28px;
}
header h1{
  margin:0;
  font-size:22px;
  font-weight:800;
  color:var(--ink);
  display:flex;
  align-items:center;
  gap:10px;
}
header .sub{
  margin-top:6px;
  font-size:13px;
  color:var(--sub);
}
.hdr-refresh{
  border:0;
  background:transparent;
  color:#9aa3b2;
  border-radius:8px;
  width:30px;
  height:30px;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:0;
  transition:background .15s,color .15s,transform .3s;
  flex:none;
}
.hdr-refresh svg{
  width:17px;
  height:17px;
  display:block;
}
.hdr-refresh:hover{
  background:rgba(31,56,100,.09);
  color:var(--accent);
  transform:rotate(180deg);
}

nav{
  position:sticky;
  top:0;
  z-index:100;
  background:var(--mat-bar) !important;
  -webkit-backdrop-filter:var(--g-blur);
  backdrop-filter:var(--g-blur);
  border-bottom:1px solid var(--g-line);
  padding:0 16px;
  display:flex;
  gap:4px;
  overflow-x:auto;
}
.tab-btn{
  border:0;
  background:none;
  padding:14px 18px;
  font-size:14px;
  font-weight:600;
  color:var(--sub);
  cursor:pointer;
  border-bottom:3px solid transparent;
  white-space:nowrap;
  transition:color 0.2s;
}
.tab-btn:hover{
  color:var(--accent);
}
.tab-btn.active{
  color:var(--ink);
  border-bottom-color:var(--accent);
}
.pane{
  display:none;
}
.pane.active{
  display:block;
  animation:ovPaneIn .4s cubic-bezier(.16,1,.3,1) both;
}
.pane-content{
  padding:20px 20px 30px;
  max-width:1200px;
  margin:0 auto;
}
.pane-full{
  padding:0;
  width:100%;
}
@keyframes ovPaneIn{
  from{opacity:0;transform:translateY(8px);}
  to{opacity:1;transform:none;}
}

/* ── 기간 수익률 (국내 스타일 테이블) ── */
.tbl-scroll{overflow-x:auto;border:1px solid var(--g-line);border-radius:10px;background:var(--mat-card);-webkit-overflow-scrolling:touch;}
.mi-table{width:100%;border-collapse:collapse;font-size:14px;text-align:right;}
.mi-table th{background:rgba(0,0,0,0.02);padding:10px 14px;border-bottom:1px solid var(--g-line);font-size:13px;color:var(--sub);font-weight:600;white-space:nowrap;}
html.dark .mi-table th{background:rgba(255,255,255,0.03);}
.mi-table td{padding:12px 14px;border-bottom:1px solid var(--g-line);color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap;}
.mi-table.bold-first td:first-child{font-weight:800;font-size:15px;text-align:left;color:var(--ink);}
.t-up{color:var(--up) !important;font-weight:700;}
.t-down{color:var(--dn) !important;font-weight:700;}

/* 현재가 히어로 (국내 주식 스타일 일치화 & 텍스트 흰색 강제) */
.price-hero{border-radius:14px;padding:20px 26px;margin-bottom:18px;color:#fff !important;
 box-shadow:0 2px 8px rgba(20,40,80,.12);position:relative;overflow:hidden;}
.price-hero *{color:#fff !important;}
.price-hero::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 20% 40%,rgba(255,255,255,.12) 0%,transparent 60%);pointer-events:none;}
.price-hero.up{background:linear-gradient(135deg,#c0392b,#e85c4a);}
.price-hero.down{background:linear-gradient(135deg,#1f5fa8,#3a8ddd);}
.price-hero.flat{background:linear-gradient(135deg,#5b6b86,#8a97ad);}
.price-hero .ph-top{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:6px;}
.price-hero .ph-name{font-size:15px;font-weight:700;opacity:.92;}
.price-hero .ph-chg{font-size:18px;font-weight:800;opacity:.98;}
.price-hero .ph-price{font-size:44px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;position:relative;display:inline-block;}
/* rolling cells */
.price-hero .ph-price .rt-ch{display:inline-block;position:relative;overflow:hidden;vertical-align:bottom;}
.price-hero .ph-price .rt-col{display:flex;flex-direction:column;}
.price-hero .ph-meta{font-size:12px;opacity:.82;margin-top:8px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
.price-hero .ph-meta span{color:#fff;}
.badge{font-size:10.5px;font-weight:700;padding:2px 6px;border-radius:5px;}
.badge.open{background:#FFD60A;color:#000;}
.badge.pre{background:#FF9F0A;color:#fff;}
.badge.closed{background:rgba(255,255,255,.15);color:#fff;}
.badge.holiday{background:rgba(255,255,255,.1);color:rgba(255,255,255,.6);}
@keyframes heroBlink{0%,100%{opacity:1;}50%{opacity:.55;}}

/* ── 국내 주식 etf-head 스타일 완벽 이식 ── */
.etf-head{padding:24px 28px !important;border-radius:16px;background:var(--mat-card) !important;
 border:.5px solid var(--g-line) !important;box-shadow:var(--g-edge), 0 8px 26px rgba(20,30,70,.08) !important;margin-bottom:18px;}
.eh-top{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:12.5px;color:var(--sub);}
.eh-code{font-weight:700;color:var(--accent);background:rgba(0,122,255,.08);padding:2px 8px;border-radius:6px;font-variant-numeric:tabular-nums;}
html.dark .eh-code{background:rgba(10,132,255,.15);}
.eh-tag{background:rgba(90,166,255,.08);color:var(--sub);padding:2px 8px;border-radius:6px;font-weight:600;}
.eh-asof{margin-left:auto;font-size:11.5px;color:var(--sub);}
.eh-name{font-size:24px;font-weight:800;color:var(--ink);margin:0 0 16px;letter-spacing:-.02em;}
.eh-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:18px;}
.eh-kpi{background:var(--mat-card) !important;border:1px solid var(--g-line) !important;border-radius:12px;padding:14px 18px;
 min-width:0;overflow:hidden;
 box-shadow:inset 0 1px 0 rgba(255,255,255,.4), 0 4px 12px rgba(20,40,80,.04);transition:transform .2s ease;}
html.dark .eh-kpi{box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 4px 12px rgba(0,0,0,.15);}
.eh-kpi:hover{transform:translateY(-1px);}
.eh-kpi .k-label{font-size:13px;color:var(--sub);font-weight:600;margin-bottom:6px;}
.eh-kpi .k-val{font-size:26px;font-weight:800;color:var(--ink);line-height:1.1;font-variant-numeric:tabular-nums;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}
.eh-kpi .k-val.k-up{color:var(--up) !important;}
.eh-kpi .k-val.k-down{color:var(--dn) !important;}
.eh-kpi .k-unit{font-size:14px;font-weight:600;color:var(--sub);margin-left:2px;}
.eh-kpi .k-sub{font-size:12px;font-weight:700;margin-top:6px;color:var(--sub);}
.eh-kpi .k-sub.k-up{color:var(--up) !important;}
.eh-kpi .k-sub.k-down{color:var(--dn) !important;}
.eh-info{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:2px 30px;
 border-top:1px solid var(--g-line);padding-top:14px;}
.eh-info .ei{display:flex;gap:14px;font-size:14px;padding:9px 2px;border-bottom:1px solid var(--line);}
.eh-info .ei-l{color:var(--sub);min-width:90px;font-weight:600;}
.eh-info .ei-v{color:var(--ink);font-weight:700;overflow-wrap:anywhere;}

/* ── 카드 공통 ── */
.card{background:var(--mat-card);-webkit-backdrop-filter:var(--g-blur);
 backdrop-filter:var(--g-blur);border:.5px solid var(--g-line);border-radius:16px;
 padding:18px 20px;box-shadow:var(--g-edge), 0 8px 26px rgba(20,30,70,.08);margin-bottom:14px;}
h3{font-size:12.5px;font-weight:700;letter-spacing:-.01em;margin-bottom:10px;}
.card-title{margin:0 0 12px;font-size:15px;color:var(--ink);font-weight:700;}
.note{font-size:11.5px;color:var(--sub);}
.state{color:var(--sub);font-size:14px;padding:20px 16px;} .err{color:var(--up);}

/* ── 기타 스타일 공용 ── */
.up{color:var(--up);} .dn{color:var(--dn);}

/* ── 차트 ── */
.seg{display:inline-flex;border:.5px solid var(--line);border-radius:9px;overflow:hidden;}
.seg button{background:transparent;border:0;color:var(--sub);font:inherit;font-size:12px;padding:5px 12px;cursor:pointer;}
.seg button.on{background:var(--accent);color:#fff;}

/* ── 뉴스 ── */
.news{max-height:400px;overflow-y:auto;padding-right:4px;}
.news .it{display:flex;gap:10px;align-items:baseline;padding:9px 2px;border-bottom:.5px solid var(--line);font-size:13.5px;}
.news .it:last-child{border-bottom:0;}
.news .t{font-weight:500;min-width:0;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;flex:1;}
.news .meta{margin-left:auto;flex:none;font-size:11px;color:var(--sub);white-space:nowrap;}

/* ── 라이트 FX (국내 리포트와 동일 감성: 카드 등장·hover 3D 틸트) ── */
.card{transition:box-shadow .22s ease,transform .18s var(--ease),background-color .55s ease;
 will-change:transform;backface-visibility:hidden;}
.card:hover{box-shadow:var(--g-edge), 0 16px 40px rgba(31,56,100,.14);transform:perspective(1100px) translateY(-2px);}
html.dark .card:hover{box-shadow:var(--g-edge), 0 16px 40px rgba(0,0,0,.45);}
.card.fx-in{animation:ovCardIn .55s cubic-bezier(.16,1,.3,1) both;}
@keyframes ovCardIn{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}
@media(prefers-reduced-motion:reduce){.card{transition:none!important;}.card.fx-in{animation:none!important;}}

/* ── AI 코멘터리 모달 ── */
#ai-modal {
  display: flex; flex-direction: column;
  position: fixed; top: 60px; right: 20px; width: 340px;
  background: var(--mat-card);
  -webkit-backdrop-filter: var(--g-blur); backdrop-filter: var(--g-blur);
  padding: 20px; border-radius: 16px;
  box-shadow: var(--g-edge), 0 10px 40px rgba(0,0,0,0.2);
  z-index: 9999; border: 1px solid var(--g-line);
  opacity: 0; transform: translateY(12px) scale(0.98); pointer-events: none;
  transition: opacity .32s var(--ease), transform .32s var(--ease);
}
#ai-modal.show {
  opacity: 1; transform: none; pointer-events: auto;
}
.ai-loader { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 12px 0; }
.ai-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--sys-indigo, #5aa6ff);
  animation: aiBounce 1.4s infinite ease-in-out both;
}
.ai-dot:nth-child(1) { animation-delay: -0.32s; }
.ai-dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes aiBounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.ai-chunk {
  animation: aiChunkIn .15s ease-out forwards;
}
@keyframes aiChunkIn {
  from { opacity: 0; transform: translateY(2px); }
  to { opacity: 1; transform: none; }
}
.ai-cursor {
  display: inline-block; width: 6px; height: 14px;
  background: var(--sys-indigo, #5aa6ff);
  margin-left: 2px; vertical-align: middle;
  animation: aiBlink 1s step-start infinite;
}
@keyframes aiBlink { 50% { opacity: 0; } }

/* ── M4 분석 레이아웃 ── */
.m4-wrap{color:#fff;background:radial-gradient(ellipse at 50% -20%,#191535 0%,#090815 85%);border-radius:18px;padding:24px 20px;box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 10px 40px rgba(0,0,0,.35);border:1px solid #1f1b40;overflow:hidden;}
.m4-hero{text-align:center;margin-bottom:28px;}
.m4-hero h2{font-size:23px;font-weight:800;background:linear-gradient(135deg,#fff,#9ba4cc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:8px;}
.m4-hero p{font-size:12.5px;color:#8f9cd0;margin-top:6px;line-height:1.6;width:90%;margin-left:auto;margin-right:auto;}
.m4-chip{display:inline-block;font-size:10px;font-weight:700;color:#c69eff;background:rgba(198,158,255,.09);border:1px solid rgba(198,158,255,.24);padding:2px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:.05em;}
.m4-grid{display:grid;grid-template-columns:1fr;gap:20px;margin-top:10px;}
.m4-card{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.04);border-radius:14px;padding:16px 18px;box-shadow:inset 0 1px 0 rgba(255,255,255,.02);}
.m4-card h4{font-size:14px;font-weight:700;color:#c69eff;margin:0 0 12px;border-left:3px solid #7b3df0;padding-left:8px;}
.m4-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;}
.m4-m{background:rgba(255,255,255,.01);border-radius:10px;padding:10px 12px;border:1px solid rgba(255,255,255,.02);}
.m4-m .k{font-size:11px;color:#8f9cd0;}
.m4-m .v{font-size:18px;font-weight:800;color:#fff;margin-top:3px;font-variant-numeric:tabular-nums;}
.m4-m .s{font-size:9.5px;color:#6d7bb0;margin-top:3px;}
.m4-note{background:rgba(123,61,240,.06);border:1px solid rgba(123,61,240,.15);border-radius:14px;padding:14px 18px;font-size:13.5px;line-height:1.8;color:#d2d7f3;}
.m4-stage{min-height:260px;display:flex;align-items:center;justify-content:center;}
.m4-loader{text-align:center;display:flex;flex-direction:column;align-items:center;gap:14px;}
.m4-orb{width:64px;height:64px;border-radius:50%;background:radial-gradient(circle at 30% 30%,#b08eff,#532cc4);box-shadow:0 0 30px rgba(123,61,240,.8);animation:m4Pulse 2s ease-in-out infinite;}
@keyframes m4Pulse{0%,100%{transform:scale(1);box-shadow:0 0 20px rgba(123,61,240,.6);}50%{transform:scale(1.08);box-shadow:0 0 40px rgba(162,118,255,.9);}}
.m4-loader h3{font-size:15px;color:#fff;margin:0;}
.m4-loader p{font-size:11.5px;color:#6d7bb0;max-width:320px;line-height:1.5;margin:0;}
.m4-prog{width:min(460px,84%);height:9px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden;}
.m4-prog-fill{height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,#9b6bff,#36c6ff);
 transition:width .45s cubic-bezier(.22,.61,.36,1);box-shadow:0 0 14px rgba(123,61,240,.7);}
.m4-prog-row{display:flex;justify-content:space-between;align-items:center;width:min(460px,84%);
 font-size:12px;color:#9fb0e8;font-weight:600;font-variant-numeric:tabular-nums;}
@media (prefers-reduced-motion:reduce){.pane.active,.m4-hero,.m4-orb{animation:none!important;}}
</style></head>
<body>
<div id="state" class="state">해외 종목 정보를 불러오는 중…</div>
<div id="body" style="display:none;">

<!-- 헤더 -->
<header>
  <h1 style="display:flex;align-items:baseline;gap:8px;">
    <span id="sy" style="font-size:24px;font-weight:800;color:var(--ink);"></span>
    <span id="nm" style="font-size:16px;font-weight:600;color:var(--sub);"></span>
    <button class="hdr-refresh" onclick="location.reload()" title="새로고침 — 최신 데이터로 다시 조회" style="margin-left:4px;vertical-align:middle;align-self:center;">
      <svg viewBox="0 0 24 24" aria-hidden="true" style="width:17px;height:17px;display:block;">
        <path fill="currentColor" d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
      </svg>
    </button>
  </h1>
  <div class="sub" id="hdrSub"></div>
</header>

<!-- 탭 메뉴 -->
<nav>
  <button class="tab-btn active" onclick="miTab(0)">종목 개요</button>
  <button class="tab-btn" onclick="miTab(1)">기업 정보</button>
  <button class="tab-btn m4-tab-btn" id="m4-tab-btn" onclick="miTab(2)">🚀 M4 퀀트 분석</button>
  <button class="tab-btn" id="ai-tab-btn" style="color:var(--sys-indigo);font-weight:600;" onclick="startAI()">✨ AI 코멘터리</button>
</nav>

<!-- 탭 0: 종목 개요 -->
<div class="pane active" id="pane0">
  <div class="pane-content">
  <!-- 히어로 (국내 주식 UI 일치화) -->
  <div class="price-hero" id="hero">
    <div class="ph-top">
      <span class="ph-name" id="heroNm"></span>
      <span class="ph-chg" id="hChg"></span>
    </div>
    <div class="ph-price">
      <span id="hCcy" style="font-size:26px;font-weight:700;margin-right:6px;opacity:.88;vertical-align:baseline;"></span>
      <span class="h-px" id="hPx">—</span>
    </div>
    <div class="ph-meta">
      <span id="heroSy" style="font-weight:600;opacity:.88;"></span>
      <span class="badge" id="mktBadge" style="display:none;"></span>
      <span id="ex" style="opacity:.85;"></span>
      <span id="sec" style="display:none;opacity:.85;"></span>
      <span id="hKrw" style="opacity:.85;"></span>
      <span id="hMeta" style="opacity:.82;"></span>
      <span id="rtBadge" style="display:none;font-weight:700;color:#FFD60A;animation:heroBlink 2s ease-in-out infinite;">● 실시간</span>
    </div>
  </div>

  <!-- 상세 정보 통합 카드 (국내 주식 etf-head 완벽 이식) -->
  <section class="etf-head">
    <div class="eh-top">
      <span class="eh-code" id="ehCode"></span>
      <span class="eh-tag" id="ehEx"></span>
      <span class="eh-tag" id="ehSec" style="display:none;"></span>
      <span class="eh-asof" id="ehAsof"></span>
    </div>
    <h2 class="eh-name" id="ehName"></h2>
    
    <!-- KPI 4카드 -->
    <div class="eh-kpis">
      <div class="eh-kpi">
        <div class="k-label">현재가</div>
        <div class="k-val" id="kpiPrice">—</div>
        <div class="k-sub" id="kpiPriceSub">—</div>
      </div>
      <div class="eh-kpi">
        <div class="k-label">등락률</div>
        <div class="k-val" id="kpiRate">—</div>
        <div class="k-sub" id="kpiRateSub">—</div>
      </div>
      <div class="eh-kpi">
        <div class="k-label">시가총액</div>
        <div class="k-val" id="kpiMcap">—</div>
        <div class="k-sub" id="kpiMcapSub">—</div>
      </div>
      <div class="eh-kpi">
        <div class="k-label">거래량</div>
        <div class="k-val" id="kpiVol">—</div>
        <div class="k-sub" id="kpiVolSub">—</div>
      </div>
    </div>
    
    <!-- 상세 정보 그리드 ( border 없는 깔끔한 3열 정렬 ) -->
    <div class="eh-info" id="descTable"></div>
  </section>

  <!-- 가격 차트 (Plotly 기반 가로폭 100% 렌더링) -->
  <section class="card">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
      <h3 style="margin:0;">🕯️ 가격 차트</h3>
      <div class="seg" id="seg" style="margin-left:auto;">
        <button class="on">1주</button>
        <button>1개월</button>
        <button>3개월</button>
        <button>연초후</button>
        <button>1년</button>
        <button>3년</button>
        <button>5년</button>
      </div>
    </div>
    <div id="plotlyChart" style="width:100%;height:430px;min-height:360px;"></div>
    <div class="note" style="margin-top:8px;">이동평균선(MA5, MA20, MA60, MA120) · 하단 거래량 · 한국투자증권 KIS 해외시세</div>
  </section>

  <!-- 기간 수익률 -->
  <section class="card">
    <h3>📈 기간 수익률</h3>
    <div class="tiles" id="tiles"></div>
  </section>

  </div> <!-- pane-content -->

  <!-- 하단 풀스크린 영역 -->
  <div class="pane-full">
    <!-- AI 질문 위젯 -->
    <div style="max-width:1200px; margin:0 auto; padding: 0 20px;">
      __KMKT_ASK_WIDGET__
    </div>

    <!-- 해외 뉴스 (가로 100% 너비 및 하단 배치) -->
    <section class="card" style="border-radius:0; border-left:0; border-right:0; border-bottom:0; margin-bottom:0; padding:30px 4vw; background:var(--mat-bar); box-shadow:none;">
      <h3 style="max-width:1160px; margin:0 auto 12px;">📰 해외 뉴스</h3>
      <div class="news" id="news" style="max-height:none; max-width:1160px; margin:0 auto;">
        <div class="state" style="padding:8px 0;">불러오는 중…</div>
      </div>
    </section>
  </div>
</div>
</div>

<!-- 탭 1: 기업 정보 -->
<div class="pane" id="pane1">
  <div class="pane-content">
    <div id="ovProfile">
      <div class="state" style="text-align:center;">기업 요약 정보가 없습니다.</div>
    </div>
  </div>
</div>

<!-- 탭 2: M4 퀀트 분석 -->
<div class="pane" id="pane2">
  <div class="pane-content">
    <div id="m4QuantPane"></div>
  </div>
</div>

<!-- AI 코멘터리 모달 팝업 -->
<div id="ai-modal">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:1px solid var(--g-line);padding-bottom:8px;">
    <h3 style="margin:0;font-size:15px;color:var(--sys-indigo);">✨ AI 코멘터리 (Local)</h3>
    <button onclick="closeAI()" style="background:none;border:none;color:var(--ink);cursor:pointer;font-size:16px;padding:0;">✕</button>
  </div>
  <div id="ai-content" style="font-size:13.5px;line-height:1.65;max-height:400px;overflow-y:auto;color:var(--ink);"></div>
</div>

</div>

<script>
var $=function(s){return document.querySelector(s);};
var P=new URLSearchParams(location.search),
    symb=(P.get('symb')||'').toUpperCase(),
    excd=(P.get('excd')||'').toUpperCase(),
    kname=P.get('name')||'', gubn='0', info=null, rows=[],
    lastFx=0, pollTid=null, lastPxStr='', lastDir='', hoverIdx=-1, chartGeo=null;
var RM=(window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches);
var DUR=0.62, EASE='cubic-bezier(.16,1,.3,1)';

function setTheme(d){document.documentElement.classList.toggle('dark',!!d);draw();}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)setTheme(e.data.kmkt==='dark');});

function fmt(n,d){return (Number(n)||0).toLocaleString('en-US',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function fmtI(n){return (Number(n)||0).toLocaleString('en-US',{maximumFractionDigits:0});}
/* 해외 시가총액(d.tomv = 상장통화 raw 값, 예: NVDA ≈ 5.11e12 USD)을 통화기호 + T/B/M 으로 압축.
   기존엔 '억' 라벨로 오인해 511,248,232조 처럼 칸을 넘쳐 튀어나왔다 → 통화 인식 포맷으로 수정. */
function fmtMcap(v,curr){v=Number(v)||0;if(!v)return '—';
  var sym=curr==='USD'?'$':(curr==='JPY'?'¥':(curr==='HKD'?'HK$':''));
  var a=Math.abs(v),s;
  if(a>=1e12)s=(v/1e12).toFixed(2)+'T';
  else if(a>=1e9)s=(v/1e9).toFixed(2)+'B';
  else if(a>=1e6)s=(v/1e6).toFixed(2)+'M';
  else s=fmtI(v);
  return sym+s;}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function dirSign(d){return d==='up'?'+':(d==='down'?'-':'');}
function fail(msg){$('#state').className='state err';$('#state').textContent=msg;}

/* ── 탭 메뉴 전환 ── */
function miTab(n){
  document.querySelectorAll('.tab-btn').forEach(function(btn, i){
    btn.classList.toggle('active', i===n);
  });
  document.querySelectorAll('.pane').forEach(function(pane, i){
    pane.classList.toggle('active', i===n);
  });
  setTimeout(function(){ window.dispatchEvent(new Event('resize')); }, 50);
}

/* ── 롤링 숫자 애니메이션 ── */
function staticCell(h,ch){var s=document.createElement('span');s.className='rt-ch';
  s.style.cssText='display:inline-block;height:'+h+'px;line-height:'+h+'px;';s.textContent=ch;return s;}
function rollCell(h,oldCh,newCh,up,delay){
  var cell=document.createElement('span');cell.className='rt-ch';
  cell.style.cssText='display:inline-block;height:'+h+'px;overflow:hidden;position:relative;vertical-align:bottom;';
  var col=document.createElement('span');col.style.cssText='display:flex;flex-direction:column;';
  function d(t){var s=document.createElement('span');
    s.style.cssText='display:block;height:'+h+'px;line-height:'+h+'px;';s.textContent=t;return s;}
  if(up){col.appendChild(d(oldCh));col.appendChild(d(newCh));col.style.transform='translateY(0)';}
  else  {col.appendChild(d(newCh));col.appendChild(d(oldCh));col.style.transform='translateY(-'+h+'px)';}
  cell.appendChild(col);
  requestAnimationFrame(function(){requestAnimationFrame(function(){
    col.style.transition='transform '+DUR+'s '+EASE+' '+delay+'ms';
    col.style.transform=up?'translateY(-'+h+'px)':'translateY(0)';});});
  return cell;}
function rollPrice(pe,oldStr,newStr,up){
  if(RM||!oldStr||oldStr===newStr){pe.textContent=newStr;return;}
  var h=parseInt(getComputedStyle(pe).fontSize)||34;
  var nL=newStr.length,oL=oldStr.length,frag=document.createDocumentFragment();
  for(var p=0;p<nL;p++){
    var r=nL-1-p,nc=newStr.charAt(p),oc=(r<oL)?oldStr.charAt(oL-1-r):'';
    if(oc===nc)frag.appendChild(staticCell(h,nc));
    else frag.appendChild(rollCell(h,oc,nc,up,Math.min(r,8)*26));}
  pe.textContent='';pe.appendChild(frag);}

/* ── AI 코멘터리 (우측 상단 팝업 모달) ── */
let _aiAborter = null;
function closeAI() {
  if (_aiAborter) { _aiAborter.abort(); _aiAborter = null; }
  document.getElementById('ai-modal').classList.remove('show');
}
function startAI() {
  if (_aiAborter) { _aiAborter.abort(); }
  _aiAborter = new AbortController();
  
  var modal = document.getElementById('ai-modal');
  var content = document.getElementById('ai-content');
  modal.classList.add('show');
  content.innerHTML = '<div style="color:var(--sub, rgba(60,60,67,0.6));font-size:12.5px;margin-bottom:8px;text-align:center;">실시간 시세·모멘텀·리스크·뉴스를<br>수집·분석 중입니다...</div>' +
                      '<div class="ai-loader"><div class="ai-dot"></div><div class="ai-dot"></div><div class="ai-dot"></div></div>';

  fetch('/api/llm_commentary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(Object.assign({ ov_excd: excd, ov_symb: symb }, (window.kmktAiProv?window.kmktAiProv():{}))),
    signal: _aiAborter.signal
  }).then(async response => {
    content.innerHTML = '<div id="ai-think" style="display:none;font-size:11.5px;opacity:.6;'
      + 'border-left:2px solid rgba(10,132,255,.4);padding:4px 9px;margin:0 0 9px;max-height:150px;'
      + 'overflow:auto;white-space:pre-wrap;line-height:1.5;">💭 <b style="opacity:.85;">추론</b><br>'
      + '<span id="ai-think-t"></span></div>'
      + '<div id="ai-text-container" style="display:inline;"></div><span id="ai-cursor" class="ai-cursor"></span>';
    var textContainer = document.getElementById('ai-text-container');
    var thinkBox = document.getElementById('ai-think');
    var thinkT = document.getElementById('ai-think-t');
    var cursor = document.getElementById('ai-cursor');
    var _nl=String.fromCharCode(10), ansBuf='', md=window.kmktMd||function(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').split(_nl).join('<br>');};
    if(textContainer){textContainer.className='kmkt-md';textContainer.style.display='block';}

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    var buf = '';
    
    function e2(s){return s.replace(/</g,'&lt;').replace(/\n/g,'<br>');}

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, {stream: true});
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            if (data.text) {
              if (data.kind === 'reasoning') {
                var span = document.createElement('span'); span.className = 'ai-chunk';
                span.innerHTML = e2(data.text);
                thinkBox.style.display='block'; thinkT.appendChild(span);
              } else { ansBuf += data.text; textContainer.innerHTML = md(ansBuf); }
              content.scrollTop = content.scrollHeight;
            }
          } catch(e) {}
        }
      }
    }
    if (cursor) cursor.remove();
  }).catch(e => {
    if (e.name === 'AbortError') return;
    content.innerHTML = '<span style="color:#FF3B30;">AI 연결 실패: ' + e.message + '</span>';
  });
}

/* ── 히어로 업데이트 ── */
function updateHero(ccy,last,diff,rate,dir,meta){
  var up=dir==='up';
  var dn=dir==='down';
  var hero=$('#hero');
  hero.className='price-hero '+(up?'up':(dn?'down':'flat'));
  var newStr=fmt(last);
  var hc=$('#hCcy');if(hc)hc.textContent=ccy;
  rollPrice($('#hPx'),lastPxStr,newStr,up);
  lastPxStr=newStr;lastDir=dir;
  var s=dirSign(dir);
  $('#hChg').textContent=(up?'▲ ':diff<0?'▼ ':'')+s+fmt(Math.abs(diff))+' ('+s+fmt(Math.abs(rate))+'%)';
  if(meta)$('#hMeta').textContent=meta;
  if(lastFx>0&&last>0)$('#hKrw').textContent='원화 약 '+fmtI(last*lastFx)+'원 · 환율 ₩'+fmt(lastFx,0);
  var rtb=$('#rtBadge');if(rtb)rtb.style.display='';
  
  // KPI 실시간 갱신 (up, dn 색상 연동)
  var kpP = $('#kpiPrice');
  if(kpP) {
    kpP.textContent = ccy + ' ' + newStr;
  }
  var kpPS = $('#kpiPriceSub');
  if(kpPS) {
    kpPS.textContent = (up ? '▲ ' : diff < 0 ? '▼ ' : '') + fmt(Math.abs(diff));
    kpPS.className = 'k-sub ' + (up ? 'k-up' : dn ? 'k-down' : '');
  }
  var signRate = (rate > 0 ? '+' : '') + fmt(rate) + '%';
  var kpR = $('#kpiRate');
  if(kpR){
    kpR.textContent = signRate;
    kpR.className = 'k-val ' + (up ? 'k-up' : dn ? 'k-down' : '');
  }
  var kpRS = $('#kpiRateSub');
  if(kpRS) {
    kpRS.textContent = '전일대비 변동';
  }
}

function start(){
  var pre=excd?Promise.resolve({ok:true,excd:excd}):fetch('/api/ov/resolve?symb='+encodeURIComponent(symb)).then(function(r){return r.json();});
  pre.then(function(r0){
    if(!r0.ok){fail(r0.needs_key?'KIS 키 필요':(r0.msg||'조회 실패'));return;}
    excd=r0.excd;
    return fetch('/api/ov/detail?excd='+excd+'&symb='+encodeURIComponent(symb)).then(function(r){return r.json();});
  }).then(function(d){
    if(!d)return;
    if(!d.ok){fail(d.needs_key?'KIS 키 필요':'상세 정보를 가져올 수 없습니다');return;}
    info=d;render(d);loadChart();loadNews();
    if(pollTid)clearInterval(pollTid);
    pollTid=setInterval(pollPrice,10000);
  }).catch(function(){fail('네트워크 오류');});
}

function render(d){
  $('#state').style.display='none';$('#body').style.display='block';
  initFX();
  document.title=(kname||d.symb)+' — 해외주식';
  
  // etf-head 헤더 데이터 주입
  var elCode = $('#ehCode'); if(elCode) elCode.textContent = d.symb;
  var elEx = $('#ehEx'); if(elEx) elEx.textContent = d.exname + (d.curr ? ' · ' + d.curr : '');
  if (d.sector) {
    var es = $('#ehSec');
    if(es) { es.style.display = ''; es.textContent = d.sector; }
  }
  var statusText = d.state ? d.state.name : '';
  var ccyText = d.curr ? ' · ' + d.curr : '';
  var elAsof = $('#ehAsof'); if(elAsof) elAsof.textContent = statusText + ccyText + ' · 기준일 ' + (d.state && d.state.date ? d.state.date : new Date().toLocaleDateString('ko-KR'));
  var elName = $('#ehName'); if(elName) elName.textContent = kname || d.symb;

  // 헤더 및 서브타이틀
  $('#sy').textContent=d.symb;
  $('#nm').textContent=kname ? '(' + kname + ')' : '';
  var hdrSubText = statusText + ccyText + ' · 기준일 ' + (d.state && d.state.date ? d.state.date : new Date().toLocaleDateString('ko-KR'));
  $('#hdrSub').textContent = hdrSubText;

  // 히어로 카드 내부
  $('#heroNm').textContent=kname||d.symb;
  $('#heroSy').textContent=d.symb;
  if(d.state){
    $('#mktBadge').style.display='';
    $('#mktBadge').className='badge '+d.state.phase;
    $('#mktBadge').textContent=d.state.name;
  }
  $('#ex').textContent=d.exname+(d.curr?' · '+d.curr:'');
  
  // KPI 그리드 초기 렌더링
  var up = d.dir === 'up';
  var dn = d.dir === 'down';
  $('#kpiPrice').textContent = d.curr + ' ' + fmt(d.last);
  
  var kpiPS = $('#kpiPriceSub');
  if(kpiPS) {
    kpiPS.textContent = (up ? '▲ ' : d.diff < 0 ? '▼ ' : '') + fmt(Math.abs(d.diff));
    kpiPS.className = 'k-sub ' + (up ? 'k-up' : dn ? 'k-down' : '');
  }
  
  var signRate = (d.rate > 0 ? '+' : '') + fmt(d.rate) + '%';
  var kpR = $('#kpiRate');
  if(kpR){
    kpR.textContent = signRate;
    kpR.className = 'k-val ' + (up ? 'k-up' : dn ? 'k-down' : '');
  }
  
  var kpRS = $('#kpiRateSub');
  if(kpRS) {
    kpRS.textContent = '전일대비 변동';
  }
  
  $('#kpiMcap').textContent = fmtMcap(d.tomv, d.curr);
  $('#kpiMcapSub').textContent = d.curr || 'USD';
  
  $('#kpiVol').textContent = fmtI(d.tvol) + '주';
  $('#kpiVolSub').textContent = '최근 거래량';

  // 상세 지표 정보 그리드 렌더링 (3열 정렬)
  var tb = $('#descTable');
  if(tb){
    var items = [
      ['시장', esc(d.exname)],
      ['결산월', d.settle_month || '12월'],
      ['시가총액', d.tomv ? fmtMcap(d.tomv, d.curr) + ' ' + (d.curr || '') : '—'],
      ['상장주식수', d.shar ? fmtI(d.shar) + '주' : '—'],
      ['52주 최고/최저', d.h52p && d.l52p ? fmt(d.h52p) + ' / ' + fmt(d.l52p) : '—'],
      ['거래량', fmtI(d.tvol) + '주'],
      ['PER / PBR', (d.per ? fmt(d.per) : '—') + ' / ' + (d.pbr ? fmt(d.pbr) : '—')],
      ['EPS / BPS', (d.eps ? fmt(d.eps) : '—') + ' / ' + (d.bps ? fmt(d.bps) : '—')],
      ['액면가', d.parp ? fmt(d.parp) : '—'],
      ['매매단위', d.vnit ? fmtI(d.vnit) + '주' : '—']
    ];
    tb.innerHTML = items.map(function(item){
      return '<div class="ei">' +
             '<span class="ei-l">' + item[0] + '</span>' +
             '<span class="ei-v">' + item[1] + '</span>' +
             '</div>';
    }).join('');
  }

  if(d.profile_html){var op=document.getElementById('ovProfile');if(op)op.innerHTML=d.profile_html;}
  window.KMKT_ASK=function(){return{scope:'ov',id:symb,excd:excd};};
  if(d.sector){$('#sec').style.display='';$('#sec').textContent=d.sector;}
  if(d.fx>0)lastFx=d.fx;
  updateHero(d.ccy,d.last,d.diff,d.rate,d.dir,'');
  
  var rw=$('#rngWrap');
  if(rw && d.h52p>d.l52p){
    rw.style.display='block';
    var p=Math.min(100,Math.max(0,(d.last-d.l52p)/(d.h52p-d.l52p)*100));
    var rngDot = $('#rngDot'); if(rngDot) rngDot.style.left=p+'%';
    var rngLo = $('#rngLo'); if(rngLo) rngLo.textContent='최저 '+d.ccy+fmt(d.l52p)+(d.l52d?' ('+esc(d.l52d)+')':'');
    var rngHi = $('#rngHi'); if(rngHi) rngHi.textContent='최고 '+d.ccy+fmt(d.h52p)+(d.h52d?' ('+esc(d.h52d)+')':'');
  }
}

var chartD = [];
var filterGubn = '4'; // 기본 1년

function loadChart(){
  fetch('/api/ov/chart?excd='+excd+'&symb='+encodeURIComponent(symb),{cache:'no-store'})
    .then(function(r){return r.json();})
    .then(function(d){
      chartD = d.rows || [];
      renderRets();
      draw();
    });
}

function calcMAAll(data, period) {
  var ma = [];
  for (var i = 0; i < data.length; i++) {
    if (i < period - 1) {
      ma.push(null);
    } else {
      var sum = 0;
      for (var j = 0; j < period; j++) {
        sum += data[i - j].c;
      }
      ma.push(sum / period);
    }
  }
  return ma;
}

function renderRets(){
  if(!chartD.length){$('#tiles').innerHTML='<div class="state" style="padding:4px 0;">차트 데이터 없음</div>';return;}
  var c = chartD[chartD.length-1].c;
  function ret(days){
    var idx = chartD.length - 1 - days;
    if(idx < 0) return null;
    return (c / chartD[idx].c - 1) * 100;
  }
  function retYTD(){
    var lastDate = new Date(chartD[chartD.length-1].d.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
    var yearStart = new Date(lastDate.getFullYear(), 0, 1);
    var firstIdx = -1;
    for(var i=0; i<chartD.length; i++){
      var d = new Date(chartD[i].d.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
      if(d >= yearStart){
        firstIdx = i;
        break;
      }
    }
    if(firstIdx <= 0) return null;
    return (c / chartD[firstIdx].c - 1) * 100;
  }
  
  var defs = [
    ['1주', 5], ['1개월', 21], ['3개월', 63], ['6개월', 126], ['연초이후', 'ytd'], ['1년', 250], ['3년', 750], ['5년', 1250]
  ];
  
  var ths = '<th style="text-align:left;">구분</th>';
  var tds = '<td>수익률(%)</td>';
  var hasData = false;
  defs.forEach(function(df){
    var v = null;
    if (df[1] === 'ytd') {
      v = retYTD();
    } else {
      if(df[1] <= chartD.length) v = ret(df[1]);
    }
    if (v !== null || df[1] !== 'ytd') {
      if(df[1] !== 'ytd' && df[1] > chartD.length) return;
      hasData = true;
      ths += '<th>' + df[0] + '</th>';
      var cls = v==null?'':(v>0?'t-up':v<0?'t-down':'');
      var t = v==null?'—':((v>0?'+':'')+fmt(v));
      tds += '<td class="'+cls+'">'+t+'</td>';
    }
  });
  
  if(!hasData){
    $('#tiles').innerHTML = '<div class="state" style="padding:4px 0;">수익률 정보 없음</div>';
    return;
  }
  $('#tiles').innerHTML = '<div class="tbl-scroll"><table class="mi-table bold-first"><thead><tr>' + ths + '</tr></thead><tbody><tr>' + tds + '</tr></tbody></table></div>';
}

function loadNews(){
  fetch('/api/ov/news?excd='+excd+'&symb='+encodeURIComponent(symb),{cache:'no-store'})
    .then(function(r){return r.json();}).then(function(d){
      var rs=(d&&d.rows)||[];
      rs=rs.slice(0,6);
      var cap=d&&d.scope==='market'
        ?'<div class="note" style="margin:0 0 6px;">이 종목의 개별 뉴스가 없어 '+(d.nation==='JP'?'일본':(d.nation==='US'?'미국':'해외'))+' 시장 뉴스를 보여드립니다.</div>':'';
      $('#news').innerHTML=rs.length?cap+rs.map(function(n){
        var dt=(n.date||'').replace(/(\d{4})(\d{2})(\d{2})/,'$2.$3')+(n.time?' '+String(n.time).slice(0,2)+':'+String(n.time).slice(2,4):'');
        return '<div class="it"><span class="t">'+esc(n.title)+'</span><span class="meta">'+esc(n.src||'')+' '+dt+'</span></div>';
      }).join(''):'<div class="state" style="padding:8px 0;">해외 뉴스가 없습니다.</div>';
    }).catch(function(){$('#news').innerHTML='<div class="state" style="padding:8px 0;">뉴스를 불러오지 못했습니다.</div>';});
}

function draw(){
  var el = document.getElementById('plotlyChart');
  if(!el || !window.Plotly || !chartD.length) return;
  
  var isDark = document.documentElement.classList.contains('dark');
  // 국내 주식 리포트의 candle_chart() 와 완전히 동일한 차트로 통일:
  // 상승=빨강 #C0392B, 하락=파랑 #2E75B6 (테마 무관 고정·채워진 캔들), MA 동일 배색.
  var upCol = '#C0392B', dnCol = '#2E75B6';
  var textCol = isDark ? '#eef3ff' : '#1d1d1f';
  var gridCol = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
  
  var ma5All = calcMAAll(chartD, 5);
  var ma20All = calcMAAll(chartD, 20);
  var ma60All = calcMAAll(chartD, 60);
  var ma120All = calcMAAll(chartD, 120);
  
  var startIdx = 0;
  var lastIdx = chartD.length - 1;
  var lastDate = new Date(chartD[lastIdx].d.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
  
  if (filterGubn === '0') {
    startIdx = Math.max(0, chartD.length - 5);
  } else if (filterGubn === '1') {
    startIdx = Math.max(0, chartD.length - 21);
  } else if (filterGubn === '2') {
    startIdx = Math.max(0, chartD.length - 63);
  } else if (filterGubn === '3') {
    var yearStart = new Date(lastDate.getFullYear(), 0, 1);
    for(var i=0; i<chartD.length; i++){
      var d = new Date(chartD[i].d.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
      if(d >= yearStart){
        startIdx = i;
        break;
      }
    }
  } else if (filterGubn === '4') {
    startIdx = Math.max(0, chartD.length - 250);
  } else if (filterGubn === '5') {
    startIdx = Math.max(0, chartD.length - 750);
  } else {
    startIdx = 0;
  }
  
  var filtered = chartD.slice(startIdx);
  var dates = filtered.map(function(r){
    return r.d.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
  });
  
  var sliceMA5 = ma5All.slice(startIdx);
  var sliceMA20 = ma20All.slice(startIdx);
  var sliceMA60 = ma60All.slice(startIdx);
  var sliceMA120 = ma120All.slice(startIdx);
  
  var traceCandle = {
    x: dates,
    open: filtered.map(function(r){return r.o;}),
    high: filtered.map(function(r){return r.h;}),
    low: filtered.map(function(r){return r.l;}),
    close: filtered.map(function(r){return r.c;}),
    type: 'candlestick',
    name: '가격',
    showlegend: false,
    increasing: {line: {color: upCol}, fillcolor: upCol},
    decreasing: {line: {color: dnCol}, fillcolor: dnCol},
    xaxis: 'x',
    yaxis: 'y'
  };
  // MA 배색은 국내 candle_chart() 와 동일: MA5=세이지그린 MA20=빨강 MA60=주황 MA120=보라
  var traceMA5 = { x: dates, y: sliceMA5, type: 'scatter', mode: 'lines', name: 'MA5', line: {color: '#2E8B57', width: 1.3}, connectgaps: true };
  var traceMA20 = { x: dates, y: sliceMA20, type: 'scatter', mode: 'lines', name: 'MA20', line: {color: '#C0392B', width: 1.3}, connectgaps: true };
  var traceMA60 = { x: dates, y: sliceMA60, type: 'scatter', mode: 'lines', name: 'MA60', line: {color: '#E08E3C', width: 1.3}, connectgaps: true };
  var traceMA120 = { x: dates, y: sliceMA120, type: 'scatter', mode: 'lines', name: 'MA120', line: {color: '#7030A0', width: 1.3}, connectgaps: true };
  
  var traceVol = {
    x: dates,
    y: filtered.map(function(r){return r.v;}),
    type: 'bar',
    name: '거래량',
    showlegend: false,
    marker: {
      color: filtered.map(function(r){return r.c >= r.o ? upCol : dnCol;})
    },
    opacity: 0.55,
    xaxis: 'x',
    yaxis: 'y2'
  };
  
  var traces = [traceCandle, traceMA5, traceMA20, traceMA60, traceMA120, traceVol];
  
  var layout = {
    template: isDark ? 'plotly_dark' : 'plotly_white',
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    height: 400,
    margin: {l: 40, r: 20, t: 30, b: 30},
    showlegend: true,
    legend: {orientation: 'h', y: 1.12, x: 0, font: {size: 11, color: textCol}},
    xaxis: {
      type: 'category',
      nticks: 8,
      tickangle: 0,
      automargin: true,
      gridcolor: gridCol,
      tickfont: {size: 10, color: textCol},
      rangeslider: {visible: false}
    },
    yaxis: {
      domain: [0.22, 1],
      gridcolor: gridCol,
      tickfont: {size: 10, color: textCol},
      separatethousands: true
    },
    yaxis2: {
      domain: [0, 0.18],
      gridcolor: gridCol,
      tickfont: {size: 10, color: textCol},
      separatethousands: true
    }
  };
  
  Plotly.react('plotlyChart', traces, layout, {displaylogo: false, responsive: true});
}

document.querySelectorAll('#seg button').forEach(function(btn, idx) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('#seg button').forEach(function(b) {
      b.classList.remove('on');
    });
    btn.classList.add('on');
    filterGubn = String(idx);
    draw();
  });
});

window.addEventListener('resize', draw);

function pollPrice(){
  if(!excd||!symb)return;
  if(document.hidden)return;
  fetch('/api/ov/price?excd='+excd+'&symb='+encodeURIComponent(symb),{cache:'no-store'})
    .then(function(r){return r.json();}).then(function(d){
      if(!d.ok)return;
      if(d.state){
        $('#mktBadge').style.display='';
        $('#mktBadge').className='badge '+d.state.phase;
        $('#mktBadge').textContent=d.state.name;
      }
      var now=new Date();
      var meta='실시간 · '+now.toLocaleTimeString('ko-KR',{hour12:false})+' 갱신';
      updateHero(d.ccy,d.last,d.diff,d.rate,d.dir,meta);
    }).catch(function(){});
}

/* ── 라이트 FX: 카드 등장 애니 + hover 3D 틸트 + 기간수익률 카운트업 ── */
var _fxDone=false;
function initFX(){
  if(_fxDone||RM)return;_fxDone=true;
  try{
    var io=new IntersectionObserver(function(es){es.forEach(function(en){
      if(en.isIntersecting){en.target.classList.add('fx-in');io.unobserve(en.target);}});},{threshold:0.08});
    document.querySelectorAll('.card').forEach(function(c){io.observe(c);});
  }catch(e){document.querySelectorAll('.card').forEach(function(c){c.classList.add('fx-in');});}
  document.querySelectorAll('.card').forEach(function(c){
    if(c.querySelector('canvas'))return;
    c.addEventListener('mousemove',function(e){
      var r=c.getBoundingClientRect(),px=(e.clientX-r.left)/r.width-.5,py=(e.clientY-r.top)/r.height-.5;
      c.style.transform='perspective(1100px) rotateX('+(-py*2.4)+'deg) rotateY('+(px*2.4)+'deg)';});
    c.addEventListener('mouseleave',function(){c.style.transform='';});
  });
}
function countTiles(){
  if(RM)return;
  document.querySelectorAll('#tiles .v').forEach(function(el){
    var raw=el.textContent.trim();if(raw==='—')return;
    var m=raw.match(/-?[\d,]+\.?\d*/);if(!m)return;
    var target=parseFloat(m[0].replace(/,/g,''));
    var sign=raw.charAt(0)==='+'?'+':(raw.charAt(0)==='-'?'-':'');
    var t0=performance.now(),dur=750;
    (function step(t){var k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);
      if(k<1){el.textContent=sign+Math.abs(target*e).toFixed(2)+'%';requestAnimationFrame(step);}
      else el.textContent=raw;})(t0);
  });
}

if(!symb){fail('종목 코드가 없습니다.');}else{start();}
</script></body></html>
"""

_REALTIME_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="realtime"><head><meta charset="utf-8">
<title>실시간 트레이딩</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f0f1f5;--card:rgba(255,255,255,.92);--ink:#1d1d1f;--sub:rgba(60,60,67,.56);
 --line:rgba(60,60,67,.11);--row:rgba(10,132,255,.05);--head:rgba(60,60,67,.5);
 --up:#FF3B30;--dn:#2E75B6;--up-bg:rgba(255,59,48,.09);--dn-bg:rgba(46,117,182,.09);
 --accent:#0A84FF;--green:#34C759;--hero-up:#FF3B30;--hero-dn:#2E75B6;}
html.dark{--bg:#0b0f1a;--card:rgba(24,26,36,.88);--ink:#eef3ff;--sub:#8a97b5;
 --line:rgba(255,255,255,.09);--row:rgba(90,166,255,.08);--head:#8a97b5;
 --up:#FF453A;--dn:#64B5FF;--up-bg:rgba(255,69,58,.14);--dn-bg:rgba(100,181,255,.14);
 --accent:#0A84FF;--green:#30D158;--hero-up:#c0241a;--hero-dn:#1f4f86;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
 background:var(--bg);color:var(--ink);
 -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;overflow-x:hidden;}

/* ── 검색/상태 바 ── */
.topbar{display:flex;align-items:center;gap:10px;padding:10px 14px 0;flex-wrap:wrap;}
.sym-row{display:flex;align-items:center;gap:7px;}
.sym-row input{font:inherit;font-size:13.5px;padding:7px 11px;border:.5px solid var(--line);
 border-radius:10px;background:var(--card);color:var(--ink);width:160px;outline:none;
 box-shadow:0 1px 4px rgba(0,0,0,.06);}
.sym-row input:focus{box-shadow:0 0 0 3px rgba(10,132,255,.22);}
.sym-row button{font:inherit;font-size:12.5px;font-weight:700;padding:7px 14px;border:0;
 border-radius:10px;background:var(--accent);color:#fff;cursor:pointer;letter-spacing:-.02em;}
.live-dot{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:var(--sub);}
.live-dot .dot{width:7px;height:7px;border-radius:50%;background:#aaa;transition:background .3s;}
.live-dot .dot.on{background:var(--green);box-shadow:0 0 6px var(--green);}

/* ── 히어로 가격 바 ── */
.hero{margin:10px 14px 12px;border-radius:14px;padding:14px 18px;
 background:var(--up);color:#fff;transition:background .4s ease;position:relative;overflow:hidden;}
.hero,.hero *{color:#fff;}            /* 전역 .dn{color:파랑} 이 히어로 글씨를 덮어쓰는 것 방지 */
.hero.dn{background:var(--hero-dn);}
.hero .h-top{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;}
.hero .h-nm{font-size:13px;font-weight:600;opacity:.88;}
.hero .h-code{font-size:11.5px;opacity:.72;}
.hero .h-badge{font-size:10px;border:1px solid rgba(255,255,255,.4);border-radius:5px;
 padding:1px 6px;opacity:.85;margin-left:auto;}
.hero .h-px{font-size:34px;font-weight:800;letter-spacing:-.025em;line-height:1.1;
 margin-top:4px;font-variant-numeric:tabular-nums;position:relative;display:inline-block;}
.hero .h-px .rt-ch{display:inline-block;position:relative;overflow:hidden;vertical-align:bottom;}
.hero .h-px .rt-col{display:flex;flex-direction:column;}
.hero .h-chg{font-size:14px;font-weight:600;opacity:.92;margin-top:3px;}
.hero .h-meta{font-size:11px;opacity:.7;margin-top:4px;}

/* ── 메인 레이아웃 (flex + 드래그 리사이저) ── */
.main{display:flex;gap:10px;padding:0 14px 10px;align-items:stretch;min-width:0;}
.col-left{flex:1 1 0;min-width:240px;display:flex;flex-direction:column;gap:10px;}
.rsz{flex:0 0 6px;align-self:stretch;cursor:col-resize;border-radius:3px;background:var(--line);
 transition:background .15s;}
.rsz:hover,.rsz.drag{background:var(--accent);}
.right-group{flex:0 1 var(--rgw,430px);min-width:0;max-width:660px;display:flex;gap:10px;align-items:flex-start;}
.col-ob{flex:1 1 0;min-width:0;}
.col-paper{flex:1 1 0;min-width:0;}
@media(max-width:760px){.main{flex-wrap:wrap;}.rsz{display:none;}
 .col-left{flex:1 1 100%;}.right-group{flex:1 1 100%;}}

/* ── 카드 공통 ── */
.card{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(28px);
 backdrop-filter:saturate(180%) blur(28px);border:.5px solid var(--line);border-radius:14px;
 padding:12px 14px;box-shadow:0 8px 28px rgba(0,0,0,.06);}
h3{font-size:13.5px;font-weight:700;letter-spacing:-.01em;margin-bottom:9px;color:var(--ink);}
.note{font-size:12px;color:var(--sub);}
.err-msg{font-size:12.5px;color:var(--up);padding:8px 0;}
.up{color:var(--up);} .dn{color:var(--dn);}

/* ── 왼쪽: 차트 + 하단 패널 ── (.col-left flex 규칙은 위 .main 블록 참조) */
canvas.chart{width:100%;height:280px;display:block;border-radius:8px;}
.chart-seg{display:inline-flex;gap:0;border:.5px solid var(--line);border-radius:8px;overflow:hidden;margin-left:auto;}
.chart-seg button{background:transparent;border:0;color:var(--sub);font:inherit;font-size:12.5px;
 padding:4px 9px;cursor:pointer;}
.chart-seg button.on{background:var(--accent);color:#fff;}
.lower-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;}

/* ── 체결 시세 ── */
.ticker-list{display:flex;flex-direction:column;gap:0;max-height:248px;overflow:hidden;}
.t-row{display:grid;grid-template-columns:1fr auto auto;gap:6px;padding:5px 2px;
 border-bottom:.5px solid var(--line);font-size:13px;align-items:center;}
.t-row:last-child{border-bottom:0;}
.t-row .tpx{font-weight:700;}
.t-row .tq{color:var(--sub);font-size:12px;text-align:right;}
.t-row .tch{font-size:12px;text-align:right;}

/* ── 수급 ── */
.flow-row{display:flex;align-items:center;gap:8px;padding:7px 2px;border-bottom:.5px solid var(--line);font-size:13px;}
.flow-row:last-child{border-bottom:0;}
.flow-row .fn{width:46px;color:var(--sub);font-size:12px;flex-shrink:0;}
.flow-row .fv{width:76px;text-align:right;font-weight:700;font-size:13.5px;}
.flow-bar-wrap{flex:1;height:5px;background:var(--line);border-radius:3px;overflow:hidden;}
.flow-bar{height:100%;border-radius:3px;transition:width .5s ease;}

/* ── 중앙: 호가창 ── */
.col-ob{}
.ob-wrap{display:flex;flex-direction:column;gap:1px;}
.ob-row{position:relative;display:flex;justify-content:space-between;align-items:center;
 padding:5px 9px;border-radius:5px;font-size:13px;overflow:hidden;min-height:30px;}
.ob-bg{position:absolute;top:0;bottom:0;opacity:.9;z-index:0;transition:width .2s;}
.ob-ask .ob-bg{background:var(--up-bg);right:0;}
.ob-bid .ob-bg{background:var(--dn-bg);right:0;}
.ob-px{position:relative;z-index:1;font-weight:700;font-size:14px;}
.ob-ask .ob-px{color:var(--up);} .ob-bid .ob-px{color:var(--dn);}
.ob-pct{position:relative;z-index:1;font-size:11px;color:var(--sub);}
.ob-ask .ob-pct{color:rgba(232,41,28,.65);} .ob-bid .ob-pct{color:rgba(26,101,192,.65);}
html.dark .ob-ask .ob-pct{color:rgba(255,90,80,.65);} html.dark .ob-bid .ob-pct{color:rgba(90,173,255,.65);}
.ob-q{position:relative;z-index:1;color:var(--sub);font-size:12.5px;}
.ob-cur{background:var(--ink);color:var(--bg) !important;text-align:center;font-size:15px;
 font-weight:800;padding:7px;border-radius:6px;margin:3px 0;letter-spacing:-.02em;}
.ob-info{display:flex;justify-content:space-between;align-items:center;margin-top:7px;font-size:11px;color:var(--sub);}
.imb-bar{height:5px;border-radius:3px;background:var(--dn);margin-top:5px;overflow:hidden;}
.imb-fill{height:100%;background:var(--up);transition:width .4s ease;}

/* ── 오른쪽: 페이퍼 트레이딩 ── */
.paper-tiles{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;}
.ptile{background:var(--row);border-radius:10px;padding:9px 10px;}
.ptile .pk{font-size:11.5px;color:var(--sub);}
.ptile .pv{font-size:16px;font-weight:700;margin-top:2px;}
.pnl-pos{color:var(--up);} .pnl-neg{color:var(--dn);}
.paper-form{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;}
.paper-form input{width:100%;padding:8px 10px;border:.5px solid var(--line);border-radius:9px;
 background:var(--bg);color:var(--ink);font:inherit;font-size:12.5px;outline:none;}
.paper-form input:focus{box-shadow:0 0 0 2.5px rgba(10,132,255,.22);}
.pbuy{background:var(--up);color:#fff;border:0;border-radius:9px;font:inherit;font-size:13px;
 font-weight:700;padding:9px;cursor:pointer;letter-spacing:-.01em;}
.psell{background:var(--dn);color:#fff;border:0;border-radius:9px;font:inherit;font-size:13px;
 font-weight:700;padding:9px;cursor:pointer;letter-spacing:-.01em;}
.preset{background:transparent;color:var(--sub);border:.5px solid var(--line);border-radius:9px;
 font:inherit;font-size:11.5px;padding:6px 10px;cursor:pointer;width:100%;margin-bottom:8px;}
.pmsg{font-size:11.5px;color:var(--sub);min-height:18px;margin-bottom:8px;}
.pos-table{width:100%;border-collapse:collapse;font-size:12.5px;table-layout:fixed;}
.pos-table th:nth-child(1) { width:34%; }
.pos-table th:nth-child(2) { width:18%; }
.pos-table th:nth-child(3) { width:24%; }
.pos-table th:nth-child(4) { width:24%; }
.pos-table th,.pos-table td{padding:6px 5px;border-bottom:.5px solid var(--line);text-align:right;white-space:nowrap;}
.pos-table th:first-child,.pos-table td:first-child{text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.pos-table th{color:var(--head);font-size:11.5px;}
.pos-table tr{cursor:pointer;} .pos-table tr:hover{background:var(--row);}
.paper-empty{font-size:12px;color:var(--sub);padding:8px 2px;}

/* ── 하단: 스크리너 ── */
.scr-section{padding:0 14px 14px;}
.scr-seg{display:inline-flex;gap:0;border:.5px solid var(--line);border-radius:8px;overflow:hidden;margin-left:auto;}
.scr-seg button{background:transparent;border:0;color:var(--sub);font:inherit;font-size:12.5px;
 padding:4px 9px;cursor:pointer;}
.scr-seg button.on{background:var(--accent);color:#fff;}
.scr-table{width:100%;border-collapse:collapse;font-size:13.5px;table-layout:fixed;}
.scr-table th:nth-child(1) { width:40%; }
.scr-table th:nth-child(2) { width:20%; }
.scr-table th:nth-child(3) { width:20%; }
.scr-table th:nth-child(4) { width:20%; }
.scr-table th,.scr-table td{padding:8px 9px;border-bottom:.5px solid var(--line);text-align:right;white-space:nowrap;}
.scr-table th:first-child,.scr-table td:first-child{text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.scr-table th{color:var(--head);font-size:12px;}
.scr-table tbody tr{cursor:pointer;transition:background .12s;}
.scr-table tbody tr:hover{background:var(--row);}
/* ── 오버플로 차단 (작업1) — flex/grid 자식이 부모(뷰포트) 밖으로 넘치지 않도록 전역 가드.
   원인: grid 항목은 기본 min-width:auto 라 긴 숫자(현금·손익·수량)가 칸을 못 줄여 카드 밖으로
   밀려난다. minmax(0,1fr)+min-width:0+ellipsis 로 강제 수축·말줄임. (지침 §10.2) ── */
.main,.col-left,.right-group,.col-ob,.col-paper,.ptile{min-width:0;}
.right-group .card,.col-left .card{max-width:100%;overflow:hidden;}
.lower-row,.paper-tiles{grid-template-columns:minmax(0,1fr) minmax(0,1fr);}
.ptile .pv{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
</style></head>
<body>

<!-- 검색 바 -->
<div class="topbar">
  <div class="sym-row">
    <input id="sym" type="text" value="005930" placeholder="종목코드 6자리" maxlength="6">
    <button id="go">구독</button>
  </div>
  <div class="live-dot"><span class="dot" id="liveDot"></span><span id="liveSt">대기 중</span></div>
</div>

<!-- 히어로 가격 바 -->
<div class="hero" id="hero">
  <div class="h-top">
    <span class="h-nm" id="hNm">실시간 트레이딩</span>
    <span class="h-code" id="hCode">005930</span>
    <span class="h-badge" id="hBadge">● 실시간</span>
  </div>
  <div style="display:flex;align-items:baseline;gap:4px;margin-top:4px;">
    <span class="h-px" id="hPx" style="margin-top:0;">—</span>
    <span style="font-size:24px;font-weight:700;opacity:0.9;">원</span>
  </div>
  <div class="h-chg" id="hChg"></div>
  <div class="h-meta" id="hMeta">종목을 구독하면 실시간으로 시세가 업데이트됩니다</div>
</div>

<!-- 메인 그리드 -->
<div class="main">

  <!-- 왼쪽: 차트 + 하단 패널 -->
  <div class="col-left">
    <div class="card">
      <div style="display:flex;align-items:center;margin-bottom:8px;">
        <h3 style="margin:0;">일봉 차트</h3>
        <div class="chart-seg" id="chartSeg">
          <button data-d="20" class="on">1개월</button>
          <button data-d="60">3개월</button>
          <button data-d="120">6개월</button>
        </div>
      </div>
      <canvas class="chart" id="cv"></canvas>
      <div class="note" id="chartNote" style="margin-top:5px;"></div>
    </div>
    <div class="lower-row">
      <div class="card">
        <h3>체결 시세</h3>
        <div class="ticker-list" id="ticker"><div class="note">장 중 체결이 여기에 흐릅니다.</div></div>
      </div>
      <div class="card">
        <h3>투자자 동향</h3>
        <div id="flowWrap"><div class="note">불러오는 중…</div></div>
      </div>
    </div>
  </div>

  <!-- 드래그 리사이저 (좌측 차트 영역 ↔ 우측 호가/페이퍼 너비 조절) -->
  <div class="rsz" id="rsz" title="드래그하여 너비 조절"></div>

  <!-- 오른쪽 그룹: 호가창 + 페이퍼 트레이딩 -->
  <div class="right-group">
    <div class="col-ob">
      <div class="card" style="padding:10px 12px;">
        <h3>호가창</h3>
        <div class="ob-wrap" id="ob"><div class="note">구독 대기 중…</div></div>
        <div class="ob-info"><span id="cttrTxt"></span><span id="cttrPct"></span></div>
        <div class="imb-bar"><div class="imb-fill" id="imbFill" style="width:50%"></div></div>
      </div>
    </div>
    <div class="col-paper">
      <div class="card">
        <h3>📝 페이퍼 트레이딩 <span class="note">시뮬 · 실주문 없음</span></h3>
        <div class="paper-tiles" id="pTiles"></div>
        <div class="paper-form">
          <input id="pQty" type="number" min="1" value="10" placeholder="수량">
          <span></span>
          <button class="pbuy" id="pBuy">매수</button>
          <button class="psell" id="pSell">매도</button>
        </div>
        <div class="pmsg" id="pMsg"></div>
        <button class="preset" id="pReset">계좌 초기화</button>
        <div id="pPos"></div>
      </div>
    </div>
  </div>

</div>

<!-- 하단: 스크리너 -->
<div class="scr-section">
  <div class="card">
    <div style="display:flex;align-items:center;margin-bottom:8px;">
      <h3 style="margin:0;">실시간 스크리너</h3>
      <div class="scr-seg" id="blngSeg">
        <button data-b="0" class="on">거래량</button>
        <button data-b="3">거래대금</button>
        <button data-b="1">거래증가율</button>
      </div>
    </div>
    <div id="scrWrap"><div class="note">불러오는 중…</div></div>
  </div>
</div>

<script>
var $=function(s){return document.querySelector(s);};
var code=(new URLSearchParams(location.search).get('code')||'005930').trim(), es=null, blng='0', lastFrame=null, histRows=[], chartDays=20;
var lastPxStr='', lastPx=0, RM=(window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches);
if($('#sym')) $('#sym').value=code;
var DUR=0.62, EASE='cubic-bezier(.16,1,.3,1)';

function setTheme(d){document.documentElement.classList.toggle('dark',!!d);drawChart();}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)setTheme(e.data.kmkt==='dark');});
try{if(localStorage.getItem('kmkt-theme')==='dark')setTheme(true);}catch(_){}

function fmt(n,d){n=Number(n)||0;return n.toLocaleString('ko-KR',{maximumFractionDigits:(d==null?0:d)});}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

/* ── 롤링 숫자 애니메이션 ── */
function staticCell(h,ch){var s=document.createElement('span');s.className='rt-ch';
  s.style.cssText='display:inline-block;height:'+h+'px;line-height:'+h+'px;';s.textContent=ch;return s;}
function rollCell(h,oldCh,newCh,up,delay){
  var cell=document.createElement('span');cell.className='rt-ch';
  cell.style.cssText='display:inline-block;height:'+h+'px;overflow:hidden;position:relative;vertical-align:bottom;';
  var col=document.createElement('span');col.style.cssText='display:flex;flex-direction:column;';
  function d(t){var s=document.createElement('span');
    s.style.cssText='display:block;height:'+h+'px;line-height:'+h+'px;';s.textContent=t;return s;}
  if(up){col.appendChild(d(oldCh));col.appendChild(d(newCh));col.style.transform='translateY(0)';}
  else  {col.appendChild(d(newCh));col.appendChild(d(oldCh));col.style.transform='translateY(-'+h+'px)';}
  cell.appendChild(col);
  requestAnimationFrame(function(){requestAnimationFrame(function(){
    col.style.transition='transform '+DUR+'s '+EASE+' '+delay+'ms';
    col.style.transform=up?'translateY(-'+h+'px)':'translateY(0)';});});
  return cell;}
function rollPrice(pe,oldStr,newStr,up){
  if(RM||!oldStr||oldStr===newStr||oldStr.length!==newStr.length){pe.textContent=newStr;return;}
  var h=parseInt(getComputedStyle(pe).fontSize)||34;
  var nL=newStr.length,oL=oldStr.length,frag=document.createDocumentFragment();
  for(var p=0;p<nL;p++){
    var r=nL-1-p,nc=newStr.charAt(p),oc=(r<oL)?oldStr.charAt(oL-1-r):'';
    if(oc===nc)frag.appendChild(staticCell(h,nc));
    else frag.appendChild(rollCell(h,oc,nc,up,Math.min(r,8)*26));}
  pe.textContent='';pe.appendChild(frag);}

/* ── 히어로 업데이트 ── */
function updateHero(px,diff,rate,dir,mktOpen,live){
  var up=dir==='up';                       // up = 전일대비(색·배지용)
  var hero=$('#hero');hero.className='hero'+(up?'':' dn');
  var newStr=fmt(px);
  // 굴림 방향은 '직전 표시값 대비 실제 틱 방향'으로 결정(§12) — 전일대비 부호와 무관.
  if(newStr!==lastPxStr){
    var tickUp = lastPx ? (px >= lastPx) : up;
    rollPrice($('#hPx'),lastPxStr,newStr,tickUp);
  }
  lastPxStr=newStr;lastPx=px;
  var s=up?'+':'';
  $('#hChg').className='h-chg';
  $('#hChg').textContent=(up?'▲ ':diff<0?'▼ ':'')+s+fmt(Math.abs(diff))+'원 ('+(diff>0?'+':'')+fmt(rate,2)+'%)';
  var now=new Date();
  $('#hMeta').textContent=(mktOpen?'실시간':'직전 종가')+' · '+now.toLocaleTimeString('ko-KR',{hour12:false})+' 갱신';
  $('#hBadge').textContent='● '+(live?'실시간':(mktOpen?'스냅샷':'종가'));}

/* ── SSE 구독 ── */
function subscribe(){
  if(es){try{es.close();}catch(_){}}
  lastPxStr='';lastPx=0;
  $('#liveDot').className='dot';$('#liveSt').textContent='연결 중…';
  $('#hCode').textContent=code;$('#hNm').textContent=code;
  loadHistory();
  es=new EventSource('/api/rt/stream?code='+code);
  es.onmessage=function(ev){var d;try{d=JSON.parse(ev.data);}catch(_){return;}
    if(!d.ok){$('#liveSt').textContent=d.msg||'오류';return;}
    lastFrame=d;
    if(d.name){$('#hNm').textContent=d.name;}
    var live=d.market_open&&d.book&&d.book.src==='ws';
    $('#liveDot').className='dot'+(live?' on':'');
    $('#liveSt').textContent=live?'실시간 · WS':(d.market_open?'스냅샷':'장 마감');
    if(d.last>0){updateHero(d.last,d.diff||0,d.rate||0,d.diff>0?'up':d.diff<0?'dn':'flat',d.market_open,live); drawChart();}
    renderOB(d);renderTicker(d.trades||[]);};
  es.onerror=function(){$('#liveDot').className='dot';$('#liveSt').textContent='연결 오류';};}

/* ── 호가창 ── */
function renderOB(d){
  var el=$('#ob');
  if(!d.book||!d.book.asks){el.innerHTML='<div class="note">호가 데이터 없음</div>';return;}
  var asks=d.book.asks||[],bids=d.book.bids||[],mx=1,tq=0;
  asks.concat(bids).forEach(function(x){tq+=(x.qty||0);if((x.qty||0)>mx)mx=x.qty;});
  if(tq===0){                              // 호가 depth 없음(폐장·개장 전) → 종가만 표시
    el.innerHTML='<div class="ob-cur">'+(d.last>0?fmt(d.last)+'원':'—')+'</div>'+
      '<div class="note" style="text-align:center;padding:12px 0;">'+
      (d.market_open?'호가 집계 중…':'장 마감 · 실시간 호가는 장중에만 제공됩니다')+'</div>';
    $('#cttrTxt').textContent='';$('#cttrPct').textContent='';$('#imbFill').style.width='50%';return;}
  var base=d.base||d.last||1;
  var h='';
  for(var i=Math.min(asks.length,5)-1;i>=0;i--){var a=asks[i]||{};h+=obRow('ask',a.px,a.qty,mx,base);}
  h+='<div class="ob-cur">'+fmt(d.last)+'원</div>';
  for(var j=0;j<Math.min(bids.length,5);j++){var b=bids[j]||{};h+=obRow('bid',b.px,b.qty,mx,base);}
  el.innerHTML=h;
  var tot=(d.buy_vol+d.sell_vol)||1,bp=Math.round(d.buy_vol/tot*100);
  $('#imbFill').style.width=bp+'%';
  var cttr=d.cttr||0;
  $('#cttrTxt').textContent='체결강도 '+fmt(cttr,2)+'%';
  $('#cttrPct').textContent='매수 '+bp+'% / 매도 '+(100-bp)+'%';}
function obRow(cls,px,qty,mx,base){
  var pct=base&&px?((px/base-1)*100):0,pctStr=(pct>0?'+':'')+fmt(pct,2)+'%';
  var w=mx?Math.round((qty||0)/mx*100):0;
  return '<div class="ob-row ob-'+cls+'">'+
    '<div class="ob-bg" style="width:'+w+'%"></div>'+
    '<span class="ob-px">'+(px?fmt(px):'—')+'</span>'+
    '<span class="ob-pct">'+pctStr+'</span>'+
    '<span class="ob-q">'+fmt(qty||0)+'</span></div>';}

/* ── 체결 시세 티커 ── */
function renderTicker(trades){
  if(!trades||!trades.length)return;
  var base=lastPx||trades[0].px||1;
  var h=trades.slice(0,18).map(function(t){
    var dir=t.side==='B'?'up':'dn',s=t.side==='B'?'+':'-';
    var pct=(t.px&&base)?((t.px/base-1)*100):0;
    return '<div class="t-row"><span class="tpx '+dir+'">'+fmt(t.px)+'</span>'+
      '<span class="tq">'+fmt(t.vol||0)+'주</span>'+
      '<span class="tch '+dir+'">'+(pct>0?'+':'')+fmt(pct,2)+'%</span></div>';}).join('');
  $('#ticker').innerHTML=h;}

/* ── 차트 (일봉 캔들) ── */
function loadHistory(){
  fetch('/api/rt/history?code='+code+'&days='+chartDays,{cache:'no-store'}).then(function(r){return r.json();})
  .then(function(d){
    histRows=d.rows||[];$('#chartNote').textContent=histRows.length?'일봉 · '+(histRows[0]&&histRows[0].d?histRows[0].d:'')+'~':'차트 데이터 없음';
    drawChart();});}
function drawChart(){
  var cv=$('#cv');if(!cv||!histRows.length)return;
  var dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=cv.clientHeight||280;
  cv.width=W*dpr;cv.height=H*dpr;var x=cv.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,W,H);
  var cs=getComputedStyle(document.documentElement);
  var up=cs.getPropertyValue('--up').trim(),dn=cs.getPropertyValue('--dn').trim();
  var sub=cs.getPropertyValue('--sub').trim(),ln=cs.getPropertyValue('--line').trim();
  var data=histRows;
  var padT=10,padB=22,padR=60,volH=30,gap=5,priceH=H-padT-padB-volH-gap,plotW=W-padR;
  var hi=Math.max.apply(null,data.map(function(r){return r.h;}));
  var lo=Math.min.apply(null,data.map(function(r){return r.l;}));
  if(lastPx>0){hi=Math.max(hi,lastPx);lo=Math.min(lo,lastPx);}
  if(hi<=lo)hi=lo+1;
  var vmx=Math.max.apply(null,data.map(function(r){return r.v;}))||1;
  function Y(p){return padT+(hi-p)/(hi-lo)*priceH;}
  // 그리드 + 우측 눈금
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.lineWidth=.5;x.textAlign='left';
  for(var g=0;g<=3;g++){var pv=lo+(hi-lo)*g/3,gy=Y(pv);
    x.beginPath();x.moveTo(0,gy);x.lineTo(plotW,gy);x.stroke();
    x.fillText(fmt(pv),plotW+5,gy+3);}
  // 현재가 라인
  if(lastPx>0&&lastPx>=lo&&lastPx<=hi){
    var cy2=Y(lastPx);
    x.strokeStyle=up;x.lineWidth=1;x.setLineDash([4,3]);
    x.beginPath();x.moveTo(0,cy2);x.lineTo(plotW,cy2);x.stroke();
    x.setLineDash([]);
    x.fillStyle=up;x.fillText(fmt(lastPx),plotW+5,cy2+3);}
  // 캔들
  var n=data.length,bw=plotW/n,cw=Math.max(1,bw*0.6);
  var volTop=padT+priceH+gap;
  for(var i=0;i<n;i++){var r=data[i],cx2=i*bw+bw/2,rise=r.c>=r.o,col=rise?up:dn;
    x.strokeStyle=col;x.fillStyle=col;x.lineWidth=.8;
    x.beginPath();x.moveTo(cx2,Y(r.h));x.lineTo(cx2,Y(r.l));x.stroke();
    var y1=Y(Math.max(r.o,r.c)),y2=Y(Math.min(r.o,r.c));x.fillRect(cx2-cw/2,y1,cw,Math.max(1,y2-y1));
    var vh=(r.v/vmx)*volH;x.globalAlpha=.45;x.fillRect(cx2-cw/2,volTop+volH-vh,cw,vh);x.globalAlpha=1;}
  // 날짜 라벨
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(n/2),n-1].forEach(function(ix){var r=data[ix];if(!r||!r.d)return;
    var lb=String(r.d).replace(/(\d{4})\.(\d{2})\.(\d{2})/,'$2.$3');
    x.fillText(lb,Math.min(plotW-24,Math.max(24,ix*bw+bw/2)),H-5);});}
$('#chartSeg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
  chartDays=Number(b.dataset.d);this.querySelectorAll('button').forEach(function(z){z.classList.toggle('on',z===b);});loadHistory();});

/* ── 수급 ── */
function loadFlow(){fetch('/api/rt/flows?code='+code+'&mkt=1',{cache:'no-store'}).then(function(r){return r.json();})
  .then(function(d){
    var el=$('#flowWrap');
    if(!d.ok){el.innerHTML='<div class="note">'+(d.needs_key?'KIS 키 필요':'당일 수급은 장 종료 후 제공')+'</div>';return;}
    var inv=d.investor||[];
    if(!inv.length){el.innerHTML='<div class="note">수급 데이터 없음</div>';return;}
    // 최근 1일치 바 차트
    var last=inv[0],mx=Math.max(Math.abs(last.frgn||0),Math.abs(last.orgn||0),Math.abs(last.prsn||0))||1;
    function frow(lbl,v){var up=v>0,pct=Math.abs(v)/mx*100;
      return '<div class="flow-row"><span class="fn">'+lbl+'</span>'+
        '<span class="fv '+(up?'up':'dn')+'">'+(v>0?'+':'')+fmt(v)+'</span>'+
        '<div class="flow-bar-wrap"><div class="flow-bar" style="width:'+pct+'%;background:'+(up?'var(--up)':'var(--dn)')+'"></div></div></div>';}
    el.innerHTML='<div class="note" style="margin-bottom:6px;">'+esc(last.date||'당일')+'</div>'+
      frow('외국인',last.frgn||0)+frow('기관',last.orgn||0)+frow('개인',last.prsn||0);});}

/* ── 스크리너 ── */
function loadScr(){fetch('/api/rt/screener?mkt=J&blng='+blng,{cache:'no-store'}).then(function(r){return r.json();})
  .then(function(d){
    var el=$('#scrWrap');
    if(!d.ok){el.innerHTML='<div class="note">'+(d.needs_key?'KIS 키 필요 — 라이브 순위':'데이터 없음')+'</div>';return;}
    if(!d.rows.length){el.innerHTML='<div class="note">데이터 없음</div>';return;}
    var h='<table class="scr-table"><thead><tr><th>종목</th><th>현재가</th><th>등락%</th><th>거래대금(억)</th></tr></thead><tbody>';
    d.rows.forEach(function(o){var up2=o.chg>0,dn2=o.chg<0;
      h+='<tr data-c="'+o.code+'"><td>'+esc(o.name||o.code)+'</td><td>'+fmt(o.price)+'</td>'+
        '<td class="'+(up2?'up':dn2?'dn':'')+'">'+(o.chg>0?'+':'')+fmt(o.chg,2)+'%</td>'+
        '<td>'+fmt(o.amt/1e8,1)+'</td></tr>';});
    el.innerHTML=h+'</tbody></table>';
    el.querySelectorAll('tr[data-c]').forEach(function(tr){tr.onclick=function(){setCode(tr.dataset.c);};});});}
$('#blngSeg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
  blng=b.dataset.b;this.querySelectorAll('button').forEach(function(z){z.classList.toggle('on',z===b);});loadScr();});

/* ── 페이퍼 트레이딩 ── */
function loadPaper(){fetch('/api/paper/state',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
  if(!d.ok)return;
  var pc=d.pnl_total>0?'pnl-pos':d.pnl_total<0?'pnl-neg':'';
  $('#pTiles').innerHTML=
    ptile('평가자산',fmt(d.equity)+'원','')+ptile('현금',fmt(d.cash)+'원','')+
    ptile('주식평가',fmt(d.market_value)+'원','')+ptile('총손익',(d.pnl_total>0?'+':'')+fmt(d.pnl_total)+'원',pc);
  var h='';
  if(d.positions.length){
    h+='<table class="pos-table"><thead><tr><th>종목</th><th>수량</th><th>평단</th><th>손익</th></tr></thead><tbody>';
    d.positions.forEach(function(p){var c=p.pnl>0?'up':p.pnl<0?'dn':'';
      h+='<tr data-c="'+p.code+'"><td>'+esc(p.name||p.code)+'</td><td>'+fmt(p.qty)+'</td><td>'+fmt(p.avg)+'</td>'+
        '<td class="'+c+'">'+(p.pnl>0?'+':'')+fmt(p.pnl)+'</td></tr>';});
    h+='</tbody></table>';}
  else h='<div class="paper-empty">보유 종목 없음</div>';
  $('#pPos').innerHTML=h;
  $('#pPos').querySelectorAll('tr[data-c]').forEach(function(tr){tr.onclick=function(){setCode(tr.dataset.c);};});})}
function ptile(k,v,vc){return '<div class="ptile"><div class="pk">'+k+'</div><div class="pv '+vc+'">'+v+'</div></div>';}
function order(side){var qty=Number($('#pQty').value)||0;if(!qty)return;
  $('#pMsg').textContent='주문 중…';
  fetch('/api/paper/order',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({code:code,side:side,qty:qty,name:code})}).then(function(r){return r.json();}).then(function(d){
    if(d.ok){$('#pMsg').textContent=(side==='BUY'?'▲ 매수':'▼ 매도')+' 체결 '+fmt(d.fill_px)+'원 × '+fmt(d.qty)+'주';loadPaper();}
    else{$('#pMsg').textContent='⚠ '+(d.msg||'실패');$('#pMsg').className='pmsg err-msg';}});}
$('#pBuy').onclick=function(){order('BUY');};
$('#pSell').onclick=function(){order('SELL');};
$('#pReset').onclick=function(){if(confirm('페이퍼 계좌를 초기화할까요?'))
  fetch('/api/paper/reset',{method:'POST'}).then(function(){loadPaper();});};

/* ── 종목 전환 ── */
function setCode(c){c=(c||'').trim();if(!/^\d{6}$/.test(c))return;code=c;$('#sym').value=c;subscribe();loadFlow();}
$('#go').onclick=function(){setCode($('#sym').value);};
$('#sym').addEventListener('keydown',function(e){if(e.key==='Enter')setCode(this.value);});

/* ── 시작 ── */
/* ── 너비 드래그 리사이저 (좌측 차트영역 ↔ 우측 호가/페이퍼) ── */
(function(){var rsz=document.getElementById('rsz'),main=document.querySelector('.main'),
   rg=document.querySelector('.right-group');if(!rsz||!main||!rg)return;
 var drag=false,sx=0,sw=0;
 rsz.addEventListener('mousedown',function(e){drag=true;sx=e.clientX;sw=rg.getBoundingClientRect().width;
   rsz.classList.add('drag');document.body.style.cursor='col-resize';document.body.style.userSelect='none';e.preventDefault();});
 window.addEventListener('mousemove',function(e){if(!drag)return;
   var w=Math.max(330,Math.min(660,sw-(e.clientX-sx)));main.style.setProperty('--rgw',w+'px');});
 window.addEventListener('mouseup',function(){if(!drag)return;drag=false;rsz.classList.remove('drag');
   document.body.style.cursor='';document.body.style.userSelect='';try{drawChart();}catch(e){}});
})();
subscribe();loadScr();loadFlow();loadPaper();
setInterval(function(){if(!document.hidden)loadScr();},5000);
setInterval(function(){if(!document.hidden)loadFlow();},15000);
setInterval(function(){if(!document.hidden)loadPaper();},4000);
window.addEventListener('resize',function(){drawChart();});
</script></body></html>
"""

_WORLD_DETAIL_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="world-detail"><head><meta charset="utf-8">
<title>세계 시장 상세</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f4f5f9;--card:rgba(255,255,255,.86);--ink:#1d1d1f;--sub:rgba(60,60,67,.6);
 --line:rgba(60,60,67,.12);--row:rgba(10,132,255,.06);--up:#FF3B30;--down:#2E75B6;--accent:#0A84FF;}
html.dark{--bg:#0b0f1a;--card:rgba(28,30,38,.78);--ink:#eef3ff;--sub:#9aa6bd;--line:rgba(255,255,255,.1);
 --row:rgba(90,166,255,.1);--up:#FF453A;--down:#64B5FF;--accent:#0A84FF;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
 background:var(--bg);color:var(--ink);padding:20px 24px 32px;transition:background .4s ease;
 -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
.hero{display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;margin-bottom:14px;}
.hero .nm{font-size:24px;font-weight:800;letter-spacing:-.02em;}
.hero .px{font-size:30px;font-weight:800;margin-left:auto;}
.hero .ch{font-size:14px;font-weight:700;margin-bottom:5px;}
.up{color:var(--up);} .down{color:var(--down);} .flat{color:var(--sub);}
.card{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(30px);
 backdrop-filter:saturate(180%) blur(30px);border:.5px solid var(--line);border-radius:16px;
 padding:16px 18px;box-shadow:0 14px 40px rgba(0,0,0,.07);margin-bottom:14px;}
h3{margin:0 0 10px;font-size:13px;font-weight:700;}
.seg{display:inline-flex;border:.5px solid var(--line);border-radius:9px;overflow:hidden;}
.seg button{background:transparent;border:0;color:var(--sub);font:inherit;font-size:12px;padding:5px 12px;cursor:pointer;}
.seg button.on{background:var(--accent);color:#fff;}
canvas{width:100%;height:360px;display:block;}
.tiles{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;}
.tile{flex:1;min-width:96px;background:var(--row);border-radius:12px;padding:10px 12px;}
.tile .k{font-size:11px;color:var(--sub);} .tile .v{font-size:16px;font-weight:700;margin-top:2px;}
table{width:100%;border-collapse:collapse;font-size:12.5px;}
th,td{padding:7px 8px;border-bottom:.5px solid var(--line);text-align:right;white-space:nowrap;}
th:first-child,td:first-child{text-align:left;}
th{color:var(--sub);font-weight:600;font-size:11px;}
.state{color:var(--sub);font-size:14px;padding:24px 2px;} .err{color:var(--up);}
.note{font-size:11.5px;color:var(--sub);margin-top:8px;}
</style></head><body>
<div id="state" class="state">차트 데이터를 불러오는 중…</div>
<div id="body" style="display:none;">
  <div class="hero"><span class="nm" id="nm"></span><span class="px" id="px"></span><span class="ch" id="ch"></span></div>
  <div class="tiles" id="tiles"></div>
  <section class="card">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
      <h3 style="margin:0;" id="ctitle">차트</h3>
      <div class="seg" id="seg" style="margin-left:auto;display:none;">
        <button data-p="day" class="on">일봉</button><button data-p="week">주봉</button><button data-p="month">월봉</button></div>
    </div>
    <canvas id="cv"></canvas>
    <div class="note" id="cnote"></div>
  </section>
  <section class="card" id="tblCard" style="display:none;"><h3>최근 일자별</h3><div id="tbl"></div></section>
</div>
<script>
var $=function(s){return document.querySelector(s);};
var P=new URLSearchParams(location.search), kind=P.get('kind')||'index',
    code=P.get('code')||'', name=P.get('name')||code, period='day', rows=[];
function setTheme(d){document.documentElement.classList.toggle('dark',!!d);draw();}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)setTheme(e.data.kmkt==='dark');});
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fmt(n,d){return (Number(n)||0).toLocaleString('ko-KR',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function load(){fetch('/api/world/chart?kind='+kind+'&code='+encodeURIComponent(code)+'&period='+period,{cache:'no-store'})
  .then(function(r){return r.json();}).then(function(d){
    if(!d.ok||!d.rows.length){$('#state').className='state err';$('#state').textContent='차트 데이터를 가져올 수 없습니다.';return;}
    rows=d.rows;render();
  }).catch(function(){$('#state').className='state err';$('#state').textContent='네트워크 오류';});}
function render(){
  $('#state').style.display='none';$('#body').style.display='block';
  document.title=name+' — 세계 시장';
  $('#nm').textContent=name;
  var last=rows[rows.length-1],prev=rows[rows.length-2]||last;
  var c=last.c,pc=kind==='fx'?(c-(prev.c||c)):(c-(prev.c||c));
  var dirc=c>prev.c?'up':(c<prev.c?'down':'flat'),s=dirc==='up'?'+':(dirc==='down'?'-':'');
  $('#px').textContent=fmt(c);
  $('#ch').className='ch '+dirc;
  var pctv=prev.c?Math.abs(pc)/prev.c*100:0;
  $('#ch').textContent=s+fmt(Math.abs(pc))+' ('+s+fmt(pctv)+'%)';
  function ret(n){var i=rows.length-1-n;if(i<0)return null;return (c/rows[i].c-1)*100;}
  var defs=kind==='fx'?[['1주',5],['1개월',21],['3개월',63],['6개월',126]]:
    (period==='day'?[['1주',5],['1개월',21],['3개월',63]]:period==='week'?[['1개월',4],['3개월',13],['1년',52]]:[['1년',12],['3년',36],['5년',60]]);
  $('#tiles').innerHTML=defs.map(function(df){var v=ret(df[1]);
    var cls=v==null?'':(v>0?'up':v<0?'down':'');
    return '<div class="tile"><div class="k">'+df[0]+'</div><div class="v '+cls+'">'+(v==null?'—':((v>0?'+':'')+fmt(v)+'%'))+'</div></div>';}).join('');
  if(kind==='index'){$('#seg').style.display='';$('#ctitle').textContent='🕯️ 가격 차트';
    $('#cnote').textContent='캔들 상승 ● 하락 ● · 네이버 세계지수';}
  else{$('#ctitle').textContent='📈 환율 추이 (약 14개월)';$('#cnote').textContent='하나은행 고시 환율 · 네이버';
    var tb='<table><thead><tr><th>일자</th><th>매매기준율</th><th>전일대비</th><th>현찰 살 때</th><th>현찰 팔 때</th></tr></thead><tbody>';
    rows.slice(-15).reverse().forEach(function(r){var cl=r.dir==='up'?'up':(r.dir==='down'?'down':'');
      var sg=r.dir==='up'?'+':(r.dir==='down'?'-':'');
      tb+='<tr><td>'+esc(r.d)+'</td><td>'+fmt(r.c)+'</td><td class="'+cl+'">'+sg+fmt(Math.abs(r.chg))+' ('+sg+fmt(Math.abs(r.pct))+'%)</td>'+
        '<td>'+esc(r.cash_buy||'—')+'</td><td>'+esc(r.cash_sell||'—')+'</td></tr>';});
    $('#tbl').innerHTML=tb+'</tbody></table>';$('#tblCard').style.display='';}
  draw();
}
function draw(){var cv=$('#cv');if(!cv||!rows.length)return;var dpr=window.devicePixelRatio||1;
  var W=cv.clientWidth,H=360;cv.width=W*dpr;cv.height=H*dpr;var x=cv.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,W,H);
  var cs=getComputedStyle(document.documentElement);
  var up=cs.getPropertyValue('--up').trim(),dn=cs.getPropertyValue('--down').trim(),
      sub=cs.getPropertyValue('--sub').trim(),ln=cs.getPropertyValue('--line').trim(),ac=cs.getPropertyValue('--accent').trim();
  var data=rows.slice(-130);
  var padT=12,padB=20,padR=64,pw=W-padR,ph=H-padT-padB;
  var hi,lo;
  if(kind==='index'){hi=Math.max.apply(null,data.map(function(r){return r.h;}));lo=Math.min.apply(null,data.map(function(r){return r.l;}));}
  else{hi=Math.max.apply(null,data.map(function(r){return r.c;}));lo=Math.min.apply(null,data.map(function(r){return r.c;}));}
  if(hi<=lo)hi=lo+1e-6;
  function Y(p){return padT+(hi-p)/(hi-lo)*ph;}
  x.strokeStyle=ln;x.fillStyle=sub;x.font='10px -apple-system';x.lineWidth=.5;x.textAlign='left';
  for(var g=0;g<=4;g++){var v=lo+(hi-lo)*g/4,gy=Y(v);
    x.beginPath();x.moveTo(0,gy);x.lineTo(pw,gy);x.stroke();x.fillText(fmt(v),pw+6,gy+3);}
  var n=data.length,bw=pw/n;
  if(kind==='index'){var cw=Math.max(1,bw*0.62);
    for(var i=0;i<n;i++){var r=data[i],cx2=i*bw+bw/2,rise=r.c>=r.o,col=rise?up:dn;
      x.strokeStyle=col;x.fillStyle=col;x.lineWidth=1;
      x.beginPath();x.moveTo(cx2,Y(r.h));x.lineTo(cx2,Y(r.l));x.stroke();
      var y1=Y(Math.max(r.o,r.c)),y2=Y(Math.min(r.o,r.c));x.fillRect(cx2-cw/2,y1,cw,Math.max(1,y2-y1));}}
  else{x.strokeStyle=ac;x.lineWidth=2;x.beginPath();
    data.forEach(function(r,i){var px=i*bw+bw/2,py=Y(r.c);if(i)x.lineTo(px,py);else x.moveTo(px,py);});x.stroke();
    x.globalAlpha=.12;x.lineTo((n-1)*bw+bw/2,Y(lo));x.lineTo(bw/2,Y(lo));x.closePath();x.fillStyle=ac;x.fill();x.globalAlpha=1;}
  x.fillStyle=sub;x.textAlign='center';
  [0,Math.floor(n/2),n-1].forEach(function(ix){var r=data[ix];if(!r||!r.d)return;
    var lb=String(r.d).replace(/(\d{4})(\d{2})(\d{2})/,'$1.$2.$3');
    x.fillText(lb,Math.min(pw-34,Math.max(34,ix*bw+bw/2)),H-5);});
}
$('#seg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
  period=b.dataset.p;this.querySelectorAll('button').forEach(function(z){z.classList.toggle('on',z===b);});load();});
window.addEventListener('resize',draw);
if(!code){$('#state').textContent='코드가 없습니다.';}else{load();}
</script></body></html>
"""

_WORLD_HTML = r"""<!DOCTYPE html>
<html lang="ko" data-kind="world"><head><meta charset="utf-8">
<title>세계 시장</title><link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<script src="/plotly.js"></script>
<style>
:root{--bg:#f4f5f9;--card:rgba(255,255,255,.86);--ink:#1d1d1f;--sub:rgba(60,60,67,.6);
 --line:rgba(60,60,67,.12);--row:rgba(10,132,255,.06);--up:#FF3B30;--down:#2E75B6;--accent:#0A84FF;}
html.dark{--bg:#0b0f1a;--card:rgba(28,30,38,.78);--ink:#eef3ff;--sub:#9aa6bd;--line:rgba(255,255,255,.1);
 --row:rgba(90,166,255,.1);--up:#FF453A;--down:#64B5FF;--accent:#0A84FF;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
 background:var(--bg);color:var(--ink);padding:18px 20px;transition:background .4s ease;
 -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
.hd{display:flex;align-items:baseline;gap:10px;margin-bottom:4px;}
h2{margin:0;font-size:20px;font-weight:700;letter-spacing:-.02em;}
.asof{font-size:12px;color:var(--sub);margin-left:auto;}
.lead{color:var(--sub);font-size:13px;margin:0 0 14px;}
h3{font-size:13px;font-weight:700;color:var(--sub);margin:18px 2px 10px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(176px,1fr));gap:12px;}
.cell{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(30px);
 backdrop-filter:saturate(180%) blur(30px);border:.5px solid var(--line);border-radius:14px;
 padding:13px 15px;box-shadow:0 10px 30px rgba(0,0,0,.06);transition:transform .15s ease;}
.cell:hover{transform:translateY(-2px);}
.cell.click{cursor:pointer;}
.cell.click:hover{box-shadow:0 14px 36px rgba(0,0,0,.12);}
.cell .rg{font-size:11px;color:var(--sub);}
.cell .nm{font-size:14px;font-weight:600;margin:3px 0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.cell .pr{font-size:20px;font-weight:700;letter-spacing:-.02em;}
.cell .ch{font-size:12.5px;font-weight:600;margin-top:3px;}
.up{color:var(--up);} .down{color:var(--down);} .flat{color:var(--sub);}
.tag{display:inline-flex;align-items:center;gap:4px;font-size:10px;color:var(--sub);border:.5px solid var(--line);
 border-radius:6px;padding:1px 6px;margin-left:6px;vertical-align:middle;}
.tag .sdot{width:6px;height:6px;border-radius:50%;background:#9aa0ab;}
.tag .sdot.open{background:#34C759;animation:wpulse 1.6s ease-in-out infinite;}
.tag .sdot.pre{background:#FF9F0A;} .tag .sdot.post{background:#5AADFF;}
@keyframes wpulse{0%{box-shadow:0 0 0 0 rgba(52,199,89,.5);}70%{box-shadow:0 0 0 5px rgba(52,199,89,0);}100%{box-shadow:0 0 0 0 rgba(52,199,89,0);}}
@media (prefers-reduced-motion:reduce){.tag .sdot.open{animation:none;}}
.state{color:var(--sub);font-size:14px;padding:30px 2px;}
/* 미국 마켓맵 (작업1) */
.maprow{display:flex;align-items:center;gap:10px;margin:18px 2px 10px;}
.maprow h3{margin:0;font-size:13px;font-weight:700;color:var(--sub);}
.mapseg{display:inline-flex;background:rgba(118,118,128,.14);border-radius:9px;padding:2px;}
.mapseg button{border:0;background:transparent;font:inherit;font-size:12px;font-weight:600;color:var(--sub);
 padding:5px 12px;border-radius:7px;cursor:pointer;transition:all .15s;}
.mapseg button.on{background:#fff;color:var(--accent);box-shadow:0 1px 3px rgba(0,0,0,.14);}
html.dark .mapseg{background:rgba(120,120,128,.28);} html.dark .mapseg button.on{background:#3a3a3e;color:#64b5ff;}
.maplegend{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:11px;color:var(--sub);font-weight:500;}
.maplegend i{display:inline-block;width:42px;height:9px;border-radius:2px;
 background:linear-gradient(90deg,#cf3a3a,#4a5160,#2e9e5b);}
#usMap{width:100%;height:540px;border-radius:14px;overflow:hidden;background:var(--card);}
.mapempty{color:var(--sub);font-size:13px;padding:60px 0;text-align:center;}
/* 3뷰 토글 + 지수카드(스파크라인) + KPI + 종목리스트 (네이버식, 작업1) */
.vtabs{display:flex;align-items:center;gap:16px;margin:0 0 2px;}
.vtab{display:inline-flex;align-items:center;gap:6px;font-size:18px;font-weight:700;color:var(--sub);
 cursor:pointer;padding:2px 0;border-bottom:2.5px solid transparent;transition:color .15s,border-color .15s;}
.vtab:hover{color:var(--ink);} .vtab.on{color:var(--ink);border-bottom-color:var(--ink);}
.idxrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(420px,100%),1fr));gap:14px;margin:10px 0 8px;}
.icard{background:var(--card);-webkit-backdrop-filter:saturate(180%) blur(30px);backdrop-filter:saturate(180%) blur(30px);
 border:.5px solid var(--line);border-radius:16px;padding:16px 18px 14px;box-shadow:0 8px 26px rgba(0,0,0,.06);
 min-width:0;overflow:hidden;}
.icard .ih{display:flex;align-items:center;gap:6px;font-size:15px;font-weight:700;min-width:0;}
.icard .ih .nmtxt{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
/* 카드별 기간 토글(작업3) */
.csg{display:inline-flex;background:rgba(118,118,128,.14);border-radius:8px;padding:2px;margin-left:auto;flex:0 0 auto;}
.csg button{border:0;background:transparent;font:inherit;font-size:11px;font-weight:600;color:var(--sub);
 padding:3px 9px;border-radius:6px;cursor:pointer;transition:all .15s;}
.csg button.on{background:#fff;color:var(--accent);box-shadow:0 1px 2px rgba(0,0,0,.12);}
html.dark .csg{background:rgba(120,120,128,.28);} html.dark .csg button.on{background:#3a3a3e;color:#64b5ff;}
.icard .ih .rg{font-size:12px;color:var(--sub);font-weight:600;}
.icard .ist{display:inline-flex;align-items:center;gap:4px;font-size:11px;color:var(--sub);font-weight:600;margin-left:4px;}
.icard .ist .sdot{width:6px;height:6px;border-radius:50%;background:#9aa0ab;}
.icard .ist .sdot.open{background:#34C759;} .icard .ist .sdot.pre{background:#FF9F0A;} .icard .ist .sdot.post{background:#5AADFF;}
.icard .ivrow{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-top:7px;}
.icard .iv{font-size:27px;font-weight:800;letter-spacing:-.02em;}
.icard .ic{font-size:14px;font-weight:700;}
.icard .ispark{width:100%;max-width:100%;height:120px;margin:8px 0 4px;overflow:hidden;}
.icard .ispark .plot-container,.icard .ispark .svg-container{max-width:100%!important;}
.icard .iinfo{display:grid;grid-template-columns:1fr 1fr;gap:6px 22px;border-top:.5px solid var(--line);padding-top:11px;margin-top:6px;}
.icard .iinfo .ilab{font-size:11.5px;color:var(--sub);font-weight:700;margin-bottom:3px;}
.icard .iinfo .irow{display:flex;justify-content:space-between;font-size:12.5px;padding:1.5px 0;}
.icard .iinfo .irow span{color:var(--sub);} .icard .iinfo .irow b{font-weight:700;color:var(--ink);}
.kpirow{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin:8px 0 4px;}
.kcard{background:var(--card);border:.5px solid var(--line);border-radius:13px;padding:11px 13px;box-shadow:0 6px 18px rgba(0,0,0,.05);min-width:0;}
.kcard .kn{font-size:11.5px;color:var(--sub);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kcard .kv{font-size:17px;font-weight:800;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.kcard .kc{font-size:11.5px;font-weight:600;margin-top:2px;}
.lhead{font-size:15px;font-weight:800;margin:20px 2px 8px;}
.wtbl{width:100%;border-collapse:collapse;font-size:13px;}
.wtbl th,.wtbl td{padding:10px 8px;border-bottom:.5px solid var(--line);text-align:right;white-space:nowrap;}
.wtbl th{color:var(--sub);font-weight:600;font-size:11.5px;}
.wtbl th:nth-child(2),.wtbl td:nth-child(2){text-align:left;}
.wtbl .rk{color:var(--sub);width:30px;}
.wtbl tbody tr{cursor:pointer;transition:background .12s;} .wtbl tbody tr:hover{background:var(--row);}
.gnote{color:var(--sub);font-size:13px;line-height:1.6;padding:26px 16px;background:var(--card);
 border:.5px solid var(--line);border-radius:14px;text-align:center;}
</style></head><body>
<div class="vtabs" id="vtabs">
  <span class="vtab" data-v="kr">🇰🇷 국내</span>
  <span class="vtab on" data-v="us">🇺🇸 미국</span>
  <span class="vtab" data-v="global">🌍 글로벌</span>
  <span class="asof" id="asof"></span>
</div>
<p class="lead">국가별 현지 시간 기준 · 상승 <span class="up">●</span> / 하락 <span class="down">●</span></p>
<div id="state" class="state">세계 시장 데이터를 불러오는 중…</div>
<div id="body" style="display:none;">
  <div class="idxrow" id="idxRow"></div>
  <div class="kpirow" id="kpiRow"></div>
  <div id="mapWrap" style="display:none;">
    <div class="maprow">
      <h3 id="mapTitle" style="margin:0;">🗺️ 마켓맵</h3>
      <div class="mapseg" id="mapSeg"></div>
      <span class="maplegend" id="mapLegend">하락 <i></i> 상승</span>
    </div>
    <div id="theMap"><div class="mapempty">마켓맵 불러오는 중…</div></div>
  </div>
  <div id="listWrap"></div>
</div>
<script>
var $=function(s){return document.querySelector(s);};
function setTheme(d){document.documentElement.classList.toggle('dark',!!d);redrawSparks();}
window.addEventListener('message',function(e){if(e.data&&e.data.kmkt)setTheme(e.data.kmkt==='dark');});
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fmtN(n,d){return (Number(n)||0).toLocaleString('en-US',{minimumFractionDigits:(d==null?2:d),maximumFractionDigits:(d==null?2:d)});}
function usMcap(b){b=Number(b)||0;return b>=1000?('$'+(b/1000).toFixed(2)+'T'):('$'+b+'B');}
function krMcap(eok){eok=Number(eok)||0;return eok>=10000?(fmtN(eok/10000,1)+'조'):(fmtN(eok,0)+'억');}
var view='us', mapExch='all', mapMkt='kospi', lastCards=[];

function hexRgba(hex,a){hex=String(hex||'').trim().replace('#','');if(hex.length===3)hex=hex.replace(/(.)/g,'$1$1');
  if(hex.length<6)return 'rgba(136,136,136,'+a+')';
  return 'rgba('+parseInt(hex.substr(0,2),16)+','+parseInt(hex.substr(2,2),16)+','+parseInt(hex.substr(4,2),16)+','+a+')';}
function fmtTick(v){return (Number(v)||0).toLocaleString('en-US',{maximumFractionDigits:2});}
function spark(el,sp){if(!el||!window.Plotly)return;
  sp=sp||{};var C=(sp.c||[]),O=(sp.o||[]),H=(sp.h||[]),L=(sp.l||[]),dts=(sp.d||[]);
  if(C.length<2){el.innerHTML='';return;}
  var cs=getComputedStyle(document.documentElement),sub=(cs.getPropertyValue('--sub')||'#888').trim();
  // 국내 종목 candle_chart() 와 동일: 상승=빨강 #C0392B / 하락=파랑 #2E75B6 (캔들)
  var up='#C0392B',dn='#2E75B6';
  var xs=C.map(function(_v,i){return i;});
  function dlab(s){s=String(s||'');return s.length===8?(s.slice(4,6)+'.'+s.slice(6,8)):s;}
  var tv=[0,Math.floor(C.length/2),C.length-1],tt=tv.map(function(ix){return dlab(dts[ix]);});
  var lo=Math.min.apply(null,L.filter(function(v){return v!=null;})),
      hi=Math.max.apply(null,H.filter(function(v){return v!=null;})),pad=(hi-lo)*0.08||1;
  Plotly.react(el,[{x:xs,open:O,high:H,low:L,close:C,type:'candlestick',
    increasing:{line:{color:up,width:1},fillcolor:up},decreasing:{line:{color:dn,width:1},fillcolor:dn},
    hoverinfo:'skip'}],
    {margin:{t:8,b:20,l:0,r:58},height:120,
     xaxis:{tickmode:'array',tickvals:tv,ticktext:tt,showgrid:false,zeroline:false,rangeslider:{visible:false},
            tickfont:{size:9.5,color:sub},fixedrange:true,showline:false,type:'linear'},
     yaxis:{side:'right',nticks:3,showgrid:true,gridcolor:hexRgba(sub,0.12),zeroline:false,
            tickfont:{size:9.5,color:sub},fixedrange:true,range:[lo-pad,hi+pad],tickformat:',.0f'},
     paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',showlegend:false},
    {displayModeBar:false,staticPlot:true,responsive:true});}
function redrawSparks(){lastCards.forEach(function(o,i){spark(document.querySelector('#idxRow .ispark[data-i="'+i+'"]'),o.spark);});}
function loadCardSpark(i,per){var o=lastCards[i];if(!o)return;o.period=per;
  var el=document.querySelector('#idxRow .ispark[data-i="'+i+'"]');if(el)el.style.opacity='.45';
  var kind=(view==='kr')?'dom':'index';
  fetch('/api/world/spark?kind='+kind+'&code='+encodeURIComponent(o.code||'')+'&period='+per,{cache:'no-store'})
    .then(function(r){return r.json();}).then(function(d){if(d&&d.c&&d.c.length)o.spark=d;spark(el,o.spark);if(el)el.style.opacity='1';})
    .catch(function(){if(el)el.style.opacity='1';});}
function bindSparkSegs(){document.querySelectorAll('#idxRow .csg').forEach(function(sg){
  sg.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
    var i=+sg.dataset.i;sg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});
    loadCardSpark(i,b.dataset.p);});});});}
function sparkSeg(i,per){per=per||'day';var opts=[['day','일'],['week','주'],['month','월']];
  return '<div class="csg" data-i="'+i+'">'+opts.map(function(p){
    return '<button data-p="'+p[0]+'"'+(p[0]===per?' class="on"':'')+'>'+p[1]+'</button>';}).join('')+'</div>';}
function icard(o,i){var sign=o.dir==='up'?'▲ ':(o.dir==='down'?'▼ ':'');var psg=o.dir==='up'?'+':'';
  var info=o.info||{};
  var st=o.status?'<span class="ist"><span class="sdot '+esc(o.phase||'')+'"></span>'+esc(o.status)+'</span>':'';
  function row(lab,val,cls){return '<div class="irow"><span>'+lab+'</span><b'+(cls?' class="'+cls+'"':'')+'>'+esc(val||'-')+'</b></div>';}
  return '<div class="icard"><div class="ih"><span class="rg">'+esc(o.region||'')+'</span> '+
    '<span class="nmtxt">'+esc(o.name)+'</span>'+st+sparkSeg(i,o.period)+'</div>'+
    '<div class="ivrow"><span class="iv">'+esc(o.value)+'</span>'+
      '<span class="ic '+o.dir+'">'+sign+esc(o.chg)+' ('+psg+esc(o.pct)+'%)</span></div>'+
    '<div class="ispark" data-i="'+i+'"></div>'+
    '<div class="iinfo"><div class="icol"><div class="ilab">52주 기준</div>'+
      row('최고',info.hi52)+row('최저',info.lo52)+'</div>'+
      '<div class="icol">'+row('전일',info.prev)+row('고가',info.high,'up')+row('저가',info.low,'down')+'</div>'+
    '</div></div>';}
function kcard(o){var sign=o.dir==='up'?'+':(o.dir==='down'?'':'');
  return '<div class="kcard"><div class="kn">'+esc(o.name)+'</div><div class="kv">'+esc(o.value)+'</div>'+
    '<div class="kc '+o.dir+'">'+sign+esc(o.pct)+'%</div></div>';}
var usFilt='actives';
function usRowsHtml(rows,filt){
  var isTurn=(filt==='actives');
  var h='<table class="wtbl"><thead><tr><th class="rk">#</th><th>종목명</th><th>현재가</th><th>전일대비</th>';
  h+=(filt==='mcap')?'<th>업종</th><th>시가총액</th>':(isTurn?'<th>거래대금</th><th>거래량</th>':'<th>거래소</th>');
  h+='</tr></thead><tbody>';
  rows.forEach(function(r,i){var dirc=r.pct>0?'up':(r.pct<0?'down':'flat'),sg=r.pct>0?'+':'';
    h+='<tr data-sym="'+esc(r.name||'')+'"><td class="rk">'+(i+1)+'</td><td>'+esc(r.name)+
       (r.company?' <span style="color:var(--sub);font-size:11px;">'+esc(r.company)+'</span>':'')+'</td>'+
       '<td>$'+fmtN(r.price)+'</td><td class="'+dirc+'">'+sg+fmtN(r.pct)+'%</td>';
    if(filt==='mcap'){h+='<td>'+esc(r.sector||'')+'</td><td>'+usMcap((r.mcap||0)/1e9)+'</td>';}
    else if(isTurn){h+='<td>'+usMcap((r.turnover||0)/1e9)+'</td><td>'+fmtN(r.volume,0)+'</td>';}
    else{h+='<td>'+esc(r.exch||'')+'</td>';}
    h+='</tr>';});
  return h+'</tbody></table>';}
function bindUsRows(){document.querySelectorAll('#usListBody tbody tr').forEach(function(tr){tr.addEventListener('click',function(){
  try{if(tr.dataset.sym&&window.parent&&window.parent.miOpenUrlTab)window.parent.miOpenUrlTab('ov:'+tr.dataset.sym,{url:'/overseas?symb='+encodeURIComponent(tr.dataset.sym),title:tr.dataset.sym+' 🌎',icon:'🌎',loading:'해외 종목 불러오는 중…'});}catch(e){}});});}
function usLoad(f){usFilt=f;var b=document.getElementById('usListBody');if(b)b.innerHTML='<div class="gnote">불러오는 중…</div>';
  fetch('/api/us_list?filter='+f,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    var b=document.getElementById('usListBody');if(!b)return;
    if(!d.rows||!d.rows.length){b.innerHTML='<div class="gnote">데이터가 없습니다.</div>';return;}
    b.innerHTML=usRowsHtml(d.rows,f);bindUsRows();}).catch(function(){var b=document.getElementById('usListBody');if(b)b.innerHTML='<div class="gnote">불러오지 못했습니다.</div>';});}
var glCountry='cn';
function glRowsHtml(rows,ccy){
  var h='<table class="wtbl"><thead><tr><th class="rk">#</th><th>종목명</th><th>현재가</th><th>전일대비</th></tr></thead><tbody>';
  rows.forEach(function(r,i){var dirc=r.pct>0?'up':(r.pct<0?'down':'flat'),sg=r.pct>0?'+':'';
    h+='<tr data-sym="'+esc(r.symb||'')+'" data-excd="'+esc(r.excd||'')+'"><td class="rk">'+(i+1)+'</td>'+
       '<td>'+esc(r.name)+' <span style="color:var(--sub);font-size:11px;">'+esc(r.symb)+'</span></td>'+
       '<td>'+esc(r.ccy||'')+fmtN(r.price,2)+'</td><td class="'+dirc+'">'+sg+fmtN(r.pct)+'%</td></tr>';});
  return h+'</tbody></table>';}
function glLoad(country){glCountry=country;var b=document.getElementById('glBody');if(b)b.innerHTML='<div class="gnote">불러오는 중…</div>';
  fetch('/api/global_list?country='+country,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    var b=document.getElementById('glBody');if(!b)return;
    if(!d.rows||!d.rows.length){b.innerHTML='<div class="gnote">현재 해당 시장 데이터를 가져오지 못했습니다 (현지 장 시간 외일 수 있음).</div>';return;}
    b.innerHTML=glRowsHtml(d.rows,d.ccy);
    b.querySelectorAll('tbody tr').forEach(function(tr){tr.addEventListener('click',function(){try{
      if(tr.dataset.sym&&window.parent&&window.parent.miOpenUrlTab)window.parent.miOpenUrlTab('ov:'+tr.dataset.sym,{url:'/overseas?symb='+encodeURIComponent(tr.dataset.sym)+'&excd='+encodeURIComponent(tr.dataset.excd||''),title:tr.dataset.sym+' 🌎',icon:'🌎',loading:'해외 종목 불러오는 중…'});}catch(e){}});});
  }).catch(function(){var b=document.getElementById('glBody');if(b)b.innerHTML='<div class="gnote">불러오지 못했습니다.</div>';});}
function renderList(L){var w=document.getElementById('listWrap');
  if(L.kind==='global'){
    w.innerHTML='<div class="lhead">🌏 국가별 종목</div>'+
      '<div class="mapseg" id="glTabs" style="margin-bottom:10px;">'+
      '<button data-c="cn" class="on">중국</button><button data-c="hk">홍콩</button>'+
      '<button data-c="jp">일본</button><button data-c="vn">베트남</button></div>'+
      '<div id="glBody"><div class="gnote">불러오는 중…</div></div>';
    var seg=document.getElementById('glTabs');
    seg.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
      seg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});glLoad(b.dataset.c);});});
    glLoad('cn');return;}
  if(L.kind==='us'){
    w.innerHTML='<div class="lhead">🇺🇸 미국 종목</div>'+
      '<div class="mapseg" id="usFilt" style="margin-bottom:10px;">'+
      '<button data-f="actives" class="on">거래대금 상위</button><button data-f="gainers">상승</button>'+
      '<button data-f="losers">하락</button><button data-f="mcap">시가총액</button></div>'+
      '<div id="usListBody"><div class="gnote">불러오는 중…</div></div>';
    var seg=document.getElementById('usFilt');
    seg.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
      seg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});usLoad(b.dataset.f);});});
    usLoad('actives');return;}
  if(!L.rows||!L.rows.length){w.innerHTML='';return;}
  var h='<div class="lhead">👑 시가총액 상위</div><table class="wtbl"><thead><tr><th class="rk">#</th><th>종목명</th><th>현재가</th><th>전일대비</th><th>거래량</th><th>시가총액</th></tr></thead><tbody>';
  L.rows.forEach(function(r,i){var dirc=r.pct>0?'up':(r.pct<0?'down':'flat'),sg=r.pct>0?'+':'';
    h+='<tr data-code="'+esc(r.code||'')+'"><td class="rk">'+(i+1)+'</td><td>'+esc(r.name)+'</td>'+
       '<td>'+fmtN(r.price,0)+'</td><td class="'+dirc+'">'+sg+fmtN(r.pct)+'%</td><td>'+fmtN(r.volume,0)+'</td><td>'+krMcap(r.mcap)+'</td></tr>';});
  w.innerHTML=h+'</tbody></table>';
  w.querySelectorAll('tbody tr').forEach(function(tr){tr.addEventListener('click',function(){try{
    if(tr.dataset.code&&window.parent&&window.parent.miOpenStockTab)window.parent.miOpenStockTab(tr.dataset.code);}catch(e){}});});}
function setupMap(v){var wrap=document.getElementById('mapWrap'),seg=document.getElementById('mapSeg'),
    title=document.getElementById('mapTitle'),leg=document.getElementById('mapLegend');
  if(v==='global'){wrap.style.display='none';return;}
  wrap.style.display='block';
  if(v==='us'){title.textContent='🇺🇸 미국 S&P 500 마켓맵';
    seg.innerHTML='<button data-e="all" class="on">전체</button><button data-e="nyse">뉴욕 NYSE</button><button data-e="nasdaq">나스닥</button>';
    leg.querySelector('i').style.background='linear-gradient(90deg,#cf3a3a,#4a5160,#2e9e5b)';
  }else{title.textContent='🗺️ 국내 마켓맵';
    seg.innerHTML='<button data-m="kospi" class="on">코스피</button><button data-m="kosdaq">코스닥</button>';
    leg.querySelector('i').style.background='linear-gradient(90deg,#2E75B6,#4a5160,#FF3B30)';}
  seg.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
    seg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});
    if(v==='us'){mapExch=b.dataset.e;}else{mapMkt=b.dataset.m;}loadMap(v);});});
  loadMap(v);}
function loadMap(v){var el=document.getElementById('theMap');el.innerHTML='<div class="mapempty">마켓맵 불러오는 중…</div>';
  var url=(v==='us')?('/api/usmap?exch='+mapExch):('/api/marketmap?mkt='+mapMkt);
  fetch(url,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    if(!d.ok||!d.fig||!window.Plotly){el.innerHTML='<div class="mapempty">마켓맵 데이터가 없습니다.</div>';return;}
    var fig=(typeof d.fig==='string')?JSON.parse(d.fig):d.fig;el.innerHTML='';
    fig.layout=fig.layout||{};fig.layout.paper_bgcolor='rgba(0,0,0,0)';
    Plotly.newPlot('theMap',fig.data,fig.layout,{displayModeBar:false,responsive:true});
  }).catch(function(){el.innerHTML='<div class="mapempty">마켓맵을 불러오지 못했습니다.</div>';});}
function render(){window.__wview=view;$('#state').style.display='block';$('#body').style.display='none';
  fetch('/api/world_view?view='+view,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    if(!d.ok){$('#state').textContent='데이터를 불러오지 못했습니다.';return;}
    lastCards=d.cards||[];
    $('#asof').textContent='기준 '+esc(d.asof);
    $('#idxRow').innerHTML=lastCards.map(icard).join('');
    $('#kpiRow').innerHTML=(d.kpis||[]).map(kcard).join('');
    $('#state').style.display='none';$('#body').style.display='block';
    redrawSparks();bindSparkSegs();renderList(d.list||{});setupMap(view);
  }).catch(function(){$('#state').textContent='네트워크 오류';});}
(function(){var t=document.getElementById('vtabs');
  t.querySelectorAll('.vtab').forEach(function(b){b.addEventListener('click',function(){
    view=b.dataset.v;t.querySelectorAll('.vtab').forEach(function(x){x.classList.toggle('on',x===b);});render();});});})();
window.addEventListener('resize',redrawSparks);
render();
</script></body></html>
"""
