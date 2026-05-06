from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

type AsyncSession = dict[str, Any]


# data classes
@dataclass
class AuthResult:
    """
    Standardised output produced by every AuthProvider.
    LoginUseCase only ever sees this object — never the
    concrete provider that produced it.
    """

    user_id: str
    email: str
    provider: str


@dataclass
class TokenDTO:
    """Carries the issued access token back to the route layer."""

    access_token: str


# Abstract product — AuthProvider
class AuthProvider(ABC):
    """
    Abstract product in the Factory Method pattern.
    Defines the interface all concrete providers must honour.
    LoginUseCase depends only on this abstraction, but
    never on GoogleAuthProvider or CredentialAuthProvider directly.
    """

    @abstractmethod
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        """
        Concrete providers implement their own authentication logic here.
        Despite different internals, every implementation returns AuthResult,
        so LoginUseCase never needs to know which provider is running.
        """
        pass


# Concrete Product 1 - CredentialAuthProvider
class CredentialAuthProvider(AuthProvider):
    """
    Concrete product for email-and-password authentication.
    Fetches the user record, hashes the submitted password,
    and compares it to the stored hash.
    """

    def __init__(self, password_hasher) -> None:
        self._password_hasher = password_hasher

    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        email = payload.get("email")
        raw_password = payload.get("password")
        print(f"[CredentialAuthProvider] Authenticating user: {email}")

        # stub: fetch user record from UserRepository
        # user = await user_repo.find_by_email(db_session, email)
        user = {
            "user_id": "user-uuid-001",
            "email": email,
            "hashed_password": self._password_hasher.hash("correct_password"),
        }
        # ---------------------------------------------------

        if user is None:
            raise ValueError(f"No account found for email: {email}")

        print("[CredentialAuthProvider] Comparing password against stored hash...")

        # stub: password verification
        # password_match = self._password_hasher.verify(raw_password, user["hashed_password"])
        password_match = True  # stub: assume match
        # -----------------------------------

        if not password_match:
            raise ValueError("Incorrect password.")

        print("[CredentialAuthProvider] Password matched. Authentication successful.")
        return AuthResult(
            user_id=user["user_id"],
            email=user["email"],
            provider="credential",
        )


# Concrete Product 2 - GoogleAuthProvider
class GoogleAuthProvider(AuthProvider):
    """
    Concrete product for Google OAuth authentication.
    Exchanges the authorisation code for tokens with Google's
    identity service and extracts the verified user identity.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        code = payload.get("code")
        redirect_uri = payload.get("redirect_uri", "")
        print(
            "[GoogleAuthProvider] Exchanging auth code with Google Identity Service..."
        )

        # stub: exchange code for token via Google OAuth client
        # token_response = await google_client.exchange_code(
        #     code=code,
        #     redirect_uri=redirect_uri,
        #     client_id=self._client_id,
        #     client_secret=self._client_secret,
        # )
        # user_info = await google_client.get_user_info(token_response.access_token)
        user_info = {
            "user_id": "google-uid-001",
            "email": "customer@gmail.com",
        }  # stub: mock identity payload
        # -------------------------------------------------------------

        print(f"[GoogleAuthProvider] Identity verified. User: {user_info['email']}")
        return AuthResult(
            user_id=user_info["user_id"],
            email=user_info["email"],
            provider="google",
        )


# abstract creator — AuthProviderFactory
class AuthProviderFactory(ABC):
    """
    Abstract creator in the Factory Method pattern.

    Declares create_provider() as the FACTORY METHOD.
    Subclasses override this to produce the correct concrete
    AuthProvider. LoginUseCase depends only on this abstract
    interface. It never references a concrete factory or provider.
    """

    @abstractmethod
    def create_provider(self) -> AuthProvider:
        """
        Factory Method: each concrete factory overrides this to
        instantiate and return its specific AuthProvider.
        LoginUseCase calls this — the concrete type is hidden behind
        the AuthProvider return type.
        """
        pass


# Concrete creator 1 — CredentialAuthProviderFactory
class CredentialAuthProviderFactory(AuthProviderFactory):
    """
    Concrete creator for the email-and-password path.
    Overrides create_provider() to return a CredentialAuthProvider,
    injecting the password hasher it was constructed with.
    Instantiated directly by the /auth/login route handler.
    """

    def __init__(self, password_hasher) -> None:
        self._password_hasher = password_hasher

    def create_provider(self) -> AuthProvider:
        # Factory Method override: produces a CredentialAuthProvider.
        # LoginUseCase receives only the AuthProvider abstract interface.
        print(
            "[CredentialAuthProviderFactory] create_provider() → CredentialAuthProvider"
        )
        return CredentialAuthProvider(password_hasher=self._password_hasher)


# Concrete creator 2 — GoogleAuthProviderFactory
class GoogleAuthProviderFactory(AuthProviderFactory):
    """
    Concrete creator for the Google OAuth path.
    Overrides create_provider() to return a GoogleAuthProvider,
    injecting the OAuth client credentials it was constructed with.
    Instantiated directly by the /auth/login/google route handler.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def create_provider(self) -> AuthProvider:
        # Factory Method override: produces a GoogleAuthProvider.
        # LoginUseCase receives only the AuthProvider abstract interface.
        print("[GoogleAuthProviderFactory] create_provider() → GoogleAuthProvider")
        return GoogleAuthProvider(
            client_id=self._client_id,
            client_secret=self._client_secret,
        )


