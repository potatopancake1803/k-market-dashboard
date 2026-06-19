"""뉴스 수집기 (비동기) — Naver 검색 API 멀티쿼리 동시 수집.

260514/market_analyzer/naver_collector.py 로직 + 종목별 필터링 강화.
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Sequence

import pandas as pd

from ..httpx_client import Fetcher

DEFAULT_QUERIES = ["코스피", "코스닥", "환율", "한국 기준금리", "외국인 매수", "외국인 매도"]


def _strip_html(s: str) -> str:
    s = re.sub(r"<.*?>", "", s or "")
    return html.unescape(s).strip()


async def _one_query(fetcher: Fetcher, headers: dict, q: str, display: int) -> list[dict]:
    payload = await fetcher.get_json(
        "https://openapi.naver.com/v1/search/news.json",
        params={"query": q, "display": display, "sort": "date"},
        headers=headers,
    )
    if not isinstance(payload, dict):
        return []
    rows = []
    for it in payload.get("items", []):
        pub = it.get("pubDate", "")
        try:
            pub_dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
            pub_s = pub_dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pub_s = pub
        rows.append({
            "검색어": q,
            "발행일": pub_s,
            "제목": _strip_html(it.get("title", "")),
            "요약": _strip_html(it.get("description", "")),
            "링크": it.get("originallink") or it.get("link"),
        })
    return rows


async def fetch_news(fetcher: Fetcher, client_id: str, client_secret: str,
                     queries: Sequence[str] = DEFAULT_QUERIES,
                     display: int = 40) -> pd.DataFrame:
    if not (client_id and client_secret):
        return pd.DataFrame()
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    results = await fetcher.gather([_one_query(fetcher, headers, q, display) for q in queries])
    rows: list[dict] = []
    for r in results:
        if isinstance(r, list):
            rows.extend(r)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["제목"]).reset_index(drop=True)
