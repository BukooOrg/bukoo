from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_entity import BookEntity


@dataclass
class ReviewEntity:
    _id: str
    _book_id: str
    _order_item_id: str
    _rating: int | None
    _comment: str | None
    _created_at: datetime
    _deleted_at: datetime | None
    # FK kept for reference; user may have been deleted (SET NULL in DB).
    _user_id: str | None = None
    # Resolved from selectin-loaded relationship on CartItemModel.
    _book: BookEntity | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def order_item_id(self) -> str:
        return self._order_item_id

    @property
    def rating(self) -> int | None:
        return self._rating

    @property
    def comment(self) -> str | None:
        return self._comment

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def book(self) -> BookEntity | None:
        return self._book

    # derived properties
    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    # methods
    def soft_delete(self) -> None:
        """
        Admin action: hide the review from public view without
        permanently removing it from the database.
        """
        self._deleted_at = datetime.now(UTC)

    def set_book(self, book: BookEntity) -> None:
        """
        Re-associate the review with a different book.
        Rarely used but exposed for completeness per the class diagram.
        """
        self._book = book
