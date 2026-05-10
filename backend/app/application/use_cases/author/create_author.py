from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.author_dto import CreateAuthorCommand, CreateAuthorResult
from app.domain.entities import AuthorEntity
from app.domain.repositories import IAuthorRepository

from ..base import BaseUseCase


class CreateAuthorUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, author_repo: IAuthorRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._author_repo = author_repo

    @override
    async def execute(self, cmd: CreateAuthorCommand) -> CreateAuthorResult:
        now = datetime.now(UTC)
        author = AuthorEntity(
            _id=str(uuid7()),
            _name=cmd.name,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )

        await self._author_repo.save(author)
        await self._db_session.commit()

        return CreateAuthorResult(
            id=author.id, name=author.name, created_at=author.created_at
        )
