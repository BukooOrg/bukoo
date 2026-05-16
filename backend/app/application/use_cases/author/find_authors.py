from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.author_dto import BaseAuthorResult, FindAuthorsCommand
from app.core.query_params import PaginatedResult
from app.domain.repositories import IAuthorRepository

from ..base import BaseUseCase


class FindAuthorsUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, author_repo: IAuthorRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._author_repo = author_repo

    @override
    async def execute(
        self, cmd: FindAuthorsCommand
    ) -> PaginatedResult[BaseAuthorResult]:
        result = await self._author_repo.find_all(cmd.query)
        return PaginatedResult(
            items=[
                BaseAuthorResult(id=a.id, name=a.name, created_at=a.created_at)
                for a in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
