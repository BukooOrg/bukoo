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


@dataclass(frozen=True)
class MarkNotificationAsReadCommand:
    user_id: str
    notification_id: str
    is_admin: bool


@dataclass(frozen=True)
class MarkAllNotificationsAsReadCommand:
    user_id: str
    is_admin: bool
    target_user_id: str | None = None


# results
@dataclass(frozen=True)
class BaseNotificationItem:
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


@dataclass(frozen=True)
class MarkNotificationResult(BaseNotificationItem):
    pass


@dataclass(frozen=True)
class MarkAllNotificationsAsReadResult:
    marked_count: int
