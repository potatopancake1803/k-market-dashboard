"""ETF 스냅샷·상세 분석 (KRX etf_bydd_trd 기반).

KRX ETF 일별매매정보에서 최신 거래일 스냅샷(가격·NAV·괴리율·순자산·기초지수)과
개별 ETF 시계열을 만든다. 운용사(브랜드)·테마 분류로 시장 구성도 집계한다.
"""
from __future__ import annotations

import pandas as pd
import polars as pl

NETASST = "INVSTASST_NETASST_TOTAMT"  # 순자산총액
_OKK = 1e8  # 억 단위


# ── 운용사·테마 분류 ───────────────────────────────────────────
def brand_of(name: str) -> str:
    """ETF명 첫 토큰 → 운용사 브랜드(KODEX/TIGER/KBSTAR/ACE …)."""
    return (name or "").split(" ")[0] or "기타"


def theme_of(name: str) -> str:
    n = name or ""
    if any(k in n for k in ("레버리지", "인버스", "2X", "곱버스")):
        return "레버리지/인버스"
    if any(k in n for k in ("채권", "국고채", "회사채", "금리", "통안", "CD금리", "단기자금", "머니마켓")):
        return "채권/금리"
    if any(k in n for k in ("리츠", "REIT", "부동산")):
        return "리츠/부동산"
    if any(k in n for k in ("금", "은", "원유", "구리", "원자재", "농산물", "천연가스")):
        return "원자재"
    if any(k in n for k in ("미국", "나스닥", "S&P", "글로벌", "선진", "신흥", "중국", "차이나",
                            "일본", "인도", "베트남", "유로", "유럽", "필라델피아", "China", "달러")):
        return "해외주식"
    if any(k in n for k in ("배당", "고배당", "커버드콜", "인컴")):
        return "배당/인컴"
    return "국내주식/기타"


# ── 최신 거래일 스냅샷 ─────────────────────────────────────────
def latest_snapshot(df: pl.DataFrame) -> tuple[pd.DataFrame, str]:
    """가장 최근 거래일의 전체 ETF 스냅샷(억원 단위 보정) + 일자 문자열."""
    if df.is_empty() or "_bas_dt" not in df.columns or "TDD_CLSPRC" not in df.columns:
        return pd.DataFrame(), ""
    last = df["_bas_dt"].max()
    d = df.filter(pl.col("_bas_dt") == last)
    have = d.columns

    def col(name, alias):
        return (pl.col(name) if name in have else pl.lit(None)).alias(alias)

    out = d.select([
        col("ISU_CD", "코드"), col("ISU_NM", "종목명"), col("IDX_IND_NM", "기초지수"),
        col("TDD_CLSPRC", "종가"), col("FLUC_RT", "등락률(%)"), col("NAV", "NAV"),
        col("ACC_TRDVAL", "_거래대금"), col(NETASST, "_순자산"), col("MKTCAP", "_시총"),
        col("ACC_TRDVOL", "거래량"),
    ]).to_pandas()
    if out.empty:
        return out, str(last)

    for raw, new in [("_거래대금", "거래대금(억)"), ("_순자산", "순자산(억)"), ("_시총", "시총(억)")]:
        out[new] = (pd.to_numeric(out[raw], errors="coerce") / _OKK).round(0)
    out = out.drop(columns=["_거래대금", "_순자산", "_시총"])

    nav = pd.to_numeric(out["NAV"], errors="coerce")
    close = pd.to_numeric(out["종가"], errors="coerce")
    out["괴리율(%)"] = ((close - nav) / nav * 100).round(2)
    out["운용사"] = out["종목명"].map(brand_of)
    out["테마"] = out["종목명"].map(theme_of)
    cols = ["코드", "종목명", "운용사", "테마", "기초지수", "종가", "등락률(%)", "NAV",
            "괴리율(%)", "거래대금(억)", "순자산(억)", "시총(억)", "거래량"]
    out = out[[c for c in cols if c in out.columns]]
    return out.reset_index(drop=True), str(last)


# ── 시장 집계 ──────────────────────────────────────────────────
def by_group(snap: pd.DataFrame, key: str, n: int = 12) -> pd.DataFrame:
    """운용사/테마별 ETF 수·평균등락률·거래대금·순자산 집계."""
    if snap.empty or key not in snap.columns:
        return pd.DataFrame()
    g = snap.groupby(key).agg(
        ETF수=("코드", "count"),
        평균등락률=("등락률(%)", "mean"),
        거래대금합=("거래대금(억)", "sum"),
        순자산합=("순자산(억)", "sum"),
    ).reset_index().rename(columns={key: key})
    g["평균등락률"] = g["평균등락률"].round(2)
    return g.sort_values("순자산합", ascending=False).head(n).reset_index(drop=True)


# ── 개별 ETF ───────────────────────────────────────────────────
def find_etf(snap: pd.DataFrame, query: str) -> pd.Series | None:
    """코드(6자리, 영문 포함 가능 예 '0115E0') 또는 이름으로 ETF 1건 선택.

    코드 정확일치 우선(대소문자 무시), 없으면 이름 부분일치(거래대금 최대).
    """
    if snap.empty:
        return None
    q = query.strip()
    codes = snap["코드"].astype(str).str.upper()
    exact = snap[codes == q.upper()]
    if not exact.empty:
        return exact.sort_values("거래대금(억)", ascending=False).iloc[0]
    m = snap[snap["종목명"].str.contains(q, case=False, na=False, regex=False)]
    if m.empty:
        return None
    return m.sort_values("거래대금(억)", ascending=False).iloc[0]


def detail_series(df: pl.DataFrame, code: str) -> pd.DataFrame:
    """개별 ETF 일별 [일자, 종가, NAV, 거래대금(억)] 시계열(오름차순)."""
    if df.is_empty() or "ISU_CD" not in df.columns:
        return pd.DataFrame()
    sub = df.filter(pl.col("ISU_CD").cast(pl.Utf8).str.contains(code, literal=True)).sort("_bas_dt")
    if sub.is_empty():
        return pd.DataFrame()
    have = sub.columns
    out = sub.select([
        pl.col("_bas_dt").dt.strftime("%Y-%m-%d").alias("일자"),
        pl.col("TDD_CLSPRC").alias("종가"),
        (pl.col("NAV") if "NAV" in have else pl.lit(None)).alias("NAV"),
        (pl.col("ACC_TRDVAL") if "ACC_TRDVAL" in have else pl.lit(None)).alias("_거래대금"),
    ]).to_pandas()
    out["거래대금(억)"] = (pd.to_numeric(out["_거래대금"], errors="coerce") / _OKK).round(0)
    return out.drop(columns=["_거래대금"])
