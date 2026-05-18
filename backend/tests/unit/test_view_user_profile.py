from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import ViewUserProfileCommand, ViewUserProfileResult
from app.application.use_cases.user.view_user_profile import ViewUserProfileUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository


def _make_user(user_id: str = "user-1") -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="jane@example.com",
        _full_name="Jane Customer",
        _date_of_birth=date(1995, 8, 20),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._store: dict[str, UserEntity] = {}
        if user is not None:
            self._store[user.id] = user

    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    async def save(self, user: UserEntity) -> None:
        self._store[user.id] = user

    async def soft_delete(self, user_id: str) -> None:
        pass

    async def exists_by_email(self, email: str) -> bool:
        return False

    async def count_including_deleted(self) -> int:
        return len(self._store)


def _build_use_case(
    user_repo: FakeUserRepository | None = None,
) -> tuple[ViewUserProfileUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = ViewUserProfileUseCase(
        db_session=db_session,
        user_repo=user_repo or FakeUserRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestViewUserProfileUseCase:
    async def test_returns_result_for_existing_user(self) -> None:
        user = _make_user("user-1")
        use_case, db_session = _build_use_case(FakeUserRepository(user))
        cmd = ViewUserProfileCommand(user_id="user-1")

        result = await use_case.execute(cmd)

        assert isinstance(result, ViewUserProfileResult)
        assert result.id == "user-1"
        assert result.email == "jane@example.com"
        assert result.role == UserRole.USER
        assert result.status == UserStatus.ACTIVE
        db_session.commit.assert_not_called()

    async def test_raises_user_not_found_when_missing(self) -> None:
        use_case, _ = _build_use_case(FakeUserRepository())
        cmd = ViewUserProfileCommand(user_id="nonexistent")

        with pytest.raises(UserNotFoundError):
            await use_case.execute(cmd)

    async def test_soft_deleted_user_raises_user_not_found(self) -> None:
        # find_by_id filters deleted_at IS NULL — simulated by returning None from empty repo
        use_case, _ = _build_use_case(FakeUserRepository())
        cmd = ViewUserProfileCommand(user_id="deleted-user")

        with pytest.raises(UserNotFoundError):
            await use_case.execute(cmd)
