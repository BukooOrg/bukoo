from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import (
    UpdateCategoryCommand,
    UpdateCategoryResult,
)
from app.domain.exceptions import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CollectionNotFoundError,
)
from app.domain.repositories import ICategoryRepository, ICollectionRepository

from ..base import BaseUseCase


class UpdateCategoryUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        category_repo: ICategoryRepository,
        collection_repo: ICollectionRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._collection_repo = collection_repo
        self._category_repo = category_repo

    @override
    async def execute(self, cmd: UpdateCategoryCommand) -> UpdateCategoryResult:
        category = await self._category_repo.find_by_id(cmd.category_id)
        if category is None:
            raise CategoryNotFoundError(cmd.category_id)

        if cmd.collection_id != category.collection_id:
            collection = await self._collection_repo.find_by_id(cmd.collection_id)
            if collection is None:
                raise CollectionNotFoundError(cmd.collection_id)

        if cmd.url_slug != category.url_slug:
            cat_by_url_slug = await self._category_repo.find_by_url_slug(cmd.url_slug)
            if cat_by_url_slug is not None and cat_by_url_slug.id != cmd.category_id:
                raise CategoryAlreadyExistsError(cmd.url_slug)

        category.update(
            collection_id=cmd.collection_id, name=cmd.name, url_slug=cmd.url_slug
        )
        await self._category_repo.save(category)
        await self._db_session.commit()

        return UpdateCategoryResult(
            id=category.id,
            collection_id=category.collection_id,
            name=category.name,
            url_slug=category.url_slug,
            created_at=category.created_at,
        )
