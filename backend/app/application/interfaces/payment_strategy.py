from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.application.dtos.payment_dto import PaymentProcessResult


class IPaymentStrategy(ABC):
    @abstractmethod
    async def process_payment(
        self, order_id: str, amount: Decimal, outcome: str
    ) -> PaymentProcessResult:
        pass
