from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.query_params import QueryParams


# commands
@dataclass(frozen=True)
class FindNotificationsCommand:
    user_id: str
    query_params: QueryParams
    is_read: bool | None = None


@dataclass(frozen=True)
class GetUnreadNotificationCountCommand:
    user_id: str


# results
@dataclass(frozen=True)
class NotificationItem:
    id: str
    user_id: str | None
    type: str
    subject: str
    body: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class GetUnreadNotificationCountResult:
    unread_count: int
