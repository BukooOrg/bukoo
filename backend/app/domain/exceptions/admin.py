from .base import DomainException


class AdminAccessRequiredError(DomainException):
    def __init__(self) -> None:
        super().__init__("Admin access required.")
