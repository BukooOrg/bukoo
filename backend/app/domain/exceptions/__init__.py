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
from .author import AuthorNotFoundError
from .base import DomainException
from .book import (
    BookAlreadyActivatedError,
    BookAlreadyDeactivatedError,
    BookAlreadyExistsError,
    BookNotFoundError,
    InvalidISBNError,
)
from .cache import CacheDeleteError, CacheReadError, CacheWriteError
from .cart import CartItemNotFoundError, CartNotFoundError
from .category import CategoryAlreadyExistsError, CategoryNotFoundError
from .collection import CollectionAlreadyExistsError, CollectionNotFoundError
from .order import (
    EmptyOrderError,
    OrderAccessDeniedError,
    OrderAlreadyPaidError,
    OrderNotCancellableError,
    OrderNotFoundError,
    OrderNotPayableError,
    OutOfStockError,
)
from .payment import (
    PaymentCreationError,
    PaymentVerificationError,
)
from .publisher import PublisherNotFoundError
from .storage import (
    FileSizeExceededError,
    InvalidFileTypeError,
    StorageNotFoundError,
    StorageUploadError,
)
from .user import CustomerOnlyError
from .wishlist import (
    WishlistItemAlreadyExistsError,
    WishlistItemNotFoundError,
    WishlistNotFoundError,
)

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
    "BookAlreadyActivatedError",
    "BookAlreadyDeactivatedError",
    "BookAlreadyExistsError",
    "BookNotFoundError",
    "InvalidISBNError",
    "CategoryAlreadyExistsError",
    "CategoryNotFoundError",
    "CollectionAlreadyExistsError",
    "CollectionNotFoundError",
    "OrderNotFoundError",
    "OrderAlreadyPaidError",
    "OrderNotPayableError",
    "OutOfStockError",
    "OrderAccessDeniedError",
    "OrderNotCancellableError",
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
    "AuthorNotFoundError",
    "PublisherNotFoundError",
    "CartNotFoundError",
    "CartItemNotFoundError",
    "WishlistItemAlreadyExistsError",
    "WishlistNotFoundError",
    "WishlistItemNotFoundError",
]
