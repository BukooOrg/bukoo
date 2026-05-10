from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AuthorEntity
from app.domain.repositories import IAuthorRepository
from app.infrastructure.db.mappers import AuthorMapper
from app.infrastructure.db.models import AuthorModel


class AuthorRepositoryImpl(IAuthorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
