from .base import DomainException


class CategoryAlreadyExistsError(DomainException):
    def __init__(self, url_slug: str) -> None:
        self.url_slug = url_slug
        super().__init__(f"A category with url_slug '{url_slug}' already exists.")


class CategoryNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Category '{identifier}' not found.")
