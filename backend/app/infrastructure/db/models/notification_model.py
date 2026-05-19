"""
SQLAlchemy ORM model for the notifications table.

Table: notifications
    Stores outbound notification records (email, etc.) dispatched by
    background Celery workers.

    status lifecycle:  pending → sent | failed

    sent_at is NULL until the notification is successfully dispatched.
    user_id is SET NULL on user deletion — notification history is retained
    for audit but disassociated from the deleted account.

    No updated_at — a notification row is written once and then its status
    is updated in-place; there is no meaningful "updated" semantic beyond
    the status transition itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import NotificationStatus

from .base import Base, UuidV7Mixin
from .types import EnumText

if TYPE_CHECKING:
    from .user_model import UserModel


class NotificationModel(Base, UuidV7Mixin):
    """
    Does not use DefaultFieldMixin because notifications have only
    created_at (no updated_at) and no soft-delete.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        # CheckConstraint(
        #     "status IN ('pending', 'sent', 'failed')",
        #     name="ck_notifications_status",
        # ),
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_status", "status"),
    )

    type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        EnumText(NotificationStatus, length=50),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        init=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )

    user: Mapped[UserModel | None] = relationship(
        "UserModel",
        back_populates="notifications",
        init=False,
    )
