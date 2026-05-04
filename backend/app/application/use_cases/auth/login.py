from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import TokenDTO
from app.application.interfaces.auth_provider_factory import IAuthProviderFactory
from app.application.interfaces.token_service import ITokenService

from ..base import BaseUseCase

logger = structlog.get_logger(__name__)


class LoginUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        factory: IAuthProviderFactory,
        token_svc: ITokenService,
    ) -> None:
        super().__init__(db_session)
        self._factory = factory
        self._token_svc = token_svc

    async def execute(self, payload: dict[str, str]) -> TokenDTO:
        provider = self._factory.create_provider()
        result = await provider.authenticate(payload)
        await self._db_session.commit()

        token = self._token_svc.create_access_token(result.user_id)
        logger.info(token)
        return TokenDTO(access_token=token)
