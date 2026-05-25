from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.order_dto import (
    BaseOrderItemResult,
    ViewOrderDetailCommand,
    ViewOrderDetailResult,
)
from app.application.dtos.payment_dto import PaymentSummaryResult
from app.core.constants import UserRole
from app.domain.exceptions import (
    OrderAccessDeniedError,
    OrderNotFoundError,
)
from app.domain.repositories import (
    IOrderRepository,
)

from ..base import BaseUseCase


class ViewOrderDetailUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        order_repo: IOrderRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._order_repo = order_repo

    @override
    async def execute(self, cmd: ViewOrderDetailCommand) -> ViewOrderDetailResult:
        order = await self._order_repo.find_by_id(cmd.order_id)
        if order is None:
            raise OrderNotFoundError(cmd.order_id)

        assert order.user_id is not None
        if cmd.user_role == UserRole.USER and order.user_id != cmd.user_id:
            raise OrderAccessDeniedError()

        latest_payment = order.latest_payment
        items: list[BaseOrderItemResult] = []
        for order_item in order.order_items:
            assert order_item.book_id is not None
            items.append(
                BaseOrderItemResult(
                    id=order_item.id,
                    book_id=order_item.book_id,
                    book_title=order_item.book_title,
                    book_cover_url=order_item.book.cover_url
                    if order_item.book
                    else None,
                    unit_price=order_item.unit_price,
                    quantity=order_item.quantity,
                    line_total=order_item.line_total,
                )
            )
        payment: PaymentSummaryResult | None = None
        if latest_payment is not None:
            payment = PaymentSummaryResult(
                id=latest_payment.id,
                method=latest_payment.method,
                amount=latest_payment.amount,
                status=latest_payment.status,
                simulated_ref=latest_payment.simulated_ref,
                created_at=latest_payment.created_at,
            )

        return ViewOrderDetailResult(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            total=order.total,
            address_snapshot=order.address_snapshot,
            items=items,
            payment=payment,
            created_at=order.created_at,
            updated_at=order._updated_at,
        )
