from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import GetOAuthLoginUrlResult
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.cache_service import ICacheService
from app.application.interfaces.oauth_provider import IOAuthProvider
from app.domain.exceptions.auth import OAuthProviderNotFoundError

from ..base import BaseUseCase

_STATE_TTL_SECONDS = 600


class GetOAuthLoginUrlUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cache_svc: ICacheService,
        factory: IAuthProviderFactory,
    ) -> None:
        super().__init__(db_session)
        self._cache_svc = cache_svc
        self._factory = factory

    async def execute(self) -> GetOAuthLoginUrlResult:
        state = secrets.token_urlsafe(32)
        await self._cache_svc.set(
            f"oauth_state:{state}", "1", ttl_seconds=_STATE_TTL_SECONDS
        )
        provider = self._factory.create_provider()
        if not isinstance(provider, IOAuthProvider):
            raise OAuthProviderNotFoundError("provider")
        url = provider.get_authorization_url(state=state)
        return GetOAuthLoginUrlResult(url=url)
