from __future__ import annotations

from typing import override

from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.storage_service import IStorageService
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.facebook_auth_provider import FacebookAuthProvider


class FacebookAuthProviderFactory(IAuthProviderFactory):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    @override
    def create_provider(self) -> IAuthProvider:
        return FacebookAuthProvider(
            user_repo=self._user_repo,
            account_repo=self._account_repo,
            storage_svc=self._storage_svc,
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._redirect_uri,
        )
