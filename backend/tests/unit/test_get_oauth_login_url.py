from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date
from typing import override
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.auth_dto import GetOAuthLoginUrlResult, OAuthUserInfo
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.cache_service import ICacheService
from app.application.interfaces.oauth_provider import IOAuthProvider
from app.application.interfaces.storage_service import IStorageService
from app.application.use_cases.auth.get_oauth_login_url import GetOAuthLoginUrlUseCase
from app.infrastructure.auth.facebook_auth_provider import FacebookAuthProvider
from app.infrastructure.auth.facebook_auth_provider_factory import (
    FacebookAuthProviderFactory,
)
from app.infrastructure.auth.google_auth_provider import GoogleAuthProvider
from app.infrastructure.auth.google_auth_provider_factory import (
    GoogleAuthProviderFactory,
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


class FakeOAuthProvider(IOAuthProvider):
    def __init__(self, base_url: str = "https://provider.example.com/auth") -> None:
        self._base_url = base_url
        self.last_state: str = ""

    @override
    def get_authorization_url(self, state: str) -> str:
        self.last_state = state
        return f"{self._base_url}?state={state}"

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
            date_of_birth=date(1990, 5, 15),
        )


class FakeOAuthProviderFactory(IAuthProviderFactory):
    def __init__(self, provider: IOAuthProvider) -> None:
        self._provider = provider
        self.create_called = 0

    @override
    def create_provider(self) -> IOAuthProvider:
        self.create_called += 1
        return self._provider


@pytest.mark.unit
class TestGetOAuthLoginUrlUseCase:
    async def test_returns_result_with_non_empty_url(self) -> None:
        db_session = AsyncMock()
        cache = FakeCacheService()
        fake_provider = FakeOAuthProvider()
        factory = FakeOAuthProviderFactory(fake_provider)

        use_case = GetOAuthLoginUrlUseCase(
            db_session=db_session, cache_svc=cache, factory=factory
        )
        result = await use_case.execute()

        assert isinstance(result, GetOAuthLoginUrlResult)
        assert result.url != ""

    async def test_url_contains_state_stored_in_cache(self) -> None:
        db_session = AsyncMock()
        cache = FakeCacheService()
        fake_provider = FakeOAuthProvider()
        factory = FakeOAuthProviderFactory(fake_provider)

        use_case = GetOAuthLoginUrlUseCase(
            db_session=db_session, cache_svc=cache, factory=factory
        )
        result = await use_case.execute()

        state = fake_provider.last_state
        assert state != ""
        assert f"state={state}" in result.url
        assert await cache.exists(f"oauth_state:{state}")

    async def test_cache_ttl_is_600_seconds(self) -> None:
        db_session = AsyncMock()

        stored_ttl: list[int | None] = []

        class CapturingCache(FakeCacheService):
            @override
            async def set(
                self, key: str, value: str, ttl_seconds: int | None = None
            ) -> None:
                stored_ttl.append(ttl_seconds)
                await super().set(key, value, ttl_seconds)

        cache = CapturingCache()
        fake_provider = FakeOAuthProvider()
        factory = FakeOAuthProviderFactory(fake_provider)

        use_case = GetOAuthLoginUrlUseCase(
            db_session=db_session, cache_svc=cache, factory=factory
        )
        await use_case.execute()

        assert stored_ttl == [600]

    async def test_factory_create_provider_called_once(self) -> None:
        db_session = AsyncMock()
        cache = FakeCacheService()
        fake_provider = FakeOAuthProvider()
        factory = FakeOAuthProviderFactory(fake_provider)

        use_case = GetOAuthLoginUrlUseCase(
            db_session=db_session, cache_svc=cache, factory=factory
        )
        await use_case.execute()

        assert factory.create_called == 1

    async def test_each_call_generates_unique_state(self) -> None:
        db_session = AsyncMock()
        cache = FakeCacheService()
        fake_provider = FakeOAuthProvider()
        factory = FakeOAuthProviderFactory(fake_provider)

        use_case = GetOAuthLoginUrlUseCase(
            db_session=db_session, cache_svc=cache, factory=factory
        )
        await use_case.execute()
        state_a = fake_provider.last_state

        await use_case.execute()
        state_b = fake_provider.last_state

        assert state_a != state_b


