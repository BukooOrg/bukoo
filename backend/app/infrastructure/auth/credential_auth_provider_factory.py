from __future__ import annotations

from typing import override

from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.password_hasher import IPasswordHasher
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.credential_auth_provider import CredentialAuthProvider


class CredentialAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    @override
    def create_provider(self) -> IAuthProvider:
        return CredentialAuthProvider(user_repo=self._user_repo, hasher=self._hasher)
