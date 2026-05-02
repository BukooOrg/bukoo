from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import DefaultFieldMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .book_model import BookModel
    from .collection_model import CollectionModel


class CategoryModel(DefaultFieldMixin, SoftDeleteMixin):
    """
    Sub-grouping within a collection (e.g. "Mystery", "Self-Help").
    Cascade-deletes when its parent collection is deleted.
    Books that reference a deleted category have category_id set to NULL
    (ON DELETE SET NULL on the books FK).
    """

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("url_slug", name="uq_categories_url_slug"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    collection_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    collection: Mapped[CollectionModel] = relationship(
        "CollectionModel",
        back_populates="categories",
        init=False,
    )
    books: Mapped[list[BookModel]] = relationship(
        "BookModel",
        back_populates="category",
        lazy="noload",
        init=False,
    )
