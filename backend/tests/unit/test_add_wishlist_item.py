from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.wishlist_dto import (
    AddWishlistItemCommand,
    AddWishlistItemResult,
)
from app.application.use_cases.wishlist.add_wishlist_item import AddWishlistItemUseCase
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.wishlist_entity import WishlistEntity
from app.domain.entities.wishlist_item_entity import WishlistItemEntity
from app.domain.exceptions import BookNotFoundError, WishlistItemAlreadyExistsError
from app.domain.repositories import IBookRepository, IWishlistRepository
from app.domain.repositories.book_repository import BookStatusFilter


def _make_book(book_id: str = "book-001") -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="The Name of the Wind",
        _price=Decimal("29.99"),
        _stock_quantity=10,
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


def _make_wishlist_item(wishlist_id: str, book_id: str) -> WishlistItemEntity:
    now = datetime.now(UTC)
    return WishlistItemEntity(
        _id="item-001",
        _wishlist_id=wishlist_id,
        _book_id=book_id,
        _added_at=now,
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

    async def find_by_user_id(self, user_id: str) -> WishlistEntity | None:
        if self._wishlist and self._wishlist.user_id == user_id:
            return self._wishlist
        return None

    async def delete_item_by_item_id(self, item_id: str) -> None:
        pass

    async def save(self, wishlist: WishlistEntity) -> None:
        self.saved = wishlist


@pytest.mark.unit
class TestAddWishlistItemUseCase:
    async def test_new_wishlist_new_item_returns_result(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        book_repo = FakeBookRepository(book=book)
        wishlist_repo = FakeWishlistRepository()
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="book-001", user_id="user-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, AddWishlistItemResult)
        assert result.book_id == "book-001"
        assert result.book.title == "The Name of the Wind"
        assert result.wishlist_id is not None
        db_session.commit.assert_called_once()

    async def test_existing_wishlist_new_book_returns_result(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        existing_wishlist = _make_wishlist(user_id="user-001")
        book_repo = FakeBookRepository(book=book)
        wishlist_repo = FakeWishlistRepository(wishlist=existing_wishlist)
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="book-001", user_id="user-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, AddWishlistItemResult)
        assert result.book_id == "book-001"
        assert result.wishlist_id == "wishlist-001"

    async def test_raises_book_not_found_when_book_missing(self) -> None:
        db_session = AsyncMock()
        book_repo = FakeBookRepository(book=None)
        wishlist_repo = FakeWishlistRepository()
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="nonexistent", user_id="user-001")

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_already_exists_when_book_already_in_wishlist(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        existing_item = _make_wishlist_item(
            wishlist_id="wishlist-001", book_id="book-001"
        )
        wishlist = _make_wishlist(items=[existing_item])
        book_repo = FakeBookRepository(book=book)
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="book-001", user_id="user-001")

        with pytest.raises(WishlistItemAlreadyExistsError):
            await use_case.execute(cmd)

    async def test_new_wishlist_entity_created_when_none_exists(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        book_repo = FakeBookRepository(book=book)
        wishlist_repo = FakeWishlistRepository(wishlist=None)
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="book-001", user_id="user-001")

        await use_case.execute(cmd)

        assert wishlist_repo.saved is not None
        assert wishlist_repo.saved.user_id == "user-001"
        assert wishlist_repo.saved.id != ""

    async def test_new_item_has_non_null_added_at(self) -> None:
        db_session = AsyncMock()
        book = _make_book()
        book_repo = FakeBookRepository(book=book)
        wishlist_repo = FakeWishlistRepository()
        use_case = AddWishlistItemUseCase(
            db_session=db_session, book_repo=book_repo, wishlist_repo=wishlist_repo
        )
        cmd = AddWishlistItemCommand(book_id="book-001", user_id="user-001")

        result = await use_case.execute(cmd)

        assert result.added_at is not None
