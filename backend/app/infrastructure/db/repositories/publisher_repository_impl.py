from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import PublisherEntity
from app.domain.repositories.publisher_repository import IPublisherRepository
from app.infrastructure.db.mappers import PublisherMapper
from app.infrastructure.db.models import PublisherModel


class PublisherRepositoryImpl(IPublisherRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
