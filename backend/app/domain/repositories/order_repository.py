from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import OrderEntity


class IOrderRepository(ABC):
    @abstractmethod
    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        pass

    @abstractmethod
    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        pass
