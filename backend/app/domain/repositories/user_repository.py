"""
IUserRepository — domain repository interface for UserEntity.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.user_entity import UserEntity


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        pass

    @abstractmethod
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> UserEntity | None:
        pass

    @abstractmethod
    async def save(self, user: UserEntity) -> None:
        pass

    @abstractmethod
    async def soft_delete(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        pass

    @abstractmethod
    async def count_including_deleted(self) -> int:
        pass
