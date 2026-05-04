from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.auth_dto import (
    ResendVerificationCommand,
    ResendVerificationResult,
)
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import VerificationTokenType
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions import UserAlreadyVerifiedError, UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)

from ..base import BaseUseCase

_OTP_TTL_MINUTES = 5


class ResendEmailVerificationUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        verification_token_repo: IVerificationTokenRepository,
        hasher: IPasswordHasher,
        email_svc: IEmailNotificationService,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._verification_token_repo = verification_token_repo
        self._hasher = hasher
        self._email_svc = email_svc

    async def execute(self, cmd: ResendVerificationCommand) -> ResendVerificationResult:
        user = await self._user_repo.find_by_email(cmd.email)
        if user is None:
            raise UserNotFoundError(cmd.email)

        if user.is_active:
            raise UserAlreadyVerifiedError(cmd.email)

        now = datetime.now(UTC)
        otp = secrets.randbelow(900000) + 100000
        token_hash = self._hasher.hash(str(otp))
        expires_at = now + timedelta(minutes=_OTP_TTL_MINUTES)

        token = VerificationTokenEntity(
            _id=str(uuid7()),
            _user_id=user.id,
            _token_hash=token_hash,
            _type=VerificationTokenType.EMAIL_VERIFY,
            _expires_at=expires_at,
            _created_at=now,
            _updated_at=now,
        )
        await self._verification_token_repo.save(token)

        await self._db_session.commit()

        self._email_svc.send_verification_email(to=user.email, otp=str(otp))

        return ResendVerificationResult(
            email=user.email,
            message="Verification email resent successfully",
        )
