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
"""한국 증시 종목 리포트 — 종목명/코드만 입력하면 끝.

프로세스를 실행하면 안에서 종목명 또는 6자리 코드를 입력받아(반복 가능)
다음 3가지를 생성한다.

  1. 회사 기본 개요  (DART 기업개황 + 전 거래일 시세 스냅샷·52주 밴드)
  2. 최신 정기공시 재무제표  (DART 사업보고서, 손익/재무상태/현금흐름 — 차트 + 표)
  3. 투자지표·재무비율  (전날 종가 기준 PER·PBR·EPS·BPS·EV/EBITDA·배당수익률 등)
     + 보너스: 시장(코스피/코스닥) 대비 상대수익률, 배당 이력

데이터 소스
  - DART(OpenDART) : 기업개황 · 사업보고서 재무제표 · 배당(주당순이익)
  - 금융위원회(data.go.kr) : 개별종목 일별시세(상장주식수·시총) · 지수시세 · 예탁결제원 배당이력
  - (백업) KRX Market Data API

산출물은 단일 인터랙티브 HTML 대시보드(output/)로 저장하고 콘솔에도 요약한다.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date

import pandas as pd
import polars as pl


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from market_intel.analyze import valuation as V
from market_intel.collectors import dart as dart_c
from market_intel.collectors import fsc
from market_intel.collectors import naver
from market_intel.collectors.krx import KRXCollector
from market_intel.config import OUTPUT_DIR, business_days, load_settings, now_stamp
from market_intel.httpx_client import Fetcher
from market_intel.progress import Spinner, gather_with_progress
from market_intel.report import dashboard as D

MARKET_MAP = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX", "E": "기타"}
INDEX_NAME = {"Y": "코스피", "K": "코스닥"}


def _won(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-"
    v = float(v)
    if abs(v) >= 1e12:
        return f"{v/1e12:,.2f}조원"
    if abs(v) >= 1e8:
        return f"{v/1e8:,.0f}억원"
    return f"{v:,.0f}원"


def _pivot_trend(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    return (long_df.pivot(index="연도", columns="항목", values="값(억원)")
            .reset_index().rename_axis(None, axis=1))


def _fmt_metric(label: str, value) -> str:
    """밸류에이션 값 표시 포맷(큰 금액은 조/억, 주식수·원 단위 보기 좋게)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    if any(k in label for k in ("시가총액", "EV(")):
        return _won(value)
    if "상장주식수" in label:
        return f"{value:,.0f}주"
    if any(k in label for k in ("EPS", "BPS", "종가", "DPS")):
        return f"{value:,.0f}원"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _metric_items(val: pd.DataFrame) -> list[tuple]:
    """밸류에이션 DataFrame[지표,값,산식] → 카드용 (라벨, 값, 산식) 목록."""
    return [(r["지표"], _fmt_metric(r["지표"], r["값"]), r["산식"]) for _, r in val.iterrows()]


# ── KRX 백업 스냅샷 (FSC 실패 시) ──────────────────────────────
def _krx_snapshot(prices_pl: pl.DataFrame, code: str) -> pd.DataFrame:
    if prices_pl.is_empty() or "ISU_CD" not in prices_pl.columns:
        return pd.DataFrame()
    sub = (prices_pl.filter(pl.col("ISU_CD").cast(pl.Utf8).str.contains(code))
           .sort("_bas_dt"))
    if sub.is_empty():
        return pd.DataFrame()
    return sub.select([
        pl.col("_bas_dt").dt.strftime("%Y-%m-%d").alias("일자"),
        pl.col("ISU_NM").alias("종목명"), pl.col("MKT_NM").alias("시장"),
        pl.col("TDD_CLSPRC").alias("종가"), pl.col("FLUC_RT").alias("등락률(%)"),
        pl.col("ACC_TRDVOL").alias("거래량"), pl.col("ACC_TRDVAL").alias("거래대금"),
        pl.col("LIST_SHRS").alias("상장주식수"), pl.col("MKTCAP").alias("시가총액"),
    ]).to_pandas().assign(
        일자=lambda d: pd.to_datetime(d["일자"]),
        시가=pd.NA, 고가=pd.NA, 저가=pd.NA,
    )


