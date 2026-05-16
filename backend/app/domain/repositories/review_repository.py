from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import ReviewEntity


class IReviewRepository(ABC):
    @abstractmethod
    async def save(self, review: ReviewEntity) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        pass

    @abstractmethod
    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        pass
