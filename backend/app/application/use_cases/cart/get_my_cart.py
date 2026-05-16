from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.cart_dtos import (
    BaseCartItemResult,
    CartItemBookResult,
    GetMyCartCommand,
    GetMyCartResult,
)
from app.application.use_cases.base import BaseUseCase
from app.domain.exceptions import CartNotFoundError
from app.domain.repositories import ICartRepository


class GetMyCartUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cart_repo: ICartRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._cart_repo = cart_repo

    @override
    async def execute(self, cmd: GetMyCartCommand) -> GetMyCartResult:
        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        if cart is None:
            raise CartNotFoundError(cmd.user_id)

        items: list[BaseCartItemResult] = []
        for item in cart.cart_items:
            book = item.book
            assert book is not None
            items.append(
                BaseCartItemResult(
                    id=item.id,
                    cart_id=cart.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    book=CartItemBookResult(
                        id=book.id,
                        title=book.title,
                        price=book.price,
                        cover_url=book.cover_url,
                    ),
                )
            )
        return GetMyCartResult(id=cart.id, items=items)
