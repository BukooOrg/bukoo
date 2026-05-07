from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import ChangePasswordCommand, ChangePasswordResult
from app.application.interfaces import IPasswordHasher
from app.application.use_cases.user.change_password import ChangePasswordUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import (
    CurrentPasswordIncorrectError,
    NewPasswordSameAsCurrentError,
    PasswordNotSetError,
)
from app.domain.repositories.user_repository import IUserRepository


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user
        self.saved: list[UserEntity] = []

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        if self._user and self._user.id == user_id:
            return self._user
        return None

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    @override
    async def save(self, user: UserEntity) -> None:
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


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


_USER_ID = "user-id-1"
_CURRENT_PASSWORD = "OldP@ssw0rd!"
_NEW_PASSWORD = "N3wSecur3P@ss!"


def _make_user(
    hashed_password: str | None = f"hashed:{_CURRENT_PASSWORD}",
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=_USER_ID,
        _email="reader@example.com",
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
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
) -> ChangePasswordUseCase:
    if db_session is None:
        db_session = AsyncMock()
    return ChangePasswordUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        hasher=FakePasswordHasher(),
    )


def _cmd(
    current_password: str = _CURRENT_PASSWORD,
    new_password: str = _NEW_PASSWORD,
) -> ChangePasswordCommand:
    return ChangePasswordCommand(
        user_id=_USER_ID,
        current_password=current_password,
        new_password=new_password,
    )


@pytest.mark.unit
class TestChangePasswordUseCase:
    async def test_returns_success_message(self) -> None:
        use_case = _make_use_case(user=_make_user())

        result = await use_case.execute(_cmd())

        assert isinstance(result, ChangePasswordResult)
        assert result.message == "Password changed successfully."

    async def test_password_is_updated_with_hashed_value(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = ChangePasswordUseCase(
            db_session=AsyncMock(),
            user_repo=user_repo,
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(_cmd())

        assert user.hashed_password == f"hashed:{_NEW_PASSWORD}"
        assert len(user_repo.saved) == 1

    async def test_db_session_committed_once(self) -> None:
        db_session = AsyncMock()
        use_case = _make_use_case(user=_make_user(), db_session=db_session)

        await use_case.execute(_cmd())

        db_session.commit.assert_called_once()

    async def test_raises_password_not_set_for_oauth_only_user(self) -> None:
        use_case = _make_use_case(user=_make_user(hashed_password=None))

        with pytest.raises(PasswordNotSetError):
            await use_case.execute(_cmd())

    async def test_raises_new_password_same_as_current(self) -> None:
        use_case = _make_use_case(user=_make_user())

        with pytest.raises(NewPasswordSameAsCurrentError):
            await use_case.execute(
                _cmd(current_password=_CURRENT_PASSWORD, new_password=_CURRENT_PASSWORD)
            )

    async def test_raises_current_password_incorrect(self) -> None:
        use_case = _make_use_case(user=_make_user())

        with pytest.raises(CurrentPasswordIncorrectError):
            await use_case.execute(_cmd(current_password="Wr0ngP@ssword!"))

    async def test_save_called_before_commit(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        db_session = AsyncMock()

        call_order: list[str] = []
        original_save = user_repo.save
        original_commit = db_session.commit

        async def tracked_save(user: UserEntity) -> None:
            call_order.append("save")
            await original_save(user)

        async def tracked_commit() -> None:
            call_order.append("commit")
            await original_commit()

        user_repo.save = tracked_save
        db_session.commit = tracked_commit

        use_case = ChangePasswordUseCase(
            db_session=db_session,
            user_repo=user_repo,
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(_cmd())

        assert call_order.index("save") < call_order.index("commit")
