from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.cart_dtos import (
    ClearAllCartItemsCommand,
    ClearAllCartItemsResult,
)
from app.domain.exceptions import CartNotFoundError
from app.domain.repositories import ICartRepository

from ..base import BaseUseCase


class ClearAllCartItemsUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cart_repo: ICartRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._cart_repo = cart_repo

    @override
    async def execute(self, cmd: ClearAllCartItemsCommand) -> ClearAllCartItemsResult:
        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        if cart is None:
            raise CartNotFoundError(cmd.user_id)

        cart.clear()
        await self._cart_repo.delete_items_by_cart_id(cart.id)
        await self._cart_repo.save(cart)
        await self._db_session.commit()

        return ClearAllCartItemsResult(id=cart.id, items=cart.cart_items)
