from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import SuspendUserCommand, SuspendUserResult
from app.application.use_cases.user.suspend_user import SuspendUserUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.exceptions.user import (
    CannotSuspendAdminError,
    UserAlreadySuspendedError,
)
from app.domain.repositories.user_repository import IUserRepository

_USER_ID = "user-id-1"
_ADMIN_ID = "admin-id-1"


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._store: dict[str, UserEntity] = {}
        if user is not None:
            self._store[user.id] = user
        self.saved: list[UserEntity] = []

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    @override
    async def save(self, user: UserEntity) -> None:
        self._store[user.id] = user
        self.saved.append(user)

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def exists_by_email(self, email: str) -> bool:
        return False

    @override
    async def count_including_deleted(self) -> int:
        return 0

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


def _make_user(
    user_id: str = _USER_ID,
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="reader@example.com",
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=role,
        _status=status,
        _hashed_password="hashed:secret",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_use_case(
    user: UserEntity | None,
    db_session: AsyncMock | None = None,
) -> SuspendUserUseCase:
    if db_session is None:
        db_session = AsyncMock()
    return SuspendUserUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
    )


@pytest.mark.unit
class TestSuspendUserUseCase:
    async def test_returns_suspended_result(self) -> None:
        use_case = _make_use_case(user=_make_user())

        result = await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        assert isinstance(result, SuspendUserResult)
        assert result.status == UserStatus.SUSPENDED
        assert result.id == _USER_ID

    async def test_user_entity_status_is_suspended(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = SuspendUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        assert user.status == UserStatus.SUSPENDED

    async def test_updated_at_changes_after_suspend(self) -> None:
        user = _make_user()
        original_updated_at = user.updated_at
        use_case = _make_use_case(user=user)

        result = await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        assert result.updated_at >= original_updated_at

    async def test_save_called_once_on_success(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = SuspendUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        assert len(user_repo.saved) == 1

    async def test_db_session_committed_once(self) -> None:
        db_session = AsyncMock()
        use_case = _make_use_case(user=_make_user(), db_session=db_session)

        await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        use_case = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

    async def test_raises_user_already_suspended(self) -> None:
        use_case = _make_use_case(user=_make_user(status=UserStatus.SUSPENDED))

        with pytest.raises(UserAlreadySuspendedError):
            await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

    async def test_raises_cannot_suspend_admin(self) -> None:
        use_case = _make_use_case(
            user=_make_user(user_id=_ADMIN_ID, role=UserRole.ADMIN)
        )

        with pytest.raises(CannotSuspendAdminError):
            await use_case.execute(SuspendUserCommand(user_id=_ADMIN_ID))

    async def test_save_not_called_when_exception_raised(self) -> None:
        user = _make_user(status=UserStatus.SUSPENDED)
        user_repo = FakeUserRepository(user=user)
        use_case = SuspendUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        with pytest.raises(UserAlreadySuspendedError):
            await use_case.execute(SuspendUserCommand(user_id=_USER_ID))

        assert len(user_repo.saved) == 0
