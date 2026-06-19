"""터미널 진행 표시 — 작동 중임을 시각화(스피너 · 진척 바 · 라이브 카운트).

실제 터미널(TTY)에서는 한 줄을 실시간 갱신하는 애니메이션을, 파이프·리다이렉트
환경에서는 주기적인 평범한 한 줄 로그를 출력한다(graceful degradation).
모든 출력은 stderr 로 보내 데이터(stdout)와 분리한다.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Any, Awaitable

_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_BAR_W = 26


def supports_ansi() -> bool:
    return sys.stderr.isatty() and os.environ.get("TERM", "") not in ("", "dumb")


class Progress:
    """완료 건수 기반 진척 바. tick() 호출마다 진행이 갱신된다."""

    def __init__(self, total: int, label: str = "진행") -> None:
        self.total = max(1, total)
        self.label = label
        self.done = 0
        self.fail = 0
        self.last = ""
        self.t0 = time.time()
        self.enabled = supports_ansi()
        self._frame = 0
        self._stop = False
        self._last_plain = 0

    def tick(self, label: str = "", ok: bool = True) -> None:
        self.done += 1
        if not ok:
            self.fail += 1
        if label:
            self.last = label
        if not self.enabled and (self.done - self._last_plain >= 4 or self.done == self.total):
            self._last_plain = self.done
            print(f"  …{self.label} {self.done}/{self.total} ({self.done * 100 // self.total}%)"
                  + (f"  최근: {label}" if label else ""), file=sys.stderr, flush=True)

    def _line(self, final: bool = False) -> str:
        frac = self.done / self.total
        filled = int(frac * _BAR_W)
        bar = "█" * filled + "·" * (_BAR_W - filled)
        el = time.time() - self.t0
        if final:
            mark = "\033[33m✓\033[0m" if self.fail else "\033[32m✓\033[0m"
            extra = f"  \033[31m({self.fail} 실패)\033[0m" if self.fail else ""
            return (f"\r  {mark} {self.label} 완료  \033[32m[{bar}]\033[0m "
                    f"{self.done}/{self.total}  {el:.1f}s{extra}" + " " * 12)
        sp = _SPIN[self._frame % len(_SPIN)]
        tail = (self.last[:20] + "…") if len(self.last) > 20 else self.last
        return (f"\r  \033[36m{sp}\033[0m {self.label}  [{bar}] {self.done:>2}/{self.total}  "
                f"\033[2m{el:4.1f}s  {tail:<22}\033[0m")

    async def spin(self) -> None:
        if not self.enabled:
            print(f"  ◆ {self.label} 시작 (총 {self.total})…", file=sys.stderr, flush=True)
            return
        while not self._stop:
            sys.stderr.write(self._line())
            sys.stderr.flush()
            self._frame += 1
            await asyncio.sleep(0.08)

    def finish(self) -> None:
        self._stop = True
        if self.enabled:
            sys.stderr.write(self._line(final=True) + "\n")
            sys.stderr.flush()
        else:
            extra = f" · {self.fail} 실패" if self.fail else ""
            print(f"  ◆ {self.label} 완료: {self.done}/{self.total} "
                  f"({time.time() - self.t0:.1f}s{extra})", file=sys.stderr, flush=True)


class Spinner:
    """카운트가 없는 단발 대기 구간용 스피너(async 컨텍스트 매니저)."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled = supports_ansi()
        self._stop = False
        self._t0 = time.time()
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        i = 0
        while not self._stop:
            sys.stderr.write(f"\r  \033[36m{_SPIN[i % len(_SPIN)]}\033[0m {self.label}  "
                             f"\033[2m{time.time() - self._t0:4.1f}s\033[0m")
            sys.stderr.flush()
            i += 1
            await asyncio.sleep(0.08)

    async def __aenter__(self) -> "Spinner":
        if self.enabled:
            self._task = asyncio.create_task(self._run())
        else:
            print(f"  ◆ {self.label}…", file=sys.stderr, flush=True)
        return self

    async def __aexit__(self, *exc) -> None:
        self._stop = True
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.enabled:
            sys.stderr.write(f"\r  \033[32m✓\033[0m {self.label}  "
                             f"\033[2m{time.time() - self._t0:.1f}s\033[0m" + " " * 20 + "\n")
            sys.stderr.flush()


async def gather_with_progress(label: str, named: dict[str, Awaitable[Any]]) -> dict[str, Any]:
    """{이름: 코루틴} 을 동시에 실행하되, 완료될 때마다 진척 바를 갱신.

    결과를 {이름: 결과} dict 로 반환(입력 순서 유지). 예외는 그대로 전파한다.
    """
    items = list(named.items())
    prog = Progress(len(items), label)
    spin = asyncio.create_task(prog.spin())

    async def _wrap(name: str, coro: Awaitable[Any]) -> tuple[str, Any]:
        try:
            r = await coro
            prog.tick(name, ok=True)
            return name, r
        except Exception:
            prog.tick(name, ok=False)
            raise

    try:
        pairs = await asyncio.gather(*(_wrap(n, c) for n, c in items))
    finally:
        prog.finish()
        try:
            await spin
        except asyncio.CancelledError:
            pass
    return dict(pairs)
