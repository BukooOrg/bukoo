"""
RegisterUseCase — creates a new PENDING user account.

The user is created with status=PENDING. A separate email verification
flow (not implemented here) calls user.activate() when the link is clicked.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.auth_dto import RegisterCommand, TokenDTO
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.password_hasher import IPasswordHasher
from app.application.interfaces.token_service import ITokenService
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user import UserEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class RegisterUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
        token_svc: ITokenService,
        email_svc: IEmailNotificationService,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_svc = token_svc
        self._email_svc = email_svc

    async def execute(self, cmd: RegisterCommand) -> TokenDTO:
        if await self._user_repo.exists_by_email(cmd.email):
            raise UserAlreadyExistsError(cmd.email)

        now = datetime.now(UTC)
        user = UserEntity(
            id=str(uuid7()),
            email=cmd.email,
            full_name=cmd.full_name,
            role=UserRole.USER,
            status=UserStatus.PENDING,  # activated after email verification
            hashed_password=self._hasher.hash(cmd.password),
            avatar_url=None,
            last_login_at=None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        await self._user_repo.save(user)
        await self._db_session.commit()

        self._email_svc.send_welcome(to=user.email, full_name=user.full_name)

        token = self._token_svc.create_access_token(user.id)
        return TokenDTO(access_token=token)
