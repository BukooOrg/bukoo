from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import (
    ViewBookDetailCommand,
    ViewBookDetailResult,
)
from app.domain.exceptions import BookNotFoundError
from app.domain.repositories import IBookRepository

from .base import BaseBookUseCase


class ViewBookDetailUseCase(BaseBookUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)

    @override
    async def execute(self, cmd: ViewBookDetailCommand) -> ViewBookDetailResult:
        book = await self._book_repo.find_by_id(cmd.book_id, cmd.filters)
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        return self._to_result(book, ViewBookDetailResult)
