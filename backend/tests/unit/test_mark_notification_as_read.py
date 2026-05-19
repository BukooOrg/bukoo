from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.notification_dto import (
    MarkNotificationAsReadCommand,
    MarkNotificationResult,
)
from app.application.use_cases.notification.mark_notification_as_read import (
    MarkNotificationAsReadUseCase,
)
from app.core.constants import NotificationStatus
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.notification_entity import NotificationEntity
from app.domain.exceptions import NotificationNotFoundError
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
    def __init__(self, notification: NotificationEntity | None = None) -> None:
        self._notification = notification
        self.saved: NotificationEntity | None = None

    async def find_by_id(self, notification_id: str) -> NotificationEntity | None:
        if self._notification and self._notification.id == notification_id:
            return self._notification
        return None

    async def save(self, notification: NotificationEntity) -> None:
        self.saved = notification

    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        raise NotImplementedError

    async def count_unread(self, user_id: str) -> int:
        raise NotImplementedError

    async def mark_all_as_read_user_id(self, user_id: str) -> int:
        raise NotImplementedError


def _make_use_case(
    notification: NotificationEntity | None = None,
) -> tuple[MarkNotificationAsReadUseCase, AsyncMock, FakeNotificationRepository]:
    db_session = AsyncMock()
    repo = FakeNotificationRepository(notification=notification)
    use_case = MarkNotificationAsReadUseCase(
        db_session=db_session, notification_repo=repo
    )
    return use_case, db_session, repo


def _cmd(
    notification_id: str = "notif-001",
    user_id: str = "user-001",
    is_admin: bool = False,
) -> MarkNotificationAsReadCommand:
    return MarkNotificationAsReadCommand(
        notification_id=notification_id,
        user_id=user_id,
        is_admin=is_admin,
    )


@pytest.mark.unit
class TestMarkNotificationAsReadUseCase:
    async def test_marks_unread_notification_as_read(self) -> None:
        notification = _make_notification(read_at=None)
        use_case, _, _ = _make_use_case(notification=notification)

        result = await use_case.execute(_cmd())

        assert isinstance(result, MarkNotificationResult)
        assert result.is_read is True
        assert result.read_at is not None

    async def test_idempotent_when_already_read(self) -> None:
        already_read_at = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
        notification = _make_notification(read_at=already_read_at)
        use_case, db_session, repo = _make_use_case(notification=notification)

        result = await use_case.execute(_cmd())

        assert result.is_read is True
        assert result.read_at == already_read_at
        db_session.commit.assert_not_called()
        assert repo.saved is None

    async def test_raises_not_found_when_notification_missing(self) -> None:
        use_case, _, _ = _make_use_case(notification=None)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(notification_id="does-not-exist"))

    async def test_raises_not_found_for_other_users_notification_when_not_admin(
        self,
    ) -> None:
        notification = _make_notification(user_id="user-999")
        use_case, _, _ = _make_use_case(notification=notification)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(user_id="user-001", is_admin=False))

    async def test_admin_can_mark_other_users_notification_as_read(self) -> None:
        notification = _make_notification(user_id="user-999", read_at=None)
        use_case, _, _ = _make_use_case(notification=notification)

        result = await use_case.execute(_cmd(user_id="admin-001", is_admin=True))

        assert result.is_read is True
        assert result.read_at is not None

    async def test_commit_called_exactly_once_on_mutation(self) -> None:
        notification = _make_notification(read_at=None)
        use_case, db_session, _ = _make_use_case(notification=notification)

        await use_case.execute(_cmd())

        db_session.commit.assert_awaited_once()

    async def test_commit_not_called_when_already_read(self) -> None:
        notification = _make_notification(read_at=datetime.now(UTC))
        use_case, db_session, _ = _make_use_case(notification=notification)

        await use_case.execute(_cmd())

        db_session.commit.assert_not_called()
