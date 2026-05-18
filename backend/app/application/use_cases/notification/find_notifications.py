from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification_dto import (
    FindNotificationsCommand,
    NotificationItem,
)
from app.core.query_params import PaginatedResult
from app.domain.repositories import INotificationRepository
from app.domain.repositories.notification_repository import NotificationFilters

from ..base import BaseUseCase


class FindNotificationsUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        notification_repo: INotificationRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._notification_repo = notification_repo

    @override
    async def execute(
        self, cmd: FindNotificationsCommand
    ) -> PaginatedResult[NotificationItem]:
        result = await self._notification_repo.find_all(
            query=cmd.query_params,
            filters=NotificationFilters(user_id=cmd.user_id, is_read=cmd.is_read),
        )

        return PaginatedResult(
            items=[
                NotificationItem(
                    id=n.id,
                    user_id=n.user_id,
                    type=n.type,
                    subject=n.subject,
                    body=n.body,
                    is_read=n.is_read,
                    read_at=n.read_at,
                    created_at=n.created_at,
                )
                for n in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
