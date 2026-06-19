"""EIA(미국 에너지정보청) API (비동기) — Brent / WTI 일별 유가.

260514/market_analyzer/eia_collector.py 로직 포팅.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from ..config import fmt_iso
from ..httpx_client import Fetcher


async def _series(fetcher: Fetcher, api_key: str, series: str,
                  start: date, end: date) -> pd.DataFrame:
    if not api_key:
        return pd.DataFrame()
    params = {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": series,
        "start": fmt_iso(start),
        "end": fmt_iso(end),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    payload = await fetcher.get_json(
        "https://api.eia.gov/v2/petroleum/pri/spt/data/", params=params
    )
    if not isinstance(payload, dict):
        return pd.DataFrame()
    data = payload.get("response", {}).get("data") or []
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    cols = [c for c in ["period", "series-description", "value", "units"] if c in df.columns]
    return df[cols]


async def collect_oil(fetcher: Fetcher, api_key: str,
                      start: date, end: date) -> dict[str, pd.DataFrame]:
    if not api_key:
        return {}
    brent, wti = await fetcher.gather([
        _series(fetcher, api_key, "RBRTE", start, end),
        _series(fetcher, api_key, "RWTC", start, end),
    ])
    out = {}
    if isinstance(brent, pd.DataFrame) and not brent.empty:
        out["Brent_유가"] = brent
    if isinstance(wti, pd.DataFrame) and not wti.empty:
        out["WTI_유가"] = wti
    return out
