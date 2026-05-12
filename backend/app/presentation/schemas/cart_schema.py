from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


# requests
class AddCartItemRequest(BaseModel):
    book_id: str
    quantity: int = Field(ge=1)


# responses
class CartItemBookResponse(BaseModel):
    id: str
    title: str
    price: Decimal
    cover_url: str | None


class BaseCartItemResponse(BaseModel):
    id: str
    cart_id: str
    book_id: str
    quantity: int
    book: CartItemBookResponse


class AddCartItemResponse(BaseCartItemResponse):
    pass
