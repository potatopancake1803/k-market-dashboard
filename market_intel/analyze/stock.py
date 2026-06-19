"""개별 종목 딥다이브 분석 헬퍼.

DART 재무제표/비율(collectors.dart) + KRX 최근 시세 추세를 결합한다.
"""
from __future__ import annotations

import pandas as pd
import polars as pl


def ticker_prices(df_stock: pl.DataFrame, stock_code: str) -> pd.DataFrame:
    """시장 전체 일별 프레임에서 특정 종목의 시계열만 추출."""
    if df_stock.is_empty():
        return pd.DataFrame()
    code_col = None
    for c in ("ISU_SRT_CD", "ISU_CD"):
        if c in df_stock.columns:
            code_col = c
            break
    if code_col is None:
        return pd.DataFrame()
    sub = df_stock.filter(
        pl.col(code_col).cast(pl.Utf8).str.contains(stock_code)
    ).sort("_bas_dt")
    if sub.is_empty():
        return pd.DataFrame()
    keep = [c for c in ["_bas_dt", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC",
                        "FLUC_RT", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP"] if c in sub.columns]
    out = sub.select(keep).with_columns(
        pl.col("_bas_dt").dt.strftime("%Y-%m-%d").alias("일자")
    ).drop("_bas_dt").to_pandas()
    cols = ["일자"] + [c for c in out.columns if c != "일자"]
    return out[cols].rename(columns={
        "ISU_NM": "종목명", "TDD_CLSPRC": "종가", "CMPPREVDD_PRC": "전일대비",
        "FLUC_RT": "등락률(%)", "ACC_TRDVOL": "거래량", "ACC_TRDVAL": "거래대금", "MKTCAP": "시가총액",
    })


def price_stats(prices: pd.DataFrame) -> dict:
    """최근 시세 요약 통계."""
    if prices.empty or "종가" not in prices.columns:
        return {}
    close = pd.to_numeric(prices["종가"], errors="coerce").dropna()
    if close.empty:
        return {}
    first, last = close.iloc[0], close.iloc[-1]
    return {
        "기간시작가": float(first),
        "현재가": float(last),
        "기간수익률(%)": round((last / first - 1) * 100, 2) if first else None,
        "기간최고": float(close.max()),
        "기간최저": float(close.min()),
        "현재가_고점대비(%)": round((last / close.max() - 1) * 100, 2) if close.max() else None,
        "관측일수": int(len(close)),
    }
