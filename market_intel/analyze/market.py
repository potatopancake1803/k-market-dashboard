"""시장 스캔 분석 — polars 집계 후 pandas 요약 반환.

260514/market_analyzer/analyzer.py 의 함수들을 polars 로 재작성.
대규모 종목×일자 groupby/pivot 을 polars 가 12코어 자동 병렬 처리한다.
요약은 리포트 렌더 일관성을 위해 pandas DataFrame 으로 반환한다.
"""
from __future__ import annotations

import pandas as pd
import polars as pl


def _has(df: pl.DataFrame, *cols: str) -> bool:
    return (not df.is_empty()) and all(c in df.columns for c in cols)


# ── 지수 요약 ──────────────────────────────────────────────────
def index_summary(df_idx: pl.DataFrame, focus_names: list[str]) -> pd.DataFrame:
    if not _has(df_idx, "IDX_NM", "CLSPRC_IDX", "_bas_dt"):
        return pd.DataFrame()
    sub = df_idx
    if focus_names:
        f = df_idx.filter(pl.col("IDX_NM").is_in(focus_names))
        if not f.is_empty():
            sub = f

    agg = (
        sub.sort("_bas_dt")
        .group_by("IDX_NM", maintain_order=True)
        .agg([
            pl.col("_bas_dt").min().dt.strftime("%Y-%m-%d").alias("시작일"),
            pl.col("_bas_dt").max().dt.strftime("%Y-%m-%d").alias("종료일"),
            pl.col("CLSPRC_IDX").drop_nulls().first().alias("시작_종가"),
            pl.col("CLSPRC_IDX").drop_nulls().last().alias("종료_종가"),
            pl.col("HGPRC_IDX").max().alias("기간최고"),
            pl.col("LWPRC_IDX").min().alias("기간최저"),
            pl.col("ACC_TRDVAL").mean().alias("일평균_거래대금(원)"),
            pl.col("ACC_TRDVOL").mean().alias("일평균_거래량"),
            pl.col("FLUC_RT").mean().alias("일변동률_평균(%)"),
            pl.col("FLUC_RT").std().alias("일변동률_표준편차(%)"),
        ])
        .with_columns(
            ((pl.col("종료_종가") / pl.col("시작_종가") - 1) * 100).alias("기간수익률(%)")
        )
        .rename({"IDX_NM": "지수명"})
        .sort("기간수익률(%)", descending=True, nulls_last=True)
    )
    cols = ["지수명", "시작일", "종료일", "시작_종가", "종료_종가", "기간수익률(%)",
            "기간최고", "기간최저", "일평균_거래대금(원)", "일평균_거래량",
            "일변동률_평균(%)", "일변동률_표준편차(%)"]
    return agg.select([c for c in cols if c in agg.columns]).to_pandas()


# ── 시장 폭(daily breadth) ─────────────────────────────────────
def market_daily_aggregate(df_stock: pl.DataFrame, market_label: str) -> pd.DataFrame:
    if not _has(df_stock, "FLUC_RT", "_bas_dt"):
        return pd.DataFrame()
    g = (
        df_stock.group_by("_bas_dt")
        .agg([
            pl.col("ACC_TRDVAL").sum().alias("거래대금합계(원)"),
            pl.col("ACC_TRDVOL").sum().alias("거래량합계"),
            pl.col("MKTCAP").sum().alias("시가총액합계(원)"),
            pl.col("ISU_CD").n_unique().alias("상장종목수"),
            (pl.col("FLUC_RT") > 0).sum().alias("상승종목수"),
            (pl.col("FLUC_RT") < 0).sum().alias("하락종목수"),
            (pl.col("FLUC_RT") == 0).sum().alias("보합종목수"),
            pl.col("FLUC_RT").mean().alias("평균등락률(%)"),
            pl.col("FLUC_RT").median().alias("중간등락률(%)"),
        ])
        .sort("_bas_dt")
        .with_columns([
            pl.col("_bas_dt").dt.strftime("%Y-%m-%d").alias("기준일자"),
            pl.lit(market_label).alias("시장"),
        ])
        .drop("_bas_dt")
    )
    front = ["기준일자", "시장"]
    return g.select(front + [c for c in g.columns if c not in front]).to_pandas()


