# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pywebview>=5.0",
#   "pyobjc-core>=10.0; sys_platform == 'darwin'",
#   "pyobjc-framework-Cocoa>=10.0; sys_platform == 'darwin'",
#   "pyobjc-framework-WebKit>=10.0; sys_platform == 'darwin'",
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
#   "duckdb>=0.10.0",
#   "websockets>=12.0",
#   "mlx>=0.15.0; sys_platform == 'darwin' and platform_machine == 'arm64'",
# ]
# ///
"""K-Market Dashboard — macOS 네이티브 앱 런처.

원본 `scripts/market_dashboard3_realtime.py` 를 **수정하지 않고** 그대로 로드해서:
  1) 내부 Flask 서버를 백그라운드 스레드로 띄우고 (127.0.0.1:8780)
  2) pywebview WKWebView 단일 네이티브 창에 그 페이지를 띄운다.

브라우저(Safari)와 동일한 WebKit 엔진으로 렌더링하므로 UI·인터랙션·3D 그래픽이
원본 웹 대시보드와 100% 동일하게 표시된다.

실행 (소스):   uv run app.py
빌드 (.app):  ./build.sh   →  dist/K-Market Dashboard.app

업데이트(재빌드 없이 소스 반영)
  · 앱은 실행 시 **라이브 소스**(원본 .py)를 직접 로드하므로, 소스를 고친 뒤
    메뉴바 "K-Market Dashboard ▸ 업데이트 확인…" → 재시작이면 최신 코드가 반영된다.
  · 라이브 소스를 못 찾으면 번들에 동결된 버전으로 안전하게 폴백.

로고
  · application_build/icon.png 가 Dock 앱 아이콘과 웹 UI 로고/파비콘의 단일 소스.
    빌드 시 번들 루트에 포함되어 동결 상태에서도 /logo.png 로 제공된다.

ProMotion(120Hz)
  · 3D 자동회전은 원본 _M4_WIRE 의 requestAnimationFrame 루프로 디스플레이 주사율에
    맞춰 매끄럽게 돈다(리포트는 iframe 이라 회전 패치는 소스 자체에 둔다).

M4 Pro 가속 포인트
  · 원본 모듈의 벡터화 NumPy(Accelerate BLAS) 몬테카를로 / asyncio 병렬 I/O /
    Plotly WebGL(16-core GPU) 렌더링을 그대로 활용 — 런처는 창만 입힐 뿐 오버헤드 0.
  · 서버는 데몬 스레드로 동작하고 창이 닫히면 프로세스 전체를 즉시 종료.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shlex
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# 경로 해석 — 소스 실행 / PyInstaller(.app) 동결 실행 양쪽 지원
# ---------------------------------------------------------------------------
def _base_dir() -> Path:
    """원본 프로젝트 루트(scripts/, market_intel/, .env 가 있는 곳)를 반환."""
    if getattr(sys, "frozen", False):
        # PyInstaller: 번들 리소스는 sys._MEIPASS 아래에 풀린다.
        return Path(getattr(sys, "_MEIPASS"))
    # 소스 실행: application_build/ 의 부모가 프로젝트 루트.
    return Path(__file__).resolve().parent.parent


BASE = _base_dir()
SCRIPTS_DIR = BASE / "scripts"

# ---------------------------------------------------------------------------
# 라이브 소스 해석 — "업데이트" 기능의 핵심
#
# .app 으로 빌드하면 market_dashboard3_realtime.py 가 번들 안에 동결되어, 원본
# 소스를 고쳐도 반영되지 않는다. 이를 해결하기 위해 앱은 실행할 때마다 **원본
# 프로젝트의 라이브 소스**(아래 _live_source())를 직접 로드한다. 따라서 소스를
# 수정한 뒤 메뉴바 "K-Market Dashboard ▸ 업데이트 확인…" 으로 재시작하면 최신
# 코드가 바로 반영된다(이미 실행 중이면 변경을 감지해 재시작을 제안).
#
# 경로 우선순위: 환경변수(KMKT_SOURCE_ROOT) → 소스 실행 시 프로젝트 루트 →
#               개발 머신 기본 경로(DEFAULT_LIVE_ROOT).
# 라이브 소스를 못 찾으면(다른 Mac 등) 번들에 동결된 버전으로 안전하게 폴백한다.
# ---------------------------------------------------------------------------
DEFAULT_LIVE_ROOT = Path("/Users/minjun1803/Documents/Python/Project_Market_Dashboard")


def _live_root() -> Path | None:
    cands: list[Path] = []
    env = os.environ.get("KMKT_SOURCE_ROOT")
    if env:
        cands.append(Path(env))
    if not getattr(sys, "frozen", False):
        cands.append(Path(__file__).resolve().parent.parent)
    cands.append(DEFAULT_LIVE_ROOT)
    for c in cands:
        try:
            if (c / "scripts" / "market_dashboard3_realtime.py").is_file():
                return c
        except Exception:  # noqa: BLE001
            pass
    return None


def _live_source() -> Path | None:
    """업데이트 대상인 라이브 market_dashboard3_realtime.py 경로(없으면 None)."""
    env = os.environ.get("KMKT_SOURCE")
    if env and Path(env).is_file():
        return Path(env)
    root = _live_root()
    if root:
        p = root / "scripts" / "market_dashboard3_realtime.py"
        if p.is_file():
            return p
    return None


def _hash_file(path: Path | None) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None
    except Exception:  # noqa: BLE001
        return None


LIVE_ROOT = _live_root()
LIVE_SOURCE = _live_source()

# import 경로: 라이브 루트(있으면) → 번들/소스 루트 순. 원본 모듈의
# `from archive import ...` / `from market_intel import ...` 가 해결되도록 한다.
_path_dirs = [str(SCRIPTS_DIR), str(BASE)]
if LIVE_ROOT is not None:
    _path_dirs = [str(LIVE_ROOT / "scripts"), str(LIVE_ROOT)] + _path_dirs
for p in _path_dirs:
    if p not in sys.path:
        sys.path.insert(0, p)

# 원본 모듈이 부모/.env 를 찾지 못하는 동결 상태를 대비해 키를 미리 환경에 로드.
# (원본 _kis_keys() 는 os.environ 을 최우선으로 보므로 충돌 없음)
try:
    from dotenv import load_dotenv

    _env_roots = [BASE]
    if LIVE_ROOT is not None:
        _env_roots.insert(0, LIVE_ROOT)
    for _r in _env_roots:
        for env_path in (_r / ".env", _r / "API.env"):
            if env_path.exists():
                load_dotenv(env_path, override=False)
except Exception:  # noqa: BLE001
    pass

# 원본의 브라우저 자동 오픈을 끈다. 네이티브 창이 그 역할을 대신한다.
os.environ.setdefault("MI_NO_OPEN", "1")


# ---------------------------------------------------------------------------
# 원본 Flask 앱 모듈 로드 — 라이브 소스 우선("업데이트" 반영)
#
# ProMotion(120Hz) 부드러운 3D 회전은 원본 _M4_WIRE 안에서 requestAnimationFrame
# 으로 처리한다(리포트는 iframe 으로 로드되어 런처 창의 top document 주입이 닿지
# 않으므로, 회전 패치는 소스 자체에 두는 것이 옳다 — 이로써 업데이트 대상에도 포함).
# ---------------------------------------------------------------------------
def _load_live_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"spec 생성 실패: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


md = None
_LIVE_LOADED = False     # 라이브 소스를 실제로 로드했는지(번들 폴백이면 False) — 실행시점 업데이트 판단용
if LIVE_SOURCE is not None:
    try:
        md = _load_live_module("market_dashboard3_realtime", LIVE_SOURCE)
        _LIVE_LOADED = True
        print(f"  · 라이브 소스 로드: {LIVE_SOURCE}")
    except Exception as e:  # noqa: BLE001
        print(f"  ! 라이브 소스 로드 실패({e}) — 번들 버전으로 폴백")
        md = None
if md is None:
    import market_dashboard3_realtime as md  # noqa: E402

# 현재 실행 중인 코드의 서명(라이브 소스 해시) — "업데이트 확인" 시 변경 감지 기준.
_LOADED_HASH = _hash_file(LIVE_SOURCE)
# 번들(.app)에 동결된 버전의 서명 — '출하 시점 대비 업데이트' 판단 기준(실행시점 1회 확인용).
_BUNDLED_HASH = (_hash_file(SCRIPTS_DIR / "market_dashboard3_realtime.py")
                 or _hash_file(BASE / "market_dashboard3_realtime.py"))

PORT = int(os.environ.get("MARKET_PORT", str(md.PORT)))
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}/"


# ---------------------------------------------------------------------------
# 서버 기동
# ---------------------------------------------------------------------------
def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, port)) == 0


def _serve() -> None:
    md.app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)


def _wait_until_ready(timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(URL + "__ping", timeout=1.0) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(0.25)
    return False


def _start_backend() -> None:
    if _port_in_use(PORT):
        # 이미 떠 있는 인스턴스(혹은 외부 실행)를 그대로 사용.
        print(f"  · 기존 서버 감지 — {URL} 재사용")
        return
    threading.Thread(target=_serve, daemon=True).start()
    # 원본 프리워밍(삼성전자·KODEX200 선계산)도 그대로 가동.
    if not os.environ.get("MI_NO_PREWARM"):
        threading.Thread(target=md._prewarm, daemon=True).start()


# ---------------------------------------------------------------------------
# 업데이트 (메뉴바 "업데이트 확인…")
#
# 앱은 실행 시 라이브 소스를 로드하므로, 소스를 고친 뒤 재시작만 하면 최신 코드가
# 반영된다. "업데이트 확인"은 (실행 중 코드 = _LOADED_HASH) 와 (현재 라이브 소스
# 해시)를 비교해 변경을 감지하고, 변경이 있으면 재시작을 제안한다.
# ※ 메뉴 액션은 pywebview 가 별도 스레드에서 호출하므로 모달 대화상자 호출이 안전.
# ---------------------------------------------------------------------------
def _native_alert(message: str, informative: str = "",
                  buttons: tuple[str, ...] = ("확인",)) -> int:
    """메인 스레드에서 NSAlert 를 띄우고 클릭된 버튼 인덱스(0=첫 버튼)를 반환."""
    if sys.platform != "darwin":
        print(f"[알림] {message} — {informative}")
        return 0
    from threading import Semaphore

    import AppKit
    from PyObjCTools import AppHelper

    holder = {"idx": 0}
    sem = Semaphore(0)

    def _show() -> None:
        try:
            AppKit.NSApplication.sharedApplication()
            AppKit.NSRunningApplication.currentApplication().activateWithOptions_(
                AppKit.NSApplicationActivateIgnoringOtherApps)
            alert = AppKit.NSAlert.alloc().init()
            alert.setMessageText_(message)
            if informative:
                alert.setInformativeText_(informative)
            for b in buttons:
                alert.addButtonWithTitle_(b)
            holder["idx"] = int(alert.runModal()) - 1000  # NSAlertFirstButtonReturn=1000
        except Exception as e:  # noqa: BLE001
            print("alert 오류:", e)
        finally:
            sem.release()

    AppHelper.callAfter(_show)
    sem.acquire()
    return holder["idx"]


def _restart() -> None:
    """현재 인스턴스를 종료하고 동일 앱을 다시 띄운다(라이브 소스 재로딩)."""
    try:
        if getattr(sys, "frozen", False):
            app_path = None
            for parent in Path(sys.executable).resolve().parents:
                if parent.suffix == ".app":
                    app_path = parent
                    break
            # 포트(8780)가 풀릴 시간을 준 뒤 새 인스턴스를 띄운다.
            if app_path is not None:
                subprocess.Popen(["/bin/bash", "-c", f'sleep 1.2; open -n "{app_path}"'])
            else:
                subprocess.Popen(["/bin/bash", "-c", f'sleep 1.2; "{sys.executable}"'])
        else:
            argv = " ".join(shlex.quote(a) for a in sys.argv)
            subprocess.Popen(["/bin/bash", "-c",
                              f'sleep 1.0; "{sys.executable}" {argv}'])
    except Exception as e:  # noqa: BLE001
        print("재시작 실패:", e)
    os._exit(0)


# 인앱 업데이트 오버레이 — 실제 앱처럼 "업데이트 적용 중" 화면을 띄우고 자동 재시작.
_UPDATE_OVERLAY_JS = r"""(function(){
  if(document.getElementById('__kmkt_upd'))return;
  var o=document.createElement('div');o.id='__kmkt_upd';
  o.style.cssText='position:fixed;inset:0;z-index:2147483647;display:flex;flex-direction:column;'+
    'align-items:center;justify-content:center;gap:15px;background:rgba(11,15,32,.74);'+
    '-webkit-backdrop-filter:saturate(160%) blur(14px);backdrop-filter:saturate(160%) blur(14px);'+
    'color:#eaf0ff;font-family:-apple-system,BlinkMacSystemFont,sans-serif;opacity:0;transition:opacity .25s;';
  o.innerHTML='<div style="font-size:36px">✨</div>'+
    '<div style="font-size:17px;font-weight:800;letter-spacing:-.01em">새 버전 적용 중…</div>'+
    '<div style="font-size:12.5px;opacity:.72">잠시 후 자동으로 재시작됩니다</div>'+
    '<div style="width:240px;height:5px;border-radius:3px;background:rgba(255,255,255,.16);overflow:hidden;margin-top:4px">'+
    '<div id="__kmkt_updbar" style="height:100%;width:6%;border-radius:3px;background:linear-gradient(90deg,#36c6ff,#9b6bff);transition:width 1.7s cubic-bezier(.4,0,.2,1)"></div></div>';
  document.body.appendChild(o);
  requestAnimationFrame(function(){o.style.opacity='1';
    requestAnimationFrame(function(){document.getElementById('__kmkt_updbar').style.width='100%';});});
})();"""


def _apply_update_ui() -> None:
    """인앱 업데이트 오버레이 표시 후 자동 재시작 (진행바 시간을 준 뒤)."""
    if _menu_state.get("updating"):
        return
    _menu_state["updating"] = True
    _evaljs_async(_UPDATE_OVERLAY_JS)
    threading.Timer(2.0, _restart).start()


def _check_update_at_launch() -> None:
    """앱 실행 시점에 '한 번만' 업데이트 여부를 확인한다(상시 폴링 없음 → 자원 절약).

    이전 구현은 12초 주기 백그라운드 폴링으로 라이브 소스를 감시했으나, 사용자 요청에 따라
    '실행 시점 1회 확인'으로 변경했다. 동작:
      · 라이브 소스가 없으면(배포 .dmg) → 업데이트 대상 없음, 종료.
      · 라이브 소스를 정상 로드했으면(_LIVE_LOADED) → 이미 최신 코드로 부팅됨, 종료.
      · 라이브 로드에 실패해 '번들 폴백'으로 떠 있는데 라이브 소스가 번들과 다르면
        → 더 새 코드가 있다는 뜻. 단, 깨진 소스로 인한 재시작 무한루프를 막기 위해
          (1) py_compile 통과 (2) 직전에 같은 해시로 시도한 적 없음(마커) 일 때만 1회 적용.
    이후 실행 중 갱신은 메뉴 '업데이트 확인…'으로 수동 적용한다(자동 감시 없음)."""
    if _LIVE_LOADED:
        return                                            # 이미 라이브(최신)로 부팅됨
    src = _live_source()
    if src is None:
        return                                            # 배포본 — 업데이트 대상 없음
    cur = _hash_file(src)
    if not cur or cur == _BUNDLED_HASH:
        return                                            # 라이브가 번들과 동일 → 적용할 것 없음
    # 재시작 루프 방지 ①: 직전에 동일 해시로 이미 시도했다면 깨진 소스로 보고 건너뜀.
    marker = Path(tempfile.gettempdir()) / "kmkt_update_attempt.txt"
    try:
        if marker.exists() and marker.read_text().strip() == cur:
            return
    except Exception:  # noqa: BLE001
        pass
    # 재시작 루프 방지 ②: 라이브 소스가 문법적으로 유효할 때만 적용.
    try:
        import py_compile
        py_compile.compile(str(src), doraise=True)
    except Exception:  # noqa: BLE001
        return
    try:
        marker.write_text(cur)
    except Exception:  # noqa: BLE001
        pass
    _apply_update_ui()


def _check_for_updates() -> None:
    """메뉴 액션 — 라이브 소스 변경 확인. 변경 시 인앱 오버레이로 자동 적용(NSAlert 없이)."""
    src = _live_source()
    if src is None:
        _native_alert(
            "업데이트를 확인할 수 없습니다",
            "원본 소스(market_dashboard3_realtime.py)를 찾지 못했습니다.\n"
            "이 빌드는 번들된 고정 버전으로 동작합니다(자동 업데이트 비활성).",
            ("확인",))
        return
    current = _hash_file(src)
    if current is not None and current == _LOADED_HASH:
        _native_alert("최신 버전입니다", "실행 중인 코드가 원본 소스와 동일합니다.\n" + str(src), ("확인",))
        return
    _apply_update_ui()                                    # 모달 없이 인앱 오버레이 → 자동 재시작


# ---------------------------------------------------------------------------
# 네이티브 메뉴바 (HIG: App → File → Edit → View → Window → Help)
#
# 4개 HIG 문서(The menu bar / Dock menus / Going full screen / File management)의
# Phase 1 — pywebview 가 만든 메뉴를 PyObjC 로 만든 HIG 순서 메뉴바로 교체한다.
#   · 표준 동작(편집·최소화·전체화면 등)은 시스템 셀렉터를 그대로 재사용
#     (cut:/copy:/paste:/selectAll:/undo:/redo:/performMiniaturize:/performZoom:/
#      arrangeInFront:/toggleFullScreen:/orderFrontStandardAboutPanel:/hide:/terminate:).
#   · 커스텀 동작(검색·탭·새로고침·인쇄·업데이트)은 아래 _KMenuTarget 셀렉터가
#     별도 스레드에서 window.evaluate_js(웹 UI 의 MI_* 브리지) 를 호출.
#     (메뉴 액션은 메인 스레드에서 발생 → evaluate_js 는 반드시 스레드로 넘겨 WKWebView 교착 방지)
# ---------------------------------------------------------------------------
_menu_state: dict = {"window": None, "target": None, "zoom": 1.0}


def _reveal_window() -> None:
    """스타일·로드가 모두 끝났을 때만, 그리고 WKWebView 첫 페인트가 합성된 뒤에 창을 노출.

    `window.events.loaded` 는 첫 페인트 *이전*(네비게이션 완료 시점)에 발생한다. 이때 바로
    show() 하면 WKWebView 가 다크 스플래시를 합성하기 전이라 기본 흰 프레임이 한 번
    깜빡인다(스플래시 배경은 #0b0f20 다크). 메인 런루프 한 틱(~80ms) 뒤 노출해 흰
    깜빡임을 제거한다. 여러 경로(styled/loaded)에서 호출되므로 shown 가드로 1회만 실행."""
    if _menu_state.get("shown"):
        return
    if not (_menu_state.get("loaded") and (_menu_state.get("styled") or sys.platform != "darwin")):
        return
    w = _menu_state.get("window")
    if w is None:
        return
    _menu_state["shown"] = True
    if sys.platform == "darwin":
        try:
            from PyObjCTools import AppHelper
            AppHelper.callLater(0.08, w.show)   # 첫 페인트 합성 대기 → 흰 깜빡임 제거
            return
        except Exception:  # noqa: BLE001
            pass
    w.show()


def _evaljs_async(js: str) -> None:
    w = _menu_state["window"]
    if w is None:
        return

    def _run() -> None:
        try:
            w.evaluate_js(js)
        except Exception as e:  # noqa: BLE001
            print("evaluate_js 오류:", e)

    threading.Thread(target=_run, daemon=True).start()


def _close_active_window() -> None:
    w = _menu_state["window"]
    try:
        if w is not None:
            w.destroy()
    except Exception:  # noqa: BLE001
        os._exit(0)


def _close_tab_or_window() -> None:
    """⌘W — 활성 리포트 탭이 있으면 닫고, 없으면 창을 닫는다(HIG Close)."""
    w = _menu_state["window"]
    if w is None:
        return

    def _run() -> None:
        closed = False
        try:
            closed = bool(w.evaluate_js("(window.MI_CLOSE_TAB?window.MI_CLOSE_TAB():false)"))
        except Exception:  # noqa: BLE001
            closed = False
        if not closed:
            from PyObjCTools import AppHelper
            AppHelper.callAfter(_close_active_window)

    threading.Thread(target=_run, daemon=True).start()


def _browser_instance():
    try:
        from webview.platforms.cocoa import BrowserView
        w = _menu_state["window"]
        return BrowserView.instances.get(w.uid) if w is not None else None
    except Exception:  # noqa: BLE001
        return None


def _native_print() -> None:
    """⌘P — 활성 WKWebView 를 macOS 인쇄 패널로(‘PDF로 저장’ 포함). File management 패턴."""
    inst = _browser_instance()
    if inst is None:
        _evaljs_async("window.MI_PRINT&&window.MI_PRINT()")
        return
    try:
        from webview.platforms.cocoa import BrowserView
        from PyObjCTools import AppHelper
        AppHelper.callAfter(BrowserView.print_webview, inst.webview)
    except Exception as e:  # noqa: BLE001
        print("네이티브 인쇄 실패 → JS 폴백:", e)
        _evaljs_async("window.MI_PRINT&&window.MI_PRINT()")


def _web_zoom_window() -> None:
    """웹 상단바 더블클릭에서 호출(window.pywebview.api._web_zoom_window) — 최대화↔복원 토글.

    NSWindow.zoom_ 은 '표준 프레임'으로 점프하듯 보여 어색하므로, 현재 프레임에서
    화면 visibleFrame 으로 setFrame:display:animate: 로 부드럽게 한 번에 확장한다.
    이미 최대화 상태면 직전 프레임으로 복원."""
    if sys.platform != "darwin":
        return
    try:
        import AppKit
        from PyObjCTools import AppHelper

        def _do() -> None:
            inst = _browser_instance()
            win = getattr(inst, "window", None) if inst is not None else None
            if win is None:
                return
            scr = win.screen() or AppKit.NSScreen.mainScreen()
            if scr is None:
                win.zoom_(None)
                return
            vis = scr.visibleFrame()
            cur = win.frame()
            prev = _menu_state.get("_prevframe")
            maxed = (abs(cur.size.width - vis.size.width) < 6
                     and abs(cur.size.height - vis.size.height) < 6)
            if maxed and prev is not None:
                win.setFrame_display_animate_(prev, True, True)
                _menu_state["_prevframe"] = None
            else:
                _menu_state["_prevframe"] = cur
                win.setFrame_display_animate_(vis, True, True)
        AppHelper.callAfter(_do)
    except Exception as e:  # noqa: BLE001
        print("창 zoom 토글 오류:", e)


def _adjust_zoom(delta) -> None:
    """View 확대/축소/실제 크기 — WKWebView pageZoom(전체 콘텐츠·iframe 포함)."""
    inst = _browser_instance()
    if inst is None:
        return
    try:
        from PyObjCTools import AppHelper

        def _do() -> None:
            z = 1.0 if delta is None else max(0.5, min(3.0, _menu_state["zoom"] + delta))
            _menu_state["zoom"] = z
            try:
                inst.webview.setPageZoom_(z)
            except Exception as e:  # noqa: BLE001
                print("zoom 오류:", e)

        AppHelper.callAfter(_do)
    except Exception as e:  # noqa: BLE001
        print("zoom 디스패치 오류:", e)


def _open_help() -> None:
    readme = Path(__file__).resolve().parent / "README.md"
    if readme.exists():
        subprocess.Popen(["open", str(readme)])
    else:
        _native_alert("K-Market Dashboard 도움말",
                      "한국 증시 통합 대시보드.\n메뉴바·검색·실시간 시세·M4 퀀트 분석을 제공합니다.",
                      ("확인",))


_MENU_TARGET_CLS = None


def _make_menu_target():
    """커스텀 메뉴 셀렉터를 담은 NSObject(영속 — GC 방지용으로 보관).

    ObjC 클래스는 프로세스당 한 번만 정의할 수 있으므로 클래스 객체를 캐시한다.
    """
    global _MENU_TARGET_CLS
    if _MENU_TARGET_CLS is not None:
        return _MENU_TARGET_CLS.alloc().init()

    import AppKit  # noqa: F401
    from Foundation import NSObject

    class _KMenuTarget(NSObject):
        def appBecameActive_(self, notification):
            _evaljs_async("window.MI_APP_ACTIVE=true;")

        def appResignedActive_(self, notification):
            _evaljs_async("window.MI_APP_ACTIVE=false;")

        def newSearch_(self, sender):
            _evaljs_async("window.MI_FOCUS_SEARCH&&window.MI_FOCUS_SEARCH()")

        def findSearch_(self, sender):
            _evaljs_async("window.MI_FOCUS_SEARCH&&window.MI_FOCUS_SEARCH()")

        def closeTab_(self, sender):
            _close_tab_or_window()

        def reloadView_(self, sender):
            _evaljs_async("window.MI_RELOAD&&window.MI_RELOAD()")

        def nextTab_(self, sender):
            _evaljs_async("window.MI_NEXT_TAB&&window.MI_NEXT_TAB()")

        def prevTab_(self, sender):
            _evaljs_async("window.MI_PREV_TAB&&window.MI_PREV_TAB()")

        def printDoc_(self, sender):
            _native_print()

        def zoomIn_(self, sender):
            _adjust_zoom(0.1)

        def zoomOut_(self, sender):
            _adjust_zoom(-0.1)

        def zoomReset_(self, sender):
            _adjust_zoom(None)

        def checkUpdates_(self, sender):
            threading.Thread(target=_check_for_updates, daemon=True).start()

        def openHelp_(self, sender):
            threading.Thread(target=_open_help, daemon=True).start()

    _MENU_TARGET_CLS = _KMenuTarget
    return _KMenuTarget.alloc().init()


def _apply_glass_transparency() -> None:
    """창이 화면에 보인 *뒤*에 WKWebView/창을 투명으로 전환(둥근 타이틀바·유리 외형).

    이걸 show() *이전*에 적용하면 창이 투명한 상태로 노출돼, 스플래시가 첫 페인트되기 전
    한 프레임 동안 뒤(데스크탑)가 비쳐 흰 깜빡임처럼 보인다 — changes_13(80ms 지연)으로도
    남았던 잔여 깜빡임의 진짜 원인. 그래서 먼저 불투명 다크(#0b0f20)로 노출하고 여기서
    투명 전환한다(다크→다크라 체감 변화 없음)."""
    if sys.platform != "darwin":
        return
    try:
        import AppKit
        inst = _browser_instance()
        win = getattr(inst, "window", None) if inst is not None else None
        if win is None:
            return
        try:                                            # ④ WKWebView 흰 배경 제거
            wv = getattr(inst, "webview", None)
            if wv is not None:
                wv.setValue_forKey_(False, "drawsBackground")
        except Exception:  # noqa: BLE001
            pass
        try:                                            # ⑤ 창/타이틀바 투명 전환
            win.contentView().superview().subviews().lastObject().setBackgroundColor_(
                AppKit.NSColor.clearColor())
            win.setOpaque_(False)
            win.setBackgroundColor_(AppKit.NSColor.clearColor())
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:  # noqa: BLE001
        print("유리 전환 실패:", e)


def _style_native_window() -> None:
    """불투명 타이틀바를 없애고 콘텐츠를 상단까지 확장(신호등은 콘텐츠 위에 떠 있음).

    NSWindow: FullSizeContentView + 투명 타이틀바 + 타이틀 숨김.
    → 좌측 상단 닫기·최소화·확대 3개 버튼만 웹 UI(상단바) 위에 일체화되어 보인다.
    창 드래그는 웹의 .pywebview-drag-region(상단바)이 담당.
    """
    if sys.platform != "darwin":
        return
    try:
        import AppKit
        from PyObjCTools import AppHelper

        inst = _browser_instance()
        win = getattr(inst, "window", None) if inst is not None else None
        if win is None:
            n = _menu_state.get("_wretry", 0)
            if n < 60:
                _menu_state["_wretry"] = n + 1
                AppHelper.callLater(0.1, _style_native_window)
            return
        # ① 콘텐츠를 타이틀바 영역까지 확장 + 타이틀바 완전 투명 → 웹 그라데이션이
        #    창 최상단까지 끊김 없이 이어진다(Gemini 식 "바 없는" 외형).
        win.setStyleMask_(win.styleMask() | AppKit.NSWindowStyleMaskFullSizeContentView)
        win.setTitlebarAppearsTransparent_(True)
        win.setTitleVisibility_(AppKit.NSWindowTitleHidden)
        win.setMovableByWindowBackground_(False)
        # ② 타이틀바-콘텐츠 사이 hairline 구분선 제거(macOS 11+) → 불투명 띠가 안 보임.
        try:
            win.setTitlebarSeparatorStyle_(AppKit.NSTitlebarSeparatorStyleNone)
        except Exception:  # noqa: BLE001
            pass
        # ③ 혹시 모를 NSToolbar 제거(있으면 타이틀바가 두꺼운 불투명 바로 보임).
        try:
            if win.toolbar() is not None:
                win.setToolbar_(None)
        except Exception:  # noqa: BLE001
            pass
        # ④⑤ 유리(투명) 효과는 창이 "보인 뒤"에 적용한다(아래 _apply_glass_transparency).
        #    show() 이전에 투명으로 만들면 스플래시 첫 페인트 전 데스크탑이 비쳐 깜빡인다.
        #    → 먼저 불투명 다크(#0b0f20)로 노출하고 0.3s 뒤 투명 전환(다크→다크, 무깜빡).
        try:
            _menu_state["styled"] = True
            _reveal_window()
            AppHelper.callLater(0.3, _apply_glass_transparency)
        except Exception as e:
            print("창 표시 실패:", e)
            
    except Exception as e:  # noqa: BLE001
        print("창 스타일 설정 실패:", e)


def _install_native_menu() -> None:
    """HIG 순서의 메뉴바를 만들어 NSApp 메인 메뉴로 설정(메인 스레드에서 호출)."""
    try:
        import AppKit
    except Exception as e:  # noqa: BLE001
        print("AppKit 로드 실패 — 메뉴바 건너뜀:", e)
        return

    app = AppKit.NSApplication.sharedApplication()
    target = _make_menu_target()
    _menu_state["target"] = target  # 영속 참조(액션이 죽지 않도록)

    nc = AppKit.NSNotificationCenter.defaultCenter()
    nc.addObserver_selector_name_object_(target, b"appBecameActive:", AppKit.NSApplicationDidBecomeActiveNotification, None)
    nc.addObserver_selector_name_object_(target, b"appResignedActive:", AppKit.NSApplicationDidResignActiveNotification, None)

    NAME = "K-Market Dashboard"
    CMD = AppKit.NSCommandKeyMask
    SHIFT = AppKit.NSShiftKeyMask
    OPT = AppKit.NSAlternateKeyMask
    CTRL = AppKit.NSControlKeyMask

    main = AppKit.NSMenu.alloc().init()

    def submenu(title: str):
        m = AppKit.NSMenu.alloc().initWithTitle_(title)
        item = AppKit.NSMenuItem.alloc().init()
        item.setSubmenu_(m)
        main.addItem_(item)
        return m

    def add(m, title, action, key="", tgt=None, mask=None):
        it = m.addItemWithTitle_action_keyEquivalent_(title, action, key)
        if tgt is not None:
            it.setTarget_(tgt)
        if mask is not None:
            it.setKeyEquivalentModifierMask_(mask)
        return it

    def sep(m):
        m.addItem_(AppKit.NSMenuItem.separatorItem())

    # ── App 메뉴(앱 이름은 시스템이 CFBundleName 으로 표시) ──
    app_menu = submenu(NAME)
    add(app_menu, f"About {NAME}", "orderFrontStandardAboutPanel:")
    sep(app_menu)
    add(app_menu, "업데이트 확인…", "checkUpdates:", "", target)
    sep(app_menu)
    services = AppKit.NSMenu.alloc().init()
    app.setServicesMenu_(services)
    svc = add(app_menu, "Services", None)
    svc.setSubmenu_(services)
    sep(app_menu)
    add(app_menu, f"Hide {NAME}", "hide:", "h")
    add(app_menu, "Hide Others", "hideOtherApplications:", "h", mask=CMD | OPT)
    add(app_menu, "Show All", "unhideAllApplications:")
    sep(app_menu)
    add(app_menu, f"Quit {NAME}", "terminate:", "q")

    # ── File ──
    file_menu = submenu("파일")
    add(file_menu, "새 검색", "newSearch:", "n", target)
    sep(file_menu)
    add(file_menu, "탭 닫기", "closeTab:", "w", target)
    sep(file_menu)
    add(file_menu, "PDF로 내보내기…", "printDoc:", "p", target)

    # ── Edit (표준 셀렉터 — 검색창에서 동작) ──
    edit_menu = submenu("편집")
    add(edit_menu, "실행 취소", "undo:", "z")
    add(edit_menu, "다시 실행", "redo:", "z", mask=CMD | SHIFT)
    sep(edit_menu)
    add(edit_menu, "오려두기", "cut:", "x")
    add(edit_menu, "복사하기", "copy:", "c")
    add(edit_menu, "붙여넣기", "paste:", "v")
    add(edit_menu, "전체 선택", "selectAll:", "a")
    sep(edit_menu)
    add(edit_menu, "찾기", "findSearch:", "f", target)

    # ── View ──
    view_menu = submenu("보기")
    add(view_menu, "새로고침", "reloadView:", "r", target)
    sep(view_menu)
    add(view_menu, "확대", "zoomIn:", "+", target)
    add(view_menu, "축소", "zoomOut:", "-", target)
    add(view_menu, "실제 크기", "zoomReset:", "0", target)
    sep(view_menu)
    add(view_menu, "전체 화면 시작/종료", "toggleFullScreen:", "f", mask=CMD | CTRL)

    # ── Window ──
    window_menu = submenu("윈도우")
    add(window_menu, "최소화", "performMiniaturize:", "m")
    add(window_menu, "확대/축소", "performZoom:")
    sep(window_menu)
    add(window_menu, "다음 탭", "nextTab:", "]", target, mask=CMD | SHIFT)
    add(window_menu, "이전 탭", "prevTab:", "[", target, mask=CMD | SHIFT)
    sep(window_menu)
    add(window_menu, "모두 앞으로 가져오기", "arrangeInFront:")
    app.setWindowsMenu_(window_menu)

    # ── Help ──
    help_menu = submenu("도움말")
    add(help_menu, f"{NAME} 도움말", "openHelp:", "?", target, mask=CMD)
    app.setHelpMenu_(help_menu)

    AppKit.NSApp.setMainMenu_(main)


def _install_dock_menu() -> None:
    """macOS Dock 아이콘 우클릭 메뉴를 동적으로 추가합니다."""
    try:
        import AppKit
        import objc
        
        app = AppKit.NSApp()
        delegate = app.delegate()
        if delegate is None:
            return
            
        def applicationDockMenu_(self, sender):
            menu = AppKit.NSMenu.alloc().init()
            
            # Spotlight 열기
            item1 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Spotlight 검색 (Cmd+K)", "newSearch:", "")
            item1.setTarget_(_menu_state.get("target"))
            menu.addItem_(item1)
            
            # 업종 현황 보기
            def _open_market(self):
                _evaljs_async("if(window.openTab) window.openTab('__market__',{url:'/market',title:'시장 현황',icon:'📈'})")
            item2 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("시장 현황 보기", "openMarket:", "")
            menu.addItem_(item2)
            
            # 스크리너 열기
            def _open_screener(self):
                _evaljs_async("if(window.openTab) window.openTab('__screener__',{url:'/screener_page',title:'스크리너 (DuckDB)',icon:'🔍'})")
            item3 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("DuckDB 스크리너", "openScreener:", "")
            menu.addItem_(item3)
            
            menu.addItem_(AppKit.NSMenuItem.separatorItem())
            
            item_upd = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("업데이트 확인...", "checkUpdates:", "")
            item_upd.setTarget_(_menu_state.get("target"))
            menu.addItem_(item_upd)
            
            return menu

        # PyObjC 런타임을 통해 applicationDockMenu: 메서드를 delegate 클래스에 삽입
        method = objc.selector(applicationDockMenu_, signature=b'@@:@')
        objc.classAddMethod(type(delegate), b'applicationDockMenu:', method)
        
        # 추가 액션용 메서드 등록
        def openMarket_(self, sender):
            _evaljs_async("if(window.openTab) window.openTab('__market__',{url:'/market',title:'시장 현황',icon:'📈'})")
        m_market = objc.selector(openMarket_, signature=b'v@:@')
        objc.classAddMethod(type(delegate), b'openMarket:', m_market)
        
        def openScreener_(self, sender):
            _evaljs_async("if(window.openTab) window.openTab('__screener__',{url:'/screener_page',title:'스크리너 (DuckDB)',icon:'🔍'})")
        m_screener = objc.selector(openScreener_, signature=b'v@:@')
        objc.classAddMethod(type(delegate), b'openScreener:', m_screener)
        
    except Exception as e:
        print("Dock Menu 설치 실패:", e)




# ---------------------------------------------------------------------------
# 네이티브 창
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("  K-Market Dashboard — macOS 네이티브 앱")
    print(f"  · 서버: {URL}")
    ak, _ = md._kis_keys()
    print("  · KIS 키 로드: " + ("OK" if ak else "실패 — .env(KIS_APP_KEY/SECRET) 확인"))
    print("=" * 60)

    _start_backend()
    if not _wait_until_ready():
        print("  ! 서버 기동 실패 — 포트/의존성을 확인하세요.")
        # 그래도 창은 띄워 오류 페이지/안내를 보여준다.

    import webview  # 늦은 import: 서버 준비 후 GUI 진입

    window = webview.create_window(
        "K-Market Dashboard",
        URL,
        width=1480,
        height=980,
        min_size=(1080, 720),
        background_color="#0b0f20",
        text_select=True,
        hidden=True,
    )
    _menu_state["window"] = window  # 메뉴 액션이 참조

    # 웹(상단바 더블클릭)에서 네이티브 창 zoom 토글을 호출할 수 있게 노출
    try:
        window.expose(_web_zoom_window)
    except Exception as e:  # noqa: BLE001
        print("zoom 브리지 노출 실패:", e)

    def _on_closed() -> None:
        # 창이 닫히면 데몬 서버 스레드까지 즉시 정리.
        os._exit(0)

    window.events.closed += _on_closed

    def _on_loaded() -> None:
        _menu_state["loaded"] = True
        _reveal_window()
        # 업데이트는 '실행 시점 1회'만 확인한다(상시 폴링 제거 — 자원 절약). 페이지 로드 후 1회.
        if not _menu_state.get("update_checked"):
            _menu_state["update_checked"] = True
            threading.Timer(0.5, _check_update_at_launch).start()

    window.events.loaded += _on_loaded

    def _bootstrap() -> None:
        # GUI 루프 시작 직후(별도 스레드) → 메인 스레드에서 HIG 메뉴바를 설치해
        # pywebview 기본 메뉴를 교체한다. callAfter 로 메인 런루프에 디스패치.
        if sys.platform != "darwin":
            _menu_state["styled"] = True
            _reveal_window()
            return
        try:
            from PyObjCTools import AppHelper
            AppHelper.callAfter(_install_native_menu)
            AppHelper.callAfter(_install_dock_menu)
            AppHelper.callAfter(_style_native_window)
        except Exception as e:  # noqa: BLE001
            print("메뉴바 설치 디스패치 실패:", e)
            _menu_state["styled"] = True
            _reveal_window()

    # macOS 는 Cocoa(WKWebView) 백엔드 — Safari 와 동일 렌더링.
    if sys.platform == "darwin":
        webview.start(_bootstrap, gui="cocoa")
    else:
        webview.start()


if __name__ == "__main__":
    main()
