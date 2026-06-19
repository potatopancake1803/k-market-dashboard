"""Claude API 로 시장 분석 본문(마크다운) 생성.

260514/market_analyzer/claude_report.py 계승. 요약 DataFrame 들을 컨텍스트로 받아
한국어 마크다운 리포트를 생성하고, 대시보드 상단에 렌더된다.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field

import pandas as pd

SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 한국 자본시장 전문 애널리스트입니다. KRX 일별 데이터, 한국은행 매크로 지표,
    OpenDART 공시, 국제 유가, 국내 뉴스 헤드라인, 섹터 로테이션 신호를 기반으로
    한 달간의 코스피·코스닥 시장 동향을 다각도로 심층 분석한 한국어 리포트를 작성합니다.

    규칙:
    - 출력은 한국어 마크다운. 최상단 # 제목, ## 섹션, ### 하위섹션.
    - 구체 수치(가격, %, 거래대금, 일자)를 본문에 인용하되 표는 만들지 말 것(표는 대시보드에 있음).
    - 데이터에 없는 사실을 지어내지 말 것. 누락은 "데이터 미수집"으로 표기.
    - 톤은 침착한 시니어 애널리스트. 길이 2,000~4,000자.

    필수 섹션:
    1. # 코스피·코스닥 시장 리포트 (기간)
    2. ## 핵심 요약 (5~7 불릿)
    3. ## 지수 동향
    4. ## 시장 폭과 거래 활동
    5. ## 종목 하이라이트
    6. ## 섹터·로테이션 신호
    7. ## ETF 시장
    8. ## 매크로 환경 (환율·금리·유가)
    9. ## 공시·뉴스 이슈
    10. ## 리스크와 모니터링 포인트
    11. ## 결론 및 익월 관전 포인트
""")


@dataclass
class ReportContext:
    start_iso: str
    end_iso: str
    biz_days: int
    sheets: dict[str, pd.DataFrame] = field(default_factory=dict)
    news_sample: pd.DataFrame = field(default_factory=pd.DataFrame)
    dart_sample: pd.DataFrame = field(default_factory=pd.DataFrame)


def _compact(df: pd.DataFrame, max_rows: int = 25, max_cols: int = 14) -> str:
    if df is None or df.empty:
        return "(데이터 없음)"
    d = df.iloc[:max_rows, :max_cols]
    return d.to_csv(index=False, sep="|", float_format="%.4f")


def _build_user_prompt(ctx: ReportContext) -> str:
    parts = [f"분석 기간: {ctx.start_iso} ~ {ctx.end_iso} (영업일 {ctx.biz_days}일)",
             "아래는 분석 대상 요약 데이터입니다. 각 블록은 시트 이름과 CSV(|구분)입니다.\n"]
    priority = [
        "지수_요약", "시장일별_KOSPI", "시장일별_KOSDAQ",
        "코스피_상위_상승", "코스피_상위_하락", "코스피_상위_거래대금",
        "코스닥_상위_상승", "코스닥_상위_하락",
        "코스피_섹터요약", "코스닥_섹터요약",
        "섹터_RS", "섹터_ETF거래대금", "섹터_수급연속성",
        "ETF_상위_거래대금", "매크로_요약", "유가_요약",
    ]
    for k in priority:
        df = ctx.sheets.get(k)
        if df is not None and not df.empty:
            parts.append(f"### [{k}]\n{_compact(df)}")
    if not ctx.news_sample.empty:
        cols = [c for c in ["발행일", "검색어", "제목"] if c in ctx.news_sample.columns]
        parts.append("### [뉴스_샘플]\n" + _compact(ctx.news_sample[cols], max_rows=40))
    if not ctx.dart_sample.empty:
        cols = [c for c in ["접수일자", "회사명", "보고서명"] if c in ctx.dart_sample.columns]
        parts.append("### [공시_샘플]\n" + _compact(ctx.dart_sample[cols], max_rows=40))
    parts.append("\n위 자료만 근거로, 시스템 지시에 따라 마크다운 리포트를 작성하세요.")
    return "\n\n".join(parts)


def generate_report(api_key: str, model: str, ctx: ReportContext) -> str:
    if not api_key:
        return "_(Claude API 키 미설정 — 분석 본문 생략. `--no-claude` 또는 키 설정 후 재실행)_"
    try:
        from anthropic import Anthropic
    except ImportError:
        return "_(anthropic 패키지 미설치)_"
    try:
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model, max_tokens=8000, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(ctx)}],
        )
        chunks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "\n".join(chunks).strip() or "_(빈 응답)_"
    except Exception as exc:  # noqa: BLE001
        return f"_(Claude 호출 실패: {exc})_"
