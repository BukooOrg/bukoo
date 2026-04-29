"""
SQLAlchemy ORM models for the orders tables.

Table: orders
    Represents a confirmed purchase intent.
    address_snapshot (JSONB) captures the shipping address at checkout time
    so that future address edits never corrupt historical order records.
    user_id is SET NULL on user deletion — orders are kept for audit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.constants import OrderStatus

from .base import DefaultFieldMixin
from .types import EnumText

if TYPE_CHECKING:
    from .order_item_model import OrderItemModel
    from .payment_model import PaymentModel
    from .user_model import UserModel


class OrderModel(DefaultFieldMixin):
    __tablename__ = "orders"
    __table_args__ = (
        # CheckConstraint(
        #     "status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')",
        #     name="ck_orders_status",
        # ),
        # CheckConstraint("subtotal >= 0", name="ck_orders_subtotal"),
        # CheckConstraint("shipping_cost >= 0", name="ck_orders_shipping_cost"),
        # CheckConstraint("total >= 0", name="ck_orders_total"),
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
    )

    user_id: Mapped[str | None] = mapped_column(
        String(255),  # FK → users.id VARCHAR(255)
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )
    # JSONB snapshot of the shipping address taken at checkout.
    address_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        EnumText(OrderStatus, length=50), nullable=False, default=OrderStatus.PENDING
    )

    user: Mapped[UserModel] = relationship(  # noqa: F821
        "UserModel",
        back_populates="orders",
        init=False,
    )
    order_items: Mapped[list[OrderItemModel]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
    payment: Mapped[PaymentModel | None] = relationship(
        "PaymentModel",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )

    @validates("subtotal")
    def validate_subtotal(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"subtotal must be >= 0, got {value}.")
        return value

    @validates("shipping_cost")
    def validate_shipping_cost(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"shipping_cost must be >= 0, got {value}.")
        return value

    @validates("total")
    def validate_total(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"total must be >= 0, got {value}.")
        return value
