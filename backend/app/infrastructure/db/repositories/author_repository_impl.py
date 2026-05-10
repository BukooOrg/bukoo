from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import AuthorEntity
from app.domain.repositories import IAuthorRepository
from app.infrastructure.db.mappers import AuthorMapper
from app.infrastructure.db.models import AuthorModel


class AuthorRepositoryImpl(IAuthorRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "name": AuthorModel.name,
        "created_at": AuthorModel.created_at,
        "updated_at": AuthorModel.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_all(self, query: QueryParams) -> PaginatedResult[AuthorEntity]:
        base_filter = AuthorModel.deleted_at.is_(None)

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(AuthorModel).where(base_filter)
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
            order_clauses = [AuthorModel.created_at.desc()]

        models = (
            (
                await self._session.execute(
                    select(AuthorModel)
                    .where(base_filter)
                    .order_by(*order_clauses)
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[AuthorMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    @override
    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        stmt = (
            select(AuthorModel)
            .where(AuthorModel.id == author_id)
            .where(AuthorModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AuthorMapper.to_entity(model) if model else None

    @override
    async def save(self, author: AuthorEntity) -> None:
        model = AuthorMapper.to_model(author)
        await self._session.merge(model)
