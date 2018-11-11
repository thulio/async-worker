import asyncio
from typing import Optional, Dict

from aiohttp import web, Signal

from asyncworker.conf import settings, logger
from asyncworker.http_server import HTTPServer
from asyncworker.models import Routes, Route
from asyncworker.utils import entrypoint


class BaseApp:
    http_app: Optional[web.Application]
    http_runner: Optional[web.AppRunner]

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.routes_registry: Routes[Route, Dict] = Routes()

        self._on_startup = Signal(self)

    def _build_consumers(self):
        raise NotImplementedError()

    @entrypoint
    async def run(self) -> None:
        logger.info("Booting App...")
        self._on_startup.freeze()
        await self.startup()
        consumers = self._build_consumers()
        for consumer in consumers:
            self.loop.create_task(consumer.start())
        while True:
            await asyncio.sleep(10)

    async def startup(self) -> None:
        """Causes on_startup signal

        Should be called in the event loop along with the request handler.
        """
        await self._on_startup.send(self)

    def http_route(self, method: str, path: str, **kwargs):
        def wrap(f):
            self.routes_registry[f] = {
                'type': 'http',
                'method': method,
                'path': path,
                'handler': f,
                **kwargs
            }
            return f
        return wrap
