"""KRX 데이터 수집기 (비동기).

- KRX Market Data Open API: 지수/주식/ETF/종목기본정보 (헤더 AUTH_KEY, basDd)
- KRX 웹 API: 투자자별 순매수(수급) — pykrx 대체 직접 호출

엔드포인트/숫자컬럼 정의는 260514/market_analyzer/krx_collector.py 에서,
수급/ISIN 로직은 260513/sector_rotation.py 에서 계승.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from io import StringIO

import pandas as pd
import polars as pl

from ..config import fmt_yyyymmdd
from ..httpx_client import Fetcher

BASE = "https://data-dbg.krx.co.kr/svc/apis"

ENDPOINTS: dict[str, str] = {
    "kospi_stock":  f"{BASE}/sto/stk_bydd_trd",       # 유가증권 일별매매정보
    "kosdaq_stock": f"{BASE}/sto/ksq_bydd_trd",       # 코스닥 일별매매정보
    "kospi_index":  f"{BASE}/idx/kospi_dd_trd",       # KOSPI 시리즈 지수
    "kosdaq_index": f"{BASE}/idx/kosdaq_dd_trd",      # KOSDAQ 시리즈 지수
    "krx_index":    f"{BASE}/idx/krx_dd_trd",         # KRX 시리즈 지수
    "etf":          f"{BASE}/etp/etf_bydd_trd",       # ETF 일별매매정보
    "kospi_base":   f"{BASE}/sto/stk_isu_base_info",  # 유가증권 종목기본정보
    "kosdaq_base":  f"{BASE}/sto/ksq_isu_base_info",  # 코스닥 종목기본정보
}

NUMERIC_COLS = {
    "TDD_CLSPRC", "CMPPREVDD_PRC", "FLUC_RT", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC",
    "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP", "LIST_SHRS",
    "CLSPRC_IDX", "CMPPREVDD_IDX", "OPNPRC_IDX", "HGPRC_IDX", "LWPRC_IDX",
    "NAV", "INVSTASST_NETASST_TOTAMT", "OBJ_STKPRC_IDX", "FLUC_RT_IDX", "PARVAL",
}

def _coerce_numeric(df: pl.DataFrame) -> pl.DataFrame:
    exprs = [
        pl.col(c).cast(pl.Utf8).str.replace_all(",", "", literal=True)
        .cast(pl.Float64, strict=False).alias(c)
        for c in df.columns if c in NUMERIC_COLS
    ]
    return df.with_columns(exprs) if exprs else df


@dataclass
class KRXCollector:
    fetcher: Fetcher
    auth_key: str
    denied: set[str] = field(default_factory=set)

    @property
    def _headers(self) -> dict:
        return {"AUTH_KEY": self.auth_key, "Accept": "application/json"}

    async def _fetch_day(self, endpoint_key: str, bas_dd: str) -> tuple[int, list[dict]]:
        url = ENDPOINTS[endpoint_key]
        status, payload = await self.fetcher.fetch(
            url, params={"basDd": bas_dd}, headers=self._headers, parse="json"
        )
        if status != 200 or not isinstance(payload, dict):
            return status, []
        rows = payload.get("OutBlock_1") or payload.get("OutBlock_2") or []
        return status, rows

    async def fetch_market_frame(self, endpoint_key: str, days: list[date]) -> pl.DataFrame:
        """엔드포인트의 영업일 N개를 동시 수집 → polars DataFrame (_bas_dt 포함).

        권한 없는(401) 엔드포인트는 첫 일자로 탐지 후 스킵.
        """
        if endpoint_key in self.denied or not days:
            return pl.DataFrame()

        # 1) 첫 일자 프로브 (권한/가용성 확인)
        first = fmt_yyyymmdd(days[0])
        status, first_rows = await self._fetch_day(endpoint_key, first)
        if status == 401:
            if endpoint_key not in self.denied:
                print(f"  ! KRX 권한 없음 → {endpoint_key} (이후 스킵)")
            self.denied.add(endpoint_key)
            return pl.DataFrame()

        # 2) 나머지 일자 동시 수집
        rest = days[1:]
        results = await self.fetcher.gather(
            [self._fetch_day(endpoint_key, fmt_yyyymmdd(d)) for d in rest]
        )

        frames: list[pl.DataFrame] = []
        per_day = [(days[0], first_rows)] + [
            (d, r[1] if isinstance(r, tuple) else [])
            for d, r in zip(rest, results)
        ]
        for d, rows in per_day:
            if not rows:
                continue
            fr = pl.DataFrame(rows, infer_schema_length=None)
            fr = fr.with_columns(pl.lit(d).cast(pl.Date).alias("_bas_dt"))
            frames.append(fr)

        if not frames:
            return pl.DataFrame()
        out = pl.concat(frames, how="diagonal_relaxed")
        return _coerce_numeric(out)

    # ── 투자자 수급 (네이버 금융 외국인·기관 매매동향) ─────────────
    # KRX 웹 API(getJsonData)는 봇 차단으로 'LOGOUT' 응답 → 안정적인 네이버 금융으로 대체.
    async def fetch_investor_flow(self, code: str, pages: int = 3) -> pd.DataFrame:
        """종목별 외국인·기관 일별 순매매량(주). 날짜 인덱스, 컬럼 [기관, 외국인]."""
        frames: list[pd.DataFrame] = []
        for page in range(1, pages + 1):
            url = f"https://finance.naver.com/item/frgn.naver?code={code}&page={page}"
            status, content = await self.fetcher.fetch(
                url, headers={"User-Agent": "Mozilla/5.0",
                              "Referer": f"https://finance.naver.com/item/frgn.naver?code={code}"},
                parse="bytes",
            )
            if status != 200 or not content:
                continue
            html = content.decode("euc-kr", errors="replace")
            try:
                tables = pd.read_html(StringIO(html))
            except ValueError:
                continue
            for t in tables:
                lvl0 = [str(x) for x in t.columns.get_level_values(0)]
                if "날짜" in lvl0 and "기관" in lvl0 and "외국인" in lvl0:
                    frames.append(t)
                    break
        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        try:
            out = pd.DataFrame({
                "날짜": df[("날짜", "날짜")],
                "기관": pd.to_numeric(df[("기관", "순매매량")], errors="coerce"),
                "외국인": pd.to_numeric(df[("외국인", "순매매량")], errors="coerce"),
            })
        except KeyError:
            return pd.DataFrame()
        out["날짜"] = pd.to_datetime(out["날짜"], format="%Y.%m.%d", errors="coerce")
        out = (out.dropna(subset=["날짜"]).drop_duplicates("날짜")
               .set_index("날짜").sort_index())
        return out
