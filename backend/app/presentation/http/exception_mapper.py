from collections.abc import Callable

from fastapi import status

from app.application.errors.error_codes import ErrorCode
from app.core.constants import OrderStatus
from app.domain.exceptions import (
    AddressNotFoundError,
    AdminAccessRequiredError,
    AuthorNotFoundError,
    BookAlreadyActivatedError,
    BookAlreadyDeactivatedError,
    BookAlreadyExistsError,
    BookNotFoundError,
    CannotActivatePendingUserError,
    CannotResetAdminPasswordError,
    CannotSoftDeleteAdminError,
    CannotSuspendAdminError,
    CartItemNotFoundError,
    CartNotFoundError,
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    CurrentPasswordIncorrectError,
    CustomerOnlyError,
    DomainException,
    EmptyOrderError,
    FacebookOAuthError,
    FileSizeExceededError,
    GoogleOAuthError,
    InvalidCredentialsError,
    InvalidFileTypeError,
    InvalidISBNError,
    InvalidTokenError,
    NewPasswordSameAsCurrentError,
    NoAuthHeaderError,
    OAuthProviderNotFoundError,
    OAuthStateInvalidError,
    OrderAccessDeniedError,
    OrderAlreadyPaidError,
    OrderNotCancellableError,
    OrderNotFoundError,
    OrderNotPayableError,
    OrderStatusTransitionInvalidError,
    OutOfStockError,
    PasswordNotSetError,
    PublisherNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotEligibleError,
    ReviewNotFoundError,
    ReviewNotOwnedError,
    StorageUploadError,
    TokenAlreadyRevokedError,
    TokenExpiredError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserAlreadySuspendedError,
    UserAlreadyVerifiedError,
    UserHasNoCredentialAccountError,
    UserNotFoundError,
    UserNotVerifiedError,
    UserSuspendedError,
    WishlistItemAlreadyExistsError,
    WishlistItemNotFoundError,
    WishlistNotFoundError,
)


class HttpExceptionMapping:
    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        message: str | Callable[[DomainException], str],
    ):
        self.status_code = status_code
        self.code = code
        self.message = message


def get_order_not_cancellable_message(exc: DomainException) -> str:
    """
    Constructs a contextual error message for order cancellation failures.
    Provides additional debugging metadata for administrators.
    """
    if exc.context.get("is_admin"):
        allowed: list[OrderStatus] = exc.context.get(
            "allowed_cancelled_status_for_admin", "None"
        )
        return (
            f"{exc.message} Allowed cancelled statuses for admin: {', '.join(allowed)}"
        )

    return exc.message


