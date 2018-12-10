import time
import asyncio
from collections.abc import AsyncIterator
from typing import Optional, Union


class ClockTicker(AsyncIterator):
    """
    T - A clock tick
    F - Something that happens inside an iteration ("x" = running "-" = waiting)
    I - A clock iteration

    E.g:

    async for tick in Clock(seconds=2):
        await asyncio.sleep(3)


    T: 15------17------19------21------23------25------27------29------
    F: xxxxxxxxxxxxx---xxxxxxxxxxxxx---xxxxxxxxxxxxx---xxxxxxxxxxxxx---
    I: x---------------x---------------x---------------x---------------

    """
    def __init__(self, seconds: Union[float, int]) -> None:
        """
        :param seconds: Tick interval in seconds
        """
        self.seconds = seconds
        self.current_iteration = 0
        self._tick_event = asyncio.Event()
        self._running: Optional[bool] = None
        self._main_task = asyncio.ensure_future(self._run())
        self.started_at = self.now()

    def now(self) -> int:
        """
        Returns an integer corresponding to the current time in seconds since
        the Epoch
        """
        return int(time.time())

    def __aiter__(self) -> AsyncIterator:
        if self._running is not None:
            raise RuntimeError("Cannot reuse a stopped clock")

        self._running = True
        return self

    async def __anext__(self) -> int:
        if not self._running:
            self.started_at = None
            raise StopAsyncIteration

        while not self._should_iter():
            await self._tick_event.wait()

        self._tick_event.clear()
        i = self.current_iteration
        self.current_iteration += 1
        return i

    def _should_iter(self) -> bool:
        return (self.now() - self.started_at) % self.seconds == 0

    async def _run(self) -> None:
        while self._running:
            print(f"tick! now: {self.now()} started: {self.started_at}")
            self._tick_event.set()
            await asyncio.sleep(self.seconds)
            self._tick_event.clear()

    async def stop(self) -> None:
        self._running = False
        await self._main_task