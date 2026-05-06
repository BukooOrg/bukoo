from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataType = TypeVar("DataType")


class ResponseMeta(BaseModel):
    request_id: str = Field(alias="requestId")
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)


class ResponseWrapper[DataType](BaseModel):
    success: bool
    data: DataType
    meta: ResponseMeta


class ValidationErrorDetail(BaseModel):
    """One field-level validation failure (from RequestValidationError)."""

    field: str
    message: str
    code: str


class ErrorBody(BaseModel):
    """The error object nested inside every 4xx/5xx envelope."""

    code: str
    message: str
    # domain errors: None | str | dict; validation errors: list[ValidationErrorDetail]
    details: Any = None


class ErrorResponse(BaseModel):
    """Full error envelope produced by exception handlers."""

    success: bool = False
    error: ErrorBody
    meta: ResponseMeta
