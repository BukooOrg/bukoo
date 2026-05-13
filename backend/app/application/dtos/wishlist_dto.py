from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .cart_dtos import BaseCartItemResult


# commands
@dataclass(frozen=True)
class GetMyWishlistCommand:
    user_id: str


@dataclass(frozen=True)
class AddWishlistItemCommand:
    book_id: str
    user_id: str


@dataclass(frozen=True)
class RemoveWishlistItemCommand:
    user_id: str
    item_id: str


@dataclass(frozen=True)
class MoveWishlistItemToCartCommand:
    user_id: str
    item_id: str


# results
@dataclass(frozen=True)
class WishlistItemBookResult:
    id: str
    title: str
    price: Decimal
    cover_url: str | None


@dataclass(frozen=True)
class BaseWishlistItemResult:
    id: str
    wishlist_id: str
    book_id: str
    added_at: datetime
    book: WishlistItemBookResult


@dataclass(frozen=True)
class GetMyWishlistResult:
    id: str
    items: list[BaseWishlistItemResult]


@dataclass(frozen=True)
class AddWishlistItemResult(BaseWishlistItemResult):
    pass


@dataclass(frozen=True)
class MoveWishlistItemToCartResult(BaseCartItemResult):
    pass
