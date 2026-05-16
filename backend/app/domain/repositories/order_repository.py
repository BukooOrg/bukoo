from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from app.core.constants import OrderStatus
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import OrderEntity
from app.domain.entities.order_item_entity import OrderItemEntity


@dataclass(frozen=True)
class OrderFilters:
    user_id: str | None = None
    status: OrderStatus | None = None
    date_from: date | None = None
    date_to: date | None = None


class IOrderRepository(ABC):
    @abstractmethod
    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        pass

    @abstractmethod
    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        pass

    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: OrderFilters
    ) -> PaginatedResult[OrderEntity]:
        pass

    @abstractmethod
    async def find_delivered_order_item(
        self, user_id: str, order_item_id: str, book_id: str
    ) -> OrderItemEntity | None:
        pass