@pytest.mark.unit
class TestGoogleAuthProviderFactory:
    def _make_factory(self) -> GoogleAuthProviderFactory:
        return GoogleAuthProviderFactory(
            user_repo=MagicMock(),
            account_repo=MagicMock(),
            storage_svc=FakeStorageService(),
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/callback",
        )

    def test_create_provider_returns_google_auth_provider(self) -> None:
        provider = self._make_factory().create_provider()

        assert isinstance(provider, GoogleAuthProvider)

    def test_create_provider_is_also_oauth_provider(self) -> None:
        provider = self._make_factory().create_provider()

        assert isinstance(provider, IOAuthProvider)

    def test_create_provider_returns_new_instance_each_call(self) -> None:
        factory = self._make_factory()
        provider_a = factory.create_provider()
        provider_b = factory.create_provider()

        assert provider_a is not provider_b


@pytest.mark.unit
class TestGoogleAuthProviderGetAuthorizationUrl:
    def _make_provider(self, client_id: str = "my-client-id") -> GoogleAuthProvider:
        return GoogleAuthProvider(
            user_repo=MagicMock(),
            account_repo=MagicMock(),
            storage_svc=FakeStorageService(),
            client_id=client_id,
            client_secret="secret",
            redirect_uri="http://localhost/callback",
        )

    def test_url_contains_client_id(self) -> None:
        provider = self._make_provider(client_id="my-client-id")
        url = provider.get_authorization_url(state="test-state")

        assert "client_id=my-client-id" in url

    def test_url_contains_state(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="abc123")

        assert "state=abc123" in url

    def test_url_starts_with_google_auth_endpoint(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="xyz")

        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")

    def test_url_contains_correct_scope(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="xyz")

        assert "scope=" in url
        assert "email" in url
        assert "profile" in url


@pytest.mark.unit
class TestFacebookAuthProviderFactory:
    def _make_factory(self) -> FacebookAuthProviderFactory:
        return FacebookAuthProviderFactory(
            user_repo=MagicMock(),
            account_repo=MagicMock(),
            storage_svc=FakeStorageService(),
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/callback",
        )

    def test_create_provider_returns_facebook_auth_provider(self) -> None:
        provider = self._make_factory().create_provider()

        assert isinstance(provider, FacebookAuthProvider)

    def test_create_provider_is_also_oauth_provider(self) -> None:
        provider = self._make_factory().create_provider()

        assert isinstance(provider, IOAuthProvider)

    def test_create_provider_returns_new_instance_each_call(self) -> None:
        factory = self._make_factory()
        provider_a = factory.create_provider()
        provider_b = factory.create_provider()

        assert provider_a is not provider_b


@pytest.mark.unit
class TestFacebookAuthProviderGetAuthorizationUrl:
    def _make_provider(self, client_id: str = "my-client-id") -> FacebookAuthProvider:
        return FacebookAuthProvider(
            user_repo=MagicMock(),
            account_repo=MagicMock(),
            storage_svc=FakeStorageService(),
            client_id=client_id,
            client_secret="secret",
            redirect_uri="http://localhost/callback",
        )

    def test_url_contains_client_id(self) -> None:
        provider = self._make_provider(client_id="my-client-id")
        url = provider.get_authorization_url(state="test-state")

        assert "client_id=my-client-id" in url

    def test_url_contains_state(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="abc123")

        assert "state=abc123" in url

    def test_url_starts_with_facebook_auth_endpoint(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="xyz")

        assert url.startswith("https://www.facebook.com/v18.0/dialog/oauth")

    def test_url_contains_correct_scope(self) -> None:
        provider = self._make_provider()
        url = provider.get_authorization_url(state="xyz")

        assert "scope=" in url
        assert "email" in url
        assert "public_profile" in url
