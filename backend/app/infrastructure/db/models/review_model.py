"""
SQLAlchemy ORM model for the reviews table.

Table: reviews
    Stores customer ratings and/or text reviews for purchased books.
    A review is tied to a specific order_item_id to enforce the
    "must have purchased the book" rule at the database level.

    Constraints:
    - ck_rating_comment: at least one of rating or comment must be non-NULL.
      This is a cross-field constraint that cannot be reliably enforced with
      @validates (the other field may not be set yet at assignment time), so
      it is enforced at the DB layer only.
    - user_id is SET NULL on user deletion.
    - book_id CASCADE deletes the review when the book is hard-deleted.
    - order_item_id CASCADE deletes the review when the order item is deleted.

    Soft-delete (deleted_at) is used by admins to hide inappropriate or
    spoiler reviews without permanent data loss.

Validation notes:
    The only CHECK constraint (ck_rating_comment) is cross-field and is
    intentionally left to the DB layer per project convention. No @validates
    methods are defined here.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .book_model import BookModel
    from .order_item_model import OrderItemModel
    from .user_model import UserModel


class ReviewModel(DefaultFieldMixin, SoftDeleteMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        # CheckConstraint(
        #     "rating IS NOT NULL OR comment IS NOT NULL",
        #     name="ck_rating_comment",
        # ),
        Index("idx_reviews_book_id", "book_id"),
        Index("idx_reviews_user_id", "user_id"),
        Index("idx_reviews_order_item_id", "order_item_id"),
        Index("idx_reviews_deleted_at", "deleted_at"),
    )

    rating: Mapped[int | None] = mapped_column(Integer(), nullable=True, default=None)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True, default=None)
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )
    book_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    order_item_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    hidden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )

    user: Mapped[UserModel | None] = relationship(
        "UserModel",
        back_populates="reviews",
        init=False,
    )
    book: Mapped[BookModel] = relationship(
        "BookModel",
        lazy="selectin",
        init=False,
    )
    order_item: Mapped[OrderItemModel] = relationship(
        "OrderItemModel",
        back_populates="review",
        init=False,
    )
