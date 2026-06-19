"""비동기 HTTP 수집 계층 — M4 Pro 활용 1순위.

- 단일 httpx.AsyncClient + asyncio.Semaphore 로 외부 API 동시 호출 제한
- 디스크 JSON 캐시 (성공 응답만): 같은 요청 재실행 시 네트워크 스킵
- 지수/지정·재시도(backoff)·graceful 실패(None 반환)

기존 순차 루프(영업일 N개 × 엔드포인트, time.sleep)를 asyncio.gather 동시 처리로 대체한다.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from .config import CACHE_DIR, HTTP_CONCURRENCY

_HTTP_CACHE = CACHE_DIR / "http"
_HTTP_CACHE.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def _cache_key(method: str, url: str, params: Any, data: Any) -> str:
    raw = json.dumps(
        {"m": method, "u": url, "p": params, "d": data},
        sort_keys=True, ensure_ascii=False, default=str,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


@dataclass
class Fetcher:
    """공용 비동기 페처. `async with Fetcher() as f:` 로 사용."""

    concurrency: int = HTTP_CONCURRENCY
    timeout: float = 30.0
    retries: int = 2
    use_cache: bool = True
    _client: httpx.AsyncClient | None = field(default=None, init=False)
    _sem: asyncio.Semaphore | None = field(default=None, init=False)

    async def __aenter__(self) -> "Fetcher":
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=self.concurrency * 2,
                                max_keepalive_connections=self.concurrency),
        )
        self._sem = asyncio.Semaphore(self.concurrency)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client is not None:
            await self._client.aclose()

    # ── 핵심 요청 ────────────────────────────────────────────────
    async def fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        cache: bool | None = None,
        parse: str = "json",
    ) -> tuple[int, Any]:
        """(status_code, payload) 반환. payload 는 parse 에 따라 dict/list/str/bytes/None.

        실패(네트워크 예외 등) 시 status_code=0, payload=None.
        """
        assert self._client is not None and self._sem is not None, "Fetcher must be entered"
        do_cache = self.use_cache if cache is None else cache
        ckey = _cache_key(method, url, params, data)
        cpath = _HTTP_CACHE / f"{ckey}.json"

        if do_cache and parse == "json" and cpath.exists():
            try:
                return 200, json.loads(cpath.read_text(encoding="utf-8"))
            except Exception:
                cpath.unlink(missing_ok=True)

        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with self._sem:
                    resp = await self._client.request(
                        method, url, params=params, data=data, headers=headers,
                    )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                await asyncio.sleep(0.4 * (attempt + 1))
                continue

            status = resp.status_code
            if status == 200:
                payload = self._parse(resp, parse)
                if do_cache and parse == "json" and payload is not None:
                    try:
                        cpath.write_text(json.dumps(payload, ensure_ascii=False),
                                         encoding="utf-8")
                    except Exception:
                        pass
                return status, payload
            # 4xx 는 재시도해도 동일 → 즉시 반환
            if 400 <= status < 500:
                return status, self._parse(resp, parse if parse != "json" else "text")
            # 5xx 는 backoff 후 재시도
            await asyncio.sleep(0.5 * (attempt + 1))

        if last_exc is not None:
            return 0, None
        return status, None

    @staticmethod
    def _parse(resp: httpx.Response, parse: str) -> Any:
        try:
            if parse == "json":
                return resp.json()
            if parse == "bytes":
                return resp.content
            return resp.text
        except Exception:
            return None

    async def get_json(self, url: str, **kw) -> Any:
        """200 JSON 만 반환, 그 외 None. 간편 헬퍼."""
        status, payload = await self.fetch(url, parse="json", **kw)
        return payload if status == 200 else None

    async def gather(self, coros: list) -> list:
        """여러 코루틴을 동시에 실행 (예외는 결과에 포함)."""
        return await asyncio.gather(*coros, return_exceptions=True)
