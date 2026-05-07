from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.errors.error_codes import ErrorCode
from app.domain.exceptions.base import DomainException
from app.presentation.http.exception_mapper import EXCEPTION_MAP

from .exception_handler import build_error_response


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainException):
        # This fallback shouldn't happen if registered correctly, but satisfies types
        raise exc

    mapping = EXCEPTION_MAP.get(type(exc))

    if mapping:
        message = mapping.message

        if callable(message):
            message = message(exc)

        return build_error_response(
            request, mapping.status_code, mapping.code, message, exc.context
        )

    return build_error_response(request, 400, ErrorCode.BAD_REQUEST, exc.message, None)
