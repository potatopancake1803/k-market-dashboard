# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "flask>=3.0",
#   "httpx>=0.27",
#   "polars>=1.0",
#   "pandas>=2.0",
#   "numpy>=1.26",
#   "pyarrow>=15.0",
#   "lxml>=5.0",
#   "plotly>=5.20",
#   "python-dotenv>=1.0",
# ]
# ///
"""한국 증시 종목 리포트 (ver2) — 웹 대시보드.

  uv run company_report_ver2.py
    → 로컬 서버가 뜨고 브라우저가 자동으로 열린다.
    → 상단 검색창에 종목명/코드를 입력(자동완성)하면 아래에 단일 페이지 리포트가 뜬다.

페이지 구성 (위 → 아래):
  1. 현재가 히어로
  2. 기본정보(KPI·정보) → 투자지표(동일 UI) → 종가 캔들차트 → 기간별 수익률
  3. 지배구조 — 주주 구성 도넛 + 최대주주 현황(6행 노출·스크롤)
  4. 투자자별 매매 동향
  5. 재무비율 · 배당 이력 (표만)
  6. 재무제표 — 손익·재무상태·현금흐름 추이(꺾은선, 가로 3개) + 표
"""
from __future__ import annotations

import asyncio
import os
import re
import tempfile
import threading
import time
import webbrowser
from datetime import date

import pandas as pd
from flask import Flask, Response, jsonify, request


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from market_intel.analyze import valuation as V
from market_intel.collectors import dart as dart_c
from market_intel.collectors import fsc
from market_intel.collectors import kis
from market_intel.collectors import naver
from market_intel.collectors.krx import KRXCollector
from market_intel.config import business_days, load_settings
from market_intel.httpx_client import Fetcher
from market_intel.progress import gather_with_progress
from market_intel.report import dashboard as D

# company_report.py 공용 헬퍼·상수 재사용
from company_report import MARKET_MAP, _fmt_metric, _krx_snapshot, _pivot_trend, _won

PORT = int(os.environ.get("COMPANY_PORT", "8766"))
app = Flask(__name__)

# ── DART 기업목록 메모리 캐시 (자동완성용) ─────────────────────────
_corp_cache: dict = {"corps": None, "ts": 0.0}
_corp_lock = threading.Lock()


async def _async_corps(settings):
    async with Fetcher() as f:
        return await dart_c.load_corp_list(f, settings.dart_key)


def get_corps(max_age: float = 86400.0) -> list[dict]:
    settings = load_settings()
    with _corp_lock:
        if _corp_cache["corps"] is not None and (time.time() - _corp_cache["ts"]) < max_age:
            return _corp_cache["corps"]
        corps = asyncio.run(_async_corps(settings))
        _corp_cache.update(corps=corps, ts=time.time())
        return corps


# ════════════════ 데이터 수집 ════════════════
async def _async_fetch(settings, cands: list[dict]) -> dict:
    async with Fetcher() as f:
        corp, info = await dart_c.pick_listed_corp(f, settings.dart_key, cands)
        corp_code, stock_code, corp_name = corp["corp_code"], corp["stock_code"], corp["corp_name"]
        corp_cls = info.get("corp_cls", "Y")
        jurir_no = info.get("jurir_no", "").replace("-", "") or None

        res = await gather_with_progress(f"{corp_name} 데이터 수집", {
            "stmts": dart_c.fetch_statements(f, settings.dart_key, corp_code),
            "dividend": dart_c.fetch_dividend(f, settings.dart_key, corp_code),
            "hist": fsc.fetch_stock_history(f, settings.fsc_key, stock_code),
            "div_hist": fsc.fetch_dividend_history(f, settings.fsc_key, crno=jurir_no, name=corp_name),
            "rt": naver.fetch_realtime_price(f, stock_code),
            "chart": naver.fetch_price_chart(f, stock_code, days=1900),
            "trend": naver.fetch_investor_trend(f, stock_code, days=30),
            "shareholders": dart_c.fetch_major_shareholders(f, settings.dart_key, corp_code),
            "gov_fsc": fsc.fetch_governance_shareholders(f, settings.fsc_key, jurir_no),
            "consensus": naver.fetch_consensus(f, stock_code),
            "finsum": naver.fetch_financial_summary(f, stock_code),
            "reports": naver.fetch_research_reports(f, stock_code, months=3, limit=12),
            # 한국투자증권 KIS Open API (한국투자증권_API_New) — 작업4·5
            "kis_opn": kis.fetch_invest_opinions(stock_code),       # 종목투자의견 [188]
            "kis_trend": kis.fetch_investor_trend(stock_code, 30),  # 투자자매매동향(일별)
            "kis_stab": kis.fetch_stability_ratios(stock_code),     # 안정성비율 [083]
            # 기업 정보 탭 (주식기본조회·재무/수익성/성장성/기타비율·추정실적·시황공시)
            "kis_info": kis.fetch_stock_info(stock_code),           # 주식기본조회 [067]
            "kis_fin": kis.fetch_finance_ratios(stock_code),        # 재무비율 [080]
            "kis_prof": kis.fetch_profit_ratios(stock_code),        # 수익성비율 [081]
            "kis_grow": kis.fetch_growth_ratios(stock_code),        # 성장성비율 [085]
            "kis_other": kis.fetch_other_ratios(stock_code),        # 기타주요비율 [082]
            "kis_est": kis.fetch_estimates(stock_code),             # 종목추정실적 [187]
            "kis_news": kis.fetch_stock_news(stock_code, 15),       # 시황·공시 제목 [141]
        })
        if res["hist"].empty:   # FSC 실패 → KRX 백업
            krx = KRXCollector(f, settings.krx_key)
            endpoint = "kospi_stock" if corp_cls == "Y" else "kosdaq_stock"
            prices_pl = await krx.fetch_market_frame(endpoint, business_days(date.today(), 12))
            res["hist"] = _krx_snapshot(prices_pl, stock_code)
        return {"corp": corp, "info": info, "corp_cls": corp_cls, **res}


