from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.cart_dtos import (
    ClearAllCartItemsCommand,
    ClearAllCartItemsResult,
)
from app.application.use_cases.cart.clear_all_cart_items import ClearAllCartItemsUseCase
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
        self.deleted_cart_id: str | None = None

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        pass

    async def delete_items_by_cart_id(self, cart_id: str) -> None:
        self.deleted_cart_id = cart_id

    async def save(self, cart: CartEntity) -> None:
        self.saved = cart


@pytest.mark.unit
class TestClearAllCartItemsUseCase:
    async def test_returns_result_with_empty_items(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        items = [
            _make_cart_item(item_id="item-001", book=book),
            _make_cart_item(item_id="item-002", book_id="book-002", book=book),
        ]
        cart = _make_cart(items=items)
        cart_repo = FakeCartRepository(cart=cart)
        use_case = ClearAllCartItemsUseCase(db_session=db_session, cart_repo=cart_repo)

        result = await use_case.execute(ClearAllCartItemsCommand(user_id="user-001"))

        assert isinstance(result, ClearAllCartItemsResult)
        assert result.id == "cart-001"
        assert result.items == []
        assert cart_repo.saved is not None
        assert cart_repo.saved.cart_items == []
        assert cart_repo.deleted_cart_id == "cart-001"
        db_session.commit.assert_called_once()

    async def test_clearing_already_empty_cart_succeeds(self) -> None:
        db_session = AsyncMock()
        cart = _make_cart(items=[])
        cart_repo = FakeCartRepository(cart=cart)
        use_case = ClearAllCartItemsUseCase(db_session=db_session, cart_repo=cart_repo)

        result = await use_case.execute(ClearAllCartItemsCommand(user_id="user-001"))

        assert isinstance(result, ClearAllCartItemsResult)
        assert result.items == []
        db_session.commit.assert_called_once()

    async def test_raises_cart_not_found_when_no_cart(self) -> None:
        db_session = AsyncMock()
        cart_repo = FakeCartRepository(cart=None)
        use_case = ClearAllCartItemsUseCase(db_session=db_session, cart_repo=cart_repo)

        with pytest.raises(CartNotFoundError):
            await use_case.execute(ClearAllCartItemsCommand(user_id="user-001"))
