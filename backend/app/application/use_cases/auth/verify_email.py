from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.auth_dto import VerifyEmailCommand, VerifyEmailResult
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import AuthProvider, VerificationTokenType
from app.domain.entities.account_entity import AccountEntity
from app.domain.exceptions import (
    InvalidTokenError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
)
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)

from ..base import BaseUseCase


class VerifyEmailUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        verification_token_repo: IVerificationTokenRepository,
        account_repo: IAccountRepository,
        hasher: IPasswordHasher,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._verification_token_repo = verification_token_repo
        self._account_repo = account_repo
        self._hasher = hasher

    async def execute(self, cmd: VerifyEmailCommand) -> VerifyEmailResult:
        user = await self._user_repo.find_by_email(cmd.email)
        if user is None:
            raise UserNotFoundError(cmd.email)

        if user.is_active:
            raise UserAlreadyVerifiedError(cmd.email)

        token = await self._verification_token_repo.find_active_by_user_and_type(
            user.id, VerificationTokenType.EMAIL_VERIFY
        )
        if token is None:
            raise InvalidTokenError()

        if not self._hasher.verify(cmd.otp, token.token_hash):
            raise InvalidTokenError()

        token.mark_used()
        await self._verification_token_repo.save(token)

        user.activate()
        await self._user_repo.save(user)

        now = datetime.now(UTC)
        account = AccountEntity(
            _id=str(uuid7()),
            _user_id=user.id,
            _provider=AuthProvider.CREDENTIAL,
            _open_id=None,
            _encrypted_token=None,
            _created_at=now,
            _updated_at=now,
        )
        await self._account_repo.save(account)

        await self._db_session.commit()

        return VerifyEmailResult(
            email=user.email,
            message="Email verified successfully",
        )
