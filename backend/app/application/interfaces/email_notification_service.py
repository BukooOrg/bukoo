from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.application.dtos.payment_dto import PaymentReceiptItem


class IEmailNotificationService(ABC):
    @abstractmethod
    def send_welcome(self, to: str, full_name: str) -> None:
        pass

    @abstractmethod
    def send_verification_email(self, to: str, otp: str) -> None:
        pass

    @abstractmethod
    def send_password_reset_email(self, to: str, otp: str) -> None:
        pass

    @abstractmethod
    def send_payment_receipt(
        self,
        to: str,
        full_name: str,
        order_id: str,
        payment_ref: str,
        payment_method_display: str,
        items: list[PaymentReceiptItem],
        subtotal: Decimal,
        shipping_cost: Decimal,
        total: Decimal,
        address_snapshot: dict[str, Any],
        paid_at: datetime,
    ) -> None:
        pass

    @abstractmethod
    def send_order_cancellation(
        self,
        to: str,
        full_name: str,
        order_id: str,
        items: list[PaymentReceiptItem],
        total: Decimal,
        cancelled_at: datetime,
    ) -> None:
        pass
