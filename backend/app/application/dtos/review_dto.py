from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# commands
@dataclass(frozen=True)
class CreateReviewCommand:
    user_id: str
    book_id: str
    order_item_id: str
    rating: int | None
    comment: str | None


@dataclass(frozen=True)
class UpdateReviewCommand:
    user_id: str
    review_id: str
    rating: int | None
    comment: str | None
    fields_to_update: frozenset[str]


@dataclass(frozen=True)
class SoftDeleteReviewCommand:
    user_id: str
    review_id: str


# results
@dataclass(frozen=True)
class CreateReviewResult:
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UpdateReviewResult:
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
