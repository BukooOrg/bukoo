from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.cart_dtos import (
    UpdateCartItemQuantityCommand,
    UpdateCartItemQuantityResult,
)
from app.application.use_cases.cart.update_cart_item_quantity import (
    UpdateCartItemQuantityUseCase,
)
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.exceptions import CartItemNotFoundError, CartNotFoundError
from app.domain.repositories import ICartRepository


def _make_book(book_id: str = "book-001") -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="Test Book",
        _price=Decimal("29.99"),
        _stock_quantity=5,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_cart_item(
    item_id: str = "item-001",
    cart_id: str = "cart-001",
    book_id: str = "book-001",
    quantity: int = 2,
    book: BookEntity | None = None,
) -> CartItemEntity:
    now = datetime.now(UTC)
    return CartItemEntity(
        _id=item_id,
        _cart_id=cart_id,
        _book_id=book_id,
        _quantity=quantity,
        _created_at=now,
        _updated_at=now,
        _book=book,
    )


def _make_cart(
    user_id: str = "user-001",
    items: list[CartItemEntity] | None = None,
) -> CartEntity:
    now = datetime.now(UTC)
    return CartEntity(
        _id="cart-001",
        _user_id=user_id,
        _created_at=now,
        _updated_at=now,
        _cart_items=items or [],
    )


class FakeCartRepository(ICartRepository):
    def __init__(self, cart: CartEntity | None = None) -> None:
        self._cart = cart
        self.saved: CartEntity | None = None

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def save(self, cart: CartEntity) -> None:
        self.saved = cart


@pytest.mark.unit
class TestUpdateCartItemQuantityUseCase:
    async def test_success_returns_updated_quantity(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        item = _make_cart_item(quantity=2, book=book)
        cart = _make_cart(items=[item])
        cart_repo = FakeCartRepository(cart=cart)
        use_case = UpdateCartItemQuantityUseCase(
            db_session=db_session, cart_repo=cart_repo
        )
        cmd = UpdateCartItemQuantityCommand(
            item_id="item-001", quantity=5, user_id="user-001"
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateCartItemQuantityResult)
        assert result.quantity == 5
        assert result.id == "item-001"
        assert result.book_id == "book-001"
        assert result.book.title == "Test Book"
        db_session.commit.assert_called_once()

    async def test_raises_cart_not_found_when_user_has_no_cart(self) -> None:
        db_session = AsyncMock()
        cart_repo = FakeCartRepository(cart=None)
        use_case = UpdateCartItemQuantityUseCase(
            db_session=db_session, cart_repo=cart_repo
        )
        cmd = UpdateCartItemQuantityCommand(
            item_id="item-001", quantity=3, user_id="user-001"
        )

        with pytest.raises(CartNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_cart_item_not_found_when_item_missing(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        item = _make_cart_item(item_id="item-001", book=book)
        cart = _make_cart(items=[item])
        cart_repo = FakeCartRepository(cart=cart)
        use_case = UpdateCartItemQuantityUseCase(
            db_session=db_session, cart_repo=cart_repo
        )
        cmd = UpdateCartItemQuantityCommand(
            item_id="nonexistent-item", quantity=3, user_id="user-001"
        )

        with pytest.raises(CartItemNotFoundError):
            await use_case.execute(cmd)

    async def test_quantity_minimum_boundary_succeeds(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        item = _make_cart_item(quantity=5, book=book)
        cart = _make_cart(items=[item])
        cart_repo = FakeCartRepository(cart=cart)
        use_case = UpdateCartItemQuantityUseCase(
            db_session=db_session, cart_repo=cart_repo
        )
        cmd = UpdateCartItemQuantityCommand(
            item_id="item-001", quantity=1, user_id="user-001"
        )

        result = await use_case.execute(cmd)

        assert result.quantity == 1
