from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import ResetPasswordCommand, ResetPasswordResult
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import VerificationTokenType
from app.domain.exceptions.auth import InvalidTokenError
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)

from ..base import BaseUseCase

_SUCCESS_MESSAGE = "Password has been reset successfully."


class ResetPasswordUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        verification_token_repo: IVerificationTokenRepository,
        hasher: IPasswordHasher,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._verification_token_repo = verification_token_repo
        self._hasher = hasher

    async def execute(self, cmd: ResetPasswordCommand) -> ResetPasswordResult:
        user = await self._user_repo.find_by_email(cmd.email)
        if user is None:
            raise InvalidTokenError()

        token = await self._verification_token_repo.find_active_by_user_and_type(
            user.id, VerificationTokenType.PASSWORD_RESET
        )
        if token is None:
            raise InvalidTokenError()

        if not self._hasher.verify(cmd.otp, token.token_hash):
            raise InvalidTokenError()

        hashed = self._hasher.hash(cmd.new_password)
        user.set_password(hashed)
        await self._user_repo.save(user)

        token.mark_used()
        await self._verification_token_repo.save(token)

        await self._db_session.commit()

        return ResetPasswordResult(message=_SUCCESS_MESSAGE)
