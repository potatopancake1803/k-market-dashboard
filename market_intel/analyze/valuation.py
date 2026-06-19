"""투자지표(밸류에이션) 산출 — 전날 종가 + DART 재무제표 결합.

collectors.dart.fetch_statements 가 돌려주는 3개년 재무제표(연도=컬럼)와
KRX 최근 거래일 시세(전날 종가·상장주식수·시가총액), DART 배당정보를 받아
PER·PBR·PSR·EPS·BPS·EV/EBITDA·배당수익률 등을 계산한다.

PER/PBR 은 종목 전체에 대한 시가총액 기준(시총÷순이익, 시총÷자본)으로 산출해
주식수 단위 차이를 피한다. EPS·BPS 는 상장주식수로 환산해 함께 표기.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..collectors import dart as _d
from ..collectors.dart import _get


# ── 시세 기반 지표 (FSC 일별 시세) ─────────────────────────────
def price_analytics(hist: pd.DataFrame) -> dict:
    """FSC 일별 시세(오름차순) → 전일 종가·52주 밴드·수익률·변동성 등."""
    if hist.empty or "종가" not in hist.columns:
        return {}
    close = pd.to_numeric(hist["종가"], errors="coerce").dropna()
    if close.empty:
        return {}
    last = float(close.iloc[-1])
    yr = close.tail(252)
    hi, lo = float(yr.max()), float(yr.min())
    rets = close.pct_change().dropna()
    vol = float(rets.tail(252).std() * np.sqrt(252) * 100) if len(rets) > 5 else None
    last_row = hist.iloc[-1]
    return {
        "기준일": hist["일자"].iloc[-1].strftime("%Y-%m-%d"),
        "전일종가": last,
        "등락률(%)": float(last_row.get("등락률(%)")) if pd.notna(last_row.get("등락률(%)")) else None,
        "시가총액": float(last_row.get("시가총액")) if pd.notna(last_row.get("시가총액")) else None,
        "상장주식수": float(last_row.get("상장주식수")) if pd.notna(last_row.get("상장주식수")) else None,
        "거래대금": float(last_row.get("거래대금")) if pd.notna(last_row.get("거래대금")) else None,
        "52주최고": hi,
        "52주최저": lo,
        "52주위치(%)": round((last - lo) / (hi - lo) * 100, 1) if hi > lo else None,
        "1년수익률(%)": round((last / float(yr.iloc[0]) - 1) * 100, 1) if len(yr) > 1 else None,
        "연율변동성(%)": round(vol, 1) if vol is not None else None,
    }


def ttm_dividend(div_hist: pd.DataFrame) -> float | None:
    """배당 이력에서 최근 12개월 주당 현금배당금 합계(TTM DPS).

    분기·반기·연배당을 가리지 않고 기준일 기준 트레일링 1년을 합산한다.
    """
    if div_hist is None or div_hist.empty or "배당기준일" not in div_hist.columns:
        return None
    cutoff = div_hist["배당기준일"].max() - pd.Timedelta(days=365)
    recent = div_hist[div_hist["배당기준일"] > cutoff]
    s = pd.to_numeric(recent["주당현금배당금"], errors="coerce").dropna()
    return float(s.sum()) if not s.empty else None


# ── 재무 펀더멘털 (연결·TTM·지배주주 기준) ──────────────────────
def _flows(items: list[dict]) -> dict:
    """기간 손익/현금흐름 흐름값(누적). 지배주주 순이익 기준."""
    return {
        "ni": _d.controlling_net_income(items),
        "rev": _d.income_revenue(items),
        "op": _d.income_operating(items),
        "da": _d.cf_depreciation(items),
    }


def fundamentals(stmts: dict) -> dict:
    """밸류에이션 입력값을 연결·지배주주·TTM 기준으로 산출.

    - 이익(순이익·매출·영업이익·상각): TTM = 직전 사업연도 + 최신누적 − 전년동기누적.
      분기 데이터가 없으면 사업연도 값으로 대체.
    - 자본(지배주주지분)·순차입금: 가장 최근 시점(분기 있으면 분기말, 없으면 사업연도말).
    """
    ann = stmts.get("raw") or []
    if not ann:
        return {}
    interim = stmts.get("interim") or {}
    prev = stmts.get("interim_prev") or {}
    icur, iprev = interim.get("items"), prev.get("items")

    af = _flows(ann)
    flows, basis = dict(af), f"{stmts.get('year')}년 연간"
    if icur and iprev:
        cf, pf = _flows(icur), _flows(iprev)

        def ttm(k):
            if af[k] is None:
                return None
            if cf.get(k) is None or pf.get(k) is None:
                return af[k]
            return af[k] + cf[k] - pf[k]

        flows = {k: ttm(k) for k in af}
        basis = f"TTM(최근 4분기·{interim.get('label')} 기준)"

    bs_items = icur if icur else ann
    bs_label = interim.get("label") if icur else f"{stmts.get('year')}년말"
    return {
        "ni": flows["ni"], "rev": flows["rev"], "op": flows["op"], "da": flows["da"],
        "equity": _d.controlling_equity(bs_items), "net_debt": _d.net_debt(bs_items),
        "flow_basis": basis, "bs_label": bs_label,
    }


def valuation_basis(stmts: dict, fs_div: str | None = None) -> str:
    """리포트 안내문구용 — 이익/자본의 산출 기준 설명."""
    fu = fundamentals(stmts)
    if not fu:
        return ""
    div = "연결" if (fs_div or stmts.get("fs_div")) == "CFS" else "개별"
    return (f"{div}(IFRS) 기준 · 이익지표는 {fu['flow_basis']}, "
            f"자본지표는 {fu['bs_label']} 지배주주지분")


def _safe_div(a, b):
    try:
        if a is None or b is None or b == 0:
            return None
        return a / b
    except (TypeError, ZeroDivisionError):
        return None


def valuation_metrics(stmts: dict, *, price: float, shares: float,
                      mktcap: float | None, dividend: dict | None = None) -> pd.DataFrame:
    """전날 종가 기준 투자지표 표 (지표·값·산식). 연결·지배주주·TTM 기준."""
    fu = fundamentals(stmts)
    if not fu:
        return pd.DataFrame()
    cap = mktcap if mktcap else (price * shares if price and shares else None)
    ni, rev, op, da = fu["ni"], fu["rev"], fu["op"], fu["da"]
    equity, nd = fu["equity"], fu["net_debt"]

    ebitda = (op + (da or 0)) if op is not None else None
    ebitda_note = "영업이익+상각" if da else "영업이익(상각 미공시)"
    ev = (cap + nd) if (cap is not None and nd is not None) else cap

    eps = _safe_div(ni, shares)
    bps = _safe_div(equity, shares)
    per = _safe_div(cap, ni)
    pbr = _safe_div(cap, equity)
    psr = _safe_div(cap, rev)
    ev_ebitda = _safe_div(ev, ebitda)

    div = dividend or {}
    dps = div.get("주당현금배당금")
    div_yield = div.get("현금배당수익률(%)")
    if div_yield is None and dps and price:
        div_yield = round(dps / price * 100, 2)
    payout = div.get("현금배당성향(%)")
    if payout is None and dps and eps and eps > 0:
        payout = round(dps / eps * 100, 1)

    def num(v, nd_=2):
        return None if v is None else round(v, nd_)

    rows = [
        ("전일 종가", num(price, 0), "원 · KRX 최근 거래일 종가"),
        ("시가총액", num(cap, 0), "원 · 상장주식수 × 종가"),
        ("상장주식수", num(shares, 0), "주"),
        ("PER(배)", num(per), "시가총액 ÷ 지배주주순이익(TTM)"),
        ("PBR(배)", num(pbr), "시가총액 ÷ 지배주주지분(최근분기)"),
        ("PSR(배)", num(psr), "시가총액 ÷ 매출액(TTM)"),
        ("EPS(원)", num(eps, 0), "지배주주순이익(TTM) ÷ 상장주식수"),
        ("BPS(원)", num(bps, 0), "지배주주지분(최근분기) ÷ 상장주식수"),
        ("EV(원)", num(ev, 0), "시가총액 + 순차입금(최근분기)"),
        ("EV/EBITDA(배)", num(ev_ebitda), f"EV ÷ ({ebitda_note}, TTM)"),
        ("주당배당금 DPS(원)", num(dps, 0), "최근 1년 합계(예탁결제원/DART)"),
        ("배당수익률(%)", num(div_yield), "DPS ÷ 종가"),
        ("배당성향(%)", num(payout), "DPS ÷ EPS"),
    ]
    out = pd.DataFrame(rows, columns=["지표", "값", "산식"])
    return out[out["값"].notna()].reset_index(drop=True)


# ── 차트용 시계열 프레임 ───────────────────────────────────────
def statement_trend(df: pd.DataFrame, items: dict[str, list[str]], unit: float = 1e8) -> pd.DataFrame:
    """재무제표(연도=컬럼) → 차트용 long [연도, 항목, 값(억원)].

    items: 표시명 → 검색 키워드 목록.
    """
    if df.empty:
        return pd.DataFrame()
    years = sorted(int(c) for c in df.columns if str(c).isdigit())
    rows = []
    for label, kws in items.items():
        for y in years:
            v = _get(df, kws, y)
            if v is not None:
                rows.append({"연도": str(y), "항목": label, "값(억원)": round(v / unit)})
    return pd.DataFrame(rows)
