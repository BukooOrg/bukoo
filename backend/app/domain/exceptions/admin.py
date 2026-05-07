from .base import DomainException


class AdminAccessRequiredError(DomainException):
    def __init__(self) -> None:
        super().__init__("Admin access required.")


class CustomerOnlyError(DomainException):
    def __init__(self) -> None:
        super().__init__("This action is not permitted for admin accounts.")
