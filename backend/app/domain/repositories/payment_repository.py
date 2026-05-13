from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import PaymentEntity


class IPaymentRepository(ABC):
    @abstractmethod
    async def save(self, payment: PaymentEntity) -> None:
        pass
