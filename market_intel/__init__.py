"""market_intel — 한국 증시 종합 인텔리전스 툴.

흩어져 있던 증시 정보수집 도구(market_analyzer, sector_rotation,
financial_statements, 뉴스 크롤러)를 하나로 취합한 패키지.

- 비동기 동시 수집(httpx) + polars 멀티스레드 집계로 M4 Pro 12코어 활용
- 산출물: 단일 인터랙티브 HTML 대시보드 (+ 옵션 Excel)
"""

__version__ = "1.0.0"
