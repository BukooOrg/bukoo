from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.inventory_dtos import GetInventoryMetricsResult
from app.core.constants import LOW_STOCK_THRESHOLD
from app.domain.repositories import IBookRepository

from ..base import BaseUseCase


class GetInventoryMetricsUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo

    @override
    async def execute(self) -> GetInventoryMetricsResult:
        metrics = await self._book_repo.get_inventory_metrics(
            low_stock_threshold=LOW_STOCK_THRESHOLD
        )
        return GetInventoryMetricsResult(
            total_sku_count=metrics.total_sku_count,
            out_of_stock_count=metrics.out_of_stock_count,
            low_stock_count=metrics.low_stock_count,
            total_inventory_value=metrics.total_inventory_value,
        )
