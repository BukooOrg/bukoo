from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.interfaces.auth_provider import IAuthProvider


class IAuthProviderFactory(ABC):
    @abstractmethod
    def create_provider(self) -> IAuthProvider:
        pass
