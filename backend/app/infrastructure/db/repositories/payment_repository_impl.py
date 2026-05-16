from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import PaymentEntity
from app.domain.repositories import IPaymentRepository
from app.infrastructure.db.mappers import PaymentMapper


class PaymentRepositoryImpl(IPaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, payment: PaymentEntity) -> None:
        model = PaymentMapper.to_model(payment)
        await self._session.merge(model)
