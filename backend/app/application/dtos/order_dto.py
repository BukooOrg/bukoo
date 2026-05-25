from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.constants import OrderStatus, UserRole
from app.core.query_params import QueryParams
from app.domain.repositories.order_repository import OrderFilters

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


@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: str
    user_id: str
    user_role: UserRole


@dataclass(frozen=True)
class UpdateOrderStatusCommand:
    order_id: str
    status: OrderStatus


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
    book_cover_url: str | None
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


@dataclass(frozen=True)
class CancelOrderResult:
    id: str
    status: OrderStatus
    updated_at: datetime


@dataclass(frozen=True)
class UpdateOrderStatusResult:
    id: str
    status: OrderStatus
    updated_at: datetime


@dataclass(frozen=True)
class FindOrdersCommand:
    query_params: QueryParams
    filters: OrderFilters = field(default_factory=OrderFilters)


@dataclass(frozen=True)
class OrderSummaryResult:
    id: str
    user_id: str | None
    status: OrderStatus
    total: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime
