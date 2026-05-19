from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import ColumnElement, and_, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import NotificationEntity
from app.domain.repositories import INotificationRepository
from app.domain.repositories.notification_repository import NotificationFilters
from app.infrastructure.db.mappers import NotificationMapper
from app.infrastructure.db.models.notification_model import NotificationModel


class NotificationRepositoryImpl(INotificationRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "created_at": NotificationModel.created_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, notification: NotificationEntity) -> None:
        model = NotificationMapper.to_model(notification)
        await self._session.merge(model)

    @override
    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        conditions: list[ColumnElement[bool]] = []

        if filters.user_id is not None:
            conditions.append(NotificationModel.user_id == filters.user_id)

        if filters.is_read is True:
            conditions.append(NotificationModel.read_at.is_not(None))
        elif filters.is_read is False:
            conditions.append(NotificationModel.read_at.is_(None))

        where_clause = and_(*conditions)
        base_stmt = select(NotificationModel)

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
            order_clauses = [NotificationModel.created_at.desc()]

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
            items=[NotificationMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    @override
    async def find_by_id(self, notification_id: str) -> NotificationEntity | None:
        stmt = select(NotificationModel).where(NotificationModel.id == notification_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return NotificationMapper.to_entity(model) if model else None

    @override
    async def count_unread(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(NotificationModel)
            .where(
                and_(
                    NotificationModel.user_id == user_id,
                    NotificationModel.read_at.is_(None),
                )
            )
        )
        return (await self._session.execute(stmt)).scalar_one()

    @override
    async def mark_all_as_read_user_id(self, user_id: str) -> int:
        stmt = (
            update(NotificationModel)
            .where(
                and_(
                    NotificationModel.user_id == user_id,
                    NotificationModel.read_at.is_(None),
                )
            )
            .values(read_at=func.now())
        )
        cursor: CursorResult[Any] = await self._session.execute(stmt)  # type: ignore[assignment]
        return cursor.rowcount
