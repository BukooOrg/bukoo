"""
SQLAlchemy ORM models for the order_items table.


Table: order_items
    Individual line items within an order.
    book_title is denormalised (copied at checkout) for the same reason
    as address_snapshot: book records can be updated or soft-deleted later.
    book_id is SET NULL on book deletion so the line item survives.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .book_model import BookModel
    from .order_model import OrderModel
    from .review_model import ReviewModel


class OrderItemModel(DefaultFieldMixin):
    """
    Immutable line item — quantities and prices are fixed at checkout.
    book_title is stored explicitly to survive future book record changes.
    """

    __tablename__ = "order_items"
    __table_args__ = (
        # CheckConstraint("quantity >= 1", name="ck_order_items_quantity"),
        # CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price"),
        # CheckConstraint("line_total >= 0", name="ck_order_items_line_total"),
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_book_id", "book_id"),
    )

    order_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    book_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )
    # Denormalised fields — copied from BookModel at checkout time.
    book_title: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer(), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[OrderModel] = relationship(
        "OrderModel",
        back_populates="order_items",
        init=False,
    )
    book: Mapped[BookModel | None] = relationship(
        "BookModel",
        lazy="selectin",
        init=False,
    )
    review: Mapped[ReviewModel | None] = relationship(
        "ReviewModel",
        back_populates="order_item",
        uselist=False,
        lazy="noload",
        init=False,
    )

    @validates("quantity")
    def validate_quantity(self, key: str, value: int) -> int:
        if value is not None and value < 1:
            raise ValueError(f"quantity must be >= 1, got {value}.")
        return value

    @validates("unit_price")
    def validate_unit_price(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"unit_price must be >= 0, got {value}.")
        return value

    @validates("line_total")
    def validate_line_total(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"line_total must be >= 0, got {value}.")
        return value
