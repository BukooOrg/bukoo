from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.core.constants import OrderStatus, PaymentStatus


# commands
@dataclass(frozen=True)
class OnlineBankingDetails:
    bank_name: str
    account_number: str


@dataclass(frozen=True)
class CardDetails:
    card_number: str
    expiry_date: str
    cvv: str


@dataclass(frozen=True)
class PayOrderCommand:
    order_id: str
    user_id: str
    user_email: str
    user_full_name: str
    payment_method: str
    outcome: str
    online_banking_details: OnlineBankingDetails | None = None
    card_details: CardDetails | None = None


@dataclass(frozen=True)
class ProcessPaymentCommand:
    order_id: str
    amount: Decimal
    payment_method: str
    outcome: str
    online_banking_details: OnlineBankingDetails | None = None
    card_details: CardDetails | None = None


# results
@dataclass(frozen=True)
class PaymentReceiptItem:
    book_title: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class PaymentProcessResult:
    success: bool
    method: str
    simulated_ref: str | None


@dataclass(frozen=True)
class PaymentSummaryResult:
    id: str
    method: str
    amount: Decimal
    status: PaymentStatus
    simulated_ref: str | None
    created_at: datetime


@dataclass(frozen=True)
class PayOrderResult:
    order_id: str
    order_status: OrderStatus
    payment: PaymentSummaryResult
