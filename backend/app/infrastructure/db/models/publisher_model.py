from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .book_model import BookModel


class PublisherModel(DefaultFieldMixin, SoftDeleteMixin):
    """
    Publisher entity. No soft-delete; books retain SET NULL on removal.
    No CHECK constraints → no @validates needed.
    """

    __tablename__ = "publishers"
    __table_args__ = (UniqueConstraint("name", name="uq_publishers_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None
    )

    books: Mapped[list[BookModel]] = relationship(
        "BookModel",
        back_populates="publisher",
        lazy="noload",
        init=False,
    )
