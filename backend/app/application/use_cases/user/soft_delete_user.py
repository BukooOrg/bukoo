from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import SoftDeleteUserCommand, SoftDeleteUserResult
from app.core.constants import UserRole
from app.domain.exceptions import UserNotFoundError
from app.domain.exceptions.user import CannotSoftDeleteAdminError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class SoftDeleteUserUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, user_repo: IUserRepository) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo

    @override
    async def execute(self, cmd: SoftDeleteUserCommand) -> SoftDeleteUserResult:
        user = await self._user_repo.find_by_id(cmd.user_id)
        if user is None:
            raise UserNotFoundError(cmd.user_id)

        if user.role == UserRole.ADMIN:
            raise CannotSoftDeleteAdminError()

        user.soft_delete()
        await self._user_repo.save(user)
        await self._db_session.commit()

        return SoftDeleteUserResult(message="User account has been deleted.")
