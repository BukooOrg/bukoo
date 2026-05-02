"""
SQLAlchemy ORM model for the addresses table.

Table: addresses
    Stores the shipping address for a user.
    Enforces a one-to-one relationship with users (uq_addresses_user).
    On user deletion the address is cascade-deleted.

    address_snapshot in orders is a JSONB copy taken at checkout time so that
    historical order records are never affected by later address edits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin

if TYPE_CHECKING:
    from .user_model import UserModel


class AddressModel(DefaultFieldMixin):
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint("user_id", name="uq_addresses_user"),)

    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postcode: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="address",
        init=False,
    )
