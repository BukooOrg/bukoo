from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.notification_dto import (
    FindNotificationsCommand,
    NotificationItem,
)
from app.application.use_cases.notification.find_notifications import (
    FindNotificationsUseCase,
)
from app.core.constants import NotificationStatus
from app.core.query_params import PageParams, PaginatedResult, QueryParams
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


def _default_query() -> QueryParams:
    return QueryParams(page=PageParams(page=1, page_size=10))


class FakeNotificationRepository(INotificationRepository):
    def __init__(self, notifications: list[NotificationEntity] | None = None) -> None:
        self._notifications = notifications or []
        self.last_filters: NotificationFilters | None = None

    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        self.last_filters = filters
        items = self._notifications
        if filters.user_id is not None:
            items = [n for n in items if n.user_id == filters.user_id]
        if filters.is_read is True:
            items = [n for n in items if n.read_at is not None]
        elif filters.is_read is False:
            items = [n for n in items if n.read_at is None]
        page = query.page.page
        page_size = query.page.page_size
        offset = (page - 1) * page_size
        paged = items[offset : offset + page_size]
        return PaginatedResult(
            items=paged,
            total_items=len(items),
            page=page,
            page_size=page_size,
        )

    async def save(self, notification: NotificationEntity) -> None:
        raise NotImplementedError


def _make_use_case(
    notifications: list[NotificationEntity] | None = None,
) -> tuple[FindNotificationsUseCase, AsyncMock, FakeNotificationRepository]:
    db_session = AsyncMock()
    repo = FakeNotificationRepository(notifications=notifications)
    use_case = FindNotificationsUseCase(db_session=db_session, notification_repo=repo)
    return use_case, db_session, repo


def _cmd(
    user_id: str = "user-001",
    is_read: bool | None = None,
) -> FindNotificationsCommand:
    return FindNotificationsCommand(
        user_id=user_id,
        query_params=_default_query(),
        is_read=is_read,
    )


@pytest.mark.unit
class TestFindNotificationsUseCase:
    async def test_returns_all_notifications_for_user(self) -> None:
        notifications = [
            _make_notification("n-001"),
            _make_notification("n-002"),
        ]
        use_case, _, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(_cmd())

        assert result.total_items == 2
        assert len(result.items) == 2
        assert all(isinstance(item, NotificationItem) for item in result.items)

    async def test_returns_only_unread_when_is_read_false(self) -> None:
        notifications = [
            _make_notification("n-001", read_at=None),
            _make_notification("n-002", read_at=datetime.now(UTC)),
            _make_notification("n-003", read_at=None),
        ]
        use_case, _, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(_cmd(is_read=False))

        assert result.total_items == 2
        assert all(item.is_read is False for item in result.items)
        assert all(item.read_at is None for item in result.items)

    async def test_returns_only_read_when_is_read_true(self) -> None:
        read_at = datetime.now(UTC)
        notifications = [
            _make_notification("n-001", read_at=None),
            _make_notification("n-002", read_at=read_at),
        ]
        use_case, _, _ = _make_use_case(notifications=notifications)

        result = await use_case.execute(_cmd(is_read=True))

        assert result.total_items == 1
        assert result.items[0].is_read is True
        assert result.items[0].read_at == read_at

    async def test_returns_empty_when_user_has_no_notifications(self) -> None:
        use_case, _, _ = _make_use_case(notifications=[])

        result = await use_case.execute(_cmd())

        assert result.total_items == 0
        assert result.items == []

    async def test_does_not_return_other_users_notifications(self) -> None:
        notifications = [
            _make_notification("n-001", user_id="user-001"),
            _make_notification("n-002", user_id="user-002"),
        ]
        use_case, _, repo = _make_use_case(notifications=notifications)

        result = await use_case.execute(_cmd(user_id="user-001"))

        assert result.total_items == 1
        assert repo.last_filters is not None
        assert repo.last_filters.user_id == "user-001"

    async def test_maps_entity_fields_to_notification_item(self) -> None:
        read_at = datetime.now(UTC)
        notification = _make_notification("n-001", user_id="user-001", read_at=read_at)
        use_case, _, _ = _make_use_case(notifications=[notification])

        result = await use_case.execute(_cmd())

        item = result.items[0]
        assert item.id == "n-001"
        assert item.user_id == "user-001"
        assert item.type == "payment_success"
        assert item.subject == "Payment Confirmed"
        assert item.is_read is True
        assert item.read_at == read_at
