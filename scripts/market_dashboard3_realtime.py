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
#   "websockets>=12.0",
# ]
# ///
"""K-Market Dashboard 3 — M4 Pro · Pro Quant · 실시간 시세 Edition (market_dashboard3_realtime.py).

market_dashboard3.py 를 보존한 채, 현재가(.ph-price) 부분만 한국투자증권(KIS)
Open API 실시간 시세에 맞추어 움직이도록 확장한 버전. 나머지 리포트 내용은 그대로.

  uv run market_dashboard3_realtime.py
    → http://127.0.0.1:8780/

실시간 시세 동작 방식
  · 서버: KIS REST `oauth2/tokenP` 로 접근토큰 발급(24h 캐시) →
    `inquire-price`(tr_id FHKST01010100, 시장코드 J)로 현재가/전일대비/등락률 조회.
  · `/api/realtime?code=` 라우트가 JSON 으로 반환(코드별 ~0.8s 마이크로 캐시 + 초당
    호출 스로틀로 EGW00201 회피). 주식·ETF 모두 동일 엔드포인트 사용.
  · 브라우저: 리포트 HTML 에 주입된 폴러가 현재 보는 탭에서 2초 간격으로 조회해
    현재가 히어로(.ph-price)·등락 배지(.ph-chg)·박스색·ETF 현재가 KPI 만 갱신.

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
import logging
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# 추가 키 파일: api_documents/API.env (FREED_KEY 등 신규 키). 루트 .env 값이 우선(override=False).
load_dotenv(Path(__file__).resolve().parent.parent / "api_documents" / "API.env", override=False)

# changes_73 이 company_report.py·etf_dashboard.py 를 scripts/archive/ 로 옮겼으나,
# archive/company_report_ver2.py 가 `from company_report import ...`(절대 import)로,
# archive/etf_dashboard_ver2.py 가 `import etf_dashboard`로 형제 모듈을 참조한다.
# archive 디렉터리를 sys.path 에 올려야 이 절대 import 들이 해결된다.
# (누락 시 백엔드 import 자체가 ModuleNotFoundError 로 실패 → 앱/서버 미기동.)
import sys as _sys

_archive_dir = str(Path(__file__).resolve().parent / "archive")
if _archive_dir not in _sys.path:
    _sys.path.insert(0, _archive_dir)

from archive import company_report_ver2 as company
from archive import etf_dashboard_ver2 as etf

# 페이지/위젯 템플릿 상수는 ui_templates.py 로 분리(changes_77). 조립/주입 로직은 이 파일에 유지.
from ui_templates import (
    _ASK_WIDGET_HTML,
    _BACKTEST_HTML,
    _FX_JS,
    _FX_STYLE,
    _INDEX_HTML,
    _LANDING_HTML,
    _M4_STYLE,
    _M4_WIRE,
    _MACRO_HTML,
    _MARKET_HTML,
    _MKT_CSS,
    _OVERSEAS_HTML,
    _PDF_VIEW_HTML,
    _REALTIME_HTML,
    _RESEARCH_HTML,
    _RT_JS,
    _RT_STYLE,
    _SECTOR_HTML,
    _WORLD_DETAIL_HTML,
    _WORLD_HTML,
)

# 순수 계산/포맷/SSE 헬퍼는 pure_helpers.py 로 분리(changes_78). 동작 동일, 재내보내기.
from pure_helpers import (
    _bt_signal,
    _clean_closes,
    _clean_ohlc,
    _cu,
    _is_us_dst,
    _krx_won,
    _news_similar,
    _risk_stats,
    _sse_done,
    _sse_failed,
    _sse_progress,
)

# 개발자 모드(changes_81/82) — KMKT_DEV=1 일 때만 활성. 오버레이 + 소스 grep + 노트/세션 저장.
from dev_overlay import (
    _DEV_OVERLAY_HTML,
    dev_locate,
    dev_template_guess,
    dev_write_note,
    dev_write_session,
)


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from market_intel.analyze import etf as E
from market_intel.collectors import dart as dart_c
from market_intel.collectors import naver
from market_intel.httpx_client import Fetcher

PORT = int(os.environ.get("MARKET_PORT", "8780"))
app = Flask(__name__)

# HTML 주입(_inject_*) 앵커 누락 등 '조용한 실패'를 표면화하기 위한 모듈 로거.
# 기존 동작은 바꾸지 않고, 앵커를 못 찾아 주입을 건너뛸 때 경고만 남긴다.
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("kmkt")

# ─────────────────────────────────────────────────────────────────────────────
# 개발자 모드 (KMKT_DEV=1) — 앱에서 고칠 부분을 클릭해 위치+소스+메모를 한 번에 캡처.
#   · 오버레이는 KMKT_DEV=1 일 때만 모든 HTML 응답에 after_request 로 주입(⌘⇧D 토글).
#   · /api/dev/locate : 클릭 요소의 id/class/text 로 소스 파일을 grep → 파일:라인 후보.
#   · /api/dev/note   : 위치+소스후보+메모를 dev_notes/*.md 로 저장(에이전트가 읽음).
#   · 비활성(기본)이면 주입·라우트 모두 no-op → 렌더 골든/일반 동작에 영향 0.
# ─────────────────────────────────────────────────────────────────────────────
_DEV_ENABLED = os.environ.get("KMKT_DEV", "") == "1"
_DEV_ROOT = Path(__file__).resolve().parent.parent


@app.post("/api/dev/locate")
def _dev_locate_route():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    info = request.get_json(silent=True) or {}
    try:
        return jsonify({"candidates": dev_locate(_DEV_ROOT, info),
                        "template_guess": dev_template_guess(info.get("route", ""))})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.post("/api/dev/note")
def _dev_note_route():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    payload = request.get_json(silent=True) or {}
    try:
        path = dev_write_note(_DEV_ROOT, payload)
        return jsonify({"ok": True, "path": path})
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)}), 500


# 세션 배칭(changes_82) — 여러 캡처를 하나의 TODO .md 로 묶는다(단일 사용자 인메모리 스토어).
_DEV_SESSION = {"title": "새 세션", "items": []}


@app.get("/api/dev/session/state")
def _dev_session_state():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    return jsonify({"title": _DEV_SESSION["title"], "items": _DEV_SESSION["items"]})


@app.post("/api/dev/session/add")
def _dev_session_add():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    item = request.get_json(silent=True) or {}
    _DEV_SESSION["items"].append(item)
    return jsonify({"ok": True, "items": _DEV_SESSION["items"]})


@app.post("/api/dev/session/remove")
def _dev_session_remove():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    i = (request.get_json(silent=True) or {}).get("index", -1)
    if isinstance(i, int) and 0 <= i < len(_DEV_SESSION["items"]):
        _DEV_SESSION["items"].pop(i)
    return jsonify({"ok": True, "items": _DEV_SESSION["items"]})


@app.post("/api/dev/session/new")
def _dev_session_new():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    title = (request.get_json(silent=True) or {}).get("title") or "새 세션"
    _DEV_SESSION["title"] = title
    _DEV_SESSION["items"] = []
    return jsonify({"ok": True})


@app.post("/api/dev/session/save")
def _dev_session_save():
    if not _DEV_ENABLED:
        return jsonify({"error": "dev mode off"}), 403
    title = (request.get_json(silent=True) or {}).get("title")
    if title:
        _DEV_SESSION["title"] = title
    if not _DEV_SESSION["items"]:
        return jsonify({"ok": False, "error": "세션이 비어 있습니다"}), 400
    try:
        path = dev_write_session(_DEV_ROOT, _DEV_SESSION)
        _DEV_SESSION["items"] = []
        return jsonify({"ok": True, "path": path})
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)}), 500


@app.after_request
def _dev_inject(resp):
    """KMKT_DEV=1 이면 모든 HTML 페이지(iframe 포함) </body> 앞에 오버레이 1회 주입."""
    if not _DEV_ENABLED:
        return resp
    try:
        if getattr(resp, "direct_passthrough", False):
            return resp
        ctype = resp.headers.get("Content-Type", "")
        if "text/html" not in ctype:
            return resp
        body = resp.get_data(as_text=True)
        if "</body>" in body and 'id="kmktDev"' not in body:
            resp.set_data(body.replace("</body>", _DEV_OVERLAY_HTML + "</body>", 1))
    except Exception:  # noqa: BLE001  (dev convenience must never break a response)
        return resp
    return resp

MARKET_PROXY = "069500"   # KODEX 200 — CAPM/베타 시장 대용치

# 색상
C_UP = "#c0392b"
C_DOWN = "#2e75b6"
C_NAVY = "#1F3864"
C_INK = "#cdd6f4"
C_VIOLET = "#9b6bff"
C_CYAN = "#36c6ff"
C_GREEN = "#7dfac0"


# ════════════════ 앱 로고 (favicon · 브랜드) ════════════════
# 네이티브 앱 아이콘(application_build/icon.png)을 웹 UI 의 favicon·브랜드 로고로
# 그대로 재사용 — 앱 아이콘과 대시보드 로고를 단일 소스로 일치시킨다.
# 동결(.app) 상태에서는 PyInstaller 가 번들 루트에 풀어둔 icon.png 를 쓴다(spec 참조).
def _logo_path() -> Path | None:
    cands: list[Path] = []
    env = os.environ.get("KMKT_LOGO")
    if env:
        cands.append(Path(env))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cands.append(Path(meipass) / "icon.png")
    root = Path(__file__).resolve().parent.parent
    cands.append(root / "application_build" / "icon.png")
    cands.append(root / "icon.png")
    for c in cands:
        try:
            if c and c.is_file():
                return c
        except Exception:  # noqa: BLE001
            pass
    return None


_LOGO_CACHE: dict[str, bytes] = {}


def _logo_bytes() -> bytes | None:
    if "png" not in _LOGO_CACHE:
        p = _logo_path()
        _LOGO_CACHE["png"] = p.read_bytes() if p else b""
    data = _LOGO_CACHE["png"]
    return data or None


# ════════════════ 캐싱 (SSD + RAM) ════════════════
_CACHE_DIR = Path.home() / ".cache" / "kmkt_m4"


# ════════════════ 한국투자증권(KIS) 실시간 시세 ════════════════
# 현재가(.ph-price)만 실시간으로 갱신하기 위한 최소 백엔드.
#   토큰: oauth2/tokenP (24h 유효) → 메모리 + 디스크 캐시 (KIS 는 분당 1회 발급 제한).
#   현재가: inquire-price (tr_id FHKST01010100, FID_COND_MRKT_DIV_CODE="J").
#   주식·ETF 모두 시장코드 "J"(KRX) 로 동일 조회.
_KIS_BASE = os.environ.get("KIS_BASE", "https://openapi.koreainvestment.com:9443")
_KIS_ENV_FILE = Path(__file__).resolve().parent / "한국투자증권" / "API_Key_한국투자증권.env"
_KIS_TOKEN_FILE = _CACHE_DIR / "kis_token.json"
_KIS_LOCK = threading.Lock()
_KIS_TOKEN: dict = {"access_token": None, "expire": 0.0}
_KIS_LAST_CALL = {"t": 0.0}                 # 초당 호출 스로틀
_KIS_PRICE_CACHE: dict[str, tuple[dict, float]] = {}   # code -> (payload, ts) 마이크로 캐시
_KIS_PRICE_TTL = 0.8
_KIS_INDEX_CLOSED_CACHE: dict[str, tuple[dict, float]] = {}  # 장 마감 종가 캐시 (5분 TTL)
_KIS_INDEX_CLOSED_TTL = 300.0


def _kis_keys() -> tuple[str | None, str | None]:
    """환경변수 우선, 없으면 .env 의 주석 아닌 두 줄(앱키·앱시크릿)."""
    ak = os.environ.get("KIS_APP_KEY")
    sk = os.environ.get("KIS_APP_SECRET")
    if ak and sk:
        return ak.strip(), sk.strip()
    try:
        lines = [ln.strip() for ln in _KIS_ENV_FILE.read_text(encoding="utf-8").splitlines()]
        vals = [ln for ln in lines if ln and not ln.startswith("#")]
        if len(vals) >= 2:
            return vals[0], vals[1]
    except Exception:  # noqa: BLE001
        pass
    return None, None


def _kis_token() -> str | None:
    """유효한 접근토큰 반환. 메모리→디스크→신규발급 순. 발급은 분당 1회 제한이라 적극 캐시."""
    now = time.time()
    with _KIS_LOCK:
        if _KIS_TOKEN["access_token"] and now < _KIS_TOKEN["expire"] - 60:
            return _KIS_TOKEN["access_token"]
        # 디스크 캐시 시도
        try:
            d = json.loads(_KIS_TOKEN_FILE.read_text(encoding="utf-8"))
            if d.get("access_token") and now < float(d.get("expire", 0)) - 60:
                _KIS_TOKEN.update(access_token=d["access_token"], expire=float(d["expire"]))
                return _KIS_TOKEN["access_token"]
        except Exception:  # noqa: BLE001
            pass
        ak, sk = _kis_keys()
        if not ak or not sk:
            return None
        try:
            r = httpx.post(f"{_KIS_BASE}/oauth2/tokenP", timeout=12,
                           json={"grant_type": "client_credentials", "appkey": ak, "appsecret": sk})
            j = r.json()
            tok = j.get("access_token")
            if not tok:
                return None
            expire = now + float(j.get("expires_in", 86400))
            _KIS_TOKEN.update(access_token=tok, expire=expire)
            try:
                _CACHE_DIR.mkdir(parents=True, exist_ok=True)
                _KIS_TOKEN_FILE.write_text(json.dumps({"access_token": tok, "expire": expire}),
                                           encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
            return tok
        except Exception:  # noqa: BLE001
            return None


_SNAPSHOT_FILE = _CACHE_DIR / "market_state_snapshot.json"
_MARKET_SNAPSHOT = None

def _get_snapshot(key: str) -> dict | None:
    global _MARKET_SNAPSHOT
    if _MARKET_SNAPSHOT is None:
        if _SNAPSHOT_FILE.exists():
            try:
                _MARKET_SNAPSHOT = json.loads(_SNAPSHOT_FILE.read_text("utf-8"))
            except Exception:
                _MARKET_SNAPSHOT = {}
        else:
            _MARKET_SNAPSHOT = {}
    return _MARKET_SNAPSHOT.get(key)

def _update_snapshot(key: str, data: dict) -> None:
    global _MARKET_SNAPSHOT
    if _MARKET_SNAPSHOT is None:
        _get_snapshot("init")
    _MARKET_SNAPSHOT[key] = data
    try:
        _SNAPSHOT_FILE.write_text(json.dumps(_MARKET_SNAPSHOT, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def _kis_sign_to_dir(sign: str) -> str:
    # KIS prdy_vrss_sign: 1 상한·2 상승 → ▲ / 3 보합 → - / 4 하한·5 하락 → ▼
    return {"1": "▲", "2": "▲", "4": "▼", "5": "▼"}.get(str(sign), "-")


_NAVER_IDX = {"0001": ("KOSPI", "KOSPI"), "1001": ("KOSDAQ", "KOSDAQ"),
              "2001": ("KPI200", "KOSPI200")}


def _naver_index_fallback(iscd: str = "0001") -> dict | None:
    """네이버 금융 지수 조회 (KIS 장 마감·개장 전 종가 폴백) — KOSPI/KOSDAQ/KOSPI200.
    개장 전·폐장 시 KIS 업종현재지수[063]가 전일대비를 0 으로 주는 문제를 회피해
    직전 세션 종가·등락을 가져온다. 성공 시 is_closed=True 포함 dict 반환."""
    naver_code, disp = _NAVER_IDX.get(iscd, ("KOSPI", "KOSPI"))

    def _f(s: object) -> float:
        try:
            return float(str(s).replace(",", "").strip())
        except Exception:  # noqa: BLE001
            return 0.0

    hdrs = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://finance.naver.com/"}

    def _build(d: dict) -> dict | None:
        val = _f(d.get("closePrice") or d.get("currentPrice") or 0)
        if val <= 0:
            return None
        chg = _f(d.get("compareToPreviousClosePrice") or d.get("cv") or 0)
        pct = _f(d.get("fluctuationsRatio") or d.get("cr") or 0)
        direction = "▲" if chg > 0 else ("▼" if chg < 0 else "-")
        return {"ok": True, "code": iscd, "name": disp,
                "value": val, "change": chg, "change_pct": pct,
                "direction": direction, "is_closed": True}

    # ① 일별 차트 — 직전 '완료된' 세션 종가 대 그 전일 종가. 개장 전·폐장 시 실시간 API 가
    #    전일대비를 0 으로 리셋하므로(KIS·네이버 공통) 차트로 직전 세션 등락을 계산한다.
    try:
        from datetime import timedelta
        start = (date.today() - timedelta(days=14)).strftime("%Y%m%d") + "000000"
        end = date.today().strftime("%Y%m%d") + "235959"
        r = httpx.get(
            f"https://api.stock.naver.com/chart/domestic/index/{naver_code}/day"
            f"?startDateTime={start}&endDateTime={end}&timeframe=day",
            timeout=6, headers=hdrs)
        items = r.json()
        if isinstance(items, list) and len(items) >= 2:
            val = _f(items[-1].get("closePrice") or 0)
            prev = _f(items[-2].get("closePrice") or 0)
            if val > 0 and prev > 0:
                chg = val - prev
                pct = round(chg / prev * 100, 2) if prev else 0.0
                direction = "▲" if chg > 0 else ("▼" if chg < 0 else "-")
                return {"ok": True, "code": iscd, "name": disp,
                        "value": val, "change": round(chg, 2), "change_pct": pct,
                        "direction": direction, "is_closed": True}
    except Exception:  # noqa: BLE001
        pass

    # ② m.stock.naver.com (실시간 — 장중 폐장 직후엔 정확)
    try:
        r = httpx.get(f"https://m.stock.naver.com/api/index/{naver_code}/basic",
                      timeout=6, headers=hdrs)
        result = _build(r.json())
        if result:
            return result
    except Exception:  # noqa: BLE001
        pass

    # ③ polling.finance.naver.com — {"datas":[{...}], ...}
    try:
        r = httpx.get(f"https://polling.finance.naver.com/api/realtime/domestic/index/{naver_code}",
                      timeout=6, headers=hdrs)
        j = r.json()
        datas = j.get("datas") or []
        if datas:
            result = _build(datas[0])
            if result:
                return result
    except Exception:  # noqa: BLE001
        pass

    return None


def _naver_kospi_fallback() -> dict | None:
    """하위호환 별칭 — KOSPI 종가 폴백."""
    return _naver_index_fallback("0001")


def _kis_price_raw(code: str, mkt: str) -> dict | None:
    """inquire-price 1회 호출 (mkt: J=KRX / NX=NXT / UN=통합). 실패·0가격 → None."""
    tok = _kis_token()
    if not tok:
        return None
    ak, sk = _kis_keys()
    with _KIS_LOCK:
        gap = time.time() - _KIS_LAST_CALL["t"]
        if gap < 0.06:
            time.sleep(0.06 - gap)
        _KIS_LAST_CALL["t"] = time.time()
    try:
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-price", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKST01010100", "custtype": "P"},
                      params={"FID_COND_MRKT_DIV_CODE": mkt, "FID_INPUT_ISCD": code})
        j = r.json()
        if j.get("rt_cd") != "0":
            return None
        o = j.get("output", {})
        price = float(o.get("stck_prpr") or 0)
        if price <= 0:
            return None
        return {"price": price, "change": float(o.get("prdy_vrss") or 0),
                "change_pct": float(o.get("prdy_ctrt") or 0),
                "direction": _kis_sign_to_dir(o.get("prdy_vrss_sign"))}
    except Exception:  # noqa: BLE001
        return None


_LASTSESS_CACHE: dict[str, tuple[dict, float]] = {}


def _kis_last_session(code: str) -> dict | None:
    """직전 '실제 체결' 세션의 종가·전일대비 — 일별시세(FHKST03010100).

    개장 전(pre)·폐장 후 KIS inquire-price 는 전일대비를 0 으로 주므로
    (당일 미체결), 직전 거래일의 종가·등락을 일별 차트에서 가져온다. 300초 캐시.
    """
    cached = _LASTSESS_CACHE.get(code)
    if cached and (time.time() - cached[1]) < 300.0:
        return cached[0]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return None
    try:
        from datetime import timedelta
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                      timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKST03010100", "custtype": "P"},
                      params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code,
                              "FID_INPUT_DATE_1": (date.today() - timedelta(days=15)).strftime("%Y%m%d"),
                              "FID_INPUT_DATE_2": date.today().strftime("%Y%m%d"),
                              "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"})
        j = r.json()
        rows = j.get("output2") or []
        # output2 는 최신일 우선. 당일 미체결 행(전일대비 0)은 건너뛰고 직전 실체결 세션 선택.
        pick = None
        for o in rows:
            clpr = float(o.get("stck_clpr") or 0)
            vrss = float(o.get("prdy_vrss") or 0)
            if clpr <= 0:
                continue
            if pick is None:
                pick = o            # 폴백(전부 0이어도 최신행 사용)
            if vrss != 0:
                pick = o
                break
        if pick is None:
            return None
        clpr = float(pick.get("stck_clpr") or 0)
        vrss = float(pick.get("prdy_vrss") or 0)
        base = clpr - vrss
        pct = (vrss / base * 100) if base else 0.0
        d = {"price": clpr, "change": vrss, "change_pct": round(pct, 2),
             "direction": _kis_sign_to_dir(pick.get("prdy_vrss_sign"))}
        _LASTSESS_CACHE[code] = (d, time.time())
        return d
    except Exception:  # noqa: BLE001
        return None


def _kis_price(code: str) -> dict:
    """현재가 조회 — 장 상태에 따라 KRX/NXT/직전종가 자동 선택 (작업1·3).

    · KRX 정규장(09:00~15:30 개장일): KRX(J) 실시간 시세
    · KRX 폐장 후 NXT 개장(프리 08:00~08:50 · 애프터 15:30~20:00): NXT(NX) 시세
    · 그 외(개장 전·폐장·휴장): 직전 거래일 종가·등락(일별시세) — inquire-price 가
      전일대비를 0 으로 주는 문제 회피. 실패 시 통합(UN) 폴백.
    반환: {ok, price, change, change_pct, direction, market_open, src, phase, last_close}
    """
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return {"ok": False, "msg": "invalid code"}
    st = _market_state()
    ckey = f"{code}:{st['src'] or 'CL'}"
    now = time.time()
    cached = _KIS_PRICE_CACHE.get(ckey)
    ttl = _KIS_PRICE_TTL if st["open"] else 60.0     # 폐장엔 종가 고정 — 길게 캐시
    if cached and (now - cached[1]) < ttl:
        return cached[0]
    if st["src"] == "KRX":
        d, src = _kis_price_raw(code, "J"), "KRX"
    elif st["src"] == "NXT":
        d, src = _kis_price_raw(code, "NX"), "NXT"
        if d is None:                                 # NXT 미체결 종목 → 통합 폴백
            d, src = _kis_price_raw(code, "UN"), "NXT"
    else:                                             # 개장 전·폐장·휴장 → 직전 세션 종가
        d, src = _kis_last_session(code), "CLOSED"
        if d is None:
            d = _kis_price_raw(code, "UN")
    if d is None:
        snap = _get_snapshot(f"price_{code}")
        if snap:
            _KIS_PRICE_CACHE[ckey] = (snap, time.time())
            return snap
        return {"ok": False, "msg": "no price"}
    payload = {"ok": True, "code": code, **d,
               "market_open": st["open"], "src": src,
               "phase": st["phase"], "last_close": st["last_close"]}
    _KIS_PRICE_CACHE[ckey] = (payload, time.time())
    _update_snapshot(f"price_{code}", payload)
    return payload


# 국내 업종지수(KOSPI=0001 / KOSDAQ=1001 / KOSPI200=2001) 현재지수.
#   참고 스펙: 한국투자증권/국내지수 실시간체결 [실시간-026].xlsx (WebSocket H0UPCNT0).
#   여기서는 동일 토큰으로 REST 업종현재지수(FHPUP02100000, 시장코드 "U")를 폴링.
_KIS_INDEX_NAME = {"0001": "KOSPI", "1001": "KOSDAQ", "2001": "KOSPI200"}


def _kis_index(iscd: str = "0001") -> dict:
    """업종지수 현재가 조회. {ok, code, name, value, change, change_pct, direction, is_closed}.
    장 마감 후 KIS 가 0 반환 시 _naver_kospi_fallback() 으로 종가를 가져온다.
    폴백 결과는 _KIS_INDEX_CLOSED_CACHE 에 5분 동안 보관해 불필요한 재호출을 방지한다."""
    iscd = (iscd or "0001").strip()
    now = time.time()
    ckey = "IDX:" + iscd
    ckey_cl = "IDX_CL:" + iscd

    # ① 실시간 캐시 (TTL 0.8s)
    cached = _KIS_PRICE_CACHE.get(ckey)
    if cached and (now - cached[1]) < _KIS_PRICE_TTL:
        return cached[0]

    def _closed_fallback() -> dict:
        """장 마감 종가 캐시 → 네이버 폴백 → 스냅샷 폴백 → 실패."""
        cc = _KIS_INDEX_CLOSED_CACHE.get(ckey_cl)
        if cc and (now - cc[1]) < _KIS_INDEX_CLOSED_TTL:
            return cc[0]
            
        fb = _naver_index_fallback(iscd)
        if fb:
            _KIS_INDEX_CLOSED_CACHE[ckey_cl] = (fb, time.time())
            _update_snapshot(ckey_cl, fb)
            return fb
            
        snap = _get_snapshot(ckey_cl)
        if snap:
            _KIS_INDEX_CLOSED_CACHE[ckey_cl] = (snap, time.time())
            return snap
            
        return {"ok": False, "msg": "no value"}

    # KRX 정규장이 아니면(개장 전·NXT 시간외·폐장·휴장) KIS 063 이 전일대비를 0 으로 주므로
    # 직전 세션 종가·등락(네이버)을 사용 — 지수는 KRX 에서만 거래.
    if _market_state()["src"] != "KRX":
        return _closed_fallback()

    tok = _kis_token()
    if not tok:
        return _closed_fallback()

    ak, sk = _kis_keys()
    # KIS 키가 없으면 API 호출 없이 바로 Naver 폴백
    if not ak or not sk:
        return _closed_fallback()
    with _KIS_LOCK:
        gap = now - _KIS_LAST_CALL["t"]
        if gap < 0.06:
            time.sleep(0.06 - gap)
        _KIS_LAST_CALL["t"] = time.time()
    try:
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-index-price", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHPUP02100000", "custtype": "P"},
                      params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": iscd})
        j = r.json()
        o = j.get("output", {})
        value = float(o.get("bstp_nmix_prpr") or 0)
        # KIS 오류 코드 또는 지수값 0 → 장 마감/주말 → 종가 폴백
        if j.get("rt_cd") != "0" or value <= 0:
            return _closed_fallback()
        # 정상 실시간 데이터 → 장 마감 캐시 초기화
        _KIS_INDEX_CLOSED_CACHE.pop(ckey_cl, None)
        def _i(v):
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return None
        payload = {"ok": True, "code": iscd, "name": _KIS_INDEX_NAME.get(iscd, iscd),
                   "value": value, "change": float(o.get("bstp_nmix_prdy_vrss") or 0),
                   "change_pct": float(o.get("bstp_nmix_prdy_ctrt") or 0),
                   "direction": _kis_sign_to_dir(o.get("prdy_vrss_sign")),
                   "up_cnt": _i(o.get("ascn_issu_cnt")), "down_cnt": _i(o.get("down_issu_cnt")),
                   "flat_cnt": _i(o.get("stnr_issu_cnt")),
                   "uplm_cnt": _i(o.get("uplm_issu_cnt")), "lslm_cnt": _i(o.get("lslm_issu_cnt")),
                   "is_closed": False}
        _KIS_PRICE_CACHE[ckey] = (payload, time.time())
        _update_snapshot(ckey_cl, payload)
        return payload
    except Exception as e:  # noqa: BLE001
        return _closed_fallback()


# ════════════════ 장 운영 상태 (작업2·3) ════════════════
# 국내휴장일조회[국내주식-040](CTCA0903R, 1일 1회 권장 → 디스크 캐시) + 시계 기반 상태머신.
#   · KRX 정규장: 개장일 09:00 ~ 15:30
#   · NXT:        프리 08:00~08:50 · 메인 09:00~15:20 · 애프터 15:30~20:00
#   → 시세 소스: KRX 정규장 중 "KRX", KRX 폐장 후 NXT 개장 중 "NXT", 그 외 None(폐장)
_HOLIDAY_FILE = _CACHE_DIR / "kis_holidays.json"
_HOLIDAY: dict = {"fetched": "", "days": {}}   # days: {"YYYYMMDD": "Y"/"N"(opnd_yn)}
_MKT_STATE_CACHE: dict = {"ts": 0.0, "state": None}


def _load_holidays() -> dict:
    """개장일 여부 맵. 하루 1회 KIS 휴장일 API 호출(기준일 7일 전 → 과거·미래 커버)."""
    today = date.today().strftime("%Y%m%d")
    if _HOLIDAY["fetched"] == today and _HOLIDAY["days"]:
        return _HOLIDAY["days"]
    try:                                          # 디스크 캐시 (당일분)
        d = json.loads(_HOLIDAY_FILE.read_text(encoding="utf-8"))
        if d.get("fetched") == today and d.get("days"):
            _HOLIDAY.update(d)
            return _HOLIDAY["days"]
    except Exception:  # noqa: BLE001
        pass
    tok = _kis_token()
    ak, sk = _kis_keys()
    days: dict[str, str] = {}
    if tok and ak:
        try:
            from datetime import timedelta
            bass = (date.today() - timedelta(days=7)).strftime("%Y%m%d")
            with _KIS_LOCK:
                gap = time.time() - _KIS_LAST_CALL["t"]
                if gap < 0.06:
                    time.sleep(0.06 - gap)
                _KIS_LAST_CALL["t"] = time.time()
            r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/chk-holiday",
                          timeout=10,
                          headers={"authorization": f"Bearer {tok}", "appkey": ak,
                                   "appsecret": sk, "tr_id": "CTCA0903R", "custtype": "P"},
                          params={"BASS_DT": bass, "CTX_AREA_NK": "", "CTX_AREA_FK": ""})
            j = r.json()
            for o in (j.get("output") or []):
                if o.get("bass_dt"):
                    days[str(o["bass_dt"])] = str(o.get("opnd_yn") or "N")
        except Exception:  # noqa: BLE001
            days = {}
    if days:
        _HOLIDAY.update(fetched=today, days=days)
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _HOLIDAY_FILE.write_text(json.dumps(_HOLIDAY), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return days


def _is_open_day(d: date) -> bool:
    """개장일 여부 — KIS 휴장일 API 우선, 실패 시 주말 판정 폴백."""
    days = _load_holidays()
    key = d.strftime("%Y%m%d")
    if key in days:
        return days[key] == "Y"
    return d.weekday() < 5


def _market_state() -> dict:
    """현재 장 상태. {open, src(KRX/NXT/None), phase, last_close} (5초 캐시).

    phase: "open"(개장) | "pre"(개장 전) | "closed"(폐장) | "holiday"(휴장)
      · open   : KRX 정규장 또는 NXT 프리·애프터 진행 중
      · pre    : 거래일 오전 6시 이후 ~ 당일 장 시작 전(첫 세션 개장 대기, 세션 공백 포함)
      · closed : 거래일 오전 6시 이전 또는 NXT 폐장(20:00) 이후
      · holiday: 휴장일(주말·공휴일)
    """
    now = time.time()
    if _MKT_STATE_CACHE["state"] and (now - _MKT_STATE_CACHE["ts"]) < 5.0:
        return _MKT_STATE_CACHE["state"]
    from datetime import datetime, timedelta
    dt = datetime.now()
    today_open = _is_open_day(dt.date())
    hm = dt.hour * 60 + dt.minute
    src = None
    if today_open:
        if 9 * 60 <= hm < 15 * 60 + 30:
            src = "KRX"                     # KRX 정규장 (NXT 메인과 병행 — KRX 우선)
        elif 8 * 60 <= hm < 8 * 60 + 50 or 15 * 60 + 30 <= hm < 20 * 60:
            src = "NXT"                     # NXT 프리/애프터마켓
    # 장 단계(phase) 판정
    if src is not None:
        phase = "open"
    elif not today_open:
        phase = "holiday"
    elif 6 * 60 <= hm < 20 * 60:
        phase = "pre"                       # 거래일 06:00 이후 ~ 당일 장 종료 전 = 개장 전
    else:
        phase = "closed"                    # 거래일 06:00 이전 또는 20:00 이후
    # 최종 폐장시각 = 직전 개장일의 NXT 폐장(20:00)
    d = dt.date()
    if not (today_open and hm >= 20 * 60):  # 오늘 20시 이전이거나 휴장 → 직전 개장일로
        d = d - timedelta(days=1)
        for _ in range(14):
            if _is_open_day(d):
                break
            d -= timedelta(days=1)
    state = {"open": src is not None, "src": src, "phase": phase,
             "last_close": f"{d.month:02d}.{d.day:02d} 20:00"}
    _MKT_STATE_CACHE.update(ts=now, state=state)
    return state


def _index_phase() -> str:
    """KRX 전용 상품(지수·시총·업종 랭킹)의 표시 단계. NXT 시간외는 KRX 기준 pre/closed 로 본다.
    KRX 정규장 중에만 'open'(실시간). 그 외 거래일 09:00 전='pre', 이후='closed', 휴장='holiday'."""
    st = _market_state()
    if st["src"] == "KRX":
        return "open"
    if st["phase"] == "holiday":
        return "holiday"
    from datetime import datetime
    hm = datetime.now().hour * 60 + datetime.now().minute
    return "pre" if hm < 9 * 60 else "closed"


def _zero_if_pre(d: dict, phase: str) -> dict:
    """개장 전(pre): 당일 미개장 → 전일 종가만 표시하고 등락은 0 으로(전일 등락 표기 방지)."""
    if phase == "pre" and isinstance(d, dict):
        d = dict(d)                       # 캐시 원본 보호 위해 복사
        d["change"] = 0.0
        d["change_pct"] = 0.0
        d["direction"] = "-"
    return d


# ════════════════ 해외주식 장 상태 ════════════════
_OV_MKT_STATE_CACHE = {"ts": 0.0, "state": {}}
_OV_HOLIDAY_CACHE = {}  # { 'YYYYMMDD': bool }


def _is_ov_holiday(dt_str: str) -> bool:
    if dt_str in _OV_HOLIDAY_CACHE:
        return _OV_HOLIDAY_CACHE[dt_str]
    # Call KIS API for countries-holiday
    j = _rt_kis_get("/uapi/overseas-stock/v1/quotations/countries-holiday", "CTOS5011R", {"TRAD_DT": dt_str, "CTX_AREA_NK": "", "CTX_AREA_FK": ""})
    is_holiday = False
    if j and j.get("output"):
        out = j.get("output", [])
        if isinstance(out, dict): out = [out]
        # KIS returns list of countries or specific holidays. If US ('미국' or similar) is holiday.
        for item in out:
            # check if US is included
            if '미국' in str(item.get('natn_name', '')) and item.get('hldy_yn') == 'Y':
                is_holiday = True
                break
    _OV_HOLIDAY_CACHE[dt_str] = is_holiday
    return is_holiday

def _ov_market_state(excd: str = "NAS") -> dict:
    """해외주식 현재 장 상태 (미국 기준).
    phase: "open" | "pre" | "closed" | "holiday"
    """
    now = time.time()
    if _OV_MKT_STATE_CACHE["state"] and (now - _OV_MKT_STATE_CACHE["ts"]) < 5.0:
        return _OV_MKT_STATE_CACHE["state"]
    
    from datetime import datetime, timedelta
    dt = datetime.now()
    hm = dt.hour * 60 + dt.minute
    
    # KST date for the US trading day (US trading day starts in KST night)
    # If it is before 14:00 KST, it belongs to the previous US trading day's schedule.
    # To determine if today is a holiday in the US, we check the US date.
    us_dt = dt - timedelta(hours=14)
    dt_str = us_dt.strftime("%Y%m%d")
    is_holiday = _is_ov_holiday(dt_str)
    
    is_dst = _is_us_dst(us_dt)
    
    # US Market Open (KST): DST 22:30 ~ 05:00 / Normal 23:30 ~ 06:00
    open_start = 22 * 60 + 30 if is_dst else 23 * 60 + 30
    open_end = 5 * 60 if is_dst else 6 * 60
    
    # Pre-market (KST): DST 17:00 ~ 22:30 / Normal 18:00 ~ 23:30
    pre_start = 17 * 60 if is_dst else 18 * 60
    
    # Is weekend in US?
    is_weekend = us_dt.weekday() >= 5
    
    phase = "closed"
    if is_weekend or is_holiday:
        phase = "holiday"
    else:
        if open_start <= hm or hm < open_end:
            phase = "open"
        elif pre_start <= hm < open_start:
            phase = "pre"
            
    name = "휴장" if phase == "holiday" else ("장마감" if phase == "closed" else ("장중" if phase == "open" else "프리마켓"))
    state = {"open": phase == "open", "phase": phase, "name": name, "mkt": "US"}
    _OV_MKT_STATE_CACHE.update(ts=now, state=state)
    return state


# ════════════════ ETF 실시간 NAV (작업1) ════════════════
# 국내ETF NAV추이 [실시간-051](웹소켓 H0STNAV0) 1회성 수신 → 장중 실시간 iNAV.
# 폐장·타임아웃 시 KIS ETF/ETN 현재가 REST(FHPST02400000)의 nav 필드 폴백.
_NAV_CACHE: dict[str, tuple[dict, float]] = {}
_NAV_TTL_OPEN, _NAV_TTL_CLOSED = 20.0, 300.0
_WS_APPROVAL: dict = {"key": None, "ts": 0.0}


def _kis_ws_approval() -> str | None:
    """웹소켓 접속키 (/oauth2/Approval) — 12시간 캐시."""
    if _WS_APPROVAL["key"] and (time.time() - _WS_APPROVAL["ts"]) < 43200:
        return _WS_APPROVAL["key"]
    ak, sk = _kis_keys()
    if not ak or not sk:
        return None
    try:
        r = httpx.post(f"{_KIS_BASE}/oauth2/Approval", timeout=10,
                       json={"grant_type": "client_credentials", "appkey": ak, "secretkey": sk})
        key = r.json().get("approval_key")
        if key:
            _WS_APPROVAL.update(key=key, ts=time.time())
        return key
    except Exception:  # noqa: BLE001
        return None


async def _ws_nav_once(code: str, timeout: float = 3.0) -> dict | None:
    """H0STNAV0 구독 → 첫 NAV 푸시 1건 파싱. 장중에만 데이터가 흐른다."""
    approval = _kis_ws_approval()
    if not approval:
        return None
    try:
        import websockets
        sub = json.dumps({"header": {"approval_key": approval, "custtype": "P",
                                     "tr_type": "1", "content-type": "utf-8"},
                          "body": {"input": {"tr_id": "H0STNAV0", "tr_key": code}}})
        async with websockets.connect(
                "ws://ops.koreainvestment.com:21000/tryitout/H0STNAV0",
                open_timeout=4) as ws:
            await ws.send(sub)
            t0 = time.time()
            while time.time() - t0 < timeout:
                msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                if isinstance(msg, str) and msg.startswith(("0|", "1|")):
                    f = msg.split("|")[3].split("^")
                    # MKSC_SHRN_ISCD^NAV^SIGN^VRSS^CTRT^OPRC^HPRC^LPRC
                    nav = float(f[1])
                    sign = f[2]
                    return {"nav": nav,
                            "nav_vrss": float(f[3]), "nav_ctrt": float(f[4]),
                            "dirc": "▲" if sign in ("1", "2") else ("▼" if sign in ("4", "5") else ""),
                            "src": "ws"}
    except Exception:  # noqa: BLE001
        return None
    return None


def _kis_etf_nav_rest(code: str) -> dict | None:
    """KIS ETF/ETN 현재가(REST) — nav/전일대비/괴리율."""
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return None
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/etfetn/v1/quotations/inquire-price", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHPST02400000", "custtype": "P"},
                      params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code})
        j = r.json()
        if j.get("rt_cd") != "0":
            return None
        o = j.get("output") or {}
        nav = float(o.get("nav") or 0)
        if nav <= 0:
            return None
        sign = str(o.get("nav_prdy_vrss_sign") or "3")
        return {"nav": nav,
                "nav_vrss": float(o.get("nav_prdy_vrss") or 0),
                "nav_ctrt": float(o.get("nav_prdy_ctrt") or 0),
                "dirc": "▲" if sign in ("1", "2") else ("▼" if sign in ("4", "5") else ""),
                "dprt": float(o.get("dprt") or 0), "src": "rest"}
    except Exception:  # noqa: BLE001
        return None


def _kis_etf_nav(code: str) -> dict:
    """ETF 실시간 iNAV — 장중 웹소켓(H0STNAV0) 우선, 폐장/실패 시 REST nav."""
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return {"ok": False, "msg": "invalid code"}
    st = _market_state()
    ttl = _NAV_TTL_OPEN if st["src"] == "KRX" else _NAV_TTL_CLOSED
    cached = _NAV_CACHE.get(code)
    if cached and (time.time() - cached[1]) < ttl:
        return cached[0]
    d = None
    if st["src"] == "KRX":                       # NAV 산출은 KRX 정규장 시간
        try:
            d = asyncio.run(_ws_nav_once(code))
        except Exception:  # noqa: BLE001
            d = None
    if d is None:
        d = _kis_etf_nav_rest(code)
    if d is None:
        return {"ok": False, "msg": "no nav"}
    payload = {"ok": True, "code": code, "market_open": st["src"] == "KRX", **d}
    _NAV_CACHE[code] = (payload, time.time())
    return payload


# ════════════════ 업종 지수 (작업6) ════════════════
# 국내업종 현재지수[v1_국내주식-063](FHPUP02100000) — KIS idxcode.mst 기준 업종코드.
# 구성종목은 시가총액 상위[v1_국내주식-091](FHPST01740000)이 업종코드를 받는 것을 활용.
_SECTOR_KOSPI = [
    ("0005", "음식료·담배"), ("0006", "섬유·의류"), ("0007", "종이·목재"),
    ("0008", "화학"), ("0009", "제약"), ("0010", "비금속"), ("0011", "금속"),
    ("0012", "기계·장비"), ("0013", "전기·전자"), ("0014", "의료·정밀기기"),
    ("0015", "운송장비·부품"), ("0016", "유통"), ("0017", "전기·가스"),
    ("0018", "건설"), ("0019", "운송·창고"), ("0020", "통신"), ("0021", "금융"),
    ("0024", "증권"), ("0025", "보험"), ("0026", "일반서비스"), ("0027", "제조"),
    ("0028", "부동산"), ("0029", "IT 서비스"), ("0030", "오락·문화"),
]
_SECTOR_KOSDAQ = [
    ("1019", "음식료·담배"), ("1020", "섬유·의류"), ("1021", "종이·목재"),
    ("1022", "출판·매체복제"), ("1023", "화학"), ("1024", "제약"), ("1025", "비금속"),
    ("1026", "금속"), ("1027", "기계·장비"), ("1028", "전기·전자"),
    ("1029", "의료·정밀기기"), ("1030", "운송장비·부품"), ("1031", "기타제조"),
    ("1032", "통신"), ("1033", "IT 서비스"), ("1006", "일반서비스"), ("1009", "제조"),
    ("1010", "건설"), ("1011", "유통"), ("1013", "운송·창고"), ("1014", "금융"),
    ("1015", "오락·문화"),
]
_SECTOR_CACHE: dict[str, tuple[list, float]] = {}
_SECTOR_TTL = 45.0


async def _afetch_sector_indices(pairs: list[tuple[str, str]]) -> list[dict]:
    """업종 지수 병렬 수집 (세마포어 6 — KIS 초당 호출 한도 보호)."""
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    sem = asyncio.Semaphore(6)
    out: list[dict] = []

    async def one(cl: httpx.AsyncClient, iscd: str, name: str):
        async with sem:
            try:
                r = await cl.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-index-price",
                                 headers={"authorization": f"Bearer {tok}", "appkey": ak,
                                          "appsecret": sk, "tr_id": "FHPUP02100000",
                                          "custtype": "P"},
                                 params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": iscd})
                j = r.json()
                o = j.get("output") or {}
                v = float(o.get("bstp_nmix_prpr") or 0)
                if j.get("rt_cd") != "0" or v <= 0:
                    return
                out.append({
                    "code": iscd, "name": name, "value": v,
                    "change": float(o.get("bstp_nmix_prdy_vrss") or 0),
                    "change_pct": float(o.get("bstp_nmix_prdy_ctrt") or 0),
                    "sign": str(o.get("prdy_vrss_sign") or "3"),
                    "open": float(o.get("bstp_nmix_oprc") or 0),
                    "high": float(o.get("bstp_nmix_hgpr") or 0),
                    "low": float(o.get("bstp_nmix_lwpr") or 0),
                    "volume": float(o.get("acml_vol") or 0),
                    "up_cnt": int(float(o.get("ascn_issu_cnt") or 0)),
                    "down_cnt": int(float(o.get("down_issu_cnt") or 0)),
                })
            except Exception:  # noqa: BLE001
                pass

    async with httpx.AsyncClient(timeout=10) as cl:
        await asyncio.gather(*[one(cl, c, n) for c, n in pairs])
    return out


def _sector_indices(mkt: str) -> list[dict]:
    """업종 지수 목록 (mkt: 'kospi'|'kosdaq') — 45초 캐시."""
    mkt = "kosdaq" if str(mkt).lower() in ("kosdaq", "1", "1001") else "kospi"
    now = time.time()
    cached = _SECTOR_CACHE.get(mkt)
    if cached and (now - cached[1]) < _SECTOR_TTL:
        return cached[0]
    pairs = _SECTOR_KOSDAQ if mkt == "kosdaq" else _SECTOR_KOSPI
    try:
        rows = asyncio.run(_afetch_sector_indices(pairs))
    except Exception:  # noqa: BLE001
        rows = []
    if rows:
        order = {c: i for i, (c, _) in enumerate(pairs)}
        rows.sort(key=lambda r: order.get(r["code"], 99))
        _SECTOR_CACHE[mkt] = (rows, time.time())
    return rows


def _sector_stocks(iscd: str) -> list[dict]:
    """업종 구성종목 시세 — 시가총액 상위[091] (업종코드 입력, 시총순 30종목). 30초 캐시."""
    iscd = (iscd or "").strip()
    if not (iscd.isdigit() and len(iscd) == 4):
        return []
    ckey = "SS:" + iscd
    cached = _SECTOR_CACHE.get(ckey)
    if cached and (time.time() - cached[1]) < 30.0:
        return cached[0]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/ranking/market-cap", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHPST01740000", "custtype": "P"},
                      params={"fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20174",
                              "fid_div_cls_code": "0", "fid_input_iscd": iscd,
                              "fid_trgt_cls_code": "0", "fid_trgt_exls_cls_code": "0",
                              "fid_input_price_1": "", "fid_input_price_2": "",
                              "fid_vol_cnt": ""})
        j = r.json()
        rows = []
        for o in (j.get("output") or []):
            try:
                rows.append({
                    "code": o.get("mksc_shrn_iscd"), "name": o.get("hts_kor_isnm"),
                    "price": float(o.get("stck_prpr") or 0),
                    "change": float(o.get("prdy_vrss") or 0),
                    "change_pct": float(o.get("prdy_ctrt") or 0),
                    "sign": str(o.get("prdy_vrss_sign") or "3"),
                    "volume": float(o.get("acml_vol") or 0),
                    "mcap": float(o.get("stck_avls") or 0),   # 억원
                    "weight": float(o.get("mrkt_whol_avls_rlim") or 0) or None,  # 시장비중 %
                })
            except Exception:  # noqa: BLE001
                continue
        if rows:
            _SECTOR_CACHE[ckey] = (rows, time.time())
        return rows
    except Exception:  # noqa: BLE001
        return []


# ════════════════ 마켓맵 (트리맵: 섹터·기업 시가총액 비중 × 등락 색) ════════════════
# 전 업종을 병렬로 시가총액상위[091] 조회 → 섹터별 상위 종목(시총·등락)로 Plotly Treemap.
_MARKETMAP_CACHE: dict[str, tuple[str, float]] = {}
_MARKETMAP_TTL = 120.0
_MARKETMAP_TOPN = 14            # 섹터당 시총 상위 N 종목


async def _afetch_marketmap(pairs: list[tuple[str, str]]) -> list[dict]:
    """전 업종 시총상위 종목 병렬 수집 (세마포어 5 — KIS 호출 한도 보호)."""
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    sem = asyncio.Semaphore(5)
    out: list[dict] = []

    async def one(cl: httpx.AsyncClient, code: str, name: str) -> None:
        async with sem:
            try:
                r = await cl.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/ranking/market-cap",
                                 headers={"authorization": f"Bearer {tok}", "appkey": ak,
                                          "appsecret": sk, "tr_id": "FHPST01740000",
                                          "custtype": "P"},
                                 params={"fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20174",
                                         "fid_div_cls_code": "0", "fid_input_iscd": code,
                                         "fid_trgt_cls_code": "0", "fid_trgt_exls_cls_code": "0",
                                         "fid_input_price_1": "", "fid_input_price_2": "", "fid_vol_cnt": ""})
                j = r.json()
                stocks = []
                for o in (j.get("output") or [])[:_MARKETMAP_TOPN]:
                    mcap = float(o.get("stck_avls") or 0)
                    if mcap <= 0:
                        continue
                    stocks.append({"code": o.get("mksc_shrn_iscd"), "name": o.get("hts_kor_isnm"),
                                   "mcap": mcap, "chg": float(o.get("prdy_ctrt") or 0)})
                if stocks:
                    out.append({"sector": name, "code": code, "stocks": stocks})
            except Exception:  # noqa: BLE001
                pass

    async with httpx.AsyncClient(timeout=12) as cl:
        await asyncio.gather(*[one(cl, c, n) for c, n in pairs])
    return out


def _marketmap_fig(mkt: str) -> str | None:
    """마켓맵 Plotly Treemap figure JSON 문자열 (120초 캐시). 데이터 없으면 None."""
    mkt = "kosdaq" if str(mkt).lower() in ("kosdaq", "1", "1001") else "kospi"
    cached = _MARKETMAP_CACHE.get(mkt)
    if cached and (time.time() - cached[1]) < _MARKETMAP_TTL:
        return cached[0]
    # '제조'(0027/1009)는 전기·전자·화학 등 구체 업종을 모두 포함하는 상위 우산 분류 →
    # 종목이 중복 표기되므로 마켓맵에서 제외(구체 업종에만 1회 표기).
    src = _SECTOR_KOSDAQ if mkt == "kosdaq" else _SECTOR_KOSPI
    pairs = [(c, n) for c, n in src if n != "제조"]
    try:
        data = asyncio.run(_afetch_marketmap(pairs))
    except Exception:  # noqa: BLE001
        data = []
    if not data:
        return None
    mname = "코스닥" if mkt == "kosdaq" else "코스피"
    ids = ["ROOT"]; labels = [mname]; parents = [""]; values = [0.0]
    colors = [0.0]; texts = [""]
    root_val = 0.0
    seen: set = set()                                  # 업종 간 종목 중복 제거
    for sec in sorted(data, key=lambda s: -sum(x["mcap"] for x in s["stocks"])):
        stocks = [x for x in sec["stocks"] if x["code"] not in seen]
        for x in stocks:
            seen.add(x["code"])
        if not stocks:
            continue
        sid = "S_" + sec["code"]
        svals = sum(x["mcap"] for x in stocks)
        savg = (sum(x["chg"] * x["mcap"] for x in stocks) / svals) if svals else 0.0
        ids.append(sid); labels.append(sec["sector"]); parents.append("ROOT")
        values.append(svals); colors.append(savg); texts.append("")
        root_val += svals
        for x in stocks:
            ids.append(sid + "_" + str(x["code"])); labels.append(x["name"]); parents.append(sid)
            values.append(x["mcap"]); colors.append(x["chg"])
            texts.append(("+" if x["chg"] > 0 else "") + f"{x['chg']:.2f}%")
    values[0] = root_val
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, text=texts,
        branchvalues="total", sort=True, tiling=dict(pad=2, packing="squarify"),
        marker=dict(colors=colors, cmid=0, cmin=-3, cmax=3,
                    colorscale=[[0, "#2E75B6"], [0.5, "#4a5160"], [1, "#FF3B30"]],
                    line=dict(width=1, color="rgba(11,15,32,.55)")),
        texttemplate="%{label}<br>%{text}", textposition="middle center",
        textfont=dict(size=15, color="#fff", family="-apple-system,BlinkMacSystemFont,sans-serif"),
        hovertemplate="<b>%{label}</b><br>시총 %{value:,.0f}억<br>등락 %{text}<extra></extra>",
        pathbar=dict(visible=True, thickness=22)))
    # 큰 칸=큰 글씨로 자동 스케일(텍스트가 칸에 맞게 축소/확대)되, size 상한을 15 로 올려 큰 칸 가독성↑.
    # uniformtext(minsize=10,mode="hide"): 10px 미만으로 줄여야 들어가는 작은 칸은 라벨을 *숨겨*
    # 얇고 깨알같은 글자로 지저분해지지 않게 한다(가독성·정돈 둘 다 — 세션 Task3).
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      uniformtext=dict(minsize=10, mode="hide"),
                      font=dict(family="-apple-system,BlinkMacSystemFont,sans-serif"))
    figjson = fig.to_json()
    _MARKETMAP_CACHE[mkt] = (figjson, time.time())
    return figjson


# ════════════════ 미국 마켓맵 (S&P 500 섹터 히트맵) — 작업1 ════════════════
# S&P500 구성종목 목록 API 는 유료(Finnhub 403)·Yahoo 벌크는 401 → 핵심 대형주를
# GICS 섹터별로 큐레이션(거래소 N=NASDAQ / Y=NYSE, 가중치=근사 시총 $B). 등락률만
# Finnhub /quote 로 실시간 조회(분당 60콜 한도 내 1버스트, 120초 캐시). 색: 미국 관례
# (상승=초록 / 하락=빨강), -3~+3%.
_US_HEATMAP: dict[str, list[tuple]] = {
    "Technology": [("NVDA", "N", 3300), ("AAPL", "N", 3000), ("MSFT", "N", 2900),
                   ("AVGO", "N", 800), ("ORCL", "Y", 480), ("AMD", "N", 250),
                   ("CRM", "Y", 280), ("CSCO", "N", 240), ("ADBE", "N", 230),
                   ("QCOM", "N", 190), ("TXN", "N", 170), ("AMAT", "N", 160),
                   ("INTC", "N", 130), ("MU", "N", 120)],
    "Communication Services": [("GOOGL", "N", 2100), ("META", "N", 1300), ("NFLX", "N", 300),
                               ("TMUS", "N", 240), ("DIS", "Y", 200), ("VZ", "Y", 180)],
    "Consumer Cyclical": [("AMZN", "N", 2000), ("TSLA", "N", 800), ("HD", "Y", 380),
                          ("MCD", "Y", 210), ("BKNG", "N", 150), ("LOW", "Y", 140),
                          ("NKE", "Y", 110)],
    "Financial Services": [("BRK.B", "Y", 900), ("JPM", "Y", 650), ("V", "Y", 560),
                           ("MA", "Y", 430), ("BAC", "Y", 320), ("WFC", "Y", 230),
                           ("AXP", "Y", 200), ("MS", "Y", 180), ("GS", "Y", 160)],
    "Healthcare": [("LLY", "Y", 800), ("UNH", "Y", 480), ("JNJ", "Y", 380),
                   ("ABBV", "Y", 330), ("MRK", "Y", 250), ("TMO", "Y", 210),
                   ("ABT", "Y", 200)],
    "Consumer Defensive": [("WMT", "Y", 600), ("COST", "N", 400), ("PG", "Y", 380),
                           ("KO", "Y", 270), ("PEP", "N", 230)],
    "Industrials": [("CAT", "Y", 200), ("GE", "Y", 200), ("RTX", "Y", 160),
                    ("HON", "N", 140), ("UNP", "Y", 140)],
    "Energy": [("XOM", "Y", 480), ("CVX", "Y", 290)],
    "Utilities": [("NEE", "Y", 160)],
    "Real Estate": [("AMT", "Y", 90), ("PLD", "Y", 110)],
    "Basic Materials": [("LIN", "N", 220)],
}
_US_SECTOR_KR = {"Technology": "기술", "Communication Services": "커뮤니케이션",
                 "Consumer Cyclical": "경기소비재", "Financial Services": "금융",
                 "Healthcare": "헬스케어", "Consumer Defensive": "필수소비재",
                 "Industrials": "산업재", "Energy": "에너지", "Utilities": "유틸리티",
                 "Real Estate": "리츠/부동산", "Basic Materials": "소재"}
_USMAP_FIG_CACHE: dict[str, tuple[str, float]] = {}
_USMAP_PCT_CACHE: dict = {"pct": None, "ts": 0.0}
_USMAP_TTL = 120.0


def _finnhub_quote(sym: str) -> dict | None:
    """Finnhub /quote → {c:현재가, dp:등락률%}."""
    key = os.environ.get("FINNHUB_KEY", "")
    if not key:
        return None
    try:
        r = httpx.get("https://finnhub.io/api/v1/quote",
                      params={"symbol": sym, "token": key}, timeout=8)
        j = r.json()
        if j.get("dp") is None and not j.get("c"):
            return None
        return {"c": float(j.get("c") or 0), "dp": float(j.get("dp") or 0),
                "d": float(j.get("d") or 0)}
    except Exception:  # noqa: BLE001
        return None


def _usmap_pct() -> dict:
    """전체 큐레이션 종목의 시세(가격+등락) 1회 조회(120초 캐시) — 히트맵 전체/NYSE/NASDAQ 뷰와
    미국 종목 리스트가 모두 공유해 Finnhub 분당 한도(60콜)를 보호한다. {t: {c,dp,d}}."""
    now = time.time()
    if _USMAP_PCT_CACHE["pct"] and (now - _USMAP_PCT_CACHE["ts"]) < _USMAP_TTL:
        return _USMAP_PCT_CACHE["pct"]
    tickers = [t for lst in _US_HEATMAP.values() for (t, _e, _w) in lst]
    quotes: dict[str, dict] = {}
    with _TPE(max_workers=10) as ex:
        futs = {t: ex.submit(_finnhub_quote, t) for t in tickers}
        for t, f in futs.items():
            try:
                v = f.result()
                if v is not None:
                    quotes[t] = v
            except Exception:  # noqa: BLE001
                pass
    if quotes:
        _USMAP_PCT_CACHE.update(pct=quotes, ts=now)
    return quotes


def _usmap_fig(exch: str = "all") -> str | None:
    """미국 S&P500 섹터 히트맵 Plotly Treemap JSON. exch: all|nasdaq|nyse (등락률 캐시 공유)."""
    exch = str(exch or "all").lower()
    flt = "N" if exch in ("nasdaq", "nas", "n") else ("Y" if exch in ("nyse", "nys", "y") else None)
    ck = "nasdaq" if flt == "N" else ("nyse" if flt == "Y" else "all")
    cached = _USMAP_FIG_CACHE.get(ck)
    if cached and (time.time() - cached[1]) < _USMAP_TTL:
        return cached[0]
    pct = _usmap_pct()
    if not pct:
        return None
    items = [(sec, t, w) for sec, lst in _US_HEATMAP.items() for (t, e, w) in lst
             if (flt is None or e == flt)]
    if not items:
        return None
    ids = ["ROOT"]; labels = ["S&P 500"]; parents = [""]; values = [0.0]
    colors = [0.0]; texts = [""]
    root_val = 0.0
    by_sec: dict[str, list] = {}
    for sec, t, w in items:
        if t in pct:
            by_sec.setdefault(sec, []).append((t, w, pct[t]["dp"]))
    for sec in sorted(by_sec, key=lambda s: -sum(w for _t, w, _c in by_sec[s])):
        rows = by_sec[sec]
        sid = "S_" + sec
        svals = sum(w for _t, w, _c in rows)
        savg = sum(c * w for _t, w, c in rows) / svals if svals else 0.0
        ids.append(sid); labels.append(_US_SECTOR_KR.get(sec, sec)); parents.append("ROOT")
        values.append(svals); colors.append(savg); texts.append("")
        root_val += svals
        for t, w, c in rows:
            ids.append(sid + "_" + t); labels.append(t); parents.append(sid)
            values.append(w); colors.append(c)
            texts.append(("+" if c > 0 else "") + f"{c:.2f}%")
    values[0] = root_val
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, text=texts,
        branchvalues="total", sort=True, tiling=dict(pad=2, packing="squarify"),
        marker=dict(colors=colors, cmid=0, cmin=-3, cmax=3,
                    colorscale=[[0, "#cf3a3a"], [0.5, "#4a5160"], [1, "#2e9e5b"]],
                    line=dict(width=1, color="rgba(11,15,32,.55)")),
        texttemplate="%{label}<br>%{text}", textposition="middle center",
        textfont=dict(color="#fff", family="-apple-system,BlinkMacSystemFont,sans-serif"),
        hovertemplate="<b>%{label}</b><br>등락 %{text}<extra></extra>",
        pathbar=dict(visible=True, thickness=22)))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="-apple-system,BlinkMacSystemFont,sans-serif"))
    figjson = fig.to_json()
    _USMAP_FIG_CACHE[ck] = (figjson, time.time())
    return figjson


# ════════════════ 지수 상세 (코스피·코스닥 캔들 차트) ════════════════
_INDEX_CHART_CACHE: dict[str, tuple[dict, float]] = {}
_INDEX_NAME2 = {"0001": "코스피", "1001": "코스닥", "2001": "코스피200"}


def _index_chart(iscd: str = "0001", period: str = "D") -> dict:
    """국내 지수 일/주/월/년봉 — inquire-daily-indexchartprice(FHKUP03500100, 시장 U). 60초 캐시.
    반환: {ok, name, rows:[{d,o,h,l,c,v}], prev_close, amount, hi52, lo52}."""
    iscd = (iscd or "0001").strip()
    period = (period or "D").upper()
    if period not in ("D", "W", "M", "Y"):
        period = "D"
    ckey = f"{iscd}:{period}"
    cached = _INDEX_CHART_CACHE.get(ckey)
    if cached and (time.time() - cached[1]) < 60.0:
        return cached[0]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return {"ok": False, "rows": []}
    from datetime import timedelta
    span = {"D": 120, "W": 800, "M": 4000, "Y": 12000}[period]
    d1 = (date.today() - timedelta(days=span)).strftime("%Y%m%d")
    d2 = date.today().strftime("%Y%m%d")
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice",
                      timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKUP03500100", "custtype": "P"},
                      params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": iscd,
                              "FID_INPUT_DATE_1": d1, "FID_INPUT_DATE_2": d2,
                              "FID_PERIOD_DIV_CODE": period})
        j = r.json()
        if j.get("rt_cd") != "0":
            return {"ok": False, "rows": []}
        rows = []
        for o in (j.get("output2") or []):
            c = float(o.get("bstp_nmix_prpr") or 0)
            if c <= 0:
                continue
            rows.append({"d": o.get("stck_bsop_date"), "o": float(o.get("bstp_nmix_oprc") or 0),
                         "h": float(o.get("bstp_nmix_hgpr") or 0), "l": float(o.get("bstp_nmix_lwpr") or 0),
                         "c": c, "v": float(o.get("acml_vol") or 0)})
        rows.reverse()                                    # 최신→과거 → 과거→최신
        o1 = j.get("output1") or {}
        hs = [x["h"] for x in rows] or [0]
        ls = [x["l"] for x in rows] or [0]
        out = {"ok": bool(rows), "name": _INDEX_NAME2.get(iscd, o1.get("hts_kor_isnm") or iscd),
               "rows": rows, "prev_close": float(o1.get("prdy_nmix") or 0),
               "amount": float(o1.get("acml_tr_pbmn") or 0),
               "hi52": max(hs), "lo52": min(ls)}
        if rows:
            _INDEX_CHART_CACHE[ckey] = (out, time.time())
        return out
    except Exception:  # noqa: BLE001
        return {"ok": False, "rows": []}


# ════════════════ 한국 경제 지표 (한국은행 ECOS) ════════════════
# 기준금리(722Y001)·국고채(817Y002)·소비자물가(901Y009)·원달러(731Y001).
# ECOS 무료데이터는 발표 시차가 있어 최신값이 한두 달 전일 수 있음 → asof(기준시점) 함께 표기.
_ECOS_KEY = os.environ.get("ECOS_KEY", "")
_ECOS_CACHE: dict = {"ts": 0.0, "data": None}
_ECOS_TTL = 3600.0                                       # 1시간 (월간 지표라 자주 안 바뀜)


def _ecos_rows(stat: str, period: str, item: str, start: str, end: str) -> list[dict]:
    """ECOS StatisticSearch → [{t, v}] (오름차순). 실패 시 빈 리스트."""
    if not _ECOS_KEY:
        return []
    url = "/".join(["https://ecos.bok.or.kr/api/StatisticSearch", _ECOS_KEY, "json", "kr",
                    "1", "1000", stat, period, start, end, item])
    try:
        j = httpx.get(url, timeout=10).json()
        rows = (j.get("StatisticSearch") or {}).get("row") or []
        out = []
        for r in rows:
            v = r.get("DATA_VALUE")
            if v in (None, "", "-"):
                continue
            try:
                out.append({"t": r.get("TIME"), "v": float(v)})
            except (TypeError, ValueError):
                continue
        return out
    except Exception:  # noqa: BLE001
        return []


def _macro_snapshot() -> dict:
    """한국 거시지표 묶음 (1시간 캐시): 기준금리·국고채3/10년·CPI(YoY)·원달러 + 추이 시리즈."""
    now = time.time()
    if _ECOS_CACHE["data"] and (now - _ECOS_CACHE["ts"]) < _ECOS_TTL:
        return _ECOS_CACHE["data"]
    if not _ECOS_KEY:
        return {"ok": False, "msg": "ECOS 키가 없습니다 (.env ECOS_KEY)"}
    from datetime import timedelta
    m_end = date.today().strftime("%Y%m")
    m_start = (date.today() - timedelta(days=365 * 3 + 60)).strftime("%Y%m")
    d_end = date.today().strftime("%Y%m%d")
    d_start = (date.today() - timedelta(days=60)).strftime("%Y%m%d")
    d_bond = (date.today() - timedelta(days=365 * 3 + 40)).strftime("%Y%m%d")
    base = _ecos_rows("722Y001", "M", "0101000", m_start, m_end)      # 한국은행 기준금리 (월)
    g3_d = _ecos_rows("817Y002", "D", "010200000", d_bond, d_end)     # 국고채 3년 (일) — 817Y002 는 월 미지원
    g10_d = _ecos_rows("817Y002", "D", "010210000", d_bond, d_end)    # 국고채 10년 (일)
    cpi = _ecos_rows("901Y009", "M", "0", m_start, m_end)             # 소비자물가지수 총지수 (월)
    usd = _ecos_rows("731Y001", "D", "0000001", d_start, d_end)       # 원/달러 매매기준율 (일)

    def _to_monthly(rows):                                            # 일별 → 월말값(오름차순)
        m = {}
        for r in rows:
            m[r["t"][:6]] = r["v"]
        return [{"t": k, "v": v} for k, v in sorted(m.items())]

    g3, g10 = _to_monthly(g3_d), _to_monthly(g10_d)

    def last(rows):
        return rows[-1]["v"] if rows else None

    def lastt(rows):
        return rows[-1]["t"] if rows else None

    # 금리 추이 (월별, 공통 축 정렬)
    months = sorted(set([r["t"] for r in base] + [r["t"] for r in g3] + [r["t"] for r in g10]))
    months = months[-30:]                                # 최근 30개월

    def align(rows):
        m = {r["t"]: r["v"] for r in rows}
        return [m.get(t) for t in months]

    us10 = _fred_series("DGS10", months)                 # 미국 국채 10년(FRED) — 추이에 함께 표기

    # CPI YoY (12개월 전 대비)
    cpi_months = [r["t"] for r in cpi][-30:]
    cpi_idx = {r["t"]: i for i, r in enumerate(cpi)}
    cpi_yoy = []
    for t in cpi_months:
        i = cpi_idx[t]
        cpi_yoy.append(round((cpi[i]["v"] / cpi[i - 12]["v"] - 1) * 100, 2) if i >= 12 else None)
    g3v = g3_d[-1]["v"] if g3_d else None                # KPI 현재값은 최신 일별
    g10v = g10_d[-1]["v"] if g10_d else None
    spread = round(g10v - g3v, 3) if (g3v is not None and g10v is not None) else None
    cpi_yoy_last = next((x for x in reversed(cpi_yoy) if x is not None), None)
    bond_asof = g3_d[-1]["t"][:6] if g3_d else None      # 표시는 월 단위(YYYYMM)

    # ── 증시 영향 종합 해석 (규칙기반 — LM Studio 불필요, 결정적) ──
    base_d3 = (base[-1]["v"] - base[-4]["v"]) if len(base) > 4 else None     # 기준금리 3개월 변화(%p)
    usd_d = (usd[-1]["v"] - usd[0]["v"]) if len(usd) >= 2 else None          # 환율 ~2개월 변화
    pts: list[dict] = []
    score = 0
    if base_d3 is not None:
        if base_d3 <= -0.1:
            pts.append({"k": "기준금리", "t": "기준금리 인하 흐름 — 유동성 확대는 주식·성장주에 우호적입니다.", "tone": "good"}); score += 1
        elif base_d3 >= 0.1:
            pts.append({"k": "기준금리", "t": "기준금리 인상 흐름 — 할인율 상승으로 밸류에이션·성장주에 부담입니다.", "tone": "bad"}); score -= 1
        else:
            pts.append({"k": "기준금리", "t": "기준금리 동결 기조 — 정책 불확실성이 낮아 변동성 완화 요인입니다.", "tone": "neutral"})
    if spread is not None:
        if spread < 0:
            pts.append({"k": "장단기 금리차", "t": "10년-3년 금리 역전 — 경기 둔화·침체 경고로 위험자산에 경계가 필요합니다.", "tone": "bad"}); score -= 1
        elif spread > 0.5:
            pts.append({"k": "장단기 금리차", "t": "장단기 금리차가 뚜렷한 정(+) — 경기 회복 기대를 반영, 경기민감·금융주에 우호적입니다.", "tone": "good"}); score += 1
        else:
            pts.append({"k": "장단기 금리차", "t": "장단기 금리차 소폭 정(+) — 완만한 경기 확장 신호로 중립~우호적입니다.", "tone": "neutral"})
    if cpi_yoy_last is not None:
        if cpi_yoy_last >= 3:
            pts.append({"k": "물가", "t": f"소비자물가 상승률이 높음({cpi_yoy_last:.1f}%) — 통화 긴축 압력으로 금리 변수에 민감한 장세입니다.", "tone": "bad"}); score -= 1
        elif cpi_yoy_last <= 2:
            pts.append({"k": "물가", "t": f"물가 상승률 안정({cpi_yoy_last:.1f}%) — 금리 인하 여력을 키워 증시에 우호적입니다.", "tone": "good"}); score += 1
        else:
            pts.append({"k": "물가", "t": f"물가가 목표(2%) 부근({cpi_yoy_last:.1f}%) — 통화정책 전환 기대와 경계가 공존합니다.", "tone": "neutral"})
    if usd_d is not None:
        if usd_d >= 10:
            pts.append({"k": "환율", "t": "원/달러 상승(원화 약세) — 외국인 자금 이탈·수입물가 부담 요인이나 수출주엔 우호적입니다.", "tone": "neutral"})
        elif usd_d <= -10:
            pts.append({"k": "환율", "t": "원/달러 하락(원화 강세) — 외국인 수급에 우호적이나 수출주 가격경쟁력은 약화됩니다.", "tone": "neutral"})
        else:
            pts.append({"k": "환율", "t": "원/달러 안정 — 환율발 수급 변동성은 제한적입니다.", "tone": "neutral"})
    if score >= 2:
        overall = {"title": "거시 환경이 증시에 우호적", "tone": "good",
                   "t": "금리·물가 여건이 위험자산에 우호적입니다. 유동성·밸류에이션 측면의 순풍을 기대할 수 있는 구간입니다."}
    elif score <= -2:
        overall = {"title": "거시 환경이 증시에 부담", "tone": "bad",
                   "t": "긴축·인플레·경기 신호가 부담으로 작용합니다. 방어적 포지션과 금리 변수 점검이 필요한 구간입니다."}
    else:
        overall = {"title": "중립적 거시 환경", "tone": "neutral",
                   "t": "상·하방 요인이 혼재합니다. 금리 피벗·물가 둔화 등 전환점을 확인하며 대응하는 구간입니다."}

    data = {"ok": True,
            "asof": {"rate": lastt(base), "bond": bond_asof, "cpi": lastt(cpi), "fx": lastt(usd)},
            "kpi": {"base": last(base), "g3": g3v, "g10": g10v, "spread": spread,
                    "usd": last(usd), "cpi": last(cpi), "cpi_yoy": cpi_yoy_last},
            "rate_series": {"months": months, "base": align(base), "g3": align(g3), "g10": align(g10), "us10": us10},
            "cpi_series": {"months": cpi_months, "yoy": cpi_yoy},
            "commentary": {"overall": overall, "points": pts}}
    _ECOS_CACHE.update(ts=now, data=data)
    return data


# ════════════════ 글로벌 경제 지표 (작업4) ════════════════
# 한국 지표만으로는 증시 해석이 부족 → 미국 증시(S&P500·나스닥)·위험심리(VIX)·
# 달러강세(달러인덱스)·원자재(국제금·WTI) 등 필수 글로벌 지표를 함께 제공한다.
# 전부 네이버 무인증 엔드포인트(/index, /marketindex/{cat})로 수집(60초 캐시, 병렬).
_GMAC_CACHE: dict = {"ts": 0.0, "data": None}
_GMAC_TTL = 60.0


def _gmac_dir(pct: str) -> str:
    try:
        v = float(str(pct).replace(",", "").lstrip("+"))
    except (TypeError, ValueError):
        return "flat"
    return "up" if v > 0 else ("down" if v < 0 else "flat")


def _gmac_idx_one(code: str, label: str, unit: str = "") -> dict | None:
    """네이버 /index/{reutersCode}/basic 단건 (지수·VIX)."""
    try:
        d = httpx.get(f"https://api.stock.naver.com/index/{code}/basic",
                      timeout=7, headers=_WORLD_UA).json()
        cp = d.get("closePrice")
        if not cp:
            return None
        pct = str(d.get("fluctuationsRatio") or "0")
        return {"key": label, "price": cp, "pct": pct, "dir": _gmac_dir(pct), "unit": unit}
    except Exception:  # noqa: BLE001
        return None


def _gmac_list_one(cat: str, code: str, label: str, unit: str = "") -> dict | None:
    """네이버 /marketindex/{cat} 목록에서 reutersCode 매칭 항목 추출 (원자재·달러인덱스)."""
    try:
        j = httpx.get(f"https://api.stock.naver.com/marketindex/{cat}",
                      timeout=7, headers=_WORLD_UA).json()
        rows = j.get("normalList") if isinstance(j, dict) else j
        for it in (rows or []):
            if (it.get("reutersCode") or it.get("symbolCode")) == code:
                cp = it.get("closePrice")
                if not cp:
                    return None
                pct = str(it.get("fluctuationsRatio") or "0")
                return {"key": label, "price": cp, "pct": pct, "dir": _gmac_dir(pct), "unit": unit}
        return None
    except Exception:  # noqa: BLE001
        return None


# (cat/kind, code, 라벨, 단위) — kind="idx" → /index, 그 외 → /marketindex/{kind}
_GMAC_SPEC = [
    ("idx", ".INX", "S&P 500", "pt"),
    ("idx", ".IXIC", "나스닥", "pt"),
    ("idx", ".VIX", "VIX 변동성", ""),
    ("exchange", ".DXY", "달러인덱스", ""),
    ("metals", "GCcv1", "국제 금", "$/oz"),
    ("energy", "CLcv1", "WTI 유가", "$/bbl"),
]


def _fred_one(series_id: str, label: str, unit: str = "%") -> dict | None:
    """FRED(미국 연준 데이터) 최신값 + 직전 대비 변화(%p). FREED_KEY 필요."""
    key = os.environ.get("FREED_KEY", "")
    if not key:
        return None
    try:
        r = httpx.get("https://api.stlouisfed.org/fred/series/observations",
                      params={"series_id": series_id, "api_key": key, "file_type": "json",
                              "sort_order": "desc", "limit": 6}, timeout=8)
        obs = [o for o in r.json().get("observations", []) if o.get("value") not in (".", "", None)]
        if not obs:
            return None
        cur = float(obs[0]["value"])
        prev = float(obs[1]["value"]) if len(obs) > 1 else cur
        d = cur - prev
        return {"key": label, "price": f"{cur:.2f}", "pct": f"{d:+.2f}",
                "dir": ("up" if d > 0 else ("down" if d < 0 else "flat")),
                "unit": unit, "asof": obs[0]["date"]}
    except Exception:  # noqa: BLE001
        return None


def _fred_series(series_id: str, months: list[str]) -> list:
    """FRED 월별 시계열을 YYYYMM 목록(months)에 정렬해 반환(금리 추이 차트용).
    FREED_KEY 없거나 실패 시 [None]*len(months) → 차트가 해당 라인만 비움(나머지 정상)."""
    out: list = [None] * len(months)
    key = os.environ.get("FREED_KEY", "")
    if not key or not months:
        return out
    try:
        start = f"{months[0][:4]}-{months[0][4:6]}-01"
        r = httpx.get("https://api.stlouisfed.org/fred/series/observations",
                      params={"series_id": series_id, "api_key": key, "file_type": "json",
                              "frequency": "m", "aggregation_method": "eop",
                              "observation_start": start}, timeout=8)
        mp: dict[str, float] = {}
        for o in r.json().get("observations", []):
            v, d = o.get("value"), o.get("date", "")
            if v not in (".", "", None) and len(d) >= 7:
                mp[d[:4] + d[5:7]] = round(float(v), 3)
        return [mp.get(t) for t in months]
    except Exception:  # noqa: BLE001
        return out


def _global_macro_snapshot() -> dict:
    """글로벌 필수 지표 묶음(60초 캐시) + 규칙기반 증시 영향 해석."""
    now = time.time()
    if _GMAC_CACHE["data"] and (now - _GMAC_CACHE["ts"]) < _GMAC_TTL:
        return _GMAC_CACHE["data"]
    with _TPE(max_workers=8) as ex:
        futs = [ex.submit(_gmac_idx_one if kind == "idx" else _gmac_list_one,
                          *( (code, lab, unit) if kind == "idx" else (kind, code, lab, unit) ))
                for kind, code, lab, unit in _GMAC_SPEC]
        # 미국 금리(FRED) — 경제 해석에 필수. 키 있을 때만.
        f_us10 = ex.submit(_fred_one, "DGS10", "미국 국채 10년", "%")
        f_fed = ex.submit(_fred_one, "FEDFUNDS", "미국 기준금리", "%")
        rows = [f.result() for f in futs]
        rows += [f_us10.result(), f_fed.result()]
    rows = [r for r in rows if r]
    if not rows:
        return {"ok": False, "msg": "글로벌 지표를 불러올 수 없습니다."}

    by = {r["key"]: r for r in rows}

    def _f(label, field="pct"):
        r = by.get(label)
        if not r:
            return None
        try:
            return float(str(r[field]).replace(",", "").lstrip("+"))
        except (TypeError, ValueError):
            return None

    pts: list[dict] = []
    dxy = _f("달러인덱스"); vixlv = _f("VIX 변동성", "price"); wti = _f("WTI 유가")
    spx = _f("S&P 500"); gold = _f("국제 금")
    if dxy is not None:
        if dxy >= 0.3:
            pts.append({"k": "달러", "t": "달러인덱스 강세 — 외국인 자금 이탈·신흥국(원화) 부담, 위험자산엔 역풍입니다.", "tone": "bad"})
        elif dxy <= -0.3:
            pts.append({"k": "달러", "t": "달러인덱스 약세 — 신흥국·위험자산 수급에 우호적이며 원화 강세 요인입니다.", "tone": "good"})
        else:
            pts.append({"k": "달러", "t": "달러인덱스 보합 — 환율발 글로벌 수급 변동은 제한적입니다.", "tone": "neutral"})
    if vixlv is not None:
        if vixlv >= 20:
            pts.append({"k": "위험심리", "t": f"VIX {vixlv:.1f}로 높음 — 시장 공포·변동성 확대 국면으로 위험회피 심리가 강합니다.", "tone": "bad"})
        elif vixlv <= 15:
            pts.append({"k": "위험심리", "t": f"VIX {vixlv:.1f}로 낮음 — 시장 안정·위험선호 심리로 주식에 우호적입니다.", "tone": "good"})
        else:
            pts.append({"k": "위험심리", "t": f"VIX {vixlv:.1f} 중립 — 변동성은 평이한 수준입니다.", "tone": "neutral"})
    if wti is not None:
        if wti >= 3:
            pts.append({"k": "유가", "t": "WTI 급등 — 에너지·인플레 부담으로 통화 긴축 변수에 민감해질 수 있습니다.", "tone": "bad"})
        elif wti <= -3:
            pts.append({"k": "유가", "t": "WTI 급락 — 물가 안정 기대를 키워 금리 부담을 더는 요인이나 경기 둔화 신호일 수도 있습니다.", "tone": "neutral"})
    if spx is not None:
        if spx >= 0.5:
            pts.append({"k": "미국증시", "t": "미국 증시 강세 — 글로벌 위험선호가 살아있어 국내 증시에도 우호적입니다.", "tone": "good"})
        elif spx <= -0.5:
            pts.append({"k": "미국증시", "t": "미국 증시 약세 — 글로벌 위험회피가 국내 증시에 하방 압력으로 작용할 수 있습니다.", "tone": "bad"})
    if gold is not None and gold >= 1.5:
        pts.append({"k": "금", "t": "국제 금값 강세 — 안전자산 선호·인플레 헤지 수요가 부각되는 국면입니다.", "tone": "neutral"})
    us10 = _f("미국 국채 10년", "price")
    if us10 is not None:
        if us10 >= 4.5:
            pts.append({"k": "미국금리", "t": f"미국 10년물 국채금리가 높음({us10:.2f}%) — 글로벌 할인율 상승으로 "
                        "성장주·신흥국 증시에 부담입니다.", "tone": "bad"})
        elif us10 <= 3.8:
            pts.append({"k": "미국금리", "t": f"미국 10년물 국채금리 안정({us10:.2f}%) — 할인율 부담이 완화돼 "
                        "위험자산에 우호적입니다.", "tone": "good"})
        else:
            pts.append({"k": "미국금리", "t": f"미국 10년물 국채금리 {us10:.2f}% — 중립 수준으로 추세 전환 여부가 관건입니다.", "tone": "neutral"})

    data = {"ok": True, "rows": rows, "points": pts, "asof": time.strftime("%m.%d %H:%M")}
    _GMAC_CACHE.update(ts=now, data=data)
    return data


# ════════════════ 시장 현황 (시총상위·상하한가·시황뉴스) ════════════════
# 시가총액 상위[091]은 _sector_stocks(0001 거래소 / 1001 코스닥) 재사용.
# 상하한가 포착[국내주식-190](FHKST130000C0) + 종합 시황·공시[141](FHKST01011800).
_UPDOWN_CACHE: dict = {"ts": 0.0, "data": None}
_MKT_NEWS_CACHE: dict = {"ts": 0.0, "rows": None}


def _kis_updown() -> dict:
    """상한가/하한가 포착 — {"up": [...], "down": [...]} (60초 캐시)."""
    now = time.time()
    if _UPDOWN_CACHE["data"] and (now - _UPDOWN_CACHE["ts"]) < 60.0:
        return _UPDOWN_CACHE["data"]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return {"up": [], "down": []}

    def fetch(prc_cls: str) -> list[dict]:
        try:
            with _KIS_LOCK:
                gap = time.time() - _KIS_LAST_CALL["t"]
                if gap < 0.06:
                    time.sleep(0.06 - gap)
                _KIS_LAST_CALL["t"] = time.time()
            r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/capture-uplowprice",
                          timeout=10,
                          headers={"authorization": f"Bearer {tok}", "appkey": ak,
                                   "appsecret": sk, "tr_id": "FHKST130000C0", "custtype": "P"},
                          params={"FID_COND_MRKT_DIV_CODE": "J",
                                  "FID_COND_SCR_DIV_CODE": "11300",
                                  "FID_PRC_CLS_CODE": prc_cls, "FID_DIV_CLS_CODE": "0",
                                  "FID_INPUT_ISCD": "0000", "FID_TRGT_CLS_CODE": "",
                                  "FID_TRGT_EXLS_CLS_CODE": "", "FID_INPUT_PRICE_1": "",
                                  "FID_INPUT_PRICE_2": "", "FID_VOL_CNT": ""})
            j = r.json()
            rows = []
            for o in (j.get("output") or []):
                try:
                    rows.append({"code": o.get("mksc_shrn_iscd"),
                                 "name": o.get("hts_kor_isnm"),
                                 "price": float(o.get("stck_prpr") or 0),
                                 "change": float(o.get("prdy_vrss") or 0),
                                 "change_pct": float(o.get("prdy_ctrt") or 0),
                                 "volume": float(o.get("acml_vol") or 0)})
                except Exception:  # noqa: BLE001
                    continue
            return rows
        except Exception:  # noqa: BLE001
            return []

    data = {"up": fetch("0"), "down": fetch("1")}
    _UPDOWN_CACHE.update(ts=time.time(), data=data)
    return data


def _kis_market_news(n: int = 20) -> list[dict]:
    """종합 시황·공시 제목 [141] — 시장 전체 최신 뉴스 (120초 캐시)."""
    now = time.time()
    if _MKT_NEWS_CACHE["rows"] is not None and (now - _MKT_NEWS_CACHE["ts"]) < 120.0:
        return _MKT_NEWS_CACHE["rows"]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/news-title", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKST01011800", "custtype": "P"},
                      params={"FID_NEWS_OFER_ENTP_CODE": "", "FID_COND_MRKT_CLS_CODE": "",
                              "FID_INPUT_ISCD": "", "FID_TITL_CNTT": "",
                              "FID_RANK_SORT_CLS_CODE": "", "FID_INPUT_SRNO": "",
                              "FID_INPUT_DATE_1": "", "FID_INPUT_HOUR_1": ""})
        j = r.json()
        rows = []
        for o in (j.get("output") or [])[: n * 2]:
            dt, tm = str(o.get("data_dt") or ""), str(o.get("data_tm") or "")
            title = (o.get("hts_pbnt_titl_cntt") or "").strip()
            if not title:
                continue
            rows.append({"when": (f"{dt[4:6]}.{dt[6:8]} {tm[:2]}:{tm[2:4]}"
                                  if len(dt) == 8 and len(tm) >= 4 else dt),
                         "title": title, "src": o.get("dorg") or "-",
                         "code": next((str(o.get(f"iscd{i}") or "")
                                       for i in range(1, 11)
                                       if str(o.get(f"iscd{i}") or "").isdigit()
                                       and len(str(o.get(f"iscd{i}") or "")) == 6), "")})
            if len(rows) >= n:
                break
        if rows:
            _MKT_NEWS_CACHE.update(ts=time.time(), rows=rows)
        return rows
    except Exception:  # noqa: BLE001
        return []


# ── 지수 요약 (KOSPI·KOSDAQ 카드 + 시장 폭) ──────────────────────
def _market_overview() -> dict:
    """KOSPI·KOSDAQ 지수 요약. {kospi:{...}, kosdaq:{...}, phase}.
    각 항목: value/change/change_pct/direction/up_cnt/down_cnt (폐장 시 종가·폭 None)."""
    st = _market_state()
    phase = _index_phase()
    out = {"phase": phase, "last_close": st["last_close"]}
    for key, iscd in (("kospi", "0001"), ("kosdaq", "1001")):
        d = _kis_index(iscd)
        if isinstance(d, dict) and d.get("ok"):
            d = _zero_if_pre(d, phase)     # 개장 전 등락 0
            out[key] = {"value": d.get("value"), "change": d.get("change"),
                        "change_pct": d.get("change_pct"), "direction": d.get("direction"),
                        "up_cnt": d.get("up_cnt"), "down_cnt": d.get("down_cnt"),
                        "uplm_cnt": d.get("uplm_cnt"), "lslm_cnt": d.get("lslm_cnt")}
        else:
            out[key] = None
    return out


# ── 증권사별 투자의견 피드 [국내주식-189] — 시장 전체 최근 의견 ──
_OPN_FEED_CACHE: dict = {"ts": 0.0, "rows": None}


def _kis_opinions_feed(n: int = 40) -> list[dict]:
    """증권사별 투자의견[189] — 시장 전체 최근 신규 투자의견 피드 (10분 캐시).

    반환: [{date, code, name, broker, opinion, target, price, upside}] (최신순,
    목표가 있는 rated 의견만). upside = 목표가 대비 현재가 상승여력(%).
    """
    now = time.time()
    if _OPN_FEED_CACHE["rows"] is not None and (now - _OPN_FEED_CACHE["ts"]) < 600.0:
        return _OPN_FEED_CACHE["rows"]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    try:
        from datetime import timedelta
        d2 = date.today().strftime("%Y%m%d")
        d1 = (date.today() - timedelta(days=14)).strftime("%Y%m%d")
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/invest-opbysec", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKST663400C0", "custtype": "P"},
                      params={"FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "16634",
                              "FID_INPUT_ISCD": "999", "FID_DIV_CLS_CODE": "0",
                              "FID_INPUT_DATE_1": d1, "FID_INPUT_DATE_2": d2})
        j = r.json()
        rows = []
        for o in (j.get("output") or []):
            opn = (o.get("invt_opnn") or "").strip()
            if not opn or "NotRated" in opn or opn.upper() in ("N/R", "NR"):
                continue
            try:
                target = float(o.get("hts_goal_prc") or 0)
                price = float(o.get("stck_prpr") or 0)
            except (ValueError, TypeError):
                continue
            if target <= 0 or price <= 0:
                continue
            dt = str(o.get("stck_bsop_date") or "")
            rows.append({
                "date": f"{dt[4:6]}.{dt[6:8]}" if len(dt) == 8 else dt,
                "code": o.get("stck_shrn_iscd"), "name": o.get("hts_kor_isnm"),
                "broker": o.get("mbcr_name") or "-", "opinion": opn,
                "target": target, "price": price,
                "upside": round((target / price - 1) * 100, 1),
            })
            if len(rows) >= n:
                break
        if rows:
            _OPN_FEED_CACHE.update(ts=time.time(), rows=rows)
        return rows
    except Exception:  # noqa: BLE001
        return []


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
    async with Fetcher() as f:
        return await _achart(f, code, days)


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
def detect_type(query: str) -> str:
    q = query.strip()
    try:
        _df, snap, _ld = etf.get_market()
    except Exception:  # noqa: BLE001
        snap = None
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


def _resolve_etf_code(q: str) -> str | None:
    try:
        _df, snap, _ld = etf.get_market()
        row = E.find_etf(snap, q)
        if row is not None:
            return str(row["코드"])
    except Exception:  # noqa: BLE001
        pass
    return None


# ════════════════ 공용 분석 헬퍼 ════════════════






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




def _metric_grid(items: list[tuple]) -> str:
    cells = "".join(
        f'<div class="m4-met"><div class="m4-met-l">{l}</div>'
        f'<div class="m4-met-v">{v}</div><div class="m4-met-s">{s}</div></div>'
        for l, v, s in items)
    return f'<div class="m4-met-grid">{cells}</div>'


# ════════════════ M4 탭 스타일 (다크 콕핏) ════════════════


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
   if(document.hidden || (window.__APP_LOADED && !document.hasFocus()))return;
   window.__APP_LOADED = true;
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
    if not code:                                  # 코드 없음은 정상(주입 비대상) — 조용히 통과
        return html_doc
    if "</nav>" not in html_doc:
        logger.warning("_inject_m4_tab: </nav> anchor not found (kind=%s, code=%s) — tab injection skipped", kind, code)
        return html_doc
    if "<footer" not in html_doc:
        logger.warning("_inject_m4_tab: <footer anchor not found (kind=%s, code=%s) — pane injection skipped", kind, code)
        return html_doc
    n = html_doc.count('class="tab-btn')
    btn = (f'<button class="tab-btn m4-tab-btn" id="m4-tab-btn" '
           f'onclick="miTab({n})">🚀 M4 퀀트 분석</button>')
    
    # AI 코멘터리 버튼 추가
    ai_btn = (f'<button class="tab-btn" id="ai-tab-btn" style="color:var(--sys-indigo);font-weight:600;" '
              f'onclick="startAI(\'{code}\')">✨ AI 코멘터리</button>')
    
    html_doc = html_doc.replace("</nav>", btn + ai_btn + "</nav>", 1)
    pane = f'<div class="pane" id="pane{n}">{_lazy_pane(kind, code)}</div>'
    html_doc = html_doc.replace("<footer", pane + "<footer", 1)
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _M4_STYLE + "</head>", 1)
    
    # AI 스크립트와 모달 추가
    _AI_SCRIPT = """
<style>
/* AI Modal Transitions */
#ai-modal {
  display: flex; flex-direction: column;
  position: fixed; top: 60px; right: 20px; width: 340px;
  background: var(--mat-card);
  -webkit-backdrop-filter: blur(20px); backdrop-filter: blur(20px);
  padding: 20px; border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  z-index: 9999; border: 1px solid var(--g-line);
  opacity: 0; transform: translateY(12px) scale(0.98); pointer-events: none;
  transition: opacity .32s cubic-bezier(.32,.72,0,1), transform .32s cubic-bezier(.32,.72,0,1);
}
#ai-modal.show {
  opacity: 1; transform: none; pointer-events: auto;
}

/* AI Loading Dots */
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

/* AI Streaming Text & Cursor */
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
</style>

<div id="ai-modal">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:1px solid var(--g-line);padding-bottom:8px;">
    <h3 style="margin:0;font-size:15px;color:var(--sys-indigo);">✨ AI 코멘터리 (Local)</h3>
    <button onclick="closeAI()" style="background:none;border:none;color:var(--text);cursor:pointer;font-size:16px;padding:0;">✕</button>
  </div>
  <div id="ai-content" style="font-size:13.5px;line-height:1.65;max-height:400px;overflow-y:auto;color:var(--text);"></div>
</div>

<script>
let _aiAborter = null;

function closeAI() {
  if (_aiAborter) { _aiAborter.abort(); _aiAborter = null; }
  document.getElementById('ai-modal').classList.remove('show');
}

function startAI(code) {
  if (_aiAborter) { _aiAborter.abort(); }
  _aiAborter = new AbortController();
  
  var modal = document.getElementById('ai-modal');
  var content = document.getElementById('ai-content');
  
  // Show modal with animation
  modal.classList.add('show');
  
  // Show Loading State
  content.innerHTML = '<div style="color:var(--sub, rgba(60,60,67,0.6));font-size:12.5px;margin-bottom:8px;text-align:center;">실시간 시세·모멘텀·리스크·뉴스를<br>수집·분석 중입니다...</div>' +
                      '<div class="ai-loader"><div class="ai-dot"></div><div class="ai-dot"></div><div class="ai-dot"></div></div>';

  fetch('/api/llm_commentary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(Object.assign({ code: String(code) }, (window.kmktAiProv?window.kmktAiProv():{}))),
    signal: _aiAborter.signal
  }).then(async response => {
    content.innerHTML = '<div id="ai-think" style="display:none;font-size:11.5px;opacity:.6;'
      + 'border-left:2px solid rgba(10,132,255,.4);padding:4px 9px;margin:0 0 9px;max-height:150px;'
      + 'overflow:auto;white-space:pre-wrap;line-height:1.5;">\\uD83D\\uDCAD <b style="opacity:.85;">\\ucd94\\ub860</b><br>'
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
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, {stream: true});
      const lines = chunk.split('\\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            if (data.text) {
              if (data.kind === 'reasoning') {
                var span = document.createElement('span'); span.className = 'ai-chunk';
                span.innerHTML = data.text.replace(/\\n/g, '<br>');
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
</script>
"""
    if "</body>" in html_doc:
        html_doc = html_doc.replace("</body>", _AI_SCRIPT + "</body>", 1)

    return html_doc



# ════════════════ 기본 리포트 탭 FX 레이어 (작업1·4) ════════════════



_FAVICON_LINK = '<link rel="icon" type="image/png" href="/logo.png">'
_FX_HEAD = "<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>"


def _inject_fx(html_doc: str) -> str:
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _FX_HEAD + _FAVICON_LINK + _FX_STYLE + "</head>", 1)
    else:
        logger.warning("_inject_fx: </head> anchor not found — FX head/style injection skipped")
    if "</body>" in html_doc:
        html_doc = html_doc.replace("</body>", _FX_JS + "</body>", 1)
    else:
        logger.warning("_inject_fx: </body> anchor not found — FX JS injection skipped")
    return html_doc


# ════════════════ 업종 지수 페이지 (작업6) ════════════════
# 랜딩 탭(iframe)으로 열리는 독립 페이지. KIS 국내업종 현재지수[063] + 시총상위[091].
# 테마: 랜딩과 동일한 localStorage('kmkt-theme') + postMessage({kmkt}) 동기화.
# 업종 지수·시장 현황 페이지 공용 CSS (토스 스타일 — 큰 행·아이콘 타일·랭크)


# ════════════════ 공통 로딩 애니메이션 컴포넌트 (작업3) ════════════════
# 모든 페이지의 "불러오는 중…" 텍스트 로더를 부드러운 스피너 + 펄스 텍스트로 통일한다.
# CSS 는 _LOADER_CSS 를 각 페이지 <head> 에 주입하고, 마크업은 _loader_html() 로 생성한다.
# prefers-reduced-motion 을 존중한다(지침 §10.4). 앞으로 추가되는 페이지도 이 컴포넌트를 사용.
_LOADER_CSS = (
    "<style id=\"kmkt-loader-css\">"
    "@keyframes kmktSpin{to{transform:rotate(360deg)}}"
    "@keyframes kmktPulse{0%,100%{opacity:.5}50%{opacity:1}}"
    ".kmkt-load{display:flex;flex-direction:column;align-items:center;justify-content:center;"
    "gap:13px;padding:38px 18px;min-height:128px;text-align:center;}"
    ".kmkt-load .ring{width:34px;height:34px;border-radius:50%;"
    "border:3px solid rgba(125,128,138,.22);border-top-color:var(--sys-blue,#007AFF);"
    "animation:kmktSpin .72s linear infinite;flex:none;}"
    ".kmkt-load .tx{font-size:13px;font-weight:500;opacity:.62;"
    "animation:kmktPulse 1.6s ease-in-out infinite;letter-spacing:.01em;}"
    ".kmkt-load.sm{flex-direction:row;gap:9px;padding:16px 12px;min-height:0;}"
    ".kmkt-load.sm .ring{width:18px;height:18px;border-width:2px;}"
    ".kmkt-load.sm .tx{font-size:12px;}"
    "@media (prefers-reduced-motion:reduce){.kmkt-load .ring{animation:none;"
    "border-top-color:rgba(125,128,138,.5)}.kmkt-load .tx{animation:none;opacity:.6}}"
    "</style>")


def _loader_html(text: str = "불러오는 중…", sm: bool = False) -> str:
    cls = "kmkt-load sm" if sm else "kmkt-load"
    return (f'<div class="{cls}" role="status" aria-live="polite">'
            f'<span class="ring" aria-hidden="true"></span>'
            f'<span class="tx">{text}</span></div>')




# ════════════════ 시장 현황 페이지 ════════════════
# 시가총액 상위[091] + 상하한가 포착[190] + 종합 시황·공시[141]. /sector 와 동일 스타일.

# 공용 CSS 주입 (플레이스홀더 치환)
_SECTOR_HTML = _SECTOR_HTML.replace("__KMKT_MKT_CSS__", _MKT_CSS)
_MARKET_HTML = _MARKET_HTML.replace("__KMKT_MKT_CSS__", _MKT_CSS)


# ════════════════ 실시간 시세 주입 (현재가 부분만) ════════════════



def _inject_realtime(html_doc: str, code: str | None) -> str:
    if not code:                                  # 코드 없음은 정상(주입 비대상) — 조용히 통과
        return html_doc
    if "</body>" not in html_doc:
        logger.warning("_inject_realtime: </body> anchor not found (code=%s) — realtime injection skipped", code)
        return html_doc
    if "</head>" in html_doc:
        html_doc = html_doc.replace("</head>", _RT_STYLE + "</head>", 1)
    else:
        logger.warning("_inject_realtime: </head> anchor not found (code=%s) — RT style injection skipped", code)
    html_doc = html_doc.replace("</body>", _RT_JS.replace("__CODE__", code) + "</body>", 1)
    return html_doc


# 결과 HTML 끝에 붙는 인터랙션 스크립트 (M4 그리드 전용)


# ════════════════ 주식 퀀트 (제너레이터) ════════════════
def _gen_stock_quant(code: str):
    yield ("p", 5, "시계열 데이터 적재 (SSD 캐시)…")
    
    is_overseas = not code.isdigit()
    ccy_symbol = "원"
    
    if is_overseas:
        resolved = _ov_resolve(code)
        if not resolved or not resolved.get("ok"):
            yield ("done", '<div class="m4-grid"><div class="m4-note">해외 종목 정보를 찾을 수 없습니다.</div></div>')
            return
        excd = resolved.get("excd", "")
        ccy = resolved.get("ccy", "USD")
        ccy_symbol = "$" if ccy == "USD" else ("¥" if ccy == "JPY" else "$")
        
        all_rows = []
        bymd = ""
        for i in range(5):
            yield ("p", 5 + i * 4, f"해외 시계열 데이터 수집 중 ({i+1}/5)…")
            j = _rt_kis_get("/uapi/overseas-price/v1/quotations/dailyprice", "HHDFS76240000",
                            {"AUTH": "", "EXCD": excd, "SYMB": code, "GUBN": "0", "BYMD": bymd, "MODP": "1"})
            if not j or not j.get("output2"):
                break
            output2 = j["output2"]
            curr_rows = []
            for o in output2:
                c = _rtf(o.get("clos"))
                if c <= 0:
                    continue
                curr_rows.append({
                    "d": o.get("xymd"), 
                    "o": _rtf(o.get("open")), 
                    "h": _rtf(o.get("high")),
                    "l": _rtf(o.get("low")), 
                    "c": c, 
                    "v": _rtf(o.get("tvol"))
                })
            if not curr_rows:
                break
            all_rows.extend(curr_rows)
            oldest_dt = output2[-1].get("xymd")
            if oldest_dt == bymd:
                break
            bymd = oldest_dt
        all_rows.reverse()
        if len(all_rows) < 120:
            yield ("done", '<div class="m4-grid"><div class="m4-note">해외 시계열 데이터가 부족하여 분석할 수 없습니다. (최소 120일 필요)</div></div>')
            return
        dates = np.array([r["d"] for r in all_rows])
        closes = np.array([r["c"] for r in all_rows], dtype=np.float64)
    else:
        dates, closes = _clean_closes(asyncio.run(_afetch(code, 2400)))
        
    if closes.size < 120:
        yield ("done", '<div class="m4-grid"><div class="m4-note">시계열이 부족하여 분석할 수 없습니다.</div></div>')
        return
    cur = float(closes[-1])
    rs = _risk_stats(closes)
    logr, mu, sigma = rs["logr"], rs["mu"], rs["sd"]

    # ① 리스크·수익 지표 + 몬테카를로
    yield ("p", 18, "리스크 지표 · 몬테카를로 (GPU 가속 판단 중)…")
    try:
        import mlx.core as mx
        n_sim, horizon = 1_000_000, 252
        draws_mx = mx.random.normal((n_sim, horizon), loc=mu, scale=sigma, dtype=mx.float32)
        paths_mx = cur * mx.exp(mx.cumsum(draws_mx, axis=1))
        paths = np.array(paths_mx)
        sim_label = "1,000,000"
        compute_desc = "Apple MLX (Metal GPU 가속)"
    except ImportError:
        n_sim, horizon = 25_000, 252
        rng = np.random.default_rng()
        draws = rng.normal(mu, sigma, size=(n_sim, horizon)).astype(np.float32)
        paths = cur * np.exp(np.cumsum(draws, axis=1))
        sim_label = "25,000"
        compute_desc = "NumPy (Apple Accelerate BLAS)"

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
    if is_overseas:
        fan.add_hline(y=cur, line_dash="dash", line_color=C_UP,
                      annotation_text=f"현재가 {ccy_symbol}{cur:,.2f}", annotation_position="top left")
        fan.update_xaxes(title="향후 거래일 (영업일)")
        fan.update_yaxes(title=f"예상 주가({ccy_symbol})", tickformat=",.2f")
    else:
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
        if is_overseas:
            _scene3d(surf, 500, dict(xaxis=dict(title=f"주가({ccy_symbol})", tickformat=",.2f"),
                                     yaxis=dict(title="향후 영업일"),
                                     zaxis=dict(title="발생 밀도", showticklabels=False),
                                     camera=dict(eye=dict(x=1.7, y=-1.5, z=1.05))))
        else:
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
        if not is_overseas and code != MARKET_PROXY:
            md, mc = _clean_closes(asyncio.run(_afetch(MARKET_PROXY, 2400)))
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
    if is_overseas:
        note = (
            f'<div class="m4-note"><b>💡 M4 퀀트 데스크 브리핑 (해외).</b> {sim_label}개의 가격 경로를 벡터화 '
            f"{compute_desc}로 생성했습니다. 1년 뒤 분포 "
            f"중앙값 {ccy_symbol}{_cu(med_t, 2)}(현재가 대비 {_cu(exp_ret, 1, True)}%), 90% 구간 "
            f"<b>{ccy_symbol}{p5_t:,.2f}~{ccy_symbol}{p95_t:,.2f}</b>, 현재가 상회 확률 {_cu(prob_up, 0)}%."
            + dist_note + frac_note +
            "<br><span style='font-size:12px;color:#8f9cd0'>※ 과거 통계 기반 추정치로 미래 수익을 "
            "보장하지 않습니다. 투자 판단의 참고 자료로만 활용하세요.</span></div>")
    else:
        note = (
            f'<div class="m4-note"><b>💡 M4 퀀트 데스크 브리핑.</b> {sim_label}개의 가격 경로를 벡터화 '
            f"{compute_desc}로 생성했습니다. 1년 뒤 분포 "
            f"중앙값 {_cu(med_t)}원(현재가 대비 {_cu(exp_ret, 1, True)}%), 90% 구간 "
            f"<b>{p5_t:,.0f}~{p95_t:,.0f}원</b>, 현재가 상회 확률 {_cu(prob_up, 0)}%."
            + dist_note + frac_note +
            "<br><span style='font-size:12px;color:#8f9cd0'>※ 과거 통계 기반 추정치로 미래 수익을 "
            "보장하지 않습니다. 투자 판단의 참고 자료로만 활용하세요.</span></div>")

    html = ('<div class="m4-grid">' + note + metric_html
            + _frag(fan, f"🎲 몬테카를로 미래주가 시뮬레이션 — {sim_label} 경로 · 1년 분포")
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


@app.get("/api/realtime")
def api_realtime() -> Response:
    """한국투자증권 실시간 현재가. 현재가 히어로(.ph-price) 갱신용 JSON."""
    code = (request.args.get("code") or "").strip()
    if not code:
        return jsonify({"ok": False, "msg": "no code"})
    return jsonify(_kis_price(code))


@app.get("/api/index")
def api_index() -> Response:
    """국내 업종지수 실시간 현재가(기본 KOSPI=0001). 상단바 지수 티커 갱신용.

    market_open: KRX 정규장 여부(휴장일 API + 장시간) — 티커 점 색상 제어(작업2).
    """
    iscd = (request.args.get("code") or "0001").strip()
    d = _kis_index(iscd)
    try:
        st = _market_state()
        if isinstance(d, dict):
            d = dict(d)                   # 캐시 원본 보호
            d["phase"] = _index_phase()
            d["market_open"] = bool(st["src"] == "KRX")
            d["last_close"] = st["last_close"]
            d = _zero_if_pre(d, d["phase"])
    except Exception:  # noqa: BLE001
        pass
    return jsonify(d)


@app.get("/api/index_chart")
def api_index_chart() -> Response:
    """지수 캔들(일/주/월/년) — 코스피·코스닥 상세 페이지 차트용."""
    return jsonify(_index_chart(request.args.get("code", "0001").strip(),
                                request.args.get("period", "D").strip()))


@app.get("/api/macro")
def api_macro() -> Response:
    """한국 거시지표(한국은행 ECOS) — 경제 지표 페이지용."""
    return jsonify(_macro_snapshot())


@app.get("/api/global_macro")
def api_global_macro() -> Response:
    """글로벌 필수 지표(미국증시·VIX·달러인덱스·금·WTI) — 경제 지표 페이지용 (작업4)."""
    return jsonify(_global_macro_snapshot())


# ════════════════ 증권사 리포트 (네이버 리서치) — 작업7 ════════════════
# finance.naver.com/research/{slug}_list.naver (EUC-KR HTML) 파싱 → 카테고리별 리포트 목록.
# 원문 PDF 프록시(Referer 필요) + 로컬 AI 요약(읽기페이지 본문 → _llm_stream).
_RESEARCH_CATS = {
    "daily":     ("market_info", "📊 데일리"),
    "company":   ("company",     "🏢 종목분석"),
    "industry":  ("industry",    "🏭 산업분석"),
    "invest":    ("invest",      "🎯 투자전략"),
    "economy":   ("economy",     "🌐 경제분석"),
    "debenture": ("debenture",   "💵 채권분석"),
    "market":    ("market",      "📊 종합시황"),     # 거래소 종합시황 AI 브리핑(KIS 데이터)
    "bok":       ("bok",         "🏦 한국은행"),     # 한국은행 보도자료(RSS) — 별도 파서
    "bok_mp":    ("bok_mp",      "🏛️ 금융통화위원회"),
}
_RESEARCH_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15"}
_RESEARCH_CACHE: dict = {}     # (cat,page) -> (rows, ts)


def _research_clean(s: str) -> str:
    import html as _h
    s = re.sub(r"<[^>]+>", "", s or "")
    return _h.unescape(s).replace("&middot;", "·").strip()


_BOK_RSS = "https://www.bok.or.kr/portal/bbs/B0000502/news.rss?menuNo=201263"
_BOK_BASE = "https://www.bok.or.kr"


def _bok_list(page: int = 1) -> list[dict]:
    """한국은행 보도자료 목록 — 공식 RSS(news.rss) 파싱. [{nid,title,date,...}]."""
    import html as _h
    try:
        r = httpx.get(_BOK_RSS, timeout=12, headers=_RESEARCH_UA)
        xml = r.text
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for m in re.finditer(r"<item>(.*?)</item>", xml, re.S):
        it = m.group(1)
        tm = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        lm = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", it, re.S)
        dm = re.search(r"<(?:dc:date|pubDate)>(.*?)</(?:dc:date|pubDate)>", it, re.S)
        nid = ""
        if lm:
            nm = re.search(r"nttId=(\d+)", lm.group(1))
            nid = nm.group(1) if nm else ""
        if not (tm and nid):
            continue
        date = ""
        if dm:
            ds = dm.group(1)
            dd = re.search(r"(\d{4})[-.](\d{2})[-.](\d{2})", ds)        # ISO (dc:date)
            if dd:
                date = f"{dd.group(1)[2:]}.{dd.group(2)}.{dd.group(3)}"
            else:                                                       # RFC822 (pubDate)
                mon = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                       "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                rm822 = re.search(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})", ds)
                if rm822:
                    date = f"{rm822.group(3)[2:]}.{mon[rm822.group(2)]}.{int(rm822.group(1)):02d}"
        title = _h.unescape(_h.unescape(tm.group(1))).replace("&middot;", "·").strip()
        rows.append({"nid": nid, "cat": "bok", "title": title,
                     "broker": "한국은행", "date": date, "pdf": True, "stock": "", "code": ""})
        if len(rows) >= 30:
            break
    return rows


def _bok_read(nid: str) -> tuple[str, str]:
    """한국은행 보도자료 view → (본문텍스트, PDF url). 첨부 .pdf(/fileSrc/...) 우선."""
    import html as _h
    url = (f"{_BOK_BASE}/portal/bbs/B0000502/view.do?nttId={int(nid)}"
           "&menuNo=201265&depth3=201263&programType=newsData")
    pdf, txt = "", ""
    try:
        page = httpx.get(url, timeout=12, headers=_RESEARCH_UA).text
        mm = re.search(r'href="(/fileSrc/[^"\']+\.pdf)"', page)
        if mm:
            pdf = _BOK_BASE + mm.group(1)
        # 본문(view 영역) 텍스트
        seg = re.sub(r"(?is)<(script|style|head|nav|header|footer)[^>]*>.*?</\1>", " ", page)
        seg = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", seg)
        seg = _h.unescape(re.sub(r"(?s)<[^>]+>", " ", seg))
        lines = [ln.strip() for ln in seg.splitlines() if len(ln.strip()) > 1]
        txt = re.sub(r"[ \t]{2,}", " ", "\n".join(lines))
        cut = txt.find("보도자료")
        if 0 < cut < 2000:
            txt = txt[cut:]
        txt = txt[:4000]
    except Exception:  # noqa: BLE001
        pass
    return txt, pdf


def _bok_mp_list(page: int = 1) -> list[dict]:
    """한국은행 금융통화위원회 목록 — listCont.do 스크래핑. [{nid,title,date,...}]."""
    import html as _h
    url = "https://www.bok.or.kr/portal/singl/newsData/listCont.do"
    params = {
        "pageIndex": page,
        "targetDepth": 3,
        "menuNo": 201154,
        "syncMenuChekKey": 1,
        "searchCnd": 1,
        "searchKwd": "",
        "depth2": "200038",
        "depth3": "201154"
    }
    headers = {
        **_RESEARCH_UA,
        "Referer": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201154"
    }
    rows = []
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=15)
        html_content = r.text
        for m_li in re.finditer(r'<li[^>]*class="[^"]*bbsRowCls[^"]*"[^>]*>(.*?)</li>', html_content, re.S):
            li_html = m_li.group(1)
            li_html = re.sub(r'<!--.*?-->', '', li_html, flags=re.S)
            am = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', li_html, re.S)
            if not am:
                continue
            href = am.group(1).strip()
            title = _h.unescape(re.sub(r'<[^>]+>', '', am.group(2))).strip()
            title = re.sub(r'\s+', ' ', title)
            m_ids = re.search(r'/portal/bbs/([^/]+)/view.do\?nttId=(\d+)', href)
            if not m_ids:
                continue
            board_id = m_ids.group(1)
            ntt_id = m_ids.group(2)
            nid = f"{board_id}_{ntt_id}"
            date = ""
            dm = re.search(r'(\d{4})[-.](\d{2})[-.](\d{2})', li_html)
            if dm:
                date = f"{dm.group(1)[2:]}.{dm.group(2)}.{dm.group(3)}"
            rows.append({
                "nid": nid,
                "cat": "bok_mp",
                "title": title,
                "broker": "금융통화위원회",
                "date": date,
                "pdf": True,
                "stock": "",
                "code": ""
            })
    except Exception:  # noqa: BLE001
        pass
    return rows


def _bok_mp_read(nid: str) -> tuple[str, str]:
    """금융통화위원회 view → (본문텍스트, PDF url)."""
    import html as _h
    if "_" not in nid:
        return "", ""
    try:
        board_id, ntt_id = nid.split("_", 1)
        url = (f"{_BOK_BASE}/portal/bbs/{board_id}/view.do?nttId={int(ntt_id)}"
               "&menuNo=201154")
        pdf, txt = "", ""
        page = httpx.get(url, timeout=12, headers=_RESEARCH_UA).text
        mm = re.search(r'href="(/fileSrc/[^"\']+\.pdf)"', page)
        if mm:
            pdf = _BOK_BASE + mm.group(1)
        seg = re.sub(r"(?is)<(script|style|head|nav|header|footer)[^>]*>.*?</\1>", " ", page)
        seg = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", seg)
        seg = _h.unescape(re.sub(r"(?s)<[^>]+>", " ", seg))
        lines = [ln.strip() for ln in seg.splitlines() if len(ln.strip()) > 1]
        txt = re.sub(r"[ \t]{2,}", " ", "\n".join(lines))
        cut = txt.find("의사록")
        if cut < 0:
            cut = txt.find("의결사항")
        if 0 < cut < 2000:
            txt = txt[cut:]
        txt = txt[:4000]
    except Exception:  # noqa: BLE001
        pdf, txt = "", ""
    return txt, pdf


# ── KRX 공식 Open API (data-dbg.krx.co.kr, AUTH_KEY=KRX_KEY) — 작업2 ──
# 스크래핑(안티봇) 대신 정식 API: 지수/주식 일별 시세·거래대금·시총. EOD 기준, basDd 지정.
_KRX_API_CACHE: dict = {}


def _krx_api(path: str, bas_dd: str) -> list:
    key = os.environ.get("KRX_KEY", "")
    if not key:
        return []
    ck = f"{path}:{bas_dd}"
    c = _KRX_API_CACHE.get(ck)
    if c and (time.time() - c[1]) < 3600.0:
        return c[0]
    try:
        r = httpx.get(f"https://data-dbg.krx.co.kr/svc/apis/{path}",
                      params={"basDd": bas_dd}, headers={"AUTH_KEY": key}, timeout=12)
        rows = (r.json() or {}).get("OutBlock_1") or []
        if rows:
            _KRX_API_CACHE[ck] = (rows, time.time())
        return rows
    except Exception:  # noqa: BLE001
        return []


def _krx_latest(path: str) -> tuple[str, list]:
    """가장 최근 거래일의 데이터(최대 7일 역추적). (basDd, rows)."""
    from datetime import date as _d, timedelta as _t
    d = _d.today()
    for _ in range(8):
        d -= _t(days=1)
        if d.weekday() >= 5:
            continue
        bd = d.strftime("%Y%m%d")
        rows = _krx_api(path, bd)
        if rows:
            return bd, rows
    return "", []




def _krx_market_brief() -> str:
    """KRX 공식 API 기반 종합시황 — 코스피·코스닥 지수(거래대금·시총) + 거래대금 상위 종목."""
    out = []
    bd, idx = _krx_latest("idx/kospi_dd_trd")
    kqbd, kqidx = (bd, _krx_api("idx/kosdaq_dd_trd", bd)) if bd else ("", [])
    if bd:
        out.append(f"[KRX 공식 데이터 · 기준 {bd[:4]}.{bd[4:6]}.{bd[6:8]}]")

    def _main(rows, want):
        for r in rows:
            if (r.get("IDX_NM") or "").strip() == want:
                return r
        return None
    for rows, want in ((idx, "코스피"), (kqidx, "코스닥")):
        m = _main(rows, want)
        if m and m.get("CLSPRC_IDX"):
            out.append(f"{want} {m.get('CLSPRC_IDX')} ({m.get('FLUC_RT','-')}%) · "
                       f"거래대금 {_krx_won(m.get('ACC_TRDVAL'))} · 시총 {_krx_won(m.get('MKTCAP'))}")
    if bd:
        stk = _krx_api("sto/stk_bydd_trd", bd)
        if stk:
            def _val(r):
                try:
                    return float(str(r.get("ACC_TRDVAL", "0")).replace(",", ""))
                except (TypeError, ValueError):
                    return 0.0
            top = sorted(stk, key=_val, reverse=True)[:8]
            out.append("[거래대금 상위 (유가증권)]")
            for r in top:
                out.append(f"- {r.get('ISU_NM','')} {float(str(r.get('TDD_CLSPRC','0')).replace(',','')):,.0f}원 "
                           f"({r.get('FLUC_RT','-')}%) · 거래대금 {_krx_won(r.get('ACC_TRDVAL'))}")
    return "\n".join(out)


def _market_brief_text() -> str:
    """거래소 종합시황 브리핑용 컨텍스트 — KRX 공식 지수·거래대금 + KIS 시장폭 + 글로벌 + 시황뉴스."""
    p = []
    try:
        kb = _krx_market_brief()       # KRX 공식 API (작업2)
        if kb:
            p.append(kb)
    except Exception:  # noqa: BLE001
        pass
    try:
        ov = _market_overview()
        for k, nm in (("kospi", "코스피"), ("kosdaq", "코스닥")):
            d = ov.get(k) or {}
            if d.get("value") is not None:
                cp = d.get("change_pct")
                seg = f"{nm} {d['value']} ({'+' if (cp or 0) > 0 else ''}{cp}%)"
                if d.get("up_cnt") is not None:
                    seg += f" · 상승 {d.get('up_cnt')}개 / 하락 {d.get('down_cnt')}개"
                if d.get("uplm_cnt") is not None:
                    seg += f" · 상한 {d.get('uplm_cnt')}/하한 {d.get('lslm_cnt')}"
                p.append(seg)
    except Exception:  # noqa: BLE001
        pass
    try:
        g = _global_macro_snapshot()
        if g.get("ok"):
            p.append("[글로벌] " + ", ".join(f"{r['key']} {r['price']}{r.get('unit','')}"
                     f"({'+' if r['dir'] == 'up' else ''}{r['pct']}%)" for r in g.get("rows", [])[:6]))
    except Exception:  # noqa: BLE001
        pass
    try:
        nws = _kis_market_news(12)
        if nws:
            p.append("[주요 시황·공시 헤드라인]")
            for n in nws[:12]:
                t = (n.get("title") or "").strip()
                if t:
                    p.append("- " + t[:84])
    except Exception:  # noqa: BLE001
        pass
    return "\n".join(p)


def _research_list(cat: str, page: int = 1) -> list[dict]:
    if cat == "market":
        return [{"nid": "0", "cat": "market", "broker": "KRX·KIS 데이터",
                 "title": "📊 오늘의 거래소 종합시황 (AI 브리핑)",
                 "date": time.strftime("%y.%m.%d"), "pdf": False, "stock": "", "code": ""}]
    if cat == "bok":
        ck = ("bok", page)
        c = _RESEARCH_CACHE.get(ck)
        if c and (time.time() - c[1]) < 300.0:
            return c[0]
        rows = _bok_list(page)
        if rows:
            _RESEARCH_CACHE[ck] = (rows, time.time())
        return rows
    if cat == "bok_mp":
        ck = ("bok_mp", page)
        c = _RESEARCH_CACHE.get(ck)
        if c and (time.time() - c[1]) < 300.0:
            return c[0]
        rows = _bok_mp_list(page)
        if rows:
            _RESEARCH_CACHE[ck] = (rows, time.time())
        return rows
    slug = _RESEARCH_CATS.get(cat, _RESEARCH_CATS["daily"])[0]
    ck = (cat, page)
    c = _RESEARCH_CACHE.get(ck)
    if c and (time.time() - c[1]) < 300.0:
        return c[0]
    url = f"https://finance.naver.com/research/{slug}_list.naver?&page={int(page)}"
    rows: list[dict] = []
    try:
        r = httpx.get(url, timeout=10, headers=_RESEARCH_UA)
        html = r.content.decode("euc-kr", errors="replace")
        for mtr in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            tr = mtr.group(1)
            rm = re.search(r"\w+_read\.naver\?nid=(\d+)", tr)
            if not rm:
                continue
            tm = re.search(r"_read\.naver\?nid=\d+[^>]*>(.*?)</a>", tr, re.S)
            title = _research_clean(tm.group(1)) if tm else ""
            if not title:
                continue
            broker_m = re.search(r"<td>([^<>]{2,40})</td>", tr)
            date_m = re.search(r"(\d{2}\.\d{2}\.\d{2})", tr)
            pdf_m = re.search(r'href="(https://stock\.pstatic\.net/[^"]+\.pdf)"', tr)
            stock_m = re.search(r'/item/main\.naver\?code=(\d+)"[^>]*>([^<]+)</a>', tr)
            rows.append({"nid": rm.group(1), "cat": cat, "title": title,
                         "broker": _research_clean(broker_m.group(1)) if broker_m else "",
                         "date": date_m.group(1) if date_m else "",
                         "pdf": bool(pdf_m),
                         "stock": _research_clean(stock_m.group(2)) if stock_m else "",
                         "code": stock_m.group(1) if stock_m else ""})
        rows = rows[:30]
    except Exception:  # noqa: BLE001
        rows = []
    if rows:
        _RESEARCH_CACHE[ck] = (rows, time.time())
    return rows


def _research_read(cat: str, nid: str) -> tuple[str, str]:
    """리포트 읽기 페이지 → (본문텍스트, PDF url). 본문은 robust 한 _fetch_url_text 로 추출."""
    if cat == "bok":
        return _bok_read(nid)
    if cat == "bok_mp":
        return _bok_mp_read(nid)
    slug = _RESEARCH_CATS.get(cat, _RESEARCH_CATS["daily"])[0]
    url = f"https://finance.naver.com/research/{slug}_read.naver?nid={int(nid)}"
    import html as _h
    pdf, txt = "", ""
    try:
        r = httpx.get(url, timeout=12, headers=_RESEARCH_UA)
        page = r.content.decode("euc-kr", errors="replace")   # 네이버 리서치는 EUC-KR
        mm = re.search(r'(https://stock\.pstatic\.net/[^"\' ]+\.pdf)', page)
        pdf = mm.group(1) if mm else ""
        seg = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", page)
        seg = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</td>|</tr>", "\n", seg)
        seg = _h.unescape(re.sub(r"(?s)<[^>]+>", " ", seg))
        lines = [ln.strip() for ln in seg.splitlines() if len(ln.strip()) > 1]
        txt = re.sub(r"[ \t]{2,}", " ", "\n".join(lines))
        cut = re.search(r"(시황정보|종목분석|산업분석|투자정보|경제분석|채권분석|리서치)", txt)
        if cut and cut.start() < 1000:
            txt = txt[cut.start():]
        txt = txt[:4000]
    except Exception:  # noqa: BLE001
        txt = ""
    return txt, pdf


@app.get("/api/research")
def api_research() -> Response:
    cat = (request.args.get("cat") or "daily").strip()
    if cat not in _RESEARCH_CATS:
        cat = "daily"
    try:
        page = max(1, int(request.args.get("page", "1")))
    except (TypeError, ValueError):
        page = 1
    return jsonify({"ok": True, "cat": cat, "rows": _research_list(cat, page)})


_PDF_BYTES_CACHE: dict = {}   # (cat,nid) → (bytes|None, ts) — 같은 리포트 연속 질문 시 750KB 재다운로드 방지
_PDF_BYTES_TTL = 600.0


def _research_pdf_bytes(cat: str, nid: str, max_mb: float = 18.0) -> bytes | None:
    """리포트 PDF 원본 바이트 (Gemini 멀티모달 직독용). 텍스트형/스캔형 모두 그대로 전달.
    실패하거나 PDF가 아니거나 max_mb 초과면 None. 10분 TTL 캐시(멀티턴 질문 시 재다운로드 방지)."""
    if cat not in _RESEARCH_CATS or (cat not in ("bok", "bok_mp") and not str(nid).isdigit()):
        return None
    _ck = (cat, str(nid))
    _c = _PDF_BYTES_CACHE.get(_ck)
    if _c and (time.time() - _c[1]) < _PDF_BYTES_TTL:
        return _c[0]
    data = None
    try:
        if cat == "bok":
            _t, pdfurl = _bok_read(nid)
            if pdfurl:
                data = httpx.get(pdfurl, timeout=25, follow_redirects=True,
                                 headers={**_RESEARCH_UA, "Referer": _BOK_BASE}).content
        elif cat == "bok_mp":
            _t, pdfurl = _bok_mp_read(nid)
            if pdfurl:
                data = httpx.get(pdfurl, timeout=25, follow_redirects=True,
                                 headers={**_RESEARCH_UA, "Referer": _BOK_BASE}).content
        else:
            slug = _RESEARCH_CATS[cat][0]
            with httpx.Client(timeout=20, follow_redirects=True, headers=_RESEARCH_UA) as cl:
                pg = cl.get(f"https://finance.naver.com/research/{slug}_read.naver?nid={nid}"
                            ).content.decode("euc-kr", errors="replace")
                mm = re.search(r'https://stock\.pstatic\.net/[^"\' ]+\.pdf', pg)
                if mm:
                    data = cl.get(mm.group(0), headers={"Referer": "https://finance.naver.com/"}).content
        if not data or data[:4] != b"%PDF" or len(data) > max_mb * 1024 * 1024:
            data = None
    except Exception as e:  # noqa: BLE001
        logger.exception(f"Error downloading PDF for cat={cat}, nid={nid}: {e}")
        data = None
    _PDF_BYTES_CACHE[_ck] = (data, time.time())
    return data


@app.get("/research_pdf2")
def research_pdf2() -> Response:
    """증권사 리포트 PDF 프록시 (모든 카테고리). Referer 필요해 서버가 대신 받아 스트림."""
    cat = (request.args.get("cat") or "daily").strip()
    nid = (request.args.get("nid") or "").strip()
    if cat not in _RESEARCH_CATS or (cat not in ("bok", "bok_mp") and not nid.isdigit()):
        return Response("잘못된 요청", status=400)
    try:
        data = _research_pdf_bytes(cat, nid)
        if not data:
            return Response("<div style='font-family:-apple-system;padding:48px;text-align:center;"
                            "color:#6b7689'>이 리포트/보도자료는 첨부 PDF가 없거나 로드할 수 없습니다.</div>", mimetype="text/html")
        return Response(data, mimetype="application/pdf")
    except Exception as e:  # noqa: BLE001
        return Response(f"PDF 로드 실패: {e}", status=502)


@app.get("/pdf_view")
def pdf_view() -> Response:
    """확대/축소 가능한 PDF 뷰어 (작업1) — 같은 출처 PDF 프록시 URL을 임베드 + 줌 툴바."""
    import json as _j
    import html as _h
    from urllib.parse import urlparse, parse_qs
    src = (request.args.get("src") or "").strip()
    title = (request.args.get("title") or "PDF")[:120]
    if not src.startswith("/"):                # 같은 출처(프록시 경로)만 허용
        return Response("잘못된 요청", status=400)
    # 리포트 PDF(src=/research_pdf2?cat=&nid=)면 cat:nid 를 뽑아 AI가 '이 리포트'를 읽게 한다.
    ask_scope, ask_id = "market", ""
    try:
        qs = parse_qs(urlparse(src).query)
        _cat = (qs.get("cat") or [""])[0].strip()
        _nid = (qs.get("nid") or [""])[0].strip()
        if _cat in _RESEARCH_CATS and (_cat in ("bok", "bok_mp") or _nid.isdigit()):
            ask_scope, ask_id = "research", f"{_cat}:{_nid}"
    except Exception:  # noqa: BLE001
        pass
    html = (_PDF_VIEW_HTML.replace("__SRC__", _j.dumps(src))
            .replace("__TITLE__", _h.escape(title))
            .replace("__ASK_SCOPE__", _j.dumps(ask_scope))
            .replace("__ASK_ID__", _j.dumps(ask_id)))
    return Response(html, mimetype="text/html")




@app.get("/api/research_summary")
def api_research_summary() -> Response:
    """리포트 원문 → 로컬 AI 요약 (SSE). request 값은 제너레이터 밖에서 읽는다(트랩#2)."""
    import json
    cat = (request.args.get("cat") or "daily").strip()
    nid = (request.args.get("nid") or "").strip()
    title = (request.args.get("title") or "").strip()[:200]
    provider = (request.args.get("provider") or "local").strip().lower()
    gmodel = (request.args.get("gemini_model") or "").strip()
    if gmodel not in _GEMINI_MODELS:
        gmodel = _GEMINI_DEFAULT
    gsys = (request.args.get("gsys") or "").strip()[:2000]

    def _synth(sysm, usr, max_tokens, pdf=None):
        # provider 에 따라 로컬 LM Studio 또는 Gemini(클라우드)로 합성. gsys=사용자 시스템 프롬프트.
        # pdf 가 있으면 Gemini 에 PDF 원본을 직접 첨부해 직독(스캔본 OCR 포함).
        if provider == "gemini":
            gsm = sysm + (("\n\n[사용자 추가 지시]\n" + gsys) if gsys else "")
            if pdf:
                yield ("data: " + json.dumps({"text": f"📑 PDF 원문({len(pdf)//1024}KB)을 직접 전달…\n",
                       "kind": "reasoning"}) + "\n\n")
                usr = "첨부된 PDF가 이 리포트의 원문입니다. PDF 내용을 최우선 근거로 요약하세요.\n\n" + usr
            yield ("data: " + json.dumps({"text": f"🌩️ {_GEMINI_MODELS[gmodel]}(클라우드)로 생성 중…\n",
                   "kind": "reasoning"}) + "\n\n")
            yield from _gemini_stream(gsm, usr, model=gmodel, max_tokens=max_tokens, use_search=False, pdf_bytes=pdf)
        else:
            yield from _llm_stream(sysm, usr, max_tokens=max_tokens)

    def gen():
        if cat not in _RESEARCH_CATS or (cat not in ("bok", "bok_mp") and not nid.isdigit()):
            yield "data: " + json.dumps({"text": "잘못된 요청입니다."}) + "\n\n"
            return
        if cat == "market":          # 거래소 종합시황 AI 브리핑 (KIS 데이터)
            yield "data: " + json.dumps({"text": "📊 거래소 종합시황 데이터 수집 중…\n", "kind": "reasoning"}) + "\n\n"
            mt = _market_brief_text()
            if len(mt) < 40:
                yield "data: " + json.dumps({"text": "현재 시황 데이터를 가져오지 못했습니다 (장 시간 외일 수 있음)."}) + "\n\n"
                return
            yield "data: " + json.dumps({"text": "✅ 수집 완료. 브리핑 생성 중…\n", "kind": "reasoning"}) + "\n\n"
            msys = ("당신은 한국 증시 데일리 브리핑을 쓰는 애널리스트입니다. 아래 [오늘 시장 데이터]만 근거로 "
                    "① 지수 요약(코스피·코스닥) ② 시장 폭(상승/하락·상하한) ③ 글로벌 배경 ④ 주요 뉴스 테마 "
                    "⑤ 한 줄 총평 을 간결한 불릿으로 한국어로 정리하세요. 데이터에 없는 수치는 지어내지 마세요. "
                    "마지막 줄에 '※ AI 브리핑이며 투자조언이 아닙니다.'를 덧붙이세요.")
            murr = f"[오늘 시장 데이터] (기준 {time.strftime('%Y-%m-%d')})\n{mt}\n\n오늘 거래소 종합시황을 브리핑해줘."
            yield from _synth(msys, murr, 1200)
            return
        sysm = ("당신은 증권사 리포트를 요약하는 한국어 애널리스트입니다. 아래 [리포트 원문]만 근거로 "
                "① 한 줄 핵심 결론 ② 주요 논거 2~3개 ③ 투자의견·목표주가(있으면) ④ 리스크·체크포인트 "
                "를 간결한 불릿으로 정리하세요. 원문에 없는 수치·사실은 지어내지 마세요. "
                "마지막 줄에 '※ AI 요약이며 투자조언이 아닙니다.'를 덧붙이세요.")
        # Gemini + PDF: PDF 직독이 원문이므로 텍스트 스크랩(추가 네트워크·6000자 프롬프트)을 생략 → 자원 절약.
        if provider == "gemini":
            pdf = _research_pdf_bytes(cat, nid)
            if pdf:
                yield from _synth(sysm, f"[리포트 제목] {title}\n\n이 리포트를 요약해줘.", 900, pdf=pdf)
                return
        # 텍스트 경로(로컬, 또는 Gemini인데 PDF 없음): 읽기 페이지에서 본문 추출.
        yield "data: " + json.dumps({"text": "📄 리포트 원문 불러오는 중…\n", "kind": "reasoning"}) + "\n\n"
        txt, _pdf = _research_read(cat, nid)
        if not txt or len(txt) < 60:
            yield ("data: " + json.dumps({"text": "원문 텍스트를 충분히 가져오지 못했습니다. "
                   "‘PDF 원문’ 버튼으로 직접 확인해 주세요."}) + "\n\n")
            return
        yield "data: " + json.dumps({"text": "✅ 원문 수집 완료. 요약 생성 중…\n", "kind": "reasoning"}) + "\n\n"
        usr = f"[리포트 제목] {title}\n\n[리포트 원문]\n{txt[:6000]}\n\n위 리포트를 요약해줘."
        yield from _synth(sysm, usr, 900)

    return Response(gen(), mimetype="text/event-stream")


@app.get("/research_page")
def research_page() -> Response:
    return Response(_RESEARCH_HTML, mimetype="text/html")




@app.get("/api/etf_nav")
def api_etf_nav() -> Response:
    """ETF 실시간 iNAV (웹소켓 H0STNAV0 → REST 폴백). 리포트 iNAV KPI 갱신용 (작업1)."""
    code = (request.args.get("code") or "").strip()
    if not code:
        return jsonify({"ok": False, "msg": "no code"})
    return jsonify(_kis_etf_nav(code))


@app.get("/api/sectors")
def api_sectors() -> Response:
    """업종 지수 목록 (작업6). ?mkt=kospi|kosdaq"""
    mkt = (request.args.get("mkt") or "kospi").strip()
    st = _market_state()
    return jsonify({"ok": True, "mkt": mkt, "rows": _sector_indices(mkt),
                    "market_open": bool(st["open"] and st["src"] == "KRX"),
                    "asof": time.strftime("%m.%d %H:%M")})


@app.get("/api/sector_stocks")
def api_sector_stocks() -> Response:
    """업종별 구성종목 시세 (작업6). ?iscd=0005"""
    iscd = (request.args.get("iscd") or "").strip()
    return jsonify({"ok": True, "iscd": iscd, "rows": _sector_stocks(iscd)})


@app.get("/sector")
def sector_page() -> Response:
    """업종 지수 탭 페이지 (작업6) — 코스피/코스닥 토글 + 등락률 정렬 + 종목 드릴다운."""
    return Response(_SECTOR_HTML, mimetype="text/html")


@app.get("/api/market_top")
def api_market_top() -> Response:
    """시가총액 상위 [091]. ?mkt=kospi|kosdaq"""
    mkt = (request.args.get("mkt") or "kospi").strip().lower()
    iscd = "1001" if mkt in ("kosdaq", "1001") else "0001"
    st = _market_state()
    return jsonify({"ok": True, "mkt": mkt, "rows": _sector_stocks(iscd),
                    "market_open": bool(st["open"] and st["src"] == "KRX"),
                    "asof": time.strftime("%m.%d %H:%M")})


@app.get("/api/updown")
def api_updown() -> Response:
    """상하한가 포착 [190] — 상한가/하한가 종목."""
    return jsonify({"ok": True, **_kis_updown()})


_MKT_WIDE_NEWS_CACHE: dict = {"ts": 0.0, "rows": None}


# ════════════════ 뉴스 근접-중복 제거 (작업2) ════════════════
# 기존엔 제목 앞 N글자 정확일치만 걸렀다 → "삼성전자, 4분기 깜짝 실적"과
# "[속보] 삼성전자 4분기 어닝 서프라이즈"처럼 사실상 같은 기사를 둘 다 통과시킴.
# 토큰 자카드 + 시퀀스 유사도로 '비슷한 내용은 하나만' 남긴다.
def _news_norm(title: str) -> str:
    """제목 정규화 — 말머리([단독]/[속보]/<...>), 특수문자, 매체명 꼬리표 제거."""
    t = (title or "").lower()
    t = re.sub(r"\[[^\]]*\]|<[^>]*>|\([^)]*\)", " ", t)   # [단독] <b> (종합) 류 제거
    t = re.sub(r"[^0-9a-z가-힣 ]+", " ", t)               # 구두점·기호 제거
    return re.sub(r"\s+", " ", t).strip()


_JOSA = ("으로서", "으로써", "에서는", "에게서", "으로", "에서", "에게", "까지", "부터",
         "보다", "처럼", "만큼", "라고", "이라", "선", "는", "은", "이", "가", "을", "를",
         "에", "의", "도", "와", "과", "로", "만", "들")


def _news_tokens(norm: str) -> set:
    """토큰화 + 한국어 조사/접미 제거(순매수에→순매수, 2700선→2700) — 근접중복 인식률↑."""
    out: set = set()
    for w in norm.split():
        if len(w) < 2:
            continue
        for j in _JOSA:                                  # 어미 1회 제거(자르고도 2자 이상일 때만)
            if w.endswith(j) and len(w) - len(j) >= 2:
                w = w[:-len(j)]
                break
        out.add(w)
    return out




def _dedup_news(rows: list[dict], key: str = "title") -> list[dict]:
    """입력 순서를 유지하며 근접-중복 뉴스를 제거(먼저 온 항목 우선)."""
    kept: list[dict] = []
    sigs: list[tuple[str, set]] = []
    for r in rows:
        norm = _news_norm(r.get(key) or "")
        if not norm:
            continue
        tok = _news_tokens(norm)
        if any(_news_similar(norm, tok, n, t) for n, t in sigs):
            continue
        sigs.append((norm, tok))
        kept.append(r)
    return kept


def _market_wide_news(n: int = 16) -> list[dict]:
    """시장 전체 뉴스 — 네이버 검색(증시·코스피·코스닥) 병합·중복제거·최신순 (3분 캐시).

    기존 _kis_market_news([141])는 개별 종목 공시가 섞여 '시장 전체'가 아니었음(사용자 보고).
    시장 단위 키워드 검색으로 진짜 증시 전반 뉴스를 제공하고, 실패 시 KIS 로 폴백."""
    now = time.time()
    if _MKT_WIDE_NEWS_CACHE["rows"] is not None and (now - _MKT_WIDE_NEWS_CACHE["ts"]) < 180.0:
        return _MKT_WIDE_NEWS_CACHE["rows"]
    out: list[dict] = []
    for q in ("증시", "코스피", "코스닥"):
        for it in _naver_news(q, 8):
            out.append({"when": it.get("when", ""), "title": it["title"], "src": "", "code": ""})
    out.sort(key=lambda r: r["when"], reverse=True)
    out = _dedup_news(out)                                # 근접-중복(비슷한 기사) 제거 (작업2)
    if not out:                                          # 네이버 실패 → KIS 폴백
        out = _dedup_news(_kis_market_news(n))
    else:
        out = out[:n]
        _MKT_WIDE_NEWS_CACHE.update(ts=now, rows=out)
    return out


@app.get("/api/market_news")
def api_market_news() -> Response:
    """시장 전체 뉴스 — 네이버 증시/코스피/코스닥 검색(시장 단위)."""
    return jsonify({"ok": True, "rows": _market_wide_news(20)})


@app.get("/api/market_overview")
def api_market_overview() -> Response:
    """KOSPI·KOSDAQ 지수 요약 + 시장 폭 (시장 현황 상단 카드)."""
    return jsonify({"ok": True, **_market_overview()})


@app.get("/api/opinions_feed")
def api_opinions_feed() -> Response:
    """증권사별 투자의견 [189] — 시장 전체 최근 신규 의견 피드."""
    return jsonify({"ok": True, "rows": _kis_opinions_feed(40)})


@app.get("/api/marketmap")
def api_marketmap() -> Response:
    """마켓맵 Treemap figure JSON — 섹터·기업 시총 비중 × 등락 색."""
    figjson = _marketmap_fig(request.args.get("mkt", "kospi"))
    if not figjson:
        return jsonify({"ok": False})
    return Response('{"ok":true,"fig":' + figjson + '}', mimetype="application/json")


@app.get("/api/usmap")
def api_usmap() -> Response:
    """미국 S&P500 섹터 히트맵 Treemap JSON (작업1). exch=all|nasdaq|nyse."""
    figjson = _usmap_fig(request.args.get("exch", "all"))
    if not figjson:
        return jsonify({"ok": False})
    return Response('{"ok":true,"fig":' + figjson + '}', mimetype="application/json")


_PLOTLY_JS_CACHE: str | None = None


@app.get("/plotly.js")
def plotly_js() -> Response:
    """번들 Plotly.js 제공(오프라인 .app 대응) — 장기 캐시. 시장 현황 마켓맵 등에서 사용."""
    global _PLOTLY_JS_CACHE
    if _PLOTLY_JS_CACHE is None:
        from plotly.offline import get_plotlyjs
        _PLOTLY_JS_CACHE = get_plotlyjs()
    return Response(_PLOTLY_JS_CACHE, mimetype="application/javascript",
                    headers={"Cache-Control": "public, max-age=86400"})




@app.get("/index_page")
def index_page() -> Response:
    """코스피·코스닥 지수 상세 — 캔들차트(일/주/월/년)·시세·등락 종목수·시장 뉴스."""
    return Response(_INDEX_HTML, mimetype="text/html")




@app.get("/macro_page")
def macro_page() -> Response:
    """한국 경제 지표 — 한국은행 ECOS 거시지표(금리·물가·환율) 대시보드."""
    return Response(_MACRO_HTML, mimetype="text/html")


@app.get("/market")
def market_page() -> Response:
    """시장 현황 탭 — 시총 상위·상하한가·시황 뉴스."""
    return Response(_MARKET_HTML, mimetype="text/html")


# ════════════════ 라우트 ════════════════
@app.get("/logo.png")
@app.get("/favicon.ico")
def logo() -> Response:
    """앱 로고(= 네이티브 앱 아이콘) 제공 — favicon·브랜드 이미지 공용."""
    data = _logo_bytes()
    if not data:
        # 로고 파일이 없으면 1x1 투명 PNG 폴백(404 깜빡임 방지).
        import base64
        data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42m" "NkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    return Response(data, mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


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


# ════════════════ 로컬 AI 코멘터리 (LM Studio 브리지) ════════════════
# 코멘트는 "짧고 빠른" 게 핵심이라 non-thinking 4B Instruct(qwen3-4b-2507)를 기본으로 쓴다.
# ⚠️ LM Studio /v1/models 의 data[0] 는 순서 보장이 없어(임베딩 모델·12B 가 먼저 올 수 있음)
#    그걸 그대로 쓰면 엉뚱한/느린 모델이 잡힌다 → 아래 선택기로 결정적으로 고른다.
#    환경변수 KMKT_LLM_MODEL 로 임의 모델을 강제할 수 있다.
_LLM_PREFERRED = "qwen3-4b-2507"   # 부분일치로 매칭 (예: "qwen/qwen3-4b-2507")
_LLM_MAX_TOKENS = 1200             # 비추론 모델 기본 토큰(한국어 토큰 잘림 방지)

# 추론(thinking) 계열 모델 패턴 — 답변 전 <think> 단계에 토큰을 대량 소모한다.
# ⚠️ qwen3-4b-2507 등 *2507*/Instruct 는 추론형이 아니므로 반드시 제외해야 한다.
# (실측: qwen3.5-9b 는 reasoning_content 에 모든 토큰을 쏟아 finish_reason=length 로
#  본문 content 를 0자 출력 → "응답 없음"의 근본 원인. 그래서 추론형은 식별해 다르게 다룬다.)
_LLM_REASONING_PAT = re.compile(
    r"(qwen3\.5|qwq|thinking|reasoning|deepseek-?r1|magistral|gpt-oss)", re.I)


def _is_reasoning_model(model_id: str) -> bool:
    mid = (model_id or "").lower()
    if "2507" in mid or "instruct" in mid:   # 명시적 Instruct = 비추론
        return False
    return bool(_LLM_REASONING_PAT.search(mid))


def _llm_model_profile(model_id: str) -> dict:
    """모델 스펙별 프롬프트/생성 파라미터 (작업4 — 모델별 정교 조절).

    - reasoning : <think> 에 토큰을 대량 쓰므로 예산을 크게, 본문 답변을 강제. temp↑(공식 권장).
    - gemma     : 장황해지기 쉬움 → 간결 지시 + 보통 토큰.
    - instruct  : 표준(qwen3-4b-2507 등)."""
    mid = (model_id or "").lower()
    if _is_reasoning_model(model_id):
        # 추론형(qwen3.5 등)은 thinking 을 끌 공식 스위치가 없어 <think> 에 토큰을 무한정
        # 쏟다 본문 0자로 끝난다(실측). 해결: **Assistant Prefilling** — messages 끝에
        # 빈 think 블록 `<think>\n\n</think>` 를 assistant 메시지로 주입하면 엔진이 추론을
        # "이미 끝난 것"으로 보고 reasoning_tokens=0 · finish_reason=stop 으로 즉시 본문을
        # 낸다(실측: qwen3.5-9b 1.7s · 754자 · finish=stop). 그래서 토큰 예산도 정상치로.
        return {"kind": "reasoning", "max_tokens": _LLM_MAX_TOKENS, "temperature": 0.5,
                "prefill": "<think>\n\n</think>",
                "sys_suffix": " 핵심만 간결하고 명확한 한국어로 답하세요."}
    if "gemma" in mid:
        return {"kind": "gemma", "max_tokens": 1000, "temperature": 0.3, "prefill": None,
                "sys_suffix": " 군더더기 없이 핵심 요점만 매우 간결한 한국어로 답하세요."}
    return {"kind": "instruct", "max_tokens": _LLM_MAX_TOKENS, "temperature": 0.3,
            "prefill": None, "sys_suffix": ""}


def _llm_chat_models_with_state() -> list[dict]:
    """LM Studio 채팅 가능 모델 + 로드 상태. [{id, loaded}] (임베딩 제외)."""
    import json as _json
    import urllib.request
    out: list[dict] = []
    try:                                       # /api/v0/models 는 state(loaded) 를 준다.
        with urllib.request.urlopen("http://127.0.0.1:1234/api/v0/models", timeout=5.0) as r:
            for m in _json.loads(r.read().decode("utf-8")).get("data", []):
                mid = m.get("id") or ""
                if mid and "embed" not in mid.lower():
                    out.append({"id": mid, "loaded": (m.get("state") == "loaded")})
    except Exception:  # noqa: BLE001  — 구버전 폴백(상태정보 없음)
        try:
            with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=5.0) as r:
                for m in _json.loads(r.read().decode("utf-8")).get("data", []):
                    mid = m.get("id") or ""
                    if mid and "embed" not in mid.lower():
                        out.append({"id": mid, "loaded": False})
        except Exception:  # noqa: BLE001
            return []
    return out


def _pick_llm_model_ex(models: list[dict]) -> str | None:
    """로드 상태를 고려한 모델 선택 (작업1 — 이중 로드 방지).

    핵심: 이미 '로드된' 모델을 최우선으로 쓴다. 그래야 ① 사용자가 팝오버에서 고른 모델을
    존중하고 ② 엉뚱한 2번째 모델이 JIT 로드되어 메모리에 동시 점유되는 문제를 막는다.
    로드된 게 전혀 없을 때만 선호 모델(qwen3-4b-2507)을 JIT 로드한다."""
    if not models:
        return None
    override = os.environ.get("KMKT_LLM_MODEL", "").strip()
    if override:
        for m in models:
            if m["id"] == override or override in m["id"]:
                return m["id"]
        return override

    loaded = [m["id"] for m in models if m.get("loaded")]
    # 1) 로드된 모델 중 비추론(instruct) 우선 — 빠르고 확실히 본문을 낸다.
    for mid in loaded:
        if not _is_reasoning_model(mid):
            return mid
    # 2) 로드된 게 추론형뿐이면 그거라도 사용(동시 로드 회피 > 추론 회피).
    if loaded:
        return loaded[0]
    # 3) 로드된 게 없으면 선호 모델 JIT 로드.
    all_ids = [m["id"] for m in models]
    for mid in all_ids:
        if _LLM_PREFERRED in mid:
            return mid
    # 4) 비추론 아무거나 → 5) 최후 폴백
    for mid in all_ids:
        if not _is_reasoning_model(mid):
            return mid
    return all_ids[0]


def _pick_llm_model(ids: list[str]) -> str | None:
    """(레거시 호환) id 리스트만 주어졌을 때의 선택기."""
    return _pick_llm_model_ex([{"id": x, "loaded": False} for x in (ids or [])])


# ── 종목별 뉴스·공시 [국내주식-141] (FID_INPUT_ISCD = code 필터) ──
# 기존 _kis_market_news 는 시장 전체용. AI 그라운딩엔 "해당 종목"의 뉴스/공시가 필요하므로
# 같은 news-title 엔드포인트를 종목코드로 필터(스펙: 공백=전체, 종목코드=해당 코드 뉴스)한다.
_STOCK_NEWS_CACHE: dict = {}   # code -> (rows, ts)


def _kis_stock_news(code: str, n: int = 6) -> list[dict]:
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return []
    now = time.time()
    c = _STOCK_NEWS_CACHE.get(code)
    if c and (now - c[1]) < 180.0:
        return c[0]
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return []
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}/uapi/domestic-stock/v1/quotations/news-title", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": "FHKST01011800", "custtype": "P"},
                      params={"FID_NEWS_OFER_ENTP_CODE": "", "FID_COND_MRKT_CLS_CODE": "",
                              "FID_INPUT_ISCD": code, "FID_TITL_CNTT": "",
                              "FID_RANK_SORT_CLS_CODE": "", "FID_INPUT_SRNO": "",
                              "FID_INPUT_DATE_1": "", "FID_INPUT_HOUR_1": ""})
        rows = []
        for o in (r.json().get("output") or []):
            title = (o.get("hts_pbnt_titl_cntt") or "").strip()
            if not title:
                continue
            # ⚠️ [141] 의 FID_INPUT_ISCD 필터는 느슨해서 시장 전체·대형주 뉴스를 그대로
            # 돌려준다(예: 009150 조회에도 005930/000660·코스피 뉴스가 섞임). 그대로 쓰면
            # 모델이 엉뚱한 종목 뉴스를 이 종목 것으로 오귀속한다(삼성전기↔삼성전자).
            # → 행의 iscd1..10 에 "이 종목코드"가 실제로 포함된 뉴스만 남긴다(없으면 생략).
            row_codes = {str(o.get(f"iscd{i}") or "") for i in range(1, 11)}
            if code not in row_codes:
                continue
            dt, tm = str(o.get("data_dt") or ""), str(o.get("data_tm") or "")
            when = (f"{dt[4:6]}.{dt[6:8]} {tm[:2]}:{tm[2:4]}"
                    if len(dt) == 8 and len(tm) >= 4 else dt)
            rows.append({"when": when, "title": title, "src": (o.get("dorg") or "-")})
            if len(rows) >= n:
                break
        _STOCK_NEWS_CACHE[code] = (rows, now)
        return rows
    except Exception:  # noqa: BLE001
        return []


# ── 네이버 뉴스 검색(최근순) — AI 코멘터리 "최근 소식" 강화용 ──
_NAVER_NEWS_CACHE: dict[str, tuple[list, float]] = {}


def _naver_news(query: str, n: int = 6) -> list[dict]:
    """네이버 뉴스 검색 API(sort=date) — 최신 뉴스 [{when,title,desc}]. 5분 캐시."""
    cid = os.environ.get("NAVER_CLIENT_ID", "")
    cs = os.environ.get("NAVER_CLIENT_SECRET", "")
    query = (query or "").strip()
    if not (cid and cs and query):
        return []
    ck = f"{query}:{n}"
    c = _NAVER_NEWS_CACHE.get(ck)
    if c and (time.time() - c[1]) < 300.0:
        return c[0]
    import html as _html
    try:
        r = httpx.get("https://openapi.naver.com/v1/search/news.json",
                      params={"query": query, "display": max(n, 10), "sort": "date"},
                      headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": cs}, timeout=8)
        out = []
        for it in (r.json() or {}).get("items", []):
            title = _html.unescape(re.sub(r"<.*?>", "", it.get("title", ""))).strip()
            desc = _html.unescape(re.sub(r"<.*?>", "", it.get("description", ""))).strip()
            pub = it.get("pubDate", "")
            try:
                from datetime import datetime as _dt
                pub = _dt.strptime(pub, "%a, %d %b %Y %H:%M:%S %z").strftime("%m-%d %H:%M")
            except Exception:  # noqa: BLE001
                pass
            link = (it.get("originallink") or it.get("link") or "").strip()
            if title:
                out.append({"when": pub, "title": title, "desc": desc, "link": link})
        out = out[:n]
        _NAVER_NEWS_CACHE[ck] = (out, time.time())
        return out
    except Exception:  # noqa: BLE001
        return []


# ── AI 코멘터리용 "데이터 시트" 구성 (실데이터 그라운딩) ──
# 모델에 코드만 주면 수치를 전부 환각한다 → 앱이 이미 계산하는 실데이터(시세·모멘텀·
# 리스크 지표·뉴스)를 모아 프롬프트에 넣고, "주어진 수치만 근거로 쓰라"고 지시한다.
# 정책(2026-06): 과거 주가 흐름은 한 줄로 압축하고 '최근 뉴스'를 본문 중심으로 둔다.
_AI_CTX_CACHE: dict = {}   # code -> (name, sheet, ts)


def _ai_stock_name(code: str) -> str:
    try:
        for c in company.get_corps():
            if str(c.get("stock_code") or "") == code:
                return c.get("corp_name") or code
    except Exception:  # noqa: BLE001
        pass
    return code


# ════════════════ 기업 개요/프로필 수집 (작업2) ════════════════
# 국내=DART company.json(대표·설립·주소·홈페이지·전화), 해외=Yahoo quoteSummary
# assetProfile(섹터·산업·직원수·기업설명·임원). 결과는 정규화 dict 로 통일해 동일 카드로 렌더.
_PROFILE_CACHE: dict = {}          # key -> (normalized|None, ts)
_PROFILE_TTL = 21600.0             # 6h (프로필은 잘 안 변함)
_YH_SESS: dict = {"crumb": None, "cookie": None, "ts": 0.0}


def _dart_key() -> str | None:
    k = os.environ.get("DART_KEY")
    if k:
        return k.strip()
    try:
        for envp in ("API.env", os.path.join(os.path.dirname(__file__), "..", "API.env")):
            if os.path.exists(envp):
                for line in open(envp, encoding="utf-8"):
                    m = re.match(r'\s*DART_KEY\s*=\s*"?([^"\n]+)"?', line)
                    if m:
                        return m.group(1).strip()
    except Exception:  # noqa: BLE001
        pass
    return None


def _corp_code_for(code: str) -> str | None:
    try:
        for c in company.get_corps():
            if str(c.get("stock_code") or "") == code:
                return c.get("corp_code")
    except Exception:  # noqa: BLE001
        pass
    return None


def _dart_company_profile(code: str) -> dict | None:
    """국내 종목 → 정규화 프로필 {desc, facts:[(라벨,값)...], officers, more}."""
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return None
    ck = f"dart:{code}"
    c = _PROFILE_CACHE.get(ck)
    if c and (time.time() - c[1]) < _PROFILE_TTL:
        return c[0]
    key, corp = _dart_key(), _corp_code_for(code)
    out = None
    if key and corp:
        try:
            r = httpx.get("https://opendart.fss.or.kr/api/company.json",
                          params={"crtfc_key": key, "corp_code": corp}, timeout=8)
            d = r.json()
            if d.get("status") == "000":
                est = str(d.get("est_dt") or "")
                est_f = f"{est[:4]}.{est[4:6]}.{est[6:8]}" if len(est) == 8 else (est or None)
                home = (d.get("hm_url") or "").strip()
                if home and not home.startswith("http"):
                    home = "http://" + home
                facts = []
                if d.get("ceo_nm"):
                    facts.append(("대표이사", d["ceo_nm"]))
                if est_f:
                    facts.append(("설립일", est_f))
                if (d.get("adres") or "").strip():
                    facts.append(("본사", d["adres"].strip()))
                if home:
                    facts.append(("홈페이지", f'<a href="{home}" target="_blank" '
                                  f'style="color:#0a84ff;text-decoration:none;">{home}</a>'))
                if (d.get("phn_no") or "").strip():
                    facts.append(("전화", d["phn_no"].strip()))
                if (d.get("induty_code") or "").strip():
                    facts.append(("표준산업분류", str(d["induty_code"]).strip()))
                out = {"desc": None, "facts": facts, "officers": [],
                       "src": "DART 전자공시"}
        except Exception:  # noqa: BLE001
            out = None
    _PROFILE_CACHE[ck] = (out, time.time())
    return out


def _yahoo_session():
    """Yahoo quoteSummary 용 (opener, crumb). 쿠키+crumb 를 ~50분 캐시. 실패 시 (None,None)."""
    import http.cookiejar
    import urllib.request as _u
    now = time.time()
    if _YH_SESS["crumb"] and (now - _YH_SESS["ts"]) < 3000.0:
        return _YH_SESS.get("opener"), _YH_SESS["crumb"]
    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120 Safari/537.36")
    cj = http.cookiejar.CookieJar()
    op = _u.build_opener(_u.HTTPCookieProcessor(cj))

    def g(url):
        with op.open(_u.Request(url, headers={"User-Agent": ua}), timeout=10) as r:
            return r.read().decode("utf-8", "replace")
    try:
        g("https://finance.yahoo.com")
        for host in ("query2", "query1"):
            try:
                cr = g(f"https://{host}.finance.yahoo.com/v1/test/getcrumb")
                if cr and "Too Many" not in cr and "<" not in cr:
                    _YH_SESS.update({"crumb": cr.strip(), "opener": op, "ts": now})
                    return op, cr.strip()
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return None, None


def _yahoo_profile(symbol: str) -> dict | None:
    """해외 심볼 → 정규화 프로필. Yahoo assetProfile. 실패(401/429 등) 시 None(우아한 생략)."""
    import urllib.parse
    import urllib.request as _u
    symbol = (symbol or "").strip().upper()
    if not symbol:
        return None
    ck = f"yh:{symbol}"
    c = _PROFILE_CACHE.get(ck)
    if c and (time.time() - c[1]) < _PROFILE_TTL:
        return c[0]
    out = None
    op, crumb = _yahoo_session()
    if op and crumb:
        ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120 Safari/537.36")
        url = (f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(symbol)}"
               f"?modules=assetProfile&crumb={urllib.parse.quote(crumb)}")
        try:
            with op.open(_u.Request(url, headers={"User-Agent": ua}), timeout=10) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            p = (d.get("quoteSummary", {}).get("result") or [{}])[0].get("assetProfile") or {}
            if p:
                facts = []
                if p.get("sector"):
                    facts.append(("섹터", p["sector"]))
                if p.get("industry"):
                    facts.append(("산업", p["industry"]))
                if p.get("fullTimeEmployees"):
                    facts.append(("임직원", f"{int(p['fullTimeEmployees']):,}명"))
                loc = ", ".join([x for x in (p.get("city"), p.get("country")) if x])
                if loc:
                    facts.append(("본사", loc))
                web = (p.get("website") or "").strip()
                if web:
                    facts.append(("홈페이지", f'<a href="{web}" target="_blank" '
                                  f'style="color:#0a84ff;text-decoration:none;">{web}</a>'))
                officers = [f"{o.get('name')} ({o.get('title')})"
                            for o in (p.get("companyOfficers") or [])[:4]
                            if o.get("name")]
                out = {"desc": (p.get("longBusinessSummary") or "").strip() or None,
                       "facts": facts, "officers": officers, "src": "Yahoo Finance"}
        except Exception:  # noqa: BLE001  (401/429/파싱 실패 → 폴백)
            out = None
    if out is None:
        # 폴백: 무인증 search 엔드포인트(crumb 불필요) — 최소 섹터·산업이라도 채운다.
        try:
            su = (f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(symbol)}"
                  "&quotesCount=1&newsCount=0")
            with _u.urlopen(_u.Request(su, headers={"User-Agent": "Mozilla/5.0"}), timeout=8) as r:
                q = (json.loads(r.read().decode("utf-8", "replace")).get("quotes") or [{}])[0]
            facts = []
            if q.get("sector"):
                facts.append(("섹터", q["sector"]))
            if q.get("industry"):
                facts.append(("산업", q["industry"]))
            if q.get("exchDisp"):
                facts.append(("거래소", q["exchDisp"]))
            if facts:
                desc = (q.get("longname") or q.get("shortname") or "")
                out = {"desc": (desc + " 의 기업 분류 정보입니다." if desc else None),
                       "facts": facts, "officers": [], "src": "Yahoo Finance"}
        except Exception:  # noqa: BLE001
            out = None
    _PROFILE_CACHE[ck] = (out, time.time())
    return out


def _profile_card_html(prof: dict | None) -> str:
    """정규화 프로필 → 자기완결 카드 HTML(국내/해외 페이지 공통). 데이터 없으면 ''."""
    import html as _h
    if not prof or (not prof.get("facts") and not prof.get("desc")):
        return ""
    rows = "".join(
        f'<div style="color:#8a94a6;white-space:nowrap;">{_h.escape(k)}</div>'
        f'<div style="min-width:0;word-break:break-word;">{v}</div>'
        for k, v in prof.get("facts", []))
    desc = prof.get("desc")
    desc_html = ""
    if desc:
        if len(desc) > 700:
            desc = desc[:700] + "…"
        desc_html = (f'<p style="font-size:13px;line-height:1.65;margin:0 0 12px;color:inherit;'
                     f'opacity:.92;">{_h.escape(desc)}</p>')
    off = prof.get("officers") or []
    off_html = ""
    if off:
        items = "".join(f"<li style=\"margin:2px 0;\">{_h.escape(x)}</li>" for x in off)
        off_html = (f'<div style="margin-top:10px;"><div style="color:#8a94a6;font-size:12px;'
                    f'margin-bottom:3px;">주요 임원</div><ul style="margin:0;padding-left:16px;'
                    f'font-size:12.5px;line-height:1.5;">{items}</ul></div>')
    src = prof.get("src", "")
    return (f'<section class="card" id="kmkt-profile" style="overflow:hidden;">'
            f'<h3 class="card-title" style="margin:0 0 10px;">🏢 기업 개요</h3>'
            f'{desc_html}'
            f'<div style="display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;'
            f'font-size:13px;line-height:1.5;">{rows}</div>{off_html}'
            f'<div style="margin-top:10px;font-size:11px;color:#8a94a6;">출처: {_h.escape(src)}</div>'
            f'</section>')


def _build_ai_context(code: str) -> tuple[str, str | None]:
    """(종목명, 데이터시트 문자열|None) 반환. 시트는 실데이터만 담는다(없으면 줄 생략)."""
    code = (code or "").strip()
    name = _ai_stock_name(code)
    now = time.time()
    c = _AI_CTX_CACHE.get(code)
    if c and (now - c[2]) < 90.0:
        return c[0], c[1]

    lines: list[str] = [f"종목: {name} ({code})"]

    # ① 실시간 시세 / 종가
    try:
        pr = _kis_price(code)
        if pr.get("ok") and pr.get("price") is not None:
            tag = "현재가" if pr.get("market_open") else "종가"
            s = f"{tag}: {int(float(pr['price'])):,}원"
            if pr.get("change_pct") is not None:
                s += f" (전일대비 {float(pr['change_pct']):+.2f}%)"
            lines.append(s)
    except Exception:  # noqa: BLE001
        pass

    # ② 시세 흐름 — 한 줄로 압축(보조 지표). 과거 주가보다 아래 '최근 뉴스'를 우선.
    try:
        _dates, closes = _clean_closes(asyncio.run(_afetch(code, 400)))
        if closes.size >= 60:
            cur = float(closes[-1])
            mom = []
            for lbl, k in (("5일", 5), ("20일", 20), ("60일", 60)):
                if closes.size > k:
                    mom.append(f"{lbl} {(cur / float(closes[-1 - k]) - 1) * 100:+.1f}%")
            win = closes[-252:] if closes.size >= 252 else closes
            lo = float(np.percentile(win, 1))
            hi = float(np.percentile(win, 99))
            extra = ""
            if hi > lo:
                pos = min(100.0, max(0.0, (cur - lo) / (hi - lo) * 100))
                extra = f" · 52주밴드 {pos:.0f}%"
            try:
                rs = _risk_stats(closes)
                extra += f" · 연변동성 {rs['ann_vol']:.0f}% · MDD {rs['mdd']:.0f}%"
            except Exception:  # noqa: BLE001
                pass
            if mom:
                lines.append("시세 흐름(보조): 모멘텀 " + " · ".join(mom) + extra)
    except Exception:  # noqa: BLE001
        pass

    # ③ 최근 뉴스 (본문 중심) — 네이버 뉴스 검색(최신순, 요약 포함) + KIS 공시 [141] 병합·근접중복제거(작업2)
    cand: list[dict] = []
    try:
        for nrow in _naver_news(name, 7):
            cand.append({"when": nrow.get("when", ""), "title": nrow.get("title", ""),
                         "desc": nrow.get("desc", ""), "src": ""})
    except Exception:  # noqa: BLE001
        pass
    try:
        for nrow in _kis_stock_news(code, 5):
            cand.append({"when": nrow.get("when", ""), "title": nrow.get("title", ""),
                         "desc": "", "src": nrow.get("src", "")})
    except Exception:  # noqa: BLE001
        pass
    news_lines: list[str] = []
    for nrow in _dedup_news(cand):                        # 비슷한 기사는 하나만 남김
        t = nrow["title"]
        if len(t) > 64:
            t = t[:64] + "…"
        desc = nrow.get("desc", "")
        if len(desc) > 90:
            desc = desc[:90] + "…"
        src = f" ({nrow['src']})" if nrow.get("src") and nrow["src"] != "-" else ""
        if desc:
            news_lines.append(f"- [{nrow.get('when', '')}] {t} — {desc}")
        else:
            news_lines.append(f"- [{nrow.get('when', '')}] {t}{src}")
    if news_lines:
        lines.append("[최근 뉴스 — 분석의 핵심 근거]")
        lines.extend(news_lines[:10])

    sheet = "\n".join(lines) if len(lines) > 1 else None
    _AI_CTX_CACHE[code] = (name, sheet, now)
    return name, sheet


_OV_AI_CTX_CACHE: dict = {}   # "excd:symb" -> (name, sheet, ts)


def _build_ov_ai_context(excd: str, symb: str) -> tuple[str, str | None]:
    """해외 종목 AI 컨텍스트(작업3) — 실데이터(시세·모멘텀·밸류·기업개요·뉴스)만 담는다."""
    excd = (excd or "").strip().upper()
    symb = (symb or "").strip().upper()
    ck = f"{excd}:{symb}"
    now = time.time()
    c = _OV_AI_CTX_CACHE.get(ck)
    if c and (now - c[2]) < 90.0:
        return c[0], c[1]
    lines = [f"종목: {symb} ({_OV_EXNAME.get(excd, excd)} 상장, 해외주식)"]
    try:
        d = _ov_detail(excd, symb)
        if isinstance(d, dict) and d.get("ok"):
            ccy = d.get("ccy", "")
            lines.append(f"현재가: {ccy}{d['last']:,.2f} (전일대비 {d['rate']:+.2f}%)")
            if d.get("h52p", 0) > d.get("l52p", 0):
                pos = min(100, max(0, (d["last"] - d["l52p"]) / (d["h52p"] - d["l52p"]) * 100))
                lines.append(f"52주 범위 {ccy}{d['l52p']:,.2f}~{ccy}{d['h52p']:,.2f} (현재 위치 {pos:.0f}%)")
            extra = []
            if d.get("per", 0) > 0:
                extra.append(f"PER {d['per']:.1f}")
            if d.get("pbr", 0) > 0:
                extra.append(f"PBR {d['pbr']:.1f}")
            if d.get("sector"):
                extra.append(f"섹터 {d['sector']}")
            if extra:
                lines.append("밸류에이션: " + " · ".join(extra))
    except Exception:  # noqa: BLE001
        pass
    try:
        closes = [r["c"] for r in _ov_chart(excd, symb, "0").get("rows", []) if r.get("c", 0) > 0]
        if len(closes) >= 20:
            cur, mom = closes[-1], []
            for lbl, k in (("5일", 5), ("20일", 20), ("60일", 60)):
                if len(closes) > k:
                    mom.append(f"{lbl} {(cur / closes[-1 - k] - 1) * 100:+.1f}%")
            if mom:
                lines.append("모멘텀(보조): " + " · ".join(mom))
    except Exception:  # noqa: BLE001
        pass
    try:
        prof = _yahoo_profile(symb)
        if prof:
            facts = "; ".join(f"{k} {re.sub('<[^>]+>', '', str(v))}" for k, v in prof.get("facts", []))
            if facts:
                lines.append(f"[기업 정보] {facts}")
            if prof.get("desc"):
                lines.append("[사업 개요] " + prof["desc"][:320])
    except Exception:  # noqa: BLE001
        pass
    try:
        rows = (_ov_news(excd, symb) or {}).get("rows", [])
        if rows:
            lines.append("[최근 뉴스 — 분석의 핵심 근거]")
            for r in rows[:8]:
                t = (r.get("title") or "")[:84]
                dt = str(r.get("date") or "")
                when = f"{dt[4:6]}.{dt[6:8]}" if len(dt) == 8 else ""
                lines.append(f"- [{when}] {t}")
    except Exception:  # noqa: BLE001
        pass
    sheet = "\n".join(lines) if len(lines) > 1 else None
    _OV_AI_CTX_CACHE[ck] = (symb, sheet, now)
    return symb, sheet


# ════════════════ 앱 전반 'AI 질문하기' (작업4) — 화면 컨텍스트 + 질문 → 답변 ════════════════
def _macro_text() -> str:
    try:
        d = _macro_snapshot()
        k = (d or {}).get("kpi", {})
        a = (d or {}).get("asof", {})
        p = []
        if k.get("base") is not None:
            p.append(f"기준금리 {k['base']}% ({a.get('rate', '')})")
        if k.get("g3") is not None:
            p.append(f"국고채 3년 {k['g3']}% / 10년 {k.get('g10')}%")
        if k.get("spread") is not None:
            p.append(f"장단기 스프레드(10-3) {k['spread']}%p")
        if k.get("usd") is not None:
            p.append(f"원/달러 환율 {k['usd']}원 ({a.get('fx', '')})")
        if k.get("cpi_yoy") is not None:
            p.append(f"소비자물가 YoY {k['cpi_yoy']}% (총지수 {k.get('cpi')})")
        rb = (d or {}).get("commentary", {}).get("overall", {})
        if rb.get("title"):
            p.append(f"규칙기반 종합판단: {rb['title']} — {rb.get('t', '')}")
        try:                                    # 글로벌 지표도 함께 그라운딩(작업4)
            g = _global_macro_snapshot()
            if g.get("ok") and g.get("rows"):
                gl = ", ".join(f"{r['key']} {r['price']}{r.get('unit', '')}"
                               f"({'+' if r['dir'] == 'up' else ''}{r['pct']}%)" for r in g["rows"])
                p.append(f"[글로벌 지표] {gl}")
        except Exception:  # noqa: BLE001
            pass
        return "\n".join(p) if p else "데이터 없음"
    except Exception:  # noqa: BLE001
        return "데이터 없음"


def _index_text(code: str) -> str:
    try:
        d = _kis_index(code or "0001")
        if d.get("ok"):
            cp = d.get("change_pct")
            return (f"{d.get('name', '지수')} ({d.get('code', code)}): {d.get('value')} "
                    f"({cp:+.2f}%)" if cp is not None else f"{d.get('name', '지수')}: {d.get('value')}")
    except Exception:  # noqa: BLE001
        pass
    return "데이터 없음"


def _ask_context(scope: str, ident: str, excd: str = "") -> str:
    """현재 화면(scope) + 식별자 → 실데이터 컨텍스트 문자열(작업4). 신선 데이터만."""
    scope = (scope or "").strip()
    ident = (ident or "").strip()
    if scope in ("stock", "etf") and ident:
        nm, sheet = _build_ai_context(ident)
        label = "ETF" if scope == "etf" else "종목"
        out = [f"[{label} 화면: {nm} ({ident})]", (sheet or "데이터 없음")]
        # 화면에 이미 떠 있는 '기업 정보'(DART 프로필)를 함께 제공 → 외부 재수집 불필요(작업1)
        if scope == "stock" and ident.isdigit() and len(ident) == 6:
            try:
                p = _dart_company_profile(ident) or {}
                facts = [f"{k} {re.sub('<[^>]+>', '', str(v)).strip()}" for k, v in (p.get("facts") or [])
                         if k in ("대표이사", "설립일", "본사", "표준산업분류")]
                if facts:
                    out.append("[화면의 기업 정보] " + " · ".join(facts))
            except Exception:  # noqa: BLE001
                pass
        return "\n".join(out)
    if scope == "ov" and ident:
        nm, sheet = _build_ov_ai_context(excd, ident)
        return f"[해외종목 화면: {ident}]\n" + (sheet or "데이터 없음")
    if scope == "macro":
        return "[한국 경제지표 화면]\n" + _macro_text()
    if scope == "world":
        view = ident if ident in ("kr", "us", "global") else "us"
        return _world_ai_text(view)
    if scope == "market":
        # 홈·시장 개요·섹터·실시간 등 국내 시장 화면 — 코스피/코스닥 + 시총 상위 종목.
        return _market_ai_text()
    if scope == "backtest":
        # 백테스트 화면 — 현재 국내 시장 상황을 배경으로 제공(전략 설정·결과는 '참고 데이터' 주입 권장).
        return ("[백테스트 화면]\n" + _market_ai_text()
                + "\n(참고: 백테스트의 구체적 전략·기간·성과 수치는 채팅창의 '참고 데이터'에 붙여넣으면 "
                  "더 정확히 분석합니다.)")
    if scope == "index":
        return "[지수 화면]\n" + _index_text(ident)
    if scope == "research":
        # PDF 뷰어에서 'cat:nid' 로 들어오면 → 지금 열려 있는 그 리포트 원문을 직접 읽어 제공.
        if ":" in ident:
            _c, _, _n = ident.partition(":")
            if _c in _RESEARCH_CATS and (_c in ("bok", "bok_mp") or _n.isdigit()):
                try:
                    if _c == "market":
                        body = _market_brief_text()
                    else:
                        body, _pdf = _research_read(_c, _n)
                except Exception:  # noqa: BLE001
                    body = ""
                label = _RESEARCH_CATS.get(_c, ("", "리포트"))[1]
                if body and len(body) >= 40:
                    return f"[지금 보고 있는 증권사 리포트 — {label}]\n{body[:6000]}"
                return (f"[증권사 리포트 뷰어 — {label}] 원문 텍스트를 추출하지 못했습니다"
                        "(이미지형 PDF일 수 있음). 사용자가 화면에서 보는 내용을 '참고 데이터'에 "
                        "붙여넣으면 분석해 드립니다.")
        # 리포트 목록 화면 → 현재 카테고리 목록 + 상위 리포트 본문을 백그라운드에서 읽어 제공(작업1)
        cat = ident if ident in _RESEARCH_CATS else "daily"
        try:
            rows = _research_list(cat)[:6]
        except Exception:  # noqa: BLE001
            rows = []
        lines = [f"[증권사 리포트 화면 — {_RESEARCH_CATS.get(cat, ('', '리포트'))[1]} 목록]"]
        for r in rows:
            lines.append(f"- {r.get('title', '')} ({r.get('broker', '')}, {r.get('date', '')})")
        for r in rows[:2]:                 # 상위 2개 리포트 본문을 직접 읽어옴
            try:
                if cat == "market":
                    body = _market_brief_text()
                else:
                    body, _pdf = _research_read(cat, r.get("nid", ""))
                if body:
                    lines.append(f"\n[리포트 본문 — {r.get('title', '')}]\n{body[:1800]}")
            except Exception:  # noqa: BLE001
                pass
        return "\n".join(lines)
    return ""


def _fsc_key() -> str | None:
    """오픈 API 인증키(FSC_KEY) 획득."""
    k = os.environ.get("FSC_KEY")
    if k:
        return k.strip()
    try:
        for envp in ("API.env", os.path.join(os.path.dirname(__file__), "..", "API.env")):
            if os.path.exists(envp):
                for line in open(envp, encoding="utf-8"):
                    m = re.match(r'\s*FSC_KEY\s*=\s*"?([^"\n]+)"?', line)
                    if m:
                        return m.group(1).strip()
    except Exception:  # noqa: BLE001
        pass
    return None


def _get_jurir_no(code: str) -> str | None:
    """DART API를 통해 6자리 종목코드에 해당하는 법인등록번호(jurir_no)를 조회."""
    key = _dart_key()
    corp = _corp_code_for(code)
    if key and corp:
        try:
            r = httpx.get("https://opendart.fss.or.kr/api/company.json",
                          params={"crtfc_key": key, "corp_code": corp}, timeout=8)
            d = r.json()
            if d.get("status") == "000":
                return str(d.get("jurir_no") or "").strip()
        except Exception:  # noqa: BLE001
            pass
    return None


def _get_governance_shareholders(code: str) -> str:
    """금융위 및 DART API를 활용하여 6자리 종목코드의 최대주주 지분율 및 지배구조 현황 조회."""
    try:
        from market_intel.collectors import fsc, dart as dart_c
        from market_intel.httpx_client import Fetcher
        
        jurir_no = _get_jurir_no(code)
        corp_code = _corp_code_for(code)
        fsc_key = _fsc_key()
        dart_key = _dart_key()
        
        if not corp_code:
            return "종목에 해당하는 DART 법인코드를 찾을 수 없습니다."
            
        async def _run_fsc():
            if not fsc_key or not jurir_no:
                return {}
            async with Fetcher() as f:
                return await fsc.fetch_governance_shareholders(f, fsc_key, jurir_no)
                
        async def _run_dart():
            if not dart_key:
                return {}
            async with Fetcher() as f:
                return await dart_c.fetch_major_shareholders(f, dart_key, corp_code)
                
        data = {}
        if fsc_key and jurir_no:
            try:
                data = asyncio.run(_run_fsc())
            except Exception:  # noqa: BLE001
                data = {}
                
        if not data or not data.get("holders"):
            try:
                data = asyncio.run(_run_dart())
            except Exception:  # noqa: BLE001
                data = {}
                
        if not data or not data.get("holders"):
            return "지배구조 주주 데이터가 전자공시에 등록되지 않았거나 조회에 실패했습니다."
            
        out = [
            f"★ 지배구조/주주 현황 (기준: {data.get('year', '')}년)",
            f"최대주주 및 특수관계인 합계 지분율: {data.get('최대주주측합계(%)', '')}%",
            "세부 지분율 내역:"
        ]
        for h in data.get("holders", []):
            out.append(f"- {h.get('성명', '')} ({h.get('관계', '특수관계인')}): {h.get('지분율(%)', '')}%")
        return "\n".join(out)
    except Exception as e:  # noqa: BLE001
        return f"지배구조 수집 중 오류 발생: {str(e)}"


def _get_financial_statements(code: str) -> str:
    """DART API를 통해 6자리 종목코드의 최근 3개년 주요 재무제표 텍스트 반환."""
    try:
        from market_intel.collectors import dart as dart_c
        from market_intel.httpx_client import Fetcher
        
        corp_code = _corp_code_for(code)
        dart_key = _dart_key()
        if not corp_code or not dart_key:
            return "DART 법인코드 또는 API 키가 존재하지 않습니다."
            
        async def _run():
            async with Fetcher() as f:
                return await dart_c.fetch_statements(f, dart_key, corp_code)
                
        data = asyncio.run(_run())
        if not data:
            return "재무제표 데이터를 조회하지 못했습니다."
            
        out = [
            f"★ 재무제표 요약 (연도: {data.get('year', '')}년 기준, 구분: {data.get('fs_div', '')})",
        ]
        for fs_type in ("income", "balance", "cashflow"):
            df = data.get(fs_type)
            if isinstance(df, pd.DataFrame) and not df.empty:
                title = "손익계산서" if fs_type == "income" else ("재무상태표" if fs_type == "balance" else "현금흐름표")
                out.append(f"\n[{title}]")
                out.append(df.to_string(index=False))
        return "\n".join(out)
    except Exception as e:  # noqa: BLE001
        return f"재무제표 수집 중 오류 발생: {str(e)}"


# ════════════════ 미국/글로벌 데이터 레이어 (FMP stable + Polygon) — 작업1/2 ════════════════
# FMP 무료 'stable' 엔드포인트: quote·profile·ratios-ttm·key-metrics-ttm·peers·price-target·
# grades(애널리스트)·movers. Polygon: grouped-daily(전 미국종목 OHLCV 1콜). 에이전트 도구 +
# 세계 페이지 미국 리스트가 공유. (v3 는 2025-08 폐지 → stable 사용)
_FMP_BASE = "https://financialmodelingprep.com/stable"
_FMP_CACHE: dict = {}


def _fmp_get(path: str, ttl: float = 300.0):
    key = os.environ.get("FMP_KEY", "")
    if not key:
        return None
    c = _FMP_CACHE.get(path)
    if c and (time.time() - c[1]) < ttl:
        return c[0]
    sep = "&" if "?" in path else "?"
    try:
        r = httpx.get(f"{_FMP_BASE}/{path}{sep}apikey={key}", timeout=12)
        j = r.json()
        if isinstance(j, dict) and j.get("Error Message"):
            return None
        _FMP_CACHE[path] = (j, time.time())
        return j
    except Exception:  # noqa: BLE001
        return None


def _fmp_one(path: str, ttl: float = 300.0):
    j = _fmp_get(path, ttl)
    if isinstance(j, list):
        return j[0] if j else None
    return j if isinstance(j, dict) else None


def _fnum(v, suf="", dec=2, pct=False):
    try:
        x = float(v)
        if pct:
            x *= 100
        return f"{x:,.{dec}f}{suf}"
    except (TypeError, ValueError):
        return None


def _get_overseas_financials(symb: str) -> str:
    """해외 종목 종합 펀더멘털 (FMP stable: profile·quote·ratios-ttm·key-metrics-ttm). DART 없는
    해외 종목용. 실패 시 Finnhub /stock/metric 폴백."""
    symb = symb.upper()
    prof = _fmp_one(f"profile?symbol={symb}", 3600)
    q = _fmp_one(f"quote?symbol={symb}", 60)
    ratios = _fmp_one(f"ratios-ttm?symbol={symb}", 1800)
    km = _fmp_one(f"key-metrics-ttm?symbol={symb}", 1800)
    if prof or q or ratios:
        out = [f"★ {symb} 펀더멘털 (FMP, TTM 기준)"]
        if prof:
            sec = " · ".join(x for x in [prof.get("sector"), prof.get("industry")] if x)
            if sec:
                out.append(f"- 섹터/산업: {sec}")
            mc = _fnum(prof.get("marketCap"), dec=0)
            if mc:
                out.append(f"- 시가총액: ${mc}")
        if q:
            for lab, v in [("현재가", _fnum(q.get("price"))), ("등락", _fnum(q.get("changePercentage"), "%")),
                           ("52주 고/저", f"{_fnum(q.get('yearHigh'))} / {_fnum(q.get('yearLow'))}"),
                           ("PER", _fnum(q.get("pe"))), ("EPS", _fnum(q.get("eps"))),
                           ("거래량", _fnum(q.get("volume"), dec=0)),
                           ("50/200일 평균", f"{_fnum(q.get('priceAvg50'))} / {_fnum(q.get('priceAvg200'))}")]:
                if v and "None" not in v:
                    out.append(f"- {lab}: {v}")
        if ratios:
            for lab, key, pc in [("유동비율", "currentRatioTTM", False), ("당좌비율", "quickRatioTTM", False),
                                  ("부채비율 D/E", "debtToEquityRatioTTM", False),
                                  ("순이익률", "netProfitMarginTTM", True), ("영업이익률", "operatingProfitMarginTTM", True),
                                  ("매출총이익률", "grossProfitMarginTTM", True), ("ROE", "returnOnEquityTTM", True),
                                  ("ROA", "returnOnAssetsTTM", True), ("배당수익률", "dividendYieldTTM", True)]:
                v = _fnum(ratios.get(key), "%" if pc else "", pct=pc)
                if v:
                    out.append(f"- {lab}: {v}")
        if km:
            for lab, key in [("EV/EBITDA", "evToEBITDATTM"), ("EV/매출", "evToSalesTTM"),
                             ("PBR", "pbRatioTTM"), ("PSR", "priceToSalesRatioTTM")]:
                v = _fnum(km.get(key))
                if v:
                    out.append(f"- {lab}: {v}")
        if len(out) > 1:
            return "\n".join(out)
    # ── 폴백: Finnhub ──
    key = os.environ.get("FINNHUB_KEY", "")
    if not key:
        return "해외 재무지표를 조회하지 못했습니다 (FMP/Finnhub 키 확인)."
    try:
        m = (httpx.get("https://finnhub.io/api/v1/stock/metric",
                       params={"symbol": symb, "metric": "all", "token": key}, timeout=10).json() or {}).get("metric", {})
        if not m:
            return "해외 재무지표를 찾지 못했습니다."

        def g(*ks):
            for k in ks:
                if m.get(k) not in (None, "", 0):
                    return m[k]
            return None
        rows = [("유동비율", g("currentRatioQuarterly")), ("당좌비율", g("quickRatioQuarterly")),
                ("부채비율 D/E", g("totalDebt/totalEquityQuarterly")), ("순이익률%", g("netProfitMarginTTM")),
                ("ROE%", g("roeTTM")), ("매출성장%", g("revenueGrowthTTMYoy")), ("PER", g("peTTM"))]
        out = [f"★ {symb} 재무지표 (Finnhub)"] + [f"- {k}: {v:.2f}" for k, v in rows if isinstance(v, (int, float))]
        return "\n".join(out) if len(out) > 1 else "해외 재무지표를 찾지 못했습니다."
    except Exception as e:  # noqa: BLE001
        return f"해외 재무지표 조회 중 오류: {str(e)[:120]}"


def _get_analyst_view(scope: str, ident: str) -> str:
    """애널리스트 컨센서스·목표주가. 미국=FMP(grades+price-target), 국내=KIS 투자의견."""
    if scope == "ov" or not (ident.isdigit() and len(ident) == 6):
        sym = ident.upper()
        gr = _fmp_one(f"grades-consensus?symbol={sym}", 1800)
        tg = _fmp_one(f"price-target-consensus?symbol={sym}", 1800)
        out = [f"★ {sym} 애널리스트 컨센서스 (FMP)"]
        if gr:
            out.append(f"- 의견분포: 적극매수 {gr.get('strongBuy',0)} · 매수 {gr.get('buy',0)} · "
                       f"보유 {gr.get('hold',0)} · 매도 {gr.get('sell',0)} · 적극매도 {gr.get('strongSell',0)} "
                       f"→ 종합 '{gr.get('consensus','-')}'")
        if tg:
            out.append(f"- 목표주가: 컨센서스 ${_fnum(tg.get('targetConsensus'))} "
                       f"(중간값 ${_fnum(tg.get('targetMedian'))}, 최고 ${_fnum(tg.get('targetHigh'))}, 최저 ${_fnum(tg.get('targetLow'))})")
        return "\n".join(out) if len(out) > 1 else "애널리스트 데이터를 찾지 못했습니다."
    # 국내: KIS 투자의견
    try:
        from market_intel.collectors import kis as kis_c
        from market_intel.httpx_client import Fetcher

        async def _run():
            async with Fetcher() as f:
                return await kis_c.fetch_invest_opinions(ident)
        op = asyncio.run(_run()) or {}
        cons = op.get("consensus") or {}
        if cons:
            return (f"★ {ident} 애널리스트 컨센서스 (KIS)\n"
                    f"- 평균의견 {cons.get('mean','-')}/5 · 목표가 {cons.get('target','-')} "
                    f"· 분포 매수 {cons.get('buy',0)}/중립 {cons.get('hold',0)}/매도 {cons.get('sell',0)}")
    except Exception:  # noqa: BLE001
        pass
    return "국내 애널리스트 컨센서스를 찾지 못했습니다."


def _get_valuation_peers(scope: str, ident: str) -> str:
    """동종업계 비교 — 미국=FMP stock-peers + 각 peer quote(PER/시총). 국내는 생략(추후)."""
    if scope != "ov" and (ident.isdigit() and len(ident) == 6):
        return ""
    sym = ident.upper()
    peers = _fmp_get(f"stock-peers?symbol={sym}", 3600)
    if not isinstance(peers, list) or not peers:
        return ""
    out = [f"★ {sym} 동종업계 비교 (FMP, 시총 상위)"]
    rows = sorted(peers, key=lambda x: -(x.get("mktCap") or 0))[:6]
    for p in rows:
        mc = _fnum(p.get("mktCap"), dec=0)
        out.append(f"- {p.get('symbol')} {p.get('companyName','')}: ${_fnum(p.get('price'))}"
                   + (f" · 시총 ${mc}" if mc else ""))
    return "\n".join(out) if len(out) > 1 else ""


def _get_price_technicals(scope: str, ident: str, excd: str = "") -> str:
    """가격·기술적 스냅샷 — 최근 종가 시계열로 모멘텀(5/20/60일)·52주 위치·연율변동성·MA배열.
    국내(6자리)=네이버 _afetch, 해외=_ov_chart. 화면 밖 정량 근거 보강."""
    try:
        if ident.isdigit() and len(ident) == 6:
            _d, closes = _clean_closes(asyncio.run(_afetch(ident, 320)))
            closes = list(closes)
        else:
            closes = [r["c"] for r in _ov_chart(excd, ident.upper(), "0").get("rows", []) if r.get("c", 0) > 0]
        if len(closes) < 30:
            return ""
        cur = closes[-1]
        out = [f"★ {ident.upper()} 가격·기술적 스냅샷"]
        mom = []
        for lab, k in (("5일", 5), ("20일", 20), ("60일", 60), ("120일", 120)):
            if len(closes) > k:
                mom.append(f"{lab} {(cur/closes[-1-k]-1)*100:+.1f}%")
        if mom:
            out.append("- 모멘텀: " + " · ".join(mom))
        hi = max(closes[-252:]); lo = min(closes[-252:])
        if hi > lo:
            out.append(f"- 52주 위치: {(cur-lo)/(hi-lo)*100:.0f}% (고 {hi:,.2f} / 저 {lo:,.2f})")
        try:
            rs = _risk_stats(closes)
            out.append(f"- 연율 변동성 {rs['ann_vol']:.0f}% · 최대낙폭 {rs['mdd']:.0f}%")
        except Exception:  # noqa: BLE001
            pass

        def ma(n):
            return sum(closes[-n:]) / n if len(closes) >= n else None
        m5, m20, m60 = ma(5), ma(20), ma(60)
        if m5 and m20 and m60:
            arr = "정배열(상승추세)" if m5 > m20 > m60 else ("역배열(하락추세)" if m5 < m20 < m60 else "혼조")
            out.append(f"- 이동평균: MA5 {m5:,.2f} / MA20 {m20:,.2f} / MA60 {m60:,.2f} → {arr}")
        return "\n".join(out) if len(out) > 1 else ""
    except Exception:  # noqa: BLE001
        return ""


def _run_agent_python(code: str) -> str:
    """LLM 에이전트가 생성한 파이썬 코드를 로컬 환경에서 실행하여 stdout 결과를 반환."""
    import sys
    import subprocess
    py_bin = sys.executable or "python3"
    try:
        res = subprocess.run(
            [py_bin, "-c", code],
            capture_output=True, text=True, timeout=10.0
        )
        if res.returncode == 0:
            return res.stdout.strip()
        return f"에러 발생 (코드 {res.returncode}): {res.stderr.strip()}"
    except Exception as e:  # noqa: BLE001
        return f"실행 중 예외 발생: {str(e)}"


_FETCH_CACHE: dict = {}   # url -> (text, ts)


def _fetch_url_text(url: str, max_chars: int = 2500) -> str:
    """에이전트 FETCH 도구 — 기사/웹페이지 URL의 본문 텍스트를 추출해 반환.
    뉴스 제목만으로 부족할 때 원문을 읽어 더 자세한 사실을 수집한다. 10분 캐시."""
    import html as _html
    url = (url or "").strip().strip('\'"')
    if not url.startswith(("http://", "https://")):
        return "유효한 URL이 아닙니다."
    c = _FETCH_CACHE.get(url)
    if c and (time.time() - c[1]) < 600.0:
        return c[0]
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                                             "Chrome/124.0 Safari/537.36"})
        ctype = r.headers.get("content-type", "")
        raw = r.content
        # 인코딩 추정(한국 언론사 EUC-KR 다수)
        enc = "utf-8"
        m = re.search(rb'charset=["\']?([\w-]+)', raw[:2048], re.I)
        if m:
            enc = m.group(1).decode("ascii", "ignore").lower()
        if enc in ("ms949", "ks_c_5601-1987"):
            enc = "euc-kr"
        try:
            page = raw.decode(enc, errors="replace")
        except (LookupError, Exception):  # noqa: BLE001
            page = raw.decode("utf-8", errors="replace")
        if "html" not in ctype and "<html" not in page[:1000].lower():
            txt = page
        else:
            # script/style 제거 → 태그 제거 → 공백 정리
            page = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", page)
            page = re.sub(r"(?is)<br\s*/?>", "\n", page)
            page = re.sub(r"(?is)</(p|div|h[1-6]|li|tr)>", "\n", page)
            txt = re.sub(r"(?s)<[^>]+>", " ", page)
            txt = _html.unescape(txt)
        lines = [ln.strip() for ln in txt.splitlines()]
        txt = "\n".join(ln for ln in lines if len(ln) > 1)
        txt = re.sub(r"[ \t]{2,}", " ", txt).strip()
        if len(txt) > max_chars:
            txt = txt[:max_chars] + " …(이하 생략)"
        if not txt:
            txt = "본문을 추출하지 못했습니다."
        _FETCH_CACHE[url] = (txt, time.time())
        return txt
    except Exception as e:  # noqa: BLE001
        return f"페이지를 불러오지 못했습니다: {str(e)[:120]}"


def _llm_complete(sys_msg: str, user_msg: str, max_tokens=60) -> str:
    """동기식 단발성 LLM API 호출. 1차 라우팅 판단용으로 가볍게 사용."""
    import json
    import urllib.request
    try:
        model_id = _pick_llm_model_ex(_llm_chat_models_with_state())
        if not model_id:
            return "DIRECT"
        prof = _llm_model_profile(model_id)
        _messages = [{"role": "system", "content": sys_msg + prof["sys_suffix"]},
                     {"role": "user", "content": user_msg}]
        payload = {
            "model": model_id,
            "messages": _messages,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "stream": False
        }
        req = urllib.request.Request(
            "http://127.0.0.1:1234/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"].get("content", "").strip()
    except Exception:  # noqa: BLE001
        return "DIRECT"


# ── 결정적 능동 리서치 에이전트 헬퍼 (작업: 로컬 LLM 외부정보 수집) ──
# 진단 결과: 4B급 로컬 모델은 native tool_calls 도 자유텍스트 라우팅도 무시하고
# 기억(환각)으로 답한다. 따라서 "모델이 도구를 고르게" 하지 않고, 질문 키워드에 따라
# 시스템이 먼저 외부정보를 능동 수집한 뒤 모델에 "수집 데이터로만 답하라"고 강제한다.
def _agent_entity(scope: str, ident: str, excd: str) -> tuple[str, str]:
    """(검색용 표시명, 한국 6자리 종목코드 or '')."""
    code6 = ident if (ident.isdigit() and len(ident) == 6) else ""
    name = ""
    try:
        if scope in ("stock", "etf") and code6:
            name = _ai_stock_name(code6)
        elif scope == "ov":
            name = ident                      # 심볼(질문에 한글 종목명이 보통 포함됨)
        elif scope == "macro":
            name = "한국·글로벌 경제"
        elif scope == "index":
            name = _kis_index(ident or "0001").get("name", "") or "코스피"
    except Exception:  # noqa: BLE001
        pass
    return name, code6


def _agent_search_query(name: str, q: str) -> str:
    q2 = re.sub(r"[?？!.…·]", " ", q)
    q2 = re.sub(r"\s+", " ", q2).strip()
    if name and name not in q2:
        q2 = f"{name} {q2}"
    return q2[:60]


# ── 결정적 의도 게이트(Intent Gate) — 수집 전에 '무엇이 진짜 필요한지'를 정교하게 분류 ──
# 목적: "안녕" 같은 잡담에 반사적으로 뉴스 검색하지 않고, 화면 질문은 화면만, 최신정보 질문만 검색.
# 로컬(9B/12B급)·Gemini 공통 1차 라우팅. 도구 호출을 모델에 맡기지 않고(신뢰성↓) 시스템이 확정한다.
_KW_NEWS = ("뉴스", "속보", "근황", "이슈", "논란", "오늘", "어제", "최근", "요즘", "지금", "현재",
            "최신", "무슨 일", "무슨일", "발표", "업데이트", "호재", "악재", "왜", "이유", "급등",
            "급락", "터졌", "사건", "사고", "루머", "소문", "공시", "리콜", "제재", "과징금", "소송",
            "전망", "실적발표")
_KW_DEEP = ("왜", "이유", "사유", "배경", "무슨", "어떤", "상세", "자세", "원인", "논란", "과징금",
            "제재", "리콜", "소송", "어떻게", "영향", "파장", "의미")
_KW_OPINION = ("어때", "어떄", "어떤가", "괜찮", "좋아", "나빠", "사도", "팔아", "팔까", "매수", "매도",
               "평가", "분석", "의견", "추천", "비중", "담아도", "들어가도", "뷰", "리스크", "위험",
               "기회", "사야", "팔지")
_KW_FIN = ("매출", "영업이익", "순이익", "재무", "실적", "부채", "자산", "현금흐름", "이익률",
           "영업손실", "재무상태", "손익", "건전성", "유동", "당좌", "마진", "roe", "수익성", "성장",
           "밸류", "valuation", "per", "pbr", "eps", "배당")
_KW_GOV = ("지배구조", "주주", "지분", "최대주주", "오너", "경영권", "대주주", "지주", "오너십")
_KW_ANALYST = ("목표주가", "목표가", "애널리스트", "투자의견", "컨센서스", "적정주가", "리포트",
               "등급", "증권사", "매수", "매도", "전망")
_KW_PEERS = ("비교", "경쟁", "동종", "피어", "peer", "업계", "고평가", "저평가", "대비")
_KW_TECH = ("주가", "차트", "흐름", "추세", "모멘텀", "변동성", "기술적", "이평", "이동평균", "52주",
            "고점", "저점", "급등", "급락", "조정", "반등", "쌀까", "오를", "내릴", "박스", "지지", "저항")
_KW_CALC = ("계산", "얼마", "몇 %", "몇%", "수익률", "환산", "평균", "표준편차", "복리", "몇 배",
            "배수", "연환산", "합치면", "나누면", "곱하면")
# 잡담/인사/감사/기능문의 — 문장 '시작'을 본다(정보성 질문 앞에 인사가 붙는 경우 제외 위해 길이·정보토큰도 검사).
_RE_CHITCHAT = re.compile(
    r'^\s*(?:'
    r'안녕|안뇽|하이|hi|hello|헬로|할로|반가|방가|좋은\s*(?:아침|오후|저녁|밤)|'
    r'고마|감사|ㄳ|ㄱㅅ|thx|thank|수고|잘\s*가|잘\s*있|바이|bye|굿바이|'
    r'ㅇㅋ|오케|오키|ok|okay|넵|넹|응|웅|그래|알겠|알았|굿|good|nice|멋지|대단|'
    r'ㅋ+|ㅎ+|ㅠ+|ㅜ+|테스트|test|핑|ping|'
    r'(?:너|넌|네가|당신)?\s*누구|네?\s*이름|정체|뭐\s*하는|뭐\s*할\s*수|무엇을?\s*할\s*수|'
    r'어떤\s*걸?\s*할\s*수|기능(?:이|은|\s*뭐)|사용법|어떻게\s*(?:써|사용|쓰)|도움말|help|'
    r'what\s*can|who\s*are'
    r')', re.I)


def _classify_intent(question: str, scope: str, has_entity: bool) -> dict:
    """질문을 의도별로 분류해 '어떤 수집이 필요한가'를 확정한다(정교한 결정적 게이트).
    chitchat=True 면 일절 수집하지 않고 대화형으로 바로 답한다."""
    q = (question or "").strip()
    # 정보성 토큰(숫자·금융/뉴스/기술 키워드)이 있으면 인사로 시작해도 잡담이 아님
    info_bearing = bool(re.search(r"\d", q)) or any(
        w in q for w in (_KW_NEWS + _KW_OPINION + _KW_FIN + _KW_GOV + _KW_ANALYST
                         + _KW_TECH + _KW_CALC + _KW_PEERS))
    chitchat = (not info_bearing) and len(q) <= 20 and bool(_RE_CHITCHAT.match(q))
    if chitchat:
        return {"chitchat": True, "news": False, "deep": False, "governance": False,
                "financials": False, "analyst": False, "peers": False, "technical": False,
                "calc": False}
    has_fresh = any(w in q for w in _KW_NEWS)
    has_op = any(w in q for w in _KW_OPINION)
    # 뉴스 검색: 명시적 최신키워드 OR (종목이 있고 평가성 질문). 단순 화면설명·조회엔 검색 안 함.
    news = bool(has_fresh or (has_entity and has_op))
    if scope == "research":
        news = False   # 리포트/PDF 원문 자체가 근거 → 뉴스·기사 수집은 낭비, 끈다
    return {
        "chitchat": False,
        "news": news,
        "deep": bool(news and any(w in q for w in _KW_DEEP)),
        "governance": bool(has_entity and any(w in q for w in _KW_GOV)),
        "financials": any(w in q for w in _KW_FIN),
        "analyst": bool(has_entity and any(w in q for w in _KW_ANALYST)),
        "peers": any(w in q for w in _KW_PEERS),
        "technical": bool(has_entity and any(w in q for w in _KW_TECH)),
        "calc": any(w in q for w in _KW_CALC),
    }


def _agent_make_python(q: str, ctx: str) -> str:
    """계산형 질문에 답하기 위한 파이썬 코드만 생성(설명·마크다운 제거)."""
    sysm = ("당신은 파이썬 코드 생성기입니다. 사용자의 금융 계산 질문에 답하는 짧은 파이썬 코드만 "
            "출력하세요. 설명·인사·마크다운 금지. 반드시 print() 로 결과를 한국어 라벨과 함께 출력하세요.")
    usr = f"[참고 데이터]\n{ctx[:1500]}\n\n[질문]\n{q}\n\n파이썬 코드:"
    code = (_llm_complete(sysm, usr, max_tokens=320) or "").strip()
    if code.startswith("```"):
        ls = code.split("\n")
        if ls and ls[0].startswith("```"):
            ls = ls[1:]
        if ls and ls[-1].strip() == "```":
            ls = ls[:-1]
        code = "\n".join(ls).strip()
    if code.upper() in ("DIRECT", "") or "print" not in code:
        return ""
    return code


@app.post("/api/llm_ask")
def llm_ask():
    import json
    try:
        _body = request.get_json(silent=True) or {}
    except Exception:  # noqa: BLE001
        _body = {}
    scope = str(_body.get("scope") or "").strip()
    ident = str(_body.get("id") or "").strip()
    excd = str(_body.get("excd") or "").strip().upper()
    question = str(_body.get("question") or "").strip()[:500]
    user_context = str(_body.get("user_context") or "").strip()[:4000]
    think = bool(_body.get("think"))               # 심층 추론 토글(작업5)
    provider = str(_body.get("provider") or "local").strip().lower()   # local | gemini (작업9)
    gemini_model = str(_body.get("gemini_model") or "").strip()        # Gemini 모델 선택(작업2)
    if gemini_model not in _GEMINI_MODELS:
        gemini_model = _GEMINI_DEFAULT
    history = _body.get("history")           # 멀티턴 메모리(작업2) — [{role,text}, …]
    if not isinstance(history, list):
        history = []
    today = time.strftime("%Y-%m-%d")

    def generate():
        nonlocal gemini_model   # 검색 자동전환 시 재할당하므로 외부 스코프 변수로 바인딩
        if not question:
            yield "data: " + json.dumps({"text": "질문을 입력해 주세요."}) + "\n\n"
            return
        try:
            ctx = _ask_context(scope, ident, excd)
        except Exception:  # noqa: BLE001
            ctx = ""
        if user_context:
            ctx += f"\n\n[사용자 주입 참고 데이터 및 추가 지시사항]\n{user_context}"

        # ── 결정적 능동 리서치 에이전트 + 의도 게이트 ──
        # 로컬(9B/12B급)·Gemini 공통. 먼저 의도를 분류(_classify_intent)해 '진짜 필요한 것만' 수집한다.
        # 잡담/인사 → 수집 0, 화면 질문 → 화면만, 최신정보/평가 질문만 뉴스·검색(반사적 검색 방지).
        def _R(t):   # 추론 박스로 진행상황 스트리밍
            return "data: " + json.dumps({"text": t, "kind": "reasoning"}) + "\n\n"

        observations: list[str] = []
        name, code6 = _agent_entity(scope, ident, excd)
        intent = _classify_intent(question, scope, bool(ident or code6))

        if intent["chitchat"]:
            yield _R("💬 일반 대화로 판단 — 데이터 수집 없이 바로 답합니다.\n")
        else:
            # (1) 실시간 뉴스 검색 — 최신정보/평가 의도일 때만
            if intent["news"]:
                kw = _agent_search_query(name, question)
                yield _R(f"🔍 실시간 정보 검색: '{kw}' …\n")
                articles = []
                try:
                    nl = _dedup_news(_naver_news(kw, 10))
                except Exception:  # noqa: BLE001
                    nl = []
                if (not nl) and name and name not in kw:
                    try:
                        nl = _dedup_news(_naver_news(name, 10))
                    except Exception:  # noqa: BLE001
                        nl = []
                if nl:
                    rows = []
                    for n in nl:
                        lk = n.get("link", "")
                        rows.append(f"- [{n.get('when','')}] {n.get('title','')} — {n.get('desc','')}"
                                    + (f"\n  URL: {lk}" if lk else ""))
                        if lk:
                            articles.append((n.get("title", ""), lk))
                    observations.append(f"[실시간 뉴스 검색 '{kw}']\n" + "\n".join(rows))
                    yield _R(f"✅ 뉴스 {len(rows)}건 수집.\n")
                else:
                    yield _R("⚠️ 관련 뉴스를 찾지 못했습니다.\n")

                # (2) 깊은 사실(이유·배경)이 필요하면 상위 기사 본문까지 읽기
                if intent["deep"] and articles:
                    for title, lk in articles[:3]:
                        yield _R(f"📄 기사 본문 분석: {title[:30]}… \n")
                        observations.append(f"[기사 본문 — {title}]\n{_fetch_url_text(lk, 3000)}")
                    yield _R("✅ 본문 분석 완료.\n")

            # (3) 지배구조/주주 → FSC/DART (한국 종목)
            if intent["governance"] and code6:
                yield _R(f"🏛️ 지배구조·주주 현황 조회 ({code6}) …\n")
                observations.append(f"[지배구조·주주 현황 {code6}]\n{_get_governance_shareholders(code6)}")
                yield _R("✅ 지배구조 수집 완료.\n")

            # (4) 재무 → 한국=DART 재무제표 / 해외=Finnhub 펀더멘털
            if intent["financials"]:
                if code6:
                    yield _R(f"📊 DART 재무제표 조회 ({code6}) …\n")
                    observations.append(f"[DART 재무제표 {code6}]\n{_get_financial_statements(code6)}")
                    yield _R("✅ 재무제표 수집 완료.\n")
                elif scope == "ov" and ident:
                    yield _R(f"📊 해외 펀더멘털 조회 ({ident}) …\n")
                    observations.append(f"[해외 펀더멘털 {ident}]\n{_get_overseas_financials(ident)}")
                    yield _R("✅ 펀더멘털 수집 완료.\n")

            # (5) 애널리스트 의견/목표주가
            if intent["analyst"] and scope in ("stock", "etf", "ov") and ident:
                yield _R("🎯 애널리스트 컨센서스 조회 …\n")
                av = _get_analyst_view(scope, ident)
                if av and "찾지 못" not in av:
                    observations.append(av)
                    yield _R("✅ 애널리스트 의견 수집 완료.\n")

            # (6) 밸류에이션/동종업계 비교(미국 FMP peers)
            if intent["peers"] and scope == "ov" and ident:
                vp = _get_valuation_peers(scope, ident)
                if vp:
                    yield _R("⚖️ 동종업계 비교 수집 …\n")
                    observations.append(vp)

            # (7) 가격·기술적 스냅샷(모멘텀·52주위치·MA배열·변동성)
            if intent["technical"] and ident:
                tech = _get_price_technicals(scope, ident, excd)
                if tech:
                    yield _R("📈 가격·기술적 스냅샷 수집 …\n")
                    observations.append(tech)

            # (8) 계산/통계 → 파이썬 생성·실행
            if intent["calc"]:
                yield _R("💻 계산용 파이썬 생성·실행 …\n")
                code = _agent_make_python(question, ctx)
                if code:
                    res = _run_agent_python(code)
                    observations.append(f"[파이썬 계산]\n코드:\n{code}\n결과:\n{res}")
                    yield _R(f"✅ 계산 결과: {res[:80]}\n")
                else:
                    yield _R("⚠️ 계산 코드 생성 생략.\n")

        tool_used = bool(observations)
        if observations:
            ctx += "\n\n[에이전트가 능동 수집한 실시간 외부 근거]\n" + "\n\n".join(observations)

        # ── 합성 프롬프트(의도별) — 9B/12B급 모델 가정: 풍부한 근거를 신뢰하고 구조적으로 합성 ──
        if intent["chitchat"]:
            # 잡담/인사/기능문의 → 가벼운 대화. 면책문구·데이터그라운딩 불필요.
            sys_msg = (
                "당신은 'K-Market Dashboard'의 친절한 AI 비서입니다. 사용자가 인사·가벼운 대화 또는 기능 "
                "문의를 했습니다. 1~3문장으로 자연스럽고 친근하게 한국어로 답하세요. 자기소개나 기능 안내가 "
                "적절하면 '종목·ETF·시장·재무·뉴스 등 화면에 대해 무엇이든 물어보세요'라고 짧게 덧붙이세요. "
                "데이터 인용·면책문구·과한 형식은 쓰지 마세요.")
            user_msg = question
        elif tool_used:
            sys_msg = (
                f"당신은 한국어로 답하는 금융 AI 어시스턴트입니다. 오늘은 {today}입니다. 아래에는 "
                "방금 인터넷·DART·FSC 등에서 실시간으로 수집한 [에이전트가 능동 수집한 실시간 외부 근거]가 "
                "주입되어 있습니다. ★ 반드시 이 수집 데이터와 [현재 화면 데이터]만을 근거로 답하세요. "
                "⚠️ 당신이 사전 학습한 지식(과거 인물·지분율·실적·사건)은 1년 이상 낡았고 종종 틀리므로 "
                "절대 사용하지 말고, 모든 사실(주주·지분율·수치·사유·날짜)은 오직 주입된 데이터에서만 인용하세요. "
                "수집 데이터에 답이 있으면 그것을 근거로 구체적으로 설명하고, 데이터에 없는 부분만 "
                "'수집된 자료에는 해당 정보가 없습니다'라고 명시하세요. 수치·뉴스·이름을 지어내지 마세요. "
                "간결하고 명확하게 한국어로 답하고, 마지막 줄에 '※ AI 답변이며 투자조언이 아닙니다.'를 덧붙이세요.")
            user_msg = f"[현재 화면 데이터]\n{ctx or '(데이터 없음)'}\n\n[질문]\n{question}"
        else:
            sys_msg = (
                f"당신은 한국어로 답하는 금융 AI 어시스턴트입니다. 오늘은 {today}입니다. 사용자는 아래 "
                "[현재 화면 데이터] 및 [사용자 주입 참고 데이터 및 추가 지시사항]을 보고 있습니다. 반드시 이 데이터와 질문에 근거해서만 답하세요. "
                "⚠️ 당신이 사전 학습한 지식(과거 가격·실적·인물·사건)은 1년 이상 낡았을 수 있으니 "
                "신뢰하지 말고, 최신 사실은 오직 제공된 데이터에서만 인용하세요. 데이터에 답이 없으면 "
                "'제공된 화면 정보로는 알 수 없습니다'라고 솔직히 말하고 무엇을 더 보면 되는지 한 줄로 "
                "안내하세요. 수치·뉴스를 지어내지 말고, 간결하고 명확하게 한국어로 답하세요. "
                "마지막 줄에 '※ AI 답변이며 투자조언이 아닙니다.'를 덧붙이세요.")
            user_msg = f"[현재 화면 데이터]\n{ctx or '(데이터 없음)'}\n\n[질문]\n{question}"

        # ── 검색 필요 시 검색 가능한 모델로 자동 전환 (작업5) ──
        # 로컬 모델은 웹 브라우징을 못 한다. 결정적 에이전트가 외부근거를 전혀 못 모았는데(tool_used=False)
        # 질문이 실시간 웹 검색을 요하면, Google Search 그라운딩이 되는 Gemini 로 자동 전환한다(키 있을 때만).
        eff_provider = provider
        gkey = bool(os.environ.get("GEMINI_KEY", ""))
        needs_search = bool(intent["news"])   # 의도 게이트와 동일 기준(반사적 검색 방지)
        if eff_provider == "local" and gkey and needs_search and not tool_used and not intent["chitchat"]:
            eff_provider = "gemini"
            gemini_model = "gemini-2.5-flash"   # 무료 티어에서 검색 동작하는 모델로 전환
            yield _R("🔎 실시간 웹 검색이 필요해 검색 가능한 모델(Gemini 2.5 Flash)로 전환했습니다.\n")

        if eff_provider == "gemini":
            # 무료 티어 기능 게이팅: Google Search 그라운딩은 2.5 계열(_GEMINI_SEARCH_OK)에서만 켠다.
            # 또한 작은 무료 검색 한도(2.5: 500~1,500회/월)를 아끼려 '검색이 실제 필요한 질문'일 때만 켠다.
            can_search = gemini_model in _GEMINI_SEARCH_OK
            use_search = bool(needs_search and can_search)
            # 작업4a — 검색이 필요한데 현재 모델이 검색 불가(3.x)면 2.5 계열 전환을 안내(오류 대신 안내).
            if needs_search and not can_search:
                yield _R("ℹ️ 무료 티어에서 실시간 웹 검색은 'Gemini 2.5 Flash / 2.5 Flash-Lite'에서만 "
                         "동작합니다(3.x 그라운딩은 유료 빌링 필요). 검색이 필요하면 상단에서 2.5 계열 모델로 "
                         "바꿔 주세요. 지금은 수집된 뉴스·데이터로만 답합니다.\n")
            # 클라우드 모델 활용: 심층·구조적 분석 프롬프트(잡담엔 제외) + (조건부)검색 + 멀티턴 메모리.
            g_sys = sys_msg + ("" if intent["chitchat"] else _GEMINI_SYS_ADDENDUM)
            g_tokens = 256 if intent["chitchat"] else 4096
            # ── 리포트 뷰어(scope=research, ident="cat:nid")면 PDF 원본을 Gemini 에 직접 첨부해 직독 ──
            g_pdf = None; g_user = user_msg
            if scope == "research" and ":" in ident and not intent["chitchat"]:
                _c, _, _n = ident.partition(":")
                if _c in _RESEARCH_CATS and (_c in ("bok", "bok_mp") or _n.isdigit()):
                    try:
                        g_pdf = _research_pdf_bytes(_c, _n)
                    except Exception:  # noqa: BLE001
                        g_pdf = None
                    if g_pdf:
                        yield _R(f"📑 PDF 원문({len(g_pdf)//1024}KB)을 Gemini 에 직접 전달해 분석합니다…\n")
                        g_user = ("첨부된 PDF가 이 증권사 리포트의 원문입니다. PDF 내용(본문·표·차트, 스캔 페이지 포함)을 "
                                  "최우선 근거로 삼아 답하세요.\n\n" + user_msg)
            yield ("data: " + json.dumps({"meta": {"provider": "gemini", "model": gemini_model,
                   "name": _GEMINI_MODELS[gemini_model]}}) + "\n\n")
            if not intent["chitchat"]:
                _mode = "클라우드·웹검색" if use_search else "클라우드"
                yield _R(f"🌩️ {_GEMINI_MODELS[gemini_model]}({_mode})로 심층 분석 중…\n")
            yield from _gemini_stream(g_sys, g_user, model=gemini_model, max_tokens=g_tokens,
                                      use_search=use_search, history=history, pdf_bytes=g_pdf)
        else:
            try:
                _mid = _pick_llm_model_ex(_llm_chat_models_with_state())
            except Exception:  # noqa: BLE001
                _mid = None
            yield ("data: " + json.dumps({"meta": {"provider": "local", "model": _mid or "",
                   "name": _short_model_name(_mid)}}) + "\n\n")
            # 9B/12B 등 상위 모델 가정 → 근거가 있으면 충분히 활용(2000), 잡담은 짧게(280).
            l_tokens = 280 if intent["chitchat"] else 2000
            yield from _llm_stream(sys_msg, user_msg, max_tokens=l_tokens, think=think, model_id=_mid)

    return Response(generate(), mimetype="text/event-stream")


# ── Gemini 모델 카탈로그 — 무료 티어 사용 가능 모델만(첨부 Gemini_API_Models.md 기준) ──
# ⚠️ 무료 티어 '지원 안 함' 모델(예: Gemini 3.1 Pro Preview)은 키가 무료면 즉시 오류 → 제외.
# 아래는 모두 무료 티어 '지원(무료)' 모델. 합성용 기본은 가장 똑똑+빠른 3.5 Flash.
_GEMINI_MODELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash",            # 무료 ✓ — 기본, 가장 지능적+빠름
    "gemini-2.5-flash": "Gemini 2.5 Flash",            # 무료 ✓ — 웹검색(그라운딩) 무료 동작
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite",  # 무료 ✓ — 최저가+웹검색 가능
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite",  # 무료 ✓ — 초고속·초저가
}
_GEMINI_DEFAULT = "gemini-3.5-flash"
# Google Search 그라운딩이 '빌링 미연결 무료 키'에서도 실제 동작하는 모델 = 2.5 계열만.
# (3.x 그라운딩은 무료 한도가 있어도 billing-enabled 프로젝트를 요구 → 미연결 시 429. trap #32)
# 따라서 검색 기능은 이 집합의 모델에서만 켠다(나머지는 오류 방지 위해 끈다).
_GEMINI_SEARCH_OK = {"gemini-2.5-flash", "gemini-2.5-flash-lite"}
# 작업3 — 클라우드 모델 활용 극대화. 로컬과 동일한 1차 수집 후, 더 똑똑한 Gemini 에는 한 단계 깊은
# 구조적 분석을 요구한다(단순 요약 금지). 위의 데이터-그라운딩 규칙은 그대로 유지된다.
_GEMINI_SYS_ADDENDUM = (
    " 당신은 고성능 클라우드 모델입니다 — 단순 요약을 넘어 한 단계 깊은 분석을 제공하세요. "
    "주입된 근거가 충분하면 ①핵심 결론(1~2문장) ②근거(데이터·뉴스 인용) ③리스크·반론 ④바로 확인할 점 "
    "순서로 간결한 마크다운(굵게·불릿)으로 구조화하세요. 다만 근거가 빈약하면 억지로 늘리지 말고 한계를 "
    "솔직히 밝히세요. 이전 대화 맥락이 있으면 그 흐름을 이어서 답하세요. 위의 데이터-그라운딩 규칙은 그대로 지키세요.")
# 실시간 웹 검색을 요하는 키워드(작업5) — 결정적 수집이 비면 검색가능 모델로 전환 트리거
_SEARCH_KW = ("최근", "오늘", "어제", "지금", "현재", "뉴스", "속보", "근황", "이슈", "논란",
              "발표", "업데이트", "최신", "무슨 일", "무슨일", "왜", "호재", "악재", "전망", "실적발표")


def _short_model_name(mid: str | None) -> str:
    """로컬 모델 id → 짧은 표시명(작업6). 예: 'qwen/qwen3-4b-2507' → 'qwen3-4b-2507'."""
    if not mid:
        return "로컬 LLM"
    return str(mid).split("/")[-1][:24]


def _llm_stream(sys_msg: str, user_msg: str, max_tokens=None, think=False, model_id=None):
    """공용 LLM SSE 제너레이터 (작업4) — 모델 선택(로드 우선)·프로파일·추론 prefill·스트림·폴백.
    think=True(작업5 '심층 추론'): 추론형 모델의 thinking 억제 prefill 을 생략하고(스스로 사고),
    instruct 모델엔 단계적 사고 지시를 더해 더 깊이 추론하게 한다.
    'data: {...}\\n\\n' 라인을 yield 한다. 커미터리/질문 등 모든 LLM 기능이 재사용."""
    import json
    import urllib.request
    try:
        try:
            if model_id is None:
                model_id = _pick_llm_model_ex(_llm_chat_models_with_state())
        except Exception:  # noqa: BLE001
            yield ("data: " + json.dumps({"text":
                   "[시스템 알림] 로컬 AI 서버(LM Studio · 포트 1234)에 연결할 수 없습니다.\n"
                   "LM Studio 를 실행하고 'Developer ▸ Local Server'를 켠 뒤 다시 시도해 주세요."}) + "\n\n")
            return
        if not model_id:
            yield ("data: " + json.dumps({"text":
                   "[시스템 알림] LM Studio 에 로드된 모델이 없습니다. "
                   "모델(예: qwen3-4b-2507)을 1개 로드한 뒤 다시 시도해 주세요."}) + "\n\n")
            return
        prof = _llm_model_profile(model_id)
        _max_tok = int(max_tokens) if max_tokens else prof["max_tokens"]
        _sys = sys_msg + prof["sys_suffix"]
        if think and prof.get("kind") != "reasoning":
            _sys += (" \n[심층 추론 모드] 결론 전에 핵심 근거를 단계적으로 짚어가며 신중히 추론한 뒤, "
                     "마지막에 명확한 결론을 제시하세요.")
        _messages = [{"role": "system", "content": _sys},
                     {"role": "user", "content": user_msg}]
        # 추론형 모델: 평소엔 thinking 억제 prefill 로 빠르게. '심층 추론' 켜면 prefill 생략→스스로 사고.
        if prof.get("prefill") and not think:
            _messages.append({"role": "assistant", "content": prof["prefill"]})
        if think and not prof.get("prefill") and prof.get("kind") != "reasoning":
            _max_tok = max(_max_tok, 1600)       # 사고 여유분
        payload = {"model": model_id, "messages": _messages, "temperature": prof["temperature"],
                   "max_tokens": _max_tok, "stream": True}
        req = urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        _got_content = False
        _got_reason = False
        with urllib.request.urlopen(req, timeout=300.0) as response:
            for line in response:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    ds = line[6:]
                    if ds == "[DONE]":
                        break
                    try:
                        delta = json.loads(ds)["choices"][0].get("delta", {})
                        chunk = delta.get("content", "")
                        reasoning = delta.get("reasoning_content", "")
                        if chunk:
                            if not _got_content:
                                chunk = chunk.lstrip("\n\r ")
                                if chunk.startswith("</think>"):
                                    chunk = chunk[len("</think>"):].lstrip("\n\r ")
                                if not chunk:
                                    continue
                            _got_content = True
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                        elif reasoning:
                            _got_reason = True
                            yield f"data: {json.dumps({'text': reasoning, 'kind': 'reasoning'})}\n\n"
                    except Exception:  # noqa: BLE001
                        pass
        if (not _got_content) and _got_reason and prof.get("kind") == "reasoning":
            yield ("data: " + json.dumps({"text":
                   "\n\n💡 이 모델은 추론에만 토큰을 모두 사용해 본문 답변을 생략했습니다. "
                   "더 빠르고 명확한 해설을 원하시면 상단 'AI' 메뉴에서 Instruct 모델"
                   "(예: qwen3-4b-2507 · gemma)을 선택해 주세요."}) + "\n\n")
    except Exception as e:  # noqa: BLE001
        es = str(e)
        if "Connection refused" in es or "urlopen error" in es:
            msg = "로컬 AI 서버(LM Studio · 포트 1234)에 연결할 수 없습니다. Local Server 를 켜 주세요."
        elif "timed out" in es or "timeout" in es.lower():
            msg = "로컬 AI 응답이 시간 초과되었습니다. LM Studio 에서 모델을 미리 로드해 주세요."
        else:
            msg = f"로컬 AI 연동 실패: {es}"
        yield f"data: {json.dumps({'text': f'[시스템 알림] {msg}'})}\n\n"


def _gemini_stream(sys_msg: str, user_msg: str, max_tokens=1400, model=None, use_search=True,
                   history=None, pdf_bytes=None):
    """Gemini(클라우드) SSE 스트리밍 — 질문당 1회 호출(작업9). 도구 수집은 결정적 에이전트가
    이미 끝낸 ctx 를 받아 합성한다. Google Search 그라운딩(use_search)을 켜면 모델이 스스로
    최신 사실을 보강한다. ⚠️ 그라운딩은 빌링이 연결된 프로젝트에서만 무료 할당량(월 5,000건)이
    열린다 — 빌링 미연결 키는 google_search 툴이 붙은 요청에서만 즉시 429(quota=0)를 받는다
    (changes_52 에서 실측: 동일 키로 그라운딩 없는 일반 호출은 200). 그래서 그라운딩 시도가
    429면 검색 없이 1회 자동 재시도 — 빌링 미연결 환경에서도 Gemini 답변 자체는 끊기지 않는다."""
    import json
    import urllib.request
    import urllib.error
    key = os.environ.get("GEMINI_KEY", "")
    if not key:
        yield ("data: " + json.dumps({"text": "[시스템 알림] Gemini API 키가 없습니다 "
               "(api_documents/API.env 의 GEMINI_KEY)."}) + "\n\n")
        return
    model = model or os.environ.get("KMKT_GEMINI_MODEL", _GEMINI_DEFAULT)
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
           f":streamGenerateContent?alt=sse&key={key}")
    base_sys_msg = sys_msg

    def _build_body(with_search: bool) -> dict:
        sm = base_sys_msg
        if with_search:
            # 주입 데이터만 쓰라는 강한 그라운딩과 Google 검색이 모순되지 않도록, 검색으로
            # '오늘 시점 최신 사실'을 직접 보강하도록 프롬프트를 보정한다.
            sm = (sm + " 또한 제공된 데이터로 부족하면 Google 검색 도구로 오늘 기준 최신 "
                  "사실(주가·뉴스·실적·이벤트)을 직접 찾아 보강하세요. 단, 검색 결과나 주입 데이터처럼 "
                  "실제 확인 가능한 최신 출처만 인용하고, 사전 학습된 추측은 쓰지 마세요.")
        # 작업2 — 멀티턴 컨텍스트 메모리(Gemini). 직전 대화(history)를 contents 앞에 붙여
        # 같은 채팅창의 흐름을 기억하게 한다. 토큰 보호: 각 발화 1500자, 직전 12발화까지만.
        contents = []
        for h in (history or [])[-12:]:
            try:
                role = "model" if str(h.get("role")) == "model" else "user"
                txt = str(h.get("text") or "")[:1500]
            except Exception:  # noqa: BLE001
                continue
            if txt:
                contents.append({"role": role, "parts": [{"text": txt}]})
        # 현재 질문 파트 — PDF 원본이 있으면 멀티모달 inline_data 로 첨부(Gemini 가 PDF 직독·OCR).
        _uparts = []
        if pdf_bytes:
            import base64 as _b64
            _uparts.append({"inline_data": {"mime_type": "application/pdf",
                            "data": _b64.b64encode(pdf_bytes).decode("ascii")}})
        _uparts.append({"text": user_msg})
        contents.append({"role": "user", "parts": _uparts})
        gen = {"maxOutputTokens": int(max_tokens), "temperature": 0.3}
        if with_search:
            # 그라운딩 시 2.5 모델이 'tool_code/thought' 체인오브쏘트를 답변 텍스트로 흘리는 문제 →
            # includeThoughts 로 사고과정을 별도 thought 파트로 분리해 답변을 깨끗하게 유지(아래서 reasoning 처리).
            # thinkingBudget 로 사고 토큰을 제한 → 이미 결정적 수집을 끝낸 뒤이므로 과도한 사고를 막아
            # 답변 지연/토큰 소진을 방지하고 최종 답변이 확실히 도착하게 한다.
            gen["thinkingConfig"] = {"includeThoughts": True, "thinkingBudget": 1024}
            b_tools = [{"google_search": {}}]
        else:
            b_tools = None
        b = {"system_instruction": {"parts": [{"text": sm}]},
             "contents": contents, "generationConfig": gen}
        if b_tools:
            b["tools"] = b_tools
        return b

    def _stream(with_search: bool):
        body = _build_body(with_search)
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120.0) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                ds = line[5:].strip()
                if not ds or ds == "[DONE]":
                    continue
                try:
                    j = json.loads(ds)
                    for cand in j.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            t = part.get("text", "")
                            if not t:
                                continue       # executableCode/functionCall 등 비텍스트 파트 무시
                            if part.get("thought"):
                                # 사고과정 → 답변이 아니라 dim '생각 과정' 박스로
                                yield "data: " + json.dumps({"text": t, "kind": "reasoning"}) + "\n\n"
                            else:
                                yield "data: " + json.dumps({"text": t}) + "\n\n"
                except Exception:  # noqa: BLE001
                    pass

    try:
        try:
            yield from _stream(use_search)
        except urllib.error.HTTPError as e:
            if e.code == 429 and use_search:
                # 그라운딩 전용 quota=0(빌링 미연결) 가능성 — 검색 없이 1회 재시도.
                yield from _stream(False)
            else:
                raise
    except urllib.error.HTTPError as e:  # noqa: BLE001
        try:
            detail = e.read().decode("utf-8", "ignore")[:200]
        except Exception:  # noqa: BLE001
            detail = ""
        if e.code == 429:
            msg = ("Gemini 호출 한도를 초과했습니다. 잠시 후 다시 시도하거나 "
                   "상단 ‘로컬’ 모델로 전환해 주세요.")
        elif e.code in (400, 403):
            msg = f"Gemini 인증/요청 오류({e.code}). API 키를 확인하거나 ‘로컬’로 전환해 주세요. {detail}"
        else:
            msg = f"Gemini 오류({e.code}). ‘로컬’로 전환해 주세요."
        yield "data: " + json.dumps({"text": "[시스템 알림] " + msg}) + "\n\n"
    except Exception as e:  # noqa: BLE001
        yield ("data: " + json.dumps({"text": f"[시스템 알림] Gemini 연동 실패: "
               f"{str(e)[:120]}. ‘로컬’로 전환해 주세요."}) + "\n\n")


@app.post("/api/llm_commentary")
def llm_commentary():
    # ⚠️ request.json 은 반드시 제너레이터 "밖"(여기, request context 가 살아있을 때)에서
    # 읽어야 한다. 제너레이터는 응답 스트리밍 시점(=request context 종료 후)에 지연 실행되어
    # 그 안에서 request 에 접근하면 RuntimeError(Working outside of request context) 가 난다.
    import json
    import urllib.request

    try:
        _body = request.get_json(silent=True) or {}
    except Exception:  # noqa: BLE001
        _body = {}
    code = str(_body.get("code") or "").strip()
    prompt = _body.get("prompt", "")
    mode = str(_body.get("mode") or "").strip()   # ""=종목 코멘트, "backtest"/"macro"=초보자용 해설(작업4)
    ov_excd = str(_body.get("ov_excd") or "").strip().upper()   # 해외 코멘터리(작업3)
    ov_symb = str(_body.get("ov_symb") or "").strip().upper()
    # 로컬/Gemini 선택(AI 팝오버) — provider=gemini 면 클라우드로 합성. gsys=사용자 시스템 프롬프트.
    provider = str(_body.get("provider") or "local").strip().lower()
    gmodel = str(_body.get("gemini_model") or "").strip()
    if gmodel not in _GEMINI_MODELS:
        gmodel = _GEMINI_DEFAULT
    gsys = str(_body.get("gsys") or "").strip()[:2000]

    def generate():
        try:
            # 메시지 구성: code 가 오면 실데이터 그라운딩, 아니면 legacy prompt.
            if ov_symb:
                # ── 해외 종목 코멘터리 (작업3) — 국내와 동일한 데이터-그라운딩 ──
                _nm, sheet = _build_ov_ai_context(ov_excd, ov_symb)
                if sheet:
                    sys_msg = (
                        "당신은 글로벌 주식을 다루는 보수적인 퀀트 애널리스트입니다. 아래 [데이터]의 "
                        "수치와 뉴스만 근거로 분석하세요. ⚠️ 오늘 기준 제공된 실시간 데이터만 신뢰하고, "
                        "당신이 학습한 과거 지식(가격·실적·사건)은 낡았을 수 있으니 절대 사용하지 마세요. "
                        "데이터에 없는 수치·뉴스·테마는 지어내지 마세요. '최근 뉴스'를 분석의 중심에 두고, "
                        "모멘텀·밸류에이션은 보조 배경으로만 짧게 언급하세요. 핵심만 3~4문장으로 한국어로 쓰고, "
                        "마지막 줄에 '※ 데이터 요약이며 투자조언이 아닙니다.'를 덧붙이세요.")
                    user_msg = (f"[데이터]\n{sheet}\n\n위 데이터의 '최근 뉴스'를 우선 근거로, "
                                "이 해외 종목의 최신 흐름과 주목할 이벤트·리스크를 날카롭게 코멘트해줘.")
                else:
                    sys_msg = "당신은 글로벌 퀀트 애널리스트입니다. 한국어로 간결하게 답합니다."
                    user_msg = (f"{ov_symb} 의 실시간 데이터를 불러오지 못했습니다. "
                                "데이터 부재를 언급하고 일반적 주의사항만 1~2문장으로 알려주세요.")
            elif code.isdigit() and len(code) == 6:
                _name, sheet = _build_ai_context(code)
                if sheet:
                    sys_msg = (
                        "당신은 한국의 보수적인 퀀트 애널리스트입니다. 아래 [데이터]에 있는 수치와 "
                        "뉴스만 근거로 분석합니다. 데이터에 없는 수치·뉴스·테마는 절대 지어내지 마세요. "
                        "★ 핵심 원칙: '최근 뉴스'를 분석의 중심에 두세요. 과거 주가 흐름(모멘텀·변동성)은 "
                        "뉴스를 보조하는 배경으로만 한 번 짧게 언급하고, 최근 소식이 이 종목에 주는 의미와 "
                        "주목할 이벤트·리스크를 우선 설명하세요. 뉴스가 없으면 그 사실을 명시하세요. "
                        "핵심만 3~4문장으로 한국어로 작성하고, 마지막 줄에 "
                        "'※ 데이터 요약이며 투자조언이 아닙니다.'를 덧붙이세요.")
                    user_msg = (f"[데이터]\n{sheet}\n\n위 데이터 중 '최근 뉴스'를 우선 근거로, "
                                "이 종목의 최신 흐름과 주목할 이벤트를 날카롭게 코멘트해줘.")
                else:
                    sys_msg = "당신은 한국의 퀀트 애널리스트입니다. 한국어로 간결하게 답합니다."
                    user_msg = (f"종목코드 {code} 의 실시간 데이터를 불러오지 못했습니다. "
                                "데이터 부재를 언급하고 일반적 주의사항만 1~2문장으로 알려주세요.")
            elif prompt and mode == "backtest":
                # 백테스터 결과 해설 — 금융 비전문가도 이해하도록 쉬운 말로 (작업4)
                sys_msg = (
                    "당신은 친절한 금융 교육 전문가입니다. 아래 [백테스트 결과] 수치만 근거로, "
                    "투자 전문지식이 없는 일반 투자자도 이해할 수 있게 한국어로 설명합니다. "
                    "전문용어(샤프지수·MDD·손익비 등)는 한 줄로 쉽게 풀어 말해주세요. "
                    "구성: ①이 전략이 무엇을 했는지 한 문장 → ②결과가 좋은지 나쁜지와 그 이유 "
                    "→ ③주의할 점(과최적화·과거≠미래). 수치를 지어내지 말고, 5~7문장으로. "
                    "마지막 줄에 '※ 과거 데이터 기반 모의실험이며 투자조언이 아닙니다.'를 덧붙이세요.")
                user_msg = f"[백테스트 결과]\n{prompt}\n\n위 결과를 초보 투자자에게 쉽게 해설해줘."
            elif prompt and mode == "macro":
                # ECOS 거시지표 해설 — 비전문가용 (작업4)
                sys_msg = (
                    "당신은 친절한 경제 해설가입니다. 아래 [경제지표] 수치만 근거로, 경제 지식이 "
                    "부족한 일반 투자자도 이해할 수 있게 한국어로 설명합니다. 기준금리·장단기 금리차·"
                    "물가(CPI)·환율이 각각 무엇을 뜻하고 주식시장에 어떤 영향을 주는지 쉬운 말로 풀어주세요. "
                    "구성: ①현재 경제 상황 한두 문장 요약 → ②지표별로 증시에 주는 의미 → ③종합 한마디. "
                    "수치를 지어내지 말고 6~8문장으로. 마지막 줄에 '※ 데이터 해설이며 투자조언이 아닙니다.'를 덧붙이세요.")
                user_msg = f"[경제지표]\n{prompt}\n\n위 지표를 초보 투자자에게 쉽게 해설해줘."
            elif prompt:
                sys_msg = ("당신은 한국의 최고 수준의 퀀트 애널리스트입니다. 수치 데이터를 바탕으로 "
                           "전문적이고 간결한 코멘터리를 한국어로 작성합니다. 핵심만 3문장 이내로 답합니다.")
                user_msg = prompt
            else:
                yield "data: " + json.dumps({"text": "No prompt provided."}) + "\n\n"
                return

            # ── Gemini(클라우드)로 합성 선택 시 — 사용자 시스템 프롬프트(gsys)를 덧붙여 위임 ──
            if provider == "gemini":
                gsm = sys_msg + (("\n\n[사용자 추가 지시]\n" + gsys) if gsys else "")
                yield ("data: " + json.dumps({"text": f"🌩️ {_GEMINI_MODELS[gmodel]}(클라우드)로 생성 중…\n",
                       "kind": "reasoning"}) + "\n\n")
                yield from _gemini_stream(gsm, user_msg, model=gmodel, max_tokens=2048, use_search=False)
                return

            model_id = None
            try:
                _models = _llm_chat_models_with_state()
                model_id = _pick_llm_model_ex(_models)
            except Exception:
                # 모델 목록 조회 실패 = LM Studio 서버 자체가 꺼져 있는 경우.
                yield ("data: " + json.dumps({"text":
                       "[시스템 알림] 로컬 AI 서버(LM Studio · 포트 1234)에 연결할 수 없습니다.\n"
                       "LM Studio 를 실행하고 'Developer ▸ Local Server'를 켠 뒤(또는 모델 1개를 로드한 뒤) "
                       "다시 시도해 주세요."}) + "\n\n")
                return

            if not model_id:
                yield ("data: " + json.dumps({"text":
                       "[시스템 알림] LM Studio 에 로드된 모델이 없습니다. "
                       "모델(예: qwen3-4b-2507)을 1개 로드한 뒤 다시 시도해 주세요."}) + "\n\n")
                return

            # ── 모델 스펙별 프롬프트/생성 파라미터 정교 조절 (작업4) ──
            prof = _llm_model_profile(model_id)
            _sys = sys_msg + prof["sys_suffix"]
            # 토큰 예산: 사용자가 명시한 값이 있으면 존중하되, 추론형은 <think> 에 토큰을
            # 대량 쓰므로 프로파일 최소치를 보장(아니면 본문 없이 잘려 "응답 없음"이 된다).
            _req_mt = _body.get("max_tokens")
            _max_tok = int(_req_mt) if _req_mt else prof["max_tokens"]
            _messages = [
                {"role": "system", "content": _sys},
                {"role": "user", "content": user_msg},
            ]
            # 추론형: 빈 <think> 블록을 assistant 로 prefill → thinking 우회(첨부 연구·실측).
            if prof.get("prefill"):
                _messages.append({"role": "assistant", "content": prof["prefill"]})

            payload = {
                "model": model_id,
                "messages": _messages,
                "temperature": prof["temperature"],
                "max_tokens": _max_tok,
                "stream": True
            }
            
            req = urllib.request.Request(
                "http://127.0.0.1:1234/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            # ⚠️ 타임아웃: LM Studio 는 첫 요청 때 모델을 메모리로 JIT 로딩하므로
            # 첫 토큰까지 수 초~수십 초 걸린다(9B/12B 모델은 7~15초 흔함). 과거 5초
            # 타임아웃이 "모델 로딩 중" 단계에서 끊겨 코멘터리가 항상 실패했다.
            # 소켓 read 타임아웃이므로 넉넉히 잡는다(로딩+생성 모두 커버).
            _got_content = False   # 정식 본문(content)이 한 번이라도 나왔는지
            _got_reason = False    # 추론(reasoning_content)이 나왔는지
            with urllib.request.urlopen(req, timeout=300.0) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json["choices"][0].get("delta", {})
                            chunk = delta.get("content", "")
                            reasoning = delta.get("reasoning_content", "")
                            # 본문(content)은 정식 답변, reasoning_content 는 '추론'으로 구분해
                            # 보낸다 → 프론트가 추론은 흐리게(접힘) 보여 빈 화면을 막고, 본문은
                            # 또렷하게 표시한다. 추론형이 본문을 못 내도 최소한 추론은 보인다.
                            if chunk:
                                if not _got_content:
                                    # prefill 직후 첫 본문은 선행 개행/`</think>` 잔여가 붙을 수
                                    # 있어 다듬는다.
                                    chunk = chunk.lstrip("\n\r ")
                                    if chunk.startswith("</think>"):
                                        chunk = chunk[len("</think>"):].lstrip("\n\r ")
                                    if not chunk:
                                        continue
                                _got_content = True
                                yield f"data: {json.dumps({'text': chunk})}\n\n"
                            elif reasoning:
                                _got_reason = True
                                yield f"data: {json.dumps({'text': reasoning, 'kind': 'reasoning'})}\n\n"
                        except Exception:
                            pass
            # 추론형이 추론만 하고 본문을 끝내 안 낸 경우(실측: qwen3.5-9b 등) → 빈 답변
            # 대신 본문 영역에 안내를 출력해 사용자가 다음 행동을 알 수 있게 한다.
            if (not _got_content) and _got_reason and prof.get("kind") == "reasoning":
                yield ("data: " + json.dumps({"text":
                       "\n\n💡 이 모델은 추론에만 토큰을 모두 사용해 본문 답변을 생략했습니다. "
                       "더 빠르고 명확한 해설을 원하시면 상단 'AI' 메뉴에서 Instruct 모델"
                       "(예: qwen3-4b-2507 · gemma)을 선택해 주세요."}) + "\n\n")
        except Exception as e:
            es = str(e)
            if "Connection refused" in es or "urlopen error" in es:
                msg = ("로컬 AI 서버(LM Studio · 포트 1234)에 연결할 수 없습니다. "
                       "LM Studio 의 Local Server 를 켜 주세요.")
            elif "timed out" in es or "timeout" in es.lower():
                msg = ("로컬 AI 응답이 시간 초과되었습니다. 모델이 너무 크거나 "
                       "로딩이 지연되고 있습니다. LM Studio 에서 모델을 미리 로드해 주세요.")
            else:
                msg = f"로컬 AI 연동 실패: {es}"
            yield f"data: {json.dumps({'text': f'[시스템 알림] {msg}'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


# ════════════════ 로컬 LLM(LM Studio) 제어 — 상단 AI 팝오버 (작업6) ════════════════
# 상단바 "AI" 버튼 팝오버에서 로컬 LLM 환경 설치 여부·모델 정보·Load/Unload 를 제어한다.
#   · 설치 감지:  lms CLI(~/.lmstudio/bin/lms) 또는 ~/.lmstudio 디렉터리 존재
#   · 모델 정보:  /api/v0/models(서버 가동 시 state·format·quant) + `lms ls`(sizeBytes)
#   · Load/Unload: `lms load <key> -y` / `lms unload <id>`
_LMS_BIN_CANDS = [os.path.expanduser("~/.lmstudio/bin/lms")]


def _lms_bin() -> str | None:
    for p in _LMS_BIN_CANDS:
        if os.path.exists(p):
            return p
    from shutil import which
    return which("lms")


def _llm_installed() -> bool:
    """로컬 LLM 환경(LM Studio) 설치 여부."""
    return _lms_bin() is not None or os.path.isdir(os.path.expanduser("~/.lmstudio"))


def _lms_run(args: list[str], timeout: float = 20.0) -> str | None:
    b = _lms_bin()
    if not b:
        return None
    try:
        r = subprocess.run([b, *args], capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else (r.stdout or r.stderr)
    except Exception:  # noqa: BLE001
        return None


def _llm_status() -> dict:
    """팝오버용 상태: {installed, model:{id,format,quant,size,loaded}|None, models:[...]}.

    정보는 /api/v0/models(서버 가동 시)에서 state/format/quant 를,
    `lms ls`에서 전체 모델 목록 및 디스크 용량을 가져온다."""
    import json as _json
    import urllib.request
    if not _llm_installed():
        return {"installed": False}
    models_list = []
    try:                                                  # 1) 디스크 용량 기반 전체 목록 수집
        ls = _lms_run(["ls", "--json"], 15.0)
        if ls:
            for m in _json.loads(ls):
                key = m.get("modelKey") or m.get("path") or ""
                models_list.append({
                    "id": key,
                    "format": (m.get("format") or "").upper(),
                    "quant": (m.get("quantization") or {}).get("name") or "",
                    "size": round(m.get("sizeBytes", 0) / 1e9, 2) if m.get("sizeBytes") else None,
                    "max_ctx": m.get("maxContextLength"),   # `lms ls` 가 주는 모델별 최대 컨텍스트
                    "loaded": False
                })
    except Exception:  # noqa: BLE001
        pass
    try:                                                  # 2) 서버 가동 중이면 state/format/quant 반영
        with urllib.request.urlopen("http://127.0.0.1:1234/api/v0/models", timeout=4.0) as r:
            for m in _json.loads(r.read().decode("utf-8")).get("data", []):
                loaded_id = m.get("id") or ""
                for ml in models_list:
                    if loaded_id in ml["id"] or ml["id"] in loaded_id:
                        ml["loaded"] = (m.get("state") == "loaded")
                        ml["format"] = ml["format"] or (m.get("compatibility_type") or "").upper()
                        ml["quant"] = ml["quant"] or m.get("quantization") or ""
                        if m.get("max_context_length"):
                            ml["max_ctx"] = m.get("max_context_length")
                        if m.get("loaded_context_length"):
                            ml["loaded_ctx"] = m.get("loaded_context_length")
    except Exception:  # noqa: BLE001
        try:                                              # 3) 서버 응답 없을 시 ps 로 fallback
            ps = _lms_run(["ps", "--json"], 8.0)
            if ps:
                for m in _json.loads(ps):
                    loaded_id = m.get("modelKey") or m.get("identifier") or ""
                    for ml in models_list:
                        if loaded_id in ml["id"] or ml["id"] in loaded_id:
                            ml["loaded"] = True
        except Exception:  # noqa: BLE001
            pass
    # ── 모델별 컨텍스트 능동 인식 → 종류·기본 Max Tokens·추천 컨텍스트 범위 (작업2) ──
    # 팝오버에서 모델을 고를 때마다 그 모델의 실제 컨텍스트로 기본값을 정한다.
    for ml in models_list:
        prof = _llm_model_profile(ml["id"])
        ml["kind"] = prof["kind"]
        # 유효 컨텍스트: 로드돼 있으면 실제 할당치, 아니면 최대치(과대 시 32K 로 캡).
        maxc = ml.get("max_ctx") or 0
        eff = ml.get("loaded_ctx") or (min(maxc, 32768) if maxc else 0)
        if eff:
            # 기본 Max Tokens = 유효 컨텍스트의 1/4 을 프로파일 기본과 절충(상·하한 클램프).
            ml["def_tokens"] = max(512, min(4096, max(prof["max_tokens"], eff // 4)))
            ml["rec_ctx_lo"] = max(256, eff // 8)
            ml["rec_ctx_hi"] = max(512, eff // 4)
        else:
            ml["def_tokens"] = prof["max_tokens"]
    active = next((m for m in models_list if m["loaded"]), None)
    if not active:
        active = next((m for m in models_list if _LLM_PREFERRED in m["id"]), None)
    if not active and models_list:
        active = models_list[0]
    return {"installed": True, "model": active, "models": models_list}


@app.get("/api/llm/status")
def api_llm_status() -> Response:
    return jsonify(_llm_status())


@app.get("/api/llm/loaded")
def api_llm_loaded() -> Response:
    """경량 로드상태 — AI 버튼 점(초록/회색)용. /api/v0/models 한 번만 본다(작업5)."""
    import json as _json
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:1234/api/v0/models", timeout=3.0) as r:
            data = _json.loads(r.read().decode("utf-8")).get("data", [])
        loaded = [m.get("id") for m in data
                  if m.get("state") == "loaded" and "embed" not in (m.get("id") or "").lower()]
        return jsonify({"up": True, "loaded": bool(loaded), "id": (loaded[0] if loaded else "")})
    except Exception:  # noqa: BLE001
        return jsonify({"up": False, "loaded": False, "id": ""})


def _llm_target_key() -> str | None:
    """Load 대상 모델 키 — ls 에서 선호 모델의 정확한 키를 찾는다."""
    import json as _json
    ls = _lms_run(["ls", "--json"], 15.0)
    if ls:
        try:
            for m in _json.loads(ls):
                key = m.get("modelKey") or m.get("path") or ""
                if _LLM_PREFERRED in key:
                    return key
        except Exception:  # noqa: BLE001
            pass
    return _LLM_PREFERRED


@app.post("/api/llm/load")
def api_llm_load() -> Response:
    if not _llm_installed():
        return jsonify({"ok": False, "msg": "로컬 LLM 환경이 설치되어 있지 않습니다."})
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    req_key = data.get("modelKey")
    key = req_key or _llm_target_key()
    
    # 다른 모델 선택 시 기존 모델 모두 언로드 보장
    _lms_run(["unload", "--all"], 30.0)
    
    out = _lms_run(["load", key or _LLM_PREFERRED, "-y"], 180.0)
    st = _llm_status()
    ok = bool(st.get("model") and st["model"].get("loaded"))
    return jsonify({"ok": ok, "msg": "" if ok else (out or "모델 로드 실패"), **st})


@app.post("/api/llm/unload")
def api_llm_unload() -> Response:
    if not _llm_installed():
        return jsonify({"ok": False, "msg": "로컬 LLM 환경이 설치되어 있지 않습니다."})
    _lms_run(["unload", "--all"], 30.0)
    st = _llm_status()
    ok = not (st.get("model") and st["model"].get("loaded"))
    return jsonify({"ok": ok, **st})


_lms_procs = {}
@app.get("/api/llm/hardware")
def api_llm_hardware() -> Response:
    mem_bytes = 0
    cpu_pct = 0.0
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = p.info.get('name') or ""
                cmdline = p.info.get('cmdline') or []
                full_cmd = " ".join(cmdline).lower()
                name_lower = name.lower()
                if "lm studio" in name_lower or "lmstudio" in full_cmd or "lmlink" in full_cmd or "llama-server" in full_cmd:
                    pid = p.info['pid']
                    if pid not in _lms_procs:
                        _lms_procs[pid] = p
                        p.cpu_percent(interval=None) # Prime it
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        dead_pids = []
        for pid, p in _lms_procs.items():
            try:
                mem_bytes += p.memory_info().rss
                cpu_pct += p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                dead_pids.append(pid)
        for pid in dead_pids:
            del _lms_procs[pid]
            
        ncpu = psutil.cpu_count() or 1
        cpu_pct = cpu_pct / ncpu
    except ImportError:
        import subprocess
        import os
        try:
            out = subprocess.check_output(["ps", "-ax", "-o", "pid,rss,%cpu,command"], text=True)
            for line in out.splitlines()[1:]:
                parts = line.strip().split(maxsplit=3)
                if len(parts) < 4: continue
                pid_str, rss_str, cpu_str, cmd = parts
                cmd_lower = cmd.lower()
                if "lm studio" in cmd_lower or "lmstudio" in cmd_lower or "lmlink" in cmd_lower or "llama-server" in cmd_lower:
                    try:
                        mem_bytes += int(rss_str) * 1024
                        cpu_pct += float(cpu_str)
                    except ValueError:
                        pass
            ncpu = os.cpu_count() or 1
            cpu_pct = cpu_pct / ncpu
        except Exception:
            pass
    except Exception:
        pass
        
    return jsonify({"ram_gb": round(mem_bytes / (1024**3), 1), "cpu_pct": round(cpu_pct, 1)})


# ════════════════ 전 종목 크로스섹셔널 스크리너 ════════════════
# SSD 의 chart_{code}_{days}.parquet 캐시를 스캔해 5영업일 모멘텀 상위를 뽑는다.
#
# ⚠️ 핵심 함정(과거 흰 화면의 원인):
#   1) 한 종목에 day-window 가 다른 parquet 가 여러 개 존재할 수 있다
#      (chart_005380_160.parquet, chart_005380_2400.parquet …). 코드만으로 JOIN 하면
#      파일 간 카테시안 곱이 생겨 같은 종목이 중복 표시된다 → 코드별로 "행이 가장 많은
#      파일"(가장 긴 히스토리) 1개만 선택해 중복을 제거한다.
#   2) 실행 환경(번들 .app 등)에 duckdb 가 없을 수 있다 → duckdb 우선, 실패 시
#      pyarrow/pandas 폴백(pyarrow 는 requirements 로 항상 보장)으로 동일 결과를 낸다.
_SCREENER_MIN_MONEY = 10_000_000_000  # 거래대금 100억 이상만 (저유동성 제거)


def _screener_rows_pandas() -> list[dict]:
    """duckdb 없이 pyarrow/pandas 로 5일 모멘텀 상위 50종목을 계산."""
    import glob
    import re

    import pandas as pd

    best: dict[str, pd.DataFrame] = {}  # code -> 가장 긴 히스토리 DF
    for path in glob.glob(str(_CACHE_DIR / "chart_*.parquet")):
        m = re.search(r"chart_([0-9A-Za-z]+)_", Path(path).name)
        if not m:
            continue
        code = m.group(1)
        try:
            df = pd.read_parquet(path, columns=["일자", "종가", "거래량"])
        except Exception:  # noqa: BLE001
            continue
        if len(df) < 6:
            continue
        if code not in best or len(df) > len(best[code]):
            best[code] = df

    rows: list[dict] = []
    for code, df in best.items():
        df = df.sort_values("일자")
        cur = df.iloc[-1]
        old = df.iloc[-5]  # rn=5 == 최근에서 5번째 (원본 쿼리와 동일 기준)
        cp = float(cur["종가"])
        op = float(old["종가"])
        vol = float(cur["거래량"])
        money = cp * vol
        if op <= 0 or money < _SCREENER_MIN_MONEY:
            continue
        rows.append({"code": code, "current_price": cp,
                     "ret_5d": round((cp - op) / op * 100, 2), "volume_money": money})
    rows.sort(key=lambda r: r["ret_5d"], reverse=True)
    return rows[:50]


def _screener_rows_duckdb() -> list[dict]:
    """duckdb 로 동일 계산 — 코드별 최장 히스토리 파일 1개만 선택해 중복 제거."""
    import duckdb

    glob_path = str(_CACHE_DIR / "chart_*.parquet")
    sql = f"""
        WITH files AS (
            SELECT
                filename,
                regexp_extract(filename, 'chart_([0-9A-Za-z]+)_', 1) AS code,
                "종가" AS close_price,
                "거래량" AS volume,
                row_number() OVER (PARTITION BY filename ORDER BY "일자" DESC) AS rn,
                count(*) OVER (PARTITION BY filename) AS nrows
            FROM read_parquet('{glob_path}', filename=true)
        ),
        best AS (  -- 코드별 가장 긴 히스토리 파일 1개만 선택
            SELECT code, arg_max(filename, nrows) AS filename
            FROM (SELECT DISTINCT code, filename, nrows FROM files)
            GROUP BY code
        ),
        chosen AS (
            SELECT f.* FROM files f JOIN best b USING (code, filename)
        )
        SELECT
            c1.code,
            c1.close_price AS current_price,
            ROUND((c1.close_price - c5.close_price) / CAST(c5.close_price AS DOUBLE) * 100, 2) AS ret_5d,
            (c1.close_price * c1.volume) AS volume_money
        FROM chosen c1
        JOIN chosen c5 ON c1.code = c5.code AND c5.rn = 5
        WHERE c1.rn = 1
          AND c5.close_price > 0
          AND (c1.close_price * c1.volume) > {_SCREENER_MIN_MONEY}
        ORDER BY ret_5d DESC NULLS LAST
        LIMIT 50
    """
    df = duckdb.connect().query(sql).df()
    return [{"code": r.code, "current_price": float(r.current_price),
             "ret_5d": float(r.ret_5d), "volume_money": float(r.volume_money)}
            for r in df.itertuples()]


@app.get("/api/screener")
def _api_screener():
    q = request.args.get("q", "momentum")
    if q != "momentum":
        return jsonify({"status": "error", "msg": "Unsupported query type"})
    try:
        try:
            rows = _screener_rows_duckdb()      # 빠른 경로
        except Exception as e:                  # noqa: BLE001 — duckdb 미설치/오류 시 폴백
            print(f"[screener] duckdb 경로 실패({e}) — pyarrow 폴백")
            rows = _screener_rows_pandas()

        corps = company.get_corps()
        name_map = {c["stock_code"]: c["corp_name"] for c in corps if c.get("stock_code")}

        res = [{
            "code": r["code"],
            "name": name_map.get(r["code"], r["code"]),
            "price": int(r["current_price"]),
            "ret_5d": float(r["ret_5d"]),
            "vol": int(r["volume_money"] // 100_000_000),
        } for r in rows if r["code"]]

        return jsonify({"status": "ok", "data": res})
    except Exception as e:  # noqa: BLE001
        return jsonify({"status": "error", "msg": str(e)})


@app.get("/screener_page")
def screener_page() -> Response:
    # ⚠️ 이 페이지는 iframe 으로 임베드된다. 부모 문서의 CSS 변수(--label 등)는
    # 상속되지 않으므로 절대 의존하면 안 된다(과거 color:var(--label,#fff) 때문에
    # 라이트 모드에서 흰 글씨+투명 배경 = 흰 화면이었다). 색을 명시하고, 부모와
    # 동일한 테마 동기화(localStorage('kmkt-theme') + postMessage({kmkt})) 를 쓴다.
    html = """<!DOCTYPE html>
<html lang="ko" data-kind="screener"><head><meta charset="utf-8">
<title>스크리너 (DuckDB)</title>
<link rel="icon" href="/favicon.ico">
<script>try{if(localStorage.getItem('kmkt-theme')==='dark')document.documentElement.classList.add('dark');}catch(e){}</script>
<style>
:root{--bg:#f4f5f9;--card:rgba(255,255,255,.82);--ink:#1d1d1f;--sub:rgba(60,60,67,.6);--line:rgba(60,60,67,.1);
 --row-hover:rgba(10,132,255,.06);--head:rgba(60,60,67,.55);--up:#FF3B30;--down:#2E75B6;}
html.dark{--bg:#0d1117;--card:rgba(28,30,38,.74);--ink:#eef3ff;--sub:#9aa6bd;--line:rgba(255,255,255,.1);
 --row-hover:rgba(90,166,255,.1);--head:#9aa6bd;--up:#FF453A;--down:#64B5FF;}
body{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
 background:var(--bg);color:var(--ink);padding:22px 26px;transition:background .4s ease;
 -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
h2{margin:0 0 4px;font-size:19px;font-weight:700;letter-spacing:-.02em;}
.lead{color:var(--sub);font-size:13px;margin:0 0 6px;}
/* macOS 26 글라스 카드로 표를 감싼다 — 다른 화면(업종·시장)과 동일한 그룹드 리스트 룩 */
.card{margin-top:14px;background:var(--card);
 -webkit-backdrop-filter:saturate(180%) blur(30px);backdrop-filter:saturate(180%) blur(30px);
 border:.5px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.08);}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px 16px;border-bottom:.5px solid var(--line);text-align:left;font-size:14px;}
tbody tr:last-child td{border-bottom:0;}
/* HIG: 테이블 헤더는 대문자화하지 않는다(소문자 세미볼드 캡션) */
th{color:var(--head);font-weight:600;font-size:12px;letter-spacing:-.01em;background:var(--card);}
td.num,th.num{text-align:right;}
.name{font-weight:600;}
.code{color:var(--sub);font-size:12px;}
.up{color:var(--up);font-weight:600;}
.down{color:var(--down);font-weight:600;}
tbody tr{cursor:pointer;transition:background .12s ease;}
tbody tr:hover{background:var(--row-hover);}
.state{color:var(--sub);font-size:14px;padding:24px 2px;}
.err{color:var(--up);}
</style>
</head><body>
<h2>전 종목 크로스섹셔널 스크리닝 <span style="font-size:12px;color:var(--sub);font-weight:500;">DuckDB</span></h2>
<p class="lead">로컬 SSD 캐시 기준 · 최근 5영업일 거래대금 100억 이상 · 수익률 상위 모멘텀</p>
<div id="state" class="state">전 종목 캐시를 스캔하는 중…</div>
<div class="card" id="tblCard" style="display:none;">
<table id="tbl">
  <thead><tr><th>종목명</th><th>코드</th><th class="num">현재가</th><th class="num">5일 수익률</th><th class="num">거래대금(억)</th></tr></thead>
  <tbody id="tbody"></tbody>
</table></div>
<script>
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function open_(code){try{if(window.parent&&window.parent.miOpenStockTab)window.parent.miOpenStockTab(code);}catch(e){}}
fetch('/api/screener?q=momentum').then(r=>r.json()).then(d=>{
  var st=document.getElementById('state');
  if(d.status!=='ok'){st.className='state err';st.textContent='스크리너 오류: '+(d.msg||'알 수 없는 오류');return;}
  if(!d.data||!d.data.length){st.textContent='조건을 만족하는 종목이 없습니다(캐시가 비어 있을 수 있습니다).';return;}
  var tb=document.getElementById('tbody');
  tb.innerHTML=d.data.map(function(r){
    var cls=r.ret_5d>0?'up':(r.ret_5d<0?'down':'');
    var sgn=r.ret_5d>0?'+':'';
    return '<tr data-code="'+esc(r.code)+'">'+
      '<td class="name">'+esc(r.name)+'</td>'+
      '<td class="code">'+esc(r.code)+'</td>'+
      '<td class="num">'+r.price.toLocaleString()+'원</td>'+
      '<td class="num '+cls+'">'+sgn+r.ret_5d.toFixed(2)+'%</td>'+
      '<td class="num">'+r.vol.toLocaleString()+'</td></tr>';
  }).join('');
  tb.querySelectorAll('tr').forEach(function(tr){tr.addEventListener('click',function(){open_(tr.dataset.code);});});
  st.style.display='none';
  document.getElementById('tblCard').style.display='';
}).catch(function(e){
  var st=document.getElementById('state');st.className='state err';st.textContent='스크리너 연결 실패: '+e;
});
window.addEventListener('message',function(e){
  var d=e&&e.data;if(!d||!d.kmkt)return;
  document.documentElement.classList.toggle('dark',d.kmkt==='dark');
});
</script>
</body></html>"""
    html = _inject_loader(html, [
        _state_loader('<div id="state" class="state">전 종목 캐시를 스캔하는 중…</div>',
                      "전 종목 캐시를 스캔하는 중…")])
    html = _inject_floating_ai(html, "market")    # AI 질문 위젯 (작업2 — 모든 화면)
    return Response(html, mimetype="text/html")



@app.get("/dashboard")
def dashboard() -> Response:
    q = (request.args.get("q") or "").strip()
    if not q:
        return Response(_error_html("검색어를 입력하세요."), mimetype="text/html")
    try:
        kind = detect_type(q)
        if kind == "etf":
            html, err = etf.build_dashboard_html(q)
            code = _resolve_etf_code(q)
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
        html = _inject_realtime(html, code)  # 현재가(.ph-price)만 KIS 실시간 시세로 갱신
        if kind != "etf" and code:
            html = _inject_profile(html, code)   # 작업2: 기업 개요 카드(히어로 아래)
        if code:
            html = _inject_ask(html, "etf" if kind == "etf" else "stock", code)  # 작업4
    except Exception:  # noqa: BLE001
        pass
    return Response(html, mimetype="text/html")


# ── 앱 전반 'AI 질문하기' 위젯 (작업4) — 어느 화면에든 주입 가능한 자기완결 카드 ──
# scope/id 는 페이지가 제공하는 window.KMKT_ASK() 에서 '질문 시점'에 읽는다(동적 값 대응).
# 일반 Python 문자열이라 JS 의 \\n 은 브라우저에서 \n(LF)로 해석된다(raw 페이지에 넣어도 안전).


def _ask_setter(scope: str, ident: str = "", excd: str = "") -> str:
    """페이지에 window.KMKT_ASK 를 심는 <script> (주입 리포트용 — scope/id 가 서버에서 확정)."""
    import json as _j
    return (f"<script>window.KMKT_ASK=function(){{return "
            f"{{scope:{_j.dumps(scope)},id:{_j.dumps(ident)},excd:{_j.dumps(excd)}}};}};</script>")


def _inject_ask(html: str, scope: str, ident: str = "", excd: str = "") -> str:
    """리포트/페이지에 플로팅 'AI 질문하기' 위젯 주입(작업2). position:fixed 위젯이라
    transform 조상 아래에서 깨지지 않도록 반드시 </body> 직전(body 직속)에 삽입한다."""
    try:
        block = _ask_setter(scope, ident, excd) + _ASK_WIDGET_HTML
        idx = html.rfind("</body>")
        if idx != -1:
            return html[:idx] + block + html[idx:]
        return html + block
    except Exception:  # noqa: BLE001
        return html


def _inject_profile(html: str, code: str) -> str:
    """국내 종목 리포트 개요탭(pane0) 히어로 카드 바로 아래에 '기업 개요' 카드를 주입(작업2)."""
    try:
        card = _profile_card_html(_dart_company_profile(code))
        if not card:
            return html
        anchor = html.find('id="pane0">')
        if anchor == -1:
            return html
        sec_end = html.find('</section>', anchor)   # pane0 첫 카드(=price-hero) 끝
        if sec_end == -1:
            return html
        ins = sec_end + len('</section>')
        return html[:ins] + card + html[ins:]
    except Exception:  # noqa: BLE001
        return html


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


# ════════════════════════════════════════════════════════════════════════════
#  내장 백테스터 (작업3) — Docker·계정 불필요. 일봉(SSD parquet 캐시+네이버) + NumPy.
#    전략: SMA 교차 / RSI 평균회귀 / N일 모멘텀 / 매수보유.  신호는 종가 산출,
#    포지션 반영은 다음 봉(look-ahead 방지), 거래 시마다 편도 비용(bp) 차감.
# ════════════════════════════════════════════════════════════════════════════


def _bt_run(code: str, strat: str, p: dict, days: int, cost_bp: float) -> dict:
    oh = _clean_ohlc(asyncio.run(_afetch(code, days)))
    if not oh or len(oh["c"]) < 70:
        return {"ok": False, "msg": f"가격 데이터 부족 ({0 if not oh else len(oh['c'])}봉)"}
    dates, closes = oh["d"], oh["c"]
    ret = np.diff(closes) / closes[:-1]              # 일간 수익률 (n-1)
    cost = cost_bp / 1e4

    def equity_of(sig: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        pos = sig[:-1]                               # t 신호 → t+1 수익률에 적용
        churn = np.abs(np.diff(sig, prepend=0.0))[:-1]
        r = pos * ret - churn * cost
        return np.cumprod(1 + r), r

    sig = _bt_signal(closes, strat, p)
    eq, r = equity_of(sig)
    beq, br = equity_of(np.ones(len(closes)))

    def metrics(curve: np.ndarray, rr: np.ndarray) -> dict:
        total = (curve[-1] - 1) * 100
        yrs = max(len(rr) / 252, 1e-9)
        cagr = ((curve[-1]) ** (1 / yrs) - 1) * 100
        peak = np.maximum.accumulate(curve)
        mdd = float(((curve - peak) / peak).min()) * 100
        sd = rr.std()
        sharpe = float(rr.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0
        return {"total": round(float(total), 2), "cagr": round(float(cagr), 2),
                "mdd": round(mdd, 2), "sharpe": round(sharpe, 2),
                "vol": round(float(sd * np.sqrt(252) * 100), 2)}

    # 거래 내역 (진입/청산 쌍 + 트레이드 수익률) + 차트 마커용 인덱스 기록
    trades, entry_i = [], None
    mark_idx = []                                     # [(index, side)]
    for i in range(1, len(sig)):
        if sig[i] > 0.5 and sig[i - 1] < 0.5:
            entry_i = i
            mark_idx.append((i, "buy"))
        elif sig[i] < 0.5 and sig[i - 1] > 0.5 and entry_i is not None:
            tr = (closes[i] / closes[entry_i] - 1) * 100 - cost_bp / 1e2 * 2
            trades.append({"in": str(dates[entry_i])[:10], "out": str(dates[i])[:10],
                           "ret": round(float(tr), 2)})
            mark_idx.append((i, "sell"))
            entry_i = None
    if entry_i is not None:                           # 미청산 포지션
        tr = (closes[-1] / closes[entry_i] - 1) * 100 - cost_bp / 1e2
        trades.append({"in": str(dates[entry_i])[:10], "out": "보유중",
                       "ret": round(float(tr), 2)})
    wins = [t for t in trades if t["ret"] > 0]
    winrate = round(len(wins) / len(trades) * 100, 1) if trades else 0.0

    # ── 프로 지표 (월스트리트식 성과 분석) ──
    strat_m = metrics(eq, r)
    wins_r = [t["ret"] for t in trades if t["ret"] > 0]
    loss_r = [t["ret"] for t in trades if t["ret"] < 0]
    gross_win, gross_loss = sum(wins_r), abs(sum(loss_r))
    avg_win = (sum(wins_r) / len(wins_r)) if wins_r else 0.0
    avg_loss = (sum(loss_r) / len(loss_r)) if loss_r else 0.0
    mcl = cur = 0                                     # 최대 연속 손실 거래수
    for t in trades:
        if t["ret"] < 0:
            cur += 1; mcl = max(mcl, cur)
        else:
            cur = 0
    rr = r[r != 0]
    pro = {
        "calmar": round(strat_m["cagr"] / abs(strat_m["mdd"]), 2) if strat_m["mdd"] < 0 else None,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else None,
        "payoff": round(abs(avg_win / avg_loss), 2) if avg_loss else None,
        "avg_win": round(avg_win, 2), "avg_loss": round(avg_loss, 2),
        "max_consec_loss": int(mcl),
        "best": round(max([t["ret"] for t in trades]), 2) if trades else None,
        "worst": round(min([t["ret"] for t in trades]), 2) if trades else None,
        "avg_hold": None,
        "pos_days": int((rr > 0).sum()), "neg_days": int((rr < 0).sum()),
    }

    # 자본곡선 다운샘플 (≤420 포인트)
    step = max(1, len(eq) // 420)
    curve = [{"d": str(dates[i + 1])[:10], "s": round(float(eq[i]), 4),
              "b": round(float(beq[i]), 4)} for i in range(0, len(eq), step)]

    # ── 캔들 차트용: OHLC 다운샘플(버킷 집계) + 지표 + 매수/매도 마커 ──
    N = len(closes)
    target = 300
    bstep = max(1, N // target)
    # 지표 시리즈(전체 길이) 계산
    ind: dict = {"type": strat}
    if strat == "sma":
        f = max(2, int(p.get("fast", 20))); s = max(f + 1, int(p.get("slow", 60)))
        ma_f = pd.Series(closes).rolling(f).mean().values
        ma_s = pd.Series(closes).rolling(s).mean().values
        ind.update(fast=f, slow=s)
    elif strat == "rsi":
        per = max(2, int(p.get("period", 14)))
        d = np.diff(closes, prepend=closes[0])
        up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / per, adjust=False).mean().values
        dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / per, adjust=False).mean().values
        rsi_arr = 100 - 100 / (1 + up / np.where(dn == 0, 1e-9, dn))
        ind.update(period=per, buy=float(p.get("buy", 30)), sell=float(p.get("sell", 70)))

    def _f(x):
        return None if (x is None or not np.isfinite(x)) else round(float(x), 2)

    bars, idx_to_bar = [], {}
    for bi, start in enumerate(range(0, N, bstep)):
        seg = slice(start, min(start + bstep, N))
        cl_seg = closes[seg]
        last = min(start + bstep, N) - 1
        bar = {"d": str(dates[last])[:10], "o": _f(closes[start]),
               "h": _f(float(np.max(oh["h"][seg]))), "l": _f(float(np.min(oh["l"][seg]))),
               "c": _f(closes[last])}
        if strat == "sma":
            bar["mf"] = _f(ma_f[last]); bar["ms"] = _f(ma_s[last])
        elif strat == "rsi":
            bar["rsi"] = _f(rsi_arr[last])
        bars.append(bar)
        for j in range(start, min(start + bstep, N)):
            idx_to_bar[j] = bi
    markers = [{"b": idx_to_bar.get(i, 0), "px": _f(closes[i]), "side": side} for i, side in mark_idx]

    return {"ok": True, "code": code, "name": _ai_stock_name(code), "n": int(N),
            "start": str(dates[0])[:10], "end": str(dates[-1])[:10],
            "strategy": strat_m, "bench": metrics(beq, br), "pro": pro,
            "trades_n": len(trades), "winrate": winrate,
            "exposure": round(float(sig.mean() * 100), 1),
            "trades": trades[-20:], "curve": curve,
            "bars": bars, "markers": markers, "ind": ind}


@app.get("/api/backtest")
def api_backtest() -> Response:
    code = (request.args.get("code") or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return jsonify({"ok": False, "msg": "6자리 종목코드가 필요합니다"})
    strat = (request.args.get("strat") or "sma").strip()
    days = min(4800, max(150, int(_rtf(request.args.get("days")) or 1250)))
    cost = min(100.0, max(0.0, _rtf(request.args.get("cost")) or 25.0))
    p = {k: request.args.get(k) for k in ("fast", "slow", "lookback", "period", "buy", "sell")
         if request.args.get(k)}
    try:
        return jsonify(_bt_run(code, strat, p, days, cost))
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "msg": f"백테스트 실패: {e}"})


@app.get("/backtest_page")
def backtest_page() -> Response:
    return Response(_BACKTEST_HTML, mimetype="text/html")




# ════════════════════════════════════════════════════════════════════════════
#  세계 시장 (작업2) — 세계 주요 지수 + 환율 한눈에
#    소스: Naver 마켓 (auth-free, 앱이 이미 쓰는 polling.finance.naver 계열).
#      · 지수  https://api.stock.naver.com/index/{reutersCode}/basic
#      · 환율  https://api.stock.naver.com/marketindex/exchange/{pair}
#      · KOSPI/KOSDAQ 는 기존 _kis_index 재사용 (KIS 일관성)
#    ~14개 HTTP 를 ThreadPool 로 병렬 수집(M4), 20초 캐시.
# ════════════════════════════════════════════════════════════════════════════
from concurrent.futures import ThreadPoolExecutor as _TPE

_WORLD_INDICES = [   # (reutersCode, 지역 라벨)
    (".INX", "🇺🇸 미국"), (".IXIC", "🇺🇸 미국"), (".DJI", "🇺🇸 미국"),
    (".N225", "🇯🇵 일본"), (".HSI", "🇭🇰 홍콩"), (".SSEC", "🇨🇳 중국"),
    (".TWII", "🇹🇼 대만"), (".GDAXI", "🇩🇪 독일"), (".FTSE", "🇬🇧 영국"), (".STOXX50E", "🇪🇺 유럽"),
]
_WORLD_FX = [("FX_USDKRW", "🇺🇸 달러"), ("FX_JPYKRW", "🇯🇵 엔(100)"),
             ("FX_EURKRW", "🇪🇺 유로"), ("FX_CNYKRW", "🇨🇳 위안")]
_WORLD_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"}
_WORLD_CACHE: dict = {"t": 0.0, "data": None}
_WORLD_TTL = 20.0


def _world_sign_dir(code: str) -> str:
    code = str(code or "3")
    return "up" if code in ("1", "2") else ("down" if code in ("4", "5") else "flat")


# 네이버 marketStatus → (한글 라벨, phase)
_WORLD_STATUS_MAP = {
    "OPEN": ("장중", "open"), "CLOSE": ("장마감", "closed"), "CLOSED": ("장마감", "closed"),
    "PREOPEN": ("개장 전", "pre"), "PRE": ("개장 전", "pre"),
    "POSTCLOSE": ("장마감", "closed"), "POST": ("시간외", "post"),
    "HOLIDAY": ("휴장", "holiday"), "PAUSE": ("거래정지", "closed"),
}


def _world_status_kr(raw: str) -> tuple[str, str]:
    raw = (raw or "").upper().strip()
    return _WORLD_STATUS_MAP.get(raw, (("장중", "open") if raw == "OPEN" else ("장마감", "closed")) if raw else ("", ""))


def _world_index_one(code: str, region: str) -> dict | None:
    try:
        r = httpx.get(f"https://api.stock.naver.com/index/{code}/basic",
                      timeout=6, headers=_WORLD_UA)
        d = r.json()
        if not d.get("closePrice"):
            return None
        lab, ph = _world_status_kr(d.get("marketStatus"))
        # 네이버 카드 정보 그리드 (전일·시가·고가·저가·52주 최고/최저)
        ti = {it.get("code"): it.get("value") for it in (d.get("stockItemTotalInfos") or [])}
        info = {"prev": ti.get("lastClosePrice"), "open": ti.get("openPrice"),
                "high": ti.get("highPrice"), "low": ti.get("lowPrice"),
                "hi52": ti.get("highPriceOf52Weeks"), "lo52": ti.get("lowPriceOf52Weeks")}
        return {"code": code, "region": region, "name": d.get("indexName") or code,
                "price": d.get("closePrice"), "chg": d.get("compareToPreviousClosePrice") or "",
                "pct": d.get("fluctuationsRatio") or "0",
                "dir": _world_sign_dir((d.get("compareToPreviousPrice") or {}).get("code")),
                "status": lab, "phase": ph, "info": info}
    except Exception:  # noqa: BLE001
        return None


def _world_fx_one(pair: str, label: str) -> dict | None:
    try:
        r = httpx.get(f"https://api.stock.naver.com/marketindex/exchange/{pair}",
                      timeout=6, headers=_WORLD_UA)
        d = (r.json() or {}).get("exchangeInfo") or {}
        if not d.get("closePrice"):
            return None
        fl = str(d.get("fluctuations") or "0")
        sign = (d.get("compareToPreviousPrice") or {}).get("code")
        dirc = _world_sign_dir(sign) if sign else ("down" if fl.startswith("-") else "up")
        return {"pair": pair, "label": label, "name": d.get("name") or label,
                "price": d.get("closePrice"), "chg": fl.lstrip("+"),
                "pct": d.get("fluctuationsRatio") or "0", "dir": dirc}
    except Exception:  # noqa: BLE001
        return None


def _world_domestic_one(iscd: str, name: str, region: str) -> dict | None:
    d = _kis_index(iscd)
    if not d.get("ok"):
        return None
    ph = _index_phase()                                   # open/pre/closed/holiday
    d = _zero_if_pre(d, ph)                                # 개장 전이면 등락 0
    pct = d.get("change_pct", 0.0)
    chg = d.get("change", 0.0)
    lab = {"open": "장중", "pre": "개장 전", "closed": "장마감", "holiday": "휴장"}.get(ph, "")
    return {"code": iscd, "region": region, "name": name,
            "price": f"{_rtf(d.get('value')):,.2f}", "chg": f"{_rtf(chg):,.2f}",
            "pct": f"{pct:.2f}", "dir": "up" if pct > 0 else ("down" if pct < 0 else "flat"),
            "status": lab, "phase": ph}


def _world_snapshot() -> dict:
    now = time.time()
    if _WORLD_CACHE["data"] and (now - _WORLD_CACHE["t"]) < _WORLD_TTL:
        return _WORLD_CACHE["data"]
    indices: list = []
    with _TPE(max_workers=12) as ex:
        idx_f = [ex.submit(_world_index_one, c, rg) for c, rg in _WORLD_INDICES]
        fx_f = [ex.submit(_world_fx_one, p, lb) for p, lb in _WORLD_FX]
        dom_f = [ex.submit(_world_domestic_one, "0001", "코스피", "🇰🇷 한국"),
                 ex.submit(_world_domestic_one, "1001", "코스닥", "🇰🇷 한국")]
        dom = [f.result() for f in dom_f]
        indices = [f.result() for f in idx_f]
        fx = [f.result() for f in fx_f]
    rows = [r for r in dom if r] + [r for r in indices if r]
    data = {"ok": True, "indices": rows, "fx": [r for r in fx if r],
            "asof": time.strftime("%m.%d %H:%M")}
    _WORLD_CACHE.update(t=now, data=data)
    return data


# ════════════════════════════════════════════════════════════════════════════
#  해외주식 (작업1) — 미국·일본 종목 시세/차트 (DART·네이버 컨센서스는 해외 미제공 → 생략)
_OV_EXCH = ["NAS", "NYS", "AMS", "TSE"]               # 미국(나스닥·뉴욕·아멕스) + 일본(도쿄)
_OV_CCY = {"NAS": "$", "NYS": "$", "AMS": "$", "TSE": "¥"}
_OV_EXNAME = {"NAS": "NASDAQ", "NYS": "NYSE", "AMS": "AMEX", "TSE": "도쿄"}
_OV_CACHE: dict = {}


def _ov_price(excd: str, symb: str) -> dict | None:
    j = _rt_kis_get("/uapi/overseas-price/v1/quotations/price", "HHDFS00000300",
                    {"AUTH": "", "EXCD": excd, "SYMB": symb})
    if not j:
        return None
    o = j.get("output") or {}
    if isinstance(o, list):
        o = o[0] if o else {}
    last = _rtf(o.get("last"))
    if last <= 0:
        return None
    return {"excd": excd, "symb": symb, "ccy": _OV_CCY.get(excd, ""),
            "exname": _OV_EXNAME.get(excd, excd), "last": last, "base": _rtf(o.get("base")),
            "diff": _rtf(o.get("diff")), "rate": _rtf(o.get("rate")),
            "tvol": _rtf(o.get("tvol"))}


def _ov_resolve(symb: str) -> dict:
    symb = (symb or "").strip().upper()
    if not symb:
        return {"ok": False, "msg": "no symbol"}
    ck = _OV_CACHE.get("r:" + symb)
    if ck and time.time() - ck[1] < 30:
        return ck[0]
    for ex in _OV_EXCH:
        p = _ov_price(ex, symb)
        if p:
            r = {"ok": True, **p,
                 "dir": "up" if p["rate"] > 0 else ("down" if p["rate"] < 0 else "flat")}
            _OV_CACHE["r:" + symb] = (r, time.time())
            return r
    return {"ok": False, "needs_key": _kis_keys()[0] is None,
            "msg": "종목을 찾을 수 없습니다 (미국·일본 종목만 지원)"}


def _ov_chart(excd: str, symb: str, gubn: str = "0") -> dict:
    # 캐싱 (30분 캐시)
    cache_key = f"c:{excd}:{symb}:{gubn}"
    ck = _OV_CACHE.get(cache_key)
    if ck and time.time() - ck[1] < 1800:
        return ck[0]

    bymd = ""
    all_rows = []
    # 최대 4회 페이징하여 약 400일치의 시계열 데이터 수집
    for _ in range(4):
        j = _rt_kis_get("/uapi/overseas-price/v1/quotations/dailyprice", "HHDFS76240000",
                        {"AUTH": "", "EXCD": excd, "SYMB": symb, "GUBN": gubn, "BYMD": bymd, "MODP": "1"})
        if not j or not j.get("output2"):
            break
        outputs = j["output2"]
        curr_rows = []
        for o in outputs:
            c = _rtf(o.get("clos"))
            if c <= 0:
                continue
            curr_rows.append({"d": o.get("xymd"), "o": _rtf(o.get("open")), "h": _rtf(o.get("high")),
                              "l": _rtf(o.get("low")), "c": c, "v": _rtf(o.get("tvol"))})
        if not curr_rows:
            break
        all_rows.extend(curr_rows)
        # 다음 페이징을 위해 가장 과거 날짜 획득
        last_date = outputs[-1].get("xymd")
        if not last_date or last_date == bymd:
            break
        try:
            dt = datetime.strptime(last_date, "%Y%m%d") - timedelta(days=1)
            bymd = dt.strftime("%Y%m%d")
        except Exception:
            break
        time.sleep(0.05) # 스로틀링 회피용 딜레이

    all_rows.reverse() # 과거 -> 최신순
    res = {"ok": True, "rows": all_rows}
    _OV_CACHE[cache_key] = (res, time.time())
    return res



# 자동완성: Naver ac (한글명 지원) → 미국·일본만 필터, 거래소를 KIS EXCD 로 매핑
_OV_TYPE2EXCD = {"NASDAQ": "NAS", "NYSE": "NYS", "AMEX": "AMS", "TOKYO": "TSE"}
_OV_NATION = {"USA": "🇺🇸", "JPN": "🇯🇵"}


def _ov_suggest(qs: str) -> list[dict]:
    qs = (qs or "").strip()
    if not qs:
        return []
    ck = _OV_CACHE.get("s:" + qs.lower())
    if ck and time.time() - ck[1] < 300:
        return ck[0]
    out: list[dict] = []
    try:
        r = httpx.get("https://ac.stock.naver.com/ac", timeout=5, headers=_WORLD_UA,
                      params={"q": qs, "target": "stock"})
        for it in (r.json() or {}).get("items", []):
            excd = _OV_TYPE2EXCD.get(it.get("typeCode") or "")
            if not excd or it.get("nationCode") not in _OV_NATION:
                continue
            out.append({"code": it.get("code"), "name": it.get("name"), "excd": excd,
                        "exname": _OV_EXNAME.get(excd, excd),
                        "flag": _OV_NATION[it["nationCode"]]})
            if len(out) >= 8:
                break
    except Exception:  # noqa: BLE001
        pass
    _OV_CACHE["s:" + qs.lower()] = (out, time.time())
    return out


def _ov_detail(excd: str, symb: str) -> dict:
    """현재가상세 HHDFS76200200 — PER/PBR/EPS/BPS·52주·시총·섹터·원환산까지."""
    j = _rt_kis_get("/uapi/overseas-price/v1/quotations/price-detail", "HHDFS76200200",
                    {"AUTH": "", "EXCD": excd, "SYMB": symb})
    if not j:
        return {"ok": False, "needs_key": _kis_keys()[0] is None}
    o = j.get("output") or {}
    if isinstance(o, list):
        o = o[0] if o else {}
    last = _rtf(o.get("last"))
    if last <= 0:
        return {"ok": False, "msg": "no data"}
    base = _rtf(o.get("base"))
    diff = last - base
    rate = (diff / base * 100) if base else 0.0
    return {"ok": True, "excd": excd, "symb": symb, "ccy": _OV_CCY.get(excd, ""),
            "exname": _OV_EXNAME.get(excd, excd),
            "last": last, "base": base, "diff": diff, "rate": rate,
            "dir": "up" if diff > 0 else ("down" if diff < 0 else "flat"),
            "open": _rtf(o.get("open")), "high": _rtf(o.get("high")), "low": _rtf(o.get("low")),
            "h52p": _rtf(o.get("h52p")), "h52d": o.get("h52d"), "l52p": _rtf(o.get("l52p")),
            "l52d": o.get("l52d"), "per": _rtf(o.get("perx")), "pbr": _rtf(o.get("pbrx")),
            "eps": _rtf(o.get("epsx")), "bps": _rtf(o.get("bpsx")),
            "tomv": _rtf(o.get("tomv")), "shar": _rtf(o.get("shar")),
            "sector": (o.get("e_icod") or "").strip(), "parp": _rtf(o.get("e_parp")),
            "tvol": _rtf(o.get("tvol")), "tamt": _rtf(o.get("tamt")),
            "krw": _rtf(o.get("t_xprc")), "krw_diff": _rtf(o.get("t_xdif")),
            "krw_rate": _rtf(o.get("t_xrat")), "fx": _rtf(o.get("t_rate")),
            "vnit": _rtf(o.get("vnit")), "curr": (o.get("curr") or "").strip(),
            "state": _ov_market_state(excd)}


_FINNHUB_NEWS_CACHE: dict = {}


def _ov_news(excd: str, symb: str) -> dict:
    """해외 종목별 뉴스 — Finnhub company-news(종목 고유) 우선, 실패 시 KIS 시장 뉴스 폴백.

    KIS HHPSTH60100C1 은 SYMB 필터가 부실해 모든 종목이 같은 시장 뉴스를 받는 문제가 있어
    (사용자 보고), 종목별로 다른 진짜 종목 뉴스를 주는 Finnhub /company-news 로 교체한다.
    미국=티커 그대로, 일본(TSE)=티커+'.T'. 5분 캐시."""
    fk = os.environ.get("FINNHUB_KEY", "")
    fsym = (symb + ".T") if excd == "TSE" else symb
    ck = "fn:" + fsym
    c = _FINNHUB_NEWS_CACHE.get(ck)
    if c and (time.time() - c[1]) < 300.0:
        return c[0]
    rows: list[dict] = []
    if fk and symb:
        try:
            from datetime import datetime as _dt, timedelta
            to = date.today().strftime("%Y-%m-%d")
            fr = (date.today() - timedelta(days=21)).strftime("%Y-%m-%d")
            r = httpx.get("https://finnhub.io/api/v1/company-news",
                          params={"symbol": fsym, "from": fr, "to": to, "token": fk}, timeout=10)
            arr = r.json()
            if isinstance(arr, list):
                for it in arr[:16]:
                    t = (it.get("headline") or "").strip()
                    if not t:
                        continue
                    ts = it.get("datetime") or 0
                    dd = _dt.fromtimestamp(ts) if ts else None
                    rows.append({"title": t,
                                 "date": dd.strftime("%Y%m%d") if dd else "",
                                 "time": dd.strftime("%H%M") if dd else "",
                                 "src": (it.get("source") or "").strip(), "name": symb,
                                 "url": it.get("url") or ""})
        except Exception:  # noqa: BLE001
            rows = []
    if rows:
        res = {"scope": "stock", "rows": _dedup_news(rows)}   # 근접-중복 제거 (작업2)
        _FINNHUB_NEWS_CACHE[ck] = (res, time.time())
        return res

    # 폴백: KIS 해외뉴스종합(시장 단위)
    def call(params: dict) -> list[dict]:
        j = _rt_kis_get("/uapi/overseas-price/v1/quotations/news-title", "HHPSTH60100C1",
                        {"INFO_GB": "", "CLASS_CD": "", "NATION_CD": "", "EXCHANGE_CD": "",
                         "SYMB": "", "DATA_DT": "", "DATA_TM": "", "CTS": "", **params})
        rows2 = (j or {}).get("outblock1") or (j or {}).get("output") or []
        out = []
        for o in rows2[:12]:
            t = (o.get("title") or "").strip()
            if t:
                out.append({"title": t, "date": o.get("data_dt"), "time": o.get("data_tm"),
                            "src": (o.get("source") or "").strip(), "name": o.get("symb_name")})
        return out

    nation = "JP" if excd == "TSE" else "US"
    mrows = call({"NATION_CD": nation}) or call({})
    return {"scope": "market", "nation": nation, "rows": _dedup_news(mrows)}


@app.get("/api/ov/suggest")
def api_ov_suggest() -> Response:
    return jsonify(_ov_suggest(request.args.get("q", "")))


@app.get("/api/ov/detail")
def api_ov_detail() -> Response:
    excd = request.args.get("excd", "").strip().upper()
    symb = request.args.get("symb", "").strip().upper()
    d = _ov_detail(excd, symb)
    if isinstance(d, dict) and d.get("ok"):
        try:                                      # 작업2: 기업 개요(Yahoo) — 실패 시 빈 문자열
            d["profile_html"] = _profile_card_html(_yahoo_profile(symb))
        except Exception:  # noqa: BLE001
            d["profile_html"] = ""
    return jsonify(d)


@app.get("/api/ov/news")
def api_ov_news() -> Response:
    return jsonify(_ov_news(request.args.get("excd", "").strip().upper(),
                            request.args.get("symb", "").strip().upper()))


@app.get("/api/ov/resolve")
def api_ov_resolve() -> Response:
    return jsonify(_ov_resolve(request.args.get("symb", "")))


@app.get("/api/ov/chart")
def api_ov_chart() -> Response:
    return jsonify(_ov_chart(request.args.get("excd", "").strip().upper(),
                             request.args.get("symb", "").strip().upper(),
                             request.args.get("gubn", "0")))


@app.get("/api/ov/price")
def api_ov_price() -> Response:
    """경량 현재가 폴링 전용 (HHDFS00000300) — 해외 페이지 10초 갱신용."""
    excd = request.args.get("excd", "").strip().upper()
    symb = request.args.get("symb", "").strip().upper()
    p = _ov_price(excd, symb) if excd and symb else None
    if p and p.get("last", 0) > 0:
        diff = p["last"] - (p.get("base") or p["last"])
        rate = p.get("rate") or (diff / p["base"] * 100 if p.get("base") else 0)
        return jsonify({"ok": True, "last": p["last"], "diff": diff, "rate": rate,
                        "dir": "up" if rate > 0 else ("down" if rate < 0 else "flat"),
                        "ccy": p["ccy"], "state": _ov_market_state(excd)})
    return jsonify({"ok": False})


@app.get("/overseas")
def overseas_page() -> Response:
    symb = (request.args.get("symb") or "").strip().upper()
    html = _OVERSEAS_HTML
    if symb:
        html = html.replace('<div id="m4QuantPane"></div>', f'<div id="m4QuantPane">{_lazy_pane("stock", symb)}</div>')
    return Response(html, mimetype="text/html")




# ════════════════════════════════════════════════════════════════════════════
#  실시간 트레이딩 데스크 (신규 — 전부 추가분, 기존 코드 비파괴)
#    1) 호가창(REST FHKST01010200 / WS H0STASP0) + 체결 히트맵(WS H0STCNT0)
#    2) 실시간 스크리너  volume-rank(FHPST01710000)
#    3) 수급 플로우  inquire-investor(FHKST01010900) + 프로그램매매(HHPPG046600C1)
#    4) 페이퍼 트레이딩(로컬 시뮬)  SQLite 원장 + _kis_price 라이브가 체결
#  설계: WS→SSE 브리지(코드별 백그라운드 asyncio 스레드가 _RT_STATE 갱신, 브라우저는
#        SSE로 폴링). 접속키는 브라우저에 노출 안 함. 무구독 30초 후 WS 자동 종료.
# ════════════════════════════════════════════════════════════════════════════
import sqlite3
from collections import deque

_RT_J = "J"
_RT_STATE: dict[str, dict] = {}          # code -> {book, trades(deque), cttr, last, poll_ts, ...}
_RT_LOCK = threading.Lock()
_RT_WS_URL = "ws://ops.koreainvestment.com:21000/tryitout/{tr}"
_RT_IDLE_STOP = 30.0                       # SSE 폴 끊긴 뒤 WS 유지 시간(초)


def _rtf(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except Exception:  # noqa: BLE001
        return 0.0


def _rt_kis_get(path: str, tr_id: str, params: dict) -> dict | None:
    """KIS REST GET 공용 — 기존 토큰/키/스로틀 재사용. 실패 시 None."""
    tok = _kis_token()
    ak, sk = _kis_keys()
    if not tok or not ak:
        return None
    try:
        with _KIS_LOCK:
            gap = time.time() - _KIS_LAST_CALL["t"]
            if gap < 0.06:
                time.sleep(0.06 - gap)
            _KIS_LAST_CALL["t"] = time.time()
        r = httpx.get(f"{_KIS_BASE}{path}", timeout=10,
                      headers={"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
                               "tr_id": tr_id, "custtype": "P"},
                      params=params)
        j = r.json()
        if str(j.get("rt_cd")) != "0":
            return None
        return j
    except Exception:  # noqa: BLE001
        return None


# ── 기능 1: 호가 스냅샷 (REST) ────────────────────────────────────────────────
def _rt_orderbook(code: str) -> dict:
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return {"ok": False, "msg": "invalid code"}
    j = _rt_kis_get("/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
                    "FHKST01010200", {"fid_cond_mrkt_div_code": _RT_J, "fid_input_iscd": code})
    if not j:
        return {"ok": False, "needs_key": _kis_keys()[0] is None, "msg": "no data"}
    o = j.get("output1") or {}
    asks = [{"px": _rtf(o.get(f"askp{i}")), "qty": _rtf(o.get(f"askp_rsqn{i}"))} for i in range(1, 11)]
    bids = [{"px": _rtf(o.get(f"bidp{i}")), "qty": _rtf(o.get(f"bidp_rsqn{i}"))} for i in range(1, 11)]
    return {"ok": True, "code": code, "asks": asks, "bids": bids,
            "total_ask": _rtf(o.get("total_askp_rsqn")), "total_bid": _rtf(o.get("total_bidp_rsqn")),
            "ts": time.time(), "src": "rest"}


# ── 기능 2: 실시간 스크리너 (거래량/거래대금/거래증가율 순위) ──────────────────
def _rt_screener(mkt: str = "J", blng: str = "0", limit: int = 30) -> dict:
    j = _rt_kis_get("/uapi/domestic-stock/v1/quotations/volume-rank", "FHPST01710000", {
        "fid_cond_mrkt_div_code": mkt, "fid_cond_scr_div_code": "20171",
        "fid_input_iscd": "0000", "fid_div_cls_code": "0", "fid_blng_cls_code": blng,
        "fid_trgt_cls_code": "111111111", "fid_trgt_exls_cls_code": "0000000000",
        "fid_input_price_1": "", "fid_input_price_2": "", "fid_vol_cnt": "", "fid_input_date_1": ""})
    if not j:
        return {"ok": False, "needs_key": _kis_keys()[0] is None, "rows": []}
    rows = []
    for o in (j.get("output") or [])[:limit]:
        rows.append({"rank": o.get("data_rank"), "name": o.get("hts_kor_isnm"),
                     "code": o.get("mksc_shrn_iscd"), "price": _rtf(o.get("stck_prpr")),
                     "chg": _rtf(o.get("prdy_ctrt")), "vol": _rtf(o.get("acml_vol")),
                     "amt": _rtf(o.get("acml_tr_pbmn"))})
    return {"ok": True, "rows": rows, "ts": time.time()}


# ── 기능 3: 수급 플로우 (종목 투자자 + 프로그램매매) ──────────────────────────
def _rt_flows(code: str, mkt: str = "1") -> dict:
    out = {"ok": True, "ts": time.time(), "investor": [], "program": [],
           "needs_key": _kis_keys()[0] is None}
    if code and code.isdigit() and len(code) == 6:
        ji = _rt_kis_get("/uapi/domestic-stock/v1/quotations/inquire-investor",
                         "FHKST01010900", {"fid_cond_mrkt_div_code": _RT_J, "fid_input_iscd": code})
        if ji:
            for o in (ji.get("output") or [])[:10]:
                out["investor"].append({"date": o.get("stck_bsop_date"),
                                        "close": _rtf(o.get("stck_clpr")),
                                        "frgn": _rtf(o.get("frgn_ntby_qty")),
                                        "orgn": _rtf(o.get("orgn_ntby_qty")),
                                        "prsn": _rtf(o.get("prsn_ntby_qty"))})
    jp = _rt_kis_get("/uapi/domestic-stock/v1/quotations/investor-program-trade-today",
                     "HHPPG046600C1", {"MRKT_DIV_CLS_CODE": mkt})
    if jp:
        out["program"] = (jp.get("output1") or jp.get("output") or [])[:30]
    if not out["investor"] and not out["program"]:
        out["ok"] = False
    return out


# ── 기능 1(live): WS→SSE 브리지 — 코드별 백그라운드 스레드 ─────────────────────
_ASP_COLS = (["MKSC", "HOUR", "HCLS"] + [f"ASKP{i}" for i in range(1, 11)]
             + [f"BIDP{i}" for i in range(1, 11)] + [f"AR{i}" for i in range(1, 11)]
             + [f"BR{i}" for i in range(1, 11)] + ["TAR", "TBR"])


def _rt_apply_asp(code: str, rec: list[str]) -> None:
    d = dict(zip(_ASP_COLS, rec))
    asks = [{"px": _rtf(d.get(f"ASKP{i}")), "qty": _rtf(d.get(f"AR{i}"))} for i in range(1, 11)]
    bids = [{"px": _rtf(d.get(f"BIDP{i}")), "qty": _rtf(d.get(f"BR{i}"))} for i in range(1, 11)]
    with _RT_LOCK:
        st = _RT_STATE.setdefault(code, {})
        st["book"] = {"asks": asks, "bids": bids, "total_ask": _rtf(d.get("TAR")),
                      "total_bid": _rtf(d.get("TBR")), "ts": time.time(), "src": "ws"}


def _rt_apply_cnt(code: str, rec: list[str]) -> None:
    # H0STCNT0: idx1 시각, idx2 현재가, idx3 부호, idx12 체결량, idx18 체결강도, idx21 체결구분(1매수/5매도)
    if len(rec) < 22:
        return
    px = _rtf(rec[2]); vol = _rtf(rec[12]); cttr = _rtf(rec[18])
    side = "B" if str(rec[21]).strip() == "1" else "S"
    with _RT_LOCK:
        st = _RT_STATE.setdefault(code, {})
        tr = st.get("trades")
        if tr is None:
            tr = st["trades"] = deque(maxlen=400)
        tr.append({"t": rec[1], "px": px, "vol": vol, "side": side})
        st["cttr"] = cttr
        st["last"] = px
        st["sign"] = rec[3]


def _rt_ws_thread(code: str) -> None:
    """코드별 WS 스레드: H0STASP0(호가)+H0STCNT0(체결) 구독 → _RT_STATE 갱신."""
    async def run() -> None:
        import websockets
        approval = _kis_ws_approval()
        if not approval:
            with _RT_LOCK:
                _RT_STATE.setdefault(code, {})["ws_err"] = "no approval key"
            return

        def reg(tr: str) -> str:
            return json.dumps({"header": {"approval_key": approval, "custtype": "P",
                                          "tr_type": "1", "content-type": "utf-8"},
                               "body": {"input": {"tr_id": tr, "tr_key": code}}})

        def expired() -> bool:
            with _RT_LOCK:
                pt = _RT_STATE.get(code, {}).get("poll_ts", 0)
            return (time.time() - pt) > _RT_IDLE_STOP

        async def sub(tr: str, cols: int, apply) -> None:
            while not expired():
                try:
                    async with websockets.connect(_RT_WS_URL.format(tr=tr),
                                                   open_timeout=5, ping_interval=None) as ws:
                        await ws.send(reg(tr))
                        while not expired():
                            msg = await asyncio.wait_for(ws.recv(), timeout=15)
                            if not isinstance(msg, str):
                                continue
                            if msg[0] == "{":                       # PINGPONG/제어
                                if "PINGPONG" in msg:
                                    await ws.send(msg)
                                continue
                            if not msg.startswith("0|"):            # 1|=암호화(시세는 0|)
                                continue
                            p = msg.split("|")
                            if len(p) < 4:
                                continue
                            try:
                                n = int(p[2])
                            except Exception:  # noqa: BLE001
                                n = 1
                            f = p[3].split("^")
                            for k in range(max(n, 1)):
                                rec = f[k * cols:(k + 1) * cols]
                                if len(rec) >= cols:
                                    apply(code, rec)
                except asyncio.TimeoutError:
                    continue
                except Exception:  # noqa: BLE001
                    await asyncio.sleep(1.5)

        await asyncio.gather(sub("H0STASP0", len(_ASP_COLS), _rt_apply_asp),
                             sub("H0STCNT0", 46, _rt_apply_cnt))

    try:
        asyncio.run(run())
    except Exception:  # noqa: BLE001
        pass
    finally:
        with _RT_LOCK:
            st = _RT_STATE.get(code)
            if st:
                st["thread"] = None


def _rt_ensure_ws(code: str) -> None:
    """해당 코드 WS 스레드가 없으면 시작. 장중에만 의미(폐장 시 데이터 없음→REST 폴백)."""
    with _RT_LOCK:
        st = _RT_STATE.setdefault(code, {})
        st["poll_ts"] = time.time()
        if st.get("thread") and st["thread"].is_alive():
            return
        if not _kis_keys()[0]:
            return
        t = threading.Thread(target=_rt_ws_thread, args=(code,), daemon=True)
        st["thread"] = t
    t.start()


_RT_NAME_CACHE: dict[str, str] = {}


def _rt_stock_name(code: str) -> str:
    """종목코드 → 한글 종목명 (DART 상장사 목록 + ETF 스냅샷 폴백, 코드별 캐시)."""
    if code in _RT_NAME_CACHE:
        return _RT_NAME_CACHE[code]
    name = ""
    try:
        for c in company.get_corps():
            if c.get("stock_code") == code:
                name = c.get("corp_name") or ""
                break
    except Exception:  # noqa: BLE001
        pass
    if not name:
        try:
            _df, snap, _ld = etf.get_market()
            if snap is not None and not snap.empty:
                m = snap[snap["코드"].astype(str) == code]
                if not m.empty:
                    name = str(m.iloc[0]["종목명"])
        except Exception:  # noqa: BLE001
            pass
    if name:
        _RT_NAME_CACHE[code] = name
    return name or code


def _rt_stream_payload(code: str) -> dict:
    """SSE 1프레임: 호가 + 최근 체결 + 체결강도 + 매수/매도 불균형(numpy).

    기준가(base)·현재가(last)·전일대비(diff/rate)는 _kis_price(장 상태별 KRX/NXT/직전종가,
    캐시 0.8s/60s)로 시드 → WS 미체결(폐장·개장 전)에도 히어로/호가 % 가 정상 표시된다.
    """
    with _RT_LOCK:
        st = _RT_STATE.get(code, {})
        st["poll_ts"] = time.time()
        book = st.get("book")
        trades = list(st.get("trades") or [])[-200:]
        cttr = st.get("cttr", 0.0)
        last = st.get("last", 0.0)
        ws_err = st.get("ws_err")
    if book is None:                                    # WS 데이터 아직/폐장 → REST 1회 시드
        ob = _rt_orderbook(code)
        if ob.get("ok"):
            book = {"asks": ob["asks"], "bids": ob["bids"], "total_ask": ob["total_ask"],
                    "total_bid": ob["total_bid"], "ts": ob["ts"], "src": "rest"}
    # 기준가·현재가 보강 (전일 종가 = price - change)
    base = diff = rate = 0.0
    market_open = False
    phase = ""
    kp = _kis_price(code)
    if kp.get("ok"):
        kprice = float(kp.get("price") or 0)
        kchg = float(kp.get("change") or 0)
        base = kprice - kchg
        market_open = bool(kp.get("market_open"))
        phase = kp.get("phase", "")
        if last <= 0:                                   # WS 라이브 체결이 없으면 KIS 현재가/종가
            last = kprice
    if base > 0 and last > 0:
        diff = last - base
        rate = diff / base * 100.0
    elif kp.get("ok"):
        diff = float(kp.get("change") or 0)
        rate = float(kp.get("change_pct") or 0)
    buy_vol = sell_vol = 0.0
    if trades:
        import numpy as np
        vols = np.array([t["vol"] for t in trades], dtype=float)
        sides = np.array([1 if t["side"] == "B" else 0 for t in trades])
        buy_vol = float(vols[sides == 1].sum())
        sell_vol = float(vols[sides == 0].sum())
    tot = buy_vol + sell_vol
    imbalance = ((buy_vol - sell_vol) / tot) if tot else 0.0
    return {"ok": True, "code": code, "name": _rt_stock_name(code), "book": book, "trades": trades,
            "cttr": cttr, "last": last, "base": base,
            "diff": round(diff, 2), "rate": round(rate, 2),
            "market_open": market_open, "phase": phase,
            "buy_vol": buy_vol, "sell_vol": sell_vol,
            "imbalance": round(imbalance, 4), "ws_err": ws_err, "ts": time.time()}


# ── 기능 4: 페이퍼 트레이딩 (로컬 시뮬, SQLite) ───────────────────────────────
_PAPER_DB = _CACHE_DIR / "paper.db"
_PAPER_START_CASH = 100_000_000.0          # 1억 가상 현금
_PAPER_LOCK = threading.Lock()


def _paper_conn() -> sqlite3.Connection:
    c = sqlite3.connect(_PAPER_DB)
    c.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS pos(code TEXT PRIMARY KEY, qty REAL, avg REAL, name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              " ts REAL, code TEXT, name TEXT, side TEXT, qty REAL, px REAL)")
    if c.execute("SELECT v FROM meta WHERE k='cash'").fetchone() is None:
        c.execute("INSERT INTO meta(k, v) VALUES('cash', ?)", (_PAPER_START_CASH,))
        c.commit()
    return c


def _paper_mark(code: str) -> float:
    p = _kis_price(code)
    return _rtf(p.get("price")) if p.get("ok") else 0.0


def _paper_state() -> dict:
    with _PAPER_LOCK:
        c = _paper_conn()
        cash = c.execute("SELECT v FROM meta WHERE k='cash'").fetchone()[0]
        positions, mv = [], 0.0
        for code, qty, avg, name in c.execute("SELECT code, qty, avg, name FROM pos WHERE qty>0"):
            mk = _paper_mark(code) or avg
            val = mk * qty
            mv += val
            positions.append({"code": code, "name": name or code, "qty": qty, "avg": avg,
                              "mark": mk, "value": val, "pnl": (mk - avg) * qty,
                              "pnl_pct": ((mk / avg - 1) * 100 if avg else 0.0)})
        recent = [{"ts": ts, "code": cd, "name": nm, "side": sd, "qty": q, "px": px}
                  for ts, cd, nm, sd, q, px in c.execute(
                      "SELECT ts, code, name, side, qty, px FROM trades ORDER BY id DESC LIMIT 30")]
        c.close()
    equity = cash + mv
    return {"ok": True, "cash": cash, "market_value": mv, "equity": equity,
            "pnl_total": equity - _PAPER_START_CASH, "start_cash": _PAPER_START_CASH,
            "positions": positions, "trades": recent}


def _paper_order(code: str, side: str, qty: float, name: str = "") -> dict:
    code = (code or "").strip()
    side = (side or "").upper()
    if not (code.isdigit() and len(code) == 6) or side not in ("BUY", "SELL") or qty <= 0:
        return {"ok": False, "msg": "invalid order"}
    px = _paper_mark(code)
    if px <= 0:
        return {"ok": False, "msg": "체결가를 가져올 수 없습니다 (시세 없음)"}
    with _PAPER_LOCK:
        c = _paper_conn()
        cash = c.execute("SELECT v FROM meta WHERE k='cash'").fetchone()[0]
        row = c.execute("SELECT qty, avg, name FROM pos WHERE code=?", (code,)).fetchone()
        cur_qty, cur_avg, cur_name = (row if row else (0.0, 0.0, name))
        if side == "BUY":
            cost = px * qty
            if cost > cash:
                c.close()
                return {"ok": False, "msg": "현금 부족"}
            new_qty = cur_qty + qty
            new_avg = (cur_avg * cur_qty + cost) / new_qty
            c.execute("INSERT INTO pos(code, qty, avg, name) VALUES(?,?,?,?)"
                      " ON CONFLICT(code) DO UPDATE SET qty=?, avg=?, name=COALESCE(?,name)",
                      (code, new_qty, new_avg, name or cur_name, new_qty, new_avg, name or cur_name))
            c.execute("UPDATE meta SET v=? WHERE k='cash'", (cash - cost,))
        else:
            if qty > cur_qty:
                c.close()
                return {"ok": False, "msg": "보유 수량 부족"}
            c.execute("UPDATE pos SET qty=? WHERE code=?", (cur_qty - qty, code))
            c.execute("UPDATE meta SET v=? WHERE k='cash'", (cash + px * qty,))
        c.execute("INSERT INTO trades(ts, code, name, side, qty, px) VALUES(?,?,?,?,?,?)",
                  (time.time(), code, name or cur_name, side, qty, px))
        c.commit()
        c.close()
    return {"ok": True, "fill_px": px, "side": side, "qty": qty, "code": code}


def _paper_reset() -> dict:
    with _PAPER_LOCK:
        c = _paper_conn()
        c.execute("DELETE FROM pos")
        c.execute("DELETE FROM trades")
        c.execute("UPDATE meta SET v=? WHERE k='cash'", (_PAPER_START_CASH,))
        c.commit()
        c.close()
    return {"ok": True}


# ── 실시간 트레이딩 데스크 페이지 (iframe — trap#1/#12: 명시 색 + 자체 body bg + 테마 동기화) ──


# ── 실시간 트레이딩 라우트 ────────────────────────────────────────────────────
@app.get("/api/rt/history")
def api_rt_history() -> Response:
    """일별 OHLCV (실시간 페이지 차트용) — SSD parquet 캐시 우선."""
    code = request.args.get("code", "005930").strip()
    days = min(max(int(request.args.get("days", "80")), 20), 240)
    if not (code.isdigit() and len(code) == 6):
        return jsonify({"ok": False, "rows": []})
    rows = asyncio.run(_afetch(code, days))
    out = [{"d": r.get("일자"), "o": r.get("시가"), "h": r.get("고가"),
            "l": r.get("저가"), "c": r.get("종가"), "v": r.get("거래량")}
           for r in rows if r.get("종가")]
    return jsonify({"ok": bool(out), "rows": out, "code": code})


@app.get("/api/rt/orderbook")
def api_rt_orderbook() -> Response:
    return jsonify(_rt_orderbook(request.args.get("code", "").strip()))


@app.get("/api/rt/stream")
def api_rt_stream() -> Response:
    code = request.args.get("code", "").strip()          # trap#2: read OUTSIDE generator

    def gen():
        if not (code.isdigit() and len(code) == 6):
            yield f"data: {json.dumps({'ok': False, 'msg': 'invalid code'})}\n\n"
            return
        _rt_ensure_ws(code)
        for _ in range(2400):                            # ~10분 상한(0.25s*2400)
            try:
                yield f"data: {json.dumps(_rt_stream_payload(code))}\n\n"
            except GeneratorExit:
                return
            time.sleep(0.25)

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/rt/screener")
def api_rt_screener() -> Response:
    return jsonify(_rt_screener(request.args.get("mkt", "J"), request.args.get("blng", "0")))


@app.get("/api/rt/flows")
def api_rt_flows() -> Response:
    return jsonify(_rt_flows(request.args.get("code", "").strip(), request.args.get("mkt", "1")))


@app.get("/api/paper/state")
def api_paper_state() -> Response:
    return jsonify(_paper_state())


@app.post("/api/paper/order")
def api_paper_order() -> Response:
    d = request.get_json(silent=True) or {}              # trap#2: read body in view fn
    return jsonify(_paper_order(str(d.get("code", "")), str(d.get("side", "")),
                                _rtf(d.get("qty")), str(d.get("name", ""))))


@app.post("/api/paper/reset")
def api_paper_reset() -> Response:
    return jsonify(_paper_reset())


@app.get("/realtime_page")
def realtime_page() -> Response:
    return Response(_REALTIME_HTML, mimetype="text/html")


# ── 세계 시장 (작업2) 라우트 + 페이지 ──────────────────────────────────────────
@app.get("/api/world")
def api_world() -> Response:
    return jsonify(_world_snapshot())


# ── 세계 상세 차트 (작업6) — 지수 캔들(일/주/월) · 환율 일별 라인 ────────────────
def _world_chart(kind: str, code: str, period: str = "day") -> dict:
    try:
        if kind == "index":
            pt = {"day": "dayCandle", "week": "weekCandle", "month": "monthCandle"}.get(period, "dayCandle")
            r = httpx.get(f"https://api.stock.naver.com/chart/foreign/index/{code}",
                          timeout=8, headers=_WORLD_UA, params={"periodType": pt})
            rows = [{"d": p.get("localDate"), "o": p.get("openPrice"), "h": p.get("highPrice"),
                     "l": p.get("lowPrice"), "c": p.get("closePrice"),
                     "v": p.get("accumulatedTradingVolume") or 0}
                    for p in (r.json() or {}).get("priceInfos", []) if p.get("closePrice")]
            return {"ok": bool(rows), "kind": "index", "rows": rows}
        if kind == "fx":
            rows: list[dict] = []
            for pg in range(1, 6):                    # 60건 × 5p ≈ 14개월 (pageSize 한도 60)
                r = httpx.get(f"https://api.stock.naver.com/marketindex/exchange/{code}/prices",
                              timeout=8, headers=_WORLD_UA, params={"page": pg, "pageSize": 60})
                chunk = r.json() or []
                if not chunk:
                    break
                for p in chunk:
                    rows.append({"d": p.get("localTradedAt"), "c": _rtf(p.get("closePrice")),
                                 "chg": _rtf(p.get("fluctuations")), "pct": _rtf(p.get("fluctuationsRatio")),
                                 "dir": _world_sign_dir((p.get("fluctuationsType") or {}).get("code")),
                                 "cash_buy": p.get("cashBuyValue"), "cash_sell": p.get("cashSellValue")})
                if len(chunk) < 60:
                    break
            rows.reverse()                            # 과거→최신
            return {"ok": bool(rows), "kind": "fx", "rows": rows}
    except Exception:  # noqa: BLE001
        pass
    return {"ok": False, "rows": []}


@app.get("/api/world/chart")
def api_world_chart() -> Response:
    return jsonify(_world_chart((request.args.get("kind") or "").strip(),
                                (request.args.get("code") or "").strip(),
                                (request.args.get("period") or "day").strip()))


@app.get("/api/world/spark")
def api_world_spark() -> Response:
    """세계 시장 카드 미니 차트의 기간 토글용 OHLC(최근 60봉). 작업3.
    kind=dom → 국내 지수(_index_chart, D/W/M) / 그 외 → 해외 지수(_world_chart, day/week/month)."""
    kind = (request.args.get("kind") or "index").strip()
    code = (request.args.get("code") or "").strip()
    period = (request.args.get("period") or "day").strip().lower()
    if kind == "dom":
        pmap = {"day": "D", "week": "W", "month": "M"}
        ic = _index_chart(code or "0001", pmap.get(period, "D"))
        rows = [r for r in ic.get("rows", [])[-60:] if r.get("c")]
    else:
        per = period if period in ("day", "week", "month") else "day"
        ch = _world_chart("index", code, per)
        rows = [r for r in ch.get("rows", [])[-60:] if r.get("c")]
    return jsonify({"d": [r.get("d") for r in rows], "o": [r.get("o") for r in rows],
                    "h": [r.get("h") for r in rows], "l": [r.get("l") for r in rows],
                    "c": [r.get("c") for r in rows]})


@app.get("/world_detail")
def world_detail_page() -> Response:
    return Response(_WORLD_DETAIL_HTML, mimetype="text/html")




# ════════════════ 세계 시장 3뷰 (국내/미국/글로벌) — 작업1 네이버식 ════════════════
_WORLDVIEW_CACHE: dict = {}
_WORLDVIEW_TTL = 30.0
_WV_US_IDX = [(".DJI", "다우존스"), (".IXIC", "나스닥 종합"), (".INX", "S&P 500")]
_WV_GLOBAL_IDX = [(".SSEC", "🇨🇳 중국", "상해종합"), (".HSI", "🇭🇰 홍콩", "항셍"),
                  (".N225", "🇯🇵 일본", "니케이225"), (".STOXX50E", "🇪🇺 유럽", "유로스톡스50"),
                  (".GDAXI", "🇩🇪 독일", "독일 DAX"), (".BVSP", "🇧🇷 브라질", "브라질 BOVESPA")]


def _wv_spark(code: str) -> dict:
    """카드 미니 차트용 OHLC(최근 60봉) — 국내 종목과 동일한 캔들 차트 툴로 렌더."""
    try:
        ch = _world_chart("index", code, "day")
        rows = [r for r in ch.get("rows", [])[-60:] if r.get("c")]
        return {"d": [r.get("d") for r in rows], "o": [r.get("o") for r in rows],
                "h": [r.get("h") for r in rows], "l": [r.get("l") for r in rows],
                "c": [r["c"] for r in rows]}
    except Exception:  # noqa: BLE001
        return {"d": [], "o": [], "h": [], "l": [], "c": []}


def _wv_idx_card(code: str, region: str, name: str) -> dict | None:
    o = _world_index_one(code, region)
    if not o:
        return None
    return {"name": name, "region": region, "value": o["price"], "chg": o["chg"],
            "pct": o["pct"], "dir": o["dir"], "status": o.get("status", ""),
            "phase": o.get("phase", ""), "code": code, "info": o.get("info")}


def _gmac_row(rows: list, key: str) -> dict | None:
    for r in rows:
        if r.get("key") == key:
            return r
    return None


def _kpi(name: str, value, pct, dr) -> dict:
    return {"name": name, "value": value, "pct": pct, "dir": dr}


def _market_ai_text() -> str:
    """국내 시장 개요 화면(홈·시장·섹터·실시간·백테스트 배경)에 표시되는 핵심 데이터를 AI 컨텍스트로."""
    arr = {"up": "▲", "down": "▼", "flat": "-"}
    out = ["[국내 시장 개요]"]
    try:
        kp = _world_domestic_one("0001", "코스피", "🇰🇷")
        kq = _world_domestic_one("1001", "코스닥", "🇰🇷")
        if kp:
            out.append(f"· 코스피 {kp['price']} {arr.get(kp['dir'], '')}{kp['pct']}%")
        if kq:
            out.append(f"· 코스닥 {kq['price']} {arr.get(kq['dir'], '')}{kq['pct']}%")
    except Exception:  # noqa: BLE001
        pass
    try:
        rows = _sector_stocks("0001")[:20]
        if rows:
            out.append(f"· 시총 상위 종목 {len(rows)}:")
            for s in rows:
                out.append(f"  - {s.get('name', '')}({s.get('code', '')}) {s.get('price', '')} "
                           f"({s.get('change_pct', '')}%)")
    except Exception:  # noqa: BLE001
        pass
    if len(out) == 1:
        out.append("데이터 없음")
    return "\n".join(out)


def _world_ai_text(view: str) -> str:
    """세계 시장 화면(국내/미국/글로벌)에 *지금 표시된* 데이터를 AI 컨텍스트 텍스트로 직렬화.
    화면을 그대로 읽어 답하게 하려는 목적 — 지수 카드·KPI·종목 리스트(마켓맵)를 압축한다."""
    try:
        d = _world_view(view)
    except Exception:  # noqa: BLE001
        return "[세계 시장 화면] 데이터 없음"
    vlabel = {"kr": "국내", "us": "미국", "global": "글로벌"}.get(view, view)
    arr = {"up": "▲", "down": "▼", "flat": "-"}
    out = [f"[세계 시장 화면 — {vlabel}] 기준 {d.get('asof', '')}"]
    cards = d.get("cards", [])
    if cards:
        out.append("· 주요 지수:")
        for c in cards:
            a = arr.get(c.get("dir"), "")
            st = c.get("status") or ""
            out.append(f"  - {c.get('name', '')}: {c.get('value', '')} {a}{c.get('pct', '')}%"
                       + (f" ({st})" if st else ""))
    kpis = d.get("kpis", [])
    if kpis:
        out.append("· 지표: " + ", ".join(
            f"{k.get('name', '')} {k.get('value', '')}({arr.get(k.get('dir'), '')}{k.get('pct', '')}%)"
            for k in kpis))
    rows = (d.get("list") or {}).get("rows", [])
    if rows:
        out.append(f"· 종목 리스트(시총 상위 {min(len(rows), 20)}):")
        for r in rows[:20]:
            seg = f"{r.get('name', '')} {r.get('price', '')}"
            if r.get("pct") is not None:
                seg += f"({r.get('pct')}%)"
            if r.get("sector"):
                seg += f" {r.get('sector')}"
            out.append("  - " + seg)
    return "\n".join(out)


def _world_view(view: str) -> dict:
    view = view if view in ("kr", "us", "global") else "us"
    c = _WORLDVIEW_CACHE.get(view)
    if c and (time.time() - c[1]) < _WORLDVIEW_TTL:
        return c[0]
    g = _global_macro_snapshot()
    grows = g.get("rows", []) if g.get("ok") else []
    cards: list = []; kpis: list = []; lst: dict = {"cols": [], "rows": [], "kind": view}

    if view == "us":
        with _TPE(max_workers=6) as ex:
            cf = {code: ex.submit(_wv_idx_card, code, "🇺🇸 미국", nm) for code, nm in _WV_US_IDX}
            sf = {code: ex.submit(_wv_spark, code) for code, nm in _WV_US_IDX}
            for code, nm in _WV_US_IDX:
                card = cf[code].result()
                if card:
                    card["spark"] = sf[code].result(); cards.append(card)
        vix = _world_index_one(".VIX", "미국"); ndx = _world_index_one(".NDX", "미국")
        if vix:
            kpis.append(_kpi("VIX", vix["price"], vix["pct"], vix["dir"]))
        if ndx:
            kpis.append(_kpi("나스닥100", ndx["price"], ndx["pct"], ndx["dir"]))
        dxy = _gmac_row(grows, "달러인덱스"); us10 = _gmac_row(grows, "미국 국채 10년")
        if dxy:
            kpis.append(_kpi("달러인덱스", dxy["price"], dxy["pct"], dxy["dir"]))
        if us10:
            kpis.append(_kpi("미국 10년물", us10["price"] + "%", us10["pct"], us10["dir"]))
        q = _usmap_pct()
        meta = {t: (sec, w) for sec, l in _US_HEATMAP.items() for (t, _e, w) in l}
        rows = [{"name": t, "price": q[t]["c"], "pct": q[t]["dp"],
                 "sector": _US_SECTOR_KR.get(meta[t][0], meta[t][0]), "mcap": meta[t][1]}
                for t in meta if t in q]
        rows.sort(key=lambda x: -x["mcap"])
        lst = {"cols": ["종목명", "현재가", "전일대비", "업종", "시가총액"], "rows": rows[:40], "kind": "us"}

    elif view == "global":
        with _TPE(max_workers=6) as ex:
            cf = {code: ex.submit(_wv_idx_card, code, rg, nm) for code, rg, nm in _WV_GLOBAL_IDX}
            sf = {code: ex.submit(_wv_spark, code) for code, rg, nm in _WV_GLOBAL_IDX}
            for code, rg, nm in _WV_GLOBAL_IDX:
                card = cf[code].result()
                if card:
                    card["spark"] = sf[code].result(); cards.append(card)
        ws = _world_snapshot()
        for fx in ws.get("fx", []):
            if fx.get("pair") == "FX_USDKRW":
                kpis.append(_kpi("미국 USD", fx["price"], fx["pct"], fx["dir"]))
        for key, lab in [("달러인덱스", "달러인덱스"), ("국제 금", "국제 금"), ("WTI 유가", "WTI")]:
            r = _gmac_row(grows, key)
            if r:
                kpis.append(_kpi(lab, r["price"], r["pct"], r["dir"]))
        kp = _world_domestic_one("0001", "코스피", "🇰🇷"); kq = _world_domestic_one("1001", "코스닥", "🇰🇷")
        if kp:
            kpis.append(_kpi("코스피", kp["price"], kp["pct"], kp["dir"]))
        if kq:
            kpis.append(_kpi("코스닥", kq["price"], kq["pct"], kq["dir"]))
        lst = {"cols": [], "rows": [], "kind": "global"}

    else:  # kr
        kp = _world_domestic_one("0001", "코스피", "🇰🇷 한국")
        kq = _world_domestic_one("1001", "코스닥", "🇰🇷 한국")

        def _dom_chart_info(iscd):
            ic = _index_chart(iscd, "D")
            rows = ic.get("rows", [])
            srows = [r for r in rows[-60:] if r.get("c")]
            spark = {"d": [r.get("d") for r in srows], "o": [r.get("o") for r in srows],
                     "h": [r.get("h") for r in srows], "l": [r.get("l") for r in srows],
                     "c": [r["c"] for r in srows]}
            last = rows[-1] if rows else {}

            def _f(v):
                return f"{_rtf(v):,.2f}" if v else None
            info = {"prev": _f(ic.get("prev_close")), "open": _f(last.get("o")),
                    "high": _f(last.get("h")), "low": _f(last.get("l")),
                    "hi52": _f(ic.get("hi52")), "lo52": _f(ic.get("lo52"))}
            return spark, info
        with _TPE(max_workers=2) as ex:
            fp = ex.submit(_dom_chart_info, "0001")
            fq = ex.submit(_dom_chart_info, "1001")
            if kp:
                sp, ip = fp.result(); kp["value"] = kp.get("price"); kp["spark"] = sp; kp["info"] = ip; cards.append(kp)
            if kq:
                sq, iq = fq.result(); kq["value"] = kq.get("price"); kq["spark"] = sq; kq["info"] = iq; cards.append(kq)
        k200 = _kis_index("2001")
        if k200.get("ok"):
            cp = k200.get("change_pct", 0.0)
            kpis.append(_kpi("코스피200", f"{_rtf(k200.get('value')):,.2f}", f"{cp:.2f}",
                             "up" if cp > 0 else ("down" if cp < 0 else "flat")))
        ws = _world_snapshot()
        for fx in ws.get("fx", []):
            if fx.get("pair") == "FX_USDKRW":
                kpis.append(_kpi("미국 USD", fx["price"], fx["pct"], fx["dir"]))
        for key, lab in [("달러인덱스", "달러인덱스"), ("국제 금", "국제 금"), ("WTI 유가", "WTI")]:
            r = _gmac_row(grows, key)
            if r:
                kpis.append(_kpi(lab, r["price"], r["pct"], r["dir"]))
        rows = [{"code": s["code"], "name": s["name"], "price": s["price"],
                 "pct": s["change_pct"], "volume": s["volume"], "mcap": s["mcap"]}
                for s in _sector_stocks("0001")[:40]]
        lst = {"cols": ["종목명", "현재가", "전일대비", "거래량", "시가총액"], "rows": rows, "kind": "kr"}

    data = {"ok": True, "view": view, "cards": cards, "kpis": kpis, "list": lst,
            "asof": time.strftime("%m.%d %H:%M")}
    _WORLDVIEW_CACHE[view] = (data, time.time())
    return data


@app.get("/api/world_view")
def api_world_view() -> Response:
    return jsonify(_world_view((request.args.get("view") or "us").strip()))


_POLY_GROUPED_CACHE: dict = {}
_US_ETF_EXCLUDE = {"SPY", "QQQ", "IWM", "VOO", "VTI", "DIA", "EEM", "EFA", "VEA", "IVV",
                   "XLF", "XLK", "XLE", "XLV", "XLY", "XLI", "XLU", "XLP", "XLB", "XLRE", "XLC",
                   "GLD", "SLV", "TLT", "HYG", "LQD", "SOXL", "SOXS", "TQQQ", "SQQQ", "TNA",
                   "UVXY", "VXX", "SPXL", "SPXS", "ARKK", "SMH", "VUG", "VTV", "SCHD", "JEPI",
                   "BITO", "USO", "UNG", "FXI", "KWEB", "EWZ", "EWJ", "INDA", "VWO", "AGG", "BND"}


def _polygon_grouped_one(date_str: str):
    """Polygon grouped-daily(전 미국종목 OHLCV) — {ticker:{c,v,o}}. 1시간 캐시(EOD)."""
    key = os.environ.get("POLYGON_KEY", "")
    if not key:
        return None
    c = _POLY_GROUPED_CACHE.get(date_str)
    if c and (time.time() - c[1]) < 3600.0:
        return c[0]
    try:
        r = httpx.get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
                      f"?adjusted=true&apiKey={key}", timeout=25)
        j = r.json()
        if j.get("status") not in ("OK", "DELAYED") or not j.get("results"):
            return None
        d = {x["T"]: x for x in j["results"] if x.get("T")}
        _POLY_GROUPED_CACHE[date_str] = (d, time.time())
        return d
    except Exception:  # noqa: BLE001
        return None


def _polygon_turnover(n: int = 40) -> list[dict]:
    """진짜 거래대금(종가×거래량) 상위 — Polygon grouped 최근 2거래일로 등락까지 산출."""
    from datetime import date as _date, timedelta as _td
    got = []
    dd = _date.today()
    for _ in range(8):
        dd = dd - _td(days=1)
        if dd.weekday() >= 5:
            continue
        g = _polygon_grouped_one(dd.isoformat())
        if g:
            got.append(g)
        if len(got) >= 2:
            break
    if not got:
        return []
    cur, prev = got[0], (got[1] if len(got) > 1 else {})
    rows = []
    for t, x in cur.items():
        if not t.isalpha() or len(t) > 5:        # 보통주만(우선주·워런트 티커 잡음 제거)
            continue
        if t in _US_ETF_EXCLUDE:                  # 대표 ETF 제외(주식 리스트용)
            continue
        c, v = x.get("c", 0), x.get("v", 0)
        if c < 5 or v <= 0:                       # 페니주 제거
            continue
        pc = (prev.get(t) or {}).get("c")
        rows.append({"name": t, "price": c, "pct": ((c - pc) / pc * 100) if pc else 0.0,
                     "turnover": c * v, "volume": v})
    rows.sort(key=lambda r: -r["turnover"])
    return rows[:n]


def _us_stock_list(filt: str) -> list[dict]:
    """미국 종목 리스트 — 거래대금(Polygon 종가×거래량)·상승/하락(FMP movers, 페니 제거)·시총(큐레이션)."""
    filt = filt if filt in ("actives", "gainers", "losers", "mcap") else "actives"
    if filt == "mcap":
        q = _usmap_pct()
        meta = {t: (sec, w) for sec, l in _US_HEATMAP.items() for (t, _e, w) in l}
        rows = [{"name": t, "price": q[t]["c"], "pct": q[t]["dp"],
                 "sector": _US_SECTOR_KR.get(meta[t][0], meta[t][0]), "mcap": meta[t][1] * 1e9}
                for t in meta if t in q]
        rows.sort(key=lambda x: -x["mcap"])
        return rows[:40]
    if filt == "actives":
        rows = _polygon_turnover(40)
        if rows:
            return rows
        # 폴백: FMP most-actives
        filt = "actives_fmp"
    path = {"gainers": "biggest-gainers", "losers": "biggest-losers",
            "actives_fmp": "most-actives"}.get(filt, "most-actives")
    data = _fmp_get(path, 120) or []
    out = []
    for it in (data if isinstance(data, list) else []):
        try:
            if float(it.get("price") or 0) < 5:    # 페니주·잡주 제거
                continue
        except (TypeError, ValueError):
            continue
        out.append({"name": it.get("symbol"), "company": it.get("name", ""),
                    "price": it.get("price"), "pct": it.get("changesPercentage"), "exch": it.get("exchange", "")})
        if len(out) >= 40:
            break
    return out


@app.get("/api/us_list")
def api_us_list() -> Response:
    return jsonify({"ok": True, "rows": _us_stock_list((request.args.get("filter") or "actives").strip())})


# ── 글로벌 국가별 종목 (KIS 해외 — 이미 통합) — 작업1 ──
# (excd, symb, 한글명) 큐레이션. KIS 해외시세 _ov_price 가 홍콩·중국·일본·베트남 모두 지원.
_GLOBAL_STOCKS = {
    "cn": ("🇨🇳 중국", "元", [
        ("SHS", "600519", "귀주모태"), ("SZS", "300750", "CATL"), ("SZS", "002594", "BYD"),
        ("SHS", "601398", "공상은행"), ("SHS", "600036", "초상은행"), ("SZS", "000858", "우량예"),
        ("SHS", "601318", "평안보험"), ("SHS", "600900", "창장전력"), ("SZS", "000333", "메이디"),
        ("SHS", "600276", "항서제약"), ("SHS", "601899", "쯔진광업"), ("SHS", "688041", "하이광정보")]),
    "hk": ("🇭🇰 홍콩", "HK$", [
        ("HKS", "00700", "텐센트"), ("HKS", "09988", "알리바바"), ("HKS", "03690", "메이퇀"),
        ("HKS", "00939", "건설은행"), ("HKS", "01299", "AIA"), ("HKS", "00941", "차이나모바일"),
        ("HKS", "09618", "JD닷컴"), ("HKS", "01810", "샤오미"), ("HKS", "00388", "홍콩거래소"),
        ("HKS", "01211", "BYD(H)"), ("HKS", "02318", "평안보험(H)"), ("HKS", "09999", "넷이즈")]),
    "jp": ("🇯🇵 일본", "¥", [
        ("TSE", "7203", "토요타"), ("TSE", "6758", "소니"), ("TSE", "9984", "소프트뱅크그룹"),
        ("TSE", "8306", "미쓰비시UFJ"), ("TSE", "6861", "키엔스"), ("TSE", "9983", "패스트리테일링"),
        ("TSE", "6098", "리크루트"), ("TSE", "8035", "도쿄일렉트론"), ("TSE", "7974", "닌텐도"),
        ("TSE", "6501", "히타치"), ("TSE", "4063", "신에쓰화학"), ("TSE", "9433", "KDDI")]),
    "vn": ("🇻🇳 베트남", "₫", [
        ("HSX", "VIC", "빈그룹"), ("HSX", "VHM", "빈홈즈"), ("HSX", "VCB", "베트콤뱅크"),
        ("HSX", "HPG", "호아팟"), ("HSX", "FPT", "FPT"), ("HSX", "VNM", "비나밀크"),
        ("HSX", "MSN", "마산그룹"), ("HSX", "GAS", "페트로베트남가스"), ("HSX", "VRE", "빈컴리테일"),
        ("HSX", "MWG", "모바일월드")]),
}
_GLOBAL_LIST_CACHE: dict = {}


def _global_country_list(country: str) -> dict:
    country = country if country in _GLOBAL_STOCKS else "cn"
    c = _GLOBAL_LIST_CACHE.get(country)
    if c and (time.time() - c[1]) < 60.0:
        return c[0]
    label, ccy, names = _GLOBAL_STOCKS[country]
    rows = []
    with _TPE(max_workers=5) as ex:
        futs = {ex.submit(_ov_price, excd, symb): (excd, symb, nm) for excd, symb, nm in names}
        for fut in futs:
            excd, symb, nm = futs[fut]
            try:
                p = fut.result()
            except Exception:  # noqa: BLE001
                p = None
            if p and p.get("last"):
                rows.append({"name": nm, "symb": symb, "excd": excd,
                             "price": p.get("last"), "pct": p.get("rate", 0.0), "ccy": ccy})
    # 표시는 큐레이션 순서 유지
    order = {s: i for i, (_e, s, _n) in enumerate(names)}
    rows.sort(key=lambda r: order.get(r["symb"], 99))
    out = {"ok": True, "country": country, "label": label, "rows": rows}
    if rows:
        _GLOBAL_LIST_CACHE[country] = (out, time.time())
    return out


@app.get("/api/global_list")
def api_global_list() -> Response:
    return jsonify(_global_country_list((request.args.get("country") or "cn").strip()))


@app.get("/world_page")
def world_page() -> Response:
    return Response(_WORLD_HTML, mimetype="text/html")




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


# ════════════════ 공통 로딩 애니메이션 일괄 적용 (작업3) ════════════════
# 각 페이지의 정적 텍스트 로더("…불러오는 중…")를 _loader_html() 스피너로 교체하고
# _LOADER_CSS 를 <head> 에 주입한다. .replace() 는 문자열이 없으면 무해한 no-op 이라
# 마크업이 바뀌어도 깨지지 않는다. 새 페이지 추가 시 여기 한 줄만 더 넣으면 된다.
def _inject_loader(html: str, swaps: list[tuple[str, str]]) -> str:
    if "kmkt-loader-css" not in html:
        if "</head>" in html:
            html = html.replace("</head>", _LOADER_CSS + "</head>", 1)
        else:
            logger.warning("_inject_loader: </head> anchor not found — loader CSS injection skipped")
    for old, new in swaps:
        if old not in html:
            logger.warning("_inject_loader: swap target not found — loader markup not applied: %.60r", old)
            continue
        html = html.replace(old, new)
    return html


def _state_loader(old_div: str, text: str) -> tuple[str, str]:
    """`<div id="state" class="state">텍스트</div>` → 스피너를 div 안에 넣어 교체.
    JS 가 #state 를 display:none 으로 숨기거나 .textContent 로 에러를 쓰는 동작은 유지."""
    return (old_div, f'<div id="state" class="state">{_loader_html(text)}</div>')


_SECTOR_HTML = _inject_loader(_SECTOR_HTML, [
    ('<div class="empty-note">업종 지수를 불러오는 중…</div>',
     _loader_html("업종 지수를 불러오는 중…", sm=True))])

_MARKET_HTML = _inject_loader(_MARKET_HTML, [
    ('<div class="mapempty">마켓맵 불러오는 중…</div>', _loader_html("마켓맵 불러오는 중…", sm=True)),
    ('<div class="empty-note">불러오는 중…</div>', _loader_html("불러오는 중…", sm=True))])

_INDEX_HTML = _inject_loader(_INDEX_HTML, [
    _state_loader('<div id="state" class="state">지수 정보를 불러오는 중…</div>', "지수 정보를 불러오는 중…")])

_MACRO_HTML = _inject_loader(_MACRO_HTML, [
    _state_loader('<div id="state" class="state">경제 지표를 불러오는 중…</div>', "경제 지표를 불러오는 중…")])

_OVERSEAS_HTML = _inject_loader(_OVERSEAS_HTML, [
    _state_loader('<div id="state" class="state">해외 종목 정보를 불러오는 중…</div>', "해외 종목 정보를 불러오는 중…")])

_WORLD_DETAIL_HTML = _inject_loader(_WORLD_DETAIL_HTML, [
    _state_loader('<div id="state" class="state">차트 데이터를 불러오는 중…</div>', "차트 데이터를 불러오는 중…")])

_WORLD_HTML = _inject_loader(_WORLD_HTML, [
    _state_loader('<div id="state" class="state">세계 시장 데이터를 불러오는 중…</div>', "세계 시장 데이터를 불러오는 중…")])

# 백테스터: CSS 만 주입(계산 중 로더는 JS 에서 _loader_html 마크업을 직접 출력 — 아래 별도 수정)
_BACKTEST_HTML = _inject_loader(_BACKTEST_HTML, [])

# 실시간 데스크: 호가/스크리너 패널 초기 로더
_REALTIME_HTML = _inject_loader(_REALTIME_HTML, [
    ('<div id="flowWrap"><div class="note">불러오는 중…</div></div>',
     '<div id="flowWrap">' + _loader_html("불러오는 중…", sm=True) + '</div>'),
    ('<div id="scrWrap"><div class="note">불러오는 중…</div></div>',
     '<div id="scrWrap">' + _loader_html("불러오는 중…", sm=True) + '</div>')])


# ── 플로팅 'AI 질문하기' 위젯 주입: 해외·거시·지수 페이지 (작업2) ──
# position:fixed 위젯이라 transform 조상 아래에서 깨지지 않도록 모두 </body> 직속에 삽입한다.
# 해외 페이지는 render() 안에서 자체적으로 window.KMKT_ASK 를 설정하므로 setter 불필요.
_OVERSEAS_HTML = _OVERSEAS_HTML.replace("__KMKT_ASK_WIDGET__", "", 1)
_OVERSEAS_HTML = _OVERSEAS_HTML.replace("</body>", _ASK_WIDGET_HTML + "</body>", 1)
_MACRO_HTML = _MACRO_HTML.replace(
    "</body>",
    "<script>window.KMKT_ASK=function(){return{scope:'macro'};};</script>"
    + _ASK_WIDGET_HTML + "</body>", 1)
_INDEX_HTML = _INDEX_HTML.replace(
    "</body>",
    "<script>window.KMKT_ASK=function(){return{scope:'index',"
    "id:new URLSearchParams(location.search).get('code')||'0001'};};</script>"
    + _ASK_WIDGET_HTML + "</body>", 1)
_RESEARCH_HTML = _RESEARCH_HTML.replace(
    "</body>",
    "<script>window.KMKT_ASK=function(){return{scope:'research',"
    "id:(typeof cat!=='undefined'?cat:'daily')};};</script>"
    + _ASK_WIDGET_HTML + "</body>", 1)


def _inject_floating_ai(html: str, scope: str) -> str:
    """플로팅 'AI 질문하기' 위젯을 임의 페이지 </body> 직속에 1회 주입(작업2 — 모든 화면 지원)."""
    if "kmktAiFab" in html:                       # 이미 있으면 스킵(중복 FAB 방지)
        return html
    block = ("<script>window.KMKT_ASK=function(){return{scope:'%s'};};</script>" % scope) + _ASK_WIDGET_HTML
    i = html.rfind("</body>")
    if i == -1:
        logger.warning("_inject_floating_ai: </body> anchor not found (scope=%s) — widget appended at end of document", scope)
        return html + block
    return html[:i] + block + html[i:]


# ── AI 질문 위젯을 모든 콘텐츠 화면에 주입 (작업2) ──
# (랜딩 top-frame 은 제외 — 콘텐츠는 iframe 이라 각자 FAB 를 가지면 중복 안 됨)
_SECTOR_HTML = _inject_floating_ai(_SECTOR_HTML, "market")
_MARKET_HTML = _inject_floating_ai(_MARKET_HTML, "market")
_BACKTEST_HTML = _inject_floating_ai(_BACKTEST_HTML, "backtest")
_REALTIME_HTML = _inject_floating_ai(_REALTIME_HTML, "market")
_WORLD_HTML = _inject_floating_ai(_WORLD_HTML, "world")
# 세계 시장은 현재 보고 있는 뷰(국내/미국/글로벌)를 AI에 함께 넘겨 '화면 그대로' 읽게 한다.
_WORLD_HTML = _WORLD_HTML.replace(
    "window.KMKT_ASK=function(){return{scope:'world'};};",
    "window.KMKT_ASK=function(){return{scope:'world',id:(window.__wview||'us')};};", 1)
_WORLD_DETAIL_HTML = _inject_floating_ai(_WORLD_DETAIL_HTML, "world")
# 증권사 리포트 PDF 뷰어 — KMKT_ASK 를 페이지가 cat:nid 로 직접 설정하므로(이 리포트를 읽게)
# _inject_floating_ai 대신 위젯 본체만 placeholder 에 주입(중복 setter·FAB 방지).
_PDF_VIEW_HTML = _PDF_VIEW_HTML.replace("__KMKT_ASK_WIDGET__", _ASK_WIDGET_HTML, 1)
# 랜딩(홈) 화면에도 'AI 질문하기' — 단, 탭(iframe)이 열려 있을 땐 숨김(iframe 이 자체 FAB 보유 → 중복 방지) (작업1)
_LANDING_AI = (
    "<script>window.KMKT_ASK=function(){return{scope:'market'};};</script>"
    + _ASK_WIDGET_HTML
    + "<script>(function(){var r=document.getElementById('kmktAI');if(!r)return;"
      "function upd(){r.style.display=document.querySelector('.framewrap.show')?'none':'';}"
      "upd();try{new MutationObserver(upd).observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});}catch(e){}})();</script>"
)
_LANDING_HTML = _LANDING_HTML.replace("</body>", _LANDING_AI + "</body>", 1)
# 해외 M4 퀀트 탭이 부분 CSS만 있어 카드가 밝게/지표가 세로로 깨지던 문제(피드백1) — 도메스틱과
# 동일한 완전한 M4 콕핏 스타일(_M4_STYLE: .m4-wrap .card · .m4-met-grid · .m4-grid 등)을 주입.
_OVERSEAS_HTML = _OVERSEAS_HTML.replace("</head>", _M4_STYLE + "</head>", 1)


def main() -> None:
    print("=" * 60)
    print("  한국 증시·ETF 통합 대시보드 3 — M4 Pro · Pro Quant · 실시간 시세")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 현재가(.ph-price) 한국투자증권 KIS 실시간 시세 2초 갱신")
    print("  · 기본 탭 3D FX + M4 퀀트 데스크(리스크/3D 변동성·상관/CAPM)")
    print("  · 캐시: SSD parquet + RAM + 프리워밍 | 종료: 탭 닫기 / Ctrl+C")
    ak, _ = _kis_keys()
    print("  · KIS 키 로드: " + ("OK" if ak else "실패 — .env 확인"))
    print("=" * 60)
    if not os.environ.get("MI_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    threading.Thread(target=_monitor_heartbeat, daemon=True).start()
    threading.Thread(target=_prewarm, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
