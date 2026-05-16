from .base import DomainException


class WishlistNotFoundError(DomainException):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"Wishlist by user {user_id} not found.")


class WishlistItemNotFoundError(DomainException):
    def __init__(self, wishlist_item_id: str) -> None:
        super().__init__(f"Wishlist item {wishlist_item_id} not found.")


class WishlistItemAlreadyExistsError(DomainException):
    def __init__(self, book_id: str) -> None:
        super().__init__(f"Book {book_id} in wishlist already exists.")
