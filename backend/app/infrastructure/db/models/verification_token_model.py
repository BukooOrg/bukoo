from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import VerificationTokenType

from .base import DefaultFieldMixin
from .types import EnumText


class VerificationTokenModel(DefaultFieldMixin):
    __tablename__ = "verification_tokens"
    __table_args__ = (
        Index("idx_verification_tokens_user_id_type", "user_id", "type"),
        Index("idx_verification_tokens_expires_at", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[VerificationTokenType] = mapped_column(
        EnumText(VerificationTokenType, length=50), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
