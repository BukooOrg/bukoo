from .base import DomainException


class AddressNotFoundError(DomainException):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' does not have address.")
