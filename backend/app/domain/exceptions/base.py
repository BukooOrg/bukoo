from typing import Any


class DomainException(Exception):
    """Base class for all domain exceptions (HTTP-agnostic)."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)
