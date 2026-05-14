from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import NotificationEntity
from app.domain.repositories import INotificationRepository
from app.infrastructure.db.mappers import NotificationMapper


class NotificationRepositoryImpl(INotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, notification: NotificationEntity) -> None:
        model = NotificationMapper.to_model(notification)
        await self._session.merge(model)
