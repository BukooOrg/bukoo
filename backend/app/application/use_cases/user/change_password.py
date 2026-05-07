from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import ChangePasswordCommand, ChangePasswordResult
from app.application.interfaces.password_hasher import IPasswordHasher
from app.domain.exceptions import (
    CurrentPasswordIncorrectError,
    NewPasswordSameAsCurrentError,
    PasswordNotSetError,
    UserNotFoundError,
)
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class ChangePasswordUseCase(BaseUseCase):
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
    async def execute(self, cmd: ChangePasswordCommand) -> ChangePasswordResult:
        user = await self._user_repo.find_by_id(cmd.user_id)
        if user is None:
            raise UserNotFoundError(cmd.user_id)

        if not user.have_password:
            raise PasswordNotSetError()

        if cmd.current_password == cmd.new_password:
            raise NewPasswordSameAsCurrentError()

        assert user.hashed_password is not None
        if not self._hasher.verify(cmd.current_password, user.hashed_password):
            raise CurrentPasswordIncorrectError()

        new_hashed_password = self._hasher.hash(cmd.new_password)
        user.set_password(new_hashed_password)
        await self._user_repo.save(user)
        await self._db_session.commit()

        return ChangePasswordResult(message="Password changed successfully.")
