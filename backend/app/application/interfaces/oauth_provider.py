from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dtos.auth_dto import OAuthUserInfo


class IOAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        pass

    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        pass
