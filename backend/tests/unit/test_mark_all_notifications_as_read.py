from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.notification_dto import (
    MarkAllNotificationsAsReadCommand,
    MarkAllNotificationsAsReadResult,
)
from app.application.use_cases.notification.mark_all_notifications_as_read import (
    MarkAllNotificationsAsReadUseCase,
)
from app.core.constants import UserRole, UserStatus
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.notification_entity import NotificationEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import AdminRoleRequiredError, UserNotFoundError
from app.domain.repositories import INotificationRepository, IUserRepository
from app.domain.repositories.notification_repository import NotificationFilters
from app.domain.repositories.user_repository import UserFilters


def _make_user(user_id: str = "user-001") -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="reader@example.com",
        _full_name="Test User",
        _date_of_birth=date(1990, 1, 1),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password=None,
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeNotificationRepository(INotificationRepository):
    def __init__(self, marked_count: int = 3) -> None:
        self._marked_count = marked_count

    async def save(self, notification: NotificationEntity) -> None:
        raise NotImplementedError

    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        raise NotImplementedError

    async def find_by_id(self, notification_id: str) -> NotificationEntity | None:
        raise NotImplementedError

    async def count_unread(self, user_id: str) -> int:
        raise NotImplementedError

    async def mark_all_as_read_user_id(self, user_id: str) -> int:
        return self._marked_count

    async def delete(self, notification_id: str) -> None:
        raise NotImplementedError


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user

    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._user

    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        raise NotImplementedError

    async def find_by_email(self, email: str) -> UserEntity | None:
        raise NotImplementedError

    async def save(self, user: UserEntity) -> None:
        raise NotImplementedError

    async def soft_delete(self, user_id: str) -> None:
        raise NotImplementedError

    async def exists_by_email(self, email: str) -> bool:
        raise NotImplementedError

    async def count_including_deleted(self) -> int:
        raise NotImplementedError

    async def find_all(
        self, query: QueryParams, filters: UserFilters
    ) -> PaginatedResult[UserEntity]:
        raise NotImplementedError


def _make_use_case(
    marked_count: int = 3,
    user: UserEntity | None = None,
) -> tuple[MarkAllNotificationsAsReadUseCase, AsyncMock]:
    db_session = AsyncMock()
    notification_repo = FakeNotificationRepository(marked_count=marked_count)
    user_repo = FakeUserRepository(user=user)
    use_case = MarkAllNotificationsAsReadUseCase(
        db_session=db_session,
        notification_repo=notification_repo,
        user_repo=user_repo,
    )
    return use_case, db_session


def _cmd(
    user_id: str = "user-001",
    is_admin: bool = False,
    target_user_id: str | None = None,
) -> MarkAllNotificationsAsReadCommand:
    return MarkAllNotificationsAsReadCommand(
        user_id=user_id,
        is_admin=is_admin,
        target_user_id=target_user_id,
    )


@pytest.mark.unit
class TestMarkAllNotificationsAsReadUseCase:
    async def test_marks_own_notifications_and_returns_count(self) -> None:
        use_case, db_session = _make_use_case(marked_count=5)

        result = await use_case.execute(_cmd(user_id="user-001"))

        assert isinstance(result, MarkAllNotificationsAsReadResult)
        assert result.marked_count == 5
        db_session.commit.assert_awaited_once()

    async def test_admin_marks_target_user_notifications(self) -> None:
        target = _make_user(user_id="user-999")
        use_case, db_session = _make_use_case(marked_count=3, user=target)

        result = await use_case.execute(
            _cmd(user_id="admin-001", is_admin=True, target_user_id=target.id)
        )

        assert result.marked_count == 3
        db_session.commit.assert_awaited_once()

    async def test_commit_called_once_when_no_unread(self) -> None:
        use_case, db_session = _make_use_case(marked_count=0)

        result = await use_case.execute(_cmd())

        assert result.marked_count == 0
        db_session.commit.assert_awaited_once()

    async def test_raises_permission_denied_when_non_admin_supplies_target_user_id(
        self,
    ) -> None:
        use_case, _ = _make_use_case()

        with pytest.raises(AdminRoleRequiredError):
            await use_case.execute(
                _cmd(user_id="user-001", is_admin=False, target_user_id="user-999")
            )

    async def test_raises_user_not_found_when_admin_target_does_not_exist(
        self,
    ) -> None:
        use_case, _ = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                _cmd(user_id="admin-001", is_admin=True, target_user_id="ghost-user")
            )

    async def test_admin_without_target_user_id_marks_own_notifications(
        self,
    ) -> None:
        use_case, db_session = _make_use_case(marked_count=2)

        result = await use_case.execute(_cmd(user_id="admin-001", is_admin=True))

        assert result.marked_count == 2
        db_session.commit.assert_awaited_once()
