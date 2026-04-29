"""
Http response envelope middleware.

Consistent Response Envelope Every API response **must** follow the same top-level shape. A uniform envelope allows clients to write generic error handling and parsing logic without special-casing individual endpoints.

1. Success Response
```json
    {
        "success": true,
        "data": {
            "id": 42,
            "name": "Jane Doe",
            "email": "jane@example.com"
        },
        "meta": {
            "requestId": "req_abc123",
            "timestamp": "2026-02-25T10:30:00Z"
        }
    }
```
2. Error Response Use the same envelope structure, replacing data with an error object.
```json
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Email is required",
            "details": [{ "field": "email", "message": "must not be empty" }]
        },
        "meta": {
            "requestId": "req_def456",
            "timestamp": "2026-02-25T10:30:01Z"
        }
    }
```

For validation errors with multiple fields:
```json
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [
            {
                "field": "name",
                "message": "Name is required",
                "code": "REQUIRED_FIELD"
            },
            {
                "field": "photoUrls",
                "message": "At least one photo URL is required",
                "code": "REQUIRED_FIELD"
            }
            ]
        },
        "meta": {
            "requestId": "req_ghi789",
            "timestamp": "2026-02-25T10:30:02Z"
        }
    }
```
"""

# import json
# import traceback
# from datetime import UTC, datetime

# import structlog
# from fastapi import Request, Response
# from fastapi.responses import JSONResponse
# from starlette.middleware.base import BaseHTTPMiddleware

# from app.application.errors.error_codes import ErrorCode
# from app.domain.exceptions.base import DomainException
# from app.presentation.http.exception_mapper import EXCEPTION_MAP

# logger = structlog.get_logger()


# EXCLUDED_PATHS = {
#     "/docs",
#     "/redoc",
#     "/openapi.json",
#     "/health",
# }


# class ResponseFormatterMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # skip excluded paths
#         if request.url.path in EXCLUDED_PATHS:
#             return await call_next(request)

#         try:
#             response = await call_next(request)

#             # 204 (no body)
#             if response.status_code == 204:
#                 return response

#             content_type = response.headers.get("content-type", "")

#             # oOnly wrap JSON responses
#             if "application/json" not in content_type:
#                 return response

#             # avoid breaking streaming responses
#             if hasattr(response, "body_iterator"):
#                 body = b""
#                 async for chunk in response.body_iterator:
#                     body += chunk
#             else:
#                 body = response.body

#             data = json.loads(body) if body else None

#             envelope = {
#                 "success": True,
#                 "data": data,
#                 "meta": self._meta(),
#             }

#             return JSONResponse(
#                 status_code=response.status_code,
#                 content=envelope,
#             )

#         except Exception as exc:
#             return await self._handle_exception(exc)

#     async def _handle_exception(self, exc: Exception) -> Response:
#         # domain exception
#         if isinstance(exc, DomainException):
#             mapping = EXCEPTION_MAP.get(type(exc))

#             if mapping:
#                 return self._error_response(
#                     status_code=mapping.status_code,
#                     code=mapping.code,
#                     message=mapping.message,
#                     details=exc.context,
#                 )

#             return self._error_response(
#                 status_code=400,
#                 code=ErrorCode.BAD_REQUEST,
#                 message=exc.message,
#             )

#         # unexpected exception (500)
#         logger.error(
#             "Unhandled exception",
#             error=str(exc),
#             traceback=traceback.format_exc(),
#         )

#         return self._error_response(
#             status_code=500,
#             code=ErrorCode.INTERNAL_ERROR,
#             message="Internal server error",
#         )

#     def _error_response(
#         self, status_code: int, code: ErrorCode, message: str, details=None
#     ):
#         return JSONResponse(
#             status_code=status_code,
#             content={
#                 "success": False,
#                 "error": {
#                     "code": code,
#                     "message": message,
#                     "details": details,
#                 },
#                 "meta": self._meta(),
#             },
#         )

#     def _meta(self):
#         ctx = structlog.contextvars.get_contextvars()
#         print(ctx)

#         return {
#             "requestId": ctx.get("request_id"),
#             "timestamp": datetime.now(UTC).isoformat(),
#         }

import json
from collections.abc import MutableMapping
from datetime import UTC, datetime
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

EXCLUDED_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
}


class ResponseFormatterMiddleware:
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

        path = scope.get("path", "")

        if path in EXCLUDED_PATHS:
            return await self.app(scope, receive, send)

        body_chunks = []
        status_code = 200
        headers = []

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            nonlocal status_code, headers

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = message.get("headers", [])

            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))

                if not message.get("more_body", False):
                    full_body = b"".join(body_chunks)

                    content_type = dict(headers).get(b"content-type", b"").decode()

                    # duplicate headers can break the app
                    # headers_dict = {k.lower(): v for k, v in headers}
                    # content_type = headers_dict.get(b"content-type", b"").decode()

                    # Skip non-JSON
                    if "application/json" not in content_type:
                        await send(message)
                        return

                    # Skip errors (this is what you want)
                    if status_code >= 400:
                        await send(
                            {
                                "type": "http.response.start",
                                "status": status_code,
                                "headers": headers,
                            }
                        )
                        await send(
                            {
                                "type": "http.response.body",
                                "body": full_body,
                                "more_body": False,
                            }
                        )
                        return

                    #  Only success responses get wrapped
                    try:
                        data = json.loads(full_body) if full_body else None
                    except Exception:
                        data = None

                    request_id = scope.get("state", {}).get("request_id")

                    envelope = {
                        "success": True,
                        "data": data,
                        "meta": {
                            "requestId": request_id,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }

                    new_body = json.dumps(envelope).encode()

                    await send(
                        {
                            "type": "http.response.start",
                            "status": status_code,
                            "headers": [(b"content-type", b"application/json")],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": new_body,
                            "more_body": False,
                        }
                    )

            else:
                await send(message)

        await self.app(scope, receive, send_wrapper)
