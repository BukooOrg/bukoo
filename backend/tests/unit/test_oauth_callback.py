from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import (
    AuthResult,
    OAuthCallbackCommand,
    OAuthUserInfo,
    TokenDTO,
)
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.cache_service import ICacheService
from app.application.interfaces.oauth_provider import IOAuthProvider
from app.application.interfaces.storage_service import IStorageService
from app.application.interfaces.token_service import ITokenService
from app.application.use_cases.auth.oauth_callback import OAuthCallbackUseCase
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.domain.entities.account_entity import AccountEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import (
    FacebookOAuthError,
    GoogleOAuthError,
    OAuthStateInvalidError,
    UserSuspendedError,
)
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.facebook_auth_provider import FacebookAuthProvider
from app.infrastructure.auth.google_auth_provider import GoogleAuthProvider


class FakeStorageService(IStorageService):
    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        return f"https://storage.example.com/{key}"

    @override
    async def load_once(self, key: str) -> bytes:
        return b""

    @override
    async def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        async def _empty() -> AsyncGenerator[bytes, None]:
            return
            yield b""

        return _empty()

    @override
    async def exists(self, key: str) -> bool:
        return False

    @override
    async def delete(self, key: str) -> None:
        pass

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"https://storage.example.com/{key}?presigned=1"


def _make_user(
    *,
    user_id: str = "user-001",
    email: str = "user@example.com",
    status: UserStatus = UserStatus.ACTIVE,
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email=email,
        _full_name="Test User",
        _date_of_birth=now.date(),
        _role=UserRole.USER,
        _status=status,
        _hashed_password=None,
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_account(
    *,
    account_id: str = "account-001",
    user_id: str = "user-001",
    open_id: str = "google-uid-001",
    token: str = "old-token",
) -> AccountEntity:
    now = datetime.now(UTC)
    return AccountEntity(
        _id=account_id,
        _user_id=user_id,
        _provider=AuthProvider.GOOGLE,
        _open_id=open_id,
        _encrypted_token=token,
        _created_at=now,
        _updated_at=now,
    )


class FakeCacheService(ICacheService):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    @override
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._store[key] = value

    @override
    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    @override
    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    @override
    async def exists(self, key: str) -> bool:
        return key in self._store


class FakeUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, UserEntity] = {}
        self._by_email: dict[str, UserEntity] = {}

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._by_id.get(user_id)

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return self._by_id.get(user_id)

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return self._by_email.get(email)

    @override
    async def save(self, user: UserEntity) -> None:
        self._by_id[user.id] = user
        self._by_email[user.email] = user

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def exists_by_email(self, email: str) -> bool:
        return email in self._by_email

    @override
    async def count_including_deleted(self) -> int:
        return len(self._by_id)


class FakeAccountRepository(IAccountRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, AccountEntity] = {}
        self._by_provider_open_id: dict[tuple[str, str], AccountEntity] = {}

    @override
    async def find_by_user_id(self, user_id: str) -> list[AccountEntity]:
        return [a for a in self._by_id.values() if a.user_id == user_id]

    @override
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> AccountEntity | None:
        return self._by_provider_open_id.get((provider, open_id))

    @override
    async def find_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> AccountEntity | None:
        for a in self._by_id.values():
            if a.user_id == user_id and a.provider == provider:
                return a
        return None

    @override
    async def save(self, account: AccountEntity) -> None:
        self._by_id[account.id] = account
        if account.open_id:
            self._by_provider_open_id[(account.provider, account.open_id)] = account

    @override
    async def delete(self, account_id: str) -> None:
        account = self._by_id.pop(account_id, None)
        if account and account.open_id:
            self._by_provider_open_id.pop((account.provider, account.open_id), None)


