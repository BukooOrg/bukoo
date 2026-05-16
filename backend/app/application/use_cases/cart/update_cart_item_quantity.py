from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.cart_dtos import (
    CartItemBookResult,
    UpdateCartItemQuantityCommand,
    UpdateCartItemQuantityResult,
)
from app.application.use_cases.base import BaseUseCase
from app.domain.exceptions import CartItemNotFoundError, CartNotFoundError
from app.domain.repositories import ICartRepository


class UpdateCartItemQuantityUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cart_repo: ICartRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._cart_repo = cart_repo

    @override
    async def execute(
        self, cmd: UpdateCartItemQuantityCommand
    ) -> UpdateCartItemQuantityResult:
        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        if cart is None:
            raise CartNotFoundError(cmd.user_id)

        item = cart.find_item_by_cart_item_id(cmd.item_id)
        if item is None:
            raise CartItemNotFoundError(cmd.item_id)

        cart.update_item_quantity(item.id, cmd.quantity)
        await self._cart_repo.save(cart)
        await self._db_session.commit()

        updated_item = cart.find_item_by_cart_item_id(cmd.item_id)
        assert updated_item is not None
        assert updated_item.book is not None
        return UpdateCartItemQuantityResult(
            id=updated_item.id,
            cart_id=cart.id,
            book_id=updated_item.book_id,
            quantity=updated_item.quantity,
            book=CartItemBookResult(
                id=updated_item.book.id,
                title=updated_item.book.title,
                price=updated_item.book.price,
                cover_url=updated_item.book.cover_url,
            ),
        )
