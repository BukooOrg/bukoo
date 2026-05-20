from __future__ import annotations

from decimal import Decimal
from typing import TypeVar

from pydantic import BaseModel, Field

from app.application.dtos.cart_dtos import BaseCartItemResult
from app.core.util import build_public_url


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


class ClearAllCartItemsResponse(BaseModel):
    id: str
    items: list[BaseCartItemResponse]


# utils
T = TypeVar("T", bound=BaseCartItemResult)
P = TypeVar("P", bound=BaseCartItemResponse)


def build_base_cart_item_response(result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=result.id,
        cart_id=result.cart_id,
        book_id=result.book_id,
        quantity=result.quantity,
        book=CartItemBookResponse(
            id=result.book.id,
            title=result.book.title,
            price=result.book.price,
            cover_url=build_public_url(result.book.cover_url),
        ),
    )
