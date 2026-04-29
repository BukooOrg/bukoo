from __future__ import annotations

from abc import ABC, abstractmethod


class IStorageService(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        pass