# Base use case class
class BaseUseCase:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session


# Consumer of the Factory Method - LoginUseCase
class LoginUseCase(BaseUseCase):
    """
    LoginUseCase is the consumer (client) of the Factory Method pattern.

    It receives an AuthProviderFactory typed as the abstract interface —
    never a concrete factory. It calls create_provider() to obtain an
    AuthProvider, then calls authenticate() on it.

    The use case has zero knowledge of whether it is running a Google
    OAuth flow or a credential flow. That decision was made at the route
    layer when the concrete factory was selected and passed in (Option A).
    """

    def __init__(
        self,
        db_session: AsyncSession,
        factory: AuthProviderFactory,  # abstract type — decoupled from concrete factories
        token_svc,  # ITokenService; token issuance is out of scope here
    ) -> None:
        super().__init__(db_session)
        self._factory = factory
        self._token_svc = token_svc

    async def execute(self, payload: dict[str, str]) -> AuthResult:
        print("[LoginUseCase] Calling factory method: create_provider()")

        # Factory Method call — returns the correct concrete AuthProvider
        # without LoginUseCase knowing which concrete type it is.
        provider: AuthProvider = self._factory.create_provider()

        print("[LoginUseCase] Delegating authentication to provider...")

        # Authenticate using the provider — uniform interface regardless of concrete type.
        result: AuthResult = await provider.authenticate(payload)

        # Commit the session (e.g., persists any new OAuth account records).
        await self._db_session.commit()

        # Token issuance is out of scope — returning AuthResult directly.
        return result


# router layer — Factory Selection and Use Case Construction
class PasswordHasher:
    """Stub password hasher — simulates bcrypt or argon2."""

    def hash(self, raw: str) -> str:
        return f"hashed({raw})"

    def verify(self, raw: str, hashed: str) -> bool:
        return self.hash(raw) == hashed


class StubDbSession:
    """Stub AsyncSession — simulates SQLAlchemy async session commit."""

    async def commit(self):
        print("[StubDbSession] db_session.commit() called.")


class StubTokenService:
    """Stub token service — token issuance is out of scope."""

    def create_access_token(self, user_id: str) -> str:
        return f"token-for-{user_id}"


async def simulate_credential_login():
    """
    Simulates POST /auth/login.

    The route handler instantiates CredentialAuthProviderFactory directly
    (Option A) — this is the only place the concrete factory type appears.
    LoginUseCase receives it typed as the abstract AuthProviderFactory.
    """
    print("=" * 60)
    print("ROUTE: POST /auth/login  (Credential)")
    print("=" * 60)

    # Route layer: select and instantiate the correct concrete factory.
    # LoginUseCase is constructed with the factory typed as AuthProviderFactory.
    factory = CredentialAuthProviderFactory(password_hasher=PasswordHasher())

    use_case = LoginUseCase(
        db_session=StubDbSession(),
        factory=factory,  # passed as AuthProviderFactory (abstract)
        token_svc=StubTokenService(),
    )

    result = await use_case.execute(
        {"email": "customer@bukoo.my", "password": "correct_password"}
    )
    print(
        f"[Route] AuthResult → user_id={result.user_id}, "
        f"email={result.email}, provider={result.provider}\n"
    )


async def simulate_google_login():
    """
    Simulates POST /auth/login/google.

    The route handler instantiates GoogleAuthProviderFactory directly
    (Option A). LoginUseCase receives it typed as AuthProviderFactory —
    identical call structure to the credential flow above.
    """
    print("=" * 60)
    print("ROUTE: POST /auth/login/google  (Google OAuth)")
    print("=" * 60)

    # Route layer: select and instantiate the correct concrete factory.
    factory = GoogleAuthProviderFactory(
        client_id="bukoo-google-client-id",
        client_secret="bukoo-google-client-secret",
    )

    use_case = LoginUseCase(
        db_session=StubDbSession(),
        factory=factory,  # passed as AuthProviderFactory (abstract)
        token_svc=StubTokenService(),
    )

    result = await use_case.execute(
        {"code": "google-auth-code-xyz", "redirect_uri": "https://bukoo.my/callback"}
    )
    print(
        f"[Route] AuthResult → user_id={result.user_id}, "
        f"email={result.email}, provider={result.provider}\n"
    )


# entry point
if __name__ == "__main__":
    import asyncio

    asyncio.run(simulate_credential_login())
    asyncio.run(simulate_google_login())
