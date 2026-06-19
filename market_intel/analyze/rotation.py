"""섹터 로테이션 3중 신호 — 260513/sector_rotation.py 계승.

1) 상대강도(RS): KRX 시리즈 섹터지수 vs KOSPI 종합 초과수익
2) ETF 거래대금 폭발: 최근 5일 평균 vs 기간 평균 배수
3) 외국인·기관 순매수 연속성: 대장주 쌍끌이 탐지

수집된 polars 프레임을 입력으로 받아 market 스캔과 데이터를 공유한다.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import polars as pl

from ..collectors.krx import KRXCollector

SECTOR_INDICES = [
    "KRX 반도체", "KRX 헬스케어", "KRX 자동차", "KRX 은행", "KRX 에너지화학",
    "KRX 철강", "KRX 미디어통신", "KRX 건설", "KRX 증권", "KRX 운송",
    "KRX 기계장비", "KRX 정보기술", "KRX 필수소비재", "KRX 경기소비재",
]
BENCHMARK_INDEX = "코스피"

SECTOR_ETFS = [
    ("091160", "KODEX 반도체", "KRX 반도체"),
    ("305540", "TIGER 2차전지테마", "KRX 에너지화학"),
    ("091510", "KODEX 은행", "KRX 은행"),
    ("091170", "KODEX 자동차", "KRX 자동차"),
    ("266420", "KODEX 헬스케어", "KRX 헬스케어"),
    ("139220", "TIGER 200 건설", "KRX 건설"),
    ("228810", "TIGER 미디어컨텐츠", "KRX 미디어통신"),
    ("117700", "KODEX 철강", "KRX 철강"),
]

SECTOR_LEADERS = [
    ("005930", "삼성전자", "KRX 반도체"), ("000660", "SK하이닉스", "KRX 반도체"),
    ("373220", "LG에너지솔루션", "KRX 에너지화학"), ("006400", "삼성SDI", "KRX 에너지화학"),
    ("005380", "현대차", "KRX 자동차"), ("000270", "기아", "KRX 자동차"),
    ("207940", "삼성바이오로직스", "KRX 헬스케어"), ("068270", "셀트리온", "KRX 헬스케어"),
    ("105560", "KB금융", "KRX 은행"), ("055550", "신한지주", "KRX 은행"),
    ("005490", "POSCO홀딩스", "KRX 철강"), ("004020", "현대제철", "KRX 철강"),
]


def _period_returns(df_idx: pl.DataFrame) -> dict[str, float]:
    if df_idx.is_empty() or "IDX_NM" not in df_idx.columns:
        return {}
    g = (
        df_idx.sort("_bas_dt").group_by("IDX_NM", maintain_order=True)
        .agg([
            pl.col("CLSPRC_IDX").drop_nulls().first().alias("f"),
            pl.col("CLSPRC_IDX").drop_nulls().last().alias("l"),
        ])
        .with_columns(((pl.col("l") / pl.col("f") - 1) * 100).alias("ret"))
    )
    return {name: ret for name, ret in zip(g["IDX_NM"], g["ret"]) if ret is not None}


def relative_strength(krx_idx: pl.DataFrame, kospi_idx: pl.DataFrame) -> pd.DataFrame:
    """KRX 섹터지수 RS 순위."""
    krx_ret = _period_returns(krx_idx)
    kospi_ret = _period_returns(kospi_idx)
    bench = kospi_ret.get(BENCHMARK_INDEX)
    if bench is None or not krx_ret:
        return pd.DataFrame()
    rows = []
    for sec in SECTOR_INDICES:
        r = krx_ret.get(sec)
        if r is None:
            continue
        excess = r - bench
        rs = ((1 + r / 100) / (1 + bench / 100) - 1) * 100
        if excess >= 3:
            sig = "★ 강한 초과수익"
        elif excess >= 1:
            sig = "↑ 초과수익"
        elif excess <= -3:
            sig = "↓ 현저한 약세"
        else:
            sig = "·"
        rows.append({
            "섹터": sec, "섹터수익률(%)": round(r, 2),
            "벤치마크수익률(%)": round(bench, 2), "초과수익(%p)": round(excess, 2),
            "RS(%)": round(rs, 2), "신호": sig,
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("초과수익(%p)", ascending=False).reset_index(drop=True)


def etf_volume(df_etf: pl.DataFrame) -> pd.DataFrame:
    """섹터 대표 ETF 거래대금 폭발 탐지."""
    if df_etf.is_empty() or "ISU_CD" not in df_etf.columns:
        return pd.DataFrame()
    target = {t: (nm, sec) for t, nm, sec in SECTOR_ETFS}
    e = df_etf.with_columns(
        pl.col("ISU_CD").cast(pl.Utf8).str.extract(r"(\d{6})").alias("SHORT")
    ).filter(pl.col("SHORT").is_in(list(target))).sort(["SHORT", "_bas_dt"])
    if e.is_empty():
        return pd.DataFrame()
    g = e.group_by("SHORT", maintain_order=True).agg([
        pl.col("ACC_TRDVAL").sum().alias("tot"),
        pl.col("ACC_TRDVAL").tail(5).sum().alias("r5sum"),
        pl.col("ACC_TRDVAL").tail(5).mean().alias("recent5"),
        pl.col("TDD_CLSPRC").drop_nulls().first().alias("p0"),
        pl.col("TDD_CLSPRC").drop_nulls().last().alias("p1"),
        pl.len().alias("n"),
    ]).to_pandas()

    rows = []
    for _, r in g.iterrows():
        tkr = r["SHORT"]
        if r["n"] < 10 or tkr not in target:
            continue
        prior_n = r["n"] - 5
        prior = (r["tot"] - r["r5sum"]) / prior_n if prior_n > 0 else None
        if not prior or pd.isna(prior):
            continue
        ratio = r["recent5"] / prior
        nm, sec = target[tkr]
        price_chg = (r["p1"] - r["p0"]) / r["p0"] * 100 if r["p0"] else None
        if ratio >= 3:
            sig = "★★ 자금 매집 강력"
        elif ratio >= 2:
            sig = "★ 자금 매집 의심"
        elif ratio >= 1.5:
            sig = "↑ 거래대금 증가"
        else:
            sig = "·"
        rows.append({
            "ETF코드": tkr, "ETF명": nm, "섹터": sec,
            "최근5일평균거래대금(억)": round(r["recent5"] / 1e8, 1),
            "기간평균거래대금(억)": round(prior / 1e8, 1),
            "거래대금배수": round(ratio, 2),
            "기간수익률(%)": round(price_chg, 2) if price_chg is not None else None,
            "신호": sig,
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("거래대금배수", ascending=False).reset_index(drop=True)


def _consec_positive(series: pd.Series) -> int:
    cnt = 0
    for v in series.iloc[::-1]:
        if v > 0:
            cnt += 1
        else:
            break
    return cnt


async def investor_flow(collector: KRXCollector, end: dt.date, lookback: int = 20,
                        focus_sectors: list[str] | None = None) -> pd.DataFrame:
    """대장주 외국인·기관 순매수 연속성 교차검증 (네이버 금융 순매매량, 단위: 주)."""
    leaders = SECTOR_LEADERS
    if focus_sectors:
        leaders = [t for t in SECTOR_LEADERS if t[2] in focus_sectors]
    if not leaders:
        return pd.DataFrame()

    pages = max(2, lookback // 10 + 1)

    async def _one(code: str, name: str, sector: str):
        df = await collector.fetch_investor_flow(code, pages=pages)
        return code, name, sector, df

    results = await collector.fetcher.gather([_one(*ld) for ld in leaders])
    rows = []
    for res in results:
        if not isinstance(res, tuple):
            continue
        code, name, sector, df = res
        if df is None or df.empty or "외국인" not in df.columns or "기관" not in df.columns:
            continue
        df = df.tail(lookback)
        f_c, i_c = _consec_positive(df["외국인"]), _consec_positive(df["기관"])
        both = min(f_c, i_c)
        if both >= 5:
            sig = "★★ 쌍끌이 강력 (5일+)"
        elif both >= 3:
            sig = "★ 쌍끌이 진입"
        elif f_c >= 3 or i_c >= 3:
            sig = "↑ 단일 주체 매수"
        else:
            sig = "·"
        rows.append({
            "종목코드": code, "종목명": name, "섹터": sector,
            "외국인 연속순매수(일)": f_c, "기관 연속순매수(일)": i_c, "쌍끌이 연속(일)": both,
            f"외국인 누적순매수({lookback}일,만주)": round(df["외국인"].sum() / 1e4, 1),
            f"기관 누적순매수({lookback}일,만주)": round(df["기관"].sum() / 1e4, 1),
            "신호": sig,
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("쌍끌이 연속(일)", ascending=False).reset_index(drop=True)


def combined_signals(rs_df: pd.DataFrame, etf_df: pd.DataFrame,
                     flow_df: pd.DataFrame) -> list[str]:
    """3중 신호 동시 점등 섹터."""
    if rs_df.empty or etf_df.empty or flow_df.empty:
        return []
    winners = []
    for sec in rs_df.head(5)["섹터"]:
        etf_hit = etf_df[(etf_df["섹터"] == sec) & (etf_df["거래대금배수"] >= 1.5)]
        flow_hit = flow_df[(flow_df["섹터"] == sec) & (flow_df["쌍끌이 연속(일)"] >= 3)]
        if not etf_hit.empty and not flow_hit.empty:
            winners.append(sec)
    return winners
