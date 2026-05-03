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


# todo: make sure this can handle set-cookie well
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

                # only construct the response envelope when the full body is received
                # if the last body chunk is received, the condition become true
                if not message.get("more_body", False):
                    full_body = b"".join(body_chunks)

                    # duplicate headers can break the app
                    headers_dict = {k.lower(): v for k, v in headers}
                    content_type = headers_dict.get(b"content-type", b"").decode()

                    # skip non-JSON
                    if "application/json" not in content_type:
                        await send(message)
                        return

                    # skip errors
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

                    # only success responses get wrapped
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

                    existing_headers = list(headers)

                    # duplicate headers can break the app
                    headers_dict = {k.lower(): v for k, v in existing_headers}

                    # ensure correct content-type
                    headers_dict.pop(b"content-length", None)
                    headers_dict[b"content-type"] = b"application/json"

                    final_headers = list(headers_dict.items())

                    await send(
                        {
                            "type": "http.response.start",
                            "status": status_code,
                            "headers": final_headers,
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
