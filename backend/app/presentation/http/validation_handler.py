"""
Special response envelope for pydantic schema validation.
Other response envelopes are handled by ResponseFormatterMiddleware in backend/app/presentation/middlewares/response_formatter_middleware.py.
"""

from datetime import UTC, datetime

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.application.errors.error_codes import ErrorCode


def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ValidationError | RequestValidationError):
        raise exc

    request_id = getattr(request.state, "request_id", None)

    details = [
        {
            "field": ".".join(map(str, err["loc"][1:])),
            "message": err["msg"],
            "code": err["type"],
        }
        for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Request validation failed",
                "details": details,
            },
            "meta": {
                "requestId": request_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        },
    )
