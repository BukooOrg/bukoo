from .base import DomainException


class CollectionAlreadyExistsError(DomainException):
    def __init__(self, url_slug: str) -> None:
        self.url_slug = url_slug
        super().__init__(f"A collection with url_slug '{url_slug}' already exists.")


class CollectionNotFoundError(DomainException):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Collection '{identifier}' not found.")
