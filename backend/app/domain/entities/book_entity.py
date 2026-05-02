from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_author_entity import BookAuthorEntity
    from .category_entity import CategoryEntity
    from .publisher_entity import PublisherEntity


@dataclass
class BookEntity:
    _id: str
    _title: str
    _price: Decimal
    _stock_quantity: int
    _language: str
    _publisher_id: str | None
    _category_id: str | None
    _isbn: str | None
    _description: str | None
    _cover_url: str | None
    _page_count: int | None
    _published_date: date | None
    _deactivated_at: datetime | None
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None
    # Resolved relationships (selectin-loaded on the ORM side).
    _publisher: PublisherEntity | None = None
    _category: CategoryEntity | None = None
    # Ordered list of BookAuthorEntity (carries display_order + AuthorEntity).
    _authors: list[BookAuthorEntity] = field(default_factory=list)

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def stock_quantity(self) -> int:
        return self._stock_quantity

    @property
    def language(self) -> str:
        return self._language

    @property
    def publisher_id(self) -> str | None:
        return self._publisher_id

    @property
    def category_id(self) -> str | None:
        return self._category_id

    @property
    def isbn(self) -> str | None:
        return self._isbn

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def cover_url(self) -> str | None:
        return self._cover_url

    @property
    def page_count(self) -> int | None:
        return self._page_count

    @property
    def published_date(self) -> date | None:
        return self._published_date

    @property
    def deactivated_at(self) -> datetime | None:
        return self._deactivated_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def publisher(self) -> PublisherEntity | None:
        return self._publisher

    @property
    def category(self) -> CategoryEntity | None:
        return self._category

    @property
    def authors(self) -> list[BookAuthorEntity]:
        return self._authors

    # derived properties
    @property
    def is_active(self) -> bool:
        """True when the book is visible on the storefront."""
        return self._deactivated_at is None and not self.is_deleted

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    @property
    def has_stock(self) -> bool:
        return self._stock_quantity > 0

    # methods
    def activate(self) -> None:
        """Make the book visible on the storefront."""
        self._deactivated_at = None
        self._updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Hide the book from the storefront without deleting it."""
        self._deactivated_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """Soft-delete the book record."""
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)

    def increase_stock(self, qty: int) -> None:
        """Add qty copies to the available stock."""
        if qty <= 0:
            raise ValueError(f"qty to increase must be > 0, got {qty}.")
        self._stock_quantity += qty
        self._updated_at = datetime.now(UTC)

    def decrease_stock(self, qty: int) -> None:
        """Deduct qty copies from the available stock (e.g. on purchase)."""
        if qty <= 0:
            raise ValueError(f"qty to decrease must be > 0, got {qty}.")
        if self._stock_quantity - qty < 0:
            raise ValueError(
                f"Insufficient stock: have {self._stock_quantity}, need {qty}."
            )
        self._stock_quantity -= qty
        self._updated_at = datetime.now(UTC)

    def set_author(self, author: BookAuthorEntity) -> None:
        """
        Add or replace an author association by author_id.
        If an association for the same author_id already exists it is
        replaced; otherwise the new association is appended.
        """
        self._authors = [a for a in self._authors if a.author_id != author.author_id]
        self._authors.append(author)
        self._authors.sort(key=lambda a: a.display_order)
        self._updated_at = datetime.now(UTC)
