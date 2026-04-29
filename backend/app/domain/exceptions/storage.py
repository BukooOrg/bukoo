from .base import DomainException


class StorageUploadError(DomainException):
    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Failed to upload '{key}': {reason}")


class StorageNotFoundError(DomainException):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Object '{key}' is not found.")
