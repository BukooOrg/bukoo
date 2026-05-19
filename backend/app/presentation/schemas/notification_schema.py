from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.application.dtos.notification_dto import FindNotificationsCommand
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.presentation.schemas.list_schema import ListQueryRequest


# requests
class NotificationListQueryRequest(ListQueryRequest):
    is_read: bool | None = None

    def to_command(self, user_id: str) -> FindNotificationsCommand:
        return FindNotificationsCommand(
            query_params=QueryParams(
                page=PageParams(page=self.page, page_size=self.page_size),
                sorts=parse_sort(self.sort),
                search=self.search,
            ),
            user_id=user_id,
            is_read=self.is_read,
        )


# responses
class UnreadNotificationCountResponse(BaseModel):
    unread_count: int


class NotificationItemResponse(BaseModel):
    id: str
    user_id: str | None
    type: str
    subject: str
    body: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
