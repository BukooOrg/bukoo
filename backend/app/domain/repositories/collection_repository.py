from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.collection_entity import CollectionEntity


class ICollectionRepository(ABC):
    @abstractmethod
    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        pass

    @abstractmethod
    async def save(self, collection: CollectionEntity) -> None:
        pass
