from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import AuthResult, TokenDTO
from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.password_hasher import IPasswordHasher
from app.application.interfaces.token_service import ITokenService
from app.application.use_cases.auth.login import LoginUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import (
    InvalidCredentialsError,
    UserNotVerifiedError,
    UserSuspendedError,
)
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.credential_auth_provider import CredentialAuthProvider
from app.infrastructure.auth.credential_auth_provider_factory import (
    CredentialAuthProviderFactory,
)


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user
        self.saved: list[UserEntity] = []

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return self._user

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
    async def exists_by_email(self, email: str) -> bool:
        return self._user is not None

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

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


class FakeTokenService(ITokenService):
    @override
    def create_access_token(self, subject: str) -> str:
        return f"token-for-{subject}"

    @override
    def decode_token(self, token: str) -> dict[str, object]:
        return {}


class FakeAuthProviderFactory(IAuthProviderFactory):
    """Stub factory that always returns a fixed provider — tests factory substitutability."""

    def __init__(self, provider: IAuthProvider) -> None:
        self._provider = provider

    @override
    def create_provider(self) -> IAuthProvider:
        return self._provider


class AlwaysSucceedProvider(IAuthProvider):
    def __init__(self, user_id: str, email: str) -> None:
        self._user_id = user_id
        self._email = email

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        return AuthResult(user_id=self._user_id, email=self._email, is_new_user=False)


# helpers
def _make_user(
    status: UserStatus = UserStatus.ACTIVE,
    hashed_password: str | None = "hashed:Secure@123",
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id="user-001",
        _email="reader@example.com",
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=status,
        _hashed_password=hashed_password,
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


_VALID_PAYLOAD: dict[str, str] = {
    "email": "reader@example.com",
    "password": "Secure@123",
}


# LoginUseCase tests
@pytest.mark.unit
class TestLoginUseCase:
    async def test_returns_token_dto_on_valid_credentials(self) -> None:
        db_session = AsyncMock()
        provider = AlwaysSucceedProvider(user_id="user-001", email="reader@example.com")
        factory = FakeAuthProviderFactory(provider)
        token_svc = FakeTokenService()

        use_case = LoginUseCase(
            db_session=db_session, factory=factory, token_svc=token_svc
        )
        result = await use_case.execute(_VALID_PAYLOAD)

        assert isinstance(result, TokenDTO)
        assert result.access_token == "token-for-user-001"

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        provider = AlwaysSucceedProvider(user_id="user-001", email="reader@example.com")
        factory = FakeAuthProviderFactory(provider)
        token_svc = FakeTokenService()

        use_case = LoginUseCase(
            db_session=db_session, factory=factory, token_svc=token_svc
        )
        await use_case.execute(_VALID_PAYLOAD)

        db_session.commit.assert_called_once()

    async def test_any_auth_provider_factory_implementation_works(self) -> None:
        """Factory substitutability: LoginUseCase works with any IAuthProviderFactory."""
        db_session = AsyncMock()
        provider = AlwaysSucceedProvider(user_id="admin-001", email="admin@bukoo.my")
        factory = FakeAuthProviderFactory(provider)
        token_svc = FakeTokenService()

        use_case = LoginUseCase(
            db_session=db_session, factory=factory, token_svc=token_svc
        )
        result = await use_case.execute({"email": "admin@bukoo.my", "password": "x"})

        assert result.access_token == "token-for-admin-001"


# CredentialAuthProvider tests
@pytest.mark.unit
class TestCredentialAuthProvider:
    async def test_raises_invalid_credentials_when_user_not_found(self) -> None:
        repo = FakeUserRepository(user=None)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        with pytest.raises(InvalidCredentialsError):
            await provider.authenticate(_VALID_PAYLOAD)

    async def test_raises_invalid_credentials_when_user_has_no_password(self) -> None:
        user = _make_user(hashed_password=None)
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        with pytest.raises(InvalidCredentialsError):
            await provider.authenticate(_VALID_PAYLOAD)

    async def test_raises_invalid_credentials_when_password_mismatch(self) -> None:
        user = _make_user(hashed_password="hashed:DifferentPassword@1")
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        with pytest.raises(InvalidCredentialsError):
            await provider.authenticate(_VALID_PAYLOAD)

    async def test_raises_user_not_verified_when_status_is_pending(self) -> None:
        user = _make_user(status=UserStatus.PENDING)
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        with pytest.raises(UserNotVerifiedError):
            await provider.authenticate(_VALID_PAYLOAD)

    async def test_raises_user_suspended_when_status_is_suspended(self) -> None:
        user = _make_user(status=UserStatus.SUSPENDED)
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        with pytest.raises(UserSuspendedError):
            await provider.authenticate(_VALID_PAYLOAD)

    async def test_record_login_called_and_user_saved_on_success(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        await provider.authenticate(_VALID_PAYLOAD)

        assert len(repo.saved) == 1
        assert repo.saved[0].last_login_at is not None

    async def test_returns_auth_result_with_correct_fields(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user=user)
        hasher = FakePasswordHasher()
        provider = CredentialAuthProvider(user_repo=repo, hasher=hasher)

        result = await provider.authenticate(_VALID_PAYLOAD)

        assert isinstance(result, AuthResult)
        assert result.user_id == "user-001"
        assert result.email == "reader@example.com"
        assert result.is_new_user is False


# CredentialAuthProviderFactory tests
@pytest.mark.unit
class TestCredentialAuthProviderFactory:
    def test_create_provider_returns_credential_auth_provider(self) -> None:
        repo = FakeUserRepository()
        hasher = FakePasswordHasher()
        factory = CredentialAuthProviderFactory(user_repo=repo, hasher=hasher)

        provider = factory.create_provider()

        assert isinstance(provider, CredentialAuthProvider)

    def test_create_provider_returns_new_instance_on_each_call(self) -> None:
        repo = FakeUserRepository()
        hasher = FakePasswordHasher()
        factory = CredentialAuthProviderFactory(user_repo=repo, hasher=hasher)

        provider_a = factory.create_provider()
        provider_b = factory.create_provider()

        assert provider_a is not provider_b
