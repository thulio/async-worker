from typing import TYPE_CHECKING
from urllib.parse import urljoin

from asyncworker.signals.handlers.base import SignalHandler
from asyncworker.sse.consumer import SSEConsumer


if TYPE_CHECKING:  # pragma: no cover
    from asyncworker.sse.app import SSEApplication


class SSE(SignalHandler):
    async def startup(self, app: 'SSEApplication'):
        app['sse_consumers'] = []
        for route_info in app.routes_registry.sse_routes:
            for route in route_info['routes']:
                consumer = SSEConsumer(
                    route_info=route_info,
                    url=urljoin(app.url, route),
                    username=app.user,
                    password=app.password
                )
                app['sse_consumers'].append(consumer)
                app.loop.create_task(consumer.start())