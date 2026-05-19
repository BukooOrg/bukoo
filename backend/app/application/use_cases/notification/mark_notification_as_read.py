from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification_dto import (
    MarkNotificationAsReadCommand,
    MarkNotificationResult,
)
from app.domain.exceptions import NotificationNotFoundError
from app.domain.repositories import INotificationRepository

from ..base import BaseUseCase


class MarkNotificationAsReadUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        notification_repo: INotificationRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._notification_repo = notification_repo

    @override
    async def execute(
        self, cmd: MarkNotificationAsReadCommand
    ) -> MarkNotificationResult:
        notification = await self._notification_repo.find_by_id(cmd.notification_id)
        if notification is None:
            raise NotificationNotFoundError(cmd.notification_id)

        # security: this deliberately treats unauthorized access as "not found" to avoid revealing the existence of other users' notifications.
        if not cmd.is_admin and cmd.user_id != notification.user_id:
            raise NotificationNotFoundError(cmd.notification_id)

        if not notification.is_read:
            notification.mark_read()
            await self._notification_repo.save(notification)
            await self._db_session.commit()

        return MarkNotificationResult(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            subject=notification.subject,
            body=notification.body,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )
