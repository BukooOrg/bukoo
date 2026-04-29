"""
SQLAlchemy ORM models for the cart_items table.
Table: cart_items
    Each row is one book line in the cart with a quantity.
    Unique on (cart_id, book_id) — adding the same book again increments
    quantity at the service layer rather than inserting a duplicate row.
    quantity must be >= 1 (CHECK constraint + @validates).

Validation notes:
    @validates covers the explicit CHECK constraint:
      CartItemModel: quantity >= 1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .book_model import BookModel
    from .cart_model import CartModel


class CartItemModel(DefaultFieldMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "book_id", name="uq_cart_items"),
        # CheckConstraint("quantity >= 1", name="ck_cart_items_quantity"),
    )

    cart_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    book_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    quantity: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)

    cart: Mapped[CartModel] = relationship(
        "CartModel",
        back_populates="cart_items",
        init=False,
    )
    book: Mapped["BookModel"] = relationship(
        "BookModel",
        lazy="selectin",
        init=False,
    )

    @validates("quantity")
    def validate_quantity(self, key: str, value: int) -> int:
        if value is not None and value < 1:
            raise ValueError(f"quantity must be >= 1, got {value}.")
        return value
