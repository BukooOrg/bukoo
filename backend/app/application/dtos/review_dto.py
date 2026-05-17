from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.query_params import QueryParams
from app.domain.repositories.review_repository import ReviewFilters


# commands
@dataclass(frozen=True)
class CreateReviewCommand:
    user_id: str
    book_id: str
    order_item_id: str
    rating: int | None
    comment: str | None


@dataclass(frozen=True)
class UpdateMyReviewCommand:
    user_id: str
    review_id: str
    rating: int | None
    comment: str | None
    fields_to_update: frozenset[str]


@dataclass(frozen=True)
class SoftDeleteMyReviewCommand:
    user_id: str
    review_id: str


@dataclass(frozen=True)
class HideOrRestoreReviewCommand:
    review_id: str
    is_hidden: bool


@dataclass(frozen=True)
class FindReviewsByAdminCommand:
    query_params: QueryParams
    filters: ReviewFilters = field(default_factory=ReviewFilters)


# results
@dataclass(frozen=True)
class BaseReviewResult:
    id: str
    book_id: str
    user_id: str | None
    order_item_id: str
    rating: int | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BaseReviewBookItem:
    id: str
    title: str
    cover_url: str | None


@dataclass(frozen=True)
class AdminReviewItem(BaseReviewResult):
    is_hidden: bool
    hidden_at: datetime | None
    book: BaseReviewBookItem


@dataclass(frozen=True)
class CreateReviewResult(BaseReviewResult):
    pass


@dataclass(frozen=True)
class UpdateMyReviewResult(BaseReviewResult):
    pass


@dataclass(frozen=True)
class HideOrRestoreReviewResult(AdminReviewItem):
    pass
