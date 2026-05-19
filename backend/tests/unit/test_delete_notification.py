from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.notification_dto import DeleteNotificationCommand
from app.application.use_cases.notification.delete_notification import (
    DeleteNotificationUseCase,
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
        _read_at=None,
    )


class FakeNotificationRepository(INotificationRepository):
    def __init__(self, notification: NotificationEntity | None = None) -> None:
        self._notification = notification
        self.deleted_ids: list[str] = []

    async def find_by_id(self, notification_id: str) -> NotificationEntity | None:
        if self._notification and self._notification.id == notification_id:
            return self._notification
        return None

    async def delete(self, notification_id: str) -> None:
        self.deleted_ids.append(notification_id)

    async def save(self, notification: NotificationEntity) -> None:
        raise NotImplementedError

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
) -> tuple[DeleteNotificationUseCase, AsyncMock, FakeNotificationRepository]:
    db_session = AsyncMock()
    repo = FakeNotificationRepository(notification=notification)
    use_case = DeleteNotificationUseCase(db_session=db_session, notification_repo=repo)
    return use_case, db_session, repo


def _cmd(
    notification_id: str = "notif-001",
    user_id: str = "user-001",
    is_admin: bool = False,
) -> DeleteNotificationCommand:
    return DeleteNotificationCommand(
        notification_id=notification_id,
        user_id=user_id,
        is_admin=is_admin,
    )


@pytest.mark.unit
class TestDeleteNotificationUseCase:
    async def test_returns_none_and_calls_delete_with_correct_id(self) -> None:
        notification = _make_notification()
        use_case, _, repo = _make_use_case(notification=notification)

        result = await use_case.execute(_cmd())

        assert result is None
        assert repo.deleted_ids == ["notif-001"]

    async def test_admin_can_delete_another_users_notification(self) -> None:
        notification = _make_notification(user_id="user-999")
        use_case, _, repo = _make_use_case(notification=notification)

        result = await use_case.execute(_cmd(user_id="admin-001", is_admin=True))

        assert result is None
        assert "notif-001" in repo.deleted_ids

    async def test_commit_called_exactly_once_on_success(self) -> None:
        notification = _make_notification()
        use_case, db_session, _ = _make_use_case(notification=notification)

        await use_case.execute(_cmd())

        db_session.commit.assert_awaited_once()

    async def test_raises_not_found_when_notification_missing(self) -> None:
        use_case, _, _ = _make_use_case(notification=None)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(notification_id="does-not-exist"))

    async def test_raises_not_found_when_user_does_not_own_notification(self) -> None:
        notification = _make_notification(user_id="user-999")
        use_case, _, _ = _make_use_case(notification=notification)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(user_id="user-001", is_admin=False))

    async def test_delete_not_called_when_existence_check_fails(self) -> None:
        use_case, db_session, repo = _make_use_case(notification=None)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(notification_id="does-not-exist"))

        assert repo.deleted_ids == []
        db_session.commit.assert_not_called()

    async def test_delete_not_called_when_ownership_check_fails(self) -> None:
        notification = _make_notification(user_id="user-999")
        use_case, db_session, repo = _make_use_case(notification=notification)

        with pytest.raises(NotificationNotFoundError):
            await use_case.execute(_cmd(user_id="user-001", is_admin=False))

        assert repo.deleted_ids == []
        db_session.commit.assert_not_called()
