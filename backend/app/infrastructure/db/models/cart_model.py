"""
SQLAlchemy ORM models for the carts table.

Table: carts
    One active cart per user (enforced by uq_carts_user).
    Cascade-deleted when the user is deleted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .cart_item_model import CartItemModel
    from .user_model import UserModel


class CartModel(DefaultFieldMixin):
    __tablename__ = "carts"
    __table_args__ = (UniqueConstraint("user_id", name="uq_carts_user"),)

    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="cart",
        init=False,
    )
    cart_items: Mapped[list[CartItemModel]] = relationship(
        "CartItemModel",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
        order_by="CartItemModel.created_at",
    )