# ════════════════ 헬퍼 (수익률·KPI·투자지표 패널) ════════════════
def _stock_period_returns(chart: pd.DataFrame) -> pd.DataFrame:
    """일별 종가에서 기간별 누적 수익률(%) 1행 표 (데이터 부족 구간 자동 생략)."""
    if chart.empty or "종가" not in chart.columns:
        return pd.DataFrame()
    c = chart.dropna(subset=["종가"]).copy()
    c["일자"] = pd.to_datetime(c["일자"], errors="coerce")
    c = c.dropna(subset=["일자"]).sort_values("일자")
    if len(c) < 2:
        return pd.DataFrame()
    last_dt, first_dt = c["일자"].iloc[-1], c["일자"].iloc[0]
    last_px = float(c["종가"].iloc[-1])

    def ret_from(start_ts):
        sub = c[c["일자"] >= start_ts]
        if sub.empty:
            return None
        base = float(sub["종가"].iloc[0])
        return round((last_px / base - 1) * 100, 2) if base else None

    row, cols = {"구분": "수익률(%)"}, []
    for label, days in [("1주", 7), ("1개월", 31), ("3개월", 92), ("6개월", 184),
                        ("1년", 365), ("3년", 1095), ("5년", 1825)]:
        start = last_dt - pd.Timedelta(days=days)
        if start < first_dt - pd.Timedelta(days=7):
            continue
        v = ret_from(start)
        if v is not None:
            row[label] = v
            cols.append(label)
    ytd = ret_from(pd.Timestamp(last_dt.year, 1, 1))
    if ytd is not None:
        row["연초이후"] = ytd
        cols.append("연초이후")
    return pd.DataFrame([row])[["구분"] + cols] if cols else pd.DataFrame()


def _stock_kpis(rt: dict, pa: dict, vol_latest, mktcap) -> list[dict]:
    kpis: list[dict] = []
    if rt and rt.get("현재가"):
        d, r, dirc = rt.get("전일대비"), rt.get("등락률(%)"), rt.get("방향", "")
        sub = f"{dirc} {abs(d):,.0f} ({abs(r):.2f}%)" if d is not None and r is not None else ""
        kpis.append({"label": "현재가", "value": f"{rt['현재가']:,.0f}", "unit": "원",
                     "sub": sub, "dir": dirc})
        rate = r
    else:
        price, rate = pa.get("전일종가"), pa.get("등락률(%)")
        kpis.append({"label": "종가(전일)", "value": f"{price:,.0f}" if price else "-",
                     "unit": "원", "sub": f"{rate:+.2f}%" if rate is not None else ""})
    if rate is not None:
        kpis.append({"label": "등락률", "value": f"{rate:+.2f}", "unit": "%", "sub": "(전일대비)",
                     "val_dir": "▲" if rate > 0 else ("▼" if rate < 0 else "")})
    if mktcap:
        kpis.append({"label": "시가총액", "value": _won(mktcap), "unit": "", "sub": ""})
    if vol_latest is not None:
        kpis.append({"label": "거래량", "value": f"{vol_latest:,.0f}", "unit": "주", "sub": "(최근일)"})
    return kpis


_IMPORTANT_METRICS = ["PER(배)", "PBR(배)", "EPS(원)", "배당수익률(%)"]


