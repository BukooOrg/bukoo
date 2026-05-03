"""
SQLAlchemy async implementation of IAccountRepository.
"""

from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AccountEntity
from app.domain.repositories.account_repository import IAccountRepository
from app.infrastructure.db.mappers import AccountMapper
from app.infrastructure.db.models import AccountModel


class AccountRepositoryImpl(IAccountRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_user_id(self, user_id: str) -> list[AccountEntity]:
        stmt = select(AccountModel).where(AccountModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return [AccountMapper.to_entity(m) for m in result.scalars().all()]

    @override
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> AccountEntity | None:
        stmt = (
            select(AccountModel)
            .where(AccountModel.provider == provider)
            .where(AccountModel.open_id == open_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AccountMapper.to_entity(model) if model else None

    @override
    async def find_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> AccountEntity | None:
        stmt = (
            select(AccountModel)
            .where(AccountModel.user_id == user_id)
            .where(AccountModel.provider == provider)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AccountMapper.to_entity(model) if model else None

    @override
    async def save(self, account: AccountEntity) -> None:
        model = AccountMapper.to_model(account)
        model.id = account.id
        await self._session.merge(model)

    @override
    async def delete(self, account_id: str) -> None:
        model = await self._session.get(AccountModel, account_id)
        if model:
            await self._session.delete(model)
