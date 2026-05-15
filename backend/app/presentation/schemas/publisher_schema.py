from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.application.dtos.publisher_dto import FindPublishersCommand
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.presentation.schemas.list_schema import ListQueryRequest


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


class FindPublishersRequest(ListQueryRequest):
    def to_command(self) -> FindPublishersCommand:
        return FindPublishersCommand(
            query_params=QueryParams(
                page=PageParams(page=self.page, page_size=self.page_size),
                sorts=parse_sort(self.sort),
                search=self.search,
            ),
        )


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


class ViewPublisherDetailResponse(BasePublisherResponse):
    pass


class CreatePublisherResponse(BasePublisherResponse):
    pass


class UpdatePublisherResponse(BasePublisherResponse):
    pass


class SoftDeletePublisherResponse(BaseModel):
    message: str
