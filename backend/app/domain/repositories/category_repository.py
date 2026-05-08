from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import CategoryEntity


class ICategoryRepository(ABC):
    @abstractmethod
    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        pass

    @abstractmethod
    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        pass

    @abstractmethod
    async def find_all(self, collection_id: str | None = None) -> list[CategoryEntity]:
        pass

    @abstractmethod
    async def save(self, category: CategoryEntity) -> None:
        pass
