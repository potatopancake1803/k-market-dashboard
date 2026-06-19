# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pytest",
#   "numpy",
#   "pandas",
#   "pyarrow",
#   # 아래는 대상 모듈(market_dashboard3_realtime) import 시 필요한 런타임 의존성.
#   # 테스트 자체는 순수 함수만 다루지만, 모듈을 import 하려면 함께 있어야 한다.
#   "httpx",
#   "flask",
#   "plotly",
#   "scipy",
#   "python-dotenv",
#   "lxml",
#   "polars",
#   "websockets",
# ]
# ///
"""핵심 순수 함수 회귀 테스트 — 네트워크 접근 없이 실행 가능.

대상: scripts/market_dashboard3_realtime.py 의 결정적(입력→출력) 헬퍼들.
목적: 금융 수치 스케일/계산 버그(이미 실제 발생한 tomv 버그류)를 자동으로 잡는다.

실행:  uv run pytest tests/test_core_functions.py -v

⚠ 참고(검증된 사실, 2026-06-17):
  · 사양서가 지정한 `fmtMcap(v)` 는 **JavaScript 함수**(HTML 문자열 내부, 약 10471줄)이며
    Python 으로는 존재하지 않는다 → 파이썬 단위테스트 불가. 같은 "억/조 스케일 포맷"
    역할의 Python 함수인 `_krx_won()` 을 스케일-버그 가드로 대신 테스트한다.
  · `_sse_*` 는 SSE 프레임이 `event: ...\\ndata: {...}\\n\\n` 형식이라 `data:` 로 *시작*
    하지 않는다(사양서 가정과 다름). 실제 출력 형식에 맞춰 검증한다.
"""
import sys
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pytest

# scripts/ 를 import 경로에 추가 후 메인 백엔드 모듈을 직접 로드.
# (모듈 최상위는 load_dotenv(파일읽기)만 수행하고, app.run/네트워크/스레드는
#  전부 `if __name__ == "__main__"` 가드 안이라 import 시 부작용이 없다 — 확인됨.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# ── 레거시 모듈 격리(테스트 이식성) ──────────────────────────────────────────
# 메인 백엔드는 import 시 `from archive import company_report_ver2/etf_dashboard_ver2`
# 를 즉시 실행한다. 이 레거시 모듈들은 `market_intel.report.dashboard` 를 끌어오는데,
# 그 파일(약 692줄)은 f-string 안에 백슬래시를 쓰는 **Python 3.12+ 전용 문법**이라
# Python 3.10/3.11 에서는 컴파일 단계에서 SyntaxError 가 난다(실제 앱 런타임은 3.12+
# 이므로 문제 없음 — 2026-06-17 확인).
# 우리가 테스트하는 6개 함수는 전부 순수 함수로 이 레거시 모듈에 의존하지 않으므로,
# 구버전 인터프리터에서도 동일 테스트가 돌도록 가벼운 더미 모듈로 선치환한다.
# (3.12+ 에서는 실제 모듈이 정상 import 되며, 이 스텁은 사용되지 않는다.)
import types  # noqa: E402

for _legacy in ("archive", "archive.company_report_ver2", "archive.etf_dashboard_ver2"):
    if _legacy not in sys.modules:
        _m = types.ModuleType(_legacy)
        if _legacy == "archive":
            _m.__path__ = []  # 패키지로 취급
        sys.modules[_legacy] = _m
# `from archive import company_report_ver2 as company` 형태가 동작하도록 속성 연결
sys.modules["archive"].company_report_ver2 = sys.modules["archive.company_report_ver2"]
sys.modules["archive"].etf_dashboard_ver2 = sys.modules["archive.etf_dashboard_ver2"]

import market_dashboard3_realtime as md  # noqa: E402


