from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator


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


# responses
class CreateReviewResponse(BaseModel):
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class UpdateMyReviewResponse(BaseModel):
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
