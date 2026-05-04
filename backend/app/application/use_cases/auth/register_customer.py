from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.auth_dto import RegisterCommand, RegisterResult
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)

from ..base import BaseUseCase

# todo move to appropriate location
_OTP_TTL_MINUTES = 5


class RegisterCustomerUseCase(BaseUseCase):
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

    async def execute(self, cmd: RegisterCommand) -> RegisterResult:
        if await self._user_repo.exists_by_email(cmd.email):
            raise UserAlreadyExistsError(cmd.email)

        now = datetime.now(UTC)
        hashed_password = self._hasher.hash(cmd.password)

        user = UserEntity(
            _id=str(uuid7()),
            _email=cmd.email,
            _full_name=cmd.full_name,
            _date_of_birth=cmd.date_of_birth,
            _role=UserRole.USER,
            _status=UserStatus.PENDING,
            _hashed_password=hashed_password,
            _avatar_url=None,
            _last_login_at=None,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )
        await self._user_repo.save(user)

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

        return RegisterResult(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            created_at=user.created_at,
        )
