from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends, Request
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
from app.application.interfaces.payment_service import IPaymentService
from app.core.config import get_configs
from app.core.constants import ObjectStorageType, UserRole
from app.domain.entities import UserEntity
from app.domain.exceptions import (
    AdminAccessRequiredError,
    CustomerOnlyError,
    InvalidCredentialsError,
    InvalidTokenError,
    NoAuthHeaderError,
    TokenAlreadyRevokedError,
)
from app.domain.repositories import (
    IAccountRepository,
    IAddressRepository,
    IAuthorRepository,
    IBookRepository,
    ICartRepository,
    ICategoryRepository,
    ICollectionRepository,
    INotificationRepository,
    IOrderRepository,
    IPaymentRepository,
    IPublisherRepository,
    IUserRepository,
    IVerificationTokenRepository,
    IWishlistRepository,
)
from app.infrastructure.auth import (
    BcryptPasswordHasher,
    CredentialAuthProviderFactory,
    FacebookAuthProviderFactory,
    GoogleAuthProviderFactory,
    JWTService,
)
from app.infrastructure.cache import RedisCacheService
from app.infrastructure.db.repositories import (
    AccountRepositoryImpl,
    AddressRepositoryImpl,
    AuthorRepositoryImpl,
    BookRepositoryImpl,
    CartRepositoryImpl,
    CategoryRepositoryImpl,
    CollectionRepositoryImpl,
    NotificationRepositoryImpl,
    OrderRepositoryImpl,
    PaymentRepositoryImpl,
    PublisherRepositoryImpl,
    UserRepositoryImpl,
    VerificationTokenRepositoryImpl,
    WishlistRepositoryImpl,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.payment.payment_service_impl import PaymentServiceImpl
from app.infrastructure.storage import MinIOStorage, S3Storage
from app.infrastructure.tasks.email_notification_service import (
    CeleryEmailNotificationService,
)

logger = structlog.getLogger(__name__)

# DB session
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# Repositories
def get_user_repository(session: DbSession) -> IUserRepository:
    return UserRepositoryImpl(session)


UserRepo = Annotated[IUserRepository, Depends(get_user_repository)]


def get_account_repository(session: DbSession) -> IAccountRepository:
    return AccountRepositoryImpl(session)


AccountRepo = Annotated[IAccountRepository, Depends(get_account_repository)]


def get_verification_token_repository(
    session: DbSession,
) -> IVerificationTokenRepository:
    return VerificationTokenRepositoryImpl(session)


VerificationTokenRepo = Annotated[
    IVerificationTokenRepository, Depends(get_verification_token_repository)
]


def get_address_repository(session: DbSession) -> IAddressRepository:
    return AddressRepositoryImpl(session)


AddressRepo = Annotated[IAddressRepository, Depends(get_address_repository)]


def get_category_repository(session: DbSession) -> ICategoryRepository:
    return CategoryRepositoryImpl(session)


CategoryRepo = Annotated[ICategoryRepository, Depends(get_category_repository)]


def get_author_repository(session: DbSession) -> IAuthorRepository:
    return AuthorRepositoryImpl(session)


AuthorRepo = Annotated[IAuthorRepository, Depends(get_author_repository)]


def get_book_repository(session: DbSession) -> IBookRepository:
    return BookRepositoryImpl(session)


BookRepo = Annotated[IBookRepository, Depends(get_book_repository)]


def get_publisher_repository(session: DbSession) -> IPublisherRepository:
    return PublisherRepositoryImpl(session)


PublisherRepo = Annotated[IPublisherRepository, Depends(get_publisher_repository)]


def get_collection_repository(session: DbSession) -> ICollectionRepository:
    return CollectionRepositoryImpl(session)


CollectionRepo = Annotated[ICollectionRepository, Depends(get_collection_repository)]


def get_cart_repository(session: DbSession) -> ICartRepository:
    return CartRepositoryImpl(session)


CartRepo = Annotated[ICartRepository, Depends(get_cart_repository)]


def get_wishlist_repository(session: DbSession) -> IWishlistRepository:
    return WishlistRepositoryImpl(session)


WishlistRepo = Annotated[IWishlistRepository, Depends(get_wishlist_repository)]


def get_order_repository(session: DbSession) -> IOrderRepository:
    return OrderRepositoryImpl(session)


OrderRepo = Annotated[IOrderRepository, Depends(get_order_repository)]


def get_payment_repository(session: DbSession) -> IPaymentRepository:
    return PaymentRepositoryImpl(session)


PaymentRepo = Annotated[IPaymentRepository, Depends(get_payment_repository)]


def get_notification_repository(session: DbSession) -> INotificationRepository:
    return NotificationRepositoryImpl(session)


NotificationRepo = Annotated[
    INotificationRepository, Depends(get_notification_repository)
]


def get_payment_service() -> IPaymentService:
    return PaymentServiceImpl()


PaymentSvc = Annotated[IPaymentService, Depends(get_payment_service)]


# Cache
def get_cache_service() -> ICacheService:
    return RedisCacheService()


CacheService = Annotated[ICacheService, Depends(get_cache_service)]


#  Auth infrastructure
def get_password_hasher() -> IPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service(cache_svc: CacheService) -> ITokenService:
    return JWTService(cache_svc=cache_svc)


PasswordHasher = Annotated[IPasswordHasher, Depends(get_password_hasher)]
TokenService = Annotated[ITokenService, Depends(get_token_service)]


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


# Factory Method pattern: auth provider factory selection
def get_credential_factory(
    user_repo: UserRepo,
    hasher: PasswordHasher,
) -> IAuthProviderFactory:
    return CredentialAuthProviderFactory(user_repo=user_repo, hasher=hasher)


def get_google_factory(
    user_repo: UserRepo, account_repo: AccountRepo, storage_svc: StorageService
) -> IAuthProviderFactory:
    configs = get_configs()
    return GoogleAuthProviderFactory(
        user_repo=user_repo,
        account_repo=account_repo,
        storage_svc=storage_svc,
        client_id=configs.GOOGLE_CLIENT_ID.get_secret_value(),
        client_secret=configs.GOOGLE_CLIENT_SECRET.get_secret_value(),
        redirect_uri=configs.GOOGLE_REDIRECT_URI,
    )


def get_facebook_factory(
    user_repo: UserRepo, account_repo: AccountRepo, storage_svc: StorageService
) -> IAuthProviderFactory:
    configs = get_configs()
    return FacebookAuthProviderFactory(
        user_repo=user_repo,
        account_repo=account_repo,
        storage_svc=storage_svc,
        client_id=configs.FACEBOOK_CLIENT_ID.get_secret_value(),
        client_secret=configs.FACEBOOK_CLIENT_SECRET.get_secret_value(),
        redirect_uri=configs.FACEBOOK_REDIRECT_URI,
    )


CredentialAuthFactory = Annotated[IAuthProviderFactory, Depends(get_credential_factory)]
GoogleAuthFactory = Annotated[IAuthProviderFactory, Depends(get_google_factory)]
FacebookAuthFactory = Annotated[IAuthProviderFactory, Depends(get_facebook_factory)]


# OAuth provider registry (factory method: maps provider name → IAuthProviderFactory)
def get_oauth_provider_registry(
    google_factory: GoogleAuthFactory,
    facebook_factory: FacebookAuthFactory,
) -> dict[str, IAuthProviderFactory]:
    return {"google": google_factory, "facebook": facebook_factory}


OAuthProviderRegistry = Annotated[
    dict[str, IAuthProviderFactory], Depends(get_oauth_provider_registry)
]


# Email notification
def get_email_notification_service() -> IEmailNotificationService:
    return CeleryEmailNotificationService()


EmailNotificationService = Annotated[
    IEmailNotificationService, Depends(get_email_notification_service)
]

# Current user guard
_bearer = HTTPBearer(auto_error=False)


TokenPayloadObj = dict[str, object]


async def get_token_payload(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    token_svc: TokenService,
) -> TokenPayloadObj:
    token: str | None = None

    if credentials is not None:
        token = credentials.credentials
    else:
        cookie_value = request.cookies.get("access_token")
        if cookie_value and cookie_value.startswith("Bearer "):
            token = cookie_value.removeprefix("Bearer ")

    if token is None:
        raise NoAuthHeaderError

    try:
        payload = token_svc.decode_token(token, verify_exp=False)
    except InvalidTokenError as exc:
        raise exc

    jti = str(payload.get("jti", ""))
    if jti and await token_svc.is_token_revoked(jti):
        raise TokenAlreadyRevokedError

    return payload


TokenPayload = Annotated[TokenPayloadObj, Depends(get_token_payload)]


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
    user_repo: UserRepo,
) -> UserEntity:
    user_id = str(payload.get("sub", ""))

    user = await user_repo.find_by_id(user_id)
    if user is None or not user.is_active:
        raise InvalidCredentialsError

    return user


CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


async def require_admin(current_user: CurrentUser) -> UserEntity:
    if current_user.role != UserRole.ADMIN:
        raise AdminAccessRequiredError
    return current_user


AdminUser = Annotated[UserEntity, Depends(require_admin)]


async def require_customer(current_user: CurrentUser) -> UserEntity:
    if current_user.role != UserRole.USER:
        raise CustomerOnlyError
    return current_user


CustomerUser = Annotated[UserEntity, Depends(require_customer)]
