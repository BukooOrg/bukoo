from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import AuthorEntity


class IAuthorRepository(ABC):
    @abstractmethod
    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        pass

    @abstractmethod
    async def save(self, author: AuthorEntity) -> None:
        pass
