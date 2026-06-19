# /// script
# requires-python = ">=3.11"
# dependencies = [
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
"""한국 ETF 리포트 — 개별 ETF 한 종목을 깊이 본다.

프로세스를 실행하면 안에서 ETF 종목명/코드(6자리, 영문 포함 가능 예 '0117V0')를
입력받아(반복 가능) 단일 'ETF 개요' 탭을 생성한다:
  헤더(현재가·기준가iNAV·수익률·거래량 KPI + 상품정보) → 수익률 그래프(1년)
  → 기간별 수익률 표 → 포트폴리오(구성종목) → 섹터/국가/자산 비중

데이터 소스
  - KRX Market Data API : ETF 일별매매정보(종가·NAV·순자산총액·기초지수·거래대금)
  - 네이버 금융          : 실시간(지연) 현재가 · ETF 분석(구성종목·보수·기간수익률) · 1년 차트

산출물은 단일 인터랙티브 HTML 대시보드(output/)로 저장한다.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime

import pandas as pd


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from market_intel.analyze import etf as E
from market_intel.collectors import naver
from market_intel.collectors.krx import KRXCollector
from market_intel.config import OUTPUT_DIR, business_days, load_settings, now_stamp
from market_intel.httpx_client import Fetcher
from market_intel.progress import Spinner
from market_intel.report import dashboard as D

ETF_LOOKBACK = 20  # KRX 가 최근 며칠 지연되므로 넉넉히(영업일)


def _jo(eok) -> str:
    """억 단위 값 → 조/억 읽기 쉽게."""
    if eok is None or (isinstance(eok, float) and pd.isna(eok)):
        return "-"
    v = float(eok)
    return f"{v/1e4:,.2f}조원" if abs(v) >= 1e4 else f"{v:,.0f}억원"


# ── 개별 ETF 상세 ──────────────────────────────────────────────
def _ymd(s) -> str:
    s = str(s or "")
    return f"{s[:4]}.{s[4:6]}.{s[6:8]}" if len(s) == 8 and s.isdigit() else (s or "-")


def _period_table(an: dict, chart: pd.DataFrame) -> pd.DataFrame:
    """이미지처럼 전치된 기간별 수익률 표 (행: NAV(%)/종가(%), 열: 기간)."""
    ret = {r["기간"]: r for r in (an.get("returns") or [])}
    cols = ["1개월", "3개월", "6개월", "1년", "3년", "5년", "연초이후", "상장이후"]
    # 상장이후(종가) — 1년 차트가 '상장일부터' 시작하는 경우(=상장 1년 이내)에만 계산.
    #   오래된 ETF는 차트가 상장일까지 닿지 않으므로 공란 처리.
    since = None
    lst = str(an.get("상장일") or "")
    if not chart.empty and len(chart) > 1 and len(lst) == 8 and lst.isdigit():
        try:
            first = datetime.strptime(chart["일자"].iloc[0], "%Y-%m-%d").date()
            listed = datetime.strptime(lst, "%Y%m%d").date()
            covers_listing = (first - listed).days <= 7
        except (ValueError, TypeError):
            covers_listing = False
        if covers_listing:
            c = pd.to_numeric(chart["종가"], errors="coerce").dropna()
            if len(c) > 1 and c.iloc[0]:
                since = round((c.iloc[-1] / c.iloc[0] - 1) * 100, 2)
    nav_row, close_row = {"구분": "NAV(%)"}, {"구분": "종가(%)"}
    for col in cols:
        if col == "상장이후":
            close_row[col] = since
            nav_row[col] = ret.get(col, {}).get("NAV(%)")
        else:
            nav_row[col] = ret.get(col, {}).get("NAV(%)")
            close_row[col] = ret.get(col, {}).get("시장가(%)")
    return pd.DataFrame([nav_row, close_row])


def _nav_change(ds: pd.DataFrame):
    """KRX 일별 NAV 시계열에서 전일대비(차이·비율·방향) 계산."""
    if ds.empty or "NAV" not in ds.columns:
        return None, None, ""
    navs = pd.to_numeric(ds["NAV"], errors="coerce").dropna()
    if len(navs) < 2:
        return None, None, ""
    diff = float(navs.iloc[-1] - navs.iloc[-2])
    rate = (navs.iloc[-1] / navs.iloc[-2] - 1) * 100 if navs.iloc[-2] else None
    return diff, rate, ("▲" if diff > 0 else ("▼" if diff < 0 else ""))


def _kpis(row: pd.Series, rt: dict, ret: dict, ds: pd.DataFrame) -> list[dict]:
    kpis = []
    if rt and rt.get("현재가"):
        d, r, dirc = rt.get("전일대비"), rt.get("등락률(%)"), rt.get("방향", "")
        sub = f"{dirc} {abs(d):,.0f} ({abs(r):.2f}%)" if d is not None and r is not None else ""
        kpis.append({"label": "현재가", "value": f"{rt['현재가']:,.0f}", "unit": "원", "sub": sub, "dir": dirc})
    else:
        kpis.append({"label": "현재가", "value": f"{row['종가']:,.0f}", "unit": "원",
                     "sub": f"{row['등락률(%)']}%"})
    # 기준가(iNAV) — KIS 실시간 NAV(국내ETF NAV추이·ETF/ETN 현재가) 우선,
    # 없으면 KRX 일별 NAV(전 영업일 기준가) 폴백.
    knav = (rt or {}).get("kis_nav") or {}
    if knav.get("nav"):
        nd, nr, ndir = knav.get("nav_vrss"), knav.get("nav_ctrt"), knav.get("dirc", "")
        sub = f"{ndir} {abs(nd):,.2f} ({abs(nr):.2f}%)" if nd is not None and nr is not None else ""
        kpis.append({"label": "기준가(iNAV)", "value": f"{knav['nav']:,.2f}", "unit": "원",
                     "sub": sub, "dir": ndir})
    elif pd.notna(nav := row.get("NAV")):
        nd, nr, ndir = _nav_change(ds)
        sub = f"{ndir} {abs(nd):,.2f} ({abs(nr):.2f}%)" if nd is not None and nr is not None else ""
        kpis.append({"label": "기준가(iNAV)", "value": f"{nav:,.2f}", "unit": "원", "sub": sub, "dir": ndir})
    r1m = ret.get("1개월", {}).get("시장가(%)")
    if r1m is not None:
        kpis.append({"label": "수익률", "value": f"{r1m:+.2f}", "unit": "%", "sub": "(1개월)",
                     "val_dir": "▲" if r1m > 0 else ("▼" if r1m < 0 else "")})
    if pd.notna(row.get("거래량")):
        kpis.append({"label": "거래량", "value": f"{row['거래량']:,.0f}", "unit": "주", "sub": ""})
    return kpis


def add_detail_tab(dash: D.Dashboard, row: pd.Series, rt: dict, an: dict,
                   quotes: dict, chart: pd.DataFrame, ds: pd.DataFrame, last_date: str,
                   trend: list[dict] | None = None, price_date: str | None = None) -> None:
    price_date = price_date or last_date
    name, code = row["종목명"], row["코드"]
    ov = dash.add_tab("📊 ETF 개요")
    fee, terr, dy = an.get("총보수"), an.get("추적오차율"), an.get("배당수익률")
    ret = {r["기간"]: r for r in (an.get("returns") or [])}

    # 0) 현재가 히어로 (주가 크게)
    if rt and rt.get("현재가"):
        _diff, _rate = rt.get("전일대비"), rt.get("등락률(%)")
        _chg = f"{_diff:+,.0f}원" if _diff is not None else "-"
        if _rate is not None:
            _chg += f" ({_rate:+.2f}%)"
        ov.add_html_raw_card(D.price_hero_html(
            name, f"{rt['현재가']:,.0f}원", _chg, rt.get("방향", "-"),
            f"실시간(지연) · {rt.get('조회시각','')} 조회 · 네이버 금융"))

    # 1) 헤더 — 코드·종목명 + KPI 4카드 + 상품정보(네이버 ETF 스타일)
    info = [
        ("운용사", an.get("운용사") or row.get("운용사")),
        ("기초지수", an.get("기초지수") or row.get("기초지수")),
        ("총보수", f"연 {fee}%" if fee is not None else None),
        ("추적오차율", f"{terr}%" if terr is not None else None),
        ("순자산", f"{row['순자산(억)']:,.0f}억원 ({last_date} 기준)" if pd.notna(row.get("순자산(억)")) else None),
        ("상장일", _ymd(an.get("상장일"))),
        ("괴리율", (f"{((rt or {}).get('kis_nav') or {})['dprt']}%"
                    if ((rt or {}).get("kis_nav") or {}).get("dprt") is not None
                    else (f"{row['괴리율(%)']}%" if pd.notna(row.get("괴리율(%)")) else None))),
        ("배당수익률(TTM)", f"{dy}%" if dy is not None else None),
    ]
    tags = [t for t in [row.get("테마")] if t]
    ov.add_html_raw_card(D.etf_header_html(
        code, name, f"{price_date} 종가 기준", tags, _kpis(row, rt, ret, ds), info))

    # 2) 종가 캔들차트 (이동평균 + 거래량) — 기간 토글(1주~전체)
    if not chart.empty and len(chart) > 1 and "시가" in chart.columns:
        ov.add_callout("종가 캔들차트 · 이동평균(MA5·20·60·120) · 아래 토글로 기간 선택 "
                       "(상승 빨강·하락 파랑)", "info")
        ov.add_candle_chart("종가 차트 (캔들 · 이동평균)",
                            chart, "일자", "시가", "고가", "저가", "종가",
                            volume_col="거래량")

    # 3) 기간별 수익률 표 (NAV / 종가) — 검색창 제거
    if an.get("returns"):
        ov.add_table("기간별 수익률 (%) — 누적", _period_table(an, chart), search=False)
        ov.add_callout("기준가(NAV)는 분배금 재투자 가정 세전 수익률 · 시장가(종가)는 분배금 미포함 시장 거래가격 기준 · "
                       "누적 수익률.", "info")

    # 4) 포트폴리오 (구성종목 Top 10)
    if an.get("top10"):
        pf = []
        for it in an["top10"]:
            q = quotes.get(str(it.get("종목코드") or ""), {})
            pf.append({
                "종목명": it.get("종목명"), "코드": it.get("종목코드"),
                "주식수": it.get("주식수"), "비중": it.get("비중(%)"),
                "시세": q.get("현재가"), "전일대비": q.get("전일대비"),
                "등락률": q.get("등락률(%)"), "방향": q.get("방향", "-"),
            })
        if not any(i.get("비중") for i in pf):
            ov.add_callout("해외 ETF 등은 개별 구성종목 비중이 제공되지 않아 종목 목록만 표시합니다.", "info")
        ov.add_portfolio("포트폴리오 (구성종목 Top 10)", pf)

    # 5) 섹터 / 국가 비중 — 도넛(파이) 차트
    def _wbar(df, title):  # 국가 비중: 축 글씨를 키운 가로 막대
        fig = D.bar_chart(df.sort_values("비중(%)"), "구분", "비중(%)", horizontal=True)
        fig.update_layout(font=dict(size=15))
        fig.update_yaxes(tickfont=dict(size=17))
        fig.update_xaxes(tickfont=dict(size=13))
        ov.add_figure(title, fig)

    sectors = pd.DataFrame(an.get("sectors") or [])
    countries = pd.DataFrame(an.get("countries") or [])
    assets = pd.DataFrame(an.get("assets") or [])
    if not sectors.empty:
        s = sectors[sectors["비중(%)"] > 0.01]
        if not s.empty:
            ov.add_donut_breakdown("섹터 비중 및 구성", s, "구분", "비중(%)")
    if not countries.empty:
        c = countries[countries["비중(%)"].abs() > 0.01]
        if len(c) > 1:
            _wbar(c, "국가 비중(%)")

    # 6) 투자자별 매매 동향 (최근 30영업일) — '자산 구성' 위에 배치
    if trend:
        ov.add_callout("최근 30영업일 외국인·기관·개인 일별 순매수(주) · 매수(+) 빨강 / 매도(-) 파랑 · 출처 네이버 금융", "info")
        ov.add_investor_trend("투자자별 매매 동향 (최근 30영업일)", trend, visible=8)

    # 7) 자산 비중 및 구성 — 도넛(원그래프) + 우측 리스트
    if not assets.empty:
        a = assets[assets["비중(%)"] > 0.01]
        if not a.empty:
            ov.add_donut_breakdown("자산 비중 및 구성", a, "구분", "비중(%)")


# ── 메인 ───────────────────────────────────────────────────────
async def build(f: Fetcher, settings, query: str) -> None:
    stamp = now_stamp()
    krx = KRXCollector(f, settings.krx_key)
    async with Spinner("KRX ETF 일별매매정보 수집"):
        df = await krx.fetch_market_frame("etf", business_days(date.today(), ETF_LOOKBACK))
    if df.is_empty():
        print("  ETF 데이터를 가져오지 못했습니다 (KRX 권한/네트워크 확인).")
        return
    snap, last_date = E.latest_snapshot(df)
    if snap.empty:
        print("  ETF 스냅샷 생성 실패.")
        return

    row = E.find_etf(snap, query)
    if row is None:
        print(f"  '{query}' 에 해당하는 ETF를 찾지 못했습니다. (종목명 또는 6자리 코드로 입력)")
        return
    code = str(row["코드"])
    print(f"  {row['종목명']} ({code}) · {row.get('운용사','')} · {row.get('기초지수','-')}")
    print(f"  종가 {row['종가']:,.0f}원 · 등락 {row['등락률(%)']}% · 괴리율 {row['괴리율(%)']}% "
          f"· 순자산 {_jo(row.get('순자산(억)'))}")

    # 실시간 시세·ETF 분석·차트(최근 5년)·투자자별 매매 동향(30영업일)을 병렬 수집
    rt, an, chart_rows, trend = await asyncio.gather(
        naver.fetch_realtime_price(f, code),
        naver.fetch_etf_analysis(f, code),
        naver.fetch_price_chart(f, code, days=1900),
        naver.fetch_investor_trend(f, code, days=30))
    chart = pd.DataFrame(chart_rows)
    ds = E.detail_series(df, code)
    # 구성종목 시세(전일대비)를 한 번에 조회
    con_codes = [str(it.get("종목코드")) for it in (an.get("top10") or []) if it.get("종목코드")]
    quotes = await naver.fetch_realtime_quotes(f, con_codes) if con_codes else {}

    # ── 가격 기준일 보정: KRX 일별매매정보는 1~3영업일 지연되므로,
    #    더 최신인 네이버 차트의 마지막 거래일·종가·거래량·등락률로 표시값을 갱신.
    price_date = last_date
    if not chart.empty and "일자" in chart.columns:
        naver_date = str(chart["일자"].iloc[-1])
        if naver_date > (last_date or ""):
            price_date = naver_date
            row = row.copy()
            last_bar = chart.iloc[-1]
            cur_c = pd.to_numeric(last_bar.get("종가"), errors="coerce")
            if pd.notna(cur_c):
                row["종가"] = float(cur_c)
            if "거래량" in chart.columns and pd.notna(last_bar.get("거래량")):
                row["거래량"] = float(last_bar["거래량"])
            if len(chart) >= 2:
                prev_c = pd.to_numeric(chart["종가"].iloc[-2], errors="coerce")
                if pd.notna(prev_c) and prev_c and pd.notna(cur_c):
                    row["등락률(%)"] = round((cur_c - prev_c) / prev_c * 100, 2)

    dash = D.Dashboard(f"{row['종목명']} ({code}) ETF 리포트",
                       f"기준일 {price_date} · {row.get('운용사','')} · {stamp}")
    add_detail_tab(dash, row, rt, an, quotes, chart, ds, last_date, trend, price_date)

    out_html = OUTPUT_DIR / f"etf_{code}_{stamp}.html"
    dash.render(out_html)
    print(f"  ✅ HTML 대시보드: {out_html}")
    if not os.environ.get("MI_NO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(out_html.resolve().as_uri())
        except Exception:  # noqa: BLE001
            pass


async def run_once(query: str) -> None:
    settings = load_settings()
    async with Fetcher() as f:
        await build(f, settings, query)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        asyncio.run(run_once(" ".join(args)))
        return
    print("=" * 60)
    print("  한국 ETF 리포트 (개별 ETF)")
    print("  · ETF 종목명 또는 6자리 코드(영문 포함 가능) 입력")
    print("  · 예: KODEX 200 / 069500 / 0117V0")
    print("  · q / quit → 종료")
    print("=" * 60)
    while True:
        try:
            query = input("\nETF 종목명/코드 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            return
        if query.lower() in {"q", "quit", "exit", "종료"}:
            print("종료합니다.")
            return
        if not query:
            continue
        try:
            asyncio.run(run_once(query))
        except Exception as e:  # noqa: BLE001
            print(f"  [오류] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
