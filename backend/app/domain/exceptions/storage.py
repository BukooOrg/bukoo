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


class InvalidFileTypeError(DomainException):
    def __init__(self, allowed_file_types: set[str]) -> None:
        super().__init__(
            f"Invalid file type. Allowed: {', '.join(allowed_file_types)}."
        )


class FileSizeExceededError(DomainException):
    def __init__(self, size: int, unit: str) -> None:
        super().__init__(f"File too large. Maximum size is {size} {unit}.")
