from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


# requests
class UpdateCartItemQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)


class AddCartItemRequest(UpdateCartItemQuantityRequest):
    book_id: str


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


class GetMyCartResponse(BaseModel):
    id: str
    items: list[BaseCartItemResponse]


class AddCartItemResponse(BaseCartItemResponse):
    pass


class UpdateCartItemQuantityResponse(BaseCartItemResponse):
    pass
