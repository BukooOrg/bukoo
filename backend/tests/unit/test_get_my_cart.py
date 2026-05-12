from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.cart_dtos import GetMyCartCommand, GetMyCartResult
from app.application.use_cases.cart.get_my_cart import GetMyCartUseCase
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.exceptions import CartNotFoundError
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
    cart_id: str = "cart-001",
    book_id: str = "book-001",
    quantity: int = 2,
) -> CartItemEntity:
    now = datetime.now(UTC)
    return CartItemEntity(
        _id="item-001",
        _cart_id=cart_id,
        _book_id=book_id,
        _quantity=quantity,
        _created_at=now,
        _updated_at=now,
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

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def save(self, cart: CartEntity) -> None:
        pass


@pytest.mark.unit
class TestGetMyCartUseCase:
    async def test_returns_cart_with_items(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        item = _make_cart_item()
        item._book = book
        cart = _make_cart(items=[item])
        use_case = GetMyCartUseCase(
            db_session=db_session, cart_repo=FakeCartRepository(cart=cart)
        )

        result = await use_case.execute(GetMyCartCommand(user_id="user-001"))

        assert isinstance(result, GetMyCartResult)
        assert result.id == "cart-001"
        assert len(result.items) == 1
        assert result.items[0].book_id == "book-001"
        assert result.items[0].quantity == 2
        assert result.items[0].book.title == "Test Book"
        assert result.items[0].book.price == Decimal("29.99")
        db_session.commit.assert_not_called()

    async def test_returns_cart_with_empty_items(self) -> None:
        db_session = AsyncMock()
        cart = _make_cart(items=[])
        use_case = GetMyCartUseCase(
            db_session=db_session, cart_repo=FakeCartRepository(cart=cart)
        )

        result = await use_case.execute(GetMyCartCommand(user_id="user-001"))

        assert isinstance(result, GetMyCartResult)
        assert result.id == "cart-001"
        assert result.items == []

    async def test_raises_cart_not_found_when_no_cart(self) -> None:
        db_session = AsyncMock()
        use_case = GetMyCartUseCase(
            db_session=db_session, cart_repo=FakeCartRepository(cart=None)
        )

        with pytest.raises(CartNotFoundError):
            await use_case.execute(GetMyCartCommand(user_id="user-001"))
