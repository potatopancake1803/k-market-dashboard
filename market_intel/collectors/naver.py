"""네이버 금융 실시간(지연) 시세 수집기.

DART·금융위 시세는 전 거래일 종가(EOD) 기준이므로, '현재 시각' 호가를
보여주기 위해 네이버 금융 폴링 API로 실시간(약간 지연) 현재가를 가져온다.
"""
from __future__ import annotations

import asyncio
import io
import math
import re
from datetime import datetime, timedelta

import pandas as pd

from ..httpx_client import Fetcher

_POLL_URL = "https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
_UP, _DOWN = {"1", "2"}, {"4", "5"}  # 네이버 등락 코드(2=상승, 5=하락)


def _to_num(s):
    try:
        return float(str(s).replace(",", "")) if s not in (None, "") else None
    except (ValueError, TypeError):
        return None


async def fetch_realtime_price(fetcher: Fetcher, code: str) -> dict:
    """종목코드의 실시간(지연) 현재가. 실패 시 빈 dict.

    반환: {현재가, 전일대비, 등락률(%), 방향('▲'/'▼'/'-'), 장상태, 조회시각}
    """
    if not code:
        return {}
    status, payload = await fetcher.fetch(
        _POLL_URL.format(code=code),
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"},
        parse="json", cache=False,
    )
    if status != 200 or not isinstance(payload, dict):
        return {}
    datas = payload.get("datas") or []
    if not datas or not isinstance(datas[0], dict):
        return {}
    d = datas[0]
    price = _to_num(d.get("closePrice"))
    if price is None:
        return {}
    cmp_code = str((d.get("compareToPreviousPrice") or {}).get("code", "3"))
    arrow = "▲" if cmp_code in _UP else ("▼" if cmp_code in _DOWN else "-")
    diff = _to_num(d.get("compareToPreviousClosePrice"))
    if diff is not None and arrow == "▼":
        diff = -abs(diff)
    rate = _to_num(d.get("fluctuationsRatio"))
    if rate is not None and arrow == "▼":
        rate = -abs(rate)
    mkt = d.get("stockExchangeType") or {}
    return {
        "현재가": price,
        "전일대비": diff,
        "등락률(%)": rate,
        "방향": arrow,
        "장상태": d.get("marketStatus") or mkt.get("nameKor", ""),
        "조회시각": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── ETF 분석(구성종목·섹터/국가/자산 비중·운용사·총보수) ───────────
_ETF_URL = "https://m.stock.naver.com/api/stock/{code}/etfAnalysis"
_SECTOR_KR = {
    "IT": "IT", "FINANCIALS": "금융", "FINANCE": "금융", "COMMUNICATION": "커뮤니케이션",
    "COMMUNICATION_SERVICES": "커뮤니케이션", "CONSUMER_DISCRETIONARY": "경기소비재",
    "CONSUMER_STAPLES": "필수소비재", "HEALTHCARE": "헬스케어", "INDUSTRIALS": "산업재",
    "ENERGY": "에너지", "UTILITIES": "유틸리티", "MATERIALS": "소재",
    "REAL_ESTATE": "부동산", "UNCLASSIFIED": "미분류", "OTHERS": "기타",
}
_COUNTRY_KR = {"KR": "한국", "US": "미국", "JP": "일본", "CN": "중국", "HK": "홍콩",
               "TW": "대만", "IN": "인도", "VN": "베트남", "EU": "유럽",
               "MISC": "기타", "OTHERS": "기타"}
_ASSET_KR = {"EQUITY": "주식", "BOND": "채권", "CASH": "현금", "DERIVATIVES": "파생상품",
             "REIT": "리츠", "COMMODITY": "원자재", "OTHERS": "기타"}


def _pct(s):
    try:
        s = str(s).replace("%", "").replace(",", "").strip()
        return float(s) if s not in ("", "-", "None") else None
    except (ValueError, TypeError):
        return None


_PERIOD_KR = {"D1": "1일", "W1": "1주", "M1": "1개월", "M3": "3개월", "M6": "6개월",
              "YTD": "연초이후", "Y1": "1년", "Y3": "3년", "Y5": "5년", "Y10": "10년"}
_PERIOD_ORDER = ["1일", "1주", "1개월", "3개월", "6개월", "1년", "3년", "5년", "10년", "연초이후"]


def _portfolio(lst, mapping):
    out = []
    for it in lst or []:
        w = it.get("weight")
        if w is None:
            continue
        out.append({"구분": mapping.get(it.get("detailTypeCode"), it.get("detailTypeCode")),
                    "비중(%)": round(float(w), 2)})
    return out


def _returns(d: dict) -> list[dict]:
    """시장가(returnPerformanceList)·NAV(navPerformanceList) 기간수익률 병합."""
    def m(key):
        return {_PERIOD_KR.get(x.get("periodTypeCode"), x.get("periodTypeCode")): x.get("value")
                for x in (d.get(key) or [])}
    mkt, nav = m("returnPerformanceList"), m("navPerformanceList")
    out = []
    for p in _PERIOD_ORDER:
        if p in mkt or p in nav:
            out.append({"기간": p, "시장가(%)": mkt.get(p), "NAV(%)": nav.get(p)})
    return out


async def fetch_price_chart(fetcher: Fetcher, code: str, days: int = 370) -> list[dict]:
    """네이버 차트 API로 종목/ETF 일별 OHLCV(최근 days일).

    반환: [{일자, 시가, 고가, 저가, 종가, 거래량}] (오름차순).
    """
    from datetime import date, timedelta
    if not code:
        return []
    end = date.today()
    start = end - timedelta(days=days)
    url = (f"https://api.stock.naver.com/chart/domestic/item/{code}/day"
           f"?startDateTime={start:%Y%m%d}0000&endDateTime={end:%Y%m%d}0000")
    status, payload = await fetcher.fetch(
        url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"},
        parse="json", cache=False)
    if status != 200 or not isinstance(payload, list):
        return []
    out = []
    for r in payload:
        ld, cp = r.get("localDate"), r.get("closePrice")
        if ld and cp is not None and len(str(ld)) == 8:
            ld = str(ld)
            out.append({
                "일자": f"{ld[:4]}-{ld[4:6]}-{ld[6:8]}",
                "시가": _to_num(r.get("openPrice")), "고가": _to_num(r.get("highPrice")),
                "저가": _to_num(r.get("lowPrice")), "종가": _to_num(cp),
                "거래량": _to_num(r.get("accumulatedTradingVolume")),
            })
    return out


async def fetch_realtime_quotes(fetcher: Fetcher, codes: list[str]) -> dict[str, dict]:
    """여러 종목 실시간(지연) 시세를 한 번에 — {종목코드: {현재가,전일대비,등락률(%),방향}}."""
    codes = [c for c in dict.fromkeys(codes) if c]
    if not codes:
        return {}
    status, payload = await fetcher.fetch(
        _POLL_URL.format(code=",".join(codes)),
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"},
        parse="json", cache=False)
    out: dict[str, dict] = {}
    if status != 200 or not isinstance(payload, dict):
        return out
    for d in payload.get("datas") or []:
        code = d.get("itemCode")
        price = _to_num(d.get("closePrice"))
        if not code or price is None:
            continue
        cc = str((d.get("compareToPreviousPrice") or {}).get("code", "3"))
        arrow = "▲" if cc in _UP else ("▼" if cc in _DOWN else "-")
        diff = _to_num(d.get("compareToPreviousClosePrice"))
        rate = _to_num(d.get("fluctuationsRatio"))
        if arrow == "▼":
            diff = -abs(diff) if diff is not None else None
            rate = -abs(rate) if rate is not None else None
        out[code] = {"현재가": price, "전일대비": diff, "등락률(%)": rate, "방향": arrow}
    return out


async def fetch_etf_analysis(fetcher: Fetcher, code: str) -> dict:
    """네이버 ETF 분석 — 구성종목 Top10·섹터/국가/자산 비중·운용사·총보수 등.

    실패 시 빈 dict. 해외 ETF는 구성종목 비중이 제공되지 않을 수 있다(비중=None).
    """
    if not code:
        return {}
    status, payload = await fetcher.fetch(
        _ETF_URL.format(code=code),
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"},
        parse="json", cache=False)
    if status != 200 or not isinstance(payload, dict) or not payload.get("itemCode"):
        return {}
    d = payload
    top10 = [{
        "순위": it.get("seq"), "종목코드": it.get("itemCode") or "",
        "종목명": it.get("itemName"), "주식수": _pct(it.get("stockCount")),
        "비중(%)": _pct(it.get("etfWeight")),
    } for it in d.get("etfTop10MajorConstituentAssets", []) if it.get("itemName")]
    div = d.get("dividend") or {}
    return {
        "운용사": d.get("issuerName"), "총보수": d.get("totalFee"),
        "상장일": d.get("listedDate"), "기초지수": d.get("etfBaseIndex"),
        "추적오차율": d.get("chaseErrorRate"), "괴리율": d.get("deviationRate"),
        "배당수익률": div.get("dividendYieldTtm"), "요약": d.get("etfSummary"),
        "top10": top10, "returns": _returns(d),
        "sectors": _portfolio(d.get("sectorPortfolioList"), _SECTOR_KR),
        "countries": _portfolio(d.get("countryPortfolioList"), _COUNTRY_KR),
        "assets": _portfolio(d.get("assetPortfolioList"), _ASSET_KR),
    }


# ── 투자자별 매매 동향 (외국인·기관·개인 일별 순매수) ────────────────
_TREND_URL = "https://m.stock.naver.com/api/stock/{code}/trend"


def _ymd_dot(s) -> str:
    """'20260602' → '2026. 06. 02.'."""
    s = str(s or "")
    return f"{s[:4]}. {s[4:6]}. {s[6:8]}." if len(s) == 8 and s.isdigit() else (s or "-")


def _signed_qty(s) -> str:
    """순매수량 문자열을 '+44,053 주' / '-60,984 주' 형태로. 부호 없으면 +."""
    s = str(s or "").strip()
    if s in ("", "0", "-"):
        return "0 주"
    if s[0] not in "+-":
        s = "+" + s
    return f"{s} 주"


async def fetch_investor_trend(fetcher: Fetcher, code: str, days: int = 30) -> list[dict]:
    """네이버 금융 투자자별 매매 동향 — 최근 days 영업일.

    반환: [{날짜, 종가, 전일대비, 등락률, 거래량, 외국인, 기관, 개인}] (최신순).
    외국인/기관/개인은 일별 순매수량(주), 등락률은 종가·전일대비로 산출.
    """
    if not code:
        return []
    status, payload = await fetcher.fetch(
        _TREND_URL.format(code=code) + f"?pageSize={max(days, 10)}",
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"},
        parse="json", cache=False)
    if status != 200 or not isinstance(payload, list):
        return []
    out = []
    for r in payload[:days]:
        close = _to_num(r.get("closePrice"))
        diff = _to_num(r.get("compareToPreviousClosePrice"))   # 부호 포함될 수 있음
        cmp_ = r.get("compareToPreviousPrice") or {}
        direction = str(cmp_.get("text") or "보합")             # 상승 / 하락 / 보합
        # 부호 일관성 보정: 크기는 abs로 통일하고 방향 라벨로 부호를 다시 부여
        mag = abs(diff) if diff is not None else None
        signed = None
        if mag is not None:
            signed = -mag if direction == "하락" else (mag if direction == "상승" else 0.0)
        # 등락률 = 전일대비 / 전일종가 × 100 (전일종가 = 종가 - 전일대비)
        rate = None
        if close is not None and signed is not None:
            prev = close - signed
            if prev:
                rate = round(signed / prev * 100, 2)
        out.append({
            "날짜": _ymd_dot(r.get("bizdate")),
            "종가": f"{close:,.0f}" if close is not None else "-",
            "전일대비": f"{direction} {mag:,.0f}".strip() if mag is not None else "-",
            "등락률": f"{rate:+.2f}%" if rate is not None else "-",
            "거래량": (f"{_to_num(r.get('accumulatedTradingVolume')):,.0f} 주"
                       if _to_num(r.get("accumulatedTradingVolume")) is not None else "-"),
            "외국인": _signed_qty(r.get("foreignerPureBuyQuant")),
            "기관": _signed_qty(r.get("organPureBuyQuant")),
            "개인": _signed_qty(r.get("individualPureBuyQuant")),
        })
    return out


# ── 애널리스트 컨센서스 + 최근 리서치 리포트 ───────────────────────
_INTEGRATION_URL = "https://m.stock.naver.com/api/stock/{code}/integration"


async def fetch_consensus(fetcher: Fetcher, code: str, n_reports: int = 8) -> dict:
    """네이버 통합 API에서 애널리스트 컨센서스·최근 리서치 리포트를 수집.

    반환: {recomm_mean(1~5 평균 투자의견), target_mean(평균 목표주가, 원),
           create_date, researches:[{증권사, 제목, 작성일}]}.
    """
    if not code:
        return {}
    status, payload = await fetcher.fetch(
        _INTEGRATION_URL.format(code=code),
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"},
        parse="json", cache=False)
    if status != 200 or not isinstance(payload, dict):
        return {}
    ci = payload.get("consensusInfo") or {}
    researches = []
    for r in (payload.get("researches") or [])[:n_reports]:
        wdt = str(r.get("wdt", ""))
        researches.append({
            "증권사": r.get("bnm", "") or "-",
            "제목": r.get("tit", "") or "-",
            "작성일": f"{wdt[:4]}-{wdt[4:6]}-{wdt[6:8]}" if len(wdt) == 8 else wdt,
        })
    return {
        "recomm_mean": _to_num(ci.get("recommMean")),
        "target_mean": _to_num(ci.get("priceTargetMean")),
        "create_date": ci.get("createDate", ""),
        "researches": researches,
    }


# ── 재무 요약(연간·분기): 실적·재무·안정성 차트용 ───────────────────
_FIN_MAIN_URL = "https://finance.naver.com/item/main.naver?code={code}"
_FIN_ROWMAP = {"매출액": "매출", "영업이익": "영업이익", "당기순이익": "순이익",
               "부채비율": "부채비율", "당좌비율": "당좌비율"}
_FIN_METRICS = ["매출", "영업이익", "순이익", "부채비율", "당좌비율"]


def _fin_num(v):
    try:
        f = float(str(v).replace(",", "").strip())
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


async def fetch_financial_summary(fetcher: Fetcher, code: str) -> dict:
    """네이버 금융 '기업실적분석' 표 → 연간/분기 매출·영업이익·순이익·부채비율·당좌비율.

    반환: {"annual": {"periods":[...], "series": {지표:[...]}},
           "quarter": {"periods":[...], "series": {지표:[...]}}}.
    (네이버 표는 유동비율 대신 당좌비율을 제공 — 안정성 토글에 당좌비율 사용)
    """
    if not code:
        return {}
    status, content = await fetcher.fetch(
        _FIN_MAIN_URL.format(code=code), headers={"User-Agent": "Mozilla/5.0"},
        parse="bytes", cache=False)
    if status != 200 or not content:
        return {}
    try:
        html_text = content.decode("utf-8", errors="replace")
        tables = pd.read_html(io.StringIO(html_text))
    except Exception:  # noqa: BLE001
        return {}
    target = None
    for t in tables:
        try:
            col0 = [str(x) for x in t.iloc[:, 0].tolist()]
        except Exception:  # noqa: BLE001
            continue
        if "매출액" in col0 and "부채비율" in col0:
            target = t
            break
    if target is None:
        return {}

    key = target.columns[0]
    rowmap = {}
    for _, r in target.iterrows():
        nm = str(r[key]).strip()
        if nm in _FIN_ROWMAP:
            rowmap[_FIN_ROWMAP[nm]] = r

    def grp(c):
        return str(c[0]) if isinstance(c, tuple) and len(c) > 0 else ""

    def per(c):
        return str(c[1]) if isinstance(c, tuple) and len(c) > 1 else str(c)

    _QMAP = {"03": "1Q", "06": "2Q", "09": "3Q", "12": "4Q"}

    def fmt_period(p, bucket):
        """'2023.12'→'2023', '2025.03'→'25.1Q', (E) 보존. 차트 x축 라벨용."""
        p = str(p).strip()
        est = "(E)" in p
        core = p.replace("(E)", "").strip()
        parts = core.split(".")
        if len(parts) != 2:
            return p
        y, mm = parts[0], parts[1]
        if bucket == "annual":
            lbl = y                                  # 2023
        else:
            lbl = f"{y[2:]}.{_QMAP.get(mm, mm)}"     # 25.1Q
        return lbl + ("(E)" if est else "")

    out = {b: {"periods": [], "series": {m: [] for m in _FIN_METRICS}}
           for b in ("annual", "quarter")}
    for c in target.columns[1:]:
        g = grp(c)
        bucket = "annual" if "연간" in g else ("quarter" if "분기" in g else None)
        if bucket is None:
            continue
        out[bucket]["periods"].append(fmt_period(per(c), bucket))
        for m in _FIN_METRICS:
            row = rowmap.get(m)
            out[bucket]["series"][m].append(_fin_num(row[c]) if row is not None else None)
    return out


# ── 애널리스트 리서치 리포트(투자의견·링크 포함, 최근 N개월) ──────────
_RES_LIST_URL = ("https://finance.naver.com/research/company_list.naver"
                 "?searchType=itemCode&itemCode={code}&page=1")
_RES_READ_URL = "https://finance.naver.com/research/company_read.naver?nid={nid}"


def _parse_res_date(s: str):
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%y.%m.%d")
    except ValueError:
        return None


async def fetch_research_reports(fetcher: Fetcher, code: str,
                                 months: int = 3, limit: int = 12) -> list[dict]:
    """최근 months 개월 애널리스트 리포트 — 증권사·제목·투자의견·작성일·링크.

    목록은 네이버 리서치, 투자의견/목표주가는 각 리포트 상세에서 병렬 수집.
    링크: https://stock.naver.com/domestic/stock/{code}/research/{nid}
    """
    if not code:
        return []
    status, content = await fetcher.fetch(
        _RES_LIST_URL.format(code=code), headers={"User-Agent": "Mozilla/5.0"},
        parse="bytes", cache=False)
    if status != 200 or not content:
        return []
    html_text = content.decode("euc-kr", errors="replace")
    pairs = re.findall(r'company_read\.naver\?nid=(\d+)[^"]*"[^>]*>([^<]+)</a>', html_text)
    if not pairs:
        return []
    # 제목 → (증권사, 작성일) 매핑 (목록 표에서)
    meta = {}
    try:
        for t in pd.read_html(io.StringIO(html_text)):
            cols = set(map(str, t.columns))
            if {"제목", "증권사", "작성일"}.issubset(cols):
                for _, r in t.dropna(subset=["제목"]).iterrows():
                    meta[str(r["제목"]).strip()] = (str(r.get("증권사", "")).strip(),
                                                    str(r.get("작성일", "")).strip())
                break
    except Exception:  # noqa: BLE001
        pass

    cutoff = datetime.now() - timedelta(days=months * 31)
    picked = []
    seen = set()
    for nid, tit in pairs:
        tit = tit.strip()
        if nid in seen:
            continue
        seen.add(nid)
        broker, wdt = meta.get(tit, ("", ""))
        dt = _parse_res_date(wdt)
        if dt and dt < cutoff:
            continue
        picked.append({"nid": nid, "제목": tit, "증권사": broker,
                       "작성일": (dt.strftime("%Y-%m-%d") if dt else wdt)})
        if len(picked) >= limit:
            break

    async def _detail(item):
        s, c = await fetcher.fetch(_RES_READ_URL.format(nid=item["nid"]),
                                   headers={"User-Agent": "Mozilla/5.0"},
                                   parse="bytes", cache=True)
        op, tp = "", ""
        if s == 200 and c:
            txt = re.sub(r"<[^>]+>", " ", c.decode("euc-kr", errors="replace"))
            mo = re.search(r"투자의견\s+([가-힣A-Za-z.]+)", txt)
            mt = re.search(r"목표주가\s+([\d,]+)", txt)
            op = mo.group(1).strip() if mo else ""
            tp = mt.group(1).strip() if mt else ""
        _en = {"buy": "매수", "strongbuy": "적극매수", "hold": "중립", "neutral": "중립",
               "marketperform": "중립", "outperform": "매수", "overweight": "매수",
               "sell": "매도", "underperform": "매도", "reduce": "매도"}
        item["투자의견"] = _en.get(op.lower().replace(" ", ""), op)
        item["목표주가"] = tp
        item["link"] = f"https://stock.naver.com/domestic/stock/{code}/research/{item['nid']}"
        return item

    return await asyncio.gather(*[_detail(it) for it in picked]) if picked else []
