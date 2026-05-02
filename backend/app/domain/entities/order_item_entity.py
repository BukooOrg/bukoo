from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_entity import BookEntity


@dataclass
class OrderItemEntity:
    """
    Immutable line item within an order.
    book_title and unit_price are denormalised snapshots taken at checkout
    so the record stays accurate even if the book is later edited or removed.
    """

    _id: str
    _order_id: str
    _book_title: str
    _unit_price: Decimal
    _quantity: int
    _line_total: Decimal
    _created_at: datetime
    _updated_at: datetime
    # book_id is nullable (SET NULL when the book is deleted).
    _book_id: str | None = None
    # Resolved from selectin-loaded relationship on OrderItemModel.
    _book: BookEntity | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def book_id(self) -> str | None:
        return self._book_id

    @property
    def book_title(self) -> str:
        return self._book_title

    @property
    def unit_price(self) -> Decimal:
        return self._unit_price

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def line_total(self) -> Decimal:
        return self._line_total

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def book(self) -> BookEntity | None:
        return self._book

    # helper methods
    def _calculate_line_total(self) -> None:
        self._line_total = self._unit_price * self._quantity

    # methods
    def set_book(self, book: BookEntity) -> None:
        """Attach the resolved BookEntity (used by the mapper)."""
        self._book = book

    def increase_quantity(self, qty: int) -> None:
        """Increase quantity and recompute line_total."""
        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}.")
        self._quantity += qty
        self._calculate_line_total()
        self._updated_at = datetime.now(UTC)

    def decrease_quantity(self, qty: int) -> None:
        """Decrease quantity and recompute line_total (minimum 1)."""
        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}.")
        if self._quantity - qty < 1:
            raise ValueError(
                f"Quantity cannot drop below 1: have {self._quantity}, reducing by {qty}."
            )
        self._quantity -= qty
        self._calculate_line_total()
        self._updated_at = datetime.now(UTC)

    def change_quantity(self, qty: int) -> None:
        """Set an absolute quantity value (must be >= 1)."""
        if qty < 1:
            raise ValueError(f"quantity must be >= 1, got {qty}.")
        self._quantity = qty
        self._calculate_line_total()
        self._updated_at = datetime.now(UTC)

    def set_book_id(self, book_id: str) -> None:
        """Re-link to a book record (used by the mapper on reassignment)."""
        self._book_id = book_id
        self._updated_at = datetime.now(UTC)
