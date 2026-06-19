"""한국투자증권(KIS) Open API 컬렉터 — 한국투자증권_API_New 명세 기반.

리포트 빌더(company_report_ver2 / etf_dashboard_ver2)에서 쓰는 async 수집기.
토큰은 ~/.cache/kmkt_m4/kis_token.json 을 market_dashboard3_realtime.py 와 공유한다
(KIS 토큰 발급은 분당 1회 제한 — 반드시 캐시 재사용).

사용 API (한국투자증권_API_New/*.xlsx):
  · 국내주식 종목투자의견 [국내주식-188]  FHKST663300C0  invest-opinion
  · 종목별 투자자매매동향(일별)           FHPTJ04160001  investor-trade-by-stock-daily
  · 국내주식 안정성비율 [v1_국내주식-083]  FHKST66430600  finance/stability-ratio
  · 국내ETF NAV (실시간-051 의 REST 보조)  FHPST02400000  etfetn inquire-price
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

BASE = os.environ.get("KIS_BASE", "https://openapi.koreainvestment.com:9443")
_TOKEN_FILE = Path.home() / ".cache" / "kmkt_m4" / "kis_token.json"
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


def _keys() -> tuple[str | None, str | None]:
    ak, sk = os.environ.get("KIS_APP_KEY"), os.environ.get("KIS_APP_SECRET")
    if ak and sk:
        return ak.strip(), sk.strip()
    try:
        for ln in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            if ln.startswith("KIS_APP_KEY="):
                ak = ln.split("=", 1)[1].strip()
            elif ln.startswith("KIS_APP_SECRET="):
                sk = ln.split("=", 1)[1].strip()
    except Exception:  # noqa: BLE001
        pass
    return ak, sk


def _token() -> str | None:
    """디스크 캐시 우선 토큰 (만료 60초 전 갱신). 동기 — 호출 빈도 낮음."""
    now = time.time()
    try:
        d = json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
        if d.get("access_token") and now < float(d.get("expire", 0)) - 60:
            return d["access_token"]
    except Exception:  # noqa: BLE001
        pass
    ak, sk = _keys()
    if not ak or not sk:
        return None
    try:
        r = httpx.post(f"{BASE}/oauth2/tokenP", timeout=12,
                       json={"grant_type": "client_credentials", "appkey": ak, "appsecret": sk})
        j = r.json()
        tok = j.get("access_token")
        if not tok:
            return None
        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(json.dumps(
            {"access_token": tok, "expire": now + float(j.get("expires_in", 86400))}),
            encoding="utf-8")
        return tok
    except Exception:  # noqa: BLE001
        return None


async def _aget(path: str, tr_id: str, params: dict) -> dict:
    """공용 GET. 실패/키없음 시 빈 dict."""
    tok = _token()
    ak, sk = _keys()
    if not tok or not ak:
        return {}
    try:
        async with httpx.AsyncClient(timeout=12) as cl:
            r = await cl.get(f"{BASE}{path}",
                             headers={"authorization": f"Bearer {tok}", "appkey": ak,
                                      "appsecret": sk, "tr_id": tr_id, "custtype": "P"},
                             params=params)
            j = r.json()
            return j if j.get("rt_cd") == "0" else {}
    except Exception:  # noqa: BLE001
        return {}


def _num(v, default=None):
    try:
        f = float(str(v).replace(",", "").strip())
        return f
    except (ValueError, TypeError):
        return default


# ── 투자의견 (188) ──────────────────────────────────────────────
# 의견 문자열 → 5점 스케일 (네이버 recommMean 호환: 5 적극매수 · 4 매수 · 3 중립 · 2 매도 · 1 적극매도)
_OPN_SCORE = [
    (("적극매수", "강력매수", "STRONG BUY", "STRONGBUY"), 5.0),
    (("매수", "BUY", "OUTPERFORM", "OVERWEIGHT", "비중확대", "TRADING BUY"), 4.0),
    (("중립", "보유", "HOLD", "NEUTRAL", "MARKETPERFORM", "MARKET PERFORM"), 3.0),
    (("매도", "SELL", "UNDERPERFORM", "UNDERWEIGHT", "비중축소", "REDUCE"), 2.0),
    (("적극매도", "강력매도", "STRONG SELL"), 1.0),
]


def _opn_score(s: str) -> float | None:
    u = (s or "").strip().upper()
    if not u or "NOT" in u or u in ("N/R", "NR", "-"):
        return None
    # 더 구체적인(강력/적극) 패턴 먼저
    for keys, sc in (_OPN_SCORE[0], _OPN_SCORE[4], _OPN_SCORE[1], _OPN_SCORE[3], _OPN_SCORE[2]):
        for k in keys:
            if k in u:
                return sc
    return None


async def fetch_invest_opinions(code: str, months: int = 12) -> dict:
    """국내주식 종목투자의견 [188] — 증권사별 의견·목표가 + 컨센서스 집계.

    반환: {opinions: [{일자,증권사,투자의견,직전의견,목표가,괴리율}],   (최신순, 전체)
           recomm_mean (5점), target_mean, n_buy/n_hold/n_sell,        (증권사별 최신 의견 기준)
           create_date}
    """
    if not (code and code.isdigit()):
        return {}
    d2 = date.today()
    d1 = d2 - timedelta(days=int(months * 30.5))
    j = await _aget("/uapi/domestic-stock/v1/quotations/invest-opinion", "FHKST663300C0",
                    {"FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "16633",
                     "FID_INPUT_ISCD": code,
                     "FID_INPUT_DATE_1": d1.strftime("%Y%m%d"),
                     "FID_INPUT_DATE_2": d2.strftime("%Y%m%d")})
    rows = j.get("output") or []
    if not rows:
        return {}
    opinions = []
    for o in rows:
        dt = str(o.get("stck_bsop_date") or "")
        opinions.append({
            "일자": f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if len(dt) == 8 else dt,
            "증권사": o.get("mbcr_name") or "-",
            "투자의견": o.get("invt_opnn") or "-",
            "직전의견": o.get("rgbf_invt_opnn") or "-",
            "목표가": _num(o.get("hts_goal_prc")),
            "괴리율(%)": _num(o.get("dprt")),
        })
    # 컨센서스: 최근 6개월 내 증권사별 '최신' 의견만 집계 (rows 는 최신순)
    cutoff = (d2 - timedelta(days=183)).strftime("%Y-%m-%d")
    latest: dict[str, dict] = {}
    for op in opinions:
        if op["일자"] >= cutoff and op["증권사"] not in latest:
            latest[op["증권사"]] = op
    scores = [s for op in latest.values() if (s := _opn_score(op["투자의견"])) is not None]
    targets = [t for op in latest.values() if (t := op["목표가"]) and t > 0]
    n_buy = sum(1 for s in scores if s >= 3.5)
    n_hold = sum(1 for s in scores if 2.5 <= s < 3.5)
    n_sell = sum(1 for s in scores if s < 2.5)
    return {
        "opinions": opinions,
        "recomm_mean": round(sum(scores) / len(scores), 2) if scores else None,
        "target_mean": round(sum(targets) / len(targets)) if targets else None,
        "n_buy": n_buy, "n_hold": n_hold, "n_sell": n_sell,
        "n_brokers": len(latest),
        "create_date": opinions[0]["일자"] if opinions else "",
    }


# ── 투자자 매매동향 일별 (FHPTJ04160001) ────────────────────────
def _signed(v) -> str:
    n = _num(v)
    if n is None:
        return "-"
    return f"{n:+,.0f}"


async def fetch_investor_trend(code: str, days: int = 30) -> list[dict]:
    """종목별 투자자매매동향(일별) — naver.fetch_investor_trend 와 동일 형식 반환.

    [{날짜, 종가, 전일대비, 등락률, 거래량, 외국인, 기관, 개인}] (최신순)
    ⚠ KIS 서비스 시간 제한(00:00~15:40 조회 불가) 시 빈 리스트 → 호출부에서 네이버 폴백.
    """
    if not (code and code.isdigit()):
        return []
    j = await _aget("/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily",
                    "FHPTJ04160001",
                    {"FID_COND_MRKT_DIV_CODE": "UN", "FID_INPUT_ISCD": code,
                     "FID_INPUT_DATE_1": date.today().strftime("%Y%m%d"),
                     "FID_ORG_ADJ_PRC": "", "FID_ETC_CLS_CODE": "1"})
    rows = j.get("output2") or j.get("output1") or j.get("output") or []
    if isinstance(rows, dict):
        rows = [rows]
    out = []
    for r in rows[:days]:
        dt = str(r.get("stck_bsop_date") or "")
        close = _num(r.get("stck_clpr"))
        diff = _num(r.get("prdy_vrss"))
        sign = str(r.get("prdy_vrss_sign") or "3")
        dirc = "상승" if sign in ("1", "2") else ("하락" if sign in ("4", "5") else "보합")
        rate = _num(r.get("prdy_ctrt"))
        vol = _num(r.get("acml_vol"))
        out.append({
            "날짜": f"{dt[4:6]}.{dt[6:8]}" if len(dt) == 8 else dt,
            "종가": f"{close:,.0f}" if close is not None else "-",
            "전일대비": f"{dirc} {abs(diff):,.0f}" if diff is not None else "-",
            "등락률": f"{rate:+.2f}%" if rate is not None else "-",
            "거래량": f"{vol:,.0f} 주" if vol is not None else "-",
            "외국인": _signed(r.get("frgn_ntby_qty")),
            "기관": _signed(r.get("orgn_ntby_qty")),
            "개인": _signed(r.get("prsn_ntby_qty")),
        })
    return out


# ── 안정성비율 (083) — 유동비율 포함 ────────────────────────────
def _yymm(s: str) -> str:
    s = str(s or "")
    return f"{s[:4]}.{s[4:6]}" if len(s) >= 6 else s


async def fetch_stability_ratios(code: str) -> dict:
    """국내주식 안정성비율 [083] — 연간·분기 부채비율/차입금의존도/유동비율/당좌비율.

    반환: {"annual": {"periods": ["2023.12",...], "series": {지표: [..]}},
           "quarter": {...}}  (옛 결산 → 최신 순)
    """
    if not (code and code.isdigit()):
        return {}
    out: dict = {}
    for div, key in (("0", "annual"), ("1", "quarter")):
        j = await _aget("/uapi/domestic-stock/v1/finance/stability-ratio", "FHKST66430600",
                        {"FID_DIV_CLS_CODE": div, "fid_cond_mrkt_div_code": "J",
                         "fid_input_iscd": code})
        rows = j.get("output") or []
        if not rows:
            continue
        rows = sorted(rows, key=lambda r: str(r.get("stac_yymm") or ""))
        out[key] = {
            "periods": [_yymm(r.get("stac_yymm")) for r in rows],
            "series": {
                "부채비율": [_num(r.get("lblt_rate")) for r in rows],
                "유동비율": [_num(r.get("crnt_rate")) for r in rows],
                "당좌비율": [_num(r.get("quck_rate")) for r in rows],
                "차입금의존도": [_num(r.get("bram_depn")) for r in rows],
            },
        }
    return out


# ── 주식기본조회 (067) — 기업 기본정보 ──────────────────────────
_MKET_NAME = {"STK": "코스피(유가증권)", "KSQ": "코스닥", "KNX": "코넥스"}


def _ymd_dot(s: str) -> str:
    s = str(s or "")
    return f"{s[:4]}.{s[4:6]}.{s[6:8]}" if len(s) == 8 else s


async def fetch_stock_info(code: str) -> dict:
    """주식기본조회 [067] — 시장·업종·상장일·상장주수·액면가·자본금 등 기업 개요.

    반환 dict 주요 키: 종목명, 시장, 업종, 표준산업, 상장일, 상장주수, 액면가(원),
    자본금(억), 결산월, K200여부, NXT가능, 거래정지, 관리종목
    """
    if not (code and code.isdigit()):
        return {}
    j = await _aget("/uapi/domestic-stock/v1/quotations/search-stock-info", "CTPF1002R",
                    {"PRDT_TYPE_CD": "300", "PDNO": code})
    o = j.get("output") or {}
    if not o:
        return {}
    cpta = _num(o.get("cpta"))
    return {
        "종목명": o.get("prdt_abrv_name") or o.get("prdt_name"),
        "영문명": o.get("prdt_eng_abrv_name"),
        "시장": _MKET_NAME.get(str(o.get("mket_id_cd") or ""), o.get("mket_id_cd")),
        "업종": o.get("idx_bztp_mcls_cd_name"),
        "표준산업": o.get("std_idst_clsf_cd_name"),
        "상장일": _ymd_dot(o.get("scts_mket_lstg_dt") or o.get("kosdaq_mket_lstg_dt")),
        "상장주수": _num(o.get("lstg_stqt")),
        "액면가": _num(o.get("papr")),
        "자본금(억)": round(cpta / 1e8) if cpta else None,
        "결산월": (str(o.get("setl_mmdd") or "")[:2].lstrip("0") or None),
        "K200": str(o.get("kospi200_item_yn") or "") == "Y",
        "NXT가능": str(o.get("cptt_trad_tr_psbl_yn") or "") == "Y",
        "거래정지": str(o.get("tr_stop_yn") or "") == "Y",
        "관리종목": str(o.get("admn_item_yn") or "") == "Y",
        "전자증권": str(o.get("elec_scty_yn") or "") == "Y",
    }


# ── 재무·수익성·성장성·기타 비율 (080/081/085/082) ──────────────
async def _ratio_series(path: str, tr_id: str, code: str, fields: dict,
                        annual_only: bool = False) -> dict:
    """연간(+분기) 비율 시계열 공용 수집. fields: {API필드: 표시지표명}."""
    out: dict = {}
    divs = (("0", "annual"),) if annual_only else (("0", "annual"), ("1", "quarter"))
    for div, key in divs:
        j = await _aget(path, tr_id,
                        {"FID_DIV_CLS_CODE": div, "fid_cond_mrkt_div_code": "J",
                         "fid_input_iscd": code})
        rows = j.get("output") or []
        if not rows:
            continue
        rows = sorted(rows, key=lambda r: str(r.get("stac_yymm") or ""))
        out[key] = {
            "periods": [_yymm(r.get("stac_yymm")) for r in rows],
            "series": {name: [_num(r.get(f)) for r in rows] for f, name in fields.items()},
        }
    return out


async def fetch_finance_ratios(code: str) -> dict:
    """재무비율 [080] — ROE/EPS/BPS/SPS/유보율/부채비율/증가율 (연간+분기)."""
    if not (code and code.isdigit()):
        return {}
    return await _ratio_series("/uapi/domestic-stock/v1/finance/financial-ratio",
                               "FHKST66430300", code,
                               {"roe_val": "ROE", "eps": "EPS", "bps": "BPS", "sps": "SPS",
                                "rsrv_rate": "유보율", "lblt_rate": "부채비율",
                                "grs": "매출증가율", "bsop_prfi_inrt": "영업이익증가율",
                                "ntin_inrt": "순이익증가율"})


async def fetch_profit_ratios(code: str) -> dict:
    """수익성비율 [081] — 총자본순이익률/ROE/매출순이익률/매출총이익률 (연간+분기)."""
    if not (code and code.isdigit()):
        return {}
    return await _ratio_series("/uapi/domestic-stock/v1/finance/profit-ratio",
                               "FHKST66430400", code,
                               {"cptl_ntin_rate": "총자본순이익률",
                                "self_cptl_ntin_inrt": "자기자본순이익률(ROE)",
                                "sale_ntin_rate": "매출순이익률",
                                "sale_totl_rate": "매출총이익률"})


async def fetch_growth_ratios(code: str) -> dict:
    """성장성비율 [085] — 매출/영업이익/자기자본/총자산 증가율 (연간+분기)."""
    if not (code and code.isdigit()):
        return {}
    return await _ratio_series("/uapi/domestic-stock/v1/finance/growth-ratio",
                               "FHKST66430800", code,
                               {"grs": "매출증가율", "bsop_prfi_inrt": "영업이익증가율",
                                "equt_inrt": "자기자본증가율", "totl_aset_inrt": "총자산증가율"})


async def fetch_other_ratios(code: str) -> dict:
    """기타주요비율 [082] — 배당성향/EVA/EBITDA/EV·EBITDA (연간만)."""
    if not (code and code.isdigit()):
        return {}
    return await _ratio_series("/uapi/domestic-stock/v1/finance/other-major-ratios",
                               "FHKST66430500", code,
                               {"payout_rate": "배당성향(%)", "eva": "EVA(억)",
                                "ebitda": "EBITDA(억)", "ev_ebitda": "EV/EBITDA"},
                               annual_only=True)


# ── 종목추정실적 (187) — 증권사 컨센서스 추정 ───────────────────
# output2(6행)=[매출액, 매출YoY×10, 영업이익, 영업YoY×10, 순이익, 순YoY×10] (억원·%)
# output3(8행)=[EBITDA, EPS×10, EPS YoY×10, PER×10, EV/EBITDA×10, ROE×10, 부채비율×10, ?]
# output4 = 결산기 5개 (… "2026.12E" 형식, E=추정) — 실측 검증: EPS·PER·ROE·부채비율이
# KIS 080/082 의 실제값과 ×10 스케일로 일치함을 확인.
async def fetch_estimates(code: str) -> dict:
    """종목추정실적 [187] — 결산기별 실적·투자지표 추정 (애널리스트 컨센서스).

    반환: {analyst, est_date, opinion, periods:[...5개],
           rows: {지표명: [값×5]}}  (금액 억원, 비율/배수/원 단위는 ÷10 적용)
    """
    if not (code and code.isdigit()):
        return {}
    j = await _aget("/uapi/domestic-stock/v1/quotations/estimate-perform", "HHKST668300C0",
                    {"SHT_CD": code})
    o1 = j.get("output1") or {}
    o2, o3, o4 = j.get("output2") or [], j.get("output3") or [], j.get("output4") or []
    if not (o1 and o2 and o4):
        return {}

    def vals(row: dict, scale: float = 1.0) -> list:
        out = []
        for k in ("data1", "data2", "data3", "data4", "data5"):
            v = _num(row.get(k))
            out.append(round(v / scale, 2) if (v is not None and scale != 1) else v)
        return out

    rows: dict[str, list] = {}
    try:
        rows["매출액(억)"] = vals(o2[0])
        rows["매출 YoY(%)"] = vals(o2[1], 10)
        rows["영업이익(억)"] = vals(o2[2])
        rows["영업이익 YoY(%)"] = vals(o2[3], 10)
        rows["순이익(억)"] = vals(o2[4])
        rows["순이익 YoY(%)"] = vals(o2[5], 10)
        if len(o3) >= 7:
            rows["EBITDA(억)"] = vals(o3[0])
            rows["EPS(원)"] = vals(o3[1], 10)
            rows["PER(배)"] = vals(o3[3], 10)
            rows["EV/EBITDA(배)"] = vals(o3[4], 10)
            rows["ROE(%)"] = vals(o3[5], 10)
            rows["부채비율(%)"] = vals(o3[6], 10)
    except (IndexError, KeyError):
        pass
    return {
        "analyst": o1.get("name1") or "",
        "est_date": _ymd_dot(o1.get("estdate")),
        "opinion": o1.get("rcmd_name") or "",
        "periods": [str(r.get("dt") or "") for r in o4],
        "rows": rows,
    }


# ── 종합 시황·공시 제목 (141) — 종목별 뉴스 ─────────────────────
async def fetch_stock_news(code: str = "", n: int = 20) -> list[dict]:
    """종합 시황/공시(제목) [141] — code 지정 시 해당 종목, 공백이면 시장 전체.

    반환: [{일시, 제목, 출처}] (최신순)
    """
    j = await _aget("/uapi/domestic-stock/v1/quotations/news-title", "FHKST01011800",
                    {"FID_NEWS_OFER_ENTP_CODE": "", "FID_COND_MRKT_CLS_CODE": "",
                     "FID_INPUT_ISCD": code or "", "FID_TITL_CNTT": "",
                     "FID_RANK_SORT_CLS_CODE": "", "FID_INPUT_SRNO": "",
                     "FID_INPUT_DATE_1": "", "FID_INPUT_HOUR_1": ""})
    rows = j.get("output") or []
    out = []
    for r in rows:
        if len(out) >= n:
            break
        # 종목 지정 조회인데 무관 뉴스가 섞이는 경우 — 연관종목(iscd1~10)에 코드 있는 것만
        if code and not any(str(r.get(f"iscd{i}") or "") == code for i in range(1, 11)):
            continue
        dt, tm = str(r.get("data_dt") or ""), str(r.get("data_tm") or "")
        when = (f"{dt[4:6]}.{dt[6:8]} {tm[:2]}:{tm[2:4]}"
                if len(dt) == 8 and len(tm) >= 4 else dt)
        title = (r.get("hts_pbnt_titl_cntt") or "").strip()
        if not title:
            continue
        out.append({"일시": when, "제목": title, "출처": r.get("dorg") or "-"})
    return out


# ── ETF NAV (실시간-051 의 REST 보조: ETF/ETN 현재가) ───────────
async def fetch_etf_nav(code: str) -> dict:
    """ETF 실시간 NAV(iNAV) — KIS etfetn inquire-price (FHPST02400000).

    반환: {nav, nav_vrss, nav_ctrt, dirc(▲/▼/-), dprt(괴리율), prpr(현재가)}
    """
    if not (code and code.isdigit()):
        return {}
    j = await _aget("/uapi/etfetn/v1/quotations/inquire-price", "FHPST02400000",
                    {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code})
    o = j.get("output") or {}
    nav = _num(o.get("nav"))
    if not nav or nav <= 0:
        return {}
    sign = str(o.get("nav_prdy_vrss_sign") or "3")
    return {
        "nav": nav,
        "nav_vrss": _num(o.get("nav_prdy_vrss")),
        "nav_ctrt": _num(o.get("nav_prdy_ctrt")),
        "dirc": "▲" if sign in ("1", "2") else ("▼" if sign in ("4", "5") else ""),
        "dprt": _num(o.get("dprt")),
        "prpr": _num(o.get("stck_prpr")),
    }
