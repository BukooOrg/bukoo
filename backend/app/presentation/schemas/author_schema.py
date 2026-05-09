from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# requests
class BaseAuthorRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be empty or whitespace.")
        return stripped


class CreateAuthorRequest(BaseAuthorRequest):
    pass


class UpdateAuthorRequest(BaseAuthorRequest):
    pass


# responses
class BaseAuthorResponse(BaseModel):
    id: str
    name: str
    created_at: datetime


class CreateAuthorResponse(BaseAuthorResponse):
    pass


class ViewAuthorDetailResponse(BaseAuthorResponse):
    pass


class UpdateAuthorResponse(BaseAuthorResponse):
    pass
