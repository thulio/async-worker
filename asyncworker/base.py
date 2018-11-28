import asyncio
from signal import Signals
from collections import MutableMapping
from typing import Iterable, Tuple, Callable, Coroutine

from asyncworker.conf import logger
from asyncworker.signals.handlers.base import SignalHandler
from asyncworker.routes import RoutesRegistry
from asyncworker.options import RouteTypes
from asyncworker.signals.base import Signal, Freezable
from asyncworker.utils import entrypoint


class BaseApp(MutableMapping, Freezable):
    handlers: Tuple[SignalHandler, ...]
    shutdown_os_signals = (Signals.SIGINT, Signals.SIGTERM)

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.routes_registry = RoutesRegistry()
        self.default_route_options: dict = {}

        self._state: dict = {}
        self._frozen = False
        self._on_startup: Signal = Signal(self)
        self._on_shutdown: Signal = Signal(self)

        for handler in self.handlers:
            self._on_startup.append(handler.startup)
            self._on_shutdown.append(handler.shutdown)

        for signal in self.shutdown_os_signals:
            self.loop.add_signal_handler(signal, self.shutdown)

    def _check_frozen(self):
        if self.frozen():
            raise RuntimeError("You shouldnt change the state of started "
                               "application")

    def frozen(self) -> bool:
        return self._frozen

    async def freeze(self) -> None:
        self._frozen = True

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._check_frozen()
        self._state[key] = value

    def __delitem__(self, key):
        self._check_frozen()
        del self._state[key]

    def __len__(self):
        return len(self._state)

    def __iter__(self):
        return iter(self._state)

    @entrypoint
    async def run(self):
        logger.info("Booting App...")
        await self.startup()

        while True:
            await asyncio.sleep(10)

    async def startup(self):
        """
        Causes on_startup signal

        Should be called in the event loop along with the request handler.
        """
        await self._on_startup.send(self)

    def shutdown(self) -> asyncio.Future:
        """
        Schredules an on_startup signal

        Is called automatically when the application receives a SIGINT or SIGTERM
        """
        return asyncio.ensure_future(self._on_shutdown.send(self))

    def route(self,
              routes: Iterable[str],
              type: RouteTypes=RouteTypes.AMQP_RABBITMQ,
              options: dict=None,
              **kwargs):
        if options is None:
            options = {}
        if not isinstance(type, RouteTypes):
            raise TypeError(f"type parameter is not a valid RouteTypes."
                            f" Found: '{type}'")

        def wrapper(f):
            self.routes_registry[f] = {
                'type': type,
                'routes': routes,
                'handler': f,
                'options': options,
                'default_options': self.default_route_options,
                **kwargs
            }
            return f
        return wrapper

    def run_on_startup(self, coro: Callable[['BaseApp'], Coroutine]) -> None:
        """
        Registers a coroutine to be awaited for during app startup
        """
        self._on_startup.append(coro)

    def run_on_shutdown(self, coro: Callable[['BaseApp'], Coroutine]) -> None:
        """
        Registers a coroutine to be awaited for during app shutdown
        """
        self._on_shutdown.append(coro)
