from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import OAuthCallbackCommand, TokenDTO
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.cache_service import ICacheService
from app.application.interfaces.token_service import ITokenService
from app.domain.exceptions.auth import OAuthStateInvalidError

from ..base import BaseUseCase


class OAuthCallbackUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        cache_svc: ICacheService,
        factory: IAuthProviderFactory,
        token_svc: ITokenService,
    ) -> None:
        super().__init__(db_session)
        self._cache_svc = cache_svc
        self._factory = factory
        self._token_svc = token_svc

    async def execute(self, command: OAuthCallbackCommand) -> TokenDTO:
        if not await self._cache_svc.exists(f"oauth_state:{command.state}"):
            raise OAuthStateInvalidError()
        await self._cache_svc.delete(f"oauth_state:{command.state}")

        provider = self._factory.create_provider()
        auth_result = await provider.authenticate({"code": command.code})

        await self._db_session.commit()
        return TokenDTO(
            access_token=self._token_svc.create_access_token(auth_result.user_id)
        )
