from __future__ import annotations

from abc import ABC, abstractmethod


class ICacheService(ABC):
    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Store value at key, with optional TTL in seconds."""
        pass

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Return the value at key, or None if missing or expired."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key. No-op if the key does not exist."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if key exists and has not expired."""
        pass
