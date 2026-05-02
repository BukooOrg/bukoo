from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_entity import BookEntity


@dataclass
class WishlistItemEntity:
    _id: str
    _wishlist_id: str
    _book_id: str
    _added_at: datetime
    _created_at: datetime
    _updated_at: datetime
    # Resolved from selectin-loaded relationship on WishlistItemModel.
    _book: BookEntity | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def wishlist_id(self) -> str:
        return self._wishlist_id

    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def added_at(self) -> datetime:
        return self._added_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def book(self) -> BookEntity | None:
        return self._book

    # methods
    def set_book(self, book: BookEntity) -> None:
        """Attach the resolved BookEntity (used by the mapper)."""
        self._book = book
