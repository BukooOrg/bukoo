from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.order_dto import FindOrdersCommand, OrderSummaryResult
from app.core.query_params import PaginatedResult
from app.domain.repositories import IOrderRepository

from ..base import BaseUseCase


class FindOrdersUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        order_repo: IOrderRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._order_repo = order_repo

    @override
    async def execute(
        self, cmd: FindOrdersCommand
    ) -> PaginatedResult[OrderSummaryResult]:
        result = await self._order_repo.find_all(cmd.query_params, cmd.filters)
        return PaginatedResult(
            items=[
                OrderSummaryResult(
                    id=order.id,
                    user_id=order.user_id,
                    status=order.status,
                    total=order.total,
                    item_count=len(order.order_items),
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                )
                for order in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
