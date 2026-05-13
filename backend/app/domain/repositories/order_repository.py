from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import OrderEntity


class IOrderRepository(ABC):
    @abstractmethod
    async def save(self, order: OrderEntity) -> None:
        pass
