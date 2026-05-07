from __future__ import annotations

from .admin import AdminAccessRequiredError
from .auth import (
    FacebookOAuthError,
    GoogleOAuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    NoAuthHeaderError,
    OAuthProviderNotFoundError,
    OAuthStateInvalidError,
    TokenAlreadyRevokedError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    UserNotVerifiedError,
    UserSuspendedError,
)
from .base import DomainException
from .book import (
    BookAlreadyExistsError,
    BookNotFoundError,
    InvalidISBNError,
)
from .cache import CacheDeleteError, CacheReadError, CacheWriteError
from .order import (
    EmptyOrderError,
    OrderAlreadyPaidError,
    OrderNotFoundError,
    OutOfStockError,
)
from .payment import (
    PaymentCreationError,
    PaymentVerificationError,
)
from .storage import (
    FileSizeExceededError,
    InvalidFileTypeError,
    StorageNotFoundError,
    StorageUploadError,
)
from .user import CustomerOnlyError

__all__ = [
    "DomainException",
    "FacebookOAuthError",
    "GoogleOAuthError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "NoAuthHeaderError",
    "OAuthProviderNotFoundError",
    "OAuthStateInvalidError",
    "TokenAlreadyRevokedError",
    "TokenExpiredError",
    "UserAlreadyExistsError",
    "UserAlreadyVerifiedError",
    "UserNotFoundError",
    "UserNotVerifiedError",
    "UserSuspendedError",
    "BookAlreadyExistsError",
    "BookNotFoundError",
    "InvalidISBNError",
    "OrderNotFoundError",
    "OrderAlreadyPaidError",
    "OutOfStockError",
    "EmptyOrderError",
    "PaymentCreationError",
    "PaymentVerificationError",
    "InvalidFileTypeError",
    "FileSizeExceededError",
    "StorageUploadError",
    "StorageNotFoundError",
    "CacheWriteError",
    "CacheReadError",
    "CacheDeleteError",
    "AdminAccessRequiredError",
    "CustomerOnlyError",
]
