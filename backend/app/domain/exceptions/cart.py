from .base import DomainException


class CartNotFoundError(DomainException):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"Cart by user {user_id} not found.")


class CartItemNotFoundError(DomainException):
    def __init__(self, cart_item_id: str) -> None:
        super().__init__(f"Cart item {cart_item_id} not found.")
