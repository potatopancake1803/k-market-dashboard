"""OpenDART 수집기 (비동기).

- 기업코드 목록(corpCode.xml) 다운로드·캐시·검색
- 기간 공시 목록 (코스피/코스닥, 정기·주요사항) 동시 수집
- 개별 종목 3개년 연결재무제표(손익/재무상태/현금흐름) + 재무비율

공시목록은 260514/.../dart_collector.py, 재무제표는
Financial_Statement/{kr_dart,kr_financial_statements}.py 로직 계승.
"""
from __future__ import annotations

import io
import pickle
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime

import pandas as pd

from ..config import CACHE_DIR, fmt_yyyymmdd
from ..httpx_client import Fetcher

DART_BASE = "https://opendart.fss.or.kr/api"
_CORP_CACHE = CACHE_DIR / "dart_corps.pkl"
_CORP_TTL = 60 * 60 * 24 * 7  # 7일
_REPRT_ANNUAL = "11011"  # 사업보고서
# 정기공시 보고서 코드 → 짧은 라벨
_REPRT_SHORT = {"11013": "1Q", "11012": "반기", "11014": "3Q", "11011": "사업"}
# 최신 분기/반기 보고서 탐색 순서(연도 내 최신순: 3Q→반기→1Q)
_INTERIM_CODES = ("11014", "11012", "11013")


# ── 기업코드 목록 ──────────────────────────────────────────────
async def load_corp_list(fetcher: Fetcher, api_key: str, force: bool = False) -> list[dict]:
    if not force and _CORP_CACHE.exists():
        if time.time() - _CORP_CACHE.stat().st_mtime < _CORP_TTL:
            try:
                return pickle.loads(_CORP_CACHE.read_bytes())
            except Exception:
                pass
    if not api_key:
        return []
    status, content = await fetcher.fetch(
        f"{DART_BASE}/corpCode.xml", params={"crtfc_key": api_key},
        parse="bytes", cache=False,
    )
    if status != 200 or not content:
        return []
    try:
        z = zipfile.ZipFile(io.BytesIO(content))
        root = ET.fromstring(z.read(z.namelist()[0]))
    except Exception:
        return []
    corps = [{
        "corp_code": c.findtext("corp_code", ""),
        "corp_name": c.findtext("corp_name", ""),
        "stock_code": c.findtext("stock_code", "").strip(),
    } for c in root.findall("list")]
    try:
        _CORP_CACHE.write_bytes(pickle.dumps(corps))
    except Exception:
        pass
    return corps


def search_corp(query: str, corps: list[dict]) -> list[dict]:
    """이름 또는 6자리 종목코드로 검색 (상장사 우선, 최대 10건).

    이름 검색은 대소문자·공백 무시 (예: 'sk 스퀘어' → 'SK스퀘어').
    """
    q = query.strip()
    digits = q.replace(" ", "")
    if digits.isdigit() and len(digits) == 6:
        return [c for c in corps if c["stock_code"] == digits]
    qn = q.lower().replace(" ", "")

    def norm(s):
        return (s or "").lower().replace(" ", "")

    exact = [c for c in corps if norm(c["corp_name"]) == qn and c["stock_code"]]
    partial = [c for c in corps
               if qn in norm(c["corp_name"]) and c["stock_code"] and c not in exact]
    return (exact + partial)[:10]


# ── 공시 목록 ──────────────────────────────────────────────────
async def _fetch_disclosures(fetcher: Fetcher, api_key: str, start: date, end: date,
                             corp_cls: str, pblntf_ty: str, max_pages: int = 5) -> pd.DataFrame:
    rows: list[dict] = []
    for page in range(1, max_pages + 1):
        data = await fetcher.get_json(
            f"{DART_BASE}/list.json",
            params={
                "crtfc_key": api_key, "bgn_de": fmt_yyyymmdd(start), "end_de": fmt_yyyymmdd(end),
                "corp_cls": corp_cls, "pblntf_ty": pblntf_ty, "page_no": page, "page_count": 100,
            },
        )
        if not isinstance(data, dict) or data.get("status") != "000":
            break
        rows.extend(data.get("list", []))
        if page >= data.get("total_page", 1):
            break
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    keep = [c for c in ["rcept_dt", "corp_name", "corp_code", "stock_code",
                        "report_nm", "flr_nm", "rcept_no"] if c in df.columns]
    return df[keep].rename(columns={
        "rcept_dt": "접수일자", "corp_name": "회사명", "corp_code": "고유번호",
        "stock_code": "종목코드", "report_nm": "보고서명", "flr_nm": "제출인", "rcept_no": "접수번호",
    })


