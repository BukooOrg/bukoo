"""
SQLAlchemy async implementation of IUserRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar, override

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.user_entity import UserEntity
from app.domain.repositories.user_repository import IUserRepository, UserFilters
from app.infrastructure.db.mappers.user_mapper import UserMapper
from app.infrastructure.db.models.user_model import UserModel


class UserRepositoryImpl(IUserRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "full_name": UserModel.full_name,
        "email": UserModel.email,
        "created_at": UserModel.created_at,
        "updated_at": UserModel.updated_at,
        "last_login_at": UserModel.last_login_at,
    }

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

    @override
    async def find_all(
        self, query: QueryParams, filters: UserFilters
    ) -> PaginatedResult[UserEntity]:
        conditions: list[ColumnElement[bool]] = [UserModel.deleted_at.is_(None)]

        if filters.role is not None:
            conditions.append(UserModel.role == filters.role)
        if filters.status is not None:
            conditions.append(UserModel.status == filters.status)
        if query.search:
            conditions.append(
                or_(
                    UserModel.full_name.ilike(f"%{query.search}%"),
                    UserModel.email.ilike(f"%{query.search}%"),
                )
            )

        where_clause = and_(*conditions)
        base_stmt = select(UserModel)

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(
                    base_stmt.where(where_clause).subquery()
                )
            )
        ).scalar_one()

        order_clauses = [
            self.SORTABLE_FIELDS[s.field].asc()
            if s.direction == "asc"
            else self.SORTABLE_FIELDS[s.field].desc()
            for s in query.sorts
            if s.field in self.SORTABLE_FIELDS
        ]
        if not order_clauses:
            order_clauses = [UserModel.created_at.desc()]

        models = (
            (
                await self._session.execute(
                    base_stmt.where(where_clause)
                    .order_by(*order_clauses)
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[UserMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )
