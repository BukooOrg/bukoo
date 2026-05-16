from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.author_dto import (
    ViewAuthorDetailCommand,
    ViewAuthorDetailResult,
)
from app.domain.exceptions import AuthorNotFoundError
from app.domain.repositories import IAuthorRepository

from ..base import BaseUseCase


class ViewAuthorDetailUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, author_repo: IAuthorRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._author_repo = author_repo

    @override
    async def execute(self, cmd: ViewAuthorDetailCommand) -> ViewAuthorDetailResult:
        author = await self._author_repo.find_by_id(cmd.author_id)
        if author is None:
            raise AuthorNotFoundError(cmd.author_id)

        return ViewAuthorDetailResult(
            id=author.id, name=author.name, created_at=author.created_at
        )