EXCEPTION_MAP: dict[type[DomainException], HttpExceptionMapping] = {
    # Auth
    InvalidCredentialsError: HttpExceptionMapping(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.INVALID_CREDENTIALS,
        "Invalid credentials",
    ),
    UserNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.USER_NOT_FOUND,
        "User not found",
    ),
    UserAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.USER_ALREADY_EXISTS,
        "User already exists",
    ),
    UserAlreadySuspendedError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.USER_ALREADY_SUSPENDED,
        "User is already suspended",
    ),
    CannotSuspendAdminError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.CANNOT_SUSPEND_ADMIN,
        "Admin accounts cannot be suspended",
    ),
    UserAlreadyActiveError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.USER_ALREADY_ACTIVE,
        "User is already active",
    ),
    CannotActivatePendingUserError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.CANNOT_ACTIVATE_PENDING_USER,
        "Cannot activate a pending user. The user must verify their email first.",
    ),
    CannotResetAdminPasswordError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.CANNOT_RESET_ADMIN_PASSWORD,
        "Admin account passwords cannot be reset by another admin.",
    ),
    CannotSoftDeleteAdminError: HttpExceptionMapping(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCode.CANNOT_SOFT_DELETE_ADMIN,
        "Admin accounts cannot be soft-deleted.",
    ),
    UserHasNoCredentialAccountError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.USER_HAS_NO_CREDENTIAL_ACCOUNT,
        "This account uses social login and does not have a password to reset.",
    ),
    UserAlreadyVerifiedError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.USER_ALREADY_VERIFIED,
        "User already verified",
    ),
    TokenExpiredError: HttpExceptionMapping(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.TOKEN_EXPIRED,
        "Token expired",
    ),
    InvalidTokenError: HttpExceptionMapping(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.INVALID_TOKEN,
        "Invalid token",
    ),
    TokenAlreadyRevokedError: HttpExceptionMapping(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.TOKEN_REVOKED,
        "Token has been revoked",
    ),
    UserNotVerifiedError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.USER_NOT_VERIFIED,
        "Account email not verified",
    ),
    NoAuthHeaderError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.NOT_AUTH_HEADER,
        lambda exc: exc.message,
    ),
    UserSuspendedError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.USER_SUSPENDED,
        "Account is suspended",
    ),
    CurrentPasswordIncorrectError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.CURRENT_PASSWORD_INCORRECT,
        "The current password you entered is incorrect. Please double-check and try again.",
    ),
    PasswordNotSetError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.PASSWORD_NOT_SET,
        "Your account is linked to a social login (like Google or Facebook) and does not have a password. Please sign in with email and try again.",
    ),
    NewPasswordSameAsCurrentError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.NEW_PASSWORD_SAME_AS_CURRENT,
        "Your new password must be different from your current one. Please choose a new, unique password.",
    ),
    # Book
    BookAlreadyActivatedError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.BOOK_ALREADY_ACTIVATED,
        "Book already activated",
    ),
    BookAlreadyDeactivatedError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.BOOK_ALREADY_DEACTIVATED,
        "Book already deactivated",
    ),
    BookNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.BOOK_NOT_FOUND,
        "Book not found",
    ),
    BookAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.BOOK_ALREADY_EXISTS,
        "Book already exists",
    ),
    InvalidISBNError: HttpExceptionMapping(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCode.INVALID_ISBN,
        "Invalid ISBN",
    ),
    # Order
    OrderNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.ORDER_NOT_FOUND,
        "Order not found",
    ),
    OrderAlreadyPaidError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.ORDER_ALREADY_PAID,
        "Order already paid",
    ),
    OrderNotPayableError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.ORDER_NOT_PAYABLE,
        lambda exc: exc.message,
    ),
    OutOfStockError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT, ErrorCode.OUT_OF_STOCK, "Out of stock."
    ),
    OrderAccessDeniedError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.ORDER_ACCESS_DENIED,
        "You do not have permission to access this order.",
    ),
    OrderNotCancellableError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.ORDER_NOT_CANCELLABLE,
        get_order_not_cancellable_message,
    ),
    OrderStatusTransitionInvalidError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.ORDER_STATUS_TRANSITION_INVALID,
        lambda exc: exc.message,
    ),
    EmptyOrderError: HttpExceptionMapping(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCode.EMPTY_ORDER,
        "Order cannot be empty",
    ),
    AdminAccessRequiredError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.ADMIN_ACCESS_REQUIRED,
        "Admin access required.",
    ),
    CustomerOnlyError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.FORBIDDEN,
        "This action is not permitted for admin accounts.",
    ),
    # OAuth
    OAuthStateInvalidError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.OAUTH_STATE_INVALID,
        "OAuth state token is invalid or expired",
    ),
    OAuthProviderNotFoundError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.OAUTH_PROVIDER_NOT_FOUND,
        "OAuth provider not supported",
    ),
    GoogleOAuthError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.GOOGLE_OAUTH_ERROR,
        "Google OAuth request failed",
    ),
    FacebookOAuthError: HttpExceptionMapping(
        status.HTTP_400_BAD_REQUEST,
        ErrorCode.FACEBOOK_OAUTH_ERROR,
        "Facebook OAuth authentication failed",
    ),
    # Storage
    StorageUploadError: HttpExceptionMapping(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.STORAGE_UPLOAD_FAILED,
        "Storage upload failed",
    ),
    FileSizeExceededError: HttpExceptionMapping(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.FILE_SIZE_EXCEEDED,
        lambda exc: exc.message,
    ),
    InvalidFileTypeError: HttpExceptionMapping(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.INVALID_FILE_TYPE,
        lambda exc: exc.message,
    ),
    # Category
    CategoryAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.CATEGORY_ALREADY_EXISTS,
        lambda exc: exc.message,
    ),
    CategoryNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.CATEGORY_NOT_FOUND,
        "Category not found.",
    ),
    # Collection
    CollectionAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.COLLECTION_ALREADY_EXISTS,
        lambda exc: exc.message,
    ),
    CollectionNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.COLLECTION_NOT_FOUND,
        "Collection not found.",
    ),
    # address
    AddressNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.ADDRESS_NOT_FOUND,
        "You do not have address",
    ),
    # author
    AuthorNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.AUTHOR_NOT_FOUND,
        "You do not have author",
    ),
    # publisher
    PublisherNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.PUBLISHER_NOT_FOUND,
        "Publisher not found.",
    ),
    # cart
    CartNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.CART_NOT_FOUND,
        "Cart not found.",
    ),
    CartItemNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.CART_ITEM_NOT_FOUND,
        "Cart item not found.",
    ),
    # review
    ReviewNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.REVIEW_NOT_FOUND,
        "Review not found.",
    ),
    ReviewNotOwnedError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.REVIEW_NOT_OWNED,
        "You do not have permission to modify this review.",
    ),
    # wishlist
    ReviewNotEligibleError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.REVIEW_NOT_ELIGIBLE,
        lambda exc: exc.message,
    ),
    ReviewAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.REVIEW_ALREADY_EXISTS,
        lambda exc: exc.message,
    ),
    WishlistItemAlreadyExistsError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.WISHLIST_ITEM_ALREADY_EXISTS_FOUND,
        "Wishlist item already exists",
    ),
    WishlistNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.WISHLIST_NOT_FOUND,
        "Wishlist not found.",
    ),
    WishlistItemNotFoundError: HttpExceptionMapping(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.WISHLIST_ITEM_NOT_FOUND,
        "Wishlist item not found.",
    ),
}
