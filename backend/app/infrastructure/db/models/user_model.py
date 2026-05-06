"""
SQLAlchemy ORM models for the users and accounts tables.

Table: users
    Core identity record. One row per person.
    hashed_password is nullable — users who sign up via OAuth have no password.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import UserRole, UserStatus

from .base import DefaultFieldMixin, SoftDeleteMixin
from .types import EnumText

if TYPE_CHECKING:
    from .account_model import AccountModel
    from .address_model import AddressModel
    from .cart_model import CartModel
    from .notification_model import NotificationModel
    from .order_model import OrderModel
    from .review_model import ReviewModel
    from .wishlist_model import WishlistModel


class UserModel(DefaultFieldMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        # CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        # CheckConstraint("status IN ('pending', 'active', 'suspended')", name="ck_users_status"),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_status", "status"),
        Index("idx_users_deleted_at", "deleted_at"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date(), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, default=None
    )
    role: Mapped[UserRole] = mapped_column(
        EnumText(UserRole, length=50), nullable=False, default=UserRole.USER
    )
    status: Mapped[UserStatus] = mapped_column(
        EnumText(UserStatus, length=50),
        nullable=False,
        default=UserStatus.PENDING,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # one-to-many: a user can have many accounts.
    accounts: Mapped[list[AccountModel]] = relationship(
        "AccountModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
    # One-to-one: a user has at most one shipping address.
    address: Mapped[AddressModel | None] = relationship(
        "AddressModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
    # One-to-one: a user has at most one wishlist.
    wishlist: Mapped[WishlistModel] = relationship(
        "WishlistModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="noload",
        init=False,
    )
    # One-to-one: a user has at most one cart.
    cart: Mapped[CartModel | None] = relationship(
        "CartModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="noload",
        init=False,
    )
    # One-to-many: a user can have many orders (SET NULL on delete).
    orders: Mapped[list[OrderModel]] = relationship(
        "OrderModel",
        back_populates="user",
        lazy="noload",
        init=False,
    )
    # One-to-many: a user can have many reviews (SET NULL on delete).
    reviews: Mapped[list[ReviewModel]] = relationship(
        "ReviewModel",
        back_populates="user",
        lazy="noload",
        init=False,
    )
    # One-to-many: a user can have many notifications (SET NULL on delete).
    notifications: Mapped[list[NotificationModel]] = relationship(
        "NotificationModel",
        back_populates="user",
        lazy="noload",
        init=False,
    )
