from __future__ import annotations

from decimal import Decimal
from typing import override

from app.application.dtos.payment_dto import PaymentProcessResult
from app.application.interfaces.payment_strategy import IPaymentStrategy
from app.core.constants import PaymentMethod


class OnlineBankingPaymentStrategy(IPaymentStrategy):
    def __init__(self, bank_name: str, account_number: str) -> None:
        self._bank_name = bank_name
        self._account_number = account_number

    @override
    async def process_payment(
        self, order_id: str, amount: Decimal, outcome: str
    ) -> PaymentProcessResult:
        success = outcome == "success"
        return PaymentProcessResult(
            success=success,
            method=PaymentMethod.ONLINE_BANKING,
            simulated_ref=f"BANK-TXN-{order_id[:8].upper()}" if success else None,
        )
