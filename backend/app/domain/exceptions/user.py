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


class CannotResetAdminPasswordError(DomainException):
    def __init__(self) -> None:
        super().__init__("Admin account passwords cannot be reset by another admin.")


class UserHasNoCredentialAccountError(DomainException):
    def __init__(self) -> None:
        super().__init__(
            "This account uses social login and does not have a password to reset."
        )


class CannotSoftDeleteAdminError(DomainException):
    def __init__(self) -> None:
        super().__init__("Admin accounts cannot be soft-deleted.")


class CannotDeleteSelfError(DomainException):
    def __init__(self) -> None:
        super().__init__(
            "You cannot delete your own account. Use account settings instead."
        )
