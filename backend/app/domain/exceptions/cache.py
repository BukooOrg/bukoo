from .base import DomainException


class CacheWriteError(DomainException):
    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Failed to write cache key '{key}': {reason}")


class CacheReadError(DomainException):
    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Failed to read cache key '{key}': {reason}")


class CacheDeleteError(DomainException):
    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Failed to delete cache key '{key}': {reason}")
