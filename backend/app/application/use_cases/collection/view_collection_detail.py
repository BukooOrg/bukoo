from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import BaseCategoryResult
from app.application.dtos.collection_dto import (
    ViewCollectionDetailCommand,
    ViewCollectionDetailResult,
)
from app.domain.exceptions.collection import CollectionNotFoundError
from app.domain.repositories import ICollectionRepository

from ..base import BaseUseCase


class ViewCollectionDetailUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, collection_repo: ICollectionRepository
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo

    async def execute(
        self, cmd: ViewCollectionDetailCommand
    ) -> ViewCollectionDetailResult:
        collection = await self._collection_repo.find_by_id(cmd.collection_id)

        if collection is None:
            raise CollectionNotFoundError(cmd.collection_id)

        return ViewCollectionDetailResult(
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
