from .base import DomainException


class AddressNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User '{identifier}' does not have address.")