# ── 종목별 기간 요약 ───────────────────────────────────────────
def period_return_by_stock(df_stock: pl.DataFrame) -> pd.DataFrame:
    if not _has(df_stock, "ISU_CD", "TDD_CLSPRC", "_bas_dt"):
        return pd.DataFrame()
    agg = (
        df_stock.sort(["ISU_CD", "_bas_dt"])
        .group_by("ISU_CD", maintain_order=True)
        .agg([
            pl.col("ISU_NM").first().alias("종목명"),
            pl.col("_bas_dt").min().dt.strftime("%Y-%m-%d").alias("시작일"),
            pl.col("_bas_dt").max().dt.strftime("%Y-%m-%d").alias("종료일"),
            pl.col("TDD_CLSPRC").drop_nulls().first().alias("시작종가"),
            pl.col("TDD_CLSPRC").drop_nulls().last().alias("종료종가"),
            pl.col("MKTCAP").drop_nulls().last().alias("최종시가총액"),
            pl.col("ACC_TRDVAL").sum().alias("누적거래대금"),
            pl.col("ACC_TRDVAL").mean().alias("평균거래대금"),
            pl.col("FLUC_RT").mean().alias("일평균변동률"),
            pl.col("FLUC_RT").std().alias("일변동률표준편차"),
            pl.len().alias("관측일수"),
        ])
        .with_columns(
            ((pl.col("종료종가") / pl.col("시작종가") - 1) * 100).alias("기간수익률(%)")
        )
        .sort("기간수익률(%)", descending=True, nulls_last=True)
    )
    cols = ["ISU_CD", "종목명", "시작일", "종료일", "시작종가", "종료종가",
            "기간수익률(%)", "최종시가총액", "누적거래대금", "평균거래대금",
            "일평균변동률", "일변동률표준편차", "관측일수"]
    return agg.select([c for c in cols if c in agg.columns]).to_pandas()


def top_movers(period_df: pd.DataFrame, n: int = 20, min_trdval: float = 1e8) -> dict[str, pd.DataFrame]:
    if period_df.empty:
        return {}
    base = period_df[period_df["평균거래대금"].fillna(0) >= min_trdval]
    return {
        "상위_상승": base.nlargest(n, "기간수익률(%)").reset_index(drop=True),
        "상위_하락": base.nsmallest(n, "기간수익률(%)").reset_index(drop=True),
        "상위_거래대금": period_df.nlargest(n, "누적거래대금").reset_index(drop=True),
        "상위_변동성": period_df.nlargest(n, "일변동률표준편차").reset_index(drop=True),
    }


# ── 섹터(소속부) 요약 ──────────────────────────────────────────
def sector_summary(df_stock: pl.DataFrame, period_df: pd.DataFrame) -> pd.DataFrame:
    if df_stock.is_empty() or period_df.empty or "SECT_TP_NM" not in df_stock.columns:
        return pd.DataFrame()
    sect = (
        df_stock.filter(pl.col("SECT_TP_NM").is_not_null())
        .group_by("ISU_CD")
        .agg(pl.col("SECT_TP_NM").mode().first().alias("소속부"))
        .to_pandas()
    )
    df = period_df.merge(sect, on="ISU_CD", how="left")
    df["소속부"] = df["소속부"].fillna("(미분류)")
    out = (
        df.groupby("소속부").agg(
            종목수=("ISU_CD", "nunique"),
            평균수익률=("기간수익률(%)", "mean"),
            중간수익률=("기간수익률(%)", "median"),
            시가총액합계=("최종시가총액", "sum"),
            누적거래대금합계=("누적거래대금", "sum"),
        ).reset_index().sort_values("시가총액합계", ascending=False)
    )
    return out


