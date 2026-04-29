"""
SQLAlchemy async implementation of IUserRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.db.mappers.user_mapper import UserMapper
from app.infrastructure.db.models.user_model import UserModel


class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        """Returns None for soft-deleted records."""
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_entity(model) if model else None

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        """Returns the record even if soft-deleted. Useful for admin operations."""
        model = await self._session.get(UserModel, user_id)
        return UserMapper.to_entity(model) if model else None

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        """Returns None for soft-deleted records."""
        stmt = (
            select(UserModel)
            .where(UserModel.email == email)
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_entity(model) if model else None

    @override
    async def save(self, user: UserEntity) -> None:
        """
        Upsert. If the entity already has an id that exists in the DB,
        merge updates it. If the id is new, merge inserts it.
        """
        model = UserMapper.to_model(user)
        # Carry the id across — MappedAsDataclass sets it via default_factory,
        # but when we reconstruct from entity we must preserve the existing id.
        model.id = user.id
        model.deleted_at = user.deleted_at
        await self._session.merge(model)

    @override
    async def soft_delete(self, user_id: str) -> None:
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(UTC)

    @override
    async def exists_by_email(self, email: str) -> bool:
        stmt = (
            select(UserModel.id)
            .where(UserModel.email == email)
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def count_including_deleted(self) -> int:
        stmt = select(func.count()).select_from(UserModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()
