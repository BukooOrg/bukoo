from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import SoftDeleteBookCommand, SoftDeleteBookResult
from app.domain.exceptions import (
    BookNotFoundError,
)
from app.domain.repositories import BookStatusFilter, IBookRepository

from .base import BaseBookUseCase


class SoftDeleteBookUseCase(BaseBookUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
    ) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)

    @override
    async def execute(self, cmd: SoftDeleteBookCommand) -> SoftDeleteBookResult:
        book = await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter("all"))
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        # The repository already filters deleted records by default, so this branch will only be reached if find_by_id with "all" is later widened to return deleted records — the check keeps the use case correct regardless.
        if book.is_deleted:
            raise BookNotFoundError(cmd.book_id)

        book.soft_delete()
        await self._book_repo.save(book)
        await self._db_session.commit()

        return self._to_result(book, SoftDeleteBookResult)
