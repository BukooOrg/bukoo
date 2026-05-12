from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


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


class AddWishlistItemResponse(BaseWishlistItemResponse):
    pass
