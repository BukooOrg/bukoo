from __future__ import annotations

from abc import ABC, abstractmethod


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, subject: str) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, object]:
        pass
