from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_entity import BookEntity


@dataclass
class CartItemEntity:
    _id: str
    _cart_id: str
    _book_id: str
    _quantity: int
    _created_at: datetime
    _updated_at: datetime
    # Resolved from selectin-loaded relationship on CartItemModel.
    _book: BookEntity | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def cart_id(self) -> str:
        return self._cart_id

    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def book(self) -> BookEntity | None:
        return self._book

    # methods
    def set_book(self, book: BookEntity) -> None:
        """Attach the resolved BookEntity (used by the mapper)."""
        self._book = book

    def increase_quantity(self, qty: int) -> None:
        """Increment the line quantity by qty."""
        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}.")
        self._quantity += qty
        self._updated_at = datetime.now(UTC)

    def decrease_quantity(self, qty: int) -> None:
        """Decrement the line quantity by qty (minimum 1)."""
        if qty <= 0:
            raise ValueError(f"qty must be > 0, got {qty}.")
        if self._quantity - qty < 1:
            raise ValueError(
                f"Quantity cannot drop below 1: have {self._quantity}, reducing by {qty}."
            )
        self._quantity -= qty
        self._updated_at = datetime.now(UTC)

    def change_quantity(self, qty: int) -> None:
        """Set an absolute quantity value (must be >= 1)."""
        if qty < 1:
            raise ValueError(f"quantity must be >= 1, got {qty}.")
        self._quantity = qty
        self._updated_at = datetime.now(UTC)
