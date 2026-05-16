from __future__ import annotations

from decimal import Decimal
from typing import override

from app.application.dtos.payment_dto import PaymentProcessResult
from app.application.interfaces.payment_strategy import IPaymentStrategy
from app.core.constants import PaymentMethod


class CardPaymentStrategy(IPaymentStrategy):
    def __init__(self, card_number: str, expiry_date: str, cvv: str) -> None:
        self._card_number = card_number
        self._expiry_date = expiry_date
        self._cvv = cvv

    @override
    async def process_payment(
        self, order_id: str, amount: Decimal, outcome: str
    ) -> PaymentProcessResult:
        success = outcome == "success"
        return PaymentProcessResult(
            success=success,
            method=PaymentMethod.CARD,
            simulated_ref=f"CARD-AUTH-{order_id[:8].upper()}" if success else None,
        )
