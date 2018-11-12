import asyncio
from aiohttp import Signal

from asyncworker.conf import logger
from asyncworker.signal_handlers.http_server import HTTPServer
from asyncworker.models import Routes
from asyncworker.utils import entrypoint


class BaseApp:
    handlers = (HTTPServer(),)

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.routes_registry = Routes()
        self.consumers = []

        self._on_startup = Signal(self)
        self._on_shutdown = Signal(self)

        for handler in self.handlers:
            if handler.is_enabled:
                self._on_startup.append(handler.startup)
                self._on_shutdown.append(handler.shutdown)

    def _build_consumers(self):
        raise NotImplementedError()

    @entrypoint
    async def run(self):
        logger.info("Booting App...")
        self._on_startup.freeze()
        self._on_shutdown.freeze()
        await self.startup()

        while True:
            await asyncio.sleep(10)

    async def startup(self):
        """Causes on_startup signal

        Should be called in the event loop along with the request handler.
        """
        await self._on_startup.send(self)

    def http_route(self, method, path, **kwargs):
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
