from .base import DomainException


class OrderNotFoundError(DomainException):
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Order '{order_id}' not found.")


class OrderAlreadyPaidError(DomainException):
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Order '{order_id}' has already been paid.")


class OutOfStockError(DomainException):
    def __init__(self, book_id: str, requested: int, available: int) -> None:
        self.book_id = book_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Book '{book_id}' has only {available} in stock "
            f"but {requested} were requested."
        )


class EmptyOrderError(DomainException):
    def __init__(self) -> None:
        super().__init__("An order must contain at least one item.")


class OrderNotPayableError(DomainException):
    def __init__(self, order_id: str, current_status: str) -> None:
        self.order_id = order_id
        self.current_status = current_status
        super().__init__(
            f"Order '{order_id}' cannot be paid because its status is '{current_status}'."
        )


class OrderAccessDeniedError(DomainException):
    def __init__(self) -> None:
        super().__init__("Order access denied.")
