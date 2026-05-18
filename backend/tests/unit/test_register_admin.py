from __future__ import annotations

from datetime import date
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import RegisterAdminCommand, RegisterAdminResult
from app.application.interfaces.password_hasher import IPasswordHasher
from app.application.use_cases.user.register_admin import RegisterAdminUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.account_entity import AccountEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository


class FakeUserRepository(IUserRepository):
    def __init__(self, email_exists: bool = False) -> None:
        self._email_exists = email_exists
        self.saved: list[UserEntity] = []

    @override
    async def exists_by_email(self, email: str) -> bool:
        return self._email_exists

    @override
    async def save(self, user: UserEntity) -> None:
        self.saved.append(user)

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def count_including_deleted(self) -> int:
        return 0

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


class FakeAccountRepository(IAccountRepository):
    def __init__(self) -> None:
        self.saved: list[AccountEntity] = []

    @override
    async def find_by_user_id(self, user_id: str) -> list[AccountEntity]:
        return []

    @override
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> AccountEntity | None:
        return None

    @override
    async def find_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> AccountEntity | None:
        return None

    @override
    async def save(self, account: AccountEntity) -> None:
        self.saved.append(account)

    @override
    async def delete(self, account_id: str) -> None:
        pass


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


def _make_valid_command(**overrides: object) -> RegisterAdminCommand:
    defaults: dict[str, object] = {
        "email": "admin@example.com",
        "password": "Admin@12345",
        "full_name": "Jane Admin",
        "date_of_birth": date(1990, 5, 15),
    }
    defaults.update(overrides)
    return RegisterAdminCommand(**defaults)  # type: ignore[arg-type]


@pytest.mark.unit
class TestRegisterAdminUseCase:
    async def test_returns_admin_result_with_correct_role_and_status(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()
        hasher = FakePasswordHasher()

        use_case = RegisterAdminUseCase(
            db_session=db_session,
            user_repo=user_repo,
            account_repo=account_repo,
            hasher=hasher,
        )
        result = await use_case.execute(_make_valid_command())

        assert isinstance(result, RegisterAdminResult)
        assert result.role == UserRole.ADMIN
        assert result.status == UserStatus.ACTIVE
        assert result.email == "admin@example.com"
        assert result.full_name == "Jane Admin"
        assert result.have_password is True
        db_session.commit.assert_called_once()

    async def test_raises_user_already_exists_when_email_taken(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository(email_exists=True)
        account_repo = FakeAccountRepository()
        hasher = FakePasswordHasher()

        use_case = RegisterAdminUseCase(
            db_session=db_session,
            user_repo=user_repo,
            account_repo=account_repo,
            hasher=hasher,
        )

        with pytest.raises(UserAlreadyExistsError):
            await use_case.execute(_make_valid_command())

    async def test_accepts_none_date_of_birth(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()
        hasher = FakePasswordHasher()

        use_case = RegisterAdminUseCase(
            db_session=db_session,
            user_repo=user_repo,
            account_repo=account_repo,
            hasher=hasher,
        )
        result = await use_case.execute(_make_valid_command(date_of_birth=None))

        assert result.date_of_birth is None

    async def test_generates_distinct_ids_for_user_and_account(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()
        hasher = FakePasswordHasher()

        use_case = RegisterAdminUseCase(
            db_session=db_session,
            user_repo=user_repo,
            account_repo=account_repo,
            hasher=hasher,
        )
        result = await use_case.execute(_make_valid_command())

        assert len(user_repo.saved) == 1
        assert len(account_repo.saved) == 1
        assert user_repo.saved[0].id != account_repo.saved[0].id
        assert result.id == user_repo.saved[0].id
