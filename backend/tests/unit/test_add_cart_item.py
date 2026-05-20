from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.cart_dtos import AddCartItemCommand, AddCartItemResult
from app.application.use_cases.cart.add_cart_item import AddCartItemUseCase
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.exceptions import BookNotFoundError, OutOfStockError
from app.domain.repositories import IBookRepository, ICartRepository
from app.domain.repositories.book_repository import BookStatusFilter


def _make_book(
    book_id: str = "book-001",
    stock_quantity: int = 5,
    deactivated_at: datetime | None = None,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="Test Book",
        _price=Decimal("29.99"),
        _stock_quantity=stock_quantity,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=deactivated_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_cart(
    user_id: str = "user-001", items: list[CartItemEntity] | None = None
) -> CartEntity:
    now = datetime.now(UTC)
    return CartEntity(
        _id="cart-001",
        _user_id=user_id,
        _created_at=now,
        _updated_at=now,
        _cart_items=items or [],
    )


def _make_cart_item(cart_id: str, book_id: str, quantity: int) -> CartItemEntity:
    now = datetime.now(UTC)
    return CartItemEntity(
        _id="item-001",
        _cart_id=cart_id,
        _book_id=book_id,
        _quantity=quantity,
        _created_at=now,
        _updated_at=now,
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._book = book

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        if self._book and self._book.id == book_id:
            if filters.status == "activate" and self._book.deactivated_at is not None:
                return None
            return self._book
        return None

    async def find_all(self, query: object, filters: object) -> object:  # type: ignore[override]
        raise NotImplementedError

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        raise NotImplementedError

    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = True
    ) -> None:
        raise NotImplementedError

    async def get_inventory_metrics(self, low_stock_threshold: int) -> Any:
        pass

    async def find_low_stock(
        self, query: QueryParams, threshold: int
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)


class FakeCartRepository(ICartRepository):
    def __init__(self, cart: CartEntity | None = None) -> None:
        self._cart = cart
        self.saved: CartEntity | None = None

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        pass

    async def delete_items_by_cart_id(self, cart_id: str) -> None:
        pass

    async def save(self, cart: CartEntity) -> None:
        self.saved = cart


@pytest.mark.unit
class TestAddCartItemUseCase:
    async def test_new_cart_new_item_returns_result(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        book_repo = FakeBookRepository(book=book)
        cart_repo = FakeCartRepository()
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="book-001", quantity=2, user_id="user-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, AddCartItemResult)
        assert result.quantity == 2
        assert result.book_id == "book-001"
        assert result.book.title == "Test Book"
        db_session.commit.assert_called_once()

    async def test_existing_cart_duplicate_book_increments_quantity(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        existing_item = _make_cart_item(
            cart_id="cart-001", book_id="book-001", quantity=3
        )
        existing_item._book = book
        cart = _make_cart(items=[existing_item])
        book_repo = FakeBookRepository(book=book)
        cart_repo = FakeCartRepository(cart=cart)
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="book-001", quantity=2, user_id="user-001")

        result = await use_case.execute(cmd)

        assert result.quantity == 5

    async def test_raises_book_not_found_when_book_missing(self) -> None:
        db_session = AsyncMock()
        book_repo = FakeBookRepository(book=None)
        cart_repo = FakeCartRepository()
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="nonexistent", quantity=1, user_id="user-001")

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_out_of_stock_when_stock_zero(self) -> None:
        db_session = AsyncMock()
        book = _make_book(stock_quantity=0)
        book_repo = FakeBookRepository(book=book)
        cart_repo = FakeCartRepository()
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="book-001", quantity=1, user_id="user-001")

        with pytest.raises(OutOfStockError):
            await use_case.execute(cmd)

    async def test_cart_auto_created_when_user_has_no_cart(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        book_repo = FakeBookRepository(book=book)
        cart_repo = FakeCartRepository(cart=None)
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="book-001", quantity=1, user_id="user-001")

        await use_case.execute(cmd)

        assert cart_repo.saved is not None
        assert cart_repo.saved.user_id == "user-001"

    async def test_adding_to_existing_cart_only_modifies_targeted_item(self) -> None:
        db_session = AsyncMock()
        book_a = _make_book(book_id="book-001")
        book_b = _make_book(book_id="book-002")
        item_b = _make_cart_item(cart_id="cart-001", book_id="book-002", quantity=4)
        item_b._book = book_b
        cart = _make_cart(items=[item_b])
        book_repo = FakeBookRepository(book=book_a)
        cart_repo = FakeCartRepository(cart=cart)
        use_case = AddCartItemUseCase(
            db_session=db_session, book_repo=book_repo, cart_repo=cart_repo
        )
        cmd = AddCartItemCommand(book_id="book-001", quantity=1, user_id="user-001")

        result = await use_case.execute(cmd)

        assert result.book_id == "book-001"
        assert result.quantity == 1
        assert cart_repo.saved is not None
        # book-002 line is untouched
        other_item = next(
            i for i in cart_repo.saved.cart_items if i.book_id == "book-002"
        )  # type: ignore[union-attr]
        assert other_item.quantity == 4
