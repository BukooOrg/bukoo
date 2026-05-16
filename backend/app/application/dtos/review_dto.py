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
