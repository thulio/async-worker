from typing import Dict, Callable
from urllib.parse import urljoin


from asyncworker import BaseApp, HTTPServer
from asyncworker.options import Options, Defaultvalues
from asyncworker.signal_handlers.sse import SSE
from asyncworker.sse.consumer import SSEConsumer


SSE_DEFAULT_HEADERS = {
    "Accept": "text/event-stream",
}


class SSEApplication(BaseApp):
    handlers = (SSE(), HTTPServer())

    def __init__(self,
                 url: str,
                 logger,
                 user: str=None,
                 password: str=None,
                 headers: Dict[str, str]=SSE_DEFAULT_HEADERS) -> None:
        super(SSEApplication, self).__init__()
        self.url = url
        self.user = user
        self.password = password
        self.headers = headers
        self.logger = logger

    def route(self, routes, headers={}, options={}):
        def wrap(f):
            self.routes_registry[f] = {
                "routes": routes,
                "handler": f,
                "options": {
                    "bulk_size": options.get(Options.BULK_SIZE, Defaultvalues.BULK_SIZE),
                    "bulk_flush_interval": options.get(Options.BULK_FLUSH_INTERVAL, Defaultvalues.BULK_FLUSH_INTERVAL),
                    "headers": {
                        **self.headers,
                        **headers,
                    },
                }
            }
            return f
        return wrap

