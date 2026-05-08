from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.collection_dto import (
    CreateCollectionCommand,
    CreateCollectionResult,
)
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.collection import CollectionAlreadyExistsError
from app.domain.repositories.collection_repository import ICollectionRepository

from ..base import BaseUseCase


class CreateCollectionUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        collection_repo: ICollectionRepository,
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo

    async def execute(self, cmd: CreateCollectionCommand) -> CreateCollectionResult:
        existing = await self._collection_repo.find_by_url_slug(cmd.url_slug)
        if existing is not None:
            raise CollectionAlreadyExistsError(cmd.url_slug)

        now = datetime.now(UTC)
        collection = CollectionEntity(
            _id=str(uuid7()),
            _name=cmd.name,
            _url_slug=cmd.url_slug,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )

        await self._collection_repo.save(collection)
        await self._db_session.commit()

        return CreateCollectionResult(
            id=collection.id,
            name=collection.name,
            url_slug=collection.url_slug,
            created_at=collection.created_at,
            categories=[],
        )
