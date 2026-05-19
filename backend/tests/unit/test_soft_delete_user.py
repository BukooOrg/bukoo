from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import SoftDeleteUserCommand, SoftDeleteUserResult
from app.application.use_cases.user.soft_delete_user import SoftDeleteUserUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.exceptions.user import CannotDeleteSelfError, CannotSoftDeleteAdminError
from app.domain.repositories.user_repository import IUserRepository

_USER_ID = "user-id-1"
_ADMIN_ID = "admin-id-1"
_ACTOR_ID = "actor-id-1"


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
) -> SoftDeleteUserUseCase:
    if db_session is None:
        db_session = AsyncMock()
    return SoftDeleteUserUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
    )


@pytest.mark.unit
class TestSoftDeleteUserUseCase:
    async def test_returns_deleted_result(self) -> None:
        use_case = _make_use_case(user=_make_user())

        result = await use_case.execute(
            SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
        )

        assert isinstance(result, SoftDeleteUserResult)
        assert result.message == "User account has been deleted."

    async def test_user_entity_deleted_at_is_set(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = SoftDeleteUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        await use_case.execute(
            SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
        )

        assert user.deleted_at is not None

    async def test_save_called_once_on_success(self) -> None:
        user = _make_user()
        user_repo = FakeUserRepository(user=user)
        use_case = SoftDeleteUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        await use_case.execute(
            SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
        )

        assert len(user_repo.saved) == 1

    async def test_db_session_committed_once(self) -> None:
        db_session = AsyncMock()
        use_case = _make_use_case(user=_make_user(), db_session=db_session)

        await use_case.execute(
            SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
        )

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        use_case = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
            )

    async def test_raises_cannot_soft_delete_admin(self) -> None:
        use_case = _make_use_case(
            user=_make_user(user_id=_ADMIN_ID, role=UserRole.ADMIN)
        )

        with pytest.raises(CannotSoftDeleteAdminError):
            await use_case.execute(
                SoftDeleteUserCommand(user_id=_ADMIN_ID, actor_id=_ACTOR_ID)
            )

    async def test_already_deleted_user_raises_user_not_found(self) -> None:
        # find_by_id filters deleted_at IS NULL, so deleted users return None
        use_case = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_ACTOR_ID)
            )

    async def test_save_not_called_when_exception_raised(self) -> None:
        user = _make_user(user_id=_ADMIN_ID, role=UserRole.ADMIN)
        user_repo = FakeUserRepository(user=user)
        use_case = SoftDeleteUserUseCase(db_session=AsyncMock(), user_repo=user_repo)

        with pytest.raises(CannotSoftDeleteAdminError):
            await use_case.execute(
                SoftDeleteUserCommand(user_id=_ADMIN_ID, actor_id=_ACTOR_ID)
            )

        assert len(user_repo.saved) == 0

    async def test_raises_cannot_delete_self(self) -> None:
        use_case = _make_use_case(user=_make_user(user_id=_USER_ID))

        with pytest.raises(CannotDeleteSelfError):
            await use_case.execute(
                SoftDeleteUserCommand(user_id=_USER_ID, actor_id=_USER_ID)
            )
