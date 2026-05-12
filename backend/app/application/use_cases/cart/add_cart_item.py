from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.cart_dtos import (
    AddCartItemCommand,
    AddCartItemResult,
    CartItemBookResult,
)
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.exceptions import BookNotFoundError, OutOfStockError
from app.domain.repositories import IBookRepository, ICartRepository
from app.domain.repositories.book_repository import BookStatusFilter

from ..base import BaseUseCase


class AddCartItemUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        cart_repo: ICartRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo
        self._cart_repo = cart_repo

    @override
    async def execute(self, cmd: AddCartItemCommand) -> AddCartItemResult:
        book = await self._book_repo.find_by_id(
            cmd.book_id, BookStatusFilter(status="activate")
        )
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        if book.stock_quantity < 1:
            raise OutOfStockError(
                cmd.book_id, requested=cmd.quantity, available=book.stock_quantity
            )

        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        if cart is None:
            now = datetime.now(UTC)
            cart = CartEntity(
                _id=str(uuid7()),
                _user_id=cmd.user_id,
                _created_at=now,
                _updated_at=now,
                _cart_items=[],
            )

        existing = cart.find_item_by_book_id(book.id)

        if existing is None:
            now = datetime.now(UTC)
            new_item = CartItemEntity(
                _id=str(uuid7()),
                _cart_id=cart.id,
                _book_id=book.id,
                _quantity=cmd.quantity,
                _created_at=now,
                _updated_at=now,
                _book=book,
            )
            cart.append_item(new_item)
        else:
            cart.add_item(book, cmd.quantity)

        await self._cart_repo.save(cart)
        await self._db_session.commit()

        final_item = cart.find_item_by_book_id(book.id)
        assert final_item is not None

        return AddCartItemResult(
            id=final_item.id,
            cart_id=cart.id,
            book_id=final_item.book_id,
            quantity=final_item.quantity,
            book=CartItemBookResult(
                id=book.id,
                title=book.title,
                price=book.price,
                cover_url=book.cover_url,
            ),
        )
