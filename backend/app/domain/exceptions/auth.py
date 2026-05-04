from .base import DomainException


class InvalidCredentialsError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class UserAlreadyExistsError(DomainException):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"A user with email '{email}' already exists.")


class UserNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User '{identifier}' not found.")


class TokenExpiredError(DomainException):
    def __init__(self) -> None:
        super().__init__("Token has expired.")


class InvalidTokenError(DomainException):
    def __init__(self) -> None:
        super().__init__("Token is invalid.")


class UserNotVerifiedError(DomainException):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(
            f"Account '{email}' has not been verified. "
            "Please check your email for the verification link."
        )


class UserAlreadyVerifiedError(DomainException):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Account '{email}' is already verified.")
