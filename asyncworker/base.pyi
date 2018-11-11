from asyncio import AbstractEventLoop
from typing import Iterable, List, Union

from aiohttp import web
from aiohttp.signals import Signal

from asyncworker import Consumer
from asyncworker.models import Routes
from asyncworker.signal_handlers.base import SignalHandler
from asyncworker.sse.consumer import SSEConsumer


class BaseApp:
    loop: AbstractEventLoop
    handlers: Iterable[SignalHandler]
    routes_registry: Routes
    consumers: List[Union[SSEConsumer, Consumer]]

    _on_startup: Signal
    _on_shutdown: Signal

    http_runner: web.AppRunner
    http_app: web.Application

    def __init__(self) -> None: ...
    def _build_consumers(self): ...
    async def run(self) -> None: ...
    async def startup(self) -> None: ...
    def http_route(self, method: str, path: str, **kwargs): ...
