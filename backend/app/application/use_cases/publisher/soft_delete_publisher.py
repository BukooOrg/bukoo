from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.publisher_dto import (
    SoftDeletePublisherCommand,
    SoftDeletePublisherResult,
)
from app.domain.exceptions import PublisherNotFoundError
from app.domain.repositories import IPublisherRepository

from ..base import BaseUseCase


class SoftDeletePublisherUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, publisher_repo: IPublisherRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._publisher_repo = publisher_repo

    @override
    async def execute(
        self, cmd: SoftDeletePublisherCommand
    ) -> SoftDeletePublisherResult:
        publisher = await self._publisher_repo.find_by_id(cmd.publisher_id)
        if publisher is None:
            raise PublisherNotFoundError(cmd.publisher_id)

        publisher.soft_delete()
        await self._publisher_repo.save(publisher)
        await self._db_session.commit()

        return SoftDeletePublisherResult(message="Publisher deleted successfully.")
