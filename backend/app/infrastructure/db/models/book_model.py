from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import DefaultFieldMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .book_author_model import BookAuthorModel
    from .category_model import CategoryModel
    from .publisher_model import PublisherModel


class BookModel(DefaultFieldMixin, SoftDeleteMixin):
    """
    Core product record.

    deactivated_at — set when a book is hidden from the storefront but kept
                     in the database (e.g. out-of-print). Distinct from
                     deleted_at (hard soft-delete for data-retention purposes).

    stock_quantity  — must be >= 0 (CHECK + @validates).
    price           — must be >= 0 (CHECK + @validates).
    page_count      — must be > 0 when provided (CHECK + @validates).
    isbn            — nullable because some books (e.g. bundles) have none.
    """

    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("isbn", name="uq_books_isbn"),
        # CheckConstraint("price >= 0", name="ck_books_price"),
        # CheckConstraint("stock_quantity >= 0", name="ck_books_stock_quantity"),
        # CheckConstraint(
        #     "page_count IS NULL OR page_count > 0", name="ck_books_page_count"
        # ),
        Index("idx_books_publisher_id", "publisher_id"),
        Index("idx_books_title", "title"),
        Index("idx_books_deleted_at", "deleted_at"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True, default=None)
    cover_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, default=None
    )
    stock_quantity: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    page_count: Mapped[int | None] = mapped_column(
        Integer(), nullable=True, default=None
    )
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="english")
    published_date: Mapped[date | None] = mapped_column(
        Date(), nullable=True, default=None
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    publisher_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("publishers.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )
    category_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        init=False,
    )

    publisher: Mapped[PublisherModel | None] = relationship(
        "PublisherModel",
        back_populates="books",
        init=False,
    )
    category: Mapped[CategoryModel | None] = relationship(
        "CategoryModel",
        back_populates="books",
        init=False,
    )
    author_associations: Mapped[list[BookAuthorModel]] = relationship(
        "BookAuthorModel",
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="BookAuthorModel.display_order",
        lazy="selectin",
        init=False,
    )

    @validates("price")
    def validate_price(self, key: str, value: Decimal) -> Decimal:
        if value is not None and value < 0:
            raise ValueError(f"price must be >= 0, got {value}.")
        return value

    @validates("stock_quantity")
    def validate_stock_quantity(self, key: str, value: int) -> int:
        if value is not None and value < 0:
            raise ValueError(f"stock_quantity must be >= 0, got {value}.")
        return value

    @validates("page_count")
    def validate_page_count(self, key: str, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError(f"page_count must be > 0 when provided, got {value}.")
        return value

    @property
    def is_active(self) -> bool:
        """True when the book is visible on the storefront."""
        return self.deactivated_at is None and not self.is_deleted

    @property
    def has_stock(self) -> bool:
        return self.stock_quantity > 0
