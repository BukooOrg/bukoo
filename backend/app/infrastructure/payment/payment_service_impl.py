from __future__ import annotations

from typing import override

from app.application.dtos.payment_dto import PaymentProcessResult, ProcessPaymentCommand
from app.application.interfaces.payment_service import IPaymentService


class PaymentServiceImpl(IPaymentService):
    @override
    async def execute_payment(
        self, command: ProcessPaymentCommand
    ) -> PaymentProcessResult:
        return await self._payment_strategy.process_payment(
            order_id=command.order_id,
            amount=command.amount,
            outcome=command.outcome,
        )
