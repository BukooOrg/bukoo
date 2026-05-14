from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.constants import OrderStatus, UserRole

from .payment_dto import PaymentSummaryResult


# commands
@dataclass(frozen=True)
class PlaceOrderCommand:
    user_id: str
    cart_item_ids: list[str]


@dataclass(frozen=True)
class ViewOrderDetailCommand:
    order_id: str
    user_id: str
    user_role: UserRole


# requests
@dataclass(frozen=True)
class BaseOrderResult:
    id: str
    status: OrderStatus
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    address_snapshot: dict[str, Any]
    items: list[BaseOrderItemResult]
    created_at: datetime


@dataclass(frozen=True)
class BaseOrderItemResult:
    id: str
    book_id: str
    book_title: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


@dataclass(frozen=True)
class PlaceOrderResult(BaseOrderResult):
    pass


@dataclass(frozen=True)
class ViewOrderDetailResult(BaseOrderResult):
    user_id: str
    payment: PaymentSummaryResult | None
    updated_at: datetime
