from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import ReviewEntity


@dataclass(frozen=True)
class ReviewFilters:
    book_id: str | None = None
    user_id: str | None = None
    is_hidden: bool | None = None


class IReviewRepository(ABC):
    @abstractmethod
    async def save(self, review: ReviewEntity) -> None:
        pass

    @abstractmethod
    async def find_by_id(
        self,
        review_id: str,
    ) -> ReviewEntity | None:
        pass

    @abstractmethod
    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        pass

    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        pass
