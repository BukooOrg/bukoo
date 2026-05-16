from .base import DomainException


class ReviewNotEligibleError(DomainException):
    def __init__(self, order_item_id: str) -> None:
        self.order_item_id = order_item_id
        super().__init__(
            f"No DELIVERED order item '{order_item_id}' found for this user and book."
        )


class ReviewAlreadyExistsError(DomainException):
    def __init__(self, order_item_id: str) -> None:
        self.order_item_id = order_item_id
        super().__init__(f"A review for order item '{order_item_id}' already exists.")
