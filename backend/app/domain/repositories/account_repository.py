"""
IAccountRepository — domain repository interface for AccountEntity (OAuth integrations).
"""

from __future__ import annotations

from abc import abstractmethod

from app.domain.entities import AccountEntity


class IAccountRepository:
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[AccountEntity]:
        pass

    @abstractmethod
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> AccountEntity | None:
        pass

    @abstractmethod
    async def find_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> AccountEntity | None:
        pass

    @abstractmethod
    async def save(self, account: AccountEntity) -> None:
        pass

    @abstractmethod
    async def delete(self, account_id: str) -> None:
        pass
