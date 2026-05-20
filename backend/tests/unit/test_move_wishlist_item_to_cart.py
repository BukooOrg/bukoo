from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.wishlist_dto import (
    MoveWishlistItemToCartCommand,
    MoveWishlistItemToCartResult,
)
from app.application.use_cases.wishlist.move_wishlist_item_to_cart import (
    MoveWishlistItemToCartUseCase,
)
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.cart_entity import CartEntity
from app.domain.entities.cart_item_entity import CartItemEntity
from app.domain.entities.wishlist_entity import WishlistEntity
from app.domain.entities.wishlist_item_entity import WishlistItemEntity
from app.domain.exceptions import (
    BookNotFoundError,
    OutOfStockError,
    WishlistItemNotFoundError,
    WishlistNotFoundError,
)
from app.domain.repositories import (
    IBookRepository,
    ICartRepository,
    IWishlistRepository,
)
from app.domain.repositories.book_repository import BookStatusFilter


def _make_book(
    book_id: str = "book-001",
    stock_quantity: int = 10,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="The Name of the Wind",
        _price=Decimal("29.99"),
        _stock_quantity=stock_quantity,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url="covers/notw.jpg",
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_wishlist_item(
    item_id: str = "item-001",
    wishlist_id: str = "wishlist-001",
    book_id: str = "book-001",
) -> WishlistItemEntity:
    now = datetime.now(UTC)
    return WishlistItemEntity(
        _id=item_id,
        _wishlist_id=wishlist_id,
        _book_id=book_id,
        _added_at=now,
        _created_at=now,
        _updated_at=now,
    )


def _make_wishlist(
    user_id: str = "user-001",
    items: list[WishlistItemEntity] | None = None,
) -> WishlistEntity:
    now = datetime.now(UTC)
    return WishlistEntity(
        _id="wishlist-001",
        _user_id=user_id,
        _created_at=now,
        _updated_at=now,
        _wishlist_items=items or [],
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


def _make_cart_item(
    cart_id: str = "cart-001",
    book_id: str = "book-001",
    quantity: int = 2,
) -> CartItemEntity:
    now = datetime.now(UTC)
    return CartItemEntity(
        _id="cart-item-001",
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


class FakeWishlistRepository(IWishlistRepository):
    def __init__(self, wishlist: WishlistEntity | None = None) -> None:
        self._wishlist = wishlist
        self.saved: WishlistEntity | None = None
        self.deleted_item_id: str | None = None

    async def find_by_user_id(self, user_id: str) -> WishlistEntity | None:
        if self._wishlist and self._wishlist.user_id == user_id:
            return self._wishlist
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        self.deleted_item_id = item_id

    async def save(self, wishlist: WishlistEntity) -> None:
        self.saved = wishlist


class FakeCartRepository(ICartRepository):
    def __init__(self, cart: CartEntity | None = None) -> None:
        self._cart = cart
        self.saved: CartEntity | None = None

    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        if self._cart and self._cart.user_id == user_id:
            return self._cart
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        raise NotImplementedError

    async def delete_items_by_cart_id(self, cart_id: str) -> None:
        raise NotImplementedError

    async def save(self, cart: CartEntity) -> None:
        self.saved = cart


def _make_use_case(
    book: BookEntity | None = None,
    wishlist: WishlistEntity | None = None,
    cart: CartEntity | None = None,
    db_session: AsyncMock | None = None,
) -> tuple[MoveWishlistItemToCartUseCase, FakeWishlistRepository, FakeCartRepository]:
    wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
    cart_repo = FakeCartRepository(cart=cart)
    book_repo = FakeBookRepository(book=book)
    use_case = MoveWishlistItemToCartUseCase(
        db_session=db_session or AsyncMock(),
        book_repo=book_repo,
        wishlist_repo=wishlist_repo,
        cart_repo=cart_repo,
    )
    return use_case, wishlist_repo, cart_repo


@pytest.mark.unit
class TestMoveWishlistItemToCartUseCase:
    async def test_returns_result_with_quantity_1_and_correct_ids_when_no_cart_exists(
        self,
    ) -> None:
        book = _make_book()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        use_case, _, cart_repo = _make_use_case(book=book, wishlist=wishlist, cart=None)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, MoveWishlistItemToCartResult)
        assert result.book_id == "book-001"
        assert result.quantity == 1
        assert result.cart_id is not None
        assert cart_repo.saved is not None

    async def test_increments_quantity_when_book_already_in_cart(self) -> None:
        book = _make_book()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        existing_cart_item = _make_cart_item(book_id="book-001", quantity=2)
        cart = _make_cart(items=[existing_cart_item])
        use_case, _, _ = _make_use_case(book=book, wishlist=wishlist, cart=cart)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        result = await use_case.execute(cmd)

        assert result.quantity == 3

    async def test_wishlist_item_is_removed_after_move(self) -> None:
        book = _make_book()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        use_case, wishlist_repo, _ = _make_use_case(book=book, wishlist=wishlist)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        await use_case.execute(cmd)

        assert wishlist_repo.deleted_item_id == "item-001"
        assert wishlist_repo.saved is not None
        assert wishlist_repo.saved.find_item_by_item_id("item-001") is None

    async def test_raises_wishlist_not_found_when_user_has_no_wishlist(self) -> None:
        use_case, _, _ = _make_use_case(wishlist=None)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        with pytest.raises(WishlistNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_wishlist_item_not_found_when_item_not_in_wishlist(
        self,
    ) -> None:
        wishlist = _make_wishlist(items=[])
        use_case, _, _ = _make_use_case(wishlist=wishlist)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="nonexistent")

        with pytest.raises(WishlistItemNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_book_not_found_when_book_is_deactivated_or_deleted(
        self,
    ) -> None:
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        use_case, _, _ = _make_use_case(book=None, wishlist=wishlist)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_out_of_stock_when_book_stock_is_zero(self) -> None:
        book = _make_book(stock_quantity=0)
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        use_case, _, _ = _make_use_case(book=book, wishlist=wishlist)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        with pytest.raises(OutOfStockError):
            await use_case.execute(cmd)

    async def test_commit_is_called_exactly_once(self) -> None:
        book = _make_book()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        db_session = AsyncMock()
        use_case, _, _ = _make_use_case(
            book=book, wishlist=wishlist, db_session=db_session
        )
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    async def test_new_cart_is_created_when_user_has_no_cart(self) -> None:
        book = _make_book()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        use_case, _, cart_repo = _make_use_case(book=book, wishlist=wishlist, cart=None)
        cmd = MoveWishlistItemToCartCommand(user_id="user-001", item_id="item-001")

        await use_case.execute(cmd)

        assert cart_repo.saved is not None
        assert cart_repo.saved.user_id == "user-001"
        assert cart_repo.saved.id != "cart-001"
