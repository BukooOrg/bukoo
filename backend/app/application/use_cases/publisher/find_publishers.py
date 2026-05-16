from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.publisher_dto import (
    BasePublisherResult,
    FindPublishersCommand,
)
from app.core.query_params import PaginatedResult
from app.domain.repositories import IPublisherRepository

from ..base import BaseUseCase


class FindPublishersUseCase(BaseUseCase):
    def __init__(
        self, db_session: AsyncSession, publisher_repo: IPublisherRepository
    ) -> None:
        super().__init__(db_session=db_session)
        self._publisher_repo = publisher_repo

    @override
    async def execute(
        self, cmd: FindPublishersCommand
    ) -> PaginatedResult[BasePublisherResult]:
        result = await self._publisher_repo.find_all(cmd.query_params)
        return PaginatedResult(
            items=[
                BasePublisherResult(
                    id=p.id, name=p.name, website=p.website, created_at=p.created_at
                )
                for p in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
