from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import UploadBookCoverCommand, UploadBookCoverResult
from app.application.interfaces.storage_service import IStorageService
from app.domain.exceptions import BookNotFoundError
from app.domain.repositories import BookStatusFilter, IBookRepository

from .base import BaseBookUseCase


class UploadBookCoverUseCase(BaseBookUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        storage_svc: IStorageService,
    ) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)
        self._storage_svc = storage_svc

    @override
    async def execute(self, cmd: UploadBookCoverCommand) -> UploadBookCoverResult:
        book = await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter("all"))
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        # todo: refactor public and private bucket
        # add a @classmethod for IStorageService that decide whether the object is public or private
        key = f"pub/covers/{cmd.book_id}"
        await self._storage_svc.upload(key, cmd.file_data, cmd.content_type)

        book.set_cover_url(key)
        await self._book_repo.save(book)
        await self._db_session.commit()

        return self._to_result(book, UploadBookCoverResult)
