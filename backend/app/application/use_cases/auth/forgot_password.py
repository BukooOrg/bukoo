from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.auth_dto import ForgotPasswordCommand, ForgotPasswordResult
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import VerificationTokenType
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)

from ..base import BaseUseCase

logger = structlog.get_logger(__name__)

# todo: move to appropriate location
_OTP_TTL_MINUTES = 15
_GENERIC_MESSAGE = "If this email is registered, a password reset code has been sent."


class ForgotPasswordUseCase(BaseUseCase):
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

    async def execute(self, cmd: ForgotPasswordCommand) -> ForgotPasswordResult:
        user = await self._user_repo.find_by_email(cmd.email)
        if user is None:
            return ForgotPasswordResult(message=_GENERIC_MESSAGE)

        if not user.is_active:
            return ForgotPasswordResult(message=_GENERIC_MESSAGE)

        existing_token = (
            await self._verification_token_repo.find_active_by_user_and_type(
                user.id, VerificationTokenType.PASSWORD_RESET
            )
        )
        if existing_token is not None:
            existing_token.mark_used()
            await self._verification_token_repo.save(existing_token)

        now = datetime.now(UTC)
        # todo: consider create generate_otp utility function
        otp = secrets.randbelow(900000) + 100000
        token_hash = self._hasher.hash(str(otp))
        expires_at = now + timedelta(minutes=_OTP_TTL_MINUTES)

        new_token = VerificationTokenEntity(
            _id=str(uuid7()),
            _user_id=user.id,
            _token_hash=token_hash,
            _type=VerificationTokenType.PASSWORD_RESET,
            _expires_at=expires_at,
            _created_at=now,
            _updated_at=now,
        )
        await self._verification_token_repo.save(new_token)

        await self._db_session.commit()

        logger.debug({"to": user.email, "otp": otp})
        self._email_svc.send_password_reset_email(to=user.email, otp=str(otp))

        return ForgotPasswordResult(message=_GENERIC_MESSAGE)
