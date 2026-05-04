from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import (
    IAuthProviderFactory,
    ICacheService,
    IEmailNotificationService,
    IPasswordHasher,
    IStorageService,
    ITokenService,
)
from app.core.config import get_configs
from app.core.constants import ObjectStorageType, UserRole
from app.domain.entities import UserEntity
from app.domain.exceptions import InvalidTokenError, TokenExpiredError
from app.domain.repositories import (
    IAccountRepository,
    IUserRepository,
    IVerificationTokenRepository,
)
from app.infrastructure.auth import (
    BcryptPasswordHasher,
    CredentialAuthProviderFactory,
    GoogleAuthProviderFactory,
    JWTService,
)
from app.infrastructure.cache import RedisCacheService
from app.infrastructure.db.repositories import (
    AccountRepositoryImpl,
    UserRepositoryImpl,
    VerificationTokenRepositoryImpl,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.storage import MinIOStorage, S3Storage
from app.infrastructure.tasks.email_notification_service import (
    CeleryEmailNotificationService,
)

# DB session
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# Repositories
def get_user_repository(session: DbSession) -> IUserRepository:
    return UserRepositoryImpl(session)


def get_account_repository(session: DbSession) -> IAccountRepository:
    return AccountRepositoryImpl(session)


def get_verification_token_repository(
    session: DbSession,
) -> IVerificationTokenRepository:
    return VerificationTokenRepositoryImpl(session)


UserRepo = Annotated[IUserRepository, Depends(get_user_repository)]
AccountRepo = Annotated[IAccountRepository, Depends(get_account_repository)]
VerificationTokenRepo = Annotated[
    IVerificationTokenRepository, Depends(get_verification_token_repository)
]


# Cache
def get_cache_service() -> ICacheService:
    return RedisCacheService()


CacheService = Annotated[ICacheService, Depends(get_cache_service)]


#  Auth infrastructure
def get_password_hasher() -> IPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service() -> ITokenService:
    return JWTService()


PasswordHasher = Annotated[IPasswordHasher, Depends(get_password_hasher)]
TokenService = Annotated[ITokenService, Depends(get_token_service)]


# Factory Method pattern: auth provider factory selection
def get_credential_factory(
    user_repo: UserRepo,
    hasher: PasswordHasher,
) -> IAuthProviderFactory:
    return CredentialAuthProviderFactory(user_repo=user_repo, hasher=hasher)


def get_google_factory(
    user_repo: UserRepo, account_repo: AccountRepo
) -> IAuthProviderFactory:
    return GoogleAuthProviderFactory(user_repo=user_repo, account_repo=account_repo)


CredentialAuthFactory = Annotated[IAuthProviderFactory, Depends(get_credential_factory)]
GoogleAuthFactory = Annotated[IAuthProviderFactory, Depends(get_google_factory)]


# Storage
def get_storage_service() -> IStorageService:
    configs = get_configs()

    match configs.STORAGE_TYPE:
        case ObjectStorageType.MINIO:
            return MinIOStorage()
        case ObjectStorageType.S3:
            return S3Storage()
        case _:
            raise ValueError(f"unsupported storage type {configs.STORAGE_TYPE}")


StorageService = Annotated[IStorageService, Depends(get_storage_service)]


# Email notification
def get_email_notification_service() -> IEmailNotificationService:
    return CeleryEmailNotificationService()


EmailNotificationService = Annotated[
    IEmailNotificationService, Depends(get_email_notification_service)
]

# Current user guard
_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    user_repo: UserRepo,
    token_svc: TokenService,
) -> UserEntity:
    try:
        payload = token_svc.decode_token(credentials.credentials)
        user_id = str(payload.get("sub", ""))
    except (InvalidTokenError, TokenExpiredError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_repo.find_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


async def require_admin(current_user: CurrentUser) -> UserEntity:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


AdminUser = Annotated[UserEntity, Depends(require_admin)]
