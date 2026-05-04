from __future__ import annotations

from abc import ABC, abstractmethod


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, subject: str) -> str:
        pass

    @abstractmethod
    def decode_token(
        self,
        token: str,
        *,
        verify_exp: bool = True,
    ) -> dict[str, object]:
        pass

    @abstractmethod
    async def revoke_token(self, payload: dict[str, object]) -> None:
        """Store the token's JTI in the blocklist until the token naturally expires."""
        pass

    @abstractmethod
    async def is_token_revoked(self, jti: str) -> bool:
        """Return True if the given JTI has been blocklisted."""
        pass
