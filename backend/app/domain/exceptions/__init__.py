from __future__ import annotations

from .address import AddressNotFoundError
from .admin import AdminAccessRequiredError
from .auth import (
    CurrentPasswordIncorrectError,
    FacebookOAuthError,
    GoogleOAuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    NewPasswordSameAsCurrentError,
    NoAuthHeaderError,
    OAuthProviderNotFoundError,
    OAuthStateInvalidError,
    PasswordNotSetError,
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
from .collection import CollectionAlreadyExistsError
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
    "CollectionAlreadyExistsError",
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
    "AddressNotFoundError",
    "CurrentPasswordIncorrectError",
    "PasswordNotSetError",
    "NewPasswordSameAsCurrentError",
]
