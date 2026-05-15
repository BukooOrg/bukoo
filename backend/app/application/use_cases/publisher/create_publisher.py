from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.publisher_dto import (
    CreatePublisherCommand,
    CreatePublisherResult,
)
from app.domain.entities import PublisherEntity
from app.domain.repositories import IPublisherRepository

from ..base import BaseUseCase


class CreatePublisherUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, publisher_repo: IPublisherRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._publisher_repo = publisher_repo

    @override
    async def execute(self, cmd: CreatePublisherCommand) -> CreatePublisherResult:
        now = datetime.now(UTC)
        publisher = PublisherEntity(
            _id=str(uuid7()),
            _name=cmd.name,
            _website=cmd.website,
            _created_at=now,
            _updated_at=now,
        )

        await self._publisher_repo.save(publisher)
        await self._db_session.commit()

        return CreatePublisherResult(
            id=publisher.id,
            name=publisher.name,
            website=publisher.website,
            created_at=publisher.created_at,
        )
