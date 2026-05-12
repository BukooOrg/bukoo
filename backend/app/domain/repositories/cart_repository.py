from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import CartEntity


class ICartRepository(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> CartEntity | None:
        pass

    @abstractmethod
    async def delete_item_by_item_id(self, item_id: str) -> None:
        pass

    @abstractmethod
    async def save(self, cart: CartEntity) -> None:
        pass
