from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import (
    ForceSetUserPasswordCommand,
    ForceSetUserPasswordResult,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.application.use_cases.user.force_set_user_password import (
    ForceSetUserPasswordUseCase,
)
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.exceptions.user import (
    CannotResetAdminPasswordError,
    UserHasNoCredentialAccountError,
)
from app.domain.repositories.user_repository import IUserRepository

_USER_ID = "user-id-1"


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


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, plain: str) -> str:
        return f"hashed:{plain}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


def _make_user(
    user_id: str = _USER_ID,
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
    hashed_password: str | None = "hashed:existing",
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="reader@example.com",
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=role,
        _status=status,
        _hashed_password=hashed_password,
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_use_case(
    user: UserEntity | None,
    db_session: AsyncMock | None = None,
) -> ForceSetUserPasswordUseCase:
    if db_session is None:
        db_session = AsyncMock()
    return ForceSetUserPasswordUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        hasher=FakePasswordHasher(),
    )


@pytest.mark.unit
class TestForceSetUserPasswordUseCase:
    async def test_returns_success_result(self) -> None:
        use_case = _make_use_case(user=_make_user())

        result = await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        assert isinstance(result, ForceSetUserPasswordResult)
        assert result.message == "Password has been reset successfully."

    async def test_password_is_hashed_and_stored(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = ForceSetUserPasswordUseCase(
            db_session=AsyncMock(), user_repo=user_repo, hasher=FakePasswordHasher()
        )

        await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        assert user.hashed_password == "hashed:NewPass123"

    async def test_save_called_once_on_success(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = ForceSetUserPasswordUseCase(
            db_session=AsyncMock(), user_repo=user_repo, hasher=FakePasswordHasher()
        )

        await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        assert len(user_repo.saved) == 1

    async def test_db_session_committed_once(self) -> None:
        db_session = AsyncMock()
        use_case = _make_use_case(user=_make_user(), db_session=db_session)

        await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        use_case = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
            )

    async def test_raises_cannot_reset_admin_password(self) -> None:
        use_case = _make_use_case(user=_make_user(role=UserRole.ADMIN))

        with pytest.raises(CannotResetAdminPasswordError):
            await use_case.execute(
                ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
            )

    async def test_raises_user_has_no_credential_account(self) -> None:
        use_case = _make_use_case(user=_make_user(hashed_password=None))

        with pytest.raises(UserHasNoCredentialAccountError):
            await use_case.execute(
                ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
            )

    async def test_pending_user_can_have_password_reset(self) -> None:
        use_case = _make_use_case(user=_make_user(status=UserStatus.PENDING))

        result = await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        assert isinstance(result, ForceSetUserPasswordResult)

    async def test_suspended_user_can_have_password_reset(self) -> None:
        use_case = _make_use_case(user=_make_user(status=UserStatus.SUSPENDED))

        result = await use_case.execute(
            ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
        )

        assert isinstance(result, ForceSetUserPasswordResult)

    async def test_save_not_called_when_exception_raised(self) -> None:
        user = _make_user(role=UserRole.ADMIN)
        user_repo = FakeUserRepository(user=user)
        use_case = ForceSetUserPasswordUseCase(
            db_session=AsyncMock(), user_repo=user_repo, hasher=FakePasswordHasher()
        )

        with pytest.raises(CannotResetAdminPasswordError):
            await use_case.execute(
                ForceSetUserPasswordCommand(user_id=_USER_ID, new_password="NewPass123")
            )

        assert len(user_repo.saved) == 0
