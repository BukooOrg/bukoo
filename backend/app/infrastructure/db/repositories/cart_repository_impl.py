from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import CartEntity
from app.domain.repositories import ICartRepository
from app.infrastructure.db.mappers.cart_item_mapper import CartItemMapper
from app.infrastructure.db.mappers.cart_mapper import CartMapper
from app.infrastructure.db.models.cart_model import CartModel


class CartRepositoryImpl(ICartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        stmt = select(CartModel).where(CartModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CartMapper.to_entity(model) if model else None

    @override
    async def save(self, cart: CartEntity) -> None:
        existing = await self._session.get(CartModel, cart.id)

        if existing is None:
            cart_model = CartMapper.to_model(cart)
            self._session.add(cart_model)
        else:
            existing.updated_at = cart.updated_at

        for item in cart.cart_items:
            item_model = CartItemMapper.to_model(item)
            await self._session.merge(item_model)
