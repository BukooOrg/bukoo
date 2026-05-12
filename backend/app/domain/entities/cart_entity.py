from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_entity import BookEntity
    from .cart_item_entity import CartItemEntity


@dataclass
class CartEntity:
    _id: str
    _user_id: str
    _created_at: datetime
    _updated_at: datetime
    # Eagerly loaded (lazy="selectin" on CartModel).
    _cart_items: list[CartItemEntity] = field(default_factory=list)

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def cart_items(self) -> list[CartItemEntity]:
        return list(self._cart_items)

    # methods
    def find_item_by_book_id(self, book_id: str) -> CartItemEntity | None:
        return next(
            (item for item in self._cart_items if item.book_id == book_id), None
        )

    def find_item_by_cart_item_id(self, cart_item_id: str) -> CartItemEntity | None:
        return next(
            (item for item in self._cart_items if item.id == cart_item_id), None
        )

    def add_item(self, book: BookEntity, qty: int) -> None:
        """
        Add qty copies of a book to the cart.
        If the book is already in the cart its quantity is incremented
        rather than creating a duplicate line.
        """
        if qty < 1:
            raise ValueError(f"qty must be >= 1, got {qty}.")

        existing = self.find_item_by_book_id(book.id)

        if existing:
            existing.increase_quantity(qty)
        else:
            raise ValueError(
                "CartItemEntity must be created by the service layer and passed "
                "to add_item; use this method only with a pre-built CartItemEntity."
            )

        self._updated_at = datetime.now(UTC)

    def remove_item(self, book_id: str) -> None:
        """Remove a line item from the cart by book_id."""
        before = len(self._cart_items)
        self._cart_items = [i for i in self._cart_items if i.book_id != book_id]

        if len(self._cart_items) == before:
            raise ValueError(f"Book {book_id!r} is not in the cart.")

        self._updated_at = datetime.now(UTC)

    def update_item_quantity(self, cart_item_id: str, qty: int) -> None:
        """Set an absolute quantity for an existing cart line."""
        item = self.find_item_by_cart_item_id(cart_item_id)

        if item is None:
            raise ValueError(f"Cart item {cart_item_id!r} is not in the cart.")

        item.change_quantity(qty)
        self._updated_at = datetime.now(UTC)

    def append_item(self, item: CartItemEntity) -> None:
        """Append a pre-built CartItemEntity to the cart."""
        self._cart_items.append(item)
        self._updated_at = datetime.now(UTC)

    def clear(self) -> None:
        """Remove all items from the cart."""
        self._cart_items = []
        self._updated_at = datetime.now(UTC)
