"""
SQLAlchemy ORM models for the users and accounts tables.

Table: accounts
    Account records. One row per (user, provider) pair.
    A single user can have different login account. For example, a credential login and a Google login.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AuthProvider

from .base import DefaultFieldMixin
from .types import EnumText

if TYPE_CHECKING:
    from .user_model import UserModel


class AccountModel(DefaultFieldMixin):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_accounts_provider"),
        UniqueConstraint("provider", "open_id", name="uq_accounts_open_id"),
        Index("idx_accounts_user_id", "user_id"),
    )

    provider: Mapped[AuthProvider] = mapped_column(
        EnumText(AuthProvider, length=50), nullable=False
    )
    open_id: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_token: Mapped[str | None] = mapped_column(
        String(2000), nullable=True, default=None
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="accounts",
        init=False,
    )
