from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import (
    SoftDeleteCategoryCommand,
    SoftDeleteCategoryResult,
)
from app.domain.exceptions import CategoryNotFoundError
from app.domain.repositories import ICategoryRepository

from ..base import BaseUseCase


class SoftDeleteCategoryUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, category_repo: ICategoryRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._category_repo = category_repo

    @override
    async def execute(self, cmd: SoftDeleteCategoryCommand) -> SoftDeleteCategoryResult:
        category = await self._category_repo.find_by_id(cmd.category_id)
        if category is None:
            raise CategoryNotFoundError(cmd.category_id)

        category.soft_delete()
        await self._category_repo.nullify_book_category(category_id=cmd.category_id)
        await self._category_repo.save(category)
        await self._db_session.commit()

        return SoftDeleteCategoryResult(message="Category deleted successfully.")
