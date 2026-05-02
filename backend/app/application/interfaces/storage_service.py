from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class IStorageService(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """
        Upload data under key and return a presigned GET URL.
        """
        pass

    @abstractmethod
    async def load_once(self, key: str) -> bytes:
        """
        Download the entire object into memory and return it as bytes.
        """
        pass

    @abstractmethod
    def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        """
        Yield the object body in 8 MB chunks.

        Suitable for large files (e.g. bulk exports, large images) where
        loading the whole object into memory is undesirable.

        Usage:

            async for chunk in storage.load_stream("reports/q3.pdf"):
                response.write(chunk)
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Return True if an object with key exits in the bucket.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the object at key. No-op if the key does not exist."""
        pass

    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate and return a presigned GET URL for key.

        Args:
            key:        Object key in the bucket.
            expires_in: URL lifetime in seconds (default: 3 600 = 1 hour).
        """
        pass
