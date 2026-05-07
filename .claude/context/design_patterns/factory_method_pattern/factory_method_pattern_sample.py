"""
Factory Method Pattern — Bukoo Auth System (v2)

Roles
─────────────────────────────────────────────────────────────────────────────
  Abstract Product    : IAuthProvider, IOAuthProvider
  Concrete Product    : CredentialAuthProvider
                        GoogleAuthProvider  (implements both interfaces)
                        FacebookAuthProvider (implements both interfaces)
  Abstract Creator    : IAuthProviderFactory
  Concrete Creator    : CredentialAuthProviderFactory
                        GoogleAuthProviderFactory
                        FacebookAuthProviderFactory
  Consumer (Client)   : LoginUseCase

Key changes from v1
─────────────────────────────────────────────────────────────────────────────
  - Interface names use the "I" prefix (IAuthProvider, IAuthProviderFactory, …)
  - OAuth providers implement a second interface, IOAuthProvider, that exposes
    get_authorization_url / get_access_token / get_user_info in addition to
    authenticate — the concrete class satisfies both ABCs simultaneously.
  - AuthResult.is_new_user (bool) replaced the old provider: str field.
  - OAuthUserInfo DTO introduced for OAuth-specific identity data.
  - Concrete factories now inject repository + service stubs alongside
    config values, matching the Clean Architecture wiring in deps.py.
  - @override marks every create_provider() implementation.

Running
─────────────────────────────────────────────────────────────────────────────
  python factory_method_pattern_sample_v2.py
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, override

# ─────────────────────────────────────────────────────────────────────────────
# DTOs
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AuthResult:
    """Standardised result produced by every IAuthProvider.authenticate()."""

    user_id: str
    email: str
    is_new_user: bool  # True when the account was created during this login


@dataclass
class OAuthUserInfo:
    """Identity payload extracted from the OAuth provider's user-info endpoint."""

    id: str  # provider-specific user ID (sub / uid)
    email: str
    name: str
    avatar_url: str | None
    date_of_birth: date | None


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Products
# ─────────────────────────────────────────────────────────────────────────────


# Step 1 — IAuthProvider is the primary abstract product.
# Every concrete provider must implement authenticate(), which is the
# uniform interface LoginUseCase calls regardless of the auth strategy.
class IAuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        pass


# Step 2 — IOAuthProvider is a second abstract product for OAuth-specific
# operations.  OAuth providers (Google, Facebook) implement both IAuthProvider
# AND IOAuthProvider, giving callers access to the OAuth flow without
# casting or isinstance checks.
class IOAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Return the provider's consent-screen URL the browser should redirect to."""
        pass

    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        """Exchange the authorization code for an access token."""
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        """Fetch and return the user's identity from the provider's API."""
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Creator
# ─────────────────────────────────────────────────────────────────────────────


# Step 3 — IAuthProviderFactory declares create_provider() as the Factory Method.
# LoginUseCase depends only on this abstract interface.  It never references
# CredentialAuthProviderFactory, GoogleAuthProviderFactory, or
# FacebookAuthProviderFactory directly.
class IAuthProviderFactory(ABC):
    @abstractmethod
    def create_provider(self) -> IAuthProvider:
        """Factory Method: subclasses override this to return the correct product."""
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Repository / service interfaces (application-layer ports — stubs only)
# ─────────────────────────────────────────────────────────────────────────────
# These are the dependency interfaces that concrete products receive.
# In the real project they live under app/domain/repositories/ and
# app/application/interfaces/.


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def save(self, user: dict[str, Any]) -> None:
        pass


class IAccountRepository(ABC):
    @abstractmethod
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def save(self, account: dict[str, Any]) -> None:
        pass


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, raw: str) -> str:
        pass

    @abstractmethod
    def verify(self, raw: str, hashed: str) -> bool:
        pass


