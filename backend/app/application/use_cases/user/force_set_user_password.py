from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import (
    ForceSetUserPasswordCommand,
    ForceSetUserPasswordResult,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import UserRole
from app.domain.exceptions import UserNotFoundError
from app.domain.exceptions.user import (
    CannotResetAdminPasswordError,
    UserHasNoCredentialAccountError,
)
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class ForceSetUserPasswordUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._hasher = hasher

    @override
    async def execute(
        self, cmd: ForceSetUserPasswordCommand
    ) -> ForceSetUserPasswordResult:
        user = await self._user_repo.find_by_id(cmd.user_id)
        if user is None:
            raise UserNotFoundError(cmd.user_id)

        if user.role == UserRole.ADMIN:
            raise CannotResetAdminPasswordError()

        if not user.have_password:
            raise UserHasNoCredentialAccountError()

        hashed = self._hasher.hash(cmd.new_password)
        user.set_password(hashed)
        await self._user_repo.save(user)
        await self._db_session.commit()

        return ForceSetUserPasswordResult(
            message="Password has been reset successfully."
        )
