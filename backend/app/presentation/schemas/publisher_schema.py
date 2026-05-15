from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# requests
class BasePublisherRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    website: str | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be empty or whitespace.")
        return stripped


class CreatePublisherRequest(BasePublisherRequest):
    pass


class UpdatePublisherRequest(BasePublisherRequest):
    pass


# responses
class BasePublisherResponse(BaseModel):
    id: str
    name: str
    website: str | None
    created_at: datetime


class CreatePublisherResponse(BasePublisherResponse):
    pass


class UpdatePublisherResponse(BasePublisherResponse):
    pass


class SoftDeletePublisherResponse(BaseModel):
    message: str
