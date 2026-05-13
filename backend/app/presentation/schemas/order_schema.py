from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import OrderStatus


# requests
class PlaceOrderRequest(BaseModel):
    cart_item_ids: list[str] = Field(min_length=1)


# responses
class BaseOrderItemResponse(BaseModel):
    id: str
    book_id: str
    book_title: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class PlaceOrderResponse(BaseModel):
    id: str
    status: OrderStatus
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    address_snapshot: dict[str, Any]
    items: list[BaseOrderItemResponse]
    created_at: datetime
