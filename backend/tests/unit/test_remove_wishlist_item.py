from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.wishlist_dto import RemoveWishlistItemCommand
from app.application.use_cases.wishlist.remove_wishlist_item import (
    RemoveWishlistItemUseCase,
)
from app.domain.entities.wishlist_entity import WishlistEntity
from app.domain.entities.wishlist_item_entity import WishlistItemEntity
from app.domain.exceptions import WishlistItemNotFoundError, WishlistNotFoundError
from app.domain.repositories import IWishlistRepository


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


@pytest.mark.unit
class TestRemoveWishlistItemUseCase:
    async def test_removes_item_returns_none(self) -> None:
        db_session = AsyncMock()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        result = await use_case.execute(cmd)

        assert result is None

    async def test_save_called_with_mutated_wishlist(self) -> None:
        db_session = AsyncMock()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        await use_case.execute(cmd)

        assert wishlist_repo.saved is not None
        assert len(wishlist_repo.saved.wishlist_items) == 0

    async def test_delete_item_called_with_correct_id(self) -> None:
        db_session = AsyncMock()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        await use_case.execute(cmd)

        assert wishlist_repo.deleted_item_id == "item-001"

    async def test_commit_called_once_on_success(self) -> None:
        db_session = AsyncMock()
        item = _make_wishlist_item()
        wishlist = _make_wishlist(items=[item])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    async def test_raises_wishlist_not_found_when_no_wishlist(self) -> None:
        db_session = AsyncMock()
        wishlist_repo = FakeWishlistRepository(wishlist=None)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        with pytest.raises(WishlistNotFoundError):
            await use_case.execute(cmd)

    async def test_commit_not_called_when_wishlist_not_found(self) -> None:
        db_session = AsyncMock()
        wishlist_repo = FakeWishlistRepository(wishlist=None)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        with pytest.raises(WishlistNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_raises_item_not_found_when_item_absent(self) -> None:
        db_session = AsyncMock()
        wishlist = _make_wishlist(items=[])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="nonexistent-item", user_id="user-001")

        with pytest.raises(WishlistItemNotFoundError):
            await use_case.execute(cmd)

    async def test_commit_not_called_when_item_not_found(self) -> None:
        db_session = AsyncMock()
        wishlist = _make_wishlist(items=[])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="nonexistent-item", user_id="user-001")

        with pytest.raises(WishlistItemNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_only_target_item_removed_from_wishlist(self) -> None:
        db_session = AsyncMock()
        item_a = _make_wishlist_item(item_id="item-001", book_id="book-001")
        item_b = _make_wishlist_item(item_id="item-002", book_id="book-002")
        wishlist = _make_wishlist(items=[item_a, item_b])
        wishlist_repo = FakeWishlistRepository(wishlist=wishlist)
        use_case = RemoveWishlistItemUseCase(
            db_session=db_session, wishlist_repo=wishlist_repo
        )
        cmd = RemoveWishlistItemCommand(item_id="item-001", user_id="user-001")

        await use_case.execute(cmd)

        assert wishlist_repo.saved is not None
        remaining = wishlist_repo.saved.wishlist_items
        assert len(remaining) == 1
        assert remaining[0].id == "item-002"
