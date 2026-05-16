from .base import DomainException


class BookNotFoundError(DomainException):
    def __init__(self, book_id: str) -> None:
        self.book_id = book_id
        super().__init__(f"Book {book_id} not found.")


class BookAlreadyExistsError(DomainException):
    def __init__(self, isbn: str) -> None:
        self.isbn = isbn
        super().__init__(f"A book with ISBN {isbn} already exists.")


class InvalidISBNError(DomainException):
    def __init__(self, isbn: str) -> None:
        self.isbn = isbn
        super().__init__(f"'{isbn}' is not a valid ISBN-13.")


class BookAlreadyDeactivatedError(DomainException):
    def __init__(self, book_id: str) -> None:
        super().__init__(f"Book {book_id} already deactivated.")


class BookAlreadyActivatedError(DomainException):
    def __init__(self, book_id: str) -> None:
        super().__init__(f"Book {book_id} already Activated.")
