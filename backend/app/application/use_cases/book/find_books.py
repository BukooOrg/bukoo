from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import (
    BaseBookResult,
    FindBooksCommand,
)
from app.core.query_params import PaginatedResult
from app.domain.repositories import IBookRepository

from .base import BaseBookUseCase


class FindBooksUseCase(BaseBookUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)

    @override
    async def execute(self, cmd: FindBooksCommand) -> PaginatedResult[BaseBookResult]:
        result = await self._book_repo.find_all(cmd.query_params, cmd.filters)
        return PaginatedResult(
            items=[self._to_result(b, BaseBookResult) for b in result.items],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
