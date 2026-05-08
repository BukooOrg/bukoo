from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.collection_entity import CollectionEntity
from app.domain.repositories.collection_repository import ICollectionRepository
from app.infrastructure.db.mappers.collection_mapper import CollectionMapper
from app.infrastructure.db.models.collection_model import CollectionModel


class CollectionRepositoryImpl(ICollectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        stmt = (
            select(CollectionModel)
            .where(CollectionModel.url_slug == url_slug)
            .where(CollectionModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CollectionMapper.to_entity(model) if model else None

    @override
    async def find_all(self) -> list[CollectionEntity]:
        stmt = select(CollectionModel).where(CollectionModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [CollectionMapper.to_entity(m) for m in models]

    @override
    async def save(self, collection: CollectionEntity) -> None:
        model = CollectionMapper.to_model(collection)
        await self._session.merge(model)
