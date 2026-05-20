from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TypeVar

from pydantic import BaseModel

from app.application.dtos.wishlist_dto import BaseWishlistItemResult
from app.core.util import build_public_url

from .cart_schema import BaseCartItemResponse


# requests
class AddWishlistItemRequest(BaseModel):
    book_id: str


# responses
class WishlistItemBookResponse(BaseModel):
    id: str
    title: str
    price: Decimal
    cover_url: str | None


class BaseWishlistItemResponse(BaseModel):
    id: str
    wishlist_id: str
    book_id: str
    added_at: datetime
    book: WishlistItemBookResponse


class GetMyWishlistResponse(BaseModel):
    id: str
    items: list[BaseWishlistItemResponse]


class AddWishlistItemResponse(BaseWishlistItemResponse):
    pass


class MoveWishlistItemToCartResponse(BaseCartItemResponse):
    pass


# utils
T = TypeVar("T", bound=BaseWishlistItemResult)
P = TypeVar("P", bound=BaseWishlistItemResponse)


def build_base_wishlist_item_response(result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=result.id,
        wishlist_id=result.wishlist_id,
        book_id=result.book_id,
        added_at=result.added_at,
        book=WishlistItemBookResponse(
            id=result.book.id,
            title=result.book.title,
            price=result.book.price,
            cover_url=build_public_url(result.book.cover_url),
        ),
    )