# ───────────────────────── 1. _krx_won (억/조 스케일 포맷, fmtMcap 대체) ─────────────────────────
class TestKrxWon:
    def test_jo_scale(self):
        # 1조 = 1e12 → "1.0조원"
        assert md._krx_won(1_000_000_000_000) == "1.0조원"

    def test_eok_scale(self):
        # 5,000억 = 5e11 → "5,000억원" (천단위 콤마)
        assert md._krx_won(500_000_000_000) == "5,000억원"

    def test_won_scale(self):
        # 1e8 미만은 원 단위
        assert md._krx_won(12_345) == "12,345원"
        assert md._krx_won(999_999) == "999,999원"

    def test_boundary_1e8(self):
        # 정확히 1억 → 억 단위 진입
        assert md._krx_won(100_000_000) == "1억원"

    def test_comma_string_input(self):
        # 콤마 포함 문자열도 파싱
        assert md._krx_won("1,000,000,000,000") == "1.0조원"

    def test_zero(self):
        assert md._krx_won(0) == "0원"

    def test_invalid_returns_dash(self):
        # None / 비숫자 → "-" (스케일 버그 대신 안전 폴백)
        assert md._krx_won(None) == "-"
        assert md._krx_won("abc") == "-"


# ───────────────────────── 2. _cu (카운트업 HTML span) ─────────────────────────
class TestCu:
    def test_basic_span(self):
        out = md._cu(1234.5, dec=2)
        assert out.startswith('<b class="cu"')
        assert 'data-to="1234.500000"' in out   # 항상 6자리 고정 포맷
        assert 'data-dec="2"' in out
        assert 'data-sign="0"' in out
        assert out.endswith(">0</b>")            # 초기 표시값은 0

    def test_sign_flag(self):
        out = md._cu(-5, dec=0, sign=True)
        assert 'data-sign="1"' in out
        assert 'data-to="-5.000000"' in out

    def test_int_input(self):
        out = md._cu(42)
        assert 'data-to="42.000000"' in out
        assert 'data-dec="0"' in out


# ───────────────────────── 3. _risk_stats (Sharpe/Sortino/VaR/CVaR/MDD) ─────────────────────────
class TestRiskStats:
    def test_known_series_sharpe(self):
        # 결정적 검증: 일정 비율(매일 +1%)로 오르는 시계열.
        # 모든 일간 로그수익이 동일하면 std=0 → 코드가 sd=1e-6 으로 클램프하고,
        # mu>0 이므로 sharpe 는 매우 큰 양수가 되어야 한다(분모 클램프 경로 확인).
        closes = np.array([100.0 * (1.01 ** i) for i in range(30)])
        s = md._risk_stats(closes)
        assert s["sharpe"] > 0
        assert math.isfinite(s["sharpe"])
        # 단조 증가 → 낙폭(MDD) 0 에 매우 근접(부동소수 허용오차)
        assert s["mdd"] == pytest.approx(0.0, abs=1e-9)

    def test_sharpe_matches_manual_formula(self):
        # 변동이 있는 시계열에서 sharpe = mu/sd*sqrt(252) 공식과 일치하는지 직접 대조.
        rng = np.random.default_rng(42)
        rets = rng.normal(0.0005, 0.01, 250)
        closes = 100.0 * np.exp(np.cumsum(np.concatenate([[0.0], rets])))
        s = md._risk_stats(closes)
        logr = np.diff(np.log(closes))
        mu, sd = logr.mean(), logr.std()
        expected_sharpe = mu / sd * np.sqrt(252)
        assert s["sharpe"] == pytest.approx(expected_sharpe, rel=1e-9)

    def test_mdd_is_negative_on_drawdown(self):
        # 올랐다가 반토막 → MDD 는 음수(-50% 부근)여야 한다.
        closes = np.array([100, 110, 120, 60, 80], dtype=float)
        s = md._risk_stats(closes)
        assert s["mdd"] < 0
        assert s["mdd"] == pytest.approx(-50.0, abs=1.0)  # 120 → 60 = -50%

    def test_var95_not_above_cvar_tail(self):
        # CVaR(꼬리 평균)은 VaR(5% 분위)보다 같거나 더 나쁜(작거나 같은) 값이어야 한다.
        rng = np.random.default_rng(7)
        rets = rng.normal(0, 0.02, 300)
        closes = 100.0 * np.exp(np.cumsum(np.concatenate([[0.0], rets])))
        s = md._risk_stats(closes)
        assert s["cvar95"] <= s["var95"] + 1e-9

    def test_short_series_safe(self):
        # 길이 2(로그수익 1개) — std=0 이라도 클램프되어 예외 없이 dict 반환.
        s = md._risk_stats(np.array([100.0, 101.0]))
        assert isinstance(s, dict)
        assert set(["sharpe", "sortino", "mdd", "var95", "cvar95"]).issubset(s.keys())
        assert math.isfinite(s["sharpe"])


