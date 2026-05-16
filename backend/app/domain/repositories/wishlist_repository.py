from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import WishlistEntity


class IWishlistRepository(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> WishlistEntity | None:
        pass

    @abstractmethod
    async def delete_item_by_item_id(self, item_id: str) -> None:
        pass

    @abstractmethod
    async def save(self, wishlist: WishlistEntity) -> None:
        pass
