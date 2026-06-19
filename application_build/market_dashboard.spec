# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — K-Market Dashboard.app (macOS, Apple Silicon).

  pyinstaller market_dashboard.spec --noconfirm

원본 소스(scripts/, market_intel/, archive/)는 수정하지 않고 분석 경로(pathex)에
올려 그대로 번들에 포함한다. 산출물: dist/K-Market Dashboard.app
"""
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# spec 파일이 있는 application_build/ 의 부모 = 프로젝트 루트
BUILD_DIR = os.path.abspath(os.getcwd())
ROOT = os.path.abspath(os.path.join(BUILD_DIR, ".."))
SCRIPTS = os.path.join(ROOT, "scripts")

datas, binaries, hiddenimports = [], [], []

# 서브모듈 수집 필터 — 테스트/미사용 선택 의존 모듈을 건너뛴다.
#   · 런타임에 안 쓰는 .tests/.testing, plotly.matplotlylib(matplotlib),
#     webview 의 비-cocoa 플랫폼, scipy array_api_compat 의 torch/cupy/dask 등을
#     제외해 빌드 경고(ModuleNotFoundError: matplotlib/torch/pytest/hypothesis…)를
#     없애고 번들 크기도 줄인다. macOS 앱에는 모두 불필요한 모듈들.
_SKIP_SUBMODULES = (
    ".tests", ".test.", ".testing", "._testing",
    "matplotlylib",
    "platforms.android", "platforms.gtk", "platforms.qt",
    "platforms.winforms", "platforms.edgechromium", "platforms.mshtml",
    "array_api_compat.torch", "array_api_compat.cupy", "array_api_compat.dask",
)


def _keep_submodule(name):
    return not any(s in name for s in _SKIP_SUBMODULES)


# 패키지 데이터/서브모듈이 필요한 라이브러리 일괄 수집 -----------------------
for pkg in ("plotly", "dotenv", "webview"):
    d, b, h = collect_all(pkg, filter_submodules=_keep_submodule, on_error="ignore")
    datas += d
    binaries += b
    hiddenimports += h

for pkg in ("scipy", "pandas", "numpy", "pyarrow", "polars", "lxml",
            "httpx", "flask", "jinja2", "werkzeug", "anyio", "h11", "certifi",
            "websockets"):
    hiddenimports += collect_submodules(pkg, filter=_keep_submodule, on_error="ignore")

# 원본 소스 모듈 (네임스페이스/명시 import 보강) ------------------------------
# app.py 가 market_dashboard3_realtime 를 importlib 로 *동적* 로드하므로 PyInstaller 의
# 정적 분석이 그 모듈과 그 모듈이 import 하는 분리 모듈들을 못 따라간다 → 명시 필요.
# ui_templates(changes_77)·pure_helpers(changes_78) 는 main 이 `from … import` 하는 분리 모듈.
# (새 분리 모듈을 추가하면 여기에도 등록할 것 — _STATUS.md 트랩/§12 구조동기화.)
hiddenimports += [
    "market_dashboard3_realtime",
    "ui_templates",
    "pure_helpers",
    "dev_overlay",
    "archive",
    "archive.company_report_ver2",
    "archive.etf_dashboard_ver2",
]
hiddenimports += collect_submodules("market_intel", filter=_keep_submodule, on_error="ignore")

# 환경설정 파일 — 번들 루트(_MEIPASS)에 둬서 app.py 의 BASE/.env 와 일치 ------
for fname in (".env", "API.env"):
    fpath = os.path.join(ROOT, fname)
    if os.path.exists(fpath):
        datas += [(fpath, ".")]

# 앱 로고(icon.png) — 번들 루트(_MEIPASS)에 둬서 realtime.py 의 _logo_path() 가
# 동결 상태에서도 /logo.png·favicon 으로 제공할 수 있게 한다(앱 아이콘과 동일 소스).
_icon_png = os.path.join(BUILD_DIR, "icon.png")
if os.path.exists(_icon_png):
    datas += [(_icon_png, ".")]

# 일부 KIS 키를 별도 디렉터리에 두는 구성도 함께 포함(있을 때만) --------------
kis_dir = os.path.join(SCRIPTS, "한국투자증권")
if os.path.isdir(kis_dir):
    datas += [(kis_dir, "scripts/한국투자증권")]


a = Analysis(
    ["app.py"],
    pathex=[BUILD_DIR, SCRIPTS, ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PySide6", "PyQt6", "test", "tests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="K-Market Dashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,           # GUI 앱 — 터미널 콘솔 없음
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",     # Apple Silicon(M4 Pro) 네이티브
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="K-Market Dashboard",
)

app = BUNDLE(
    coll,
    name="K-Market Dashboard.app",
    icon="icon.icns" if os.path.exists(os.path.join(BUILD_DIR, "icon.icns")) else None,
    bundle_identifier="com.minjun.kmarketdashboard",
    info_plist={
        "CFBundleName": "K-Market Dashboard",
        "CFBundleDisplayName": "K-Market Dashboard",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
        "LSApplicationCategoryType": "public.app-category.finance",
        # 로컬(127.0.0.1) HTTP 서버 허용
        "NSAppTransportSecurity": {
            "NSAllowsLocalNetworking": True,
            "NSAllowsArbitraryLoads": False,
        },
    },
)