# ── ETF 요약 ───────────────────────────────────────────────────
def etf_summary(df_etf: pl.DataFrame, n: int = 20) -> dict[str, pd.DataFrame]:
    if not _has(df_etf, "ISU_CD", "TDD_CLSPRC", "_bas_dt"):
        return {}
    agg = (
        df_etf.sort(["ISU_CD", "_bas_dt"])
        .group_by("ISU_CD", maintain_order=True)
        .agg([
            pl.col("ISU_NM").first().alias("종목명"),
            (pl.col("IDX_IND_NM").last() if "IDX_IND_NM" in df_etf.columns
             else pl.lit(None)).alias("기초지수"),
            pl.col("_bas_dt").min().dt.strftime("%Y-%m-%d").alias("시작일"),
            pl.col("_bas_dt").max().dt.strftime("%Y-%m-%d").alias("종료일"),
            pl.col("TDD_CLSPRC").drop_nulls().first().alias("시작가"),
            pl.col("TDD_CLSPRC").drop_nulls().last().alias("종료가"),
            pl.col("MKTCAP").drop_nulls().last().alias("기간말_시가총액"),
            pl.col("ACC_TRDVAL").sum().alias("누적거래대금"),
            pl.col("ACC_TRDVAL").mean().alias("평균거래대금"),
        ])
        .with_columns(((pl.col("종료가") / pl.col("시작가") - 1) * 100).alias("기간수익률(%)"))
    )
    cols = ["ISU_CD", "종목명", "기초지수", "시작일", "종료일", "시작가", "종료가",
            "기간수익률(%)", "기간말_시가총액", "누적거래대금", "평균거래대금"]
    df = agg.select([c for c in cols if c in agg.columns]).to_pandas()
    return {
        "ETF_전체": df.sort_values("누적거래대금", ascending=False).reset_index(drop=True),
        "ETF_상위_상승": df.nlargest(n, "기간수익률(%)").reset_index(drop=True),
        "ETF_상위_하락": df.nsmallest(n, "기간수익률(%)").reset_index(drop=True),
        "ETF_상위_거래대금": df.nlargest(n, "누적거래대금").reset_index(drop=True),
    }


# ── 매크로 / 유가 (pandas dict 입력) ───────────────────────────
def macro_summary(macro: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for name, df in macro.items():
        if df.empty or "DATA_VALUE" not in df.columns:
            continue
        s = df.sort_values("TIME")
        first, last = s.iloc[0], s.iloc[-1]
        fv, lv = first["DATA_VALUE"], last["DATA_VALUE"]
        rows.append({
            "지표": name, "기간시작": first.get("TIME"), "기간종료": last.get("TIME"),
            "시작값": fv, "종료값": lv,
            "변동": (lv - fv) if pd.notna(lv) and pd.notna(fv) else None,
            "변동률(%)": ((lv / fv) - 1) * 100 if pd.notna(lv) and pd.notna(fv) and fv else None,
            "평균": s["DATA_VALUE"].mean(), "관측수": len(s),
        })
    return pd.DataFrame(rows)


def oil_summary(oil: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for name, df in oil.items():
        if df.empty or "value" not in df.columns:
            continue
        s = df.copy()
        s["value"] = pd.to_numeric(s["value"], errors="coerce")
        s = s.dropna(subset=["value"]).sort_values("period")
        if s.empty:
            continue
        first, last = s.iloc[0], s.iloc[-1]
        rows.append({
            "유종": name, "기간시작": first["period"], "기간종료": last["period"],
            "시작가": first["value"], "종료가": last["value"],
            "변동률(%)": ((last["value"] / first["value"]) - 1) * 100,
            "평균": s["value"].mean(), "최고": s["value"].max(),
            "최저": s["value"].min(), "관측일수": len(s),
        })
    return pd.DataFrame(rows)
