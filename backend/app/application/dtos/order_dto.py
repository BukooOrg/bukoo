from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.constants import OrderStatus


# commands
@dataclass(frozen=True)
class PlaceOrderCommand:
    user_id: str
    cart_item_ids: list[str]


# requests
@dataclass(frozen=True)
class BaseOrderItemResult:
    id: str
    book_id: str
    book_title: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


@dataclass(frozen=True)
class PlaceOrderResult:
    id: str
    status: OrderStatus
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    address_snapshot: dict[str, Any]
    items: list[BaseOrderItemResult]
    created_at: datetime
