from .base import DomainException


class CustomerOnlyError(DomainException):
    def __init__(self) -> None:
        super().__init__("This action is only permitted for customer accounts.")
