from .base import DomainException


class AdminRoleRequiredError(DomainException):
    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(
            f"Administrative privileges are required to perform this action: {action}."
        )