async def collect_dart(fetcher: Fetcher, api_key: str,
                       start: date, end: date) -> dict[str, pd.DataFrame]:
    if not api_key:
        return {}
    specs = [
        ("코스피_정기공시", "Y", "A"), ("코스피_주요사항", "Y", "B"),
        ("코스닥_정기공시", "K", "A"), ("코스닥_주요사항", "K", "B"),
    ]
    results = await fetcher.gather(
        [_fetch_disclosures(fetcher, api_key, start, end, cls, ty) for _, cls, ty in specs]
    )
    out: dict[str, pd.DataFrame] = {}
    for (name, _, _), res in zip(specs, results):
        if isinstance(res, pd.DataFrame) and not res.empty:
            out[name] = res
    return out


# ── 재무제표 ───────────────────────────────────────────────────
async def _fetch_raw_fs(fetcher: Fetcher, api_key: str, corp_code: str,
                        year: str, fs_div: str, reprt_code: str = _REPRT_ANNUAL) -> list[dict]:
    data = await fetcher.get_json(f"{DART_BASE}/fnlttSinglAcntAll.json", params={
        "crtfc_key": api_key, "corp_code": corp_code, "bsns_year": year,
        "reprt_code": reprt_code, "fs_div": fs_div,
    })
    if not isinstance(data, dict) or data.get("status") != "000":
        return []
    return data.get("list", [])


async def _fetch_latest_interim(fetcher: Fetcher, api_key: str, corp_code: str,
                                fs_div: str) -> dict | None:
    """최신 분기/반기 보고서(사업보고서 제외)를 탐색해 원시 항목과 라벨 반환."""
    cur = datetime.today().year
    for y in range(cur, cur - 2, -1):
        for code in _INTERIM_CODES:
            items = await _fetch_raw_fs(fetcher, api_key, corp_code, str(y), fs_div, code)
            if items:
                return {"year": y, "reprt": code,
                        "label": f"{y}.{_REPRT_SHORT[code]}", "items": items}
    return None


def _parse_amt(val: str):
    try:
        return int(val.replace(",", "")) if val else None
    except (ValueError, AttributeError):
        return None


def _items_to_df(items: list[dict], sj_nm: str, year: int) -> pd.DataFrame:
    rows = {}
    for it in items:
        if it.get("sj_nm") != sj_nm:
            continue
        acct = it["account_nm"].strip()
        if not acct or acct in rows:
            continue
        rows[acct] = {
            year: _parse_amt(it.get("thstrm_amount", "")),
            year - 1: _parse_amt(it.get("frmtrm_amount", "")),
            year - 2: _parse_amt(it.get("bfefrmtrm_amount", "")),
        }
    return pd.DataFrame(rows).T.rename_axis("계정과목") if rows else pd.DataFrame()


