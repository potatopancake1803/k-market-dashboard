"""환경 변수 로드 및 공용 설정.

API 키는 기존 `260514/API.env` 를 그대로 재사용한다. 탐색 순서:
  1. 환경변수 MARKET_INTEL_ENV 가 가리키는 파일
  2. 이 패키지 상위(260531)/API.env
  3. 형제 폴더 ../260514/API.env  (기존 키 모음)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# 260531/market_intel/config.py → ROOT_DIR = 260531
ROOT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = ROOT_DIR.parent  # .../Python
OUTPUT_DIR = ROOT_DIR / "output"
CACHE_DIR = ROOT_DIR / ".cache"

# M4 Pro: 논리 코어 수. polars 는 자동으로 전 코어 사용,
# HTTP 동시성은 외부 API 보호를 위해 보수적으로 제한한다.
WORKERS = os.cpu_count() or 8
HTTP_CONCURRENCY = min(12, WORKERS)


def _candidate_env_paths() -> list[Path]:
    paths: list[Path] = []
    env_override = os.environ.get("MARKET_INTEL_ENV")
    if env_override:
        paths.append(Path(env_override).expanduser())
    paths.append(ROOT_DIR / ".env")
    paths.append(PARENT_DIR / "260514" / "API.env")
    return paths


def _load_env() -> Path | None:
    for p in _candidate_env_paths():
        if p.exists():
            load_dotenv(p, override=False)
            return p
    return None


ENV_PATH = _load_env()
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    krx_key: str
    ecos_key: str
    dart_key: str
    fsc_key: str
    naver_id: str
    naver_secret: str
    eia_key: str
    finnhub_key: str
    claude_key: str
    alpha_vantage_key: str
    eodhd_key: str
    claude_model: str = "claude-opus-4-8"

    @property
    def env_path(self) -> Path | None:
        return ENV_PATH


def load_settings() -> Settings:
    g = lambda k: os.environ.get(k, "").strip()
    return Settings(
        krx_key=g("KRX_KEY"),
        ecos_key=g("ECOS_KEY"),
        dart_key=g("DART_KEY"),
        fsc_key=g("FSC_KEY"),
        naver_id=g("NAVER_CLIENT_ID"),
        naver_secret=g("NAVER_CLIENT_SECRET"),
        eia_key=g("EIA_KEY"),
        finnhub_key=g("FINNHUB_KEY"),
        claude_key=g("CLAUDE_KEY"),
        alpha_vantage_key=g("ALPHA_VANTAGE_KEY"),
        eodhd_key=g("EODHD_KEY"),
        claude_model=g("CLAUDE_MODEL") or "claude-opus-4-8",
    )


def business_days(end: date, count: int = 30) -> list[date]:
    """end 일자(포함)에서 거꾸로 영업일 count개 반환 (주말 제외, 오름차순).

    한국 공휴일은 KRX 응답이 비면 호출 측에서 자연히 스킵된다.
    """
    days: list[date] = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


def fmt_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def fmt_iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
