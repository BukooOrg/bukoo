from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.constants import VerificationTokenType
from app.domain.entities.verification_token_entity import VerificationTokenEntity


class IVerificationTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: VerificationTokenEntity) -> None:
        pass

    @abstractmethod
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
        """Return the most recent non-expired, non-used token of the given type for the user."""
        pass
