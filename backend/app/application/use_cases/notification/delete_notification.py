from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification_dto import (
    DeleteNotificationCommand,
)
from app.domain.exceptions import NotificationNotFoundError
from app.domain.repositories import INotificationRepository

from ..base import BaseUseCase


class DeleteNotificationUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        notification_repo: INotificationRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._notification_repo = notification_repo

    @override
    async def execute(self, cmd: DeleteNotificationCommand) -> None:
        notification = await self._notification_repo.find_by_id(cmd.notification_id)
        if notification is None:
            raise NotificationNotFoundError(cmd.notification_id)

        # security: this deliberately treats unauthorized access as "not found" to avoid revealing the existence of other users' notifications.
        if not cmd.is_admin and cmd.user_id != notification.user_id:
            raise NotificationNotFoundError(cmd.notification_id)

        await self._notification_repo.delete(cmd.notification_id)
        await self._db_session.commit()
