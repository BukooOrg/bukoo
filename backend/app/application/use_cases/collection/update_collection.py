from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import BaseCategoryResult
from app.application.dtos.collection_dto import (
    UpdateCollectionCommand,
    UpdateCollectionResult,
)
from app.domain.exceptions import CollectionAlreadyExistsError, CollectionNotFoundError
from app.domain.repositories import ICollectionRepository

from ..base import BaseUseCase


class UpdateCollectionUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, collection_repo: ICollectionRepository
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo

    @override
    async def execute(self, cmd: UpdateCollectionCommand) -> UpdateCollectionResult:
        collection = await self._collection_repo.find_by_id(cmd.collection_id)

        if collection is None:
            raise CollectionNotFoundError(cmd.collection_id)

        if cmd.url_slug != collection.url_slug:
            collection_by_url_slug = await self._collection_repo.find_by_url_slug(
                cmd.url_slug
            )
            if (
                collection_by_url_slug is not None
                and collection_by_url_slug.id != cmd.collection_id
            ):
                raise CollectionAlreadyExistsError(cmd.url_slug)

        collection.update(name=cmd.name, url_slug=cmd.url_slug)
        await self._collection_repo.save(collection)
        await self._db_session.commit()

        return UpdateCollectionResult(
            id=collection.id,
            name=collection.name,
            url_slug=collection.url_slug,
            created_at=collection.created_at,
            categories=[
                BaseCategoryResult(
                    id=cat.id,
                    collection_id=cat.collection_id,
                    name=cat.name,
                    url_slug=cat.url_slug,
                    created_at=cat.created_at,
                )
                for cat in collection.categories
            ],
        )
