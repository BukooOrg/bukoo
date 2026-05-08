from .base import DomainException


class CollectionAlreadyExistsError(DomainException):
    def __init__(self, url_slug: str) -> None:
        self.url_slug = url_slug
        super().__init__(f"A collection with url_slug '{url_slug}' already exists.")
