from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.cart_dtos import RemoveCartItemCommand
from app.application.use_cases.base import BaseUseCase
from app.domain.exceptions import CartItemNotFoundError, CartNotFoundError
from app.domain.repositories import ICartRepository


class RemoveCartItemUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cart_repo: ICartRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._cart_repo = cart_repo

    @override
    async def execute(self, cmd: RemoveCartItemCommand) -> None:
        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        print(f"user id: {cmd.user_id}")
        print(cart)

        if cart is None:
            raise CartNotFoundError(cmd.user_id)

        item = cart.find_item_by_cart_item_id(cmd.item_id)
        if item is None:
            raise CartItemNotFoundError(cmd.item_id)

        cart.remove_item(cmd.item_id)
        await self._cart_repo.delete_item_by_item_id(cmd.item_id)
        await self._cart_repo.save(cart)
        await self._db_session.commit()
