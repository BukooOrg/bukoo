from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.application.dtos.review_dto import (
    FindReviewsByAdminCommand,
    FindReviewsCommand,
)
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.domain.repositories.review_repository import ReviewFilters
from app.presentation.schemas.list_schema import ListQueryRequest


# requests
class BaseReviewRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_rating_or_comment(self) -> Self:
        if self.rating is None and self.comment is None:
            raise ValueError("At least one of 'rating' or 'comment' must be provided.")
        return self


class CreateReviewRequest(BaseReviewRequest):
    order_item_id: str


class UpdateMyReviewRequest(BaseReviewRequest):
    pass


class HideOrRestoreReviewRequest(BaseModel):
    is_hidden: bool


class ReviewListQueryRequest(ListQueryRequest):
    def to_command(self, book_id: str) -> FindReviewsCommand:
        return FindReviewsCommand(
            book_id=book_id,
            query_params=QueryParams(
                page=PageParams(page=self.page, page_size=self.page_size),
                sorts=parse_sort(self.sort),
                search=self.search,
            ),
        )


class AdminReviewListQueryRequest(ListQueryRequest):
    book_id: str | None = None
    user_id: str | None = None
    is_hidden: bool | None = None

    def to_command(self) -> FindReviewsByAdminCommand:
        return FindReviewsByAdminCommand(
            query_params=QueryParams(
                page=PageParams(page=self.page, page_size=self.page_size),
                sorts=parse_sort(self.sort),
                search=self.search,
            ),
            filters=ReviewFilters(
                book_id=self.book_id, user_id=self.user_id, is_hidden=self.is_hidden
            ),
        )


# responses
class BaseReviewResponse(BaseModel):
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class BaseReviewBookItem(BaseModel):
    id: str
    title: str
    cover_url: str | None


class BaseAdminReviewResponse(BaseReviewResponse):
    is_hidden: bool
    hidden_at: datetime | None
    book: BaseReviewBookItem


class PublicReviewItemResponse(BaseReviewResponse):
    book: BaseReviewBookItem


class CreateReviewResponse(BaseReviewResponse):
    pass


class UpdateMyReviewResponse(BaseReviewResponse):
    pass


class HideOrRestoreReviewResponse(BaseAdminReviewResponse):
    pass


class AdminReviewItemResponse(BaseAdminReviewResponse):
    pass
