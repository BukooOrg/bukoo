"""
SystemRegisterUseCase — creates a new admin user.

This is only called once on the app setup. No need email verification.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.config import get_configs
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user import UserEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase

logger = structlog.get_logger(__name__)


class SystemRegisterUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._hasher = hasher

    async def execute(self) -> None:
        logger.info("Creating system admin user...")

        configs = get_configs()
        email = configs.DEFAULT_ADMIN_MAIL
        full_name = configs.DEFAULT_ADMIN_FULL_NAME
        password = configs.DEFAULT_ADMIN_PASSWORD

        if await self._user_repo.exists_by_email(email):
            raise UserAlreadyExistsError(email)

        now = datetime.now(UTC)
        user = UserEntity(
            id=str(uuid7()),
            email=email,
            full_name=full_name,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,  # no need email verification
            hashed_password=self._hasher.hash(password),
            avatar_url=None,
            last_login_at=None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        await self._user_repo.save(user)
        await self._db_session.commit()

        logger.info("System admin user is created successfully!")
        logger.info(
            "System admin details", email=email, full_name=full_name, password=password
        )
