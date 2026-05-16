from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import PublisherEntity
from app.domain.repositories.publisher_repository import (
    IPublisherRepository,
)
from app.infrastructure.db.mappers import PublisherMapper
from app.infrastructure.db.models import PublisherModel


class PublisherRepositoryImpl(IPublisherRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "name": PublisherModel.name,
        "created_at": PublisherModel.created_at,
        "updated_at": PublisherModel.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_all(self, query: QueryParams) -> PaginatedResult[PublisherEntity]:
        conditions: list[ColumnElement[bool]] = [PublisherModel.deleted_at.is_(None)]

        if query.search:
            conditions.append(PublisherModel.name.ilike(f"%{query.search}%"))

        where_clause = and_(*conditions)

        base_stmt = select(PublisherModel)

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
            order_clauses = [PublisherModel.created_at.asc()]

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
            items=[PublisherMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    @override
    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        stmt = (
            select(PublisherModel)
            .where(PublisherModel.id == publisher_id)
            .where(PublisherModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return PublisherMapper.to_entity(model) if model else None

    @override
    async def save(self, publisher: PublisherEntity) -> None:
        model = PublisherMapper.to_model(publisher)
        await self._session.merge(model)
