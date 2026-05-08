from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.collection_entity import CollectionEntity


class ICollectionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, collection_id: str) -> CollectionEntity | None:
        pass

    @abstractmethod
    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        pass

    @abstractmethod
    async def find_all(self) -> list[CollectionEntity]:
        pass

    @abstractmethod
    async def save(self, collection: CollectionEntity) -> None:
        pass

    @abstractmethod
    async def soft_delete_with_categories(self, collection_id: str) -> None:
        pass
