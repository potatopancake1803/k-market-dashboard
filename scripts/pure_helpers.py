"""Pure, side-effect-free helpers extracted from market_dashboard3_realtime.py (changes_78).

No network / file / env / Flask — ONLY stdlib + numpy/pandas. These are deterministic
input→output functions (quant/risk math, OHLC cleaning, number formatting, SSE frame
builders, US-DST date math), so they are trivially unit-testable in isolation. The main
file does `from pure_helpers import (...)` and uses them unchanged; assembly/wiring stays there.

If you add a function here it MUST stay pure (no module globals, no I/O). After editing, run
`uv run scripts/smoke_check.py` and `uv run --with pytest pytest tests/test_core_functions.py`.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta  # noqa: F401  (used by extracted fns)

import numpy as np
import pandas as pd


def _is_us_dst(dt: datetime) -> bool:
    """US Daylight Saving Time: 2nd Sunday in March to 1st Sunday in November."""
    # This is a basic approximation for KST matching
    # A more precise calculation checks the exact dates.
    y = dt.year
    # March 2nd Sunday
    mar_1st = datetime(y, 3, 1)
    mar_2nd_sun = 1 + (6 - mar_1st.weekday()) + 7
    # Nov 1st Sunday
    nov_1st = datetime(y, 11, 1)
    nov_1st_sun = 1 + (6 - nov_1st.weekday())
    
    start_dst = datetime(y, 3, mar_2nd_sun, 2, 0) # US time approx
    end_dst = datetime(y, 11, nov_1st_sun, 2, 0)
    # Simplify by checking the date (KST is +14h or +13h)
    return datetime(y, 3, mar_2nd_sun) <= dt.replace(hour=0, minute=0, second=0, microsecond=0) < datetime(y, 11, nov_1st_sun)

def _clean_closes(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    df = pd.DataFrame(rows)
    if df.empty or "종가" not in df.columns:
        return np.array([]), np.array([])
    df["일자"] = pd.to_datetime(df["일자"], errors="coerce")
    df = df.dropna(subset=["일자"]).sort_values("일자")
    cl = pd.to_numeric(df["종가"].astype(str).str.replace(",", ""), errors="coerce").ffill().bfill()
    mask = cl.notna() & (cl > 0)
    return df["일자"].values[mask.values], cl.values[mask.values].astype(float)

def _clean_ohlc(rows: list[dict]) -> dict | None:
    """일자/시가/고가/저가/종가/거래량 정제(정렬·결측보정·이상치 제외) → 정렬된 배열 dict."""
    df = pd.DataFrame(rows)
    if df.empty or "종가" not in df.columns:
        return None
    df["일자"] = pd.to_datetime(df["일자"], errors="coerce")
    df = df.dropna(subset=["일자"]).sort_values("일자")

    def num(col):
        return (pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
                if col in df.columns else pd.Series([float("nan")] * len(df), index=df.index))

    c = num("종가").ffill().bfill()
    o, h, l, v = num("시가").fillna(c), num("고가").fillna(c), num("저가").fillna(c), num("거래량").fillna(0)
    mask = (c.notna() & (c > 0)).values
    return {"d": df["일자"].values[mask], "o": o.values[mask].astype(float),
            "h": h.values[mask].astype(float), "l": l.values[mask].astype(float),
            "c": c.values[mask].astype(float), "v": v.values[mask].astype(float)}

def _risk_stats(closes: np.ndarray) -> dict:
    logr = np.diff(np.log(closes))
    logr = logr[np.isfinite(logr)]
    mu, sd = float(logr.mean()), float(logr.std())
    if not np.isfinite(sd) or sd <= 0:
        sd = 1e-6
    ann_ret = (np.exp(mu * 252) - 1) * 100
    ann_vol = sd * np.sqrt(252) * 100
    sharpe = mu / sd * np.sqrt(252)
    dn = logr[logr < 0]
    dsd = float(dn.std()) if dn.size > 1 else sd
    sortino = mu / (dsd if dsd > 0 else sd) * np.sqrt(252)
    peak = np.maximum.accumulate(closes)
    mdd = float((closes / peak - 1).min() * 100)
    q5 = float(np.percentile(logr, 5))
    var95 = q5 * 100
    tail = logr[logr <= q5]
    cvar95 = float(tail.mean() * 100) if tail.size else var95
    return dict(logr=logr, mu=mu, sd=sd, ann_ret=ann_ret, ann_vol=ann_vol,
                sharpe=sharpe, sortino=sortino, mdd=mdd, var95=var95, cvar95=cvar95)

def _cu(v, dec: int = 0, sign: bool = False) -> str:
    return (f'<b class="cu" data-to="{float(v):.6f}" data-dec="{dec}" '
            f'data-sign="{1 if sign else 0}">0</b>')

def _sse_progress(pct: int, label: str) -> str:
    return f"event: progress\ndata: {json.dumps({'pct': pct, 'label': label}, ensure_ascii=False)}\n\n"

def _sse_done(html: str) -> str:
    return f"event: done\ndata: {json.dumps({'html': html}, ensure_ascii=False)}\n\n"

def _sse_failed(msg: str) -> str:
    return f"event: failed\ndata: {json.dumps({'msg': msg}, ensure_ascii=False)}\n\n"

def _krx_won(v) -> str:
    try:
        n = float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return "-"
    if n >= 1e12:
        return f"{n/1e12:.1f}조원"
    if n >= 1e8:
        return f"{n/1e8:,.0f}억원"
    return f"{n:,.0f}원"

def _news_similar(a_norm: str, a_tok: set, b_norm: str, b_tok: set) -> bool:
    """두 정규화 제목이 사실상 같은 기사인지."""
    if not a_norm or not b_norm:
        return a_norm == b_norm
    if not a_tok or not b_tok:                            # 토큰이 거의 없으면 문자열 유사도로
        import difflib
        return difflib.SequenceMatcher(None, a_norm, b_norm).ratio() >= 0.78
    inter, union = len(a_tok & b_tok), len(a_tok | b_tok)
    if union and inter / union >= 0.5:                    # 단어 절반 이상 겹침
        return True
    # 한쪽이 다른 쪽에 거의 포함(부제·말머리 차이) — 작은 집합 기준 포함률
    if inter / min(len(a_tok), len(b_tok)) >= 0.8:
        return True
    import difflib
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio() >= 0.72

def _bt_signal(closes: np.ndarray, strat: str, p: dict) -> np.ndarray:
    n = len(closes)
    sig = np.zeros(n)
    if strat == "sma":
        f = max(2, int(p.get("fast", 20))); s = max(f + 1, int(p.get("slow", 60)))
        cf = pd.Series(closes).rolling(f).mean().values
        cs = pd.Series(closes).rolling(s).mean().values
        sig = np.where(cf > cs, 1.0, 0.0)
        sig[:s] = 0.0
    elif strat == "mom":
        lb = max(2, int(p.get("lookback", 60)))
        sig[lb:] = np.where(closes[lb:] > closes[:-lb], 1.0, 0.0)
    elif strat == "rsi":
        per = max(2, int(p.get("period", 14)))
        buy = float(p.get("buy", 30)); sell = float(p.get("sell", 70))
        d = np.diff(closes, prepend=closes[0])
        up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / per, adjust=False).mean().values
        dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / per, adjust=False).mean().values
        rsi = 100 - 100 / (1 + up / np.where(dn == 0, 1e-9, dn))
        hold = 0.0
        for i in range(per, n):                      # 상태 보존(진입 후 청산까지 유지)
            if rsi[i] < buy:
                hold = 1.0
            elif rsi[i] > sell:
                hold = 0.0
            sig[i] = hold
    elif strat == "macd":                            # MACD 시그널 교차 (추세추종)
        f = max(2, int(p.get("fast", 12))); s = max(f + 1, int(p.get("slow", 26)))
        sp = max(2, int(p.get("signal", 9)))
        ef = pd.Series(closes).ewm(span=f, adjust=False).mean()
        es = pd.Series(closes).ewm(span=s, adjust=False).mean()
        macd = ef - es
        sigl = macd.ewm(span=sp, adjust=False).mean()
        sig = np.where(macd.values > sigl.values, 1.0, 0.0)
        sig[:s] = 0.0
    elif strat == "boll":                            # 볼린저밴드 평균회귀 (하단매수·중심청산)
        per = max(2, int(p.get("period", 20))); k = float(p.get("k", 2))
        ma = pd.Series(closes).rolling(per).mean().values
        sd = pd.Series(closes).rolling(per).std().values
        lower = ma - k * sd
        hold = 0.0
        for i in range(per, n):
            if closes[i] < lower[i]:
                hold = 1.0
            elif closes[i] > ma[i]:
                hold = 0.0
            sig[i] = hold
    else:                                            # bh — 매수보유
        sig[:] = 1.0
    return sig