# ── 메인 ───────────────────────────────────────────────────────
async def build_report(f: Fetcher, settings, query: str) -> None:
    stamp = now_stamp()
    async with Spinner("기업 목록 로드(DART)"):
        corps = await dart_c.load_corp_list(f, settings.dart_key)
    cands = dart_c.search_corp(query, corps)
    if not cands:
        print(f"  '{query}' 에 해당하는 상장 기업을 찾지 못했습니다.")
        return
    # 동명 기업 중 실제 상장(Y/K/N)된 기업 우선 선택 (상장폐지분 회피)
    corp, info = await dart_c.pick_listed_corp(f, settings.dart_key, cands)
    corp_code, stock_code, corp_name = corp["corp_code"], corp["stock_code"], corp["corp_name"]
    if len(cands) > 1:
        others = ", ".join(f"{c['corp_name']}({c['stock_code']})" for c in cands if c is not corp)
        print(f"  {len(cands)}건 중 '{corp_name}({stock_code})' 선택 (다른 후보: {others})")
    corp_cls = info.get("corp_cls", "Y")
    jurir_no = info.get("jurir_no", "").replace("-", "") or None
    idx_name = INDEX_NAME.get(corp_cls, "코스피")

    res = await gather_with_progress(f"{corp_name} 데이터 수집", {
        "stmts": dart_c.fetch_statements(f, settings.dart_key, corp_code),
        "dividend": dart_c.fetch_dividend(f, settings.dart_key, corp_code),
        "hist": fsc.fetch_stock_history(f, settings.fsc_key, stock_code),
        "index": fsc.fetch_index_history(f, settings.fsc_key, idx_name),
        "div_hist": fsc.fetch_dividend_history(f, settings.fsc_key, crno=jurir_no, name=corp_name),
        "rt": naver.fetch_realtime_price(f, stock_code),
    })
    stmts, dividend = res["stmts"], res["dividend"]
    hist, index_hist, div_hist, rt = res["hist"], res["index"], res["div_hist"], res["rt"]

    # FSC 시세 실패 시 KRX 백업
    if hist.empty:
        async with Spinner("FSC 시세 없음 → KRX 백업 수집"):
            krx = KRXCollector(f, settings.krx_key)
            endpoint = "kospi_stock" if corp_cls == "Y" else "kosdaq_stock"
            prices_pl = await krx.fetch_market_frame(endpoint, business_days(date.today(), 12))
        hist = _krx_snapshot(prices_pl, stock_code)

    income = stmts.get("income", pd.DataFrame())
    balance = stmts.get("balance", pd.DataFrame())
    cashflow = stmts.get("cashflow", pd.DataFrame())
    ratios = (dart_c.compute_ratios(income, balance, cashflow, stmts.get("prior_balance"))
              if stmts else pd.DataFrame())
    # 최신 분기(예: 2026.1Q) 재무비율을 연간 표 왼쪽(최신)에 추가
    iratio_label, iratios = dart_c.compute_interim_ratios(stmts) if stmts else (None, None)
    if iratios and not ratios.empty:
        ratios.insert(0, iratio_label, pd.Series(iratios))

    pa = V.price_analytics(hist)
    price = pa.get("전일종가")
    shares = pa.get("상장주식수")
    mktcap = pa.get("시가총액")

    # 배당: FSC 이력의 TTM DPS 우선, 없으면 DART 공시값
    ttm_dps = V.ttm_dividend(div_hist)
    div_for_val = dict(dividend or {})
    if ttm_dps:
        div_for_val["주당현금배당금"] = ttm_dps
        div_for_val["현금배당수익률(%)"] = None  # 종가 기준 재계산 유도
    val = (V.valuation_metrics(stmts, price=price, shares=shares, mktcap=mktcap,
                               dividend=div_for_val)
           if stmts and price else pd.DataFrame())

    market = MARKET_MAP.get(corp_cls, corp_cls)
    fs_label = "연결" if stmts.get("fs_div") == "CFS" else "개별"
    yr = stmts.get("year")

    # ── 콘솔 요약 ──
    print(f"  {corp_name} ({stock_code}) · {market} · 업종 {info.get('induty_code','-')}")
    if price:
        print(f"  전일 종가 {price:,.0f}원 ({pa.get('기준일')}) · 시총 {_won(mktcap)} "
              f"· 등락 {pa.get('등락률(%)')}% · 52주 {pa.get('52주최저'):,.0f}~{pa.get('52주최고'):,.0f}")
    if yr:
        print(f"  기준 재무제표: {yr}년 {fs_label} (사업보고서)")
    if not val.empty:
        kv = {r["지표"]: r["값"] for _, r in val.iterrows()}
        print(f"  PER {kv.get('PER(배)','-')} · PBR {kv.get('PBR(배)','-')} · "
              f"EPS {kv.get('EPS(원)','-')} · 배당수익률 {kv.get('배당수익률(%)','-')}%")

    # ── 대시보드 ──
    dash = D.Dashboard(f"{corp_name} ({stock_code}) 종목 리포트",
                       f"{market} · 기준 재무 {yr}년 {fs_label} · {stamp}")

    # 1) 개요 ─────────────────────────────────────────
    ov = dash.add_tab("🏢 회사 개요")
    if rt and rt.get("현재가"):
        diff = rt.get("전일대비")
        rate = rt.get("등락률(%)")
        chg = f"{diff:+,.0f}원" if diff is not None else "-"
        if rate is not None:
            chg += f" ({rate:+.2f}%)"
        meta = f"실시간(지연) · {rt.get('조회시각','')} 조회 · 네이버 금융"
        ov.add_html_raw_card(D.price_hero_html(
            corp_name, f"{rt['현재가']:,.0f}원", chg, rt.get("방향", "-"), meta))
    rows = [
        ("기업명", info.get("corp_name", corp_name)), ("종목코드", stock_code),
        ("시장", market), ("대표자", info.get("ceo_nm", "-")),
        ("설립일", info.get("est_dt", "-")), ("업종코드", info.get("induty_code", "-")),
        ("결산월", f"{info.get('acc_mt','-')}월"), ("법인등록번호", jurir_no or "-"),
        ("주소", info.get("adres", "-")), ("홈페이지", info.get("hm_url", "-")),
    ]
    if price:
        rows += [
            ("전일 종가", f"{price:,.0f}원 ({pa.get('기준일')})"),
            ("전일 등락률", f"{pa.get('등락률(%)')}%"),
            ("시가총액", _won(mktcap)),
            ("상장주식수", f"{shares:,.0f}주" if shares else "-"),
            ("52주 최고/최저", f"{pa.get('52주최고'):,.0f} / {pa.get('52주최저'):,.0f}원"),
            ("52주 내 위치", f"{pa.get('52주위치(%)')}%"),
            ("최근 1년 수익률", f"{pa.get('1년수익률(%)')}%"),
            ("연율 변동성", f"{pa.get('연율변동성(%)')}%"),
        ]
    kv = "<table class='mi-table'><tbody>" + "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</tbody></table>"
    ov.add_html(f"<section class='card'><h3 class='card-title'>기업 개요</h3>{kv}</section>")
    if not hist.empty and "종가" in hist.columns:
        ph = hist.copy()
        ph["일자"] = ph["일자"].dt.strftime("%Y-%m-%d")
        ov.add_figure("최근 1년 종가 추이", D.line_chart(ph, "일자", "종가"))

    # 2) 재무제표 (시각) ───────────────────────────────
    fin = dash.add_tab("💵 재무제표")
    interim_label = (stmts.get("interim") or {}).get("label")
    if yr:
        extra = f" · 최신 정기공시 {interim_label} 포함" if interim_label else ""
        fin.add_callout(f"기준: {yr}년 {fs_label}재무제표(DART 사업보고서){extra} · 차트 단위 억원", "info")
    pl_trend = V.statement_trend(income, {
        "매출액": ["매출액", "영업수익"], "영업이익": ["영업이익"], "당기순이익": ["당기순이익"]})
    if not pl_trend.empty:
        fin.add_figure("손익 추이 (매출·영업이익·순이익)",
                       D.grouped_bar(_pivot_trend(pl_trend), "연도", ["매출액", "영업이익", "당기순이익"]))
    bs_trend = V.statement_trend(balance, {
        "자산총계": ["자산총계"], "부채총계": ["부채총계", "부채합계"], "자본총계": ["자본총계", "자본합계"]})
    if not bs_trend.empty:
        fin.add_figure("재무상태 추이 (자산·부채·자본)",
                       D.grouped_bar(_pivot_trend(bs_trend), "연도", ["자산총계", "부채총계", "자본총계"]))
    cf_trend = V.statement_trend(cashflow, {
        "영업활동": ["영업활동현금흐름"], "투자활동": ["투자활동현금흐름"], "재무활동": ["재무활동현금흐름"]})
    if not cf_trend.empty:
        fin.add_figure("현금흐름 추이 (영업·투자·재무)",
                       D.grouped_bar(_pivot_trend(cf_trend), "연도", ["영업활동", "투자활동", "재무활동"]))
    inc_df, unit = dart_c.display_statement(stmts, "income")
    bal_df, _ = dart_c.display_statement(stmts, "balance")
    cf_df, _ = dart_c.display_statement(stmts, "cashflow")
    note = (unit + (f" · {interim_label} 포함" if interim_label else "")) if unit else ""
    fin.add_grouped_table("손익계산서 (매출·영업·순이익 구분)", inc_df, note)
    fin.add_grouped_table("재무상태표 (자산·부채·자본 구분)", bal_df, unit)
    fin.add_grouped_table("현금흐름표 (영업·투자·재무 구분)", cf_df, note)

    # 3) 투자지표·재무비율 ─────────────────────────────
    iv = dash.add_tab("📊 투자지표·재무비율")
    if price:
        iv.add_callout(f"전 거래일({pa.get('기준일')}) 종가 {price:,.0f}원 · {V.valuation_basis(stmts)}", "info")
    else:
        iv.add_callout("시세를 가져오지 못해 밸류에이션(PER·PBR 등)은 생략됩니다.", "warn")
    if not val.empty:
        iv.add_metrics("투자지표 (밸류에이션) — 전일 종가 기준", _metric_items(val))
    if not ratios.empty:
        if iratios:
            iv.add_callout(f"재무비율에 최신 분기({iratio_label})를 추가 — 마진·부채/유동비율은 누적/시점값, "
                           f"ROE·ROA·FCF는 연율화(연환산)", "info")
        rtab = ratios.T.reset_index().rename(columns={"index": "연도"})
        rtab["연도"] = rtab["연도"].astype(str)
        for grp, title in [(["영업이익률(%)", "순이익률(%)", "매출총이익률(%)"], "수익성 비율(%)"),
                           (["ROE(%)", "ROA(%)"], "자본효율 (ROE·ROA, %)"),
                           (["부채비율(%)", "유동비율(%)"], "안정성 비율(%)")]:
            cols = [c for c in grp if c in rtab.columns]
            if cols:
                iv.add_figure(title, D.grouped_bar(rtab, "연도", cols))
    ratio_title = "재무비율 (분기 + 연도별)" if iratios else "재무비율 (연도별)"
    iv.add_table(ratio_title, ratios.reset_index() if not ratios.empty else ratios)
    # 배당 이력
    if not div_hist.empty:
        dh = div_hist.copy()
        dh["배당기준일"] = dh["배당기준일"].dt.strftime("%Y-%m-%d")
        iv.add_figure("주당 현금배당금 추이(원)",
                      D.bar_chart(dh.sort_values("배당기준일"), "배당기준일", "주당현금배당금"))
        iv.add_table("배당 이력 (예탁결제원)", dh)

    # 4) 시장 비교 (보너스) ────────────────────────────
    if not hist.empty and not index_hist.empty:
        mc = dash.add_tab("📈 시장 비교")
        merged = pd.merge(
            hist[["일자", "종가"]].rename(columns={"종가": "종목"}),
            index_hist[["일자", "종가"]].rename(columns={"종가": "지수"}),
            on="일자", how="inner").dropna()
        if len(merged) > 2:
            base_s, base_i = merged["종목"].iloc[0], merged["지수"].iloc[0]
            norm = pd.concat([
                pd.DataFrame({"일자": merged["일자"].dt.strftime("%Y-%m-%d"),
                              "시리즈": corp_name, "지수(시작=100)": merged["종목"] / base_s * 100}),
                pd.DataFrame({"일자": merged["일자"].dt.strftime("%Y-%m-%d"),
                              "시리즈": idx_name, "지수(시작=100)": merged["지수"] / base_i * 100}),
            ])
            mc.add_callout(f"{corp_name} vs {idx_name} — 기간 시작일을 100으로 정규화", "info")
            mc.add_figure(f"{corp_name} vs {idx_name} 상대 추이",
                          D.line_chart(norm, "일자", "지수(시작=100)", "시리즈"))
            stock_ret = (merged["종목"].iloc[-1] / base_s - 1) * 100
            idx_ret = (merged["지수"].iloc[-1] / base_i - 1) * 100
            cmp_tbl = pd.DataFrame({
                "구분": [corp_name, idx_name, "초과수익(%p)"],
                "기간수익률(%)": [round(stock_ret, 1), round(idx_ret, 1), round(stock_ret - idx_ret, 1)],
            })
            mc.add_table("기간 수익률 비교", cmp_tbl)

    out_html = OUTPUT_DIR / f"company_{stock_code}_{stamp}.html"
    dash.render(out_html)
    print(f"  ✅ HTML 리포트: {out_html}")
    import os
    if not os.environ.get("MI_NO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(out_html.resolve().as_uri())
        except Exception:  # noqa: BLE001
            pass


async def run_once(query: str) -> None:
    settings = load_settings()
    if not settings.dart_key:
        print("  [오류] DART_KEY 가 없습니다. API.env 를 확인하세요.")
        return
    async with Fetcher() as f:
        await build_report(f, settings, query)


def main() -> None:
    # 인수로 종목을 주면 1회 실행, 없으면 프로세스 내부에서 반복 입력
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        asyncio.run(run_once(" ".join(args)))
        return
    print("=" * 56)
    print("  한국 증시 종목 리포트")
    print("  종목명 또는 6자리 코드를 입력하세요. (종료: q / quit / 빈 줄)")
    print("=" * 56)
    while True:
        try:
            query = input("\n종목명/코드 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            return
        if not query or query.lower() in {"q", "quit", "exit", "종료"}:
            print("종료합니다.")
            return
        try:
            asyncio.run(run_once(query))
        except Exception as e:  # noqa: BLE001 — 한 종목 실패가 세션을 끝내지 않도록
            print(f"  [오류] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
