"""
SQLAlchemy ORM models for the wishlist_items table.

Table: wishlist_items
    Each row is one book in a user's wishlist.
    Unique on (wishlist_id, book_id) — a book can only appear once.
    Cascade-deleted when either the parent wishlist or the book is deleted.

    added_at replaces the standard created_at/updated_at pair because
    wishlist items are immutable after insertion; the only relevant
    timestamp is when the item was added.

"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .book_model import BookModel
    from .wishlist_model import WishlistModel


class WishlistItemModel(DefaultFieldMixin):
    """
    Single book entry in a wishlist.

    added_at is server-managed (DEFAULT CURRENT_TIMESTAMP) and kept
    separate from the inherited created_at/updated_at timestamps so that
    the semantic intent — "when was this book wished for" — is explicit.
    """

    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint("wishlist_id", "book_id", name="uq_wishlist_items"),
    )

    wishlist_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("wishlists.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    book_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        init=False,
    )

    wishlist: Mapped[WishlistModel] = relationship(
        "WishlistModel",
        back_populates="wishlist_items",
        init=False,
    )
    book: Mapped["BookModel"] = relationship(
        "BookModel",
        lazy="selectin",
        init=False,
    )
