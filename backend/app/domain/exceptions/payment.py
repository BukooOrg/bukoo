from .base import DomainException


class PaymentCreationError(DomainException):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Failed to create payment order: {reason}")


class PaymentVerificationError(DomainException):
    def __init__(self) -> None:
        super().__init__("Payment signature verification failed.")
