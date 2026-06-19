"""금융위원회 오픈API 수집기 (data.go.kr · FSC_KEY).

기존 KRX Market Data API(권한 이슈·일자별 전수 스캔)를 보완한다.
개별 종목의 시세를 단축코드+기간으로 직접 조회할 수 있어 장기 시계열을
한 번에 받고, 같은 기간 지수 시세와 예탁결제원 배당 이력까지 결합한다.

- 주식시세정보 getStockPriceInfo  : 종목 일별 OHLCV + 상장주식수 + 시가총액
- 지수시세정보 getStockMarketIndex : 코스피/코스닥 등 지수 일별 종가(+연중 최고/최저)
- 주식배당정보 getDiviInfo_V2      : 예탁결제원 배당 이력(주당 현금배당금·배당률·액면가)

문서: 개발명세서/오픈API 활용자가이드_금융위원회_*.md
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ..httpx_client import Fetcher

BASE = "https://apis.data.go.kr/1160100"
STOCK_URL = f"{BASE}/service/GetStockSecuritiesInfoService/getStockPriceInfo"
INDEX_URL = f"{BASE}/service/GetMarketIndexInfoService/getStockMarketIndex"
DIVI_URL = f"{BASE}/GetStocDiviInfoService_V2/getDiviInfo_V2"


def _items(payload) -> list[dict]:
    """data.go.kr 표준 응답에서 items.item 리스트 추출 (단건/빈값 정규화)."""
    if not isinstance(payload, dict):
        return []
    body = payload.get("response", {}).get("body", {})
    if not isinstance(body, dict):
        return []
    items = body.get("items")
    if not items or items == "":
        return []
    item = items.get("item") if isinstance(items, dict) else items
    if item is None:
        return []
    return item if isinstance(item, list) else [item]


def _num(v):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


async def _get(fetcher: Fetcher, key: str, url: str, params: dict,
               num_rows: int = 500) -> list[dict]:
    payload = await fetcher.get_json(url, params={
        "serviceKey": key, "resultType": "json",
        "numOfRows": str(num_rows), "pageNo": "1", **params,
    })
    return _items(payload)


def _ymd(d: date) -> str:
    return d.strftime("%Y%m%d")


# ── 개별 종목 일별 시세 ────────────────────────────────────────
async def fetch_stock_history(fetcher: Fetcher, key: str, code: str,
                              days_back: int = 400) -> pd.DataFrame:
    """단축코드(6자리) 종목의 최근 days_back일 일별 시세(오름차순).

    컬럼: [일자, 종가, 시가, 고가, 저가, 등락률(%), 거래량, 거래대금, 상장주식수, 시가총액]
    우선주/유사코드 혼입을 막기 위해 srtnCd == code 로 정확히 필터한다.
    """
    if not key or not code:
        return pd.DataFrame()
    end = date.today()
    begin = end - timedelta(days=days_back)
    rows = await _get(fetcher, key, STOCK_URL, {
        "likeSrtnCd": code, "beginBasDt": _ymd(begin), "endBasDt": _ymd(end),
    }, num_rows=days_back + 50)
    rows = [r for r in rows if str(r.get("srtnCd", "")).zfill(6) == code]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([{
        "일자": pd.to_datetime(r.get("basDt"), format="%Y%m%d", errors="coerce"),
        "종목명": r.get("itmsNm"),
        "시장": r.get("mrktCtg"),
        "종가": _num(r.get("clpr")),
        "시가": _num(r.get("mkp")),
        "고가": _num(r.get("hipr")),
        "저가": _num(r.get("lopr")),
        "등락률(%)": _num(r.get("fltRt")),
        "거래량": _num(r.get("trqu")),
        "거래대금": _num(r.get("trPrc")),
        "상장주식수": _num(r.get("lstgStCnt")),
        "시가총액": _num(r.get("mrktTotAmt")),
    } for r in rows])
    return df.dropna(subset=["일자"]).drop_duplicates("일자").sort_values("일자").reset_index(drop=True)


# ── 지수 일별 시세 ─────────────────────────────────────────────
async def fetch_index_history(fetcher: Fetcher, key: str, idx_name: str,
                              days_back: int = 400) -> pd.DataFrame:
    """지수명(예: '코스피','코스닥')의 최근 days_back일 일별 종가(오름차순).

    컬럼: [일자, 종가, 등락률(%), 연중최고, 연중최저]
    """
    if not key or not idx_name:
        return pd.DataFrame()
    end = date.today()
    begin = end - timedelta(days=days_back)
    rows = await _get(fetcher, key, INDEX_URL, {
        "idxNm": idx_name, "beginBasDt": _ymd(begin), "endBasDt": _ymd(end),
    }, num_rows=days_back + 50)
    # 동일 idxNm 정확 일치만 (코스피200 등 유사명 제외)
    rows = [r for r in rows if r.get("idxNm") == idx_name]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([{
        "일자": pd.to_datetime(r.get("basDt"), format="%Y%m%d", errors="coerce"),
        "종가": _num(r.get("clpr")),
        "등락률(%)": _num(r.get("fltRt")),
        "연중최고": _num(r.get("yrWRcrdHgst")),
        "연중최저": _num(r.get("yrWRcrdLwst")),
    } for r in rows])
    return df.dropna(subset=["일자"]).drop_duplicates("일자").sort_values("일자").reset_index(drop=True)


# ── 배당 이력 (예탁결제원) ─────────────────────────────────────
async def fetch_dividend_history(fetcher: Fetcher, key: str, *,
                                 crno: str | None = None,
                                 name: str | None = None) -> pd.DataFrame:
    """보통주 현금배당 이력(배당기준일 내림차순, 최근 8건).

    crno(법인등록번호, DART jurir_no) 우선, 없으면 회사명으로 조회.
    컬럼: [배당기준일, 현금배당지급일, 주당현금배당금, 현금배당률(%), 액면가]
    """
    if not key or not (crno or name):
        return pd.DataFrame()
    params: dict = {}
    if crno:
        params["crno"] = crno
    if name:
        params["stckIssuCmpyNm"] = name
    rows = await _get(fetcher, key, DIVI_URL, params, num_rows=100)
    # 보통주 + 실제 현금배당 발생분만
    out = []
    for r in rows:
        if r.get("scrsItmsKcdNm") not in (None, "", "보통주"):
            continue
        amt = _num(r.get("stckGenrDvdnAmt"))
        bas = pd.to_datetime(r.get("dvdnBasDt"), format="%Y%m%d", errors="coerce")
        if bas is pd.NaT or amt is None or amt <= 0:
            continue
        out.append({
            "배당기준일": bas,
            "현금배당지급일": r.get("cashDvdnPayDt") or "",
            "주당현금배당금": amt,
            "현금배당률(%)": _num(r.get("stckGenrCashDvdnRt")),
            "액면가": _num(r.get("stckParPrc")),
        })
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out).drop_duplicates("배당기준일")
    return df.sort_values("배당기준일", ascending=False).head(8).reset_index(drop=True)


# ── 지배구조: 주주정보(최대주주·특수관계인 지분) ─────────────────────
GOV_SH_URL = f"{BASE}/service/GetCorpGoveInfoService/getStockholderInfo"


async def fetch_governance_shareholders(fetcher: Fetcher, key: str, crno: str) -> dict:
    """금융위 지배구조정보(getStockholderInfo)로 최대주주·특수관계인 지분을 수집.

    crno(법인등록번호)로 조회 → 지분율이 채워진 가장 최근 기준일(basDt)의
    의결권 있는 주식(보통주) 기준 주주별 지분율 집계.
    반환: {year, holders:[{성명,관계,지분율(%)}], 최대주주측합계(%)} (DART 수집과 동일 형식).
    """
    if not key or not crno:
        return {}
    rows = await _get(fetcher, key, GOV_SH_URL, {"crno": crno}, num_rows=300)
    if not rows:
        return {}

    def rat(r):
        try:
            s = str(r.get("sthdEoteShrRatCtt") or "").replace(",", "").strip()
            return float(s) if s else None
        except (ValueError, TypeError):
            return None

    dated = [(str(r.get("basDt", "")), r) for r in rows if rat(r) is not None]
    if not dated:
        return {}
    latest = max(bd for bd, _ in dated)
    sel = [r for bd, r in dated if bd == latest]
    common = [r for r in sel
              if ("의결권 있는" in str(r.get("stckCsfNm", "")) or "보통" in str(r.get("stckCsfNm", "")))]
    use = common if common else sel

    agg = {}
    for r in use:
        nm = str(r.get("sthdFnm", "")).strip()
        if not nm:
            continue
        if nm not in agg:
            agg[nm] = {"성명": nm, "관계": str(r.get("maxSthdRltNm", "") or "").strip(),
                       "지분율(%)": 0.0}
        agg[nm]["지분율(%)"] += (rat(r) or 0.0)
    holders = sorted(agg.values(), key=lambda x: x["지분율(%)"], reverse=True)
    for h in holders:
        h["지분율(%)"] = round(h["지분율(%)"], 2)
    if not holders:
        return {}
    total = round(sum(h["지분율(%)"] for h in holders), 2)
    return {"year": latest[:4], "holders": holders, "최대주주측합계(%)": total}
