from .base import DomainException


class AuthorNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Author '{identifier}' not found.")
