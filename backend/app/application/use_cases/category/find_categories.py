from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import (
    BaseCategoryResult,
    FindCategoriesCommand,
    FindCategoriesResult,
)
from app.domain.repositories import ICategoryRepository

from ..base import BaseUseCase


class FindCategoriesUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, category_repo: ICategoryRepository
    ) -> None:
        super().__init__(db_session)
        self._category_repo = category_repo

    @override
    async def execute(self, cmd: FindCategoriesCommand) -> FindCategoriesResult:
        categories = await self._category_repo.find_all(collection_id=cmd.collection_id)

        return FindCategoriesResult(
            categories=[
                BaseCategoryResult(
                    id=c.id,
                    collection_id=c.collection_id,
                    name=c.name,
                    url_slug=c.url_slug,
                    created_at=c.created_at,
                )
                for c in categories
            ]
        )
