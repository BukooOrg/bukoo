from fastapi import status

from app.application.errors.error_codes import ErrorCode
from app.domain.exceptions import (
    AdminAccessRequiredError,
    BookAlreadyExistsError,
    BookNotFoundError,
    DomainException,
    EmptyOrderError,
    FacebookOAuthError,
    GoogleOAuthError,
    InvalidCredentialsError,
    InvalidISBNError,
    InvalidTokenError,
    NoAuthHeaderError,
    OAuthProviderNotFoundError,
    OAuthStateInvalidError,
    OrderAlreadyPaidError,
    OrderNotFoundError,
    OutOfStockError,
    TokenAlreadyRevokedError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    UserNotVerifiedError,
    UserSuspendedError,
)


class HttpExceptionMapping:
    def __init__(self, status_code: int, code: ErrorCode, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


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
        NoAuthHeaderError().message,
    ),
    UserSuspendedError: HttpExceptionMapping(
        status.HTTP_403_FORBIDDEN,
        ErrorCode.USER_SUSPENDED,
        "Account is suspended",
    ),
    # Book
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
    OutOfStockError: HttpExceptionMapping(
        status.HTTP_409_CONFLICT,
        ErrorCode.OUT_OF_STOCK,
        "Out of stock",
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
}
