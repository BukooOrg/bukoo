from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.category_dto import (
    CreateCategoryCommand,
    CreateCategoryResult,
)
from app.domain.entities import CategoryEntity
from app.domain.exceptions import CategoryAlreadyExistsError, CollectionNotFoundError
from app.domain.repositories import ICategoryRepository, ICollectionRepository

from ..base import BaseUseCase


class CreateCategoryUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        category_repo: ICategoryRepository,
        collection_repo: ICollectionRepository,
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo
        self._category_repo = category_repo

    @override
    async def execute(self, cmd: CreateCategoryCommand) -> CreateCategoryResult:
        collection = await self._collection_repo.find_by_id(cmd.collection_id)
        if collection is None:
            raise CollectionNotFoundError(cmd.collection_id)

        existing = await self._category_repo.find_by_url_slug(cmd.url_slug)
        if existing is not None:
            raise CategoryAlreadyExistsError(cmd.url_slug)

        now = datetime.now(UTC)
        category = CategoryEntity(
            _id=str(uuid7()),
            _collection_id=cmd.collection_id,
            _name=cmd.name,
            _url_slug=cmd.url_slug,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )

        await self._category_repo.save(category)
        await self._db_session.commit()

        return CreateCategoryResult(
            id=category.id,
            collection_id=category.collection_id,
            name=category.name,
            url_slug=category.url_slug,
            created_at=category.created_at,
        )
