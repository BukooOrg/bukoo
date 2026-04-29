from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dtos.auth_dto import AuthResult


class IAuthStrategy(ABC):
    @abstractmethod
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        pass
