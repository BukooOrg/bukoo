from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification_dto import (
    GetUnreadNotificationCountCommand,
    GetUnreadNotificationCountResult,
)
from app.domain.repositories import INotificationRepository

from ..base import BaseUseCase


class GetUnreadNotificationCountUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        notification_repo: INotificationRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._notification_repo = notification_repo

    @override
    async def execute(
        self, cmd: GetUnreadNotificationCountCommand
    ) -> GetUnreadNotificationCountResult:
        count = await self._notification_repo.count_unread(user_id=cmd.user_id)
        return GetUnreadNotificationCountResult(unread_count=count)