def _kpi_metric_val(label: str, v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-", ""
    if "시가총액" in label or "EV(" in label:
        return _won(v), ""
    if "(배)" in label:
        return f"{float(v):.2f}", "배"
    if "(원)" in label:
        return f"{float(v):,.0f}", "원"
    if "(%)" in label:
        return f"{float(v):.2f}", "%"
    if "상장주식수" in label:
        return f"{float(v):,.0f}", "주"
    try:
        return f"{float(v):,.2f}".rstrip("0").rstrip("."), ""
    except (ValueError, TypeError):
        return str(v), ""


def _metric_panel_args(val: pd.DataFrame) -> tuple[list[dict], list[tuple]]:
    """투자지표 DataFrame → (상단 KPI 박스용 중요지표, 하단 그리드용 나머지)."""
    rows = [(r["지표"], r["값"]) for _, r in val.iterrows()]
    kpis, info = [], []
    important = sorted([(k, v) for k, v in rows if k in _IMPORTANT_METRICS],
                       key=lambda kv: _IMPORTANT_METRICS.index(kv[0]))
    for k, v in important:
        val_s, unit = _kpi_metric_val(k, v)
        kpis.append({"label": re.sub(r"\((?:배|원|%)\)", "", k).strip(),
                     "value": val_s, "unit": unit, "sub": ""})
    for k, v in rows:
        if k not in _IMPORTANT_METRICS:
            info.append((k, _fmt_metric(k, v)))
    if not kpis:   # 중요지표가 하나도 없으면 앞쪽 4개를 박스로
        for k, v in rows[:4]:
            val_s, unit = _kpi_metric_val(k, v)
            kpis.append({"label": re.sub(r"\((?:배|원|%)\)", "", k).strip(),
                         "value": val_s, "unit": unit, "sub": ""})
        info = [(k, _fmt_metric(k, v)) for k, v in rows[4:]]
    return kpis, info


# ════════════════ 대시보드 빌드 ════════════════
def _build_dashboard(d: dict) -> D.Dashboard:
    corp, info = d["corp"], d["info"]
    stock_code, corp_name = corp["stock_code"], corp["corp_name"]
    corp_cls = d["corp_cls"]
    stmts, dividend = d["stmts"], d["dividend"]
    hist, div_hist, rt = d["hist"], d["div_hist"], d["rt"]
    chart = pd.DataFrame(d["chart"])
    # 매매동향: KIS 일별 투자자매매동향 우선 (15:40 이전 시간제한·실패 시 네이버 폴백)
    trend, shareholders = (d.get("kis_trend") or d["trend"]), d["shareholders"]

    income = stmts.get("income", pd.DataFrame())
    balance = stmts.get("balance", pd.DataFrame())
    cashflow = stmts.get("cashflow", pd.DataFrame())
    ratios = (dart_c.compute_ratios(income, balance, cashflow, stmts.get("prior_balance"))
              if stmts else pd.DataFrame())
    iratio_label, iratios = dart_c.compute_interim_ratios(stmts) if stmts else (None, None)
    if iratios and not ratios.empty:
        ratios.insert(0, iratio_label, pd.Series(iratios))

    pa = V.price_analytics(hist)
    price, shares, mktcap = pa.get("전일종가"), pa.get("상장주식수"), pa.get("시가총액")
    ttm_dps = V.ttm_dividend(div_hist)
    div_for_val = dict(dividend or {})
    if ttm_dps:
        div_for_val["주당현금배당금"] = ttm_dps
        div_for_val["현금배당수익률(%)"] = None
    val = (V.valuation_metrics(stmts, price=price, shares=shares, mktcap=mktcap,
                               dividend=div_for_val) if stmts and price else pd.DataFrame())
    kv = {r["지표"]: r["값"] for _, r in val.iterrows()} if not val.empty else {}

    market = MARKET_MAP.get(corp_cls, corp_cls)
    fs_label = "연결" if stmts.get("fs_div") == "CFS" else "개별"
    yr = stmts.get("year")

    price_date = (str(chart["일자"].iloc[-1]) if (not chart.empty and "일자" in chart.columns)
                  else (pa.get("기준일") or ""))
    vol_latest = None
    if not chart.empty and "거래량" in chart.columns:
        vv = pd.to_numeric(chart["거래량"].iloc[-1], errors="coerce")
        vol_latest = float(vv) if pd.notna(vv) else None

    dash = D.Dashboard(f"{corp_name} ({stock_code})",
                       f"{market} · 기준일 {price_date} · 재무 {yr}년 {fs_label}", kind="stock")
    ov = dash.add_tab("📊 종목 개요")

    # 1) 현재가 히어로
    if rt and rt.get("현재가"):
        diff, rate = rt.get("전일대비"), rt.get("등락률(%)")
        chg = f"{diff:+,.0f}원" if diff is not None else "-"
        if rate is not None:
            chg += f" ({rate:+.2f}%)"
        ov.add_html_raw_card(D.price_hero_html(
            corp_name, f"{rt['현재가']:,.0f}원", chg, rt.get("방향", "-"),
            f"실시간(지연) · {rt.get('조회시각','')} 조회 · 네이버 금융"))

    # 2) 기본정보 헤더 → 투자지표 → 캔들차트 → 기간별 수익률
    info_items = [
        ("시장", market), ("업종코드", info.get("induty_code", "-")),
        ("대표자", info.get("ceo_nm", "-")), ("설립일", info.get("est_dt", "-")),
        ("결산월", f"{info.get('acc_mt','-')}월"),
        ("상장주식수", f"{shares:,.0f}주" if shares else "-"),
        ("시가총액", _won(mktcap) if mktcap else "-"),
        ("52주 최고/최저",
         f"{pa.get('52주최고'):,.0f} / {pa.get('52주최저'):,.0f}원" if pa.get("52주최고") else "-"),
        ("52주 내 위치", f"{pa.get('52주위치(%)')}%" if pa.get("52주위치(%)") is not None else "-"),
        ("최근 1년 수익률", f"{pa.get('1년수익률(%)')}%" if pa.get("1년수익률(%)") is not None else "-"),
        ("연율 변동성", f"{pa.get('연율변동성(%)')}%" if pa.get("연율변동성(%)") is not None else "-"),
    ]
    ov.add_html_raw_card(D.etf_header_html(
        stock_code, corp_name, f"{price_date} 종가 기준", [market],
        _stock_kpis(rt, pa, vol_latest, mktcap), info_items))

    # 투자지표 (기본정보와 동일 UI — 중요지표 박스 + 나머지 그리드)
    if not val.empty:
        m_kpis, m_info = _metric_panel_args(val)
        ov.add_html_raw_card(D.metric_header_html("투자지표 (밸류에이션) — 전일 종가 기준", m_kpis, m_info))
        if price:
            ov.add_callout(f"전 거래일({pa.get('기준일')}) 종가 {price:,.0f}원 · {V.valuation_basis(stmts)}", "info")

    if not chart.empty and len(chart) > 1 and "시가" in chart.columns:
        ov.add_callout("종가 캔들차트 · 이동평균(MA5·20·60·120) · 아래 토글로 기간 선택 "
                       "(상승 빨강·하락 파랑)", "info")
        ov.add_candle_chart("종가 차트 (캔들 · 이동평균)", chart, "일자", "시가", "고가", "저가", "종가",
                            volume_col="거래량")

    pr = _stock_period_returns(chart)
    if not pr.empty:
        ov.add_table("기간별 수익률 (%) — 누적", pr, search=False)
        ov.add_callout("종가(배당 미반영) 기준 누적 수익률 · 네이버 일별 종가로 산출.", "info")

    # 4) 투자자별 매매 동향
    if trend:
        _trend_src = "한국투자증권 KIS" if d.get("kis_trend") else "네이버 금융"
        ov.add_callout("최근 30영업일 외국인·기관·개인 일별 순매수(주) · 매수(+) 빨강 / 매도(-) 파랑 · "
                       f"출처 {_trend_src}", "info")
        ov.add_investor_trend("투자자별 매매 동향 (최근 30영업일)", trend, visible=8)

    # 5) 지배구조 — 주주 구성 도넛 + 최대주주 현황(6행·스크롤) — 투자자 매매동향 아래 배치
    #    금융위 지배구조정보(FSC) 우선, 없으면 DART 최대주주현황으로 폴백 (조회 가능 종목 확대)
    gov_fsc = d.get("gov_fsc") or {}
    if gov_fsc.get("holders"):
        shareholders = gov_fsc
        _gov_src = "금융위 지배구조정보"
    else:
        _gov_src = "DART"
    holders = shareholders.get("holders", [])
    if holders:
        ov.add_callout(f"최대주주 및 특수관계인 지분 ({shareholders.get('year')}년 기준 · "
                       f"합계 {shareholders.get('최대주주측합계(%)')}%) · 출처 {_gov_src}", "info")
        top, rest = holders[:6], holders[6:]
        comp = [{"구분": h["성명"], "비중(%)": h["지분율(%)"]} for h in top]
        rest_sum = round(sum(h["지분율(%)"] for h in rest), 2)
        if rest_sum > 0:
            comp.append({"구분": "기타 특수관계인", "비중(%)": rest_sum})
        total_major = shareholders.get("최대주주측합계(%)") or sum(h["지분율(%)"] for h in holders)
        others = round(max(0.0, 100.0 - total_major), 2)
        if others > 0:
            comp.append({"구분": "기타 주주(유통)", "비중(%)": others})
        # 최대주주를 도넛 중앙에, '기타 주주(유통)'·'기타 특수관계인'은 회색으로
        _top = holders[0]
        ov.add_donut_breakdown(
            "지배구조 — 주주 구성 (보통주 기준)", pd.DataFrame(comp), "구분", "비중(%)",
            gray_labels={"기타 주주(유통)", "기타 특수관계인"},
            center=(_top["성명"], _top["지분율(%)"]))
        detail = pd.DataFrame([{"성명": h["성명"], "관계": h["관계"], "지분율(%)": h["지분율(%)"]}
                               for h in holders])
        ov.add_table("최대주주 및 특수관계인 현황", detail, search=False, scroll_rows=6, bold_first=True)

    # 6) 재무비율 · 배당 이력 (표만, 그래프 없음)
    if not ratios.empty:
        if iratios:
            ov.add_callout(f"재무비율에 최신 분기({iratio_label}) 포함 — 마진·부채/유동비율은 누적/시점값, "
                           f"ROE·ROA·FCF는 연율화", "info")
        rtab = ratios.reset_index()
        rtab = rtab.rename(columns={rtab.columns[0]: "재무비율 항목"})
        ov.add_table("재무비율 (분기 + 연도별)" if iratios else "재무비율 (연도별)",
                     rtab, search=False, bold_first=True)
    if not div_hist.empty:
        dh = div_hist.copy()
        dh["배당기준일"] = dh["배당기준일"].dt.strftime("%Y-%m-%d")
        ov.add_table("배당 이력 (예탁결제원)", dh, search=False)

    # 6-2) 애널리스트 투자의견 (종목 리포트 탭 맨 아래) — 시각화
    #   1순위: KIS 종목투자의견[국내주식-188] (증권사별 의견·목표가 → 자체 컨센서스 집계)
    #   2순위: 네이버 통합 API consensusInfo (KIS 무응답 종목 폴백)
    kis_opn = d.get("kis_opn") or {}
    cons = d.get("consensus") or {}
    use_kis = bool(kis_opn.get("recomm_mean") or kis_opn.get("target_mean"))
    if use_kis:
        rm, tgt = kis_opn.get("recomm_mean"), kis_opn.get("target_mean")
        n_buy, n_hold, n_sell = kis_opn.get("n_buy", 0), kis_opn.get("n_hold", 0), kis_opn.get("n_sell", 0)
        cons_date, cons_src = kis_opn.get("create_date", ""), "한국투자증권 KIS"
    else:
        rm, tgt = cons.get("recomm_mean"), cons.get("target_mean")
        n_buy = n_hold = n_sell = None
        cons_date, cons_src = cons.get("create_date", ""), "네이버 금융"
    cur_px = float(rt["현재가"]) if (rt and rt.get("현재가")) else (float(price) if price else None)
    reports = d.get("reports") or []
    if n_buy is None:
        # 폴백: 최근 3개월 네이버 리포트 기준 분포 집계
        n_buy = sum(1 for r in reports if any(k in (r.get("투자의견") or "") for k in ("매수", "적극", "Buy")))
        n_hold = sum(1 for r in reports if any(k in (r.get("투자의견") or "") for k in ("중립", "보유", "Hold")))
        n_sell = sum(1 for r in reports if any(k in (r.get("투자의견") or "") for k in ("매도", "Sell")))
    if rm or tgt or reports:
        parts = []
        if rm:
            parts.append(f"평균 투자의견 {D.opinion_label(rm)} ({rm:.2f}/5)")
        if tgt:
            parts.append(f"평균 목표주가 {tgt:,.0f}원")
        if tgt and cur_px:
            parts.append(f"상승여력 {(tgt / cur_px - 1) * 100:+.1f}%")
        if use_kis:
            parts.append(f"최근 6개월 증권사 {kis_opn.get('n_brokers', 0)}곳 "
                         f"(매수 {n_buy}·중립 {n_hold}·매도 {n_sell})")
        elif reports:
            parts.append(f"최근 3개월 리포트 {len(reports)}건 (매수 {n_buy}·중립 {n_hold}·매도 {n_sell})")
        if parts:
            ov.add_callout("애널리스트 컨센서스 — " + " · ".join(parts)
                           + f"  (출처 {cons_src})", "info")
        ov.add_consensus_panel("애널리스트 투자의견", rm, tgt, cur_px, cons_date,
                               dist={"매수": n_buy, "중립": n_hold, "매도": n_sell})
        # 증권사별 투자의견 상세 (KIS 188 — 최근 1년, 최신순)
        if kis_opn.get("opinions"):
            df_opn = pd.DataFrame(kis_opn["opinions"][:40])
            df_opn["목표가"] = df_opn["목표가"].map(lambda v: f"{v:,.0f}" if v else "-")
            df_opn["괴리율(%)"] = df_opn["괴리율(%)"].map(lambda v: f"{v:+.2f}" if v is not None else "-")
            ov.add_table(f"증권사별 투자의견 (최근 1년 {len(kis_opn['opinions'])}건 · 한국투자증권 KIS)",
                         df_opn, search=False, scroll_rows=8)
        if reports:
            ov.add_research_table(f"최근 애널리스트 리포트 (최근 3개월 · {len(reports)}건)",
                                  reports, code=stock_code)
        elif cons.get("researches"):
            ov.add_table("최근 애널리스트 리포트", pd.DataFrame(cons["researches"]), search=False)

    # 7) 재무제표 — 별도 탭으로 분리 ('종목 개요' 탭 옆)
    fin = dash.add_tab("💵 재무제표")
    interim_label = (stmts.get("interim") or {}).get("label")
    # 7-1) 실적 · 안정성 · 재무 인터랙티브 차트 (연간/분기 + 지표 토글) — 네이버 기업실적분석
    finsum = d.get("finsum") or {}
    # 안정성: KIS 안정성비율[083] 우선 — 분기 유동비율 제공(네이버 미제공 한계 해소).
    kis_stab = d.get("kis_stab") or {}
    if kis_stab.get("annual") and kis_stab.get("quarter"):
        _SK = ("부채비율", "유동비율", "당좌비율")
        stab_data = {k: {"periods": v["periods"][-8:],
                         "series": {m: v["series"][m][-8:] for m in _SK}}
                     for k, v in kis_stab.items() if k in ("annual", "quarter")}
        stab_chart = {"title": "안정성", "mode": "toggle", "type": "line",
                      "keys": list(_SK), "data": stab_data, "period": "annual"}
        stab_src = "안정성 출처 한국투자증권 KIS(유동·당좌비율 분기 포함)"
    else:
        stab_chart = {"title": "안정성", "mode": "toggle", "type": "line",
                      "keys": ["부채비율", "당좌비율"], "data": finsum, "period": "annual"}
        stab_src = "안정성 출처 네이버 금융"
    if finsum.get("annual", {}).get("periods"):
        fin.add_callout("실적·재무는 매출/영업이익/순이익(억원), 안정성은 부채비율·유동비율·당좌비율(%) · "
                        f"각 차트 우측 상단에서 연간/분기 전환 · 실적 출처 네이버 금융 · {stab_src}", "info")
        fin.add_fin_charts([
            {"title": "실적", "mode": "toggle", "type": "bar",
             "keys": ["매출", "영업이익"], "data": finsum, "period": "annual"},
            stab_chart,
            {"title": "재무", "mode": "group", "type": "bar",
             "keys": ["매출", "영업이익", "순이익"], "data": finsum, "period": "annual"},
        ])
    if yr:
        extra = f" · 최신 정기공시 {interim_label} 포함" if interim_label else ""
        fin.add_callout(f"재무제표(DART 사업보고서) — {yr}년 {fs_label}{extra}", "info")
    inc_df, unit = dart_c.display_statement(stmts, "income")
    bal_df, _ = dart_c.display_statement(stmts, "balance")
    cf_df, _ = dart_c.display_statement(stmts, "cashflow")
    note = (unit + (f" · {interim_label} 포함" if interim_label else "")) if unit else ""
    fin.add_grouped_table("손익계산서 (매출·영업·순이익 구분)", inc_df, note)
    fin.add_grouped_table("재무상태표 (자산·부채·자본 구분)", bal_df, unit)
    fin.add_grouped_table("현금흐름표 (영업·투자·재무 구분)", cf_df, note)

    # 8) 🏢 기업 정보 탭 — 한국투자증권 KIS (주식기본조회[067]·재무비율[080]·
    #    수익성[081]·성장성[085]·기타비율[082]·추정실적[187]·시황공시[141])
    _add_company_info_tab(dash, d)
    return dash


def _slice8(ratio: dict) -> dict:
    """KIS 비율 시계열을 fin_charts 데이터 형식으로 — 최근 8개 기간만."""
    out = {}
    for key in ("annual", "quarter"):
        v = ratio.get(key)
        if not v or not v.get("periods"):
            continue
        out[key] = {"periods": v["periods"][-8:],
                    "series": {m: s[-8:] for m, s in v["series"].items()}}
    return out


def _fmt_est(name: str, v) -> str:
    """추정실적 셀 포맷 — 금액은 천단위, 비율·배수는 소수 1자리."""
    if v is None:
        return "-"
    if "(억)" in name or "(원)" in name:
        return f"{v:,.0f}"
    return f"{v:,.1f}"


def _add_company_info_tab(dash: D.Dashboard, d: dict) -> None:
    info = d.get("kis_info") or {}
    fin_r = d.get("kis_fin") or {}
    prof = d.get("kis_prof") or {}
    grow = d.get("kis_grow") or {}
    other = d.get("kis_other") or {}
    est = d.get("kis_est") or {}
    news = d.get("kis_news") or []
    if not (info or fin_r.get("annual")):
        return          # KIS 무응답 종목 — 탭 자체를 생략
    ci = dash.add_tab("🏢 기업 정보")
    ci.add_callout("기업 개요 · 투자지표(연간/분기) · 증권사 추정실적 · 종목 뉴스 — "
                   "출처 한국투자증권 KIS Open API", "info")

    # 거래정지/관리종목 경고
    warns = [w for w, on in (("거래정지", info.get("거래정지")),
                             ("관리종목", info.get("관리종목"))) if on]
    if warns:
        ci.add_callout("⚠️ " + " · ".join(warns) + " 지정 종목 — 투자에 유의하세요.", "warn")

    # ① 기업 개요 그리드
    if info:
        shares = info.get("상장주수")
        cpta = info.get("자본금(억)")
        items = [
            ("시장", info.get("시장")),
            ("업종(KRX)", info.get("업종")),
            ("표준산업분류", info.get("표준산업")),
            ("상장일", info.get("상장일")),
            ("상장주식수", f"{shares:,.0f} 주" if shares else None),
            ("액면가", f"{info['액면가']:,.0f} 원" if info.get("액면가") else None),
            ("자본금", f"{cpta:,.0f} 억원" if cpta else None),
            ("결산월", f"{info['결산월']}월" if info.get("결산월") else None),
            ("KOSPI200 편입", "예" if info.get("K200") else "아니오"),
            ("NXT(대체거래소) 거래", "가능" if info.get("NXT가능") else "불가"),
        ]
        ci.add_info_grid("기업 개요", [(k, v) for k, v in items if v is not None])

    # ② 투자지표 차트 (연간/분기 토글) — 주당지표·수익성·성장성
    charts = []
    if fin_r.get("annual"):
        charts.append({"title": "주당지표", "mode": "toggle", "type": "line",
                       "keys": ["EPS", "BPS", "SPS"], "data": _slice8(fin_r),
                       "period": "annual"})
    if prof.get("annual"):
        charts.append({"title": "수익성", "mode": "toggle", "type": "line",
                       "keys": ["자기자본순이익률(ROE)", "매출순이익률", "매출총이익률"],
                       "data": _slice8(prof), "period": "annual"})
    if grow.get("annual"):
        charts.append({"title": "성장성", "mode": "toggle", "type": "line",
                       "keys": ["매출증가율", "영업이익증가율", "총자산증가율"],
                       "data": _slice8(grow), "period": "annual"})
    if charts:
        ci.add_callout("주당지표(원) · 수익성/성장성(%) — 각 차트 우측 상단에서 연간/분기 전환", "info")
        ci.add_fin_charts(charts)

    # ③ 증권사 추정실적 (187) — 행=결산기, E=추정
    if est.get("rows") and est.get("periods"):
        cols = ["매출액(억)", "매출 YoY(%)", "영업이익(억)", "영업이익 YoY(%)",
                "순이익(억)", "EPS(원)", "PER(배)", "ROE(%)"]
        cols = [c for c in cols if c in est["rows"]]
        recs = []
        for i, p in enumerate(est["periods"]):
            rec = {"결산기": p + (" 🅴" if p.endswith("E") else "")}
            for c in cols:
                vals = est["rows"][c]
                rec[c] = _fmt_est(c, vals[i] if i < len(vals) else None)
            recs.append(rec)
        meta = " · ".join(x for x in (
            f"애널리스트 {est['analyst']}" if est.get("analyst") else "",
            f"추정일 {est['est_date']}" if est.get("est_date") else "",
            f"의견 {est['opinion']}" if est.get("opinion") else "") if x)
        ci.add_table("증권사 추정실적 — 🅴 = 추정치" + (f" ({meta})" if meta else ""),
                     pd.DataFrame(recs), search=False, bold_first=True)

    # ④ 밸류에이션·주주환원 (082 연간 최근 5년)
    oa = (other.get("annual") or {})
    if oa.get("periods"):
        per = oa["periods"][-5:]
        ser = oa["series"]
        recs = [{"결산기": p} for p in per]
        for name in ("EBITDA(억)", "EV/EBITDA", "배당성향(%)", "EVA(억)"):
            vals = (ser.get(name) or [])[-5:]
            for i, rec in enumerate(recs):
                v = vals[i] if i < len(vals) else None
                rec[name] = ("-" if v is None
                             else (f"{v:,.0f}" if "(억)" in name else f"{v:,.2f}"))
        ci.add_table("밸류에이션 · 주주환원 (연간)", pd.DataFrame(recs),
                     search=False, bold_first=True)

    # ⑤ 최근 종목 뉴스·공시 (141)
    if news:
        ci.add_table(f"최근 종목 뉴스·공시 ({len(news)}건 · 한국투자증권 KIS)",
                     pd.DataFrame(news), search=False, scroll_rows=8)


def _dash_to_html(dash: D.Dashboard) -> str:
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        dash.render(path)
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def build_company_html(query: str) -> tuple[str | None, str | None]:
    settings = load_settings()
    if not settings.dart_key:
        return None, "DART_KEY 가 없습니다. API.env 를 확인하세요."
    corps = get_corps()
    cands = dart_c.search_corp(query, corps)
    if not cands:
        return None, f"'{query}' 에 해당하는 상장 기업을 찾지 못했습니다. (종목명 또는 6자리 코드)"
    raw = asyncio.run(_async_fetch(settings, cands))
    return _dash_to_html(_build_dashboard(raw)), None


# ════════════════ 라우트 ════════════════
@app.get("/")
def index() -> Response:
    return Response(_LANDING_HTML, mimetype="text/html")


@app.get("/suggest")
def suggest():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    try:
        corps = get_corps()
    except Exception:  # noqa: BLE001
        return jsonify([])
    listed = [c for c in corps if c.get("stock_code")]
    if q.isdigit():
        hits = [c for c in listed if c["stock_code"].startswith(q)]
    else:
        exact = [c for c in listed if c["corp_name"] == q]
        partial = [c for c in listed if q in c["corp_name"] and c not in exact]
        hits = exact + partial
    out = [{"code": c["stock_code"], "name": c["corp_name"], "extra": ""} for c in hits[:12]]
    return jsonify(out)


@app.get("/dashboard")
def dashboard() -> Response:
    q = (request.args.get("q") or "").strip()
    if not q:
        return Response(_error_html("검색어를 입력하세요."), mimetype="text/html")
    try:
        html, err = build_company_html(q)
    except Exception as e:  # noqa: BLE001
        return Response(_error_html(f"오류가 발생했습니다: {e}"), mimetype="text/html")
    if err:
        return Response(_error_html(err), mimetype="text/html")
    return Response(html, mimetype="text/html")


def _error_html(msg: str) -> str:
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<style>body{{margin:0;font-family:-apple-system,'Apple SD Gothic Neo',sans-serif;
background:#f4f6fb;color:#1a1a2e;display:flex;align-items:center;justify-content:center;height:100vh;}}
.box{{background:#fff;border:1px solid #e3e8f0;border-radius:14px;padding:40px 48px;text-align:center;
box-shadow:0 4px 20px rgba(20,40,80,.06);max-width:520px;}}
.box .ic{{font-size:42px;margin-bottom:10px;}}
.box h2{{margin:0 0 8px;color:#1F3864;font-size:19px;}}
.box p{{margin:0;color:#6b7689;font-size:14.5px;line-height:1.6;}}</style></head>
<body><div class="box"><div class="ic">🔍</div><h2>결과를 표시할 수 없습니다</h2><p>{msg}</p></div></body></html>"""


# ════════════════ 랜딩 페이지 ════════════════
_LANDING_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>한국 증시 종목 리포트</title>
<style>
:root{--navy:#1F3864;--blue:#2E75B6;--bg:#f4f6fb;--line:#e3e8f0;}
*{box-sizing:border-box;}
html,body{margin:0;height:100%;}
body{display:flex;flex-direction:column;background:var(--bg);
 font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','Apple SD Gothic Neo',sans-serif;color:#1a1a2e;}
.topbar{background:linear-gradient(135deg,var(--navy),var(--blue));color:#fff;
 padding:16px 24px;display:flex;align-items:center;gap:18px;box-shadow:0 2px 8px rgba(20,40,80,.12);z-index:20;}
.topbar .brand{font-size:18px;font-weight:800;white-space:nowrap;}
.topbar .brand small{font-weight:500;opacity:.8;font-size:12px;margin-left:6px;}
.searchwrap{position:relative;flex:1;max-width:620px;}
#q{width:100%;padding:12px 16px;font-size:15px;border:0;border-radius:10px;
 box-shadow:0 1px 3px rgba(0,0,0,.15);outline:none;}
#q::placeholder{color:#9aa3b2;}
.sg{position:absolute;top:48px;left:0;right:0;background:#fff;border:1px solid var(--line);
 border-radius:10px;box-shadow:0 8px 24px rgba(20,40,80,.14);overflow:hidden;display:none;z-index:30;max-height:380px;overflow-y:auto;}
.sg.show{display:block;}
.sg-item{padding:11px 16px;cursor:pointer;border-bottom:1px solid #f0f3f8;display:flex;align-items:baseline;gap:10px;}
.sg-item:last-child{border-bottom:0;}
.sg-item:hover,.sg-item.active{background:#eef5ff;}
.sg-code{font-weight:700;color:var(--blue);font-size:13px;font-variant-numeric:tabular-nums;min-width:64px;}
.sg-name{font-weight:700;color:#15233f;font-size:14.5px;}
.btn{background:#fff;color:var(--navy);border:0;border-radius:10px;padding:12px 22px;
 font-size:15px;font-weight:700;cursor:pointer;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.btn:hover{background:#f0f4fb;}
.stage{flex:1;position:relative;}
#frame{width:100%;height:100%;border:0;background:#fff;display:none;}
.empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 color:#8a93a6;text-align:center;padding:24px;}
.empty .big{font-size:54px;margin-bottom:14px;}
.empty h2{margin:0 0 8px;color:#1F3864;font-size:22px;font-weight:800;}
.empty p{margin:2px 0;font-size:14.5px;}
.empty .ex{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;}
.empty .ex span{background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 14px;
 font-size:13px;color:#33415c;cursor:pointer;font-weight:600;}
.empty .ex span:hover{border-color:var(--blue);color:var(--blue);}
.overlay{position:absolute;inset:0;background:rgba(244,246,251,.86);display:none;
 align-items:center;justify-content:center;flex-direction:column;gap:16px;z-index:10;}
.overlay.show{display:flex;}
.spinner{width:42px;height:42px;border:4px solid #d4ddec;border-top-color:var(--blue);
 border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.overlay p{color:#5b6b86;font-weight:600;font-size:14px;}
</style></head>
<body>
<div class="topbar">
  <div class="brand">🏢 한국 증시 종목 리포트<small>DART · 금융위 · 네이버 금융</small></div>
  <form class="searchwrap" id="form" autocomplete="off" onsubmit="return doSearch();">
    <input id="q" type="text" placeholder="종목명 또는 6자리 코드 입력 (예: 삼성전자, 005930, 현대차)">
    <div class="sg" id="sg"></div>
  </form>
  <button class="btn" type="button" onclick="doSearch()">검색</button>
</div>
<div class="stage">
  <iframe id="frame" title="종목 리포트"></iframe>
  <div class="empty" id="empty">
    <div class="big">🔍</div>
    <h2>종목을 검색해 보세요</h2>
    <p>종목명 또는 6자리 코드를 입력하면 상세 리포트가 아래에 표시됩니다.</p>
    <p>현재가 · 투자지표 · 캔들차트 · 지배구조 · 투자자 매매동향 · 재무제표</p>
    <div class="ex">
      <span onclick="pick('005930')">삼성전자</span>
      <span onclick="pick('000660')">SK하이닉스</span>
      <span onclick="pick('005380')">현대차</span>
      <span onclick="pick('035420')">NAVER</span>
    </div>
  </div>
  <div class="overlay" id="overlay"><div class="spinner"></div><p>재무·시세 데이터를 수집하고 리포트를 생성하는 중…</p></div>
</div>
<script>
var q=document.getElementById('q'),sg=document.getElementById('sg'),
    frame=document.getElementById('frame'),overlay=document.getElementById('overlay'),
    empty=document.getElementById('empty');
var tmr=null,items=[],active=-1;
q.addEventListener('input',function(){
  clearTimeout(tmr); active=-1;
  var v=q.value.trim();
  if(!v){hideSg();return;}
  tmr=setTimeout(function(){fetchSg(v);},180);
});
q.addEventListener('keydown',function(e){
  if(!sg.classList.contains('show'))return;
  var rows=sg.querySelectorAll('.sg-item');
  if(e.key==='ArrowDown'){e.preventDefault();active=Math.min(active+1,rows.length-1);paint(rows);}
  else if(e.key==='ArrowUp'){e.preventDefault();active=Math.max(active-1,0);paint(rows);}
  else if(e.key==='Enter'){if(active>=0&&items[active]){e.preventDefault();pick(items[active].code);}}
  else if(e.key==='Escape'){hideSg();}
});
document.addEventListener('click',function(e){if(!sg.contains(e.target)&&e.target!==q)hideSg();});
function paint(rows){rows.forEach(function(r,i){r.classList.toggle('active',i===active);});}
function hideSg(){sg.classList.remove('show');sg.innerHTML='';}
function fetchSg(v){
  fetch('/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(d){
    items=d||[];
    if(!items.length){hideSg();return;}
    sg.innerHTML=items.map(function(it){
      return '<div class="sg-item" onclick="pick(\\''+it.code+'\\')">'+
        '<span class="sg-code">'+it.code+'</span>'+
        '<span class="sg-name">'+it.name+'</span></div>';
    }).join('');
    sg.classList.add('show');
  }).catch(function(){hideSg();});
}
function pick(code){q.value=code;hideSg();doSearch();}
function doSearch(){
  var v=q.value.trim();
  if(!v)return false;
  hideSg(); empty.style.display='none'; frame.style.display='block'; overlay.classList.add('show');
  frame.src='/dashboard?q='+encodeURIComponent(v);
  return false;
}
frame.addEventListener('load',function(){if(frame.src)overlay.classList.remove('show');});
</script>
</body></html>
"""


def _open_browser():
    time.sleep(1.0)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    print("=" * 60)
    print("  한국 증시 종목 리포트 (웹 버전)")
    print(f"  · 브라우저에서 열기:  http://127.0.0.1:{PORT}/")
    print("  · 종료: Ctrl + C")
    print("=" * 60)
    if not os.environ.get("MI_NO_OPEN"):
        threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
