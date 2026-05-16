from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ReviewEntity
from app.domain.repositories.review_repository import IReviewRepository
from app.infrastructure.db.mappers.review_mapper import ReviewMapper
from app.infrastructure.db.models.review_model import ReviewModel


class ReviewRepositoryImpl(IReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, review: ReviewEntity) -> None:
        model = ReviewMapper.to_model(review)
        await self._session.merge(model)

    @override
    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        stmt = (
            select(ReviewModel)
            .where(ReviewModel.id == review_id)
            .where(ReviewModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ReviewMapper.to_entity(model) if model else None

    @override
    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        stmt = select(ReviewModel).where(ReviewModel.order_item_id == order_item_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ReviewMapper.to_entity(model) if model else None
