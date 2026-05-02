"""
SQLAlchemy ORM models for the payments tables.

Table: payments
    One-to-one with orders (uq_payments_order).
    simulated_ref holds a fake transaction reference for the simulated
    payment provider used during development.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.constants import PaymentStatus

from .base import DefaultFieldMixin
from .types import EnumText

if TYPE_CHECKING:
    from .order_model import OrderModel


class PaymentModel(DefaultFieldMixin):
    """
    One-to-one payment record per order.
    simulated_ref stores a fake transaction ID for the mock payment provider.
    """

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payments_order"),
        # CheckConstraint(
        #     "status IN ('pending', 'success', 'failed')",
        #     name="ck_payments_status",
        # ),
        # CheckConstraint("amount >= 0", name="ck_payments_amount"),
    )

    order_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        EnumText(PaymentStatus, length=50),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    simulated_ref: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    order: Mapped[OrderModel] = relationship(
        "OrderModel",
        back_populates="payments",
        init=False,
    )

    @validates("amount")
    def validate_amount(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"amount must be >= 0, got {value}.")
        return value
