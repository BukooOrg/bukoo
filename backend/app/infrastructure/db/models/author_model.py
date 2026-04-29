from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .book_author_model import BookAuthorModel


class AuthorModel(DefaultFieldMixin):
    """
    Author entity. Linked to books via the books_authors association table.
    No CHECK constraints → no @validates needed.
    """

    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    book_associations: Mapped[list[BookAuthorModel]] = relationship(
        "BookAuthorModel",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
