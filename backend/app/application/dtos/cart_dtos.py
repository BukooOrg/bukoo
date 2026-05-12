from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# commands
@dataclass(frozen=True)
class AddCartItemCommand:
    book_id: str
    quantity: int
    user_id: str


@dataclass(frozen=True)
class CartItemBookResult:
    id: str
    title: str
    price: Decimal
    cover_url: str | None


# results
@dataclass(frozen=True)
class AddCartItemResult:
    id: str
    cart_id: str
    book_id: str
    quantity: int
    book: CartItemBookResult
