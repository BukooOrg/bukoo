from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import BaseBookResult
from app.application.dtos.inventory_dtos import FindLowStockItemsCommand
from app.core.query_params import PaginatedResult
from app.domain.repositories import IBookRepository

from ..book.base import BaseBookUseCase


class FindLowStockItemsUseCase(BaseBookUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)

    @override
    async def execute(
        self, cmd: FindLowStockItemsCommand
    ) -> PaginatedResult[BaseBookResult]:
        result = await self._book_repo.find_low_stock(
            query=cmd.query_params, threshold=cmd.threshold
        )
        return PaginatedResult(
            items=[self._to_result(b, BaseBookResult) for b in result.items],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
