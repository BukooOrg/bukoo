from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# commands
@dataclass(frozen=True)
class AddCartItemCommand:
    book_id: str
    user_id: str
    quantity: int


@dataclass(frozen=True)
class UpdateCartItemQuantityCommand:
    item_id: str
    user_id: str
    quantity: int


# results
@dataclass(frozen=True)
class CartItemBookResult:
    id: str
    title: str
    price: Decimal
    cover_url: str | None


@dataclass(frozen=True)
class BaseCartItemResult:
    id: str
    cart_id: str
    book_id: str
    quantity: int
    book: CartItemBookResult


@dataclass(frozen=True)
class AddCartItemResult(BaseCartItemResult):
    pass


@dataclass(frozen=True)
class UpdateCartItemQuantityResult(BaseCartItemResult):
    pass
