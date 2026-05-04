from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import LogoutCommand, LogoutResult
from app.application.interfaces.token_service import ITokenService

from ..base import BaseUseCase


class LogoutUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, token_svc: ITokenService) -> None:
        super().__init__(db_session)
        self._token_svc = token_svc

    async def execute(self, command: LogoutCommand) -> LogoutResult:
        await self._token_svc.revoke_token(command.token_payload)
        return LogoutResult(message="Logged out successfully.")
