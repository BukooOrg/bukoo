from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.notification_dto import (
    GetUnreadNotificationCountCommand,
    GetUnreadNotificationCountResult,
)
from app.application.use_cases.notification.get_unread_notification_count import (
    GetUnreadNotificationCountUseCase,
)
from app.core.constants import NotificationStatus
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.notification_entity import NotificationEntity
from app.domain.repositories import INotificationRepository
from app.domain.repositories.notification_repository import NotificationFilters


def _make_notification(
    notification_id: str = "notif-001",
    user_id: str = "user-001",
    read_at: datetime | None = None,
) -> NotificationEntity:
    now = datetime.now(UTC)
    return NotificationEntity(
        _id=notification_id,
        _type="payment_success",
        _subject="Payment Confirmed",
        _body="Your payment has been confirmed.",
        _status=NotificationStatus.PENDING,
        _created_at=now,
        _sent_at=None,
        _user_id=user_id,
        _read_at=read_at,
    )


class FakeNotificationRepository(INotificationRepository):
    def __init__(self, notifications: list[NotificationEntity] | None = None) -> None:
        self._notifications = notifications or []

    async def save(self, notification: NotificationEntity) -> None:
        raise NotImplementedError

    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        raise NotImplementedError

    async def count_unread(self, user_id: str) -> int:
        return sum(
            1 for n in self._notifications if n.user_id == user_id and n.read_at is None
        )


def _make_use_case(
    notifications: list[NotificationEntity] | None = None,
) -> tuple[GetUnreadNotificationCountUseCase, AsyncMock]:
    db_session = AsyncMock()
    repo = FakeNotificationRepository(notifications=notifications)
    use_case = GetUnreadNotificationCountUseCase(
        db_session=db_session, notification_repo=repo
    )
    return use_case, db_session


@pytest.mark.unit
class TestGetUnreadNotificationCountUseCase:
    async def test_returns_unread_count_for_user(self) -> None:
        notifications = [
            _make_notification("n-001", read_at=None),
            _make_notification("n-002", read_at=None),
            _make_notification("n-003", read_at=datetime.now(UTC)),
        ]
        use_case, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(
            GetUnreadNotificationCountCommand(user_id="user-001")
        )

        assert isinstance(result, GetUnreadNotificationCountResult)
        assert result.unread_count == 2

    async def test_returns_zero_when_user_has_no_notifications(self) -> None:
        use_case, _ = _make_use_case(notifications=[])

        result = await use_case.execute(
            GetUnreadNotificationCountCommand(user_id="user-001")
        )

        assert result.unread_count == 0

    async def test_returns_zero_when_all_notifications_are_read(self) -> None:
        read_at = datetime.now(UTC)
        notifications = [
            _make_notification("n-001", read_at=read_at),
            _make_notification("n-002", read_at=read_at),
        ]
        use_case, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(
            GetUnreadNotificationCountCommand(user_id="user-001")
        )

        assert result.unread_count == 0

    async def test_does_not_count_other_users_notifications(self) -> None:
        notifications = [
            _make_notification("n-001", user_id="user-001", read_at=None),
            _make_notification("n-002", user_id="user-002", read_at=None),
            _make_notification("n-003", user_id="user-002", read_at=None),
        ]
        use_case, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(
            GetUnreadNotificationCountCommand(user_id="user-001")
        )

        assert result.unread_count == 1
