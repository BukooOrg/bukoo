from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .author_model import AuthorModel
    from .book_model import BookModel


class BookAuthorModel(Base, TimestampMixin):
    """
    Many-to-many join table between books and authors.
    display_order controls the credit order on a book's detail page
    (1 = primary/first-listed author).

    No UuidV7Mixin — the composite (book_id, author_id) is the PK.
    No SoftDeleteMixin — rows are hard-deleted when an author is
    removed from a book.
    """

    __tablename__ = "books_authors"
    __table_args__ = (
        # CheckConstraint("display_order >= 1", name="ck_books_authors_order"),
        Index("idx_books_authors_author_id", "author_id"),
    )

    book_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        init=False,
    )
    author_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("authors.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        init=False,
    )
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)

    book: Mapped[BookModel] = relationship(
        "BookModel",
        back_populates="author_associations",
        init=False,
    )
    author: Mapped[AuthorModel] = relationship(
        "AuthorModel",
        back_populates="book_associations",
        init=False,
    )

    @validates("display_order")
    def validate_display_order(self, key: str, value: int) -> int:
        if value is not None and value < 1:
            raise ValueError(f"display_order must be >= 1, got {value}.")
        return value
