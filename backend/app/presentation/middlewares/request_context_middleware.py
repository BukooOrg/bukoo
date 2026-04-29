"""
Middleware to add request ID to the context variables.

Reference link: https://github.com/benavlabs/FastAPI-boilerplate/blob/main/src/app/middleware/logger_middleware.py
"""

# import uuid

# import structlog
# from fastapi import FastAPI, Request
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from starlette.responses import Response


# class RequestContextMiddleware(BaseHTTPMiddleware):
#     """Middleware to add request ID to the context variables.

#     Parameters
#     ----------
#     app: FastAPI
#         The FastAPI application instance.
#     """

#     def __init__(self, app: FastAPI) -> None:
#         super().__init__(app)

#     async def dispatch(
#         self, request: Request, call_next: RequestResponseEndpoint
#     ) -> Response:
#         """
#         Add request ID to the context variables.
#         """
#         request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
#         print(request_id)
#         structlog.contextvars.clear_contextvars()
#         structlog.contextvars.bind_contextvars(
#             request_id=request_id,
#             client_host=request.client.host if request.client else None,
#             status_code=None,
#             path=request.url.path,
#             method=request.method,
#         )
#         response = await call_next(request)
#         structlog.contextvars.bind_contextvars(status_code=response.status_code)
#         response.headers["X-Request-ID"] = request_id
#         return response

import uuid
from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers") or [])
        request_id = headers.get(b"x-request-id")
        request_id = request_id.decode() if request_id else str(uuid.uuid4())

        # clear and bind contextvars (logging only)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=scope["path"],
            method=scope["method"],
        )

        # attach to request.state via scope
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                structlog.contextvars.bind_contextvars(status_code=message["status"])
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", request_id.encode()))

            await send(message)

        await self.app(scope, receive, send_wrapper)
