from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification_dto import (
    MarkAllNotificationsAsReadCommand,
    MarkAllNotificationsAsReadResult,
)
from app.domain.exceptions import AdminRoleRequiredError, UserNotFoundError
from app.domain.repositories import INotificationRepository, IUserRepository

from ..base import BaseUseCase


class MarkAllNotificationsAsReadUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        notification_repo: INotificationRepository,
        user_repo: IUserRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._notification_repo = notification_repo
        self._user_repo = user_repo

    @override
    async def execute(
        self, cmd: MarkAllNotificationsAsReadCommand
    ) -> MarkAllNotificationsAsReadResult:
        if cmd.target_user_id is not None:
            if not cmd.is_admin:
                raise AdminRoleRequiredError("mark all notifications as read")
            user = await self._user_repo.find_by_id(cmd.target_user_id)
            if user is None:
                raise UserNotFoundError(cmd.target_user_id)

        effective_user_id = cmd.target_user_id if cmd.target_user_id else cmd.user_id
        marked_count = await self._notification_repo.mark_all_as_read_user_id(
            user_id=effective_user_id
        )
        await self._db_session.commit()

        return MarkAllNotificationsAsReadResult(marked_count=marked_count)
