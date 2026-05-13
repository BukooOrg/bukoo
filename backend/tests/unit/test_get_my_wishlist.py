from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.wishlist_dto import (
    GetMyWishlistCommand,
    GetMyWishlistResult,
)
from app.application.use_cases.wishlist.get_my_wishlist import GetMyWishlistUseCase
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.wishlist_entity import WishlistEntity
from app.domain.entities.wishlist_item_entity import WishlistItemEntity
from app.domain.exceptions import WishlistNotFoundError
from app.domain.repositories import IWishlistRepository


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


def _make_wishlist_item(
    wishlist_id: str = "wishlist-001",
    book_id: str = "book-001",
    item_id: str = "item-001",
    book: BookEntity | None = None,
) -> WishlistItemEntity:
    now = datetime.now(UTC)
    item = WishlistItemEntity(
        _id=item_id,
        _wishlist_id=wishlist_id,
        _book_id=book_id,
        _added_at=now,
        _created_at=now,
        _updated_at=now,
    )
    if book is not None:
        item.set_book(book)
    return item


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


class FakeWishlistRepository(IWishlistRepository):
    def __init__(self, wishlist: WishlistEntity | None = None) -> None:
        self._wishlist = wishlist

    async def find_by_user_id(self, user_id: str) -> WishlistEntity | None:
        if self._wishlist and self._wishlist.user_id == user_id:
            return self._wishlist
        return None

    async def save(self, wishlist: WishlistEntity) -> None:
        pass


@pytest.mark.unit
class TestGetMyWishlistUseCase:
    async def test_returns_result_with_populated_items(self) -> None:
        book = _make_book()
        item = _make_wishlist_item(book=book)
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = GetMyWishlistUseCase(
            db_session=AsyncMock(), wishlist_repo=wishlist_repo
        )
        cmd = GetMyWishlistCommand(user_id="user-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, GetMyWishlistResult)
        assert result.id == "wishlist-001"
        assert len(result.items) == 1
        assert result.items[0].book_id == "book-001"

    async def test_returns_result_with_empty_items_when_wishlist_has_no_items(
        self,
    ) -> None:
        wishlist = _make_wishlist(items=[])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = GetMyWishlistUseCase(
            db_session=AsyncMock(), wishlist_repo=wishlist_repo
        )
        cmd = GetMyWishlistCommand(user_id="user-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, GetMyWishlistResult)
        assert result.items == []

    async def test_raises_wishlist_not_found_when_repo_returns_none(self) -> None:
        wishlist_repo = FakeWishlistRepository(wishlist=None)
        use_case = GetMyWishlistUseCase(
            db_session=AsyncMock(), wishlist_repo=wishlist_repo
        )
        cmd = GetMyWishlistCommand(user_id="user-001")

        with pytest.raises(WishlistNotFoundError):
            await use_case.execute(cmd)

    async def test_commit_is_never_called(self) -> None:
        book = _make_book()
        item = _make_wishlist_item(book=book)
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        db_session = AsyncMock()
        use_case = GetMyWishlistUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = GetMyWishlistCommand(user_id="user-001")

        await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_item_book_title_is_correctly_mapped(self) -> None:
        book = _make_book()
        item = _make_wishlist_item(book=book)
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = GetMyWishlistUseCase(
            db_session=AsyncMock(), wishlist_repo=wishlist_repo
        )
        cmd = GetMyWishlistCommand(user_id="user-001")

        result = await use_case.execute(cmd)

        assert result.items[0].book.title == "The Name of the Wind"