class FakeOAuthProvider(IOAuthProvider):
    def __init__(self, *, user_id: str = "stub") -> None:
        self._user_id = user_id

    @override
    def get_authorization_url(self, state: str) -> str:
        return f"https://provider.example.com/auth?state={state}"

    @override
    async def get_access_token(self, code: str) -> str:
        return "fake-access-token"

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        return OAuthUserInfo(
            id="google-uid-001",
            email="user@example.com",
            name="Test User",
            avatar_url=None,
            date_of_birth=None,
        )

    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        return AuthResult(
            user_id=self._user_id, email="stub@example.com", is_new_user=False
        )


class FakeOAuthProviderFactory(IAuthProviderFactory):
    def __init__(self, provider: FakeOAuthProvider) -> None:
        self._provider = provider

    @override
    def create_provider(self) -> FakeOAuthProvider:
        return self._provider


class FakeTokenService(ITokenService):
    @override
    def create_access_token(self, subject: str) -> str:
        return f"jwt-for-{subject}"

    @override
    def decode_token(self, token: str, *, verify_exp: bool = True) -> dict[str, object]:
        return {}

    @override
    async def revoke_token(self, payload: dict[str, object]) -> None:
        pass

    @override
    async def is_token_revoked(self, jti: str) -> bool:
        return False


class FakeGoogleAuthProvider(GoogleAuthProvider):
    """Subclass that stubs out HTTP calls for unit testing."""

    def __init__(
        self,
        *,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        access_token: str = "new-access-token",
        user_info: OAuthUserInfo | None = None,
        raise_on_token: bool = False,
    ) -> None:
        super().__init__(
            user_repo=user_repo,
            account_repo=account_repo,
            storage_svc=FakeStorageService(),
            client_id="fake-client-id",
            client_secret="fake-secret",
            redirect_uri="http://fake/callback",
        )
        self._fake_access_token = access_token
        self._fake_user_info = user_info or OAuthUserInfo(
            id="google-uid-001",
            email="user@example.com",
            name="Test User",
            avatar_url=None,
            date_of_birth=None,
        )
        self._raise_on_token = raise_on_token

    @override
    async def get_access_token(self, code: str) -> str:
        if self._raise_on_token:
            raise GoogleOAuthError()
        return self._fake_access_token

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        return self._fake_user_info


def _build_use_case(
    *,
    cache: ICacheService,
    provider: FakeOAuthProvider,
    token_svc: ITokenService | None = None,
) -> OAuthCallbackUseCase:
    return OAuthCallbackUseCase(
        db_session=AsyncMock(),
        cache_svc=cache,
        factory=FakeOAuthProviderFactory(provider),
        token_svc=token_svc or FakeTokenService(),
    )


@pytest.mark.unit
class TestOAuthCallbackUseCase:
    async def test_raises_state_invalid_when_state_not_in_cache(self) -> None:
        cache = FakeCacheService()

        use_case = _build_use_case(cache=cache, provider=FakeOAuthProvider())

        with pytest.raises(OAuthStateInvalidError):
            await use_case.execute(
                OAuthCallbackCommand(code="auth-code", state="nonexistent-state")
            )

    async def test_state_deleted_from_cache_after_use(self) -> None:
        cache = FakeCacheService()
        await cache.set("oauth_state:state-abc", "1")

        use_case = _build_use_case(cache=cache, provider=FakeOAuthProvider())
        await use_case.execute(
            OAuthCallbackCommand(code="auth-code", state="state-abc")
        )

        assert not await cache.exists("oauth_state:state-abc")

    async def test_returns_jwt_from_provider_auth_result(self) -> None:
        cache = FakeCacheService()
        await cache.set("oauth_state:state-abc", "1")

        use_case = _build_use_case(
            cache=cache, provider=FakeOAuthProvider(user_id="user-001")
        )
        result = await use_case.execute(
            OAuthCallbackCommand(code="auth-code", state="state-abc")
        )

        assert isinstance(result, TokenDTO)
        assert result.access_token == "jwt-for-user-001"


