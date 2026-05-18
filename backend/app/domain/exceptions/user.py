from .base import DomainException


class CustomerOnlyError(DomainException):
    def __init__(self) -> None:
        super().__init__("This action is only permitted for customer accounts.")


class UserAlreadySuspendedError(DomainException):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' is already suspended.")


class CannotSuspendAdminError(DomainException):
    def __init__(self) -> None:
        super().__init__("Admin accounts cannot be suspended.")


class UserAlreadyActiveError(DomainException):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' is already active.")


class CannotActivatePendingUserError(DomainException):
    def __init__(self) -> None:
        super().__init__(
            "Cannot activate a pending user. The user must verify their email first."
        )