class IStorageService(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Product 1 — CredentialAuthProvider
# ─────────────────────────────────────────────────────────────────────────────


# Step 4a — Implements IAuthProvider only (no OAuth flow).
# The factory injects the repository and hasher; the provider uses them to
# validate the submitted password against the stored hash.
class CredentialAuthProvider(IAuthProvider):
    def __init__(
        self,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        email = payload.get("email", "")
        password = payload.get("password", "")
        print(f"[CredentialAuthProvider] authenticate() — email={email}")

        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise ValueError("No account found for that email.")

        if not self._hasher.verify(password, user["hashed_password"]):
            raise ValueError("Incorrect password.")

        print("[CredentialAuthProvider] Password verified. Authentication successful.")
        return AuthResult(user_id=user["id"], email=user["email"], is_new_user=False)


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Product 2 — GoogleAuthProvider
# ─────────────────────────────────────────────────────────────────────────────


# Step 4b — Implements BOTH IAuthProvider and IOAuthProvider.
# This dual-interface structure lets the route that handles the OAuth callback
# call authenticate() through IAuthProvider, while the route that builds the
# consent-screen URL calls get_authorization_url() through IOAuthProvider —
# both via the same concrete instance.
class GoogleAuthProvider(IAuthProvider, IOAuthProvider):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    # ── IOAuthProvider ────────────────────────────────────────────────────────

    @override
    def get_authorization_url(self, state: str) -> str:
        # stub: builds the Google consent-screen URL with scopes + state
        url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={self._client_id}&state={state}&redirect_uri={self._redirect_uri}"
        )
        print(f"[GoogleAuthProvider] get_authorization_url() → {url}")
        return url

    @override
    async def get_access_token(self, code: str) -> str:
        # stub: POST to https://oauth2.googleapis.com/token, returns access_token
        print(f"[GoogleAuthProvider] get_access_token() — code={code}")
        return "google-access-token-stub"

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        # stub: GET https://www.googleapis.com/oauth2/v3/userinfo
        print("[GoogleAuthProvider] get_user_info() — fetching identity from Google")
        return OAuthUserInfo(
            id="google-uid-001",
            email="customer@gmail.com",
            name="Google User",
            avatar_url=None,
            date_of_birth=None,
        )

    # ── IAuthProvider ─────────────────────────────────────────────────────────

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        code = payload.get("code", "")
        print(f"[GoogleAuthProvider] authenticate() — code={code}")

        access_token = await self.get_access_token(code)
        user_info = await self.get_user_info(access_token)

        # Branch A: account already linked to this Google identity
        existing_account = await self._account_repo.find_by_provider_and_open_id(
            "google", user_info.id
        )
        if existing_account:
            linked_user = await self._user_repo.find_by_id(existing_account["user_id"])
            if linked_user:
                print("[GoogleAuthProvider] Returning existing linked account.")
                return AuthResult(
                    user_id=linked_user["id"],
                    email=linked_user["email"],
                    is_new_user=False,
                )

        # Branch B: find existing user by email or create a new one
        user_by_email = await self._user_repo.find_by_email(user_info.email)
        if user_by_email:
            user = user_by_email
            is_new_user = False
            print("[GoogleAuthProvider] Linked existing user account.")
        else:
            user = {"id": "user-new-uuid", "email": user_info.email}
            await self._user_repo.save(user)
            is_new_user = True
            print("[GoogleAuthProvider] Created new user account.")

        new_account = {
            "id": "account-new-uuid",
            "user_id": user["id"],
            "provider": "google",
            "open_id": user_info.id,
            "token": access_token,
        }
        await self._account_repo.save(new_account)

        return AuthResult(
            user_id=user["id"], email=user["email"], is_new_user=is_new_user
        )


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Product 3 — FacebookAuthProvider
# ─────────────────────────────────────────────────────────────────────────────


# Step 4c — Also implements both IAuthProvider and IOAuthProvider.
# Structurally identical to GoogleAuthProvider; only the endpoint URLs and
# field names differ.  LoginUseCase calls authenticate() without knowing
# which OAuth provider is behind the factory.
class FacebookAuthProvider(IAuthProvider, IOAuthProvider):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    # ── IOAuthProvider ────────────────────────────────────────────────────────

    @override
    def get_authorization_url(self, state: str) -> str:
        url = (
            f"https://www.facebook.com/v18.0/dialog/oauth"
            f"?client_id={self._client_id}&state={state}&redirect_uri={self._redirect_uri}"
        )
        print(f"[FacebookAuthProvider] get_authorization_url() → {url}")
        return url

    @override
    async def get_access_token(self, code: str) -> str:
        print(f"[FacebookAuthProvider] get_access_token() — code={code}")
        return "facebook-access-token-stub"

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        print(
            "[FacebookAuthProvider] get_user_info() — fetching identity from Facebook"
        )
        return OAuthUserInfo(
            id="facebook-uid-001",
            email="customer@facebook.com",
            name="Facebook User",
            avatar_url=None,
            date_of_birth=None,
        )

    # ── IAuthProvider ─────────────────────────────────────────────────────────

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        code = payload.get("code", "")
        print(f"[FacebookAuthProvider] authenticate() — code={code}")

        access_token = await self.get_access_token(code)
        user_info = await self.get_user_info(access_token)

        # Branch A: account already linked to this Facebook identity
        existing_account = await self._account_repo.find_by_provider_and_open_id(
            "facebook", user_info.id
        )
        if existing_account:
            linked_user = await self._user_repo.find_by_id(existing_account["user_id"])
            if linked_user:
                print("[FacebookAuthProvider] Returning existing linked account.")
                return AuthResult(
                    user_id=linked_user["id"],
                    email=linked_user["email"],
                    is_new_user=False,
                )

        # Branch B: find existing user by email or create a new one
        user_by_email = await self._user_repo.find_by_email(user_info.email)
        if user_by_email:
            user = user_by_email
            is_new_user = False
            print("[FacebookAuthProvider] Linked existing user account.")
        else:
            user = {"id": "user-new-uuid", "email": user_info.email}
            await self._user_repo.save(user)
            is_new_user = True
            print("[FacebookAuthProvider] Created new user account.")

        new_account = {
            "id": "account-new-uuid",
            "user_id": user["id"],
            "provider": "facebook",
            "open_id": user_info.id,
            "token": access_token,
        }
        await self._account_repo.save(new_account)

        return AuthResult(
            user_id=user["id"], email=user["email"], is_new_user=is_new_user
        )


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Creators
# ─────────────────────────────────────────────────────────────────────────────


# Step 5a — CredentialAuthProviderFactory injects only the two dependencies
# that CredentialAuthProvider needs: a user repository and a password hasher.
class CredentialAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    @override
    def create_provider(self) -> IAuthProvider:
        # Factory Method override — constructs and returns the concrete product.
        # The caller (LoginUseCase) only ever sees the IAuthProvider return type.
        print(
            "[CredentialAuthProviderFactory] create_provider() → CredentialAuthProvider"
        )
        return CredentialAuthProvider(user_repo=self._user_repo, hasher=self._hasher)


# Step 5b — GoogleAuthProviderFactory injects all six dependencies that
# GoogleAuthProvider needs, including the two repository ports and the
# storage service port.
class GoogleAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    @override
    def create_provider(self) -> IAuthProvider:
        print("[GoogleAuthProviderFactory] create_provider() → GoogleAuthProvider")
        return GoogleAuthProvider(
            user_repo=self._user_repo,
            account_repo=self._account_repo,
            storage_svc=self._storage_svc,
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._redirect_uri,
        )


# Step 5c — FacebookAuthProviderFactory is structurally identical to
# GoogleAuthProviderFactory; only the concrete product it instantiates differs.
class FacebookAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    @override
    def create_provider(self) -> IAuthProvider:
        print("[FacebookAuthProviderFactory] create_provider() → FacebookAuthProvider")
        return FacebookAuthProvider(
            user_repo=self._user_repo,
            account_repo=self._account_repo,
            storage_svc=self._storage_svc,
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._redirect_uri,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Consumer (Client) — LoginUseCase
# ─────────────────────────────────────────────────────────────────────────────


# Step 6 — LoginUseCase is the consumer of the Factory Method pattern.
# It holds a reference to IAuthProviderFactory (the abstract creator).
# It calls create_provider() to obtain an IAuthProvider, then calls
# authenticate() on it.  The use case has no knowledge of which concrete
# factory or provider it is working with.
class LoginUseCase:
    def __init__(
        self,
        db_session: Any,
        factory: IAuthProviderFactory,  # abstract type — decoupled from concrete factories
    ) -> None:
        self._db_session = db_session
        self._factory = factory

    async def execute(self, payload: dict[str, str]) -> AuthResult:
        print("[LoginUseCase] Calling factory method: create_provider()")

        # Factory Method call — the correct concrete IAuthProvider is returned
        # without LoginUseCase knowing its concrete type.
        provider: IAuthProvider = self._factory.create_provider()

        print("[LoginUseCase] Delegating authentication to provider...")

        # authenticate() is called through the uniform IAuthProvider interface.
        result: AuthResult = await provider.authenticate(payload)

        # Commit the session — persists any new user / account records created
        # during the OAuth sign-up path.
        await self._db_session.commit()

        return result


# ─────────────────────────────────────────────────────────────────────────────
# Stub infrastructure (simulates deps.py wiring in the real project)
# ─────────────────────────────────────────────────────────────────────────────


class StubUserRepository(IUserRepository):
    """In-memory user store — simulates IUserRepository."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {
            "credential@bukoo.my": {
                "id": "user-credential-001",
                "email": "credential@bukoo.my",
                "hashed_password": "hashed(correct_password)",
            },
        }

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        return self._store.get(email)

    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        return next((u for u in self._store.values() if u["id"] == user_id), None)

    async def save(self, user: dict[str, Any]) -> None:
        self._store[user["email"]] = user
        print(f"[StubUserRepository] save() — user_id={user['id']}")


class StubAccountRepository(IAccountRepository):
    """In-memory account store — simulates IAccountRepository."""

    def __init__(self) -> None:
        self._store: list[dict[str, Any]] = []

    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> dict[str, Any] | None:
        return next(
            (
                a
                for a in self._store
                if a["provider"] == provider and a["open_id"] == open_id
            ),
            None,
        )

    async def save(self, account: dict[str, Any]) -> None:
        self._store.append(account)
        print(f"[StubAccountRepository] save() — provider={account['provider']}")


class StubPasswordHasher(IPasswordHasher):
    """Simulates bcrypt / argon2 — deterministic for testing."""

    def hash(self, raw: str) -> str:
        return f"hashed({raw})"

    def verify(self, raw: str, hashed: str) -> bool:
        return self.hash(raw) == hashed


class StubStorageService(IStorageService):
    """Simulates MinIO / S3 — no-op upload."""

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        print(f"[StubStorageService] upload() — key={key}")


class StubDbSession:
    """Simulates SQLAlchemy AsyncSession."""

    async def commit(self) -> None:
        print("[StubDbSession] db_session.commit() called.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Route simulations
# ─────────────────────────────────────────────────────────────────────────────


async def simulate_credential_login() -> None:
    """
    Simulates POST /api/app/v1/auth/login.

    The route (or deps.py) selects CredentialAuthProviderFactory and wires it
    with the concrete repository + hasher implementations.  LoginUseCase
    receives it typed as IAuthProviderFactory — the concrete type is hidden.
    """
    print("=" * 60)
    print("ROUTE: POST /api/app/v1/auth/login  (Credential)")
    print("=" * 60)

    # Route layer: instantiate the concrete factory and inject infrastructure.
    # This is the ONLY place CredentialAuthProviderFactory is referenced by name.
    factory = CredentialAuthProviderFactory(
        user_repo=StubUserRepository(),
        hasher=StubPasswordHasher(),
    )

    use_case = LoginUseCase(db_session=StubDbSession(), factory=factory)

    result = await use_case.execute(
        {"email": "credential@bukoo.my", "password": "correct_password"}
    )
    print(
        f"[Route] AuthResult → user_id={result.user_id}, "
        f"email={result.email}, is_new_user={result.is_new_user}\n"
    )


async def simulate_google_login() -> None:
    """
    Simulates POST /api/app/v1/auth/login/google (OAuth callback).

    GoogleAuthProviderFactory is selected here.  LoginUseCase receives it
    typed as IAuthProviderFactory — identical call structure to the credential
    flow above, demonstrating the pattern's uniformity.
    """
    print("=" * 60)
    print("ROUTE: POST /api/app/v1/auth/login/google  (Google OAuth)")
    print("=" * 60)

    factory = GoogleAuthProviderFactory(
        user_repo=StubUserRepository(),
        account_repo=StubAccountRepository(),
        storage_svc=StubStorageService(),
        client_id="bukoo-google-client-id",
        client_secret="bukoo-google-client-secret",
        redirect_uri="https://bukoo.my/auth/callback/google",
    )

    use_case = LoginUseCase(db_session=StubDbSession(), factory=factory)

    result = await use_case.execute({"code": "google-auth-code-xyz"})
    print(
        f"[Route] AuthResult → user_id={result.user_id}, "
        f"email={result.email}, is_new_user={result.is_new_user}\n"
    )


async def simulate_facebook_login() -> None:
    """
    Simulates POST /api/app/v1/auth/login/facebook (OAuth callback).

    Identical structure to the Google flow — FacebookAuthProviderFactory
    swaps in FacebookAuthProvider behind the same IAuthProviderFactory interface.
    """
    print("=" * 60)
    print("ROUTE: POST /api/app/v1/auth/login/facebook  (Facebook OAuth)")
    print("=" * 60)

    factory = FacebookAuthProviderFactory(
        user_repo=StubUserRepository(),
        account_repo=StubAccountRepository(),
        storage_svc=StubStorageService(),
        client_id="bukoo-facebook-app-id",
        client_secret="bukoo-facebook-app-secret",
        redirect_uri="https://bukoo.my/auth/callback/facebook",
    )

    use_case = LoginUseCase(db_session=StubDbSession(), factory=factory)

    result = await use_case.execute({"code": "facebook-auth-code-xyz"})
    print(
        f"[Route] AuthResult → user_id={result.user_id}, "
        f"email={result.email}, is_new_user={result.is_new_user}\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(simulate_credential_login())
    asyncio.run(simulate_google_login())
    asyncio.run(simulate_facebook_login())
