from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dtos.payment_dto import PaymentProcessResult, ProcessPaymentCommand

from .payment_strategy import IPaymentStrategy


class IPaymentService(ABC):
    _payment_strategy: IPaymentStrategy

    def set_strategy(self, strategy: IPaymentStrategy) -> None:
        self._payment_strategy = strategy

    @abstractmethod
    async def execute_payment(
        self, command: ProcessPaymentCommand
    ) -> PaymentProcessResult:
        pass
