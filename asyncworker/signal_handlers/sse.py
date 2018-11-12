from typing import TYPE_CHECKING
from urllib.parse import urljoin

from aiohttp.client import ClientSession, ClientTimeout

from asyncworker.signal_handlers.base import SignalHandler
from asyncworker.sse.consumer import SSEConsumer

if TYPE_CHECKING:
    from asyncworker.sse.app import SSEApplication


class SSE(SignalHandler):
    async def startup(self, app: 'SSEApplication'):
        session = ClientSession(timeout=ClientTimeout(sock_read=5))
        for _handler, route_info in app.routes_registry.items():
            for route in route_info['routes']:
                consumer = SSEConsumer(
                    route_info=route_info,
                    url=urljoin(app.url, route),
                    username=app.user,
                    password=app.password,
                    session=session
                )
                app.consumers.append(consumer)
        return app.consumers