@pytest.mark.unit
class TestGoogleAuthProviderAuthenticate:
    async def test_branch_a_returns_auth_result_for_existing_account(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001")
        await user_repo.save(user)
        account = _make_account(user_id="user-001", open_id="google-uid-001")
        await account_repo.save(account)

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        result = await provider.authenticate({"code": "auth-code"})

        assert isinstance(result, AuthResult)
        assert result.user_id == "user-001"
        assert result.is_new_user is False

    async def test_branch_b_new_user_created_with_active_status(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo,
            account_repo=account_repo,
            user_info=OAuthUserInfo(
                id="google-uid-new",
                email="new@example.com",
                name="New User",
                avatar_url=None,
                date_of_birth=None,
            ),
        )
        result = await provider.authenticate({"code": "auth-code"})

        assert isinstance(result, AuthResult)
        saved_user = await user_repo.find_by_email("new@example.com")
        assert saved_user is not None
        assert saved_user.status == UserStatus.ACTIVE
        assert result.is_new_user is True

    async def test_raises_google_oauth_error_when_token_exchange_fails(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo, account_repo=account_repo, raise_on_token=True
        )

        with pytest.raises(GoogleOAuthError):
            await provider.authenticate({"code": "bad-code"})

    async def test_raises_suspended_error_for_suspended_linked_user(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001", status=UserStatus.SUSPENDED)
        await user_repo.save(user)
        account = _make_account(user_id="user-001", open_id="google-uid-001")
        await account_repo.save(account)

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )

        with pytest.raises(UserSuspendedError):
            await provider.authenticate({"code": "auth-code"})

    async def test_pending_user_found_by_email_is_activated(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        pending_user = _make_user(
            user_id="user-pending",
            email="user@example.com",
            status=UserStatus.PENDING,
        )
        await user_repo.save(pending_user)

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        await provider.authenticate({"code": "auth-code"})

        saved = await user_repo.find_by_email("user@example.com")
        assert saved is not None
        assert saved.status == UserStatus.ACTIVE

    async def test_branch_a_updates_existing_account_token(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001")
        await user_repo.save(user)
        account = _make_account(
            user_id="user-001", open_id="google-uid-001", token="old-token"
        )
        await account_repo.save(account)

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo,
            account_repo=account_repo,
            access_token="new-access-token",
        )
        await provider.authenticate({"code": "auth-code"})

        saved_account = await account_repo.find_by_provider_and_open_id(
            AuthProvider.GOOGLE, "google-uid-001"
        )
        assert saved_account is not None
        assert saved_account.encrypted_token == "new-access-token"

    async def test_new_account_linked_with_google_provider(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeGoogleAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        result = await provider.authenticate({"code": "auth-code"})

        saved_account = await account_repo.find_by_provider_and_open_id(
            AuthProvider.GOOGLE, "google-uid-001"
        )
        assert saved_account is not None
        assert saved_account.provider == AuthProvider.GOOGLE
        assert saved_account.user_id == result.user_id


class FakeFacebookAuthProvider(FacebookAuthProvider):
    """Subclass that stubs out HTTP calls for unit testing."""

    def __init__(
        self,
        *,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        access_token: str = "new-access-token",
        user_info: OAuthUserInfo | None = None,
        raise_on_token: bool = False,
    ) -> None:
        super().__init__(
            user_repo=user_repo,
            account_repo=account_repo,
            storage_svc=FakeStorageService(),
            client_id="fake-client-id",
            client_secret="fake-secret",
            redirect_uri="http://fake/callback",
        )
        self._fake_access_token = access_token
        self._fake_user_info = user_info or OAuthUserInfo(
            id="facebook-uid-001",
            email="user@example.com",
            name="Test User",
            avatar_url=None,
            date_of_birth=None,
        )
        self._raise_on_token = raise_on_token

    @override
    async def get_access_token(self, code: str) -> str:
        if self._raise_on_token:
            raise FacebookOAuthError()
        return self._fake_access_token

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        return self._fake_user_info


def _make_facebook_account(
    *,
    account_id: str = "account-001",
    user_id: str = "user-001",
    open_id: str = "facebook-uid-001",
    token: str = "old-token",
) -> AccountEntity:
    now = datetime.now(UTC)
    return AccountEntity(
        _id=account_id,
        _user_id=user_id,
        _provider=AuthProvider.FACEBOOK,
        _open_id=open_id,
        _encrypted_token=token,
        _created_at=now,
        _updated_at=now,
    )


@pytest.mark.unit
class TestFacebookAuthProviderAuthenticate:
    async def test_branch_a_returns_auth_result_for_existing_account(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001")
        await user_repo.save(user)
        account = _make_facebook_account(user_id="user-001", open_id="facebook-uid-001")
        await account_repo.save(account)

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        result = await provider.authenticate({"code": "auth-code"})

        assert isinstance(result, AuthResult)
        assert result.user_id == "user-001"
        assert result.is_new_user is False

    async def test_branch_b_new_user_created_with_active_status(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo,
            account_repo=account_repo,
            user_info=OAuthUserInfo(
                id="facebook-uid-new",
                email="new@example.com",
                name="New User",
                avatar_url=None,
                date_of_birth=None,
            ),
        )
        result = await provider.authenticate({"code": "auth-code"})

        assert isinstance(result, AuthResult)
        saved_user = await user_repo.find_by_email("new@example.com")
        assert saved_user is not None
        assert saved_user.status == UserStatus.ACTIVE
        assert result.is_new_user is True

    async def test_raises_facebook_oauth_error_when_token_exchange_fails(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo, account_repo=account_repo, raise_on_token=True
        )

        with pytest.raises(FacebookOAuthError):
            await provider.authenticate({"code": "bad-code"})

    async def test_raises_suspended_error_for_suspended_linked_user(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001", status=UserStatus.SUSPENDED)
        await user_repo.save(user)
        account = _make_facebook_account(user_id="user-001", open_id="facebook-uid-001")
        await account_repo.save(account)

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )

        with pytest.raises(UserSuspendedError):
            await provider.authenticate({"code": "auth-code"})

    async def test_pending_user_found_by_email_is_activated(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        pending_user = _make_user(
            user_id="user-pending",
            email="user@example.com",
            status=UserStatus.PENDING,
        )
        await user_repo.save(pending_user)

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        await provider.authenticate({"code": "auth-code"})

        saved = await user_repo.find_by_email("user@example.com")
        assert saved is not None
        assert saved.status == UserStatus.ACTIVE

    async def test_branch_a_updates_existing_account_token(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        user = _make_user(user_id="user-001")
        await user_repo.save(user)
        account = _make_facebook_account(
            user_id="user-001", open_id="facebook-uid-001", token="old-token"
        )
        await account_repo.save(account)

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo,
            account_repo=account_repo,
            access_token="new-access-token",
        )
        await provider.authenticate({"code": "auth-code"})

        saved_account = await account_repo.find_by_provider_and_open_id(
            AuthProvider.FACEBOOK, "facebook-uid-001"
        )
        assert saved_account is not None
        assert saved_account.encrypted_token == "new-access-token"

    async def test_new_account_linked_with_facebook_provider(self) -> None:
        user_repo = FakeUserRepository()
        account_repo = FakeAccountRepository()

        provider = FakeFacebookAuthProvider(
            user_repo=user_repo, account_repo=account_repo
        )
        result = await provider.authenticate({"code": "auth-code"})

        saved_account = await account_repo.find_by_provider_and_open_id(
            AuthProvider.FACEBOOK, "facebook-uid-001"
        )
        assert saved_account is not None
        assert saved_account.provider == AuthProvider.FACEBOOK
        assert saved_account.user_id == result.user_id
