from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .category_model import CategoryModel


class CollectionModel(DefaultFieldMixin, SoftDeleteMixin):
    """
    Top-level catalogue grouping (e.g. "Fiction", "Non-Fiction").
    Soft-deletable; categories cascade-delete when their parent collection
    is hard-deleted.
    """

    __tablename__ = "collections"
    __table_args__ = (UniqueConstraint("url_slug", name="uq_collections_url_slug"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url_slug: Mapped[str] = mapped_column(String(100), nullable=False)

    categories: Mapped[list[CategoryModel]] = relationship(
        "CategoryModel",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
