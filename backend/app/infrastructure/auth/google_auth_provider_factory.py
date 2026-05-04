from __future__ import annotations

from typing import override

from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.google_auth_provider import GoogleAuthProvider


class GoogleAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo

    @override
    def create_provider(self) -> IAuthProvider:
        return GoogleAuthProvider(
            user_repo=self._user_repo, account_repo=self._account_repo
        )
