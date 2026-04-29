from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.auth_provider import IAuthStrategy
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.application.interfaces.storage_service import IStorageService
from app.application.interfaces.token_service import ITokenService
from app.core.config import get_configs
from app.core.constants import ObjectStorageType, UserRole
from app.domain.entities.user import UserEntity
from app.domain.exceptions import InvalidTokenError, TokenExpiredError
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.credential_provider import CredentialProvider
from app.infrastructure.auth.google_provider import GoogleProvider
from app.infrastructure.auth.jwt_service import JWTService
from app.infrastructure.auth.password_hasher import BcryptPasswordHasher
from app.infrastructure.db.repositories.account_repository_impl import (
    AccountRepositoryImpl,
)
from app.infrastructure.db.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.db.session import get_db_session
from app.infrastructure.storage.minio_storage import MinIOStorage
from app.infrastructure.storage.s3_storage import S3Storage
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


UserRepo = Annotated[IUserRepository, Depends(get_user_repository)]
AccountRepo = Annotated[IAccountRepository, Depends(get_account_repository)]


#  Auth infrastructure
def get_password_hasher() -> IPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service() -> ITokenService:
    return JWTService()


PasswordHasher = Annotated[IPasswordHasher, Depends(get_password_hasher)]
TokenService = Annotated[ITokenService, Depends(get_token_service)]


# Strategy pattern: auth provider selection
def get_credential_strategy(
    user_repo: UserRepo,
    hasher: PasswordHasher,
) -> IAuthStrategy:
    return CredentialProvider(user_repo=user_repo, hasher=hasher)


def get_google_strategy(
    user_repo: UserRepo, account_repo: AccountRepo
) -> IAuthStrategy:
    return GoogleProvider(user_repo=user_repo, account_repo=account_repo)


CredentialStrategy = Annotated[IAuthStrategy, Depends(get_credential_strategy)]
GoogleStrategy = Annotated[IAuthStrategy, Depends(get_google_strategy)]


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
