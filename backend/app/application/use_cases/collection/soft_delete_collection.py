from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.collection_dto import (
    SoftDeleteCollectionCommand,
    SoftDeleteCollectionResult,
)
from app.domain.exceptions import CollectionNotFoundError
from app.domain.repositories import ICollectionRepository

from ..base import BaseUseCase


class SoftDeleteCollectionUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, collection_repo: ICollectionRepository
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo

    async def execute(
        self, cmd: SoftDeleteCollectionCommand
    ) -> SoftDeleteCollectionResult:
        collection = await self._collection_repo.find_by_id(cmd.collection_id)

        if collection is None:
            raise CollectionNotFoundError(cmd.collection_id)

        collection.soft_delete()
        await self._collection_repo.soft_delete_with_categories(cmd.collection_id)
        await self._collection_repo.save(collection)
        await self._db_session.commit()

        return SoftDeleteCollectionResult(message="Collection deleted successfully.")
