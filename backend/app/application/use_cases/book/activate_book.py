from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import ActivateBookCommand, ActivateBookResult
from app.domain.exceptions import (
    BookAlreadyActivatedError,
    BookNotFoundError,
)
from app.domain.repositories import (
    BookStatusFilter,
    IBookRepository,
)

from .base import BaseBookUseCase


class ActivateBookUseCase(BaseBookUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)

    @override
    async def execute(self, cmd: ActivateBookCommand) -> ActivateBookResult:
        book = await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter("all"))
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        if book.is_active:
            raise BookAlreadyActivatedError(cmd.book_id)

        book.activate()
        await self._book_repo.save(book)
        await self._db_session.commit()

        return self._to_result(book, ActivateBookResult)
