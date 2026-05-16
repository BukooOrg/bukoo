from .base import DomainException


class PublisherNotFoundError(DomainException):
    def __init__(self, publisher_id: str) -> None:
        self.publisher_id = publisher_id
        super().__init__(f"Publisher '{publisher_id}' not found.")
