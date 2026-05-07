from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import SoftDeleteMeCommand, SoftDeleteMeResult
from app.application.interfaces.token_service import ITokenService
from app.core.constants import UserRole
from app.domain.exceptions import CustomerOnlyError, UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class SoftDeleteMeUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        token_svc: ITokenService,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._token_svc = token_svc

    @override
    async def execute(self, command: SoftDeleteMeCommand) -> SoftDeleteMeResult:
        user = await self._user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        if user.role != UserRole.USER:
            raise CustomerOnlyError

        user.soft_delete()

        await self._user_repo.save(user)
        await self._db_session.commit()

        await self._token_svc.revoke_token(command.token_payload)

        return SoftDeleteMeResult(message="Your account has been deleted.")
