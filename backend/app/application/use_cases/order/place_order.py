from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.order_dto import (
    BaseOrderItemResult,
    PlaceOrderCommand,
    PlaceOrderResult,
)
from app.core.constants import EAST_MALAYSIA_STATES, OrderStatus
from app.domain.entities import BookEntity, CartItemEntity, OrderEntity, OrderItemEntity
from app.domain.exceptions import (
    AddressNotFoundError,
    BookNotFoundError,
    CartItemNotFoundError,
    CartNotFoundError,
    OutOfStockError,
)
from app.domain.repositories import (
    IAddressRepository,
    IBookRepository,
    ICartRepository,
    IOrderRepository,
)
from app.domain.repositories.book_repository import BookStatusFilter

from ..base import BaseUseCase


class PlaceOrderUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cart_repo: ICartRepository,
        book_repo: IBookRepository,
        address_repo: IAddressRepository,
        order_repo: IOrderRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._cart_repo = cart_repo
        self._book_repo = book_repo
        self._address_repo = address_repo
        self._order_repo = order_repo

    @override
    async def execute(self, cmd: PlaceOrderCommand) -> PlaceOrderResult:
        cart = await self._cart_repo.find_by_user_id(cmd.user_id)
        if cart is None:
            raise CartNotFoundError(cmd.user_id)

        # edge case: remove duplicate cart items
        cart_item_ids = list(set(cmd.cart_item_ids))
        selected_items: list[tuple[CartItemEntity, BookEntity]] = []
        for item_id in cart_item_ids:
            item = cart.find_item_by_cart_item_id(item_id)
            if item is None:
                raise CartItemNotFoundError(item_id)

            book = await self._book_repo.find_by_id(
                item.book_id, BookStatusFilter("activate")
            )
            if book is None:
                raise BookNotFoundError(item.book_id)
            if book.stock_quantity < item.quantity:
                raise OutOfStockError(book.id, item.quantity, book.stock_quantity)

            item.set_book(book)
            selected_items.append((item, book))

        address = await self._address_repo.find_address_by_user_id(cmd.user_id)
        if address is None:
            raise AddressNotFoundError(cmd.user_id)

        shipping_cost = Decimal("5.00")
        if address.state.strip().lower() in EAST_MALAYSIA_STATES:
            shipping_cost = Decimal("10.00")

        now = datetime.now(UTC)
        order = OrderEntity(
            _id=str(uuid7()),
            _user_id=cmd.user_id,
            _address_snapshot=address.to_snapshot(),
            _subtotal=Decimal("0"),
            _shipping_cost=shipping_cost,
            _total=shipping_cost,
            _status=OrderStatus.PENDING,
            _created_at=now,
            _updated_at=now,
        )

        for item, book in selected_items:
            order_item = OrderItemEntity(
                _id=str(uuid7()),
                _order_id=order.id,
                _book_id=book.id,
                _book_title=book.title,
                _unit_price=book.price,
                _quantity=item.quantity,
                _line_total=book.price * item.quantity,
                _created_at=now,
                _updated_at=now,
            )
            order.add_order_item(order_item)
            book.decrease_stock(item.quantity)
            await self._book_repo.save(book)
            await self._cart_repo.delete_item_by_item_id(item.id)

        await self._order_repo.save(order, False)
        await self._db_session.commit()

        item_results: list[BaseOrderItemResult] = []
        for order_item in order.order_items:
            assert order_item.book_id is not None
            item_results.append(
                BaseOrderItemResult(
                    id=order_item.id,
                    book_id=order_item.book_id,
                    book_title=order_item.book_title,
                    unit_price=order_item.unit_price,
                    quantity=order_item.quantity,
                    line_total=order_item.line_total,
                )
            )
        return PlaceOrderResult(
            id=order.id,
            status=order.status,
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            total=order.total,
            address_snapshot=order.address_snapshot,
            items=item_results,
            created_at=order.created_at,
        )
