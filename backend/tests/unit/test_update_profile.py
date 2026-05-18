from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import UpdateProfileCommand, UpdateProfileResult
from app.application.use_cases.user.update_profile import UpdateProfileUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository


def _make_user(
    user_id: str = "user-001",
    full_name: str = "Original Name",
    date_of_birth: date | None = date(1990, 1, 1),
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="user@example.com",
        _full_name=full_name,
        _date_of_birth=date_of_birth,
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

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return next((u for u in self._store.values() if u.email == email), None)

    @override
    async def save(self, user: UserEntity) -> None:
        self._store[user.id] = user

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def exists_by_email(self, email: str) -> bool:
        return any(u.email == email for u in self._store.values())

    @override
    async def count_including_deleted(self) -> int:
        return len(self._store)

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


@pytest.mark.unit
class TestUpdateProfileUseCase:
    async def test_returns_result_with_updated_full_name(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        use_case = UpdateProfileUseCase(db_session=AsyncMock(), user_repo=repo)

        result = await use_case.execute(
            UpdateProfileCommand(
                user_id=user.id,
                full_name="New Name",
                date_of_birth=date(1990, 1, 1),
            )
        )

        assert isinstance(result, UpdateProfileResult)
        assert result.full_name == "New Name"

    async def test_returns_result_with_updated_date_of_birth(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        use_case = UpdateProfileUseCase(db_session=AsyncMock(), user_repo=repo)
        new_dob = date(1995, 6, 15)

        result = await use_case.execute(
            UpdateProfileCommand(
                user_id=user.id,
                full_name="New Name",
                date_of_birth=new_dob,
            )
        )

        assert result.date_of_birth == new_dob

    async def test_updated_at_is_bumped(self) -> None:
        user = _make_user()
        original_updated_at = user.updated_at
        repo = FakeUserRepository(user)
        use_case = UpdateProfileUseCase(db_session=AsyncMock(), user_repo=repo)

        result = await use_case.execute(
            UpdateProfileCommand(
                user_id=user.id,
                full_name="New Name",
                date_of_birth=date(1990, 1, 1),
            )
        )

        assert result.updated_at >= original_updated_at

    async def test_commit_called_once(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        db_session = AsyncMock()
        use_case = UpdateProfileUseCase(db_session=db_session, user_repo=repo)

        await use_case.execute(
            UpdateProfileCommand(
                user_id=user.id,
                full_name="New Name",
                date_of_birth=date(1990, 1, 1),
            )
        )

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        repo = FakeUserRepository()  # empty store
        use_case = UpdateProfileUseCase(db_session=AsyncMock(), user_repo=repo)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                UpdateProfileCommand(
                    user_id="nonexistent-id",
                    full_name="New Name",
                    date_of_birth=date(1990, 1, 1),
                )
            )

    async def test_date_of_birth_none_clears_field(self) -> None:
        user = _make_user(date_of_birth=date(1990, 1, 1))
        repo = FakeUserRepository(user)
        use_case = UpdateProfileUseCase(db_session=AsyncMock(), user_repo=repo)

        result = await use_case.execute(
            UpdateProfileCommand(
                user_id=user.id,
                full_name="New Name",
                date_of_birth=None,
            )
        )

        assert result.date_of_birth is None
