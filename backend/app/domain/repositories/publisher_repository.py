from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import PublisherEntity


class IPublisherRepository(ABC):
    @abstractmethod
    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        pass

    @abstractmethod
    async def save(self, publisher: PublisherEntity) -> None:
        pass
