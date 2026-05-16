from __future__ import annotations

from typing import override

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import OrderStatus
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import OrderEntity
from app.domain.entities.order_item_entity import OrderItemEntity
from app.domain.repositories import IOrderRepository
from app.domain.repositories.order_repository import OrderFilters
from app.infrastructure.db.mappers import OrderItemMapper, OrderMapper
from app.infrastructure.db.models import OrderModel
from app.infrastructure.db.models.order_item_model import OrderItemModel


class OrderRepositoryImpl(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return OrderMapper.to_entity(model) if model else None

    @override
    async def find_all(
        self, query: QueryParams, filters: OrderFilters
    ) -> PaginatedResult[OrderEntity]:
        stmt = select(OrderModel)

        if filters.user_id is not None:
            stmt = stmt.where(OrderModel.user_id == filters.user_id)
        if filters.status is not None:
            stmt = stmt.where(OrderModel.status == filters.status)
        if filters.date_from is not None:
            stmt = stmt.where(cast(OrderModel.created_at, Date) >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(cast(OrderModel.created_at, Date) <= filters.date_to)

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()

        models = (
            (
                await self._session.execute(
                    stmt.order_by(OrderModel.updated_at.desc())
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[OrderMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    @override
    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        existing = await self._session.get(OrderModel, order.id)

        if existing is None:
            order_model = OrderMapper.to_model(order)
            self._session.add(order_model)
        else:
            existing.status = order.status
            existing.updated_at = order.updated_at

        if not should_skip_items:
            for item in order.order_items:
                item_model = OrderItemMapper.to_model(item)
                await self._session.merge(item_model)

    @override
    async def find_delivered_order_item(
        self, user_id: str, order_item_id: str, book_id: str
    ) -> OrderItemEntity | None:
        stmt = (
            select(OrderItemModel)
            .join(OrderModel, OrderItemModel.order_id == OrderModel.id)
            .where(OrderModel.user_id == user_id)
            .where(OrderModel.status == OrderStatus.DELIVERED)
            .where(OrderItemModel.id == order_item_id)
            .where(OrderItemModel.book_id == book_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return OrderItemMapper.to_entity(model) if model else None
