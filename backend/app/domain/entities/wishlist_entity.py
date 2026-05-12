from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wishlist_item_entity import WishlistItemEntity


@dataclass
class WishlistEntity:
    _id: str
    _user_id: str
    _created_at: datetime
    _updated_at: datetime
    # Eagerly loaded (lazy="selectin" on WishlistModel).
    _wishlist_items: list[WishlistItemEntity] = field(default_factory=list)

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def wishlist_items(self) -> list[WishlistItemEntity]:
        return list(self._wishlist_items)

    # methods
    def find_item_by_book_id(self, book_id: str) -> WishlistItemEntity | None:
        return next(
            (item for item in self._wishlist_items if item.book_id == book_id), None
        )

    def add_wishlist_item(self, wishlist_item: WishlistItemEntity) -> None:
        """
        Append a pre-built WishlistItemEntity.
        Raises if the same book_id is already present.
        """
        if self.find_item_by_book_id(wishlist_item.book_id) is not None:
            raise ValueError(
                f"Book {wishlist_item.book_id!r} is already in the wishlist."
            )
        self._wishlist_items.append(wishlist_item)
        self._updated_at = datetime.now(UTC)

    def remove_wishlist_item(self, wishlist_item_id: str) -> None:
        """Remove a wishlist item by its entity id."""
        before = len(self._wishlist_items)
        self._wishlist_items = [
            i for i in self._wishlist_items if i.id != wishlist_item_id
        ]

        if len(self._wishlist_items) == before:
            raise ValueError(
                f"WishlistItem {wishlist_item_id!r} not found in this wishlist."
            )

        self._updated_at = datetime.now(UTC)
