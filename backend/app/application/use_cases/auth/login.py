from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import TokenDTO
from app.application.interfaces.auth_provider import IAuthStrategy
from app.application.interfaces.token_service import ITokenService

from ..base import BaseUseCase


class LoginUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        strategy: IAuthStrategy,
        token_svc: ITokenService,
    ) -> None:
        super().__init__(db_session)
        self._strategy = strategy
        self._token_svc = token_svc

    async def execute(self, payload: dict[str, str]) -> TokenDTO:
        result = await self._strategy.authenticate(payload)
        await self._db_session.commit()

        token = self._token_svc.create_access_token(result.user_id)
        return TokenDTO(access_token=token)