def _sorted_by(df: pd.DataFrame, priority: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    def key(name: str) -> int:
        for i, kw in enumerate(priority):
            if kw in name:
                return i
        return len(priority)
    return df.loc[sorted(df.index, key=key)].dropna(how="all")


def income_statement(items: list[dict], year: int) -> pd.DataFrame:
    sj = "손익계산서" if any(it["sj_nm"] == "손익계산서" for it in items) else "포괄손익계산서"
    return _sorted_by(_items_to_df(items, sj, year), [
        "매출액", "영업수익", "매출원가", "매출총이익", "판매비", "관리비", "연구개발",
        "영업이익", "금융수익", "금융비용", "법인세비용차감전", "법인세비용", "당기순이익",
    ])


def balance_sheet(items: list[dict], year: int) -> pd.DataFrame:
    return _sorted_by(_items_to_df(items, "재무상태표", year), [
        "자산총계", "유동자산", "현금및현금성자산", "매출채권", "재고자산", "비유동자산",
        "유형자산", "무형자산", "부채총계", "유동부채", "매입채무", "단기차입금",
        "비유동부채", "사채", "장기차입금", "자본총계", "자본금", "이익잉여금",
    ])


def cash_flow(items: list[dict], year: int) -> pd.DataFrame:
    return _sorted_by(_items_to_df(items, "현금흐름표", year), [
        "영업활동현금흐름", "투자활동현금흐름", "유형자산의 취득", "재무활동현금흐름",
        "배당금의 지급", "기말현금",
    ])


async def fetch_statements(fetcher: Fetcher, api_key: str, corp_code: str) -> dict:
    """최근 사업연도 기준 3개년 재무제표 (연결 우선, 없으면 개별) + 최신 정기공시(분기/반기)."""
    cur = datetime.today().year
    for fs_div in ("CFS", "OFS"):
        for year in range(cur - 1, cur - 4, -1):
            items = await _fetch_raw_fs(fetcher, api_key, corp_code, str(year), fs_div)
            if items:
                interim = await _fetch_latest_interim(fetcher, api_key, corp_code, fs_div)
                interim_prev = None
                if interim:  # TTM 계산용 전년 동기 분기/반기
                    prev_items = await _fetch_raw_fs(
                        fetcher, api_key, corp_code, str(interim["year"] - 1),
                        fs_div, interim["reprt"])
                    if prev_items:
                        interim_prev = {"items": prev_items}
                # 가장 오래된 표시연도(year-2)의 ROE·ROA 평균계산용 전년(year-3) 자본·자산.
                #   직전 사업연도(year-1) 보고서의 전전기(bfefrmtrm)에서 추출.
                prior_balance = None
                prev_ann = await _fetch_raw_fs(fetcher, api_key, corp_code, str(year - 1), fs_div)
                if prev_ann:
                    pe = raw_item_value(prev_ann, "재무상태표", ["자본총계", "자본합계"],
                                        field="bfefrmtrm_amount")
                    pas = raw_item_value(prev_ann, "재무상태표", ["자산총계"],
                                         field="bfefrmtrm_amount")
                    if pe or pas:
                        prior_balance = {"year": year - 3, "equity": pe, "assets": pas}
                return {
                    "year": year, "fs_div": fs_div, "raw": items,
                    "interim": interim, "interim_prev": interim_prev,
                    "prior_balance": prior_balance,
                    "income": income_statement(items, year),
                    "balance": balance_sheet(items, year),
                    "cashflow": cash_flow(items, year),
                }
    return {}


# ── 원시 항목 추출기 (지배주주·TTM 산출용) ─────────────────────
def raw_item_value(items: list[dict], sj: str, keywords: list[str],
                   exclude: tuple = (), field: str = "thstrm_amount") -> int | None:
    """sj(재무제표) 내에서 keywords 중 하나를 포함하는 첫 계정의 금액.

    field 로 당기(thstrm)·전기(frmtrm)·전전기(bfefrmtrm) 금액을 선택할 수 있다.
    """
    for it in items:
        if it.get("sj_nm") != sj:
            continue
        a = it["account_nm"].strip()
        if any(x in a for x in exclude):
            continue
        if any(k in a for k in keywords):
            return _parse_amt(it.get(field, ""))
    return None


def total_net_income(items: list[dict]) -> int | None:
    """총 당기순이익(지배+비지배). 분기/반기는 '분기순이익'·'반기순이익'으로 표기."""
    sj = _income_sj(items)
    bottom = ("당기순이익", "분기순이익", "반기순이익", "반기순손익", "분기순손익")
    for it in items:
        if it.get("sj_nm") != sj:
            continue
        a = it["account_nm"].strip()
        if (any(p in a for p in bottom) and "차감" not in a and "포괄" not in a
                and "주당" not in a and "지배" not in a and "비지배" not in a):
            return _parse_amt(it.get("thstrm_amount", ""))
    return None


def controlling_net_income(items: list[dict]) -> int | None:
    """지배기업 소유주 귀속 당기순이익. '당기순이익' 직후의 '지배기업…소유주' 라인.

    포괄손익 구획의 동명(지배기업의 소유주지분)과 혼동되지 않도록 당기순이익을
    먼저 만난 뒤의 지배 라인을 취한다. 없으면 총 당기순이익으로 대체.
    """
    sj = _income_sj(items)
    total, seen = None, False
    # 분기/반기 보고서는 '분기순이익'·'반기순이익'으로 표기되므로 모두 포착
    bottom = ("당기순이익", "분기순이익", "반기순이익", "반기순손익", "분기순손익")
    for it in items:
        if it.get("sj_nm") != sj:
            continue
        a = it["account_nm"].strip()
        if (any(p in a for p in bottom) and "차감" not in a and "포괄" not in a
                and "주당" not in a and "지배" not in a and "비지배" not in a):
            total = _parse_amt(it.get("thstrm_amount", ""))
            seen = True
            continue
        if seen and "지배기업" in a and "비지배" not in a and "포괄" not in a:
            v = _parse_amt(it.get("thstrm_amount", ""))
            if v is not None:
                return v
    return total


def controlling_equity(items: list[dict]) -> int | None:
    """지배주주지분 = 자본총계 − 비지배지분(최근 시점 재무상태표)."""
    total = raw_item_value(items, "재무상태표", ["자본총계", "자본합계"])
    if total is None:
        return None
    minor = raw_item_value(items, "재무상태표", ["비지배지분", "비지배주주지분"])
    return total - (minor or 0)


def net_debt(items: list[dict]) -> int | None:
    """순차입금 = (단기·장기차입금+사채+유동성장기부채) − 현금및현금성자산."""
    debt = sum(v for v in (
        raw_item_value(items, "재무상태표", ["단기차입금"]),
        raw_item_value(items, "재무상태표", ["장기차입금"]),
        raw_item_value(items, "재무상태표", ["사채"]),
        raw_item_value(items, "재무상태표", ["유동성장기"]),
    ) if v)
    cash = raw_item_value(items, "재무상태표", ["현금및현금성자산"])
    return debt - (cash or 0)


def income_revenue(items: list[dict]) -> int | None:
    return raw_item_value(items, _income_sj(items), ["매출액", "영업수익"])


def income_operating(items: list[dict]) -> int | None:
    return raw_item_value(items, _income_sj(items), ["영업이익"])


def cf_depreciation(items: list[dict]) -> int | None:
    dep = raw_item_value(items, "현금흐름표", ["감가상각"])
    intan = raw_item_value(items, "현금흐름표", ["무형자산상각", "무형자산의 상각"])
    s = sum(v for v in (dep, intan) if v)
    return s or None


# ── 그룹화된 표시용 재무제표 (자산/부채/자본 등 구분 + 최신 분기 컬럼) ──────
_SECTION_ORDER = {
    "balance": ["자산", "부채", "자본"],
    "income": ["매출·매출총이익", "영업손익", "영업외·세전", "순이익·포괄손익", "기타"],
    "cashflow": ["영업활동", "투자활동", "재무활동", "기타"],
}


def _bs_section(acct: str) -> str:
    if "부채와자본" in acct:        # 총계(=자산총계) → 자산 구획에
        return "자산"
    cap = ("자본", "이익잉여금", "주식발행초과금", "지배기업 소유주", "비지배지분",
           "자기주식", "기타자본", "신종자본")
    liab = ("부채", "차입금", "사채", "매입채무", "예수금", "미지급", "선수금",
            "충당부채", "리스부채", "예수부채")
    if any(k in acct for k in cap):
        return "자본"
    if any(k in acct for k in liab):
        return "부채"
    return "자산"


def _is_section(acct: str) -> str:
    if any(k in acct for k in ("매출원가", "매출총이익")) or acct in ("매출액", "영업수익"):
        return "매출·매출총이익"
    if any(k in acct for k in ("판매비", "관리비", "물류비", "연구개발", "영업이익", "영업손실")):
        return "영업손익"
    if any(k in acct for k in ("금융수익", "금융비용", "기타수익", "기타비용", "지분법",
                               "차감전", "외환")):
        return "영업외·세전"
    if any(k in acct for k in ("법인세", "당기순이익", "당기순손실", "순손익", "포괄",
                               "주당", "지배기업")):
        return "순이익·포괄손익"
    return "기타"


def _cf_section_map(items: list[dict]) -> dict[str, str]:
    """현금흐름표를 API 순서대로 훑어 각 계정의 활동 구분을 매핑."""
    m: dict[str, str] = {}
    cur = "기타"
    summary = ("기초", "기말", "외화환산", "현금및현금성자산의 증가", "현금및현금성자산의 순증가",
               "매각예정분류")
    for it in items:
        if it.get("sj_nm") != "현금흐름표":
            continue
        a = it["account_nm"].strip()
        if "현금흐름" in a and "영업활동" in a:
            cur = "영업활동"
        elif "현금흐름" in a and "투자활동" in a:
            cur = "투자활동"
        elif "현금흐름" in a and "재무활동" in a:
            cur = "재무활동"
        m[a] = "기타" if any(k in a for k in summary) else cur
    return m


def _section_of(kind: str, acct: str, cf_map: dict | None) -> str:
    if kind == "balance":
        return _bs_section(acct)
    if kind == "income":
        return _is_section(acct)
    return (cf_map or {}).get(acct, "기타")


def display_statement(stmts: dict, kind: str, unit: float = 1e8) -> tuple[pd.DataFrame, str]:
    """그룹(구분)·최신분기 컬럼을 포함한 표시용 재무제표(단위 억원) + 단위라벨.

    kind: 'income' | 'balance' | 'cashflow'. raw 항목 순서를 보존해 가독성을 높인다.
    """
    items = stmts.get("raw") or []
    year = stmts.get("year")
    if not items or year is None:
        return pd.DataFrame(), ""
    sjmap = {"income": _income_sj(items), "balance": "재무상태표", "cashflow": "현금흐름표"}
    sj = sjmap[kind]
    seckind = {"income": "income", "balance": "balance", "cashflow": "cashflow"}[kind]
    cf_map = _cf_section_map(items) if kind == "cashflow" else None

    interim = stmts.get("interim")
    icol = None
    imap: dict[str, int | None] = {}
    if interim and interim.get("items"):
        isj = _income_sj(interim["items"]) if kind == "income" else sj
        suffix = "" if kind == "balance" else "(누적)"
        icol = f"{interim['label']}{suffix}"
        for it in interim["items"]:
            if it.get("sj_nm") == isj:
                acct = it["account_nm"].strip()
                if acct and acct not in imap:
                    imap[acct] = _parse_amt(it.get("thstrm_amount", ""))

    def scale(v):
        return None if v is None else round(v / unit)

    rows, seen = [], set()
    for it in items:
        if it.get("sj_nm") != sj:
            continue
        acct = it["account_nm"].strip()
        if not acct or acct in seen:
            continue
        seen.add(acct)
        row = {"구분": _section_of(seckind, acct, cf_map), "계정과목": acct}
        if icol:
            row[icol] = scale(imap.get(acct))
        row[f"{year}년"] = scale(_parse_amt(it.get("thstrm_amount", "")))
        row[f"{year - 1}년"] = scale(_parse_amt(it.get("frmtrm_amount", "")))
        row[f"{year - 2}년"] = scale(_parse_amt(it.get("bfefrmtrm_amount", "")))
        rows.append(row)
    if not rows:
        return pd.DataFrame(), ""
    df = pd.DataFrame(rows)
    val_cols = [c for c in df.columns if c not in ("구분", "계정과목")]
    order = {s: i for i, s in enumerate(_SECTION_ORDER[seckind])}
    df["_o"] = df["구분"].map(order).fillna(99).astype(int)
    df = (df.sort_values("_o", kind="stable").drop(columns="_o")
          .dropna(subset=val_cols, how="all").reset_index(drop=True))
    return df, "단위: 억원"


def _income_sj(items: list[dict]) -> str:
    return "손익계산서" if any(it.get("sj_nm") == "손익계산서" for it in items) else "포괄손익계산서"


def _get(df: pd.DataFrame, keywords: list[str], col) -> float | None:
    for kw in keywords:
        m = [idx for idx in df.index if kw in idx]
        if not m:
            continue
        # 정확 일치 우선, 그다음 짧은 계정명 우선.
        #   '부채총계' 가 '자본과부채총계'(=총자산) 같은 합계항목에 부분일치하는 오인을 방지.
        m.sort(key=lambda idx: (idx != kw, len(idx)))
        for cand in m:
            try:
                v = df.loc[cand, col]
            except Exception:
                continue
            if v is not None and not pd.isna(v):
                return float(v)
    return None


def compute_ratios(income: pd.DataFrame, balance: pd.DataFrame,
                   cashflow: pd.DataFrame, prior_balance: dict | None = None) -> pd.DataFrame:
    """주요 재무비율. Financial_Statement/kr_financial_statements.py:138 계승.

    prior_balance: 가장 오래된 표시연도의 ROE·ROA 평균계산용 전년 자본/자산
                   {"year": Y, "equity": .., "assets": ..} (재무제표 컬럼에 없는 해).
    """
    rows = {}
    years = sorted(set(income.columns) | set(balance.columns), reverse=True)
    for y in years:
        r: dict = {}
        revenue = _get(income, ["매출액", "영업수익"], y)
        gp = _get(income, ["매출총이익"], y)
        op = _get(income, ["영업이익"], y)
        ni = _get(income, ["당기순이익"], y)
        assets = _get(balance, ["자산총계"], y)
        equity = _get(balance, ["자본총계", "자본합계"], y)
        assets_p = _get(balance, ["자산총계"], y - 1)
        equity_p = _get(balance, ["자본총계", "자본합계"], y - 1)
        # 재무제표 컬럼에 전년이 없으면(가장 오래된 해) prior_balance 로 보완
        if prior_balance and prior_balance.get("year") == y - 1:
            equity_p = equity_p if equity_p is not None else prior_balance.get("equity")
            assets_p = assets_p if assets_p is not None else prior_balance.get("assets")
        liab = _get(balance, ["부채총계", "부채합계"], y)
        cur_a = _get(balance, ["유동자산"], y)
        cur_l = _get(balance, ["유동부채"], y)
        op_cf = _get(cashflow, ["영업활동현금흐름"], y)
        capex = _get(cashflow, ["유형자산의 취득"], y)
        # ROE·ROA 는 기초·기말 평균 자본/자산 기준(증권사·네이버 관행)
        avg_eq = (equity + equity_p) / 2 if equity and equity_p else equity
        avg_as = (assets + assets_p) / 2 if assets and assets_p else assets
        if revenue and gp:
            r["매출총이익률(%)"] = round(gp / revenue * 100, 1)
        if revenue and op:
            r["영업이익률(%)"] = round(op / revenue * 100, 1)
        if revenue and ni:
            r["순이익률(%)"] = round(ni / revenue * 100, 1)
        if avg_as and ni:
            r["ROA(%)"] = round(ni / avg_as * 100, 1)
        if avg_eq and ni:
            r["ROE(%)"] = round(ni / avg_eq * 100, 1)
        if liab and equity:
            r["부채비율(%)"] = round(liab / equity * 100, 1)
        if cur_a and cur_l:
            r["유동비율(%)"] = round(cur_a / cur_l * 100, 1)
        if op_cf and capex and capex < 0:
            r["FCF(억)"] = round((op_cf + capex) / 1e8)
        rows[y] = r
    return pd.DataFrame(rows).rename_axis("비율") if rows else pd.DataFrame()


# 정기공시 보고서 코드 → 연율화 계수(분기누적 → 연환산)
_ANNUALIZE = {"11013": 4.0, "11012": 2.0, "11014": 4 / 3, "11011": 1.0}


def compute_interim_ratios(stmts: dict) -> tuple[str | None, dict | None]:
    """최신 분기/반기 보고서 기준 재무비율 (연간 표와 동일 산식·항목).

    - 마진(매출총이익률·영업이익률·순이익률)·부채비율·유동비율: 누적/시점값 그대로(비교 가능).
    - ROE·ROA·FCF: 분기 누적이므로 보고기간에 맞춰 연율화(annualize)한다.
    - ROE·ROA 의 분모는 (당기말+전기말)/2 평균(연간 compute_ratios 와 동일 관행).
    반환: (컬럼라벨 예 '2026.1Q', {비율명: 값}) — 데이터 없으면 (None, None).
    """
    interim = stmts.get("interim")
    if not interim or not interim.get("items"):
        return None, None
    items = interim["items"]
    factor = _ANNUALIZE.get(interim.get("reprt", ""), 1.0)
    sj = _income_sj(items)

    revenue = raw_item_value(items, sj, ["매출액", "영업수익"])
    gp = raw_item_value(items, sj, ["매출총이익"])
    op = raw_item_value(items, sj, ["영업이익"])
    ni = total_net_income(items)
    assets = raw_item_value(items, "재무상태표", ["자산총계"])
    assets_p = raw_item_value(items, "재무상태표", ["자산총계"], field="frmtrm_amount")
    equity = raw_item_value(items, "재무상태표", ["자본총계", "자본합계"])
    equity_p = raw_item_value(items, "재무상태표", ["자본총계", "자본합계"], field="frmtrm_amount")
    # '부채총계' 가 합계항목('자본과부채총계' 등)에 부분일치하지 않도록 제외
    _LIAB_EXC = ("자본과부채", "부채와자본", "부채및자본")
    liab = raw_item_value(items, "재무상태표", ["부채총계", "부채합계"], exclude=_LIAB_EXC)
    cur_a = raw_item_value(items, "재무상태표", ["유동자산"], exclude=("비유동",))
    cur_l = raw_item_value(items, "재무상태표", ["유동부채"], exclude=("비유동",))
    op_cf = raw_item_value(items, "현금흐름표", ["영업활동현금흐름"])
    capex = raw_item_value(items, "현금흐름표", ["유형자산의 취득"])

    avg_eq = (equity + equity_p) / 2 if equity and equity_p else equity
    avg_as = (assets + assets_p) / 2 if assets and assets_p else assets

    r: dict = {}
    if revenue and gp:
        r["매출총이익률(%)"] = round(gp / revenue * 100, 1)
    if revenue and op:
        r["영업이익률(%)"] = round(op / revenue * 100, 1)
    if revenue and ni:
        r["순이익률(%)"] = round(ni / revenue * 100, 1)
    if avg_as and ni:
        r["ROA(%)"] = round(ni * factor / avg_as * 100, 1)
    if avg_eq and ni:
        r["ROE(%)"] = round(ni * factor / avg_eq * 100, 1)
    if liab and equity:
        r["부채비율(%)"] = round(liab / equity * 100, 1)
    if cur_a and cur_l:
        r["유동비율(%)"] = round(cur_a / cur_l * 100, 1)
    if op_cf and capex and capex < 0:
        r["FCF(억)"] = round((op_cf + capex) * factor / 1e8)
    return interim["label"], (r or None)


async def get_company_info(fetcher: Fetcher, api_key: str, corp_code: str) -> dict:
    data = await fetcher.get_json(f"{DART_BASE}/company.json",
                                  params={"crtfc_key": api_key, "corp_code": corp_code})
    return data if isinstance(data, dict) and data.get("status") == "000" else {}


_LISTED_CLS = ("Y", "K", "N")  # KOSPI·KOSDAQ·KONEX (E=기타/상장폐지)


async def pick_listed_corp(fetcher: Fetcher, api_key: str, cands: list[dict],
                           max_probe: int = 6) -> tuple[dict, dict]:
    """후보 중 실제 상장(corp_cls Y/K/N)인 기업을 우선 선택해 (corp, info) 반환.

    동명 기업에 상장폐지분(예: 옛 삼성물산 000830, corp_cls=E)이 섞여 검색 상위로
    올라오는 문제를 막는다. 첫 후보가 상장사면 추가 조회 없이 즉시 반환.
    """
    if not cands:
        return {}, {}
    first_info: dict = {}
    for i, c in enumerate(cands[:max_probe]):
        info = await get_company_info(fetcher, api_key, c["corp_code"])
        if i == 0:
            first_info = info
        if info.get("corp_cls") in _LISTED_CLS:
            return c, info
    return cands[0], first_info


async def fetch_dividend(fetcher: Fetcher, api_key: str, corp_code: str) -> dict:
    """최근 사업연도 배당 정보 (alotMatter.json). 보통주 기준 핵심값 추출.

    반환: {year, 주당현금배당금, 현금배당수익률(%), 주당순이익, 액면가, 현금배당성향(%)}.
    값이 없으면 빈 dict.
    """
    cur = datetime.today().year
    for year in range(cur - 1, cur - 4, -1):
        data = await fetcher.get_json(f"{DART_BASE}/alotMatter.json", params={
            "crtfc_key": api_key, "corp_code": corp_code,
            "bsns_year": str(year), "reprt_code": _REPRT_ANNUAL,
        })
        if not isinstance(data, dict) or data.get("status") != "000":
            continue
        items = data.get("list", [])
        if not items:
            continue

        def pick(keyword: str, *, common_only: bool = True):
            for it in items:
                se = it.get("se", "")
                if keyword not in se:
                    continue
                if common_only and it.get("stock_knd") not in ("", "보통주", "-", None):
                    continue
                v = _parse_amt(it.get("thstrm", ""))
                if v is not None:
                    return v
            return None

        # 현금배당수익률은 % 라 소수 포함 → 별도 파싱
        def pick_float(keyword: str):
            for it in items:
                if keyword in it.get("se", "") and it.get("stock_knd") in ("", "보통주", "-", None):
                    try:
                        return float(str(it.get("thstrm", "")).replace(",", ""))
                    except (ValueError, TypeError):
                        continue
            return None

        out = {
            "year": year,
            "주당현금배당금": pick("주당 현금배당금"),
            "현금배당수익률(%)": pick_float("현금배당수익률"),
            "주당순이익": pick("주당순이익"),
            "액면가": pick("주당액면가"),
            "현금배당성향(%)": pick_float("현금배당성향"),
        }
        if any(v is not None for k, v in out.items() if k != "year"):
            return out
    return {}


def _to_pct(v) -> float | None:
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


async def fetch_major_shareholders(fetcher: Fetcher, api_key: str, corp_code: str) -> dict:
    """최대주주 및 특수관계인 현황 (hyslrSttus.json) — 보통주 기준 기말 지분율.

    반환: {"year": 사업연도, "holders": [{성명, 관계, 지분율(%)}], "최대주주측합계(%)": float}.
    동일 성명이 여러 행이면 합산. 합계('계') 행은 최대주주측 총지분으로 사용. 없으면 빈 dict.
    """
    cur = datetime.today().year
    for year in range(cur - 1, cur - 4, -1):
        data = await fetcher.get_json(f"{DART_BASE}/hyslrSttus.json", params={
            "crtfc_key": api_key, "corp_code": corp_code,
            "bsns_year": str(year), "reprt_code": _REPRT_ANNUAL,
        })
        if not isinstance(data, dict) or data.get("status") != "000":
            continue
        rows = data.get("list", [])
        if not rows:
            continue

        agg: dict[str, dict] = {}
        total: float | None = None
        for r in rows:
            if r.get("stock_knd") != "보통주":   # 보통주만 (우선주 중복 제외)
                continue
            nm = (r.get("nm") or "").strip()
            rate = _to_pct(r.get("trmend_posesn_stock_qota_rt"))
            if nm in ("계", "소계"):
                if rate is not None:
                    total = rate
                continue
            if not nm or rate is None:
                continue
            if nm not in agg:
                agg[nm] = {"성명": nm, "관계": (r.get("relate") or "").strip(), "지분율(%)": 0.0}
            agg[nm]["지분율(%)"] += rate

        holders = sorted(agg.values(), key=lambda x: x["지분율(%)"], reverse=True)
        for h in holders:
            h["지분율(%)"] = round(h["지분율(%)"], 2)
        if not holders:
            continue
        if total is None:
            total = round(sum(h["지분율(%)"] for h in holders), 2)
        return {"year": year, "holders": holders, "최대주주측합계(%)": round(total, 2)}
    return {}
