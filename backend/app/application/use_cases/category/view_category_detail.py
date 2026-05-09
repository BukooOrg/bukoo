from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import (
    ViewCategoryDetailCommand,
    ViewCategoryDetailResult,
)
from app.domain.exceptions import CategoryNotFoundError
from app.domain.repositories import ICategoryRepository

from ..base import BaseUseCase


class ViewCategoryDetailUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, category_repo: ICategoryRepository
    ) -> None:
        super().__init__(db_session)
        self._category_repo = category_repo

    @override
    async def execute(self, cmd: ViewCategoryDetailCommand) -> ViewCategoryDetailResult:
        category = await self._category_repo.find_by_id(cmd.category_id)
        if category is None:
            raise CategoryNotFoundError(cmd.category_id)

        return ViewCategoryDetailResult(
            id=category.id,
            collection_id=category.collection_id,
            name=category.name,
            url_slug=category.url_slug,
            created_at=category.created_at,
        )
