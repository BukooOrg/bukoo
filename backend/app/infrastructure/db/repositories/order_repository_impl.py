from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import OrderEntity
from app.domain.repositories import IOrderRepository
from app.infrastructure.db.mappers import OrderItemMapper, OrderMapper
from app.infrastructure.db.models import OrderModel


class OrderRepositoryImpl(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, order: OrderEntity) -> None:
        existing = await self._session.get(OrderModel, order.id)

        if existing is None:
            order_model = OrderMapper.to_model(order)
            self._session.add(order_model)
        else:
            existing.updated_at = order.updated_at

        for item in order.order_items:
            item_model = OrderItemMapper.to_model(item)
            await self._session.merge(item_model)