# ───────────────────────── 4. _clean_closes (종가 추출·정제) ─────────────────────────
class TestCleanCloses:
    def test_basic_extraction_and_sort(self):
        # 일부러 날짜 역순으로 넣어도 정렬되어 나와야 한다.
        rows = [
            {"일자": "2026-01-03", "종가": "120"},
            {"일자": "2026-01-01", "종가": "100"},
            {"일자": "2026-01-02", "종가": "110"},
        ]
        dates, closes = md._clean_closes(rows)
        assert list(closes) == [100.0, 110.0, 120.0]   # 날짜 오름차순으로 재정렬
        assert len(dates) == 3

    def test_comma_numbers(self):
        rows = [{"일자": "2026-01-01", "종가": "1,234,500"}]
        _, closes = md._clean_closes(rows)
        assert list(closes) == [1234500.0]

    def test_empty_list(self):
        dates, closes = md._clean_closes([])
        assert len(dates) == 0 and len(closes) == 0

    def test_missing_column(self):
        # '종가' 컬럼 없음 → 빈 배열 두 개
        dates, closes = md._clean_closes([{"일자": "2026-01-01", "가격": 100}])
        assert len(dates) == 0 and len(closes) == 0

    def test_drops_nonpositive_and_nan(self):
        # 0/음수/결측 종가는 (ffill/bfill 후) 양수 마스크로 걸러지는지.
        rows = [
            {"일자": "2026-01-01", "종가": "100"},
            {"일자": "2026-01-02", "종가": "0"},     # 비양수 → 제외 대상
            {"일자": "2026-01-03", "종가": "130"},
        ]
        _, closes = md._clean_closes(rows)
        assert all(c > 0 for c in closes)


# ───────────────────────── 5. _is_open_day (개장일 판정, 주말 폴백) ─────────────────────────
class TestIsOpenDay:
    def test_weekend_fallback(self, monkeypatch):
        # 휴장일 캐시가 비어 있으면(=네트워크 불가) 주말 판정 폴백.
        # 네트워크/디스크 의존을 끊기 위해 _load_holidays 를 빈 dict 로 고정.
        monkeypatch.setattr(md, "_load_holidays", lambda: {})
        assert md._is_open_day(date(2026, 6, 13)) is False  # 토요일
        assert md._is_open_day(date(2026, 6, 14)) is False  # 일요일
        assert md._is_open_day(date(2026, 6, 15)) is True   # 월요일
        assert md._is_open_day(date(2026, 6, 17)) is True   # 수요일

    def test_holiday_map_override(self, monkeypatch):
        # 캐시에 명시된 날짜는 주말 여부와 무관하게 맵 값(Y/N)을 따른다.
        monkeypatch.setattr(md, "_load_holidays", lambda: {"20260615": "N"})
        assert md._is_open_day(date(2026, 6, 15)) is False   # 평일이지만 휴장(N)
        # 맵에 없는 평일은 폴백으로 True
        assert md._is_open_day(date(2026, 6, 16)) is True


# ───────────────────────── 6. _sse_progress / _sse_done / _sse_failed ─────────────────────────
class TestSSE:
    def test_progress_format(self):
        out = md._sse_progress(42, "계산 중")
        # SSE 프레임: 'event: progress\n' + 'data: {...}\n\n'
        assert out.startswith("event: progress\n")
        assert "data: " in out
        assert out.endswith("\n\n")
        # data 라인의 JSON 파싱 검증
        payload = out.split("data: ", 1)[1].rstrip("\n")
        obj = json.loads(payload)
        assert obj == {"pct": 42, "label": "계산 중"}

    def test_done_format(self):
        out = md._sse_done("<div>hi</div>")
        assert out.startswith("event: done\n")
        payload = out.split("data: ", 1)[1].rstrip("\n")
        assert json.loads(payload) == {"html": "<div>hi</div>"}
        assert out.endswith("\n\n")

    def test_failed_format(self):
        out = md._sse_failed("오류 발생")
        assert out.startswith("event: failed\n")
        payload = out.split("data: ", 1)[1].rstrip("\n")
        assert json.loads(payload) == {"msg": "오류 발생"}

    def test_korean_not_escaped(self):
        # ensure_ascii=False 라 한글이 \\uXXXX 로 이스케이프되지 않아야 한다.
        out = md._sse_progress(1, "한글라벨")
        assert "한글라벨" in out
