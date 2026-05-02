from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.errors.error_codes import ErrorCode


def build_error_response(
    request: Request,
    status_code: int,
    code: ErrorCode,
    message: str,
    details: str | dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Example:
    ```python
    from fastapi.exceptions import RequestValidationError
    from fastapi import Request

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return build_error_response(
            request=request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
        )
    ```
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "meta": {
                "requestId": getattr(request.state, "request_id", None),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        },
    )
