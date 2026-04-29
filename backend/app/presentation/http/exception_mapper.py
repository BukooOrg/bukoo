from fastapi import status

from app.application.errors.error_codes import ErrorCode
from app.domain.exceptions import (
    BookAlreadyExistsError,
    BookNotFoundError,
    DomainException,
    EmptyOrderError,
    InvalidCredentialsError,
    InvalidISBNError,
    InvalidTokenError,
    OrderAlreadyPaidError,
    OrderNotFoundError,
    OutOfStockError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserNotFoundError,
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
}
