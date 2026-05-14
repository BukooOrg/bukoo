from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.core.constants import OrderStatus, PaymentStatus


# requests
class PlaceOrderRequest(BaseModel):
    cart_item_ids: list[str] = Field(min_length=1)


class OnlineBankingPaymentRequest(BaseModel):
    payment_method: Literal["online_banking"]
    outcome: Literal["success", "failure"]
    bank_name: str = Field(min_length=1)
    account_number: str = Field(min_length=1)


class CardPaymentRequest(BaseModel):
    payment_method: Literal["card"]
    outcome: Literal["success", "failure"]
    card_number: str = Field(min_length=1)
    expiry_date: str = Field(min_length=1)
    cvv: str = Field(min_length=1)


PayOrderRequest = Annotated[
    OnlineBankingPaymentRequest | CardPaymentRequest,
    Field(discriminator="payment_method"),
]


# responses
class BaseOrderItemResponse(BaseModel):
    id: str
    book_id: str
    book_title: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class BaseOrderResponse(BaseModel):
    id: str
    status: OrderStatus
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    address_snapshot: dict[str, Any]
    items: list[BaseOrderItemResponse]
    created_at: datetime


class PlaceOrderResponse(BaseOrderResponse):
    pass


class PaymentSummaryResponse(BaseModel):
    id: str
    method: str
    amount: Decimal
    status: PaymentStatus
    simulated_ref: str | None
    created_at: datetime


class PayOrderResponse(BaseModel):
    order_id: str
    order_status: OrderStatus
    payment: PaymentSummaryResponse


class ViewOrderDetailResponse(BaseOrderResponse):
    user_id: str
    payment: PaymentSummaryResponse | None
    updated_at: datetime


class CancelOrderResponse(BaseModel):
    id: str
    status: OrderStatus
    updated_at: datetime


class UpdateOrderStatusRequest(BaseModel):
    status: Literal[OrderStatus.SHIPPED, OrderStatus.DELIVERED]


class UpdateOrderStatusResponse(BaseModel):
    id: str
    status: OrderStatus
    updated_at: datetime
