from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .author_entity import AuthorEntity


@dataclass
class BookAuthorEntity:
    """
    Represents a row in the books_authors join table.

    Carries display_order (the credit position of the author on a book's
    detail page) and resolves the full AuthorEntity for convenience.
    Both the raw author_id FK and the resolved AuthorEntity are held so
    that callers can work with either without extra lookups.
    """

    _book_id: str
    _author_id: str
    _display_order: int
    _created_at: datetime
    _updated_at: datetime
    # Resolved from the selectin-loaded relationship on BookAuthorModel.
    _author: AuthorEntity | None = None

    # getters
    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def author_id(self) -> str:
        return self._author_id

    @property
    def display_order(self) -> int:
        return self._display_order

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def author(self) -> AuthorEntity | None:
        return self._author

    # methods
    def set_author(self, author: AuthorEntity) -> None:
        """Attach the resolved AuthorEntity (used by the mapper)."""
        self._author = author

    def reorder(self, display_order: int) -> None:
        """Change the credit position of this author on the book."""
        if display_order < 1:
            raise ValueError(f"display_order must be >= 1, got {display_order}.")
        self._display_order = display_order
        self._updated_at = datetime.now(UTC)
