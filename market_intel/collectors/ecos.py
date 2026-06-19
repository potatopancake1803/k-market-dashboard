"""한국은행 ECOS Open API (비동기) — 기준금리·환율·국고채.

260514/market_analyzer/ecos_collector.py 로직 포팅 (requests → httpx async).
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ..httpx_client import Fetcher


async def _fetch(fetcher: Fetcher, api_key: str, stat_code: str, period: str,
                 start: date, end: date, *items: str) -> pd.DataFrame:
    if not api_key:
        return pd.DataFrame()
    cycle_fmt = "%Y%m%d" if period == "D" else "%Y%m"
    s, e = start.strftime(cycle_fmt), end.strftime(cycle_fmt)
    parts = ["https://ecos.bok.or.kr/api/StatisticSearch", api_key, "json", "kr",
             "1", "1000", stat_code, period, s, e]
    parts += [i for i in items if i]
    url = "/".join(parts)

    payload = await fetcher.get_json(url)
    if not isinstance(payload, dict) or "StatisticSearch" not in payload:
        return pd.DataFrame()
    rows = payload["StatisticSearch"].get("row", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["DATA_VALUE"] = pd.to_numeric(df["DATA_VALUE"], errors="coerce")
    return df


async def collect_macro(fetcher: Fetcher, api_key: str,
                        start: date, end: date) -> dict[str, pd.DataFrame]:
    """매크로 지표 묶음 동시 수집."""
    if not api_key:
        return {}
    monthly_start = start - timedelta(days=180)  # 월간 시리즈 여유분
    specs = {
        "기준금리":   _fetch(fetcher, api_key, "722Y001", "M", monthly_start, end, "0101000"),
        "원달러환율": _fetch(fetcher, api_key, "731Y001", "D", start, end, "0000001"),
        "원엔환율":   _fetch(fetcher, api_key, "731Y001", "D", start, end, "0000002"),
        "원유로환율": _fetch(fetcher, api_key, "731Y001", "D", start, end, "0000003"),
        "국고채3년":  _fetch(fetcher, api_key, "817Y002", "D", start, end, "010190000"),
        "국고채10년": _fetch(fetcher, api_key, "817Y002", "D", start, end, "010195000"),
    }
    names = list(specs)
    results = await fetcher.gather(list(specs.values()))
    out: dict[str, pd.DataFrame] = {}
    for name, res in zip(names, results):
        if isinstance(res, pd.DataFrame) and not res.empty:
            out[name] = res
    return out
