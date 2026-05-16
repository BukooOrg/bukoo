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


class ReviewNotFoundError(DomainException):
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(f"Review '{review_id}' not found.")


class ReviewNotOwnedError(DomainException):
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(f"Review '{review_id}' does not belong to the current user.")
