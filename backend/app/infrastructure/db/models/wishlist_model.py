"""
SQLAlchemy ORM models for the wishlists tables.

Table: wishlists
    One per user (enforced by uq_wishlists_user). Created lazily on first
    "add to wishlist" action. Cascade-deleted when the user is deleted.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .user_model import UserModel
    from .wishlist_item_model import WishlistItemModel


class WishlistModel(DefaultFieldMixin):
    __tablename__ = "wishlists"
    __table_args__ = (UniqueConstraint("user_id", name="uq_wishlists_user"),)

    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="wishlist",
        init=False,
    )
    wishlist_items: Mapped[list[WishlistItemModel]] = relationship(
        "WishlistItemModel",
        back_populates="wishlist",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
        order_by="WishlistItemModel.added_at",
    )
