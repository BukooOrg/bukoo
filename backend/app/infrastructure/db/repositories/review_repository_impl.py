from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import ReviewEntity
from app.domain.repositories.review_repository import IReviewRepository, ReviewFilters
from app.infrastructure.db.mappers.review_mapper import ReviewMapper
from app.infrastructure.db.models.review_model import ReviewModel


class ReviewRepositoryImpl(IReviewRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "created_at": ReviewModel.created_at,
        "updated_at": ReviewModel.updated_at,
    }

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

    @override
    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        conditions: list[ColumnElement[bool]] = [
            ReviewModel.deleted_at.is_(None),
        ]

        if filters.book_id is not None:
            conditions.append(ReviewModel.book_id == filters.book_id)
        if filters.user_id is not None:
            conditions.append(ReviewModel.user_id == filters.user_id)

        if filters.is_hidden is True:
            conditions.append(ReviewModel.hidden_at.is_not(None))
        elif filters.is_hidden is False:
            conditions.append(ReviewModel.hidden_at.is_(None))

        where_clause = and_(*conditions)
        base_stmt = select(ReviewModel)

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(
                    base_stmt.where(where_clause).subquery()
                )
            )
        ).scalar_one()

        order_clauses = [
            self.SORTABLE_FIELDS[s.field].asc()
            if s.direction == "asc"
            else self.SORTABLE_FIELDS[s.field].desc()
            for s in query.sorts
            if s.field in self.SORTABLE_FIELDS
        ]
        if not order_clauses:
            order_clauses = [ReviewModel.created_at.desc()]

        models = (
            (
                await self._session.execute(
                    base_stmt.where(where_clause)
                    .order_by(*order_clauses)
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[ReviewMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )
